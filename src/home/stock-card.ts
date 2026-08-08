// 事务所端 · 商品收发存报表(Stock Card · 路由 stock-card · window.loadStockCard)
// 视觉规格照搬桌面原型 stock-card-prototype-v1.html(Zihao 拍板稿):三段式表头(入绿/出粉/
// 结存紫)+ 商品列表→点行进单品卡 + 负库存整行标红 + 未入账清单 tab + 期初弹窗 + 归并弹窗。
// 令牌换本仓 static/pearnly-ui.css + home-01-base.css,标记/HTML 拼装收在 stock-card-render.ts,
// 取数收在 stock-card-api.ts,期初/归并弹窗收在 stock-card-modals.ts,本文件只管状态编排
// + 事件绑定(单一职责 · <500 行预算)。
/* global t, escapeHtml, showToast */
import { ymdIso } from './format-date.js';
import { listErrorHtml } from './list-error-state.js';
import {
    activeWsId,
    stcGetCard,
    stcGetExcluded,
    stcGetStatus,
    stcGetSummary,
    type StcCardResp,
    type StcExcludedRow,
    type StcProduct,
} from './stock-card-api.js';
import {
    stcDetailFoot,
    stcDetailHead,
    stcDetailRow,
    stcEmptyRow,
    stcExcludedHead,
    stcExcludedRow,
    stcListHead,
    stcListRow,
    stcNeedWorkspaceHtml,
    stcNotEnabledHtml,
    stcSkeletonBody,
} from './stock-card-render.js';
import { openMergeModal, openOpeningsModal } from './stock-card-modals.js';

type ReportSub = 'list' | 'detail';
let currentTab: 'report' | 'excluded' = 'report';
let reportSub: ReportSub = 'list';
let products: StcProduct[] = [];
let excludedRows: StcExcludedRow[] | null = null; // null = 本次日期范围内还没拉过
let excludedCount = 0;
let detailKey: string | null = null;
let detailData: StcCardResp | null = null;
let keyword = '';
let searchTimer: number | undefined;
let dateFrom = '';
let dateTo = '';

function defaultRange(): { from: string; to: string } {
    const now = new Date();
    return { from: ymdIso(new Date(now.getFullYear(), now.getMonth(), 1)), to: ymdIso(now) };
}

function filteredProducts(): StcProduct[] {
    const q = keyword.trim().toLowerCase();
    if (!q) return products;
    return products.filter(
        (p) => p.name.toLowerCase().includes(q) || p.product_id.toLowerCase().includes(q)
    );
}

function esc(s: string): string {
    return escapeHtml(s);
}

// ── 外壳(一次性挂载)──────────────────────────────────────────────
function shellHtml(): string {
    return `<div class="stc">
        <div class="stc-head">
            <div class="stc-head-t">
                <div class="t">${esc(t('stc-title'))}</div>
                <div class="sub">${esc(t('stc-subtitle'))}</div>
            </div>
        </div>
        <div class="stc-toolbar">
            <div class="stc-search"><input id="stc-q" placeholder="${esc(t('stc-search-ph'))}"></div>
            <div class="stc-daterange">
                <label>${esc(t('stc-date-from-label'))} <input type="date" id="stc-date-from"></label>
                <label>${esc(t('stc-date-to-label'))} <input type="date" id="stc-date-to"></label>
                <button type="button" class="btn btn-secondary btn-sm" id="stc-apply">${esc(t('stc-btn-apply'))}</button>
            </div>
            <div class="stc-grow"></div>
            <button type="button" class="btn btn-ghost btn-sm" id="stc-btn-opening">${esc(t('stc-btn-opening'))}</button>
        </div>
        <div class="stc-rules">
            <b>${esc(t('stc-rules-title'))}</b>
            <div class="stc-rules-list">
                <div>${esc(t('stc-rule-opening'))}</div>
                <div>${esc(t('stc-rule-negative'))}</div>
                <div>${esc(t('stc-rule-excluded'))}</div>
            </div>
        </div>
        <div class="stc-tabs">
            <div class="stc-tab on" id="stc-tab-report">${esc(t('stc-tab-report'))}</div>
            <div class="stc-tab" id="stc-tab-excluded">${esc(t('stc-tab-excluded'))}<span class="stc-cnt" id="stc-excluded-cnt">0</span></div>
        </div>
        <div class="stc-card" id="stc-view-list">
            <div class="stc-scroll"><table id="stc-tbl-list"></table></div>
            <p class="stc-hint">${esc(t('stc-list-hint'))}</p>
        </div>
        <div class="stc-card" id="stc-view-detail" style="display:none">
            <button type="button" class="stc-link" id="stc-back">← ${esc(t('stc-back'))}</button>
            <div class="stc-det-top">
                <dl class="stc-info" id="stc-det-info"></dl>
                <div class="stc-formula" id="stc-det-formula"></div>
            </div>
            <div class="stc-scroll"><table id="stc-tbl-detail"></table></div>
        </div>
        <div class="stc-card" id="stc-view-excluded" style="display:none">
            <div class="stc-scroll"><table id="stc-tbl-excluded"></table></div>
            <p class="stc-hint">${esc(t('stc-excluded-hint'))}</p>
        </div>
    </div>`;
}

