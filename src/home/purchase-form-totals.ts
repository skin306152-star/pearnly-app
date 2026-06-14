// 商户采购 · 复核屏汇总卡(价内外切换 + 手动改额四项 + 一致性校验)。从 purchase-form 抽出保 <500。
// 手动改额(高风险兜底):开关打开后可改 小计/折扣/VAT/合计 对齐票面 + 实时一致性(净+VAT+WHT=合计±0.01);
// 过账权威仍在后端(amount_override 再校验借贷平)· 前端只做即时反馈 + 拦明显不平。
/* global t, escapeHtml */
import type { FormState } from './purchase-form-types.js';
import { computeForm, overrideConsistent } from './purchase-form-lines.js';

export function totalsCardHtml(st: FormState): string {
    return `<div class="card"><div class="hd">${escapeHtml(t('pur-totals'))}
        <span class="swrow" id="pur-manual-tog" style="font-size:12px;"><span>${escapeHtml(t('pur-manual-edit'))}</span><span class="sw ${st.manualOn ? 'on' : ''}"></span></span>
    </div><div class="bd">
        <div class="seg sm2" id="pur-pricemode" style="margin-bottom:12px;"><div class="o ${st.priceMode === 'exclusive' ? 'on' : ''}" data-pm="exclusive">${escapeHtml(t('pur-price-ex'))}</div><div class="o ${st.priceMode === 'inclusive' ? 'on' : ''}" data-pm="inclusive">${escapeHtml(t('pur-price-in'))}</div></div>
        <div id="pur-totals">${totalsHtml(st)}</div>
    </div></div>`;
}

export function totalsHtml(st: FormState): string {
    const r = computeForm(st);
    const m = st.manualOn;
    const cell = (key: keyof FormState['override'], val: string) =>
        m
            ? `<input class="medit tnum" type="number" data-ov="${key}" value="${st.override[key]}">`
            : `<span class="tnum">฿${val}</span>`;
    const vatRow = st.hasVat
        ? `<div class="sum"><span>${escapeHtml(t('pur-vat-in'))} <span class="pill ok">${escapeHtml(t('pur-creditable'))}</span></span>${cell('vat', r.vat_amount)}</div>`
        : '';
    const whtRow =
        Number(r.wht_amount) > 0
            ? `<div class="sum"><span>${escapeHtml(t('pur-wht'))} <span class="pill warn">${escapeHtml(t('pur-withheld'))}</span></span><span class="tnum wht">−฿${r.wht_amount}</span></div>`
            : '';
    const consist = m
        ? overrideConsistent(st)
            ? `<div class="consist ok">${escapeHtml(t('pur-consist-ok'))}</div>`
            : `<div class="consist bad">${escapeHtml(t('pur-consist-bad'))}</div>`
        : '';
    return `<div class="sum"><span>${escapeHtml(t('pur-subtotal'))}</span>${cell('subtotal', r.subtotal)}</div>
        <div class="sum"><span>${escapeHtml(t('pur-discount'))}</span>${cell('discount', r.discount_total)}</div>
        ${vatRow}
        <div class="sum mid"><span>${escapeHtml(t('pur-grand'))}</span>${cell('grand', r.grand_total)}</div>
        ${whtRow}
        <div class="sum tot"><span>${escapeHtml(t('pur-net-payable'))}</span><span class="tnum">฿${r.net_payable}</span></div>
        ${consist}`;
}

// 进入手动模式时用当前自动算值初始化 override 四项(用户在此基础上对齐票面)。
function seedOverride(st: FormState): void {
    const r = computeForm({ ...st, manualOn: false });
    st.override = {
        subtotal: Number(r.subtotal),
        discount: Number(r.discount_total),
        vat: Number(r.vat_amount),
        grand: Number(r.grand_total),
    };
}

export function bindTotals(st: FormState, refresh: () => void): void {
    const tog = document.getElementById('pur-manual-tog');
    if (tog)
        tog.onclick = () => {
            st.manualOn = !st.manualOn;
            if (st.manualOn) seedOverride(st);
            refresh();
        };
    document.querySelectorAll<HTMLElement>('#pur-pricemode [data-pm]').forEach((el) => {
        el.onclick = () => {
            st.priceMode = el.dataset.pm as 'exclusive' | 'inclusive';
            refresh();
        };
    });
    document.querySelectorAll<HTMLInputElement>('#pur-totals [data-ov]').forEach((el) => {
        el.oninput = () => {
            const k = el.dataset.ov as keyof FormState['override'];
            st.override[k] = Number(el.value) || 0;
            refreshTotalsOnly(st);
        };
    });
}

// 仅重渲汇总数字(不重建明细)· 手动改额时即时刷新一致性,避免输入框失焦。
function refreshTotalsOnly(st: FormState): void {
    const box = document.getElementById('pur-totals');
    if (!box) return;
    const consist = box.querySelector('.consist');
    if (consist) {
        const okC = overrideConsistent(st);
        consist.className = 'consist ' + (okC ? 'ok' : 'bad');
        consist.textContent = okC ? t('pur-consist-ok') : t('pur-consist-bad');
    }
    const net = box.querySelector('.sum.tot .tnum');
    if (net) net.textContent = '฿' + computeForm(st).net_payable;
}
