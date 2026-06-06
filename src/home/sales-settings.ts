// 销项 PO-10 · 开票设置(右上齿轮弹窗)· 接真接口 GET/PUT /api/sales/settings(§M7)
// 连号前缀/重置/起始号 · 审批模式 · 价内外默认 · WHT 默认 · 默认语言/纸张/省纸。租户级默认,开票时可单据覆盖。
/* global t, escapeHtml, apiGet, showToast */
import { salesFetch } from './sales-common.js';

interface Settings {
    number_prefix?: string | null;
    number_reset: string;
    number_start: number;
    approval_mode: string;
    price_includes_vat_default: boolean;
    default_wht_rate: string | number;
    default_doc_lang: string;
    default_paper: string;
    default_copies_layout: string;
}

const IC_X =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>';

let st: Settings;

function mask(): HTMLElement {
    let m = document.getElementById('sales-settings-mask');
    if (!m) {
        m = document.createElement('div');
        m.id = 'sales-settings-mask';
        m.className = 'modal-mask';
        m.style.display = 'none';
        document.body.appendChild(m);
    }
    return m;
}
function close() {
    const m = document.getElementById('sales-settings-mask');
    if (m) {
        m.style.display = 'none';
        m.innerHTML = '';
    }
}

function seg(field: keyof Settings, opts: [string, string][]): string {
    return `<div class="sx-seg" style="width:100%">${opts
        .map(
            (o) =>
                `<button type="button" data-f="${String(field)}" data-v="${o[0]}" class="${String(st[field]) === o[0] ? 'on' : ''}" style="flex:1">${escapeHtml(o[1])}</button>`
        )
        .join('')}</div>`;
}

function render() {
    mask().innerHTML = `<div class="modal" role="dialog" style="max-width:560px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t('sx-set-title'))}</div>
            <button class="modal-close" id="sx-set-close">${IC_X}</button></div>
        <div class="modal-body">
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t('sx-set-num'))}</div>
                <div class="sx-acc-grid">
                    <div class="sx-field"><label>${escapeHtml(t('sx-set-prefix'))}</label><input type="text" id="sx-set-prefix" value="${escapeHtml(st.number_prefix || '')}" maxlength="20" placeholder="INV"></div>
                    <div class="sx-field"><label>${escapeHtml(t('sx-set-start'))}</label><input type="number" id="sx-set-start" value="${st.number_start || 1}" min="1"></div>
                </div>
                <div class="sx-field"><label>${escapeHtml(t('sx-set-reset'))}</label>
                    ${seg('number_reset', [
                        ['yearly', t('sx-set-reset-yearly')],
                        ['monthly', t('sx-set-reset-monthly')],
                        ['never', t('sx-set-reset-never')],
                    ])}</div>
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t('sx-set-approval'))}</div>
                ${seg('approval_mode', [
                    ['none', t('sx-set-appr-none')],
                    ['single', t('sx-set-appr-single')],
                ])}
                <div class="sx-hint">${escapeHtml(t('sx-set-appr-hint'))}</div>
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t('sx-set-vat'))}</div>
                ${seg('price_includes_vat_default', [
                    ['false', t('sx-set-vat-ex')],
                    ['true', t('sx-set-vat-in')],
                ])}
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t('sx-set-wht'))}</div>
                <input type="number" id="sx-set-wht" value="${Number(st.default_wht_rate) || 0}" min="0" max="100" step="0.5" style="max-width:160px">
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t('sx-set-output'))}</div>
                <div class="sx-field"><label>${escapeHtml(t('sx-set-lang'))}</label>
                    ${seg('default_doc_lang', [
                        ['th', t('sx-set-lang-th')],
                        ['th_en', t('sx-set-lang-then')],
                        ['th_zh', t('sx-set-lang-thzh')],
                    ])}</div>
                <div class="sx-field"><label>${escapeHtml(t('sx-set-paper'))}</label>
                    ${seg('default_paper', [
                        ['A4', 'A4'],
                        ['A5', 'A5'],
                    ])}</div>
                <div class="sx-field"><label>${escapeHtml(t('sx-set-copies'))}</label>
                    ${seg('default_copies_layout', [
                        ['separate', t('sx-set-copies-sep')],
                        ['two_up', t('sx-set-copies-2up')],
                    ])}</div>
            </div>
        </div>
        <div class="modal-footer" style="justify-content:space-between">
            <span class="sx-hint">${escapeHtml(t('sx-set-note'))}</span>
            <button class="btn btn-primary" id="sx-set-save">${escapeHtml(t('sx-set-save'))}</button>
        </div></div>`;
    mask().style.display = 'flex';
    bind();
}

function bind() {
    document.getElementById('sx-set-close')!.onclick = close;
    mask().onclick = (e) => {
        if (e.target === mask()) close();
    };
    mask()
        .querySelectorAll<HTMLElement>('[data-f]')
        .forEach((el) => {
            el.onclick = () => {
                const f = el.dataset.f as keyof Settings;
                const v = el.dataset.v!;
                (st[f] as unknown) = f === 'price_includes_vat_default' ? v === 'true' : v;
                render();
            };
        });
    document.getElementById('sx-set-save')!.onclick = save;
}

async function save() {
    const prefix = (document.getElementById('sx-set-prefix') as HTMLInputElement).value.trim();
    const payload = {
        number_prefix: prefix || null,
        number_reset: st.number_reset,
        number_start:
            Number((document.getElementById('sx-set-start') as HTMLInputElement).value) || 1,
        approval_mode: st.approval_mode,
        price_includes_vat_default: st.price_includes_vat_default,
        default_wht_rate:
            Number((document.getElementById('sx-set-wht') as HTMLInputElement).value) || 0,
        default_doc_lang: st.default_doc_lang,
        default_paper: st.default_paper,
        default_copies_layout: st.default_copies_layout,
    };
    try {
        const r = await salesFetch('/api/sales/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!r.ok) throw new Error();
        close();
        showToast(t('sx-set-saved'), 'success');
    } catch (_) {
        showToast(t('sx-set-save-fail'), 'error');
    }
}

window.openSalesSettings = async function () {
    mask().innerHTML = `<div class="modal" role="dialog" style="max-width:560px"><div class="modal-body"><div class="sx-state">${escapeHtml(t('sx-loading'))}</div></div></div>`;
    mask().style.display = 'flex';
    try {
        const data = await apiGet('/api/sales/settings');
        if (!data) return;
        st = data.settings as Settings;
        render();
    } catch (_) {
        mask().innerHTML = `<div class="modal" role="dialog" style="max-width:480px"><div class="modal-body"><div class="sx-state error">${escapeHtml(t('sx-error'))}</div></div></div>`;
        mask().onclick = (e) => {
            if (e.target === mask()) close();
        };
    }
};
