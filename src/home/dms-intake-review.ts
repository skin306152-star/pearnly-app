// ============================================================
// 录入工作台 · 步骤3 复核 · 就地手风琴展开 + 原图查看器
//   点文件行「查看结果」→ 识别结果就地展开在该行下方(只开一行);
//   左字段卡可直接编辑(核心6 + 展开全部字段含明细行表) · 右原图卡边看边改
//   (拖拽 / 滚轮缩放 / 放大缩小 / 旋转 / 重置 / 双击)。
//   多发票 PDF → 同面板堆叠 N 组字段,共用一张原图(/api/history/{id}/page/1.png)。
//   确认为纯前端视觉态(IV.confirmed) · 不写回后端 · 导出仍按 history_ids 全量走。
//   从 invoice-submit.ts 拆出以控行数。
// ============================================================
/* global t, showToast */
import { esc, $, authHeaders } from './dms-intake-core.js';
import { IV, ext, showStepInv } from './dms-intake-invoice.js';
import type { Dict, IvInvoice, IvResult } from './dms-intake-invoice.js';

// 复核预览字段(复用 OCR 抽屉字段标签键)
const REV_CORE: Array<[string, string]> = [
    ['seller_name', 'drawer-lbl-name'],
    ['seller_tax', 'drawer-lbl-tax'],
    ['invoice_number', 'drawer-lbl-invoice'],
    ['date', 'drawer-lbl-date'],
    ['subtotal', 'drawer-lbl-subtotal'],
    ['vat', 'drawer-lbl-vat'],
];
const REV_MORE: Array<[string, string]> = [
    ['total_amount', 'drawer-lbl-total'],
    ['buyer_name', 'drawer-lbl-name'],
    ['wht_amount', 'drawer-lbl-wht-amount'],
];

function warnFields(f: Dict): Set<string> {
    const s = new Set<string>();
    ['invoice_number', 'seller_tax', 'total_amount'].forEach((k) => {
        if (!String(f[k] || '').trim()) s.add(k);
    });
    return s;
}
function fileWarns(r: IvResult): number {
    return r.invoices.reduce((n, inv) => n + warnFields(inv.fields).size, 0);
}
// 「可通过项」= 不需复核且无低置信空字段(确认全部只动这些)
function passable(r: IvResult): boolean {
    return !r.needs_review && fileWarns(r) === 0;
}

// 原图缓存(history_id → objectURL) + 查看器变换态(同一刻只一个面板展开)
const imgCache = new Map<string, string>();
let vstate = { x: 0, y: 0, scale: 1, rot: 0 };
let viewerCleanup: (() => void) | null = null;
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

export function renderReview() {
    IV.view = 'review';
    const el = $('dx-s-inv-review');
    if (!el) return;
    if (IV.openIdx == null) IV.openIdx = IV.results.length ? 0 : -1;
    const banner = IV.results.some((r) => r.needs_review)
        ? `<div class="dx-recheck-banner">${esc(t('dxi-needs-review'))}</div>`
        : '';
    const items = IV.results.map((r, i) => accItemHtml(r, i)).join('');
    el.innerHTML = banner + barHtml() + `<div class="dx-acc">${items}</div>` + footHtml();
    showStepInv(3, 'dx-s-inv-review');
    bindOpenViewer();
}

function barHtml(): string {
    const sideBtn = (side: 'right' | 'left', lk: string) =>
        `<button class="dx-imgside-btn${IV.imgSide === side ? ' active' : ''}" data-iv-side="${side}">${esc(t(lk))}</button>`;
    return (
        '<div class="dx-rv-bar"><div class="dx-rv-bar-t">' +
        `<b>${esc(t('dxi-rev-files-h'))}</b><span>${esc(t('dxi-rev-files-tip'))}</span></div>` +
        '<div class="dx-rv-bar-a">' +
        `<button class="btn small" id="dx-inv-collapse-all">${esc(t('dxi-rev-collapse-all'))}</button>` +
        `<button class="btn small primary" id="dx-inv-confirm-all">${esc(t('dxi-rev-confirm-all'))}</button>` +
        `<span class="dx-imgside-l">${esc(t('dxi-rev-imgside'))}</span>` +
        `<div class="dx-imgside">${sideBtn('right', 'dxi-rev-side-right')}${sideBtn('left', 'dxi-rev-side-left')}</div>` +
        '</div></div>'
    );
}

