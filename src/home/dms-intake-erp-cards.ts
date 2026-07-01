// ============================================================
// 录入工作台 · 上下文 ERP 连接卡(按任务)
// 发票/收据录入 → MR.ERP(财务)+ Express;身份证→DMS 客户 → MR.ERP DMS。
// 卡片显示连接状态 · 点击开对应连接向导(全局入口,不与重卡片模块耦合)。
// 状态来自 /api/erp/endpoints(data.items) · 卡片交互 hover 放大见 home-49-dms-intake.css。
// ============================================================
import { esc, authHeaders } from './dms-intake-core.js';

interface ErpCardDef {
    key: string;
    name: string;
    adapter: string; // 与 endpoint.adapter 匹配 · 也是开向导的 key
}

// 任务 → 该任务上下文相关的 ERP。发票走财务两家;身份证走 DMS。
const TASK_CARDS: Record<string, ErpCardDef[]> = {
    invoice: [
        { key: 'mrerp', name: 'MR.ERP', adapter: 'mrerp' },
        { key: 'express', name: 'Express', adapter: 'express' },
    ],
    identity: [{ key: 'mrerp_dms', name: 'MR.ERP DMS', adapter: 'mrerp_dms' }],
};

const ICONS: Record<string, string> = {
    mrerp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="22" height="22"><path d="M4 7h16M4 12h16M4 17h10"/><circle cx="18" cy="17" r="2.6"/></svg>',
    express:
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="22" height="22"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 9h18M8 18v2m8-2v2"/></svg>',
    mrerp_dms:
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="22" height="22"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2.1"/><path d="M6 16c.7-1.4 1.9-2.1 3-2.1s2.3.7 3 2.1M14 10h4M14 14h4"/></svg>',
};

function T(k: string): string {
    const w = window as unknown as { t?: (k: string) => string };
    return typeof w.t === 'function' ? w.t(k) : k;
}

function cardHtml(def: ErpCardDef): string {
    return (
        `<div class="dx-erp-card" data-erp="${esc(def.adapter)}" role="button" tabindex="0">` +
        `<div class="dx-erp-ic">${ICONS[def.key] || ''}</div>` +
        '<div class="dx-erp-info">' +
        `<b>${esc(def.name)}</b>` +
        `<span class="dx-erp-status" data-erp-status>${esc(T('dx-erp-checking'))}</span>` +
        '</div>' +
        `<span class="dx-erp-cta" data-erp-cta>${esc(T('dx-erp-connect'))}</span>` +
        '</div>'
    );
}

function openWizardFor(adapter: string, ep: unknown): void {
    const w = window as unknown as Record<string, ((ep: unknown) => void) | undefined> & {
        ExpressWizard?: { open?: (ep: unknown) => void };
    };
    if (adapter === 'mrerp') w._mrerpOpenWizard?.(ep || null);
    else if (adapter === 'express') w.ExpressWizard?.open?.(ep || null);
    else if (adapter === 'mrerp_dms') w._mrerpDmsOpenWizard?.(ep || null);
}

function bindClicks(zone: HTMLElement): void {
    zone.querySelectorAll<HTMLElement>('.dx-erp-card').forEach((card) => {
        const fire = () =>
            openWizardFor(card.dataset.erp || '', (card as unknown as { _ep?: unknown })._ep);
        card.addEventListener('click', fire);
        card.addEventListener('keydown', (e) => {
            if ((e as KeyboardEvent).key === 'Enter' || (e as KeyboardEvent).key === ' ') {
                e.preventDefault();
                fire();
            }
        });
    });
}

async function loadStatus(zone: HTMLElement, defs: ErpCardDef[]): Promise<void> {
    let items: Array<Record<string, unknown>> = [];
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
        (card as unknown as { _ep: unknown })._ep = ep;
        const st = card.querySelector('[data-erp-status]');
        const cta = card.querySelector('[data-erp-cta]');
        if (ep) {
            card.classList.add('is-connected');
            if (st) st.textContent = T('dx-erp-connected');
            if (cta) cta.textContent = T('dx-erp-config');
        } else {
            card.classList.remove('is-connected');
            if (st) st.textContent = T('dx-erp-not-connected');
            if (cta) cta.textContent = T('dx-erp-connect');
        }
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
