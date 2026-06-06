// 销项 PO-10 · 账套 / 开票资料(卖方主体 + 品牌资产 + 模板)
// 接真接口 GET /api/sales/sellers · PUT /api/sales/sellers/{id}(name/税号/地址/分店/电话/promptpay
// + template_id/brand_color/logo_url/seal_url/signature_url/footer_text · §L4 后端已支持)。
/* global t, escapeHtml, apiGet, showToast */
import { salesFetch, htmlVal } from './sales-common.js';

interface Seller {
    id: number;
    name?: string;
    tax_id?: string;
    address?: string;
    branch?: string;
    phone?: string;
    promptpay_id?: string;
    template_id?: string;
    brand_color?: string;
    logo_url?: string;
    seal_url?: string;
    signature_url?: string;
    footer_text?: string;
}

const TEMPLATES = ['classic', 'clean', 'brand', 'compact', 'official', 'mono'];
const COLORS = ['#2563eb', '#0f766e', '#b45309', '#7c3aed', '#be123c', '#111827'];

let sellers: Seller[] = [];
let idx = 0;
let tpl = 'classic';
let color = '#2563eb';

function cur(): Seller | undefined {
    return sellers[idx];
}

function formHtml(): string {
    const s = cur();
    if (!s) return `<div class="sx-state">${escapeHtml(t('sx-acc-none'))}</div>`;
    const sellerOpts = sellers
        .map(
            (x, i) =>
                `<option value="${i}" ${i === idx ? 'selected' : ''}>${escapeHtml(x.name || '—')}</option>`
        )
        .join('');
    const tplCards = TEMPLATES.map(
        (id) =>
            `<div class="sx-tpl ${tpl === id ? 'on' : ''}" data-tpl="${id}"><div class="sx-tpl-pv" style="border-top:3px solid ${tpl === id ? color : 'var(--line)'}"></div><div class="sx-tpl-nm">${escapeHtml(t('sx-acc-tpl-' + id))}</div></div>`
    ).join('');
    const swatches = COLORS.map(
        (c) =>
            `<span class="sx-sw ${color === c ? 'on' : ''}" data-color="${c}" style="background:${c}"></span>`
    ).join('');
    return `<div class="sx-field"><label>${escapeHtml(t('sx-acc-pick'))}</label><select id="sx-acc-sel">${sellerOpts}</select></div>
    <div class="sx-acc-grid">
        <div class="sx-field"><label>${escapeHtml(t('sx-acc-name'))}</label><input type="text" id="sx-a-name" value="${htmlVal(s.name)}" maxlength="200"></div>
        <div class="sx-field"><label>${escapeHtml(t('sx-acc-tax'))}</label><input type="text" id="sx-a-tax" value="${htmlVal(s.tax_id)}" maxlength="20"></div>
    </div>
    <div class="sx-field"><label>${escapeHtml(t('sx-acc-address'))}</label><input type="text" id="sx-a-addr" value="${htmlVal(s.address)}" maxlength="500"></div>
    <div class="sx-acc-grid">
        <div class="sx-field"><label>${escapeHtml(t('sx-acc-branch'))}</label><input type="text" id="sx-a-branch" value="${htmlVal(s.branch)}" maxlength="120"></div>
        <div class="sx-field"><label>${escapeHtml(t('sx-acc-phone'))}</label><input type="text" id="sx-a-phone" value="${htmlVal(s.phone)}" maxlength="50"></div>
    </div>
    <div class="sx-field"><label>${escapeHtml(t('sx-acc-promptpay'))}</label><input type="text" id="sx-a-pp" value="${htmlVal(s.promptpay_id)}" maxlength="40" placeholder="08x-xxx-xxxx / ${escapeHtml(t('sx-acc-tax'))}"></div>

    <div class="sx-head" style="margin-top:18px"><h2 style="font-size:14px">${escapeHtml(t('sx-acc-sec-brand'))}</h2></div>
    <div class="sx-acc-grid">
        <div class="sx-field"><label>${escapeHtml(t('sx-acc-logo'))}</label><input type="text" id="sx-a-logo" value="${htmlVal(s.logo_url)}" maxlength="500" placeholder="https://…"></div>
        <div class="sx-field"><label>${escapeHtml(t('sx-acc-seal'))}</label><input type="text" id="sx-a-seal" value="${htmlVal(s.seal_url)}" maxlength="500" placeholder="https://…"></div>
    </div>
    <div class="sx-field"><label>${escapeHtml(t('sx-acc-sign'))}</label><input type="text" id="sx-a-sign" value="${htmlVal(s.signature_url)}" maxlength="500" placeholder="https://…"></div>
    <div class="sx-field"><label>${escapeHtml(t('sx-acc-footer'))}</label><textarea id="sx-a-footer" rows="2" maxlength="500">${htmlVal(s.footer_text)}</textarea></div>

    <div class="sx-head" style="margin-top:18px"><h2 style="font-size:14px">${escapeHtml(t('sx-acc-sec-template'))}</h2></div>
    <div class="sx-tpls">${tplCards}</div>
    <div class="sx-head" style="margin-top:14px"><h2 style="font-size:14px">${escapeHtml(t('sx-acc-sec-color'))}</h2></div>
    <div style="display:flex;gap:10px">${swatches}</div>

    <button class="btn btn-primary" id="sx-a-save" style="margin-top:18px">${escapeHtml(t('sx-acc-save'))}</button>`;
}