function statusHtml(r: IvResult, i: number): string {
    if (IV.confirmed.has(i))
        return `<span class="dx-pill ok">✓ ${esc(t('dxi-rev-confirmed'))}</span>`;
    if (r.needs_review) return `<span class="dx-pill warn">! ${esc(t('dxi-rev-recheck'))}</span>`;
    const w = fileWarns(r);
    if (w > 0)
        return `<span class="dx-pill warn">! ${esc(t('dxi-rev-need').replace('{n}', String(w)))}</span>`;
    return `<span class="dx-pill ok">✓ ${esc(t('dxi-rev-ok'))}</span>`;
}

function accItemHtml(r: IvResult, i: number): string {
    const open = i === IV.openIdx;
    const w = fileWarns(r);
    const sub =
        (r.invoice_count > 1
            ? esc(t('dxi-multi').replace('{n}', String(r.invoice_count)))
            : esc(t(w ? 'dxi-rev-only' : 'dxi-rev-noneed'))) +
        (r.from_cache ? ' · ' + esc(t('cache-hit-badge')) : '');
    const row =
        `<div class="dx-acc-row" data-iv-toggle="${i}">` +
        `<div class="dx-file-ic">${esc(ext(r.filename))}</div>` +
        `<div class="dx-file-c"><b>${esc(r.filename)}</b><span>${sub} · ${esc(t('dxi-rev-editable'))}</span></div>` +
        statusHtml(r, i) +
        `<button class="dx-acc-btn" data-iv-toggle="${i}">${esc(t(open ? 'dxi-rev-collapse' : 'dxi-rev-view'))}</button></div>`;
    const panel = open ? accPanelHtml(r, i) : '';
    return `<div class="dx-acc-item${open ? ' open' : ''}" data-acc="${i}">${row}${panel}</div>`;
}

function accPanelHtml(r: IvResult, i: number): string {
    const groups = r.invoices.map((inv, ii) => invoiceGroupHtml(i, ii, inv)).join('');
    const gridCls = IV.imgSide === 'left' ? ' image-left' : '';
    return (
        '<div class="dx-acc-panel"><div class="dx-acc-top"><div>' +
        `<b>${esc(r.filename)} · ${esc(t('dxi-rev-h'))}</b>` +
        `<span class="dx-acc-tip">${esc(t('dxi-rev-panel-tip'))}</span></div>` +
        '<div class="dx-acc-top-a">' +
        `<button class="dx-toggle dx-extra-toggle">${esc(t('dxi-rev-toggle-all'))}</button>` +
        `<button class="dx-toggle dx-collapse-one">${esc(t('dxi-rev-collapse'))}</button></div></div>` +
        `<div class="dx-rgrid${gridCls}"><div class="dx-fields">${groups}${fieldsFootHtml()}</div>` +
        imageCardHtml(r) +
        '</div></div>'
    );
}

function invoiceGroupHtml(fi: number, ii: number, inv: IvInvoice): string {
    const warns = warnFields(inv.fields);
    if (inv.fmtWarn) warns.add('invoice_number'); // 格式偏离多数派 → 标黄该张发票号
    const head =
        inv.total > 1
            ? `<div class="dx-inv-head">${esc(t('dxi-inv-no').replace('{i}', String(inv.idx)).replace('{n}', String(inv.total)))}${inv.fmtWarn ? `<span class="dx-inv-fmtwarn">${esc(t('dxi-fmt-warn'))}</span>` : ''}</div>`
            : inv.fmtWarn
              ? `<div class="dx-inv-head"><span class="dx-inv-fmtwarn">${esc(t('dxi-fmt-warn'))}</span></div>`
              : '';
    const cell = ([k, lk]: [string, string]) => {
        const warn = warns.has(k) ? ' warn' : '';
        const v = String(inv.fields[k] ?? '');
        return (
            `<div class="dx-rv${warn}"><label>${esc(t(lk))}</label>` +
            `<input class="dx-rv-in" data-iv-field="${fi}:${ii}:${esc(k)}" value="${esc(v)}"></div>`
        );
    };
    const core = REV_CORE.map(cell).join('');
    const more = REV_MORE.map(cell).join('');
    return (
        head +
        `<div class="dx-review-grid">${core}</div>` +
        `<div class="dx-extra"><div class="dx-review-grid">${more}</div>${itemsTableHtml(inv)}</div>`
    );
}

