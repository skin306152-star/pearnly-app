// ============================================================
// 录入工作台 · 上下文 ERP 连接卡(按任务)
// 发票/收据录入 与 汇总表批量建单 → MR.ERP(财务)+ Express。
// 卡片显示连接状态 + 启用/停用开关 · 点「配置」开对应连接向导。
// 启用/停用是「同批票据不误投多个 ERP」的闸:停用 → 第四步推送面板不显示该端点、
//   自动推送后端也按 enabled=TRUE 过滤(services/erp/push_store.list_erp_endpoints)。
// 状态来自 /api/erp/endpoints(data.items) · toggle 走 PATCH {enabled} 并刷新全局端点缓存。
// ============================================================
import { esc, authHeaders } from './dms-intake-core.js';

interface ErpCardDef {
    key: string;
    name: string;
    adapter: string; // 与 endpoint.adapter 匹配 · 也是开向导的 key
}

// 任务 → 该任务上下文相关的 ERP。发票与汇总表批量落点同(两家财务 ERP)·
// 建成的 ocr_history 走同一推送链路,故两任务共用同一组卡(FINANCE_CARDS)。
const FINANCE_CARDS: ErpCardDef[] = [
    { key: 'mrerp', name: 'MR.ERP', adapter: 'mrerp' },
    { key: 'express', name: 'Express', adapter: 'express' },
];
const TASK_CARDS: Record<string, ErpCardDef[]> = {
    invoice: FINANCE_CARDS,
    summary_batch: FINANCE_CARDS,
};

const ICONS: Record<string, string> = {
    mrerp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="22" height="22"><path d="M4 7h16M4 12h16M4 17h10"/><circle cx="18" cy="17" r="2.6"/></svg>',
    express:
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="22" height="22"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 9h18M8 18v2m8-2v2"/></svg>',
};

type WinBridge = {
    t?: (k: string) => string;
    pearnlyConfirm?: (msg: string, title?: string) => Promise<boolean>;
    _refreshErpEndpointsCache?: () => void;
};

function T(k: string): string {
    const w = window as unknown as WinBridge;
    return typeof w.t === 'function' ? w.t(k) : k;
}

type EpRec = Record<string, unknown> & {
    id?: string;
    enabled?: boolean;
    adapter?: string;
    auto_push?: boolean;
    config?: Record<string, unknown>;
};

function isEnabled(ep: EpRec | null): boolean {
    return !!ep && ep.enabled !== false;
}

// 推送方式:发票/汇总表 ERP 看 auto_push。
function isAutoPush(ep: EpRec): boolean {
    return ep.auto_push === true;
}

function cardHtml(def: ErpCardDef): string {
    // 骨架:图标 + 名称 + 状态占位 + 动作区(状态拉回后由 fillCard 填按钮)。
    return (
        `<div class="dx-erp-card" data-erp="${esc(def.adapter)}">` +
        `<div class="dx-erp-ic">${ICONS[def.key] || ''}</div>` +
        '<div class="dx-erp-info">' +
        `<b>${esc(def.name)}</b>` +
        `<span class="dx-erp-status" data-erp-status>${esc(T('dx-erp-checking'))}</span>` +
        '</div>' +
        '<div class="dx-erp-acts" data-erp-acts></div>' +
        '</div>'
    );
}

// 依端点状态填充单张卡的状态徽章 + 动作按钮。
function fillCard(card: HTMLElement, ep: EpRec | null): void {
    (card as unknown as { _ep: EpRec | null })._ep = ep;
    const st = card.querySelector<HTMLElement>('[data-erp-status]');
    const acts = card.querySelector<HTMLElement>('[data-erp-acts]');
    const enabled = isEnabled(ep);
    card.classList.toggle('is-connected', !!ep && enabled);
    card.classList.toggle('is-disabled', !!ep && !enabled);

    if (st) {
        // 已连接时接上推送方式(自动/手动)· 停用/未连接不显示(此时方式无意义)。
        if (!ep) st.textContent = T('dx-erp-not-connected');
        else if (!enabled) st.textContent = T('dx-erp-disabled');
        else
            st.textContent =
                T('dx-erp-connected') +
                ' · ' +
                T(isAutoPush(ep) ? 'dx-erp-mode-auto' : 'dx-erp-mode-manual');
    }
    if (!acts) return;
    if (!ep) {
        acts.innerHTML = `<button type="button" class="dx-erp-cta" data-erp-config>${esc(
            T('dx-erp-connect')
        )}</button>`;
        return;
    }
    // 已配置:启用/停用 + 配置。toggle 在前、配置在后(对齐老连接卡按钮顺序)。
    acts.innerHTML =
        `<button type="button" class="dx-erp-toggle" data-erp-toggle>${esc(
            T(enabled ? 'dx-erp-disable' : 'dx-erp-enable')
        )}</button>` +
        `<button type="button" class="dx-erp-cta" data-erp-config>${esc(T('dx-erp-config'))}</button>`;
}

