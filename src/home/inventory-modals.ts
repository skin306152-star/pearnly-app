// POS 项目 · PO-A4 库存后台 · 入库 / 盘点弹窗
// 概念稿屏7 只画了列表;入库/盘点为「补交互」,用 .modal(D1 闸禁新增 .drawer),沿用 home-41 同套令牌。
// 接 04 §4:POST /api/inventory/in、POST /api/inventory/count(带 workspace_client_id)。表单四态:提交转圈 + inline 错误码本地化。
/* global t, escapeHtml, showToast */
import { invApi, activeWsId, invErrMsg, type InLine, type CountLine } from './inventory-common.js';

const IC_X =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>';

let rowSeq = 0;

function productOptions(): string {
    return invApi
        .products()
        .map((p) => `<option value="${escapeHtml(p.product_id)}">${escapeHtml(p.name)}</option>`)
        .join('');
}

function inRowHtml(): string {
    const id = 'invr-' + rowSeq++;
    // 批号/效期默认藏起来:只有选中的商品在商品资料里勾了「批次管理」才显(applyBatchVisibility)。
    // 普通百货不碰批次 → 货进散装桶、收银台直接可卖(否则批次桶货够不着 = 看得见卖不出)。
    return `<div class="inv-frow" data-row="${id}">
        <select class="inv-field" data-k="product_id"><option value="">—</option>${productOptions()}</select>
        <input class="inv-field" data-k="qty" type="number" min="0" step="0.001" placeholder="0">
        <input class="inv-field" data-k="unit_cost" type="number" min="0" step="0.01" placeholder="0.00">
        <span style="display:flex;gap:6px;align-items:center">
            <span class="inv-batchcell" data-batchcell style="display:none;gap:6px;align-items:center;flex:1">
                <input class="inv-field" data-k="batch_no" placeholder="${escapeHtml(t('inv-f-batch'))}">
                <input class="inv-field" data-k="expiry_date" type="date">
            </span>
            <button type="button" class="inv-rowx" data-rowx="${id}" aria-label="${escapeHtml(t('inv-row-remove'))}">×</button>
        </span>
    </div>`;
}

function productById(id: string) {
    return invApi.products().find((p) => p.product_id === id) || null;
}

// 收货行:按选中商品是否批次品显隐批号/效期;非批次品同时清空,确保不发批号(不落批次桶)。
function applyBatchVisibility(row: HTMLElement) {
    const cell = row.querySelector<HTMLElement>('[data-batchcell]');
    if (!cell) return;
    const sel = row.querySelector<HTMLSelectElement>('[data-k="product_id"]');
    const prod = sel ? productById(sel.value) : null;
    const show = !!(prod && prod.track_batch);
    cell.style.display = show ? 'flex' : 'none';
    if (!show) cell.querySelectorAll<HTMLInputElement>('input').forEach((i) => (i.value = ''));
}

function bindProductChange(maskId: string) {
    const mask = document.getElementById(maskId);
    if (!mask) return;
    mask.querySelectorAll<HTMLElement>('[data-row]').forEach((row) => {
        const sel = row.querySelector<HTMLSelectElement>('[data-k="product_id"]');
        if (sel) sel.onchange = () => applyBatchVisibility(row);
    });
}

function countRowHtml(): string {
    const id = 'invc-' + rowSeq++;
    return `<div class="inv-frow count" data-row="${id}">
        <select class="inv-field" data-k="product_id"><option value="">—</option>${productOptions()}</select>
        <span style="display:flex;gap:6px;align-items:center">
            <input class="inv-field" data-k="counted_qty" type="number" min="0" step="0.001" placeholder="0">
            <button type="button" class="inv-rowx" data-rowx="${id}" aria-label="${escapeHtml(t('inv-row-remove'))}">×</button>
        </span>
    </div>`;
}

interface ModalCfg {
    maskId: string;
    titleKey: string;
    submitKey: string;
    isCount: boolean;
    labels: string;
    rowFactory: () => string;
}

function modalHtml(cfg: ModalCfg, rows: string): string {
    return `<div class="inv-modal">
        <div class="inv-modal-head">
            <div class="h">${escapeHtml(t(cfg.titleKey))}</div>
            <button type="button" class="inv-modal-x" data-inv-close="${cfg.maskId}">${IC_X}</button>
        </div>
        <div class="inv-modal-body">
            ${cfg.labels}
            <div id="${cfg.maskId}-rows">${rows}</div>
            <button type="button" class="inv-addrow" data-inv-add="${cfg.maskId}">+ ${escapeHtml(t('inv-add-row'))}</button>
            <div class="inv-merr" id="${cfg.maskId}-err"></div>
        </div>
        <div class="inv-modal-foot">
            <button type="button" class="inv-mbtn" data-inv-close="${cfg.maskId}">${escapeHtml(t('inv-cancel'))}</button>
            <button type="button" class="inv-mbtn primary" id="${cfg.maskId}-submit">${escapeHtml(t(cfg.submitKey))}</button>
        </div>
    </div>`;
}

const IN_LABELS = () =>
    `<div class="inv-flabels"><span>${escapeHtml(t('inv-col-product'))}</span><span>${escapeHtml(t('inv-f-qty'))}</span><span>${escapeHtml(t('inv-f-cost'))}</span><span>${escapeHtml(t('inv-f-batch-exp'))}</span></div>`;

