// 销项 PO-10 · 开票设置(右上齿轮弹窗)· 接真接口 GET/PUT /api/sales/settings(§M7)
// 照 app.html settingsModal:号码格式预览 / WHT 下拉 / 纸张含 80mm / 省纸复选。
// 交互(seg/下拉/复选)只改状态 + 就地 toggle,不整体 render → 不闪、不回顶。
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
// WHT 档位(照草稿):值 + 类型标签 i18n 键;另加「自定义」可填任意率。
const WHT_OPTS: [string, string][] = [
    ['0', 'sx-wht-none'],
    ['1', 'sx-wht-transport'],
    ['2', 'sx-wht-ad'],
    ['3', 'sx-wht-service'],
    ['5', 'sx-wht-rent'],
];

let st: Settings;

function mask(): HTMLElement {
    let m = document.getElementById('sales-settings-mask');
    if (!m) {
        m = document.createElement('div');
        m.id = 'sales-settings-mask';
        m.className = 'modal-mask sx-modal-mask';
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

// seg:就地切换(改状态 + 同组 .on),不整体 render(避免滚动回顶/闪)
function seg(field: keyof Settings, opts: [string, string][]): string {
    return `<div class="sx-seg" data-seg="${String(field)}" style="width:100%">${opts
        .map(
            (o) =>
                `<button type="button" data-seg-v="${o[0]}" class="${String(st[field]) === o[0] ? 'on' : ''}" style="flex:1">${escapeHtml(o[1])}</button>`
        )
        .join('')}</div>`;
}

function numberPreview(): string {
    const prefix = st.number_prefix || 'INV';
    const year = new Date().getFullYear();
    return `${escapeHtml(prefix)}${year}-00001`;
}

function render() {
    const whtCur = String(Number(st.default_wht_rate) || 0);
    const whtPreset = WHT_OPTS.some((o) => o[0] === whtCur);
    const whtOpts =
        WHT_OPTS.map(
            ([r, k]) =>
                `<option value="${r}" ${whtCur === r ? 'selected' : ''}>${r}% ${escapeHtml(t(k))}</option>`
        ).join('') +
        `<option value="custom" ${!whtPreset ? 'selected' : ''}>${escapeHtml(t('sx-wht-custom'))}</option>`;
    mask().innerHTML = `<div class="modal" role="dialog" style="max-width:560px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t('sx-set-title'))}</div>
            <button class="modal-close" id="sx-set-close">${IC_X}</button></div>
        <div class="modal-body">
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t('sx-set-num'))}</div>
                <div class="sx-set-row3">
                    <div class="sx-field"><label>${escapeHtml(t('sx-set-prefix'))}</label><input type="text" id="sx-set-prefix" value="${escapeHtml(st.number_prefix || '')}" maxlength="20" placeholder="INV"></div>
                    <div class="sx-field"><label>${escapeHtml(t('sx-set-reset'))}</label>${seg(
                        'number_reset',
                        [
                            ['yearly', t('sx-set-reset-yearly')],
                            ['monthly', t('sx-set-reset-monthly')],
                            ['never', t('sx-set-reset-never')],
                        ]
                    )}</div>
                    <div class="sx-field"><label>${escapeHtml(t('sx-set-start'))}</label><input type="number" id="sx-set-start" value="${st.number_start || 1}" min="1"></div>
                </div>
                <div class="sx-hint">${escapeHtml(t('sx-set-num-preview'))}: <b id="sx-set-preview">${numberPreview()}</b> · ${escapeHtml(t('sx-set-num-preview-note'))}</div>
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
                <select id="sx-set-wht" style="width:100%">${whtOpts}</select>
                <input type="number" id="sx-set-wht-custom" min="0" max="100" step="0.5" value="${whtPreset ? '' : Number(st.default_wht_rate) || 0}" placeholder="%" style="width:120px;margin-top:8px;${whtPreset ? 'display:none' : ''}">
                <div class="sx-hint">${escapeHtml(t('sx-set-wht-hint'))}</div>
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t('sx-set-output'))}</div>
                <div class="sx-field"><label>${escapeHtml(t('sx-set-lang'))}</label>${seg(
                    'default_doc_lang',
                    [
                        ['th', t('sx-set-lang-th')],
                        ['th_en', t('sx-set-lang-then')],
                        ['th_zh', t('sx-set-lang-thzh')],
                    ]
                )}</div>
                <div class="sx-field"><label>${escapeHtml(t('sx-set-paper'))}</label>${seg(
                    'default_paper',
                    [
                        ['A4', 'A4'],
                        ['A5', 'A5'],
                        ['80mm', '80mm'],
                    ]
                )}</div>
                <label style="display:flex;align-items:center;gap:8px;margin-top:8px;cursor:pointer"><input type="checkbox" id="sx-set-2up" ${st.default_copies_layout === 'two_up' ? 'checked' : ''} style="width:auto"> ${escapeHtml(t('sx-set-copies-2up'))}</label>
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
    // seg 就地切换:不 render(避免滚动回顶 + 失焦)
    mask()
        .querySelectorAll<HTMLElement>('[data-seg]')
        .forEach((grp) => {
            const field = grp.dataset.seg as keyof Settings;
            grp.querySelectorAll<HTMLElement>('[data-seg-v]').forEach((btn) => {
                btn.onclick = () => {
                    const v = btn.dataset.segV!;
                    (st[field] as unknown) =
                        field === 'price_includes_vat_default' ? v === 'true' : v;
                    grp.querySelectorAll<HTMLElement>('[data-seg-v]').forEach((b) =>
                        b.classList.toggle('on', b.dataset.segV === v)
                    );
                };
            });
        });
    const prefix = document.getElementById('sx-set-prefix') as HTMLInputElement | null;
    if (prefix)
        prefix.oninput = () => {
            st.number_prefix = prefix.value;
            const pv = document.getElementById('sx-set-preview');
            if (pv) pv.textContent = numberPreview();
        };
    const wht = document.getElementById('sx-set-wht') as HTMLSelectElement | null;
    const whtCustom = document.getElementById('sx-set-wht-custom') as HTMLInputElement | null;
    if (wht)
        wht.onchange = () => {
            const custom = wht.value === 'custom';
            if (whtCustom) whtCustom.style.display = custom ? '' : 'none';
            st.default_wht_rate = custom ? Number(whtCustom?.value) || 0 : wht.value;
        };
    if (whtCustom) whtCustom.oninput = () => (st.default_wht_rate = Number(whtCustom.value) || 0);
    const twoUp = document.getElementById('sx-set-2up') as HTMLInputElement | null;
    if (twoUp)
        twoUp.onchange = () => (st.default_copies_layout = twoUp.checked ? 'two_up' : 'separate');
    document.getElementById('sx-set-save')!.onclick = save;
}

async function save() {
    const payload = {
        number_prefix:
            (document.getElementById('sx-set-prefix') as HTMLInputElement).value.trim() || null,
        number_reset: st.number_reset,
        number_start:
            Number((document.getElementById('sx-set-start') as HTMLInputElement).value) || 1,
        approval_mode: st.approval_mode,
        price_includes_vat_default: st.price_includes_vat_default,
        default_wht_rate: Number(st.default_wht_rate) || 0,
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