function setBody(html: string): void {
    const sec = document.getElementById('page-stock-card');
    if (sec) sec.innerHTML = html;
}

// ── tab / 子视图切换(纯 DOM 显隐,不重取数)───────────────────────
function applyViewVisibility(): void {
    const list = document.getElementById('stc-view-list');
    const detail = document.getElementById('stc-view-detail');
    const excluded = document.getElementById('stc-view-excluded');
    if (list) list.style.display = currentTab === 'report' && reportSub === 'list' ? '' : 'none';
    if (detail)
        detail.style.display = currentTab === 'report' && reportSub === 'detail' ? '' : 'none';
    if (excluded) excluded.style.display = currentTab === 'excluded' ? '' : 'none';
    document.getElementById('stc-tab-report')?.classList.toggle('on', currentTab === 'report');
    document.getElementById('stc-tab-excluded')?.classList.toggle('on', currentTab === 'excluded');
}

function switchTab(tab: 'report' | 'excluded'): void {
    currentTab = tab;
    applyViewVisibility();
    if (tab === 'excluded' && excludedRows === null) loadExcluded();
}

function backToList(): void {
    reportSub = 'list';
    applyViewVisibility();
}

// ── 商品列表(报表 tab)────────────────────────────────────────────
function renderListTable(): void {
    const tbl = document.getElementById('stc-tbl-list');
    if (!tbl) return;
    const list = filteredProducts();
    const body = list.length
        ? `<tbody>${list.map(stcListRow).join('')}</tbody>`
        : stcEmptyRow(keyword ? t('stc-empty-filtered') : t('stc-empty-list'));
    tbl.innerHTML = stcListHead() + body;
    tbl.querySelectorAll<HTMLElement>('[data-stc-key]').forEach((row) => {
        row.onclick = (e) => {
            if ((e.target as HTMLElement).closest('[data-stc-merge]')) return; // 归并按钮自己接管
            openDetail(row.dataset.stcKey || '');
        };
    });
    tbl.querySelectorAll<HTMLElement>('[data-stc-merge]').forEach((btn) => {
        btn.onclick = (e) => {
            e.stopPropagation();
            openMergeModal(
                { products, wsId: activeWsId()!, onSaved: loadSummary, defaultDate: dateFrom },
                btn.dataset.stcMerge || ''
            );
        };
    });
}

// shellHtml() 里徽章文案是静态占位「0」,语言切换整壳重渲后必须用这份状态补一次真值,
// 不然刚拉到手的 excludedCount 会被模板里那个「0」悄悄顶掉(真实复现过:切语言后角标归零)。
function syncExcludedBadge(): void {
    const badge = document.getElementById('stc-excluded-cnt');
    if (badge) badge.textContent = String(excludedCount);
}

async function loadSummary(): Promise<void> {
    const tbl = document.getElementById('stc-tbl-list');
    if (tbl) tbl.innerHTML = stcListHead() + stcSkeletonBody(9);
    const wsId = activeWsId();
    if (wsId == null) return;
    try {
        const resp = await stcGetSummary(wsId, dateFrom, dateTo);
        products = resp.products;
        excludedCount = resp.excluded_count;
        excludedRows = null; // 日期范围可能已变,强制未入账清单下次切 tab 重拉
        syncExcludedBadge();
        renderListTable();
        backToList();
    } catch (_) {
        if (tbl) tbl.innerHTML = listErrorHtml('stc-error', 'data-stc-list-retry');
        const retry = tbl?.querySelector<HTMLElement>('[data-stc-list-retry]');
        if (retry) retry.onclick = () => loadSummary();
    }
}

// ── 单品卡(详情)──────────────────────────────────────────────────
function renderDetailInfo(card: StcCardResp): void {
    const info = document.getElementById('stc-det-info');
    if (info)
        info.innerHTML = `
        <dt>${esc(t('stc-info-code'))}</dt><dd>${esc(card.product.product_id || '—')}</dd>
        <dt>${esc(t('stc-info-name'))}</dt><dd>${esc(card.product.name)}</dd>
        <dt>${esc(t('stc-col-unit'))}</dt><dd>${esc(card.product.unit || '—')}</dd>
        <dt>${esc(t('stc-info-method'))}</dt><dd>${esc(t('stc-method-wa'))}</dd>`;
    const formula = document.getElementById('stc-det-formula');
    if (formula)
        formula.innerHTML = `<b>${esc(t('stc-info-method'))}</b><br>${esc(t('stc-formula-wa'))}`;
}

