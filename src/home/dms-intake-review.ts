// ============================================================
// 录入工作台 · 步骤3 复核 · 就地手风琴展开 + 原图查看器
//   点文件行「查看结果」→ 识别结果就地展开在该行下方(只开一行);
//   左字段卡可直接编辑(核心6 + 展开全部字段含明细行表) · 右原图卡边看边改
//   (拖拽 / 滚轮缩放 / 放大缩小 / 旋转 / 重置 / 双击)。
//   多发票 PDF → 同面板堆叠 N 组字段 + 右侧复用共享 image-viewer.ts(识别记录/异常同款):
//   按物理页翻(‹ 1/N ›)看到每一页,治「一份多页 PDF 只渲第一页」。不再各写一套查看器。
//   字段编辑经「保存修改」真持久化到各张 ocr_history；正式确认后按后端状态锁定只读。
//   从 invoice-submit.ts 拆出以控行数。
// ============================================================
/* global t, showToast, withLoading */
import { esc, $, authHeaders } from './dms-intake-core.js';
import { IV, ext, showStepInv } from './dms-intake-invoice.js';
import type { Dict, IvInvoice, IvResult } from './dms-intake-invoice.js';
import { imageViewerHtml, mountImageViewer } from './image-viewer.js';
import type { ViewerApi } from './image-viewer.js';
import { revCore, revMore, isAnonBuyerDoc, warnFields } from './dms-intake-review-fields.js';
import {
    guardBannerHtml,
    onGuardClick,
    blockedIdxs,
    initGuard,
    ensureGuardData,
} from './dms-intake-workspace-guard.js';
import { isErpEntry } from './erp-intake.js';
import {
    confirmationErrorMessage,
    confirmIndices,
    convertChipHtml,
    pagesForInvoice,
} from './dms-intake-review-convert.js';
import {
    applyPostingDefault,
    editablePostingItems,
    missingPostingKind,
    selectedPostingDefault,
} from './dms-intake-review-posting.js';
import type { PostingKind } from './dms-intake-review-posting.js';

// 套账不符横幅需要重渲复核屏(归入/保持后横幅状态变化)→ 把 renderReview 交给 guard 模块。
initGuard(renderReview);

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
let viewerApi: ViewerApi | null = null;
let confirmationInFlight = false;

export function renderReview() {
    IV.view = 'review';
    const el = $('dx-s-inv-review');
    if (!el) return;
    if (IV.openIdx == null) IV.openIdx = IV.results.length ? 0 : -1;
    const banner = IV.results.some((r) => r.needs_review)
        ? `<div class="dx-recheck-banner">${esc(t('dxi-needs-review'))}</div>`
        : '';
    const wsguard = guardBannerHtml();
    const items = IV.results.map((r, i) => accItemHtml(r, i)).join('');
    el.innerHTML = banner + wsguard + barHtml() + `<div class="dx-acc">${items}</div>` + footHtml();
    showStepInv(3, 'dx-s-inv-review');
    bindPostingDefault();
    bindOpenViewer();
    void ensureGuardData(); // 首次进入复核:拉账套列表 → 有错配时补渲出横幅
}

function barHtml(): string {
    return (
        '<div class="dx-rv-bar"><div class="dx-rv-bar-t">' +
        `<b>${esc(t('dxi-rev-files-h'))}</b><span>${esc(t('dxi-rev-files-tip'))}</span></div>` +
        '<div class="dx-rv-bar-a">' +
        postingDefaultHtml() +
        `<button class="btn small" id="dx-inv-collapse-all">${esc(t('dxi-rev-collapse-all'))}</button>` +
        `<button class="btn small primary" id="dx-inv-confirm-all">${esc(t('dxi-rev-confirm-all'))}</button>` +
        '</div></div>'
    );
}