function render() {
    const body = document.getElementById('sx-acc-body');
    if (!body) return;
    body.innerHTML = formHtml();
    bind();
}

function selectSeller(i: number) {
    idx = i;
    const s = cur();
    tpl = (s && s.template_id) || 'classic';
    color = (s && s.brand_color) || '#2563eb';
    render();
}

function bind() {
    const sel = document.getElementById('sx-acc-sel') as HTMLSelectElement | null;
    if (sel) sel.onchange = () => selectSeller(+sel.value);
    document.querySelectorAll<HTMLElement>('[data-tpl]').forEach((el) => {
        el.onclick = () => {
            tpl = el.dataset.tpl!;
            render();
        };
    });
    document.querySelectorAll<HTMLElement>('[data-color]').forEach((el) => {
        el.onclick = () => {
            color = el.dataset.color!;
            render();
        };
    });
    const save = document.getElementById('sx-a-save');
    if (save) save.onclick = doSave;
}

async function doSave() {
    const s = cur();
    if (!s) return;
    const val = (id: string) => (document.getElementById(id) as HTMLInputElement).value.trim();
    const payload = {
        name: val('sx-a-name'),
        tax_id: val('sx-a-tax') || null,
        address: val('sx-a-addr') || null,
        branch: val('sx-a-branch') || null,
        phone: val('sx-a-phone') || null,
        promptpay_id: val('sx-a-pp') || null,
        logo_url: val('sx-a-logo') || null,
        seal_url: val('sx-a-seal') || null,
        signature_url: val('sx-a-sign') || null,
        footer_text:
            (document.getElementById('sx-a-footer') as HTMLTextAreaElement).value.trim() || null,
        template_id: tpl,
        brand_color: color,
    };
    try {
        const r = await salesFetch(`/api/sales/sellers/${s.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!r.ok) throw new Error();
        Object.assign(s, payload);
        showToast(t('sx-acc-saved'), 'success');
    } catch (_) {
        showToast(t('sx-acc-save-fail'), 'error');
    }
}

async function load() {
    const body = document.getElementById('sx-acc-body');
    if (body) body.innerHTML = `<div class="sx-state">${escapeHtml(t('sx-loading'))}</div>`;
    try {
        const data = await apiGet('/api/sales/sellers');
        if (!data) return;
        sellers = (data.sellers || []) as Seller[];
        idx = 0;
        selectSeller(0);
    } catch (_) {
        if (body)
            body.innerHTML = `<div class="sx-state error">${escapeHtml(t('sx-error'))}<br><button class="btn btn-ghost" id="sx-acc-retry">${escapeHtml(t('sx-retry'))}</button></div>`;
        const retry = document.getElementById('sx-acc-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadSalesAccount = function () {
    const sec = document.getElementById('page-sales-account');
    if (!sec) return;
    if (sec.dataset.sxInit !== '1') {
        sec.innerHTML = `<div class="sx-page"><div class="sx-head"><h2>${escapeHtml(t('nav-sales-account'))}</h2><span class="sx-sub">กิจการ / ข้อมูลออกบิล</span></div><div id="sx-acc-body" style="max-width:680px"></div></div>`;
        sec.dataset.sxInit = '1';
    }
    load();
};
