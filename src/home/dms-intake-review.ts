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
import type { ViewerApi } from './image-viewer.js';

// 复核预览字段(复用 OCR 抽屉字段标签键)
const REV_REST: Array<[string, string]> = [
    ['invoice_number', 'drawer-lbl-invoice'],
    // 票面原文(泰国票面印佛历)· 保存走 PUT /api/history 由后端按它反推公历 date
    ['date_raw', 'drawer-lbl-date'],
    ['subtotal', 'drawer-lbl-subtotal'],
    ['vat', 'drawer-lbl-vat'],
];

// 对手方在哪一侧看方向:销项是买方,进项是卖方。此前写死 seller_*,销项票(回导来的、
// 或税号判成 sales 的)于是"名称/税号空 + 需确认",看着像识别失败,其实数据在 buyer_*。
function partyKeys(f: Dict): { name: string; tax: string; other: string } {
    return String(f.direction || '') === 'sales'
        ? { name: 'buyer_name', tax: 'buyer_tax', other: 'seller_name' }
        : { name: 'seller_name', tax: 'seller_tax', other: 'buyer_name' };
}
function revCore(f: Dict): Array<[string, string]> {
    const p = partyKeys(f);
    return [[p.name, 'drawer-lbl-name'], [p.tax, 'drawer-lbl-tax'], ...REV_REST];
}
function revMore(f: Dict): Array<[string, string]> {
    return [
        ['total_amount', 'drawer-lbl-total'],
        [partyKeys(f).other, 'drawer-lbl-name'],
        ['wht_amount', 'drawer-lbl-wht-amount'],
    ];
}