const COUNT_LABELS = () =>
    `<div class="inv-flabels count"><span>${escapeHtml(t('inv-col-product'))}</span><span>${escapeHtml(t('inv-f-counted'))}</span></div>`;

function collectRows(maskId: string): Record<string, string>[] {
    const wrap = document.getElementById(maskId + '-rows');
    if (!wrap) return [];
    const out: Record<string, string>[] = [];
    wrap.querySelectorAll<HTMLElement>('[data-row]').forEach((row) => {
        const rec: Record<string, string> = {};
        row.querySelectorAll<HTMLInputElement | HTMLSelectElement>('[data-k]').forEach((f) => {
            rec[f.dataset.k!] = f.value.trim();
        });
        out.push(rec);
    });
    return out;
}

function showErr(maskId: string, msg: string) {
    const el = document.getElementById(maskId + '-err');
    if (el) el.textContent = msg;
}

function openModal(cfg: ModalCfg) {
    const mask = document.getElementById(cfg.maskId);
    if (!mask) return;
    rowSeq = 0;
    mask.innerHTML = modalHtml(cfg, cfg.rowFactory() + cfg.rowFactory());
    mask.classList.add('show');
    mask.querySelectorAll<HTMLElement>('[data-inv-close]').forEach((b) => {
        b.onclick = () => closeModal(cfg.maskId);
    });
    const add = mask.querySelector<HTMLElement>('[data-inv-add]');
    if (add)
        add.onclick = () => {
            const rows = document.getElementById(cfg.maskId + '-rows');
            if (rows) rows.insertAdjacentHTML('beforeend', cfg.rowFactory());
            bindRowX(cfg.maskId);
            bindProductChange(cfg.maskId);
        };
    bindRowX(cfg.maskId);
    bindProductChange(cfg.maskId);
    const submit = document.getElementById(cfg.maskId + '-submit') as HTMLButtonElement | null;
    if (submit) submit.onclick = () => doSubmit(cfg, submit);
    mask.onclick = (e) => {
        if (e.target === mask) closeModal(cfg.maskId);
    };
}

function bindRowX(maskId: string) {
    const mask = document.getElementById(maskId);
    if (!mask) return;
    mask.querySelectorAll<HTMLElement>('[data-rowx]').forEach((x) => {
        x.onclick = () => {
            const row = mask.querySelector(`[data-row="${x.dataset.rowx}"]`);
            if (row) row.remove();
        };
    });
}

function closeModal(maskId: string) {
    const mask = document.getElementById(maskId);
    if (mask) {
        mask.classList.remove('show');
        mask.innerHTML = '';
    }
}

async function doSubmit(cfg: ModalCfg, submit: HTMLButtonElement) {
    showErr(cfg.maskId, '');
    const wsId = activeWsId();
    if (wsId == null) {
        showErr(cfg.maskId, t('inv-need-workspace'));
        return;
    }
    const raw = collectRows(cfg.maskId);
    if (cfg.isCount) {
        const lines: CountLine[] = raw
            .filter((r) => r.product_id && r.counted_qty !== '')
            .map((r) => ({ product_id: r.product_id, counted_qty: r.counted_qty }));
        if (!lines.length) {
            showErr(cfg.maskId, t('inv-err-no-lines'));
            return;
        }
        try {
            await withLoading(submit, () => invApi.postCount(wsId, lines));
            showToast(t('inv-count-ok'), 'success');
            closeModal(cfg.maskId);
            window.reloadInventory?.();
        } catch (e) {
            showErr(cfg.maskId, invErrMsg(e, 'inv-submit-fail'));
        }
        return;
    }
    // 空批号/效期不发(后端 Optional · 空串会把效期当坏日期);单价缺省 0。
    const lines: InLine[] = raw
        .filter((r) => r.product_id && Number(r.qty) > 0)
        .map((r) => {
            const ln: InLine = { product_id: r.product_id, qty: r.qty };
            if (r.unit_cost) ln.unit_cost = r.unit_cost;
            if (r.batch_no) ln.batch_no = r.batch_no;
            if (r.batch_no && r.expiry_date) ln.expiry_date = r.expiry_date;
            return ln;
        });
    if (!lines.length) {
        showErr(cfg.maskId, t('inv-err-no-lines'));
        return;
    }
    submit.disabled = true;
    try {
        await invApi.postIn(wsId, lines);
        showToast(t('inv-in-ok'), 'success');
        closeModal(cfg.maskId);
        window.reloadInventory?.();
    } catch (e) {
        showErr(cfg.maskId, invErrMsg(e, 'inv-submit-fail'));
        submit.disabled = false;
    }
}

window.openInventoryIn = function () {
    openModal({
        maskId: 'inv-in-mask',
        titleKey: 'inv-in-title',
        submitKey: 'inv-in-submit',
        isCount: false,
        labels: IN_LABELS(),
        rowFactory: inRowHtml,
    });
};

window.openInventoryCount = function () {
    openModal({
        maskId: 'inv-count-mask',
        titleKey: 'inv-count-title',
        submitKey: 'inv-count-submit',
        isCount: true,
        labels: COUNT_LABELS(),
        rowFactory: countRowHtml,
    });
};