async function openDetail(key: string): Promise<void> {
    if (!key) return;
    detailKey = key;
    reportSub = 'detail';
    applyViewVisibility();
    const tbl = document.getElementById('stc-tbl-detail');
    if (tbl) tbl.innerHTML = stcDetailHead() + stcSkeletonBody(13);
    const info = document.getElementById('stc-det-info');
    if (info) info.innerHTML = '';
    const wsId = activeWsId();
    if (wsId == null) return;
    try {
        detailData = await stcGetCard(wsId, key, dateFrom, dateTo);
        renderDetailInfo(detailData);
        if (tbl)
            tbl.innerHTML =
                stcDetailHead() +
                `<tbody>${detailData.rows.map(stcDetailRow).join('')}</tbody>` +
                stcDetailFoot(detailData);
    } catch (_) {
        if (tbl)
            tbl.innerHTML = stcDetailHead() + listErrorHtml('stc-error', 'data-stc-detail-retry');
        const retry = tbl?.querySelector<HTMLElement>('[data-stc-detail-retry]');
        if (retry) retry.onclick = () => openDetail(key);
    }
}

// ── 未入账清单(tab 懒加载)────────────────────────────────────────
async function loadExcluded(): Promise<void> {
    const tbl = document.getElementById('stc-tbl-excluded');
    if (tbl) tbl.innerHTML = stcExcludedHead() + stcSkeletonBody(5);
    const wsId = activeWsId();
    if (wsId == null) return;
    try {
        excludedRows = await stcGetExcluded(wsId, dateFrom, dateTo);
        if (tbl)
            tbl.innerHTML = excludedRows.length
                ? stcExcludedHead() + `<tbody>${excludedRows.map(stcExcludedRow).join('')}</tbody>`
                : stcExcludedHead() + stcEmptyRow(t('stc-empty-excluded'));
    } catch (_) {
        excludedRows = null;
        if (tbl) tbl.innerHTML = listErrorHtml('stc-error', 'data-stc-excluded-retry');
        const retry = tbl?.querySelector<HTMLElement>('[data-stc-excluded-retry]');
        if (retry) retry.onclick = () => loadExcluded();
    }
}

// ── 事件绑定(一次性)─────────────────────────────────────────────
function bindShell(): void {
    document.getElementById('stc-tab-report')!.onclick = () => switchTab('report');
    document.getElementById('stc-tab-excluded')!.onclick = () => switchTab('excluded');
    document.getElementById('stc-back')!.onclick = () => backToList();
    document.getElementById('stc-btn-opening')!.onclick = () =>
        openOpeningsModal({
            products,
            wsId: activeWsId()!,
            onSaved: loadSummary,
            defaultDate: dateFrom,
        });
    const q = document.getElementById('stc-q') as HTMLInputElement;
    q.oninput = () => {
        keyword = q.value;
        clearTimeout(searchTimer);
        searchTimer = window.setTimeout(renderListTable, 200);
    };
    const from = document.getElementById('stc-date-from') as HTMLInputElement;
    const to = document.getElementById('stc-date-to') as HTMLInputElement;
    from.value = dateFrom;
    to.value = dateTo;
    document.getElementById('stc-apply')!.onclick = () => {
        dateFrom = from.value || dateFrom;
        dateTo = to.value || dateTo;
        loadSummary();
    };
}

// ── 入口 ────────────────────────────────────────────────────────────
window.loadStockCard = function (): void {
    const sec = document.getElementById('page-stock-card');
    if (!sec) return;
    if (window._stockCardDisabled) {
        sec.innerHTML = `<div class="stc">${stcNotEnabledHtml()}</div>`;
        return;
    }
    const wsId = activeWsId();
    if (wsId == null) {
        sec.innerHTML = `<div class="stc">${stcNeedWorkspaceHtml()}</div>`;
        const pick = document.getElementById('stc-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => window.loadStockCard!())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    const range = defaultRange();
    dateFrom = dateFrom || range.from;
    dateTo = dateTo || range.to;
    setBody(shellHtml());
    bindShell();
    loadSummary();
};

// ── entitlement 探针(SPA 起动即探一次,结果双写进 window._stockCardDisabled,
//    与 nav-presets.applyNavPreset 谁先跑到都收敛——见该文件尾部注释)────────
async function probeStockCardNav(): Promise<void> {
    if (window._stockCardProbed) return;
    window._stockCardProbed = true;
    try {
        window._stockCardDisabled = !(await stcGetStatus());
    } catch (_) {
        window._stockCardDisabled = false; // 探针本身失败(网络抖动)≠ 关闭,不误杀入口
    }
    if (window._stockCardDisabled) {
        const nav = document.getElementById('nav-group-firm-goods');
        if (nav) nav.style.display = 'none';
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', probeStockCardNav);
} else {
    probeStockCardNav();
}

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('stock-card', () => {
        const sec = document.getElementById('page-stock-card');
        if (!sec || !sec.querySelector('.stc')) return;
        setBody(shellHtml());
        bindShell();
        syncExcludedBadge();
        renderListTable();
        applyViewVisibility();
        if (currentTab === 'excluded' && excludedRows) loadExcluded();
        if (reportSub === 'detail' && detailKey) openDetail(detailKey);
    });
}
