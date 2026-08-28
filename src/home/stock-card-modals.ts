// 事务所端 · 商品收发存报表 · 期初库存弹窗(模态层 · 依赖走显式 ctx 传入,不反引主模块)
// 2026-08-27 口径:归并弹窗随旧「汇总→单品详情」流程一并删除,这里只剩已拍板的期初录入。
/* global t, escapeHtml, showToast */
import {
    stcGetOpenings,
    stcPostOpenings,
    type StcGroupProduct,
    type StcOpeningRow,
    type StcOpeningSaved,
} from './stock-card-api.js';

export interface StcModalCtx {
    products: StcGroupProduct[];
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
    p: StcGroupProduct,
    saved: StcOpeningSaved | undefined,
    defaultDate: string
): string {
    const qty = saved ? saved.qty : '';
    const cost = saved && saved.unit_cost ? saved.unit_cost : '';
    const date = saved && saved.as_of_date ? saved.as_of_date : defaultDate;
    return `<tr data-op-key="${esc(p.key)}">
        <td class="stc-op-name">${esc(p.name)}</td>
        <td class="num"><input type="number" min="0" step="0.001" class="stc-in" data-op-qty value="${esc(qty)}"></td>
        <td class="num"><input type="number" min="0" step="0.01" class="stc-in" data-op-cost placeholder="0.00" value="${esc(cost)}"></td>
        <td><input type="date" class="stc-in" data-op-date value="${esc(date)}"></td>
    </tr>`;
}

export async function openOpeningsModal(ctx: StcModalCtx): Promise<void> {
    const mask = document.getElementById('stc-op-mask');
    if (!mask) return;
    // 已存期初按归组钥匙建档(与行身份同构):product_id → p:<id> / name_key → n:<清洗名>。
    // 预填只用这份用户期初;报表首行是计算结转,不预填(2026-08-08 口径)。
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
                    ? `<div class="stc-scroll"><table id="stc-op-tbl"><colgroup><col class="stc-op-col-product"><col class="stc-op-col-qty"><col class="stc-op-col-cost"><col class="stc-op-col-date"></colgroup><thead><tr>
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
