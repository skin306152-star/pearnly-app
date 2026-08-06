// ============================================================
// 录入工作台 · 步④推送前预览(记账画像 gate)· 独立模块(控行数 · 单一职责)
//   仅 Express 端点显示(库存/非库存之分是 Express 专属)。调 /api/erp/posting-preview 拿 gate:
//     ok            全干净 → 一行摘要(N 复用 · M 新建),照常推,不打断
//     confirm_profile 本批未声明过账去向 → 诚实提示态,指回第①步重新选(2026-08-06 拍板
//                   补刀:UI 收集画像的两按钮弹卡已删除,停止收集新画像;后端 posting-profile
//                   路由与存量画像兜底消费不动,老客户仍走 mapper 回落)
//     escalate      永续客户 + 库存路未开 → 商品行需人工,本批留人工(不假装成功)
//     decide_items  有行只存在于库存目录 / 拿不准 → 捞出来给人看(默认建独立非库存 · firm-safe)
// ============================================================
import { esc, authHeaders } from './dms-intake-core.js';

declare const t: (k: string) => string;

type PreviewItem = {
    name: string;
    status: string;
    kind?: string;
    cross_kind?: boolean;
};
type Preview = {
    gate?: string;
    profile?: { posting_mode?: string; inventory_usage?: string };
    items?: PreviewItem[];
    summary?: { reuse: number; new: number; confirm: number };
};

const CONTAINER_ID = 'dx-posting-preview';
let _sig = '';
let _cache: Preview | null = null;

export function postingPreviewContainer(): string {
    return `<div id="${CONTAINER_ID}" class="dx-pp"></div>`;
}

/** 拉预览并渲染进容器。同批同目标不重复拉;失败静默清空(不阻断推送)。 */
export async function refreshPostingPreview(
    historyIds: string[],
    endpointId: string
): Promise<void> {
    const el = document.getElementById(CONTAINER_ID);
    if (!el || !endpointId || !historyIds.length) return;
    const sig = endpointId + '|' + historyIds.join(',');
    // 同签名(同批同目标)重渲:从缓存数据重画,不重复打后端。renderSubmit 每次重建空容器 →
    // 旧的 `el.innerHTML` 守卫恒失效,每次勾选/切目标/doFinish 都重拉(还与推送并发)。
    // 改按数据签名去重根治。
    if (sig === _sig && _cache) {
        renderGate(el, _cache);
        return;
    }
    _sig = sig;
    _cache = null;
    el.innerHTML = `<div class="dx-pp-load">${esc(t('dxpp-loading'))}</div>`;
    try {
        const r = await fetch('/api/erp/posting-preview', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ history_ids: historyIds, endpoint_id: endpointId }),
        });
        _cache = (await r.json().catch(() => ({}))) as Preview;
        renderGate(el, _cache);
    } catch {
        el.innerHTML = '';
    }
}

function renderGate(el: HTMLElement, d: Preview): void {
    const gate = d.gate || '';
    if (gate === 'na' || gate === '') {
        el.innerHTML = ''; // MR.ERP 等非 Express:无此预览
        return;
    }
    const sm = d.summary || { reuse: 0, new: 0, confirm: 0 };
    if (gate === 'ok') {
        const line = t('dxpp-ok').replace('{r}', String(sm.reuse)).replace('{n}', String(sm.new));
        el.innerHTML = `<div class="dx-pp-ok">${esc(line)}</div>`;
        return;
    }
    if (gate === 'escalate') {
        el.innerHTML = `<div class="dx-pp-warn">${esc(t('dxpp-escalate'))}</div>`;
        return;
    }
    if (gate === 'confirm_profile') {
        // 诚实提示态(2026-08-06 拍板补刀):本批未声明过账去向,不再弹卡收集画像——
        // 指回第①步重新选服务/库存。data-iv-pp-back-step1 由 dms-intake-invoice.ts 的
        // 单一事件委托接住(onInvoiceClick),这里不直接依赖那个模块(防循环依赖)。
        el.innerHTML =
            `<div class="dx-pp-noprofile"><p>${esc(t('dxpp-noprofile-txt'))}</p>` +
            `<button type="button" class="btn" data-iv-pp-back-step1="1">${esc(t('dxpp-noprofile-back'))}</button></div>`;
        return;
    }
    // decide_items:把例外(拿不准 / 只存在于库存目录)捞出来给人看。默认另建非库存(firm-safe)。
    const rows = (d.items || [])
        .filter((it) => it.cross_kind || it.status === 'confirm')
        .map(
            (it) =>
                `<div class="dx-pp-row"><b>${esc(it.name)}</b><span>${esc(
                    it.cross_kind ? t('dxpp-cross-kind') : t('dxpp-fuzzy')
                )}</span></div>`
        )
        .join('');
    el.innerHTML =
        `<div class="dx-pp-decide"><p>${esc(t('dxpp-decide-h'))}</p>${rows}` +
        `<div class="dx-pp-note">${esc(t('dxpp-decide-note'))}</div></div>`;
}