function itemsTableHtml(inv: IvInvoice): string {
    const items = (inv.fields.items as Array<Dict>) || [];
    if (!Array.isArray(items) || !items.length) return '';
    const rows = items
        .map((it) => {
            const name = String(it.name ?? '');
            const qty = String(it.qty ?? '');
            const amt = String(it.price ?? it.subtotal ?? it.amount ?? '');
            return `<tr><td>${esc(name)}</td><td>${esc(qty)}</td><td>${esc(amt)}</td></tr>`;
        })
        .join('');
    return (
        '<table class="dx-item-tbl"><thead><tr>' +
        `<th>${esc(t('dxi-rev-item-name'))}</th><th>${esc(t('dxi-rev-item-qty'))}</th>` +
        `<th class="r">${esc(t('dxi-rev-item-amt'))}</th></tr></thead><tbody>${rows}</tbody></table>`
    );
}

function fieldsFootHtml(): string {
    return (
        `<div class="dx-fields-foot"><div class="dx-note">${esc(t('dxi-rev-hint'))}</div>` +
        '<div class="dx-fields-foot-a">' +
        `<button class="btn small dx-save-one">${esc(t('dxi-rev-save'))}</button>` +
        `<button class="btn small primary dx-confirm-one">${esc(t('dxi-rev-next'))}</button></div></div>`
    );
}

function imageCardHtml(r: IvResult): string {
    const noimg = !r.history_ids.length;
    return (
        `<div class="dx-imgcard${noimg ? ' noimg' : ''}"><div class="dx-vtoolbar">` +
        `<div class="dx-vtitle">${esc(t('dxi-rev-viewer-title'))}</div><div class="dx-vctrls">` +
        '<button class="dx-icon-btn dx-zoom-out" title="−">−</button>' +
        '<span class="dx-zoom">100%</span>' +
        '<button class="dx-icon-btn dx-zoom-in" title="+">＋</button>' +
        '<button class="dx-icon-btn dx-rotate" title="↻">↻</button>' +
        '<button class="dx-icon-btn dx-reset" title="⟲">⟲</button></div></div>' +
        '<div class="dx-viewport"><div class="dx-canvas">' +
        '<img class="dx-rimg" draggable="false" alt="">' +
        '</div>' +
        `<div class="dx-vempty">${esc(t('dxi-rev-noimg'))}</div>` +
        `<div class="dx-vloading"><span class="dx-vspin"></span>${esc(t('dxi-rev-loading'))}</div>` +
        `<div class="dx-vhelp">${esc(t('dxi-rev-viewer-help'))}</div></div></div>`
    );
}

function footHtml(): string {
    return (
        `<div class="dx-foot"><div class="dx-note">${esc(t('dxi-rev-hint'))}</div>` +
        '<div style="display:flex;gap:8px">' +
        `<button class="btn" id="dx-inv-rev-back">${esc(t('dxi-rev-back'))}</button>` +
        `<button class="btn primary" id="dx-inv-rev-next">${esc(t('dxi-rev-goexport'))}</button></div></div>`
    );
}