function openWizardFor(adapter: string, ep: unknown): void {
    const w = window as unknown as Record<string, ((ep: unknown) => void) | undefined> & {
        ExpressWizard?: { open?: (ep: unknown) => void };
    };
    if (adapter === 'mrerp') w._mrerpOpenWizard?.(ep || null);
    else if (adapter === 'express') w.ExpressWizard?.open?.(ep || null);
}

async function toggleEndpoint(card: HTMLElement): Promise<void> {
    const ep = (card as unknown as { _ep?: EpRec | null })._ep || null;
    if (!ep || !ep.id) return;
    const enabling = !isEnabled(ep);
    const w = window as unknown as WinBridge;
    if (!enabling && typeof w.pearnlyConfirm === 'function') {
        const ok = await w.pearnlyConfirm(T('dx-erp-confirm-disable'));
        if (!ok) return;
    }
    try {
        const r = await fetch(`/api/erp/endpoints/${encodeURIComponent(ep.id)}`, {
            method: 'PATCH',
            headers: authHeaders(true),
            body: JSON.stringify({ enabled: enabling }),
        });
        if (!r.ok) throw new Error('http_' + r.status);
        // 单一状态源:刷新全局端点缓存 → 第四步推送面板/自动推送 picker 立刻反映启停(铁律 #12)。
        if (typeof w._refreshErpEndpointsCache === 'function') w._refreshErpEndpointsCache();
        fillCard(card, { ...ep, enabled: enabling });
    } catch {
        /* 网络/权限失败:保持原状,不误显启停成功 */
    }
}

function bindClicks(zone: HTMLElement): void {
    zone.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        const card = target.closest<HTMLElement>('.dx-erp-card');
        if (!card) return;
        if (target.closest('[data-erp-toggle]')) {
            e.preventDefault();
            void toggleEndpoint(card);
            return;
        }
        if (target.closest('[data-erp-config]')) {
            e.preventDefault();
            openWizardFor(card.dataset.erp || '', (card as unknown as { _ep?: unknown })._ep);
        }
    });
}

async function loadStatus(zone: HTMLElement, defs: ErpCardDef[]): Promise<void> {
    let items: EpRec[] = [];
    try {
        const r = await fetch('/api/erp/endpoints', { headers: authHeaders() });
        if (r.ok) {
            const data = await r.json();
            if (Array.isArray(data.items)) items = data.items;
        }
    } catch {
        /* 离线/无端点 → 全部按未连接渲染 */
    }
    defs.forEach((def) => {
        const card = zone.querySelector<HTMLElement>(`[data-erp="${def.adapter}"]`);
        if (!card) return;
        const ep = items.find((e) => String(e.adapter || '').toLowerCase() === def.adapter) || null;
        fillCard(card, ep);
    });
}

// 渲染当前任务的 ERP 卡到 #dx-erp-cards(dxShell 里的占位)。每次整壳重渲后调。
export function renderDxErpCards(task: string): void {
    const zone = document.getElementById('dx-erp-cards');
    if (!zone) return;
    const defs = TASK_CARDS[task] || [];
    if (!defs.length) {
        zone.innerHTML = '';
        return;
    }
    zone.innerHTML =
        `<div class="dx-erp-h">${esc(T('dx-erp-h'))}</div>` +
        `<div class="dx-erp-row">${defs.map(cardHtml).join('')}</div>`;
    bindClicks(zone);
    void loadStatus(zone, defs);
}
