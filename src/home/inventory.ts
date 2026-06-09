// POS 项目 · PO-A4 库存后台主页(屏7)· window.loadInventoryPage
// 视觉照搬概念稿 桌面/Pearnly_POS_UI预览/07-库存后台.html(09 §H):DOM 结构逐字移植到 .invp 作用域,
// 仅改三处 —— ① 假数据→invApi(04 §4 契约)② 写死文案→i18n(4语)③ 补四态(07)。
// 按钮→动作 对齐 05 矩阵:盘点/调拨/导出/入库 + 搜索 + 低库存筛选。
/* global t, escapeHtml, showToast */
import {
    invApi,
    activeWsId,
    localizedName,
    fmtMoney,
    fmtQty,
    invErrMsg,
    NEAR_EXPIRY_DAYS,
    type InvItem,
    type StockResp,
    type StockFilter,
} from './inventory-common.js';

const IC_PLUS =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';
const IC_SEARCH =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
const IC_BOX =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8"/></svg>';

let resp: StockResp | null = null;
let lowOut = false; // 「只看低库存 / 缺货」开关(client 端组合 low+out · 04 filter 为单值)
let keyword = '';
let searchTimer: number | undefined;

function statusBadge(it: InvItem): string {
    const min = fmtQty(it.min_stock);
    let txt: string;
    if (it.status === 'out') txt = t('inv-st-out');
    else if (it.status === 'low') txt = t('inv-st-low') + ' (≤' + min + ')';
    else txt = t('inv-st-ok');
    return `<span class="st ${it.status}">● ${escapeHtml(txt)}</span>`;
}

function rowHtml(it: InvItem): string {
    const near = invApi.hasNearExpiry(it, NEAR_EXPIRY_DAYS)
        ? `<span class="exp-dot" title="${escapeHtml(t('inv-near-expiry'))}"></span>`
        : '';
    const qtyBad = it.status === 'out' ? ' bad' : '';
    return `<tr>
        <td><span class="nm"><span class="thumb">${IC_BOX}</span>${escapeHtml(localizedName(it.name))}${near}</span></td>
        <td class="tnum">${escapeHtml(it.barcode || '')}</td>
        <td>${escapeHtml(it.base_unit || '')}</td>
        <td class="num qty${qtyBad}">${fmtQty(it.qty_on_hand)}</td>
        <td class="num">฿${fmtMoney(it.avg_cost)}</td>
        <td>${statusBadge(it)}</td>
    </tr>`;
}

function visibleItems(): InvItem[] {
    if (!resp) return [];
    return lowOut ? resp.items.filter((it) => it.status !== 'ok') : resp.items;
}

function tbodyHtml(): string {
    const list = visibleItems();
    if (!list.length) {
        const msg = keyword || lowOut ? t('inv-empty-filtered') : t('inv-empty');
        return `<tr><td colspan="6"><div class="inv-state">${IC_BOX}<div>${escapeHtml(msg)}</div></div></td></tr>`;
    }
    return list.map(rowHtml).join('');
}

function skeletonRows(): string {
    let r = '';
    for (let i = 0; i < 5; i++)
        r += `<tr>${'<td><div class="inv-skel"></div></td>'.repeat(6)}</tr>`;
    return r;
}