// 保存修改:把当前展开文件的每张发票(用户在输入框改过的 fields 已实时写入 IV.results)
// 真持久化到各自 ocr_history 行 → 识别记录 / 导出 / 推 ERP 都用改后值。
// 此前此按钮只弹 toast 不写库(假保存)→ 用户修正凭空蒸发,见问题 02。
async function saveOpenFileEdits(btn: HTMLElement | null): Promise<void> {
    const r = IV.results[IV.openIdx];
    if (!r) return;
    const targets = r.invoices.filter((iv) => iv.history_id);
    if (!targets.length) {
        showToast(t('dxi-rev-save-fail'), 'error');
        return;
    }
    btn?.setAttribute('disabled', '1');
    try {
        await Promise.all(
            targets.map((iv) =>
                fetch(`/api/history/${encodeURIComponent(iv.history_id as string)}`, {
                    method: 'PUT',
                    headers: authHeaders(true),
                    body: JSON.stringify({ pages: [{ fields: iv.fields }] }),
                }).then((resp) => {
                    if (!resp.ok) throw new Error(String(resp.status));
                })
            )
        );
        showToast(t('dxi-rev-saved'), 'success');
    } catch {
        showToast(t('dxi-rev-save-fail'), 'error');
    } finally {
        btn?.removeAttribute('disabled');
    }
}

// ── 交互(由 onInvoiceClick 在 review 阶段优先转发)─────────────
export function onReviewClick(tg: HTMLElement): boolean {
    const tog = tg.closest('[data-iv-toggle]') as HTMLElement | null;
    if (tog) {
        const i = +tog.dataset.ivToggle!;
        IV.openIdx = IV.openIdx === i ? -1 : i;
        renderReview();
        return true;
    }
    if (tg.closest('.dx-collapse-one') || tg.closest('#dx-inv-collapse-all')) {
        IV.openIdx = -1;
        renderReview();
        return true;
    }
    const side = tg.closest('[data-iv-side]') as HTMLElement | null;
    if (side) {
        IV.imgSide = side.dataset.ivSide as 'right' | 'left';
        const panel = openPanel();
        panel?.querySelector('.dx-rgrid')?.classList.toggle('image-left', IV.imgSide === 'left');
        document
            .querySelectorAll('.dx-imgside-btn')
            .forEach((b) =>
                b.classList.toggle('active', (b as HTMLElement).dataset.ivSide === IV.imgSide)
            );
        return true;
    }
    if (tg.closest('.dx-extra-toggle')) {
        const btn = tg.closest('.dx-extra-toggle') as HTMLElement;
        const panel = openPanel();
        const on = !!panel && panel.classList.toggle('extra-on');
        btn.textContent = t(on ? 'dxi-rev-toggle-less' : 'dxi-rev-toggle-all');
        return true;
    }
    if (tg.closest('.dx-zoom-in')) return (zoomBy(0.15), true);
    if (tg.closest('.dx-zoom-out')) return (zoomBy(-0.15), true);
    if (tg.closest('.dx-rotate')) {
        vstate.rot = (vstate.rot + 90) % 360;
        applyViewer();
        return true;
    }
    if (tg.closest('.dx-reset')) {
        vstate = { x: 0, y: 0, scale: 1, rot: 0 };
        applyViewer();
        return true;
    }
    if (tg.closest('.dx-save-one')) {
        void saveOpenFileEdits(tg.closest('.dx-save-one'));
        return true;
    }
    if (tg.closest('.dx-confirm-one')) {
        if (IV.openIdx >= 0) {
            IV.confirmed.add(IV.openIdx);
            IV.openIdx = nextUnconfirmed(IV.openIdx);
            renderReview();
            showToast(t('dxi-rev-confirmed-toast'), 'success');
        }
        return true;
    }
    if (tg.closest('#dx-inv-confirm-all')) {
        IV.results.forEach((r, i) => {
            if (passable(r)) IV.confirmed.add(i);
        });
        renderReview();
        showToast(t('dxi-rev-confirmed-all'), 'success');
        return true;
    }
    return false;
}