function postingDefaultHtml(): string {
    if (!isErpEntry()) return '';
    const items = editablePostingItems(IV.results, IV.confirmed);
    const selected = selectedPostingDefault(items);
    const disabled = items.length ? '' : ' disabled';
    return (
        `<label class="dx-item-default"><span>${esc(t('dxi-item-type'))}</span>` +
        `<select data-iv-posting-default${disabled}>` +
        `<option value=""${selected ? '' : ' selected'}>${esc(t('dxi-item-type-batch'))}</option>` +
        `<option value="stock"${selected === 'stock' ? ' selected' : ''}>${esc(t('dxi-item-type-all-stock'))}</option>` +
        `<option value="service"${selected === 'service' ? ' selected' : ''}>${esc(t('dxi-item-type-all-service'))}</option>` +
        '</select></label>'
    );
}

function syncPostingDefault(): void {
    const select = document.querySelector('[data-iv-posting-default]') as HTMLSelectElement | null;
    if (select)
        select.value = selectedPostingDefault(editablePostingItems(IV.results, IV.confirmed));
}

function bindPostingDefault(): void {
    const select = document.querySelector('[data-iv-posting-default]') as HTMLSelectElement | null;
    select?.addEventListener('change', () => {
        if (!['stock', 'service'].includes(select.value)) return;
        applyPostingDefault(
            editablePostingItems(IV.results, IV.confirmed),
            select.value as PostingKind
        );
        renderReview();
    });
    document.querySelectorAll('.dx-item-type').forEach((itemSelect) => {
        itemSelect.addEventListener('change', () => window.setTimeout(syncPostingDefault, 0));
    });
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
    const confirmed = IV.confirmed.has(i);
    const w = fileWarns(r);
    const sub =
        (r.invoice_count > 1
            ? esc(t('dxi-multi').replace('{n}', String(r.invoice_count)))
            : esc(t(w ? 'dxi-rev-only' : 'dxi-rev-noneed'))) +
        (r.from_cache ? ' · ' + esc(t('cache-hit-badge')) : '');
    const row =
        `<div class="dx-acc-row" data-iv-toggle="${i}">` +
        `<div class="dx-file-ic">${esc(ext(r.filename))}</div>` +
        `<div class="dx-file-c"><b>${esc(r.filename)}</b><span>${sub} · ${esc(t(confirmed ? 'dxi-rev-confirmed' : 'dxi-rev-editable'))}</span></div>` +
        statusHtml(r, i) +
        `<button class="dx-acc-btn" data-iv-toggle="${i}">${esc(t(open ? 'dxi-rev-collapse' : 'dxi-rev-view'))}</button></div>`;
    const panel = open ? accPanelHtml(r, i) : '';
    return `<div class="dx-acc-item${open ? ' open' : ''}" data-acc="${i}">${row}${panel}</div>`;
}

function accPanelHtml(r: IvResult, i: number): string {
    const locked = IV.confirmed.has(i);
    const groups = r.invoices.map((inv, ii) => invoiceGroupHtml(i, ii, inv)).join('');
    return (
        '<div class="dx-acc-panel"><div class="dx-acc-top"><div>' +
        `<b>${esc(r.filename)} · ${esc(t('dxi-rev-h'))}</b>` +
        `<span class="dx-acc-tip">${esc(t('dxi-rev-panel-tip'))}</span></div></div>` +
        `<div class="dx-rgrid"><div class="dx-fields">${groups}${fieldsFootHtml(locked)}</div>` +
        imageCardHtml(r) +
        '</div></div>'
    );
}