function warnFields(f: Dict): Set<string> {
    const s = new Set<string>();
    ['invoice_number', partyKeys(f).tax, 'total_amount'].forEach((k) => {
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

// ── 确认 → 正式单据(转换桥)──────────────────────────────────
// 「确认」此前只是纯前端视觉态,后端只翻 ocr_history.staged,不落 purchase_docs/
// sales_documents —— 商品收发存报表读的正是这两张表,于是"确认完"≠"过账完",报表恒空。
// 这里把确认接上真实建账(POST /api/ocr/convert-documents),按 history_id 记住转换结果,
// 就地渲染 chip:四态诚实,跳过原因不吞。
interface ConvertResult {
    status: 'converted' | 'skipped';
    reason?: string;
}
const convertStatus = new Map<string, ConvertResult>();

function activeWorkspaceId(): number | null {
    const w = window as unknown as { getActiveWorkspaceClientId?: () => number | null };
    return typeof w.getActiveWorkspaceClientId === 'function'
        ? w.getActiveWorkspaceClientId()
        : null;
}

export async function convertHistoryIds(ids: string[]): Promise<void> {
    const pending = Array.from(new Set(ids.filter((id) => id && !convertStatus.has(id))));
    if (!pending.length) return;
    const ws = activeWorkspaceId();
    if (!ws) {
        pending.forEach((id) =>
            convertStatus.set(id, { status: 'skipped', reason: 'no_workspace' })
        );
        return;
    }
    try {
        const r = await fetch('/api/ocr/convert-documents', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ history_ids: pending, workspace_client_id: ws }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(String(r.status));
        (d.converted || []).forEach((c: { history_id: string }) =>
            convertStatus.set(c.history_id, { status: 'converted' })
        );
        (d.skipped || []).forEach((s: { history_id: string; reason: string }) =>
            convertStatus.set(s.history_id, { status: 'skipped', reason: s.reason })
        );
    } catch {
        pending.forEach((id) => convertStatus.set(id, { status: 'skipped', reason: 'error' }));
    }
}

// 已确认文件的全部下标(供 invoice-submit 进第4步前兜底补转换 · confirmIndices 的入参)。
export function confirmedIndices(): number[] {
    const idxs: number[] = [];
    IV.results.forEach((_r, i) => {
        if (IV.confirmed.has(i)) idxs.push(i);
    });
    return idxs;
}

// 单一入口:把 idxs 标记为已确认 + 收集其 history_ids + 提交转换桥(convertHistoryIds
// 内部按 history_id 去重,已转换过的不重复调用)。此前「单张确认」「确认全部」「步骤4 兜底」
// 三处各写一遍"IV.confirmed.add + 收集 ids + convertHistoryIds",口径一旦漂移就是某条路
// 确认了却没转换。不在这里重渲——三个调用点各自的后续动作不同(单张要挪到下一条待办、
// confirm-all 全部展开重排、enterSubmit 兜底则接着进第4步),交回调用方处理。
export async function confirmIndices(idxs: number[]): Promise<void> {
    const ids: string[] = [];
    idxs.forEach((i) => {
        const r = IV.results[i];
        if (!r) return;
        IV.confirmed.add(i);
        ids.push(...r.history_ids);
    });
    if (ids.length) await convertHistoryIds(ids);
}

// convert_histories 的跳过原因 → i18n 键(导出供 dms-intake-batch-submit.ts 复用,不
// 另造一份文案 · duplicate/already_converted 不进这张表,走下面 convertChipHtml 的专属分支)。
export const CONVERT_REASON_KEY: Record<string, string> = {
    no_items: 'dxi-conv-r-no-items',
    no_direction: 'dxi-conv-r-no-direction',
    no_workspace: 'dxi-conv-r-no-workspace',
    no_doc_no: 'dxi-conv-r-no-doc-no',
    no_date: 'dxi-conv-r-no-date',
    not_found: 'dxi-conv-r-error',
};

function convertChipHtml(historyId: string | null): string {
    if (!historyId) return '';
    const st = convertStatus.get(historyId);
    if (!st) return '';
    if (st.status === 'converted')
        return `<span class="dx-badge green">${esc(t('dxi-conv-done'))}</span>`;
    if (st.reason === 'duplicate' || st.reason === 'already_converted')
        return `<span class="dx-badge blue">${esc(t('dxi-conv-dup'))}</span>`;
    const reasonKey = CONVERT_REASON_KEY[st.reason || ''] || 'dxi-conv-r-error';
    const phrase = t(reasonKey);
    return `<span class="dx-badge amber">${esc(t('dxi-conv-skip').replace('{reason}', phrase))}</span>`;
}

// 原图查看器复用识别记录/异常同款共享件(image-viewer.ts · 按物理页翻 + 缩放/旋转/全屏)·
// 同一刻只一个面板挂载,重渲先清旧实例。
let viewerCleanup: (() => void) | null = null;
let viewerApi: ViewerApi | null = null;

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
    const headInner = label + fmtChip + convertChipHtml(inv.history_id);
    const head = headInner ? `<div class="dx-inv-head">${headInner}</div>` : '';
    const cell = ([k, lk]: [string, string]) => {
        const warn = warns.has(k) ? ' warn' : '';
        // 旧记录/文字层来源没有 date_raw → 回落已归一的 date,不让格子空着
        const raw = k === 'date_raw' ? (inv.fields.date_raw ?? inv.fields.date) : inv.fields[k];
        const v = String(raw ?? '');
        return (
            `<div class="dx-rv${warn}"><label>${esc(t(lk))}</label>` +
            `<input class="dx-rv-in" data-iv-field="${fi}:${ii}:${esc(k)}" value="${esc(v)}"></div>`
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
        itemsTableHtml(fi, ii, inv) +
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

function itemsTableHtml(fi: number, ii: number, inv: IvInvoice): string {
    const items = (inv.fields.items as Array<Dict>) || [];
    if (!Array.isArray(items) || !items.length) return '';
    const rows = items
        .map((it, ti) => {
            const tds = ITEM_COLS.map(([k], ci) => {
                const v = String(it[k] ?? (k === 'subtotal' ? (it.amount ?? '') : ''));
                return (
                    `<td${ci ? ' class="r"' : ''}><input class="dx-item-in"` +
                    ` data-iv-item="${fi}:${ii}:${ti}:${k}" value="${esc(v)}"></td>`
                );
            }).join('');
            return `<tr>${tds}</tr>`;
        })
        .join('');
    const ths = ITEM_COLS.map(
        ([, lk], ci) => `<th${ci ? ' class="r"' : ''}>${esc(t(lk))}</th>`
    ).join('');
    return `<table class="dx-item-tbl"><thead><tr>${ths}</tr></thead><tbody>${rows}</tbody></table>`;
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
    if (tg.closest('.dx-save-one')) {
        void saveOpenFileEdits(tg.closest('.dx-save-one'));
        return true;
    }
    if (tg.closest('.dx-confirm-one')) {
        if (IV.openIdx >= 0) {
            const idx = IV.openIdx;
            const done = confirmIndices([idx]);
            IV.openIdx = nextUnconfirmed(idx);
            renderReview();
            showToast(t('dxi-rev-confirmed-toast'), 'success');
            void done.then(renderReview);
        }
        return true;
    }
    if (tg.closest('#dx-inv-confirm-all')) {
        const idxs = IV.results.reduce<number[]>((acc, r, i) => {
            if (passable(r)) acc.push(i);
            return acc;
        }, []);
        const done = confirmIndices(idxs);
        renderReview();
        showToast(t('dxi-rev-confirmed-all'), 'success');
        void done.then(renderReview);
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
