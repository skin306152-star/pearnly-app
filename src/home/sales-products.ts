// 销项 PO-10 · 商品管理(主数据 · 共享 · 以后 POS/库存复用)
// 接真接口 GET/POST/PATCH/DELETE /api/sales/products + /import。四态 + .modal(非抽屉)。
/* global t, escapeHtml, apiGet, apiPost, showToast */
import {
    salesFetch,
    fmtMoney,
    htmlVal,
    imageFieldHtml,
    bindImageField,
    IC_X,
} from './sales-common.js';

interface Product {
    id: string;
    code?: string;
    barcode?: string;
    name_th?: string;
    name_en?: string;
    name_zh?: string;
    unit?: string;
    unit_price: number;
    vat_applicable: boolean;
    image_url?: string;
}

const IC_BOX =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 8 12 3 3 8l9 5 9-5ZM3 8v8l9 5 9-5V8"/></svg>';
const IC_EDIT =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M11 4H4v16h16v-7M18.5 2.5a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>';
const IC_TRASH =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>';

let products: Product[] = [];
let keyword = '';

function ensureMask(id: string): HTMLElement {
    let m = document.getElementById(id);
    if (!m) {
        m = document.createElement('div');
        m.id = id;
        m.className = 'modal-mask sx-modal-mask';
        m.style.display = 'none';
        document.body.appendChild(m);
    }
    return m;
}
function closeMask(id: string) {
    const m = document.getElementById(id);
    if (m) {
        m.style.display = 'none';
        m.innerHTML = '';
    }
}

function visible(): Product[] {
    const kw = keyword.trim().toLowerCase();
    if (!kw) return products;
    return products.filter((p) =>
        [p.code, p.name_th, p.name_en, p.name_zh, p.barcode]
            .filter(Boolean)
            .some((v) => v!.toLowerCase().indexOf(kw) >= 0)
    );
}

function rowsHtml(): string {
    const list = visible();
    if (!list.length)
        return `<tr><td colspan="7"><div class="sx-state">${escapeHtml(t('sx-empty'))}</div></td></tr>`;
    return list
        .map((p) => {
            const name = p.name_th || p.name_en || p.name_zh || '—';
            const img = p.image_url
                ? `<img src="${escapeHtml(p.image_url)}" alt="" style="width:34px;height:34px;border-radius:7px;object-fit:cover">`
                : `<div class="sx-thumb">${IC_BOX}</div>`;
            return `<tr>
                <td>${img}</td>
                <td style="color:var(--ink-3)">${escapeHtml(p.code || '—')}</td>
                <td><b>${escapeHtml(name)}</b></td>
                <td>${escapeHtml(p.unit || '—')}</td>
                <td class="r">${fmtMoney(p.unit_price)}</td>
                <td>${p.vat_applicable ? '<span class="sx-badge issued">7%</span>' : '<span class="sx-badge draft">—</span>'}</td>
                <td class="r"><button class="sx-chev" data-edit="${escapeHtml(p.id)}">${IC_EDIT}</button><button class="sx-chev" data-del="${escapeHtml(p.id)}">${IC_TRASH}</button></td>
            </tr>`;
        })
        .join('');
}

function listHtml(): string {
    return `<div class="sx-toolbar">
        <div class="sx-search"><input type="text" id="sx-p-search" value="${escapeHtml(keyword)}" placeholder="${escapeHtml(t('sx-p-search-ph'))}"></div>
        <button class="btn btn-ghost" id="sx-p-import">${escapeHtml(t('sx-p-import'))}</button>
        <button class="btn btn-primary" id="sx-p-add">${escapeHtml(t('sx-p-add'))}</button>
    </div>
    <div class="sx-panel"><table class="sx-tbl">
        <thead><tr>
            <th>${escapeHtml(t('sx-p-col-img'))}</th><th>${escapeHtml(t('sx-p-col-code'))}</th>
            <th>${escapeHtml(t('sx-p-col-name'))}</th><th>${escapeHtml(t('sx-p-col-unit'))}</th>
            <th class="r">${escapeHtml(t('sx-p-col-price'))}</th><th>${escapeHtml(t('sx-p-col-vat'))}</th><th></th>
        </tr></thead>
        <tbody id="sx-p-tbody">${rowsHtml()}</tbody>
    </table></div>`;
}

function renderBody(html: string) {
    const body = document.getElementById('sx-p-body');
    if (body) body.innerHTML = html;
}