function invoiceGroupHtml(fi: number, ii: number, inv: IvInvoice): string {
    const locked = IV.confirmed.has(fi);
    const warns = warnFields(inv.fields);
    if (inv.fmtWarn) warns.add('invoice_number'); // 格式偏离多数派 → 标黄该张发票号
    const fmtChip = inv.fmtWarn
        ? `<span class="dx-inv-fmtwarn">${esc(t('dxi-fmt-warn'))}</span>`
        : '';
    const label =
        inv.total > 1
            ? esc(t('dxi-inv-no').replace('{i}', String(inv.idx)).replace('{n}', String(inv.total)))
            : '';
    const walkin =
        isAnonBuyerDoc(inv.fields) && !inv.fields.buyer_name && !inv.fields.buyer_tax
            ? `<span class="dx-badge blue">${esc(t('rev-walkin-badge'))}</span>`
            : '';
    const headInner = label + fmtChip + walkin + convertChipHtml(inv.history_id);
    const head = headInner ? `<div class="dx-inv-head">${headInner}</div>` : '';
    const cell = ([k, lk]: [string, string]) => {
        const warn = warns.has(k) ? ' warn' : '';
        // 旧记录/文字层来源没有 date_raw → 回落已归一的 date,不让格子空着
        const raw = k === 'date_raw' ? (inv.fields.date_raw ?? inv.fields.date) : inv.fields[k];
        const v = String(raw ?? '');
        return (
            `<div class="dx-rv${warn}"><label>${esc(t(lk))}</label>` +
            `<input class="dx-rv-in" data-iv-field="${fi}:${ii}:${esc(k)}" value="${esc(v)}"${locked ? ' disabled' : ''}></div>`
        );
    };
    const core = revCore(inv.fields).map(cell).join('');
    const more = revMore(inv.fields).map(cell).join('');
    // 包一层:右侧查看器要靠它知道"用户正在核对第几张",才能翻到那张票所在的物理页。
    // 分组号同时给反向高亮用(手动翻页 → 点亮该页第一张)。
    //
    // 明细表不放进 .dx-extra:它是核对时最常看的东西(数量单价对不对、商品名会不会建错档),
    // 藏在「展开全部字段」后面等于没有。折叠区只留补充字段(总额/对手方/预扣税)。
    return (
        `<div class="dx-inv-grp" data-inv-grp="${ii}" data-inv-page="${invPage(inv)}">` +
        head +
        `<div class="dx-review-grid">${core}</div>` +
        itemsTableHtml(fi, ii, inv, locked) +
        `<div class="dx-extra"><div class="dx-review-grid">${more}</div></div></div>`
    );
}

// 该张发票在原 PDF 的物理页。后端 invoice_grouper 一直算着 page_indices 并透到前端,
// 但从来没人读 —— 查看器因此固定停在第一页,三张票共用一个画面(2026-07-25 用户实测)。
function invPage(inv: IvInvoice): number {
    return inv.pageIndices?.length ? inv.pageIndices[0] : inv.idx;
}

// 明细四列各归各位:此前「金额」列取的是 price(单价),16×55=880 的票在那列显示 55,
// 会计对不上票面只会以为我们读错了。走库存路时这几格还是建 STMAS 主档的依据,故可编辑 ——
// 名字读歪一个字就是一个永久垃圾档(Express 删单不删档)。
const ITEM_COLS: Array<[string, string]> = [
    ['name', 'dxi-rev-item-name'],
    ['qty', 'dxi-rev-item-qty'],
    ['price', 'dxi-rev-item-price'],
    ['subtotal', 'dxi-rev-item-amt'],
];