function bodyHtml(): string {
    const s = resp ? resp.summary : { sku_count: 0, stock_value: '0', low_count: 0, out_count: 0 };
    return `<div class="stats">
        <div class="stat"><div class="l">${escapeHtml(t('inv-stat-sku'))}</div><div class="v tnum">${s.sku_count}</div></div>
        <div class="stat"><div class="l">${escapeHtml(t('inv-stat-value'))}</div><div class="v tnum">฿${fmtMoney(s.stock_value)}</div></div>
        <div class="stat"><div class="l">${escapeHtml(t('inv-stat-low'))}</div><div class="v warn tnum">${s.low_count}</div></div>
        <div class="stat"><div class="l">${escapeHtml(t('inv-stat-out'))}</div><div class="v bad tnum">${s.out_count}</div></div>
    </div>
    <div class="bar">
        <div class="search">${IC_SEARCH}<input id="inv-search" value="${escapeHtml(keyword)}" placeholder="${escapeHtml(t('inv-search-ph'))}"></div>
        <div class="chip${lowOut ? ' on' : ''}" id="inv-chip-lowout">${escapeHtml(t('inv-chip-lowout'))}</div>
        <div class="chip${lowOut ? '' : ' on'}" id="inv-chip-all">${escapeHtml(t('inv-chip-all'))}</div>
    </div>
    <table>
        <thead><tr>
            <th>${escapeHtml(t('inv-col-product'))}</th>
            <th>${escapeHtml(t('inv-col-barcode'))}</th>
            <th>${escapeHtml(t('inv-col-unit'))}</th>
            <th class="num">${escapeHtml(t('inv-col-onhand'))}</th>
            <th class="num">${escapeHtml(t('inv-col-cost'))}</th>
            <th>${escapeHtml(t('inv-col-status'))}</th>
        </tr></thead>
        <tbody id="inv-tbody">${tbodyHtml()}</tbody>
    </table>`;
}

function shellHtml(): string {
    return `<div class="invp">
        <div class="ph">
            <div class="t">${escapeHtml(t('inv-title'))}</div>
            <div class="acts">
                <button class="btn" id="inv-btn-count">${escapeHtml(t('inv-act-count'))}</button>
                <button class="btn primary" id="inv-btn-in">${IC_PLUS}${escapeHtml(t('inv-act-in'))}</button>
                <div class="more">
                    <button class="btn more-btn" id="inv-btn-more" aria-haspopup="true" aria-expanded="false">⋯</button>
                    <div class="menu" id="inv-more-menu" hidden>
                        <div class="mi" id="inv-btn-export" role="button" tabindex="0">${escapeHtml(t('inv-act-export'))}</div>
                        <div class="mi" id="inv-btn-transfer" role="button" tabindex="0">${escapeHtml(t('inv-act-transfer'))}</div>
                    </div>
                </div>
            </div>
        </div>
        <div id="inv-body"></div>
    </div>`;
}

function setBody(html: string) {
    const b = document.getElementById('inv-body');
    if (b) b.innerHTML = html;
}

function rerenderRows() {
    const tb = document.getElementById('inv-tbody');
    if (tb) tb.innerHTML = tbodyHtml();
}

