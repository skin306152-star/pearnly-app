// 事务所端 · 商品收发存报表 · 期初库存 / 归并弹窗(模态层 · 依赖走显式 ctx 传入,不反引主模块)
/* global t, escapeHtml, showToast */
import {
    stcGetOpenings,
    stcPostMerge,
    stcPostOpenings,
    type StcOpeningRow,
    type StcOpeningSaved,
    type StcProduct,
} from './stock-card-api.js';

export interface StcModalCtx {
    products: StcProduct[];
    wsId: number;
    onSaved: () => void;
    defaultDate: string;
}

function esc(s: string): string {
    return escapeHtml(s);
}

// ── 期初库存弹窗 ────────────────────────────────────────────────────
// 行身份用归组钥匙 key(p:<id> / n:<清洗名>):名字轨行没有 product_id,发 pid 等于把期初
// 挂到不存在的商品上 —— 后端 OpeningIn 本来就吃「product_id 或 name」双轨。
function openingRowHtml(
    p: StcProduct,
    saved: StcOpeningSaved | undefined,
    defaultDate: string
): string {
    const qty = saved ? saved.qty : '';
    const cost = saved && saved.unit_cost ? saved.unit_cost : '';
    const date = saved && saved.as_of_date ? saved.as_of_date : defaultDate;
    return `<tr data-op-key="${esc(p.key)}">
        <td>${esc(p.name)}</td>
        <td class="num"><input type="number" min="0" step="0.001" class="stc-in" data-op-qty value="${esc(qty)}"></td>
        <td class="num"><input type="number" min="0" step="0.01" class="stc-in" data-op-cost placeholder="0.00" value="${esc(cost)}"></td>
        <td><input type="date" class="stc-in" data-op-date value="${esc(date)}"></td>
    </tr>`;
}

export async function openOpeningsModal(ctx: StcModalCtx): Promise<void> {
    const mask = document.getElementById('stc-op-mask');
    if (!mask) return;
    // 已存期初按归组钥匙建档(与行身份同构):product_id → p:<id> / name_key → n:<清洗名>。
    // 预填只用这份用户期初;product.opening_qty 是计算结转,不预填(2026-08-08 口径)。
    let savedByKey = new Map<string, StcOpeningSaved>();
    try {
        const saved = await stcGetOpenings(ctx.wsId);
        const pairs: Array<[string, StcOpeningSaved]> = [];
        for (const o of saved) {
            const k = o.product_id ? `p:${o.product_id}` : o.name_key ? `n:${o.name_key}` : null;
            if (k) pairs.push([k, o]);
        }
        savedByKey = new Map(pairs);
    } catch (_) {
        // 期初拉取失败不挡弹窗:按空数组开,保存仍走 POST 写路径。
    }
    const rows = ctx.products
        .map((p) => openingRowHtml(p, savedByKey.get(p.key), ctx.defaultDate))
        .join('');
    mask.innerHTML = `<div class="modal modal-md stc">
        <div class="modal-header"><div class="modal-title">${esc(t('stc-op-title'))}</div><button type="button" class="modal-close" id="stc-op-close">&times;</button></div>
        <div class="modal-body">
            <p class="stc-hint">${esc(t('stc-op-hint'))}</p>
            ${
                ctx.products.length
                    ? `<div class="stc-scroll"><table id="stc-op-tbl"><thead><tr>
                        <th>${esc(t('stc-col-product'))}</th><th class="num">${esc(t('stc-col-qty'))}</th>
                        <th class="num">${esc(t('stc-op-col-cost'))}</th><th>${esc(t('stc-op-col-date'))}</th>
                    </tr></thead><tbody>${rows}</tbody></table></div>`
                    : `<div class="stc-state">${esc(t('stc-op-empty'))}</div>`
            }
            <div class="stc-merr" id="stc-op-err"></div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary btn-sm" id="stc-op-cancel">${esc(t('btn-cancel'))}</button>
            <button type="button" class="btn btn-primary btn-sm" id="stc-op-save">${esc(t('btn-save'))}</button>
        </div>
    </div>`;
    mask.style.display = 'flex';
    const close = () => {
        mask.style.display = 'none';
    };
    document.getElementById('stc-op-close')!.onclick = close;
    document.getElementById('stc-op-cancel')!.onclick = close;
    mask.onclick = (e) => {
        if (e.target === mask) close();
    };
    const save = document.getElementById('stc-op-save') as HTMLButtonElement;
    save.onclick = () => void saveOpenings(ctx, save, close);
}

