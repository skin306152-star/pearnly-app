// ============================================================
// 录入工作台 · 步④推送前预览(记账画像 gate)· 独立模块(控行数 · 单一职责)
//   仅 Express 端点显示(库存/非库存之分是 Express 专属)。调 /api/erp/posting-preview 拿 gate:
//     ok            全干净 → 一行摘要(N 复用 · M 新建),照常推,不打断
//     confirm_profile 画像待定 → 问这家管不管库存,存 config 后不再问
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
    // 同签名(同批同目标)重渲:从缓存画像数据重画(renderGate 会重挂按钮监听),不重复打后端。
    // renderSubmit 每次重建空容器 → 旧的 `el.innerHTML` 守卫恒失效,每次勾选/切目标/doFinish 都
    // 重拉(还与推送并发)。改按数据签名去重根治。
    if (sig === _sig && _cache) {
        renderGate(el, _cache, endpointId, historyIds);
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
        renderGate(el, _cache, endpointId, historyIds);
    } catch {
        el.innerHTML = '';
    }
}

function renderGate(el: HTMLElement, d: Preview, endpointId: string, historyIds: string[]): void {
    const gate = d.gate || '';
    if (gate === 'na' || gate === '') {
        el.innerHTML = ''; // MR.ERP 等非 Express:无此预览
        return;
    }
    const sm = d.summary || { reuse: 0, new: 0, confirm: 0 };
    if (gate === 'ok') {
        const line = t('dxpp-ok').replace('{r}', String(sm.reuse)).replace('{n}', String(sm.new));
        el.innerHTML = `<div class="dx-pp-ok">✓ ${esc(line)}</div>`;
        return;
    }
    if (gate === 'escalate') {
        el.innerHTML = `<div class="dx-pp-warn">⚠ ${esc(t('dxpp-escalate'))}</div>`;
        return;
    }
    if (gate === 'confirm_profile') {
        el.innerHTML =
            `<div class="dx-pp-confirm"><p>${esc(t('dxpp-confirm-q'))}</p>` +
            `<div class="dx-pp-btns"><button class="btn" data-pp="non_stock">${esc(t('dxpp-confirm-nonstock'))}</button>` +
            `<button class="btn" data-pp="stock">${esc(t('dxpp-confirm-stock'))}</button></div></div>`;
        el.querySelectorAll('[data-pp]').forEach((b) =>
            b.addEventListener('click', () =>
                saveProfile(el, endpointId, historyIds, (b as HTMLElement).dataset.pp || '')
            )
        );
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

async function saveProfile(
    el: HTMLElement,
    endpointId: string,
    historyIds: string[],
    mode: string
): Promise<void> {
    if (!mode) return;
    el.innerHTML = `<div class="dx-pp-load">${esc(t('dxpp-loading'))}</div>`;
    try {
        await fetch('/api/erp/posting-profile', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({
                endpoint_id: endpointId,
                posting_mode: mode,
                inventory_usage: mode === 'stock' ? 'perpetual' : 'none',
            }),
        });
    } catch {
        /* 存失败:重拉预览时会回到 confirm_profile,不静默假装成功 */
    }
    _sig = ''; // 破缓存,拿新画像重渲
    _cache = null;
    await refreshPostingPreview(historyIds, endpointId);
}
