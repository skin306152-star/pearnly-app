// ERP 门户 · 商品收发存报表(Stock Card · 路由 stock-card · window.loadStockCard)
// 一份按商品连续排列的参考图原样 13 列表格(2026-08-27 拍板):所有商品默认同页、逐笔流水
// 全露,不设「汇总→单品详情」两段式、未入账 tab、归并/规则/搜索/状态。唯一报表附加能力
// = 已拍板的期初库存录入(作为每个商品的第一行流水参与计算,不新增列)。
// 视觉规格严格按业务参考图:三段式表头(入绿/出粉/结存紫),负数只按原值展示,
// 不添加参考图之外的告警行或状态组件。令牌换本仓 static/pearnly-ui.css + home-01-base.css,HTML 拼装
// 收在 stock-card-render.ts,取数收在 stock-card-api.ts,期初弹窗收在 stock-card-modals.ts,
// 本文件只管状态编排 + 事件绑定(单一职责 · <500 行预算)。
/* global t, escapeHtml */
import { ymdIso } from './format-date.js';
import { listErrorHtml } from './list-error-state.js';
import { activeWsId, stcGetReport, stcGetStatus, type StcGroup } from './stock-card-api.js';
import {
    stcEmptyState,
    stcGroupBlock,
    stcNeedWorkspaceHtml,
    stcNotEnabledHtml,
    stcSkeletonBody,
    stc13Head,
} from './stock-card-render.js';
import { openOpeningsModal } from './stock-card-modals.js';

let groups: StcGroup[] = [];
let dateFrom = '';
let dateTo = '';

function defaultRange(): { from: string; to: string } {
    const now = new Date();
    return { from: ymdIso(new Date(now.getFullYear(), now.getMonth(), 1)), to: ymdIso(now) };
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
            </div>
        </div>
        <div class="stc-toolbar">
            <div class="stc-daterange">
                <label>${esc(t('stc-date-from-label'))} <input type="date" id="stc-date-from"></label>
                <label>${esc(t('stc-date-to-label'))} <input type="date" id="stc-date-to"></label>
                <button type="button" class="btn btn-secondary btn-sm" id="stc-apply">${esc(t('stc-btn-apply'))}</button>
            </div>
            <div class="stc-grow"></div>
            <button type="button" class="btn btn-ghost btn-sm" id="stc-btn-opening">${esc(t('stc-btn-opening'))}</button>
        </div>
        <div class="stc-card" id="stc-report"></div>
    </div>`;
}

function setBody(html: string): void {
    const sec = document.getElementById('page-stock-card');
    if (sec) sec.innerHTML = html;
}

// ── 报表主体:四态(骨架 / 空 / 错 / 正常)──────────────────────────
function setReport(html: string): void {
    const card = document.getElementById('stc-report');
    if (card) card.innerHTML = html;
}

function renderSkeleton(): void {
    setReport(`<div class="stc-scroll"><table>${stc13Head()}${stcSkeletonBody(13)}</table></div>`);
}

function renderReport(): void {
    if (!groups.length) {
        setReport(stcEmptyState(t('stc-empty-list')));
        return;
    }
    setReport(groups.map(stcGroupBlock).join(''));
}

async function loadReport(): Promise<void> {
    renderSkeleton();
    const wsId = activeWsId();
    if (wsId == null) return;
    try {
        const resp = await stcGetReport(wsId, dateFrom, dateTo);
        groups = resp.groups;
        renderReport();
    } catch (_) {
        setReport(listErrorHtml('stc-error', 'data-stc-report-retry'));
        const retry = document.querySelector<HTMLElement>('[data-stc-report-retry]');
        if (retry) retry.onclick = () => void loadReport();
    }
}

// ── 事件绑定(一次性)─────────────────────────────────────────────
function bindShell(): void {
    const from = document.getElementById('stc-date-from') as HTMLInputElement;
    const to = document.getElementById('stc-date-to') as HTMLInputElement;
    from.value = dateFrom;
    to.value = dateTo;
    document.getElementById('stc-apply')!.onclick = () => {
        dateFrom = from.value || dateFrom;
        dateTo = to.value || dateTo;
        void loadReport();
    };
    document.getElementById('stc-btn-opening')!.onclick = () =>
        openOpeningsModal({
            products: groups.map((g) => g.product),
            wsId: activeWsId()!,
            onSaved: () => void loadReport(),
            defaultDate: dateFrom,
        });
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
    groups = [];
    setBody(shellHtml());
    bindShell();
    loadReport();
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
        renderReport();
    });
}