async function saveOpenings(
    ctx: StcModalCtx,
    btn: HTMLButtonElement,
    close: () => void
): Promise<void> {
    const rows: StcOpeningRow[] = [];
    document.querySelectorAll<HTMLElement>('#stc-op-tbl [data-op-key]').forEach((tr) => {
        const qty = (tr.querySelector('[data-op-qty]') as HTMLInputElement)?.value.trim();
        if (!qty) return; // 空 = 这个商品不填期初,跳过(不是 0)
        const cost = (tr.querySelector('[data-op-cost]') as HTMLInputElement)?.value.trim() || '0';
        const date =
            (tr.querySelector('[data-op-date]') as HTMLInputElement)?.value || ctx.defaultDate;
        const key = tr.dataset.opKey || '';
        const who = key.startsWith('p:') ? { product_id: key.slice(2) } : { name: key.slice(2) };
        rows.push({ ...who, qty, unit_cost: cost, as_of_date: date });
    });
    const err = document.getElementById('stc-op-err');
    if (!rows.length) {
        if (err) err.textContent = t('stc-op-empty');
        return;
    }
    btn.disabled = true;
    try {
        await stcPostOpenings(ctx.wsId, rows);
        showToast(t('stc-op-save-ok'), 'success');
        close();
        ctx.onSaved();
    } catch (_) {
        if (err) err.textContent = t('stc-op-save-fail');
        btn.disabled = false;
    }
}

// ── 归并弹窗 ────────────────────────────────────────────────────────
// 勾选默认只勾入口那一行:其余名字是不是同一件货只有会计知道,默认全勾在真机上把
// 冰块和美妆并成了一件货 —— 勾选必须是明确动作。目标下拉用 key 当 value(名字轨的
// product_id 恒空,v1 拿它当 value 是这功能从没成功过的断口之一);已建档商品也进
// 目标列表,把散名并进真商品档。
export function openMergeModal(ctx: StcModalCtx, selfKey: string): void {
    const mask = document.getElementById('stc-mg-mask');
    const self = ctx.products.find((p) => p.key === selfKey);
    if (!mask || !self) return;
    const others = ctx.products.filter((p) => !p.matched && p.key !== selfKey);
    const checks = [self, ...others]
        .map(
            (p) =>
                `<label class="stc-mg-row"><input type="checkbox"${p.key === selfKey ? ' checked' : ''} data-mg-cb value="${esc(p.key)}"> ${esc(p.name)}</label>`
        )
        .join('');
    const options = [self, ...ctx.products.filter((p) => p.matched), ...others]
        .map((p) => `<option value="${esc(p.key)}">${esc(p.name)}</option>`)
        .join('');
    mask.innerHTML = `<div class="modal modal-md stc">
        <div class="modal-header"><div class="modal-title">${esc(t('stc-mg-title'))}</div><button type="button" class="modal-close" id="stc-mg-close">&times;</button></div>
        <div class="modal-body">
            <p class="stc-hint">${esc(t('stc-mg-hint'))}</p>
            <p><b>${esc(t('stc-mg-found'))}</b></p>
            ${checks}
            <p style="margin-top:12px"><b>${esc(t('stc-mg-target'))}</b></p>
            <select id="stc-mg-target">${options}</select>
            <div class="stc-merr" id="stc-mg-err"></div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary btn-sm" id="stc-mg-cancel">${esc(t('btn-cancel'))}</button>
            <button type="button" class="btn btn-primary btn-sm" id="stc-mg-confirm">${esc(t('stc-mg-confirm'))}</button>
        </div>
    </div>`;
    mask.style.display = 'flex';
    const close = () => {
        mask.style.display = 'none';
    };
    document.getElementById('stc-mg-close')!.onclick = close;
    document.getElementById('stc-mg-cancel')!.onclick = close;
    mask.onclick = (e) => {
        if (e.target === mask) close();
    };
    const confirm = document.getElementById('stc-mg-confirm') as HTMLButtonElement;
    confirm.onclick = () => void saveMerge(ctx, confirm, close);
}

// key → 后端吃的裸清洗名(去掉归组钥匙的 n: 前缀 · 与 services/stockcard/grouping.py 同约定)。
function mergeNameOf(key: string): string {
    return key.replace(/^n:/, '');
}

async function saveMerge(
    ctx: StcModalCtx,
    btn: HTMLButtonElement,
    close: () => void
): Promise<void> {
    const nameKeys = Array.from(
        document.querySelectorAll<HTMLInputElement>('[data-mg-cb]:checked')
    ).map((cb) => mergeNameOf(cb.value));
    const targetKey = (document.getElementById('stc-mg-target') as HTMLSelectElement)?.value;
    const target = ctx.products.find((p) => p.key === targetKey);
    const err = document.getElementById('stc-mg-err');
    // 名字轨目标自己的名字必须入组,否则并完留一个同名空卡。
    if (target && !target.matched && !nameKeys.includes(mergeNameOf(targetKey))) {
        nameKeys.push(mergeNameOf(targetKey));
    }
    if (!target || !nameKeys.length) {
        if (err) err.textContent = t('stc-mg-none');
        return;
    }
    const payload = target.matched
        ? { name_keys: nameKeys, target_product_id: target.product_id }
        : { name_keys: nameKeys, new_product_name: target.name, unit: target.unit || undefined };
    btn.disabled = true;
    try {
        await stcPostMerge(ctx.wsId, payload);
        showToast(t('stc-mg-ok'), 'success');
        close();
        ctx.onSaved();
    } catch (_) {
        if (err) err.textContent = t('stc-mg-fail');
        btn.disabled = false;
    }
}