function bindList() {
    const search = document.getElementById('sx-p-search') as HTMLInputElement | null;
    if (search)
        search.oninput = () => {
            keyword = search.value;
            const tb = document.getElementById('sx-p-tbody');
            if (tb) tb.innerHTML = rowsHtml();
            bindRowActions();
        };
    document.getElementById('sx-p-add')!.onclick = () => openEdit(null);
    document.getElementById('sx-p-import')!.onclick = openImport;
    bindRowActions();
}
function bindRowActions() {
    document.querySelectorAll<HTMLElement>('#sx-p-body [data-edit]').forEach((el) => {
        el.onclick = () => openEdit(products.find((p) => p.id === el.dataset.edit) || null);
    });
    document.querySelectorAll<HTMLElement>('#sx-p-body [data-del]').forEach((el) => {
        el.onclick = () => del(el.dataset.del!);
    });
}

function openEdit(p: Product | null) {
    const mask = ensureMask('sales-prod-mask');
    mask.innerHTML = `<div class="modal" role="dialog" style="max-width:560px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t(p ? 'sx-p-edit' : 'sx-p-new'))}</div>
            <button class="modal-close" id="sx-p-close">${IC_X}</button></div>
        <div class="modal-body">
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t('sx-p-f-code'))}</label><input type="text" id="sx-pf-code" value="${htmlVal(p?.code)}" maxlength="100"><div class="sx-field-err" id="sx-pf-code-err"></div></div>
                <div><label>${escapeHtml(t('sx-p-f-barcode'))}</label><input type="text" id="sx-pf-barcode" value="${htmlVal(p?.barcode)}" maxlength="100"></div>
            </div>
            <div class="form-row"><label>${escapeHtml(t('sx-p-f-name-th'))} *</label><input type="text" id="sx-pf-th" value="${htmlVal(p?.name_th)}" maxlength="300"></div>
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t('sx-p-f-name-en'))}</label><input type="text" id="sx-pf-en" value="${htmlVal(p?.name_en)}" maxlength="300"></div>
                <div><label>${escapeHtml(t('sx-p-f-name-zh'))}</label><input type="text" id="sx-pf-zh" value="${htmlVal(p?.name_zh)}" maxlength="300"></div>
            </div>
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t('sx-p-f-unit'))}</label><input type="text" id="sx-pf-unit" value="${htmlVal(p?.unit)}" maxlength="50"></div>
                <div><label>${escapeHtml(t('sx-p-f-price'))}</label><input type="number" id="sx-pf-price" value="${p ? p.unit_price : ''}" min="0" step="0.01"></div>
            </div>
            <div class="form-row"><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" id="sx-pf-vat" ${!p || p.vat_applicable ? 'checked' : ''} style="width:auto"> ${escapeHtml(t('sx-p-f-vat'))}</label></div>
            <div class="form-row">${imageFieldHtml('sx-pf-image', t('sx-p-f-image'), p?.image_url)}</div>
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-p-cancel">${escapeHtml(t('sx-cancel'))}</button>
            <button class="btn btn-primary" id="sx-p-save">${escapeHtml(t('sx-p-save'))}</button>
        </div></div>`;
    mask.style.display = 'flex';
    document.getElementById('sx-p-close')!.onclick = () => closeMask('sales-prod-mask');
    document.getElementById('sx-p-cancel')!.onclick = () => closeMask('sales-prod-mask');
    mask.onclick = (e) => {
        if (e.target === mask) closeMask('sales-prod-mask');
    };
    document.getElementById('sx-p-save')!.onclick = () => save(p);
    bindImageField('sx-pf-image');
}

function readForm() {
    const val = (id: string) => (document.getElementById(id) as HTMLInputElement).value.trim();
    return {
        name_th: val('sx-pf-th'),
        code: val('sx-pf-code') || null,
        barcode: val('sx-pf-barcode') || null,
        name_en: val('sx-pf-en') || null,
        name_zh: val('sx-pf-zh') || null,
        unit: val('sx-pf-unit') || null,
        unit_price: Number(val('sx-pf-price')) || 0,
        vat_applicable: (document.getElementById('sx-pf-vat') as HTMLInputElement).checked,
        image_url: val('sx-pf-image') || null,
    };
}

async function failMsg(r: Response, fallbackKey: string): Promise<string> {
    const d = await r.json().catch(() => ({}));
    const detail = d && d.detail ? String(d.detail) : 'HTTP ' + r.status;
    return t(fallbackKey) + ' · ' + detail;
}