function exportCsv() {
    const list = visibleItems();
    const head = [
        t('inv-col-product'),
        t('inv-col-barcode'),
        t('inv-col-unit'),
        t('inv-col-onhand'),
        t('inv-col-cost'),
        t('inv-col-status'),
    ];
    const rows = list.map((it) => [
        localizedName(it.name),
        it.barcode || '',
        it.base_unit || '',
        fmtQty(it.qty_on_hand),
        fmtMoney(it.avg_cost),
        t('inv-st-' + it.status),
    ]);
    const esc = (v: string) => '"' + String(v).replace(/"/g, '""') + '"';
    const csv = [head, ...rows].map((r) => r.map(esc).join(',')).join('\r\n');
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'inventory.csv';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast(t('inv-export-ok'), 'success');
}

function bindBody() {
    const search = document.getElementById('inv-search') as HTMLInputElement | null;
    if (search)
        search.oninput = () => {
            keyword = search.value;
            clearTimeout(searchTimer);
            searchTimer = window.setTimeout(refresh, 250);
        };
    const chipLow = document.getElementById('inv-chip-lowout');
    if (chipLow)
        chipLow.onclick = () => {
            lowOut = true;
            setBody(bodyHtml());
            bindBody();
        };
    const chipAll = document.getElementById('inv-chip-all');
    if (chipAll)
        chipAll.onclick = () => {
            lowOut = false;
            setBody(bodyHtml());
            bindBody();
        };
}

// 搜索:服务端按 q 取 → 只刷表格行,不重渲整页,保住搜索框焦点。
async function refresh() {
    const wsId = activeWsId();
    if (wsId == null) return;
    try {
        resp = await invApi.getStock(wsId, currentFilter(), keyword);
    } catch (_) {
        return;
    }
    rerenderRows();
}

function currentFilter(): StockFilter {
    return 'all'; // 低库存/缺货组合在 client 端做(见 visibleItems);搜索仍走全量
}

// 库存按账套(workspace_client_id)隔离 · 个人模式/未选账套 → 引导先选账套(不空请求 422)。
function needWorkspaceHtml(): string {
    return `<div class="inv-state">${IC_BOX}<div>${escapeHtml(t('inv-need-workspace'))}</div>
        <button class="btn primary" id="inv-pick-ws">${escapeHtml(t('inv-pick-workspace'))}</button></div>`;
}

async function load() {
    const wsId = activeWsId();
    if (wsId == null) {
        setBody(needWorkspaceHtml());
        const pick = document.getElementById('inv-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => load())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    setBody(loadingShell());
    try {
        resp = await invApi.getStock(wsId, currentFilter(), keyword);
        setBody(bodyHtml());
        bindBody();
    } catch (e) {
        setBody(
            `<div class="inv-state error">${escapeHtml(invErrMsg(e, 'inv-error'))}<br><button class="btn" id="inv-retry">${escapeHtml(t('inv-retry'))}</button></div>`
        );
        const retry = document.getElementById('inv-retry');
        if (retry) retry.onclick = () => load();
    }
}

function loadingShell(): string {
    return `<table><thead><tr>
        <th>${escapeHtml(t('inv-col-product'))}</th><th>${escapeHtml(t('inv-col-barcode'))}</th>
        <th>${escapeHtml(t('inv-col-unit'))}</th><th class="num">${escapeHtml(t('inv-col-onhand'))}</th>
        <th class="num">${escapeHtml(t('inv-col-cost'))}</th><th>${escapeHtml(t('inv-col-status'))}</th>
    </tr></thead><tbody>${skeletonRows()}</tbody></table>`;
}

window.loadInventoryPage = function () {
    const sec = document.getElementById('page-inventory');
    if (!sec) return;
    if (sec.dataset.invInit !== '1') {
        sec.innerHTML = shellHtml();
        sec.dataset.invInit = '1';
        bindShell();
    }
    load();
};

function bindShell() {
    const inBtn = document.getElementById('inv-btn-in');
    if (inBtn) inBtn.onclick = () => window.openInventoryIn?.();
    const countBtn = document.getElementById('inv-btn-count');
    if (countBtn) countBtn.onclick = () => window.openInventoryCount?.();
    const exportBtn = document.getElementById('inv-btn-export');
    if (exportBtn) exportBtn.onclick = () => exportCsv();
    const transferBtn = document.getElementById('inv-btn-transfer');
    // 调拨 = 多仓功能 · 05 标「后续」· 单仓阶段给明确提示,不做死按钮也不做假功能。
    if (transferBtn) transferBtn.onclick = () => showToast(t('inv-transfer-soon'), 'info');
    // §4-bis 渐进披露:⋯ 更多菜单(导出/调拨)· 点外部关闭。
    const moreBtn = document.getElementById('inv-btn-more');
    const moreMenu = document.getElementById('inv-more-menu');
    if (moreBtn && moreMenu) {
        moreBtn.onclick = (e) => {
            e.stopPropagation();
            const opening = moreMenu.hasAttribute('hidden');
            moreMenu.toggleAttribute('hidden', !opening);
            moreBtn.setAttribute('aria-expanded', String(opening));
        };
        document.addEventListener('click', () => {
            if (!moreMenu.hasAttribute('hidden')) {
                moreMenu.setAttribute('hidden', '');
                moreBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }
}

// 入库/盘点弹窗提交成功后回流刷新列表。
window.reloadInventory = function () {
    load();
};

// 切账套重载已统一收口到 core-boot 全局 pearnly:workspace-changed → reloadCurrentRoute。