function nextUnconfirmed(from: number): number {
    for (let i = from + 1; i < IV.results.length; i++) if (!IV.confirmed.has(i)) return i;
    for (let i = 0; i < IV.results.length; i++) if (!IV.confirmed.has(i)) return i;
    return -1;
}
function openPanel(): HTMLElement | null {
    return document.querySelector('.dx-acc-item.open .dx-acc-panel');
}
function zoomBy(d: number) {
    vstate.scale = clamp(vstate.scale + d, 0.4, 3.4);
    applyViewer();
}
function applyViewer() {
    const panel = openPanel();
    if (!panel) return;
    const canvas = panel.querySelector('.dx-canvas') as HTMLElement | null;
    const label = panel.querySelector('.dx-zoom');
    if (canvas)
        canvas.style.transform = `translate(calc(-50% + ${vstate.x}px), calc(-50% + ${vstate.y}px)) scale(${vstate.scale}) rotate(${vstate.rot}deg)`;
    if (label) label.textContent = Math.round(vstate.scale * 100) + '%';
}

// 展开后:加载原图 + 接拖拽/滚轮(只对当前展开面板 · 重渲先清旧 window 监听)
function bindOpenViewer() {
    if (viewerCleanup) {
        viewerCleanup();
        viewerCleanup = null;
    }
    if (IV.openIdx < 0) return;
    const panel = openPanel();
    const r = IV.results[IV.openIdx];
    if (!panel || !r) return;
    vstate = { x: 0, y: 0, scale: 1, rot: 0 };
    applyViewer();
    void loadImage(panel, r);
    const viewport = panel.querySelector('.dx-viewport') as HTMLElement | null;
    if (!viewport) return;
    let drag = false;
    let sx = 0;
    let sy = 0;
    let ox = 0;
    let oy = 0;
    viewport.addEventListener('mousedown', (e) => {
        drag = true;
        sx = e.clientX;
        sy = e.clientY;
        ox = vstate.x;
        oy = vstate.y;
        viewport.classList.add('dragging');
    });
    const move = (e: MouseEvent) => {
        if (!drag) return;
        vstate.x = ox + (e.clientX - sx);
        vstate.y = oy + (e.clientY - sy);
        applyViewer();
    };
    const up = () => {
        drag = false;
        viewport.classList.remove('dragging');
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
    viewport.addEventListener(
        'wheel',
        (e) => {
            e.preventDefault();
            zoomBy(e.deltaY < 0 ? 0.1 : -0.1);
        },
        { passive: false }
    );
    viewport.addEventListener('dblclick', () => {
        vstate = { x: 0, y: 0, scale: 1.6, rot: 0 };
        applyViewer();
    });
    viewerCleanup = () => {
        window.removeEventListener('mousemove', move);
        window.removeEventListener('mouseup', up);
    };
}

async function loadImage(panel: HTMLElement, r: IvResult) {
    const img = panel.querySelector('.dx-rimg') as HTMLImageElement | null;
    const card = panel.querySelector('.dx-imgcard');
    const hid = r.history_ids[0];
    if (!img || !card) return;
    if (!hid) {
        card.classList.add('noimg');
        return;
    }
    const cached = imgCache.get(hid);
    if (cached) {
        img.src = cached;
        return;
    }
    // 留底 PDF 是识别返回后【异步后台】回填(几秒后才落盘)· 首次 404 = 还没就绪 →
    // 轮询重试等它,别一次 404 就永久判「原图不可用」。面板被收起/重渲(isConnected=false)即放弃。
    card.classList.add('loading');
    for (let attempt = 0; attempt < 8; attempt++) {
        if (!panel.isConnected) return;
        try {
            const resp = await fetch(`/api/history/${encodeURIComponent(hid)}/page/1.png`, {
                headers: authHeaders(),
            });
            if (resp.ok) {
                const url = URL.createObjectURL(await resp.blob());
                imgCache.set(hid, url);
                card.classList.remove('loading');
                img.src = url;
                return;
            }
            if (resp.status !== 404) break; // 渲染失败等硬错 → 不再等
        } catch {
            break; // 网络错 → 停
        }
        await new Promise((res) => setTimeout(res, 1200));
    }
    card.classList.remove('loading');
    card.classList.add('noimg');
}