function itemsTableHtml(fi: number, ii: number, inv: IvInvoice, locked: boolean): string {
    const items = (inv.fields.items as Array<Dict>) || [];
    if (!Array.isArray(items) || !items.length) return '';
    const rows = items
        .map((it, ti) => {
            const tds = ITEM_COLS.map(([k], ci) => {
                const v = String(it[k] ?? (k === 'subtotal' ? (it.amount ?? '') : ''));
                return (
                    `<td${ci ? ' class="r"' : ''}><input class="dx-item-in"` +
                    ` data-iv-item="${fi}:${ii}:${ti}:${k}" value="${esc(v)}"${locked ? ' disabled' : ''}></td>`
                );
            }).join('');
            const postingKind = String(it.posting_kind || '');
            const typeCell = isErpEntry()
                ? `<td><select class="dx-item-type" data-iv-item="${fi}:${ii}:${ti}:posting_kind"${locked ? ' disabled' : ''}><option value="">${esc(t('dxi-item-type-pick'))}</option><option value="stock"${postingKind === 'stock' ? ' selected' : ''}>${esc(t('dxi-posting-stock-t'))}</option><option value="service"${postingKind === 'service' ? ' selected' : ''}>${esc(t('dxi-posting-service-t'))}</option></select></td>`
                : '';
            return `<tr>${tds}${typeCell}</tr>`;
        })
        .join('');
    const ths =
        ITEM_COLS.map(([, lk], ci) => `<th${ci ? ' class="r"' : ''}>${esc(t(lk))}</th>`).join('') +
        (isErpEntry() ? `<th>${esc(t('dxi-item-type'))}</th>` : '');
    return `<table class="dx-item-tbl"><thead><tr>${ths}</tr></thead><tbody>${rows}</tbody></table>`;
}

