// ============================================================
// 录入工作台 · 步骤3 复核 · 就地手风琴展开 + 原图查看器
//   点文件行「查看结果」→ 识别结果就地展开在该行下方(只开一行);
//   左字段卡可直接编辑(核心6 + 展开全部字段含明细行表) · 右原图卡边看边改
//   (拖拽 / 滚轮缩放 / 放大缩小 / 旋转 / 重置 / 双击)。
//   多发票 PDF → 同面板堆叠 N 组字段 + 右侧复用共享 image-viewer.ts(识别记录/异常同款):
//   按物理页翻(‹ 1/N ›)看到每一页,治「一份多页 PDF 只渲第一页」。不再各写一套查看器。
//   字段编辑经「保存修改」真持久化到各张 ocr_history;确认态(IV.confirmed)仍纯前端视觉。
//   从 invoice-submit.ts 拆出以控行数。
// ============================================================
/* global t, showToast, withLoading */
import { esc, $, authHeaders } from './dms-intake-core.js';
import { IV, ext, showStepInv } from './dms-intake-invoice.js';
import type { Dict, IvInvoice, IvResult } from './dms-intake-invoice.js';
import { imageViewerHtml, mountImageViewer } from './image-viewer.js';

// 复核预览字段(复用 OCR 抽屉字段标签键)
const REV_CORE: Array<[string, string]> = [
    ['seller_name', 'drawer-lbl-name'],
    ['seller_tax', 'drawer-lbl-tax'],
    ['invoice_number', 'drawer-lbl-invoice'],
    // 票面原文(泰国票面印佛历)· 保存走 PUT /api/history 由后端按它反推公历 date
    ['date_raw', 'drawer-lbl-date'],
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

// 原图查看器复用识别记录/异常同款共享件(image-viewer.ts · 按物理页翻 + 缩放/旋转/全屏)·
// 同一刻只一个面板挂载,重渲先清旧实例。
let viewerCleanup: (() => void) | null = null;

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
    const fmtChip = inv.fmtWarn
        ? `<span class="dx-inv-fmtwarn">${esc(t('dxi-fmt-warn'))}</span>`
        : '';
    const label =
        inv.total > 1
            ? esc(t('dxi-inv-no').replace('{i}', String(inv.idx)).replace('{n}', String(inv.total)))
            : '';
    const headInner = label + fmtChip;
    const head = headInner ? `<div class="dx-inv-head">${headInner}</div>` : '';
    const cell = ([k, lk]: [string, string]) => {
        const warn = warns.has(k) ? ' warn' : '';
        // 旧记录/文字层来源没有 date_raw → 回落已归一的 date,不让格子空着
        const v = String(
            (k === 'date_raw' ? (inv.fields.date_raw ?? inv.fields.date) : inv.fields[k]) ?? ''
        );
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
        `<div class="dx-imgcard${noimg ? ' noimg' : ''}">` +
        imageViewerHtml({
            hint: t('imgv-hint'),
            noimg: t('imgv-noimg'),
            loading: t('imgv-loading'),
        }) +
        '</div>'
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
    try {
        await withLoading(btn, () =>
            Promise.all(
                targets.map((iv) =>
                    fetch(`/api/history/${encodeURIComponent(iv.history_id as string)}`, {
                        method: 'PUT',
                        headers: authHeaders(true),
                        body: JSON.stringify({ pages: [{ fields: iv.fields }] }),
                    }).then((resp) => {
                        if (!resp.ok) throw new Error(String(resp.status));
                    })
                )
            )
        );
        showToast(t('dxi-rev-saved'), 'success');
    } catch {
        showToast(t('dxi-rev-save-fail'), 'error');
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
// 展开后:把共享查看器挂到 .dx-imgcard(内含 .pv-viewer)· 各张发票共用整份留底 PDF,
// 用首张记录 + 物理页翻页(‹ 1/N ›)即可翻到每张票所在页。重渲先清旧实例。
function bindOpenViewer() {
    if (viewerCleanup) {
        viewerCleanup();
        viewerCleanup = null;
    }
    if (IV.openIdx < 0) return;
    const panel = openPanel();
    const r = IV.results[IV.openIdx];
    if (!panel || !r) return;
    const pane = panel.querySelector('.dx-imgcard') as HTMLElement | null;
    if (pane?.querySelector('.pv-viewer')) {
        viewerCleanup = mountImageViewer(pane, r.history_ids[0] || null);
    }
}