function setCodeErr(msg: string) {
    const el = document.getElementById('sx-pf-code-err');
    if (el) el.textContent = msg;
}

async function save(p: Product | null) {
    const payload = readForm();
    setCodeErr('');
    if (!payload.name_th) return showToast(t('sx-p-name-required'), 'error');
    const url = p ? `/api/sales/products/${p.id}` : '/api/sales/products';
    try {
        const r = await salesFetch(url, {
            method: p ? 'PATCH' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!r.ok) {
            const d = await r.json().catch(() => ({}));
            const detail = d && d.detail ? String(d.detail) : 'HTTP ' + r.status;
            // 编码重复 → 标在「编码」框旁(红字),不弹系统错误
            if (detail === 'sales.product_code_exists') {
                setCodeErr(t('sales.product_code_exists'));
                (document.getElementById('sx-pf-code') as HTMLInputElement)?.focus();
                return;
            }
            showToast(t('sx-p-save-fail') + ' · ' + detail, 'error');
            return;
        }
        closeMask('sales-prod-mask');
        showToast(t('sx-p-saved'), 'success');
        await load();
    } catch (_) {
        showToast(t('sx-p-save-fail'), 'error');
    }
}

async function del(id: string) {
    if (window.pearnlyConfirm) {
        const ok = await window.pearnlyConfirm(t('sx-p-del-confirm'));
        if (!ok) return;
    } else if (!confirm(t('sx-p-del-confirm'))) return;
    try {
        const r = await salesFetch(`/api/sales/products/${id}`, { method: 'DELETE' });
        if (!r.ok) {
            showToast(await failMsg(r, 'sx-p-del-fail'), 'error');
            return;
        }
        showToast(t('sx-p-deleted'), 'success');
        await load();
    } catch (_) {
        showToast(t('sx-p-del-fail'), 'error');
    }
}

function openImport() {
    const mask = ensureMask('sales-prod-mask');
    mask.innerHTML = `<div class="modal" role="dialog" style="max-width:480px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t('sx-p-import-title'))}</div>
            <button class="modal-close" id="sx-imp-close">${IC_X}</button></div>
        <div class="modal-body">
            <input type="file" id="sx-imp-file" accept=".xlsx,.xls" style="width:100%">
            <div class="sx-banner" style="margin-top:10px">${escapeHtml(t('sx-p-import-hint'))}</div>
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-imp-cancel">${escapeHtml(t('sx-cancel'))}</button>
            <button class="btn btn-primary" id="sx-imp-go">${escapeHtml(t('sx-p-import-go'))}</button>
        </div></div>`;
    mask.style.display = 'flex';
    document.getElementById('sx-imp-close')!.onclick = () => closeMask('sales-prod-mask');
    document.getElementById('sx-imp-cancel')!.onclick = () => closeMask('sales-prod-mask');
    document.getElementById('sx-imp-go')!.onclick = doImport;
}
async function doImport() {
    const f = (document.getElementById('sx-imp-file') as HTMLInputElement).files?.[0];
    if (!f) return showToast(t('sx-p-import-pick'), 'error');
    const fd = new FormData();
    fd.append('file', f);
    try {
        const r = await salesFetch('/api/sales/products/import', { method: 'POST', body: fd });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error();
        closeMask('sales-prod-mask');
        showToast(t('sx-p-import-done').replace('{n}', String(data.imported ?? 0)), 'success');
        await load();
    } catch (_) {
        showToast(t('sx-p-import-fail'), 'error');
    }
}

async function load() {
    renderBody(`<div class="sx-state">${escapeHtml(t('sx-loading'))}</div>`);
    try {
        const data = await apiGet('/api/sales/products');
        if (!data) return;
        products = (data.products || []) as Product[];
        renderBody(listHtml());
        bindList();
    } catch (_) {
        renderBody(
            `<div class="sx-state error">${escapeHtml(t('sx-error'))}<br><button class="btn btn-ghost" id="sx-p-retry">${escapeHtml(t('sx-retry'))}</button></div>`
        );
        const retry = document.getElementById('sx-p-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadSalesProducts = function () {
    const sec = document.getElementById('page-sales-products');
    if (!sec) return;
    if (sec.dataset.sxInit !== '1') {
        sec.innerHTML = `<div class="sx-page"><div class="sx-head"><h2>${escapeHtml(t('nav-sales-products'))}</h2></div><div id="sx-p-body"></div></div>`;
        sec.dataset.sxInit = '1';
    }
    load();
};