function fieldsFootHtml(locked: boolean): string {
    if (locked)
        return `<div class="dx-fields-foot"><div class="dx-note">${esc(t('dxi-rev-confirmed'))}</div></div>`;
    return (
        `<div class="dx-fields-foot"><div class="dx-note">${esc(t('dxi-rev-hint'))}</div>` +
        '<div class="dx-fields-foot-a">' +
        `<button class="btn small dx-save-one">${esc(t('dxi-rev-save'))}</button>` +
        `<button class="btn small primary dx-confirm-one">${esc(t('dxi-rev-next'))}</button>` +
        (isErpEntry()
            ? `<button class="btn small danger" data-dx-action="discard">${esc(t('dxi-discard'))}</button>`
            : '') +
        '</div></div>'
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
    if (IV.confirmed.has(IV.openIdx)) {
        showToast(t('dxi-err-formal-locked'), 'error');
        return;
    }
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
                        body: JSON.stringify({ pages: pagesForInvoice(r, iv) }),
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
    if (onGuardClick(tg)) return true;
    const tog = tg.closest('[data-iv-toggle]') as HTMLElement | null;
    if (tog) {
        const i = +tog.dataset.ivToggle!;
        IV.openIdx = IV.openIdx === i ? -1 : i;
        renderReview();
        return true;
    }
    if (tg.closest('#dx-inv-collapse-all')) {
        IV.openIdx = -1;
        renderReview();
        return true;
    }
    if (tg.closest('.dx-save-one')) {
        void saveOpenFileEdits(tg.closest('.dx-save-one'));
        return true;
    }
    if (tg.closest('.dx-confirm-one')) {
        if (IV.openIdx >= 0) {
            const idx = IV.openIdx;
            if (IV.confirmed.has(idx)) return true;
            if (isErpEntry() && missingPostingKind(IV.results[idx])) {
                showToast(t('dxi-item-type-required'), 'error');
                return true;
            }
            void confirmAndRender([idx], idx);
        }
        return true;
    }
    if (tg.closest('[data-dx-action="discard"]')) {
        void discardOpenFile();
        return true;
    }
    if (tg.closest('#dx-inv-confirm-all')) {
        // 套账不符且未处理的文件不进「确认全部」—— 确认=落进当前账本,错账本里多落一张
        // 就多污染一张报表。单文件「确认并继续」不拦(用户逐张看过了,是显式决定)。
        const blocked = blockedIdxs();
        const idxs = IV.results.reduce<number[]>((acc, r, i) => {
            if (passable(r) && !blocked.has(i) && (!isErpEntry() || !missingPostingKind(r)))
                acc.push(i);
            return acc;
        }, []);
        if (
            isErpEntry() &&
            idxs.length < IV.results.filter((r, i) => passable(r) && !blocked.has(i)).length
        ) {
            showToast(t('dxi-item-type-required'), 'error');
            return true;
        }
        void confirmAndRender(idxs, -1);
        return true;
    }
    return false;
}

async function confirmAndRender(idxs: number[], current: number): Promise<void> {
    if (confirmationInFlight) return;
    confirmationInFlight = true;
    try {
        const ok = await confirmIndices(idxs);
        if (!ok && isErpEntry()) {
            renderReview();
            showToast(confirmationErrorMessage(), 'error');
            return;
        }
        if (current >= 0) IV.openIdx = nextUnconfirmed(current);
        renderReview();
        showToast(t(current >= 0 ? 'dxi-rev-confirmed-toast' : 'dxi-rev-confirmed-all'), 'success');
    } finally {
        confirmationInFlight = false;
    }
}

async function discardOpenFile(): Promise<void> {
    const r = IV.results[IV.openIdx];
    if (!r) return;
    const ids = r.history_ids.filter(Boolean);
    const ok = window.pearnlyConfirm
        ? await window.pearnlyConfirm(t('dxi-discard-confirm'))
        : window.confirm(t('dxi-discard-confirm'));
    if (!ok) return;
    try {
        const response = await fetch('/api/erp/intake/discard', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ history_ids: ids }),
        });
        if (!response.ok) throw new Error('discard_failed');
        const removed = IV.openIdx;
        IV.results.splice(removed, 1);
        IV.confirmed = new Set(
            Array.from(IV.confirmed)
                .filter((index) => index !== removed)
                .map((index) => (index > removed ? index - 1 : index))
        );
        IV.openIdx = Math.min(removed, IV.results.length - 1);
        renderReview();
    } catch {
        showToast(t('dxi-discard-fail'), 'error');
    }
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
    viewerApi = null;
    if (IV.openIdx < 0) return;
    const panel = openPanel();
    const r = IV.results[IV.openIdx];
    if (!panel || !r) return;
    const pane = panel.querySelector('.dx-imgcard') as HTMLElement | null;
    if (pane?.querySelector('.pv-viewer')) {
        viewerCleanup = mountImageViewer(pane, r.history_ids[0] || null, {
            onReady: (api) => {
                viewerApi = api;
            },
            // 手动翻页 → 点亮该页第一张发票。跟随是双向的,否则翻到第 2 页后左侧
            // 仍高亮着第 1 张,用户不知道自己在核对哪一张。
            // 但同一页装着两张票时不能抢:聚焦第 2 张会触发 goToPage(同一页)→ 这里若无脑
            // 点亮"该页第一张",高亮当场被夺回第 1 张(实测同页多票必现)。
            onPage: (p) => {
                const cur = panel.querySelector('[data-inv-grp].active') as HTMLElement | null;
                if (cur && Number(cur.dataset.invPage || 0) === p) return;
                markActive(panel, groupOnPage(panel, p));
            },
        });
    }
    // focusin 而非 click:键盘 Tab 走到下一张的字段时同样该跟随。
    panel.addEventListener('focusin', onFieldFocus);
}

function onFieldFocus(e: Event) {
    const grp = (e.target as HTMLElement)?.closest?.('[data-inv-grp]') as HTMLElement | null;
    const panel = openPanel();
    if (!grp || !panel) return;
    markActive(panel, grp);
    const p = Number(grp.dataset.invPage || 0);
    if (p > 0) viewerApi?.goToPage(p);
}

function groupOnPage(panel: HTMLElement, page: number): HTMLElement | null {
    const all = Array.from(panel.querySelectorAll('[data-inv-grp]')) as HTMLElement[];
    return all.find((g) => Number(g.dataset.invPage || 0) === page) || null;
}

function markActive(panel: HTMLElement, grp: HTMLElement | null): void {
    panel
        .querySelectorAll('[data-inv-grp]')
        .forEach((g) => g.classList.toggle('active', g === grp));
}
