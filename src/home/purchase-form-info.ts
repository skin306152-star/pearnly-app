// 商户采购 · 复核屏单据信息卡(字段三态 + 分店/税票/币种联动 + 硬必填校验)。从 purchase-form 抽出保 <500。
// 三态:已识别绿(ok·field_confidence 高)/ 请确认琥珀(fix·低)/ 需补红(need·必填且空·主动显红)。
// 税票号 = doc_no(docs §十三#3,无独立列);分店名派生不存独立列(拍板#3)。
/* global t, escapeHtml */
import type { FormState } from './purchase-form-types.js';

const CURRENCIES = ['THB', 'USD', 'EUR', 'CNY', 'JPY', 'SGD'];

export interface MissingField {
    field: string;
    label: string;
}

// field_confidence(0~1)→ 三态映射:高(≥0.8)已识别;低请确认。键 = OCR invoice 属性名
// (services/ocr/page_runner _FIELD_CONF_ATTRS)→ 归一到信息卡字段名。
export function mapConf(fc: Record<string, number> | undefined): Record<string, 'ok' | 'fix'> {
    const out: Record<string, 'ok' | 'fix'> = {};
    if (!fc) return out;
    const alias: Record<string, string> = {
        invoice_number: 'doc_no',
        doc_no: 'doc_no',
        seller_tax: 'tax_id',
        tax_id: 'tax_id',
        date: 'doc_date',
        doc_date: 'doc_date',
        seller_name: 'supplier',
        supplier_name: 'supplier',
        supplier: 'supplier',
    };
    for (const k in fc) {
        const key = alias[k] || k;
        out[key] = fc[k] >= 0.8 ? 'ok' : 'fix';
    }
    return out;
}

// 给定当前 toggle 状态,该必填字段是否空(需补红 · 主动)。
export function isReqEmpty(st: FormState, key: string): boolean {
    if (key === 'supplier') return !st.supplierName.trim();
    if (key === 'doc_date') return !st.docDate.trim();
    if (key === 'doc_no') return st.hasVat && !st.docNo.trim(); // 税票号
    if (key === 'branchNo') return st.branchType === 'branch' && !st.branchNo.trim();
    if (key === 'fx') return st.currency !== 'THB' && !(Number(st.fxRate) > 0);
    return false;
}
// 字段态:必填空 → need;否则按 field_confidence 高/低 → ok/fix;其余普通。
function stateOf(st: FormState, key: string): 'ok' | 'fix' | 'need' | '' {
    if (isReqEmpty(st, key)) return 'need';
    const c = st.fieldConf[key];
    return c === 'ok' ? 'ok' : c === 'fix' ? 'fix' : '';
}
function tag(st: FormState, key: string): string {
    const s = stateOf(st, key);
    if (s === 'ok') return `<span class="tg tg-ok">${escapeHtml(t('pur-tag-read'))}</span>`;
    if (s === 'fix') return `<span class="tg tg-fix">${escapeHtml(t('pur-tag-confirm'))}</span>`;
    if (s === 'need') return `<span class="tg tg-need">${escapeHtml(t('pur-tag-need'))}</span>`;
    return '';
}
function cls(st: FormState, key: string): string {
    const s = stateOf(st, key);
    return s ? 'field ' + s : 'field';
}
function req(): string {
    return ' <span class="req">*</span>';
}

export function infoCardHtml(st: FormState): string {
    const k = st.doc_kind;
    const isBranch = st.branchType === 'branch';
    const nonThb = st.currency !== 'THB';
    const curOpts = CURRENCIES.map(
        (c) => `<option value="${c}" ${c === st.currency ? 'selected' : ''}>${c}</option>`
    ).join('');
    // 单号/税票号同 doc_no:有税票 → 「税票号 *」必填;无税票 → 「单号」选填(docs §十三#3)。
    const docNoField = st.hasVat
        ? `<div class="${cls(st, 'doc_no')}" id="f-taxno"><label>${escapeHtml(t('pur-tax-no'))}${req()} ${tag(st, 'doc_no')}</label><div class="inp"><input class="fin" data-fld="docNo" value="${escapeHtml(st.docNo)}"></div><div class="et">${escapeHtml(t('pur-req-taxno'))}</div></div>`
        : `<div class="field"><label>${escapeHtml(t('pur-doc-no'))}</label><div class="inp"><input class="fin" data-fld="docNo" value="${escapeHtml(st.docNo)}"></div></div>`;
    return `<div class="card"><div class="hd">${escapeHtml(t('pur-doc-info'))}</div><div class="bd">
        <div class="field"><label>${escapeHtml(t('pur-type'))}</label><div class="seg" id="pur-kind">
            <div class="o ${k === 'purchase_invoice' ? 'on' : ''}" data-kind="purchase_invoice">${escapeHtml(t('pur-kind-invoice'))}</div>
            <div class="o ${k === 'expense' ? 'on' : ''}" data-kind="expense">${escapeHtml(t('pur-kind-expense'))}</div>
            <div class="o ${k === 'purchase_order' ? 'on' : ''}" data-kind="purchase_order">${escapeHtml(t('pur-kind-order'))}</div></div></div>
        <div class="${cls(st, 'supplier')}" id="f-supplier"><label>${escapeHtml(t('pur-supplier'))}${req()} ${tag(st, 'supplier')}</label><div class="inp pick" id="pur-supplier-pick">${escapeHtml(st.supplierName || t('pur-supplier-choose'))} <span style="color:var(--ink3)">${escapeHtml(t('pur-switch'))} ▾</span></div><div class="et">${escapeHtml(t('pur-req-supplier'))}</div></div>
        <div class="two">
            <div class="${cls(st, 'tax_id')}"><label>${escapeHtml(t('pur-tax-id'))} ${tag(st, 'tax_id')}</label><div class="inp"><input class="fin tnum" data-fld="taxId" value="${escapeHtml(st.taxId)}" placeholder=""></div></div>
            <div class="field"><label>${escapeHtml(t('pur-branch'))}</label><div class="inp"><select class="fsel" id="pur-branchtype" data-fld="branchType"><option value="head_office" ${st.branchType === 'head_office' ? 'selected' : ''}>${escapeHtml(t('pur-branch-head'))}</option><option value="branch" ${st.branchType === 'branch' ? 'selected' : ''}>${escapeHtml(t('pur-branch-sub'))}</option><option value="none" ${st.branchType === 'none' ? 'selected' : ''}>${escapeHtml(t('pur-branch-na'))}</option></select></div></div>
        </div>
        <div class="two ${isBranch ? '' : 'hide'}" id="pur-branchfields">
            <div class="${cls(st, 'branchNo')}" id="f-branchcode"><label>${escapeHtml(t('pur-branch-code'))}${req()} ${tag(st, 'branchNo')}</label><div class="inp"><input class="fin tnum" data-fld="branchNo" value="${escapeHtml(st.branchNo)}" placeholder="00000"></div><div class="et">${escapeHtml(t('pur-req-branchcode'))}</div></div>
            <div class="field"><label>${escapeHtml(t('pur-branch-name'))}</label><div class="inp"><input class="fin" data-fld="branchName" value="${escapeHtml(st.branchName)}"></div></div>
        </div>
        <div class="field"><label>${escapeHtml(t('pur-address'))}</label><div class="inp"><input class="fin" data-fld="address" value="${escapeHtml(st.address)}" placeholder="—"></div></div>
        <div class="two">
            <div class="${cls(st, 'doc_date')}" id="f-docdate"><label>${escapeHtml(t('pur-doc-date'))}${req()} ${tag(st, 'doc_date')}</label><div class="inp"><input class="fin tnum" type="date" data-fld="docDate" value="${escapeHtml(st.docDate)}"></div><div class="et">${escapeHtml(t('pur-req-docdate'))}</div></div>
            ${docNoField}
        </div>
        <div class="field"><label>${escapeHtml(t('pur-has-vat'))}</label><div class="seg sm2" id="pur-hasvat"><div class="o ${st.hasVat ? 'on' : ''}" data-vat="1">${escapeHtml(t('pur-yes'))}</div><div class="o ${st.hasVat ? '' : 'on'}" data-vat="0">${escapeHtml(t('pur-no'))}</div></div></div>
        <div class="two">
            <div class="field"><label>${escapeHtml(t('pur-pay-status'))}</label><div class="seg sm2" id="pur-pay"><div class="o ${st.paymentStatus === 'paid' ? 'on' : ''}" data-pay="paid">${escapeHtml(t('pur-pay-paid'))}</div><div class="o ${st.paymentStatus === 'unpaid' ? 'on' : ''}" data-pay="unpaid">${escapeHtml(t('pur-pay-ap'))}</div></div></div>
            <div class="field"><label>${escapeHtml(t('pur-currency'))}</label><div class="inp"><select class="fsel" id="pur-cur" data-fld="currency">${curOpts}</select></div></div>
        </div>
        <div class="${cls(st, 'fx')} ${nonThb ? '' : 'hide'}" id="f-fx"><label>${escapeHtml(t('pur-fx-rate'))}${req()}</label><div class="inp"><input class="fin tnum" type="number" data-fld="fxRate" value="${st.fxRate}" placeholder="36.5"></div><div class="et">${escapeHtml(t('pur-req-fx'))}</div></div>
    </div></div>`;
}

// 仅「确认入账」触发的硬必填:返回缺项(供 banner 列 + 红框);存草稿不校验。
export function validateInfo(st: FormState): MissingField[] {
    const miss: MissingField[] = [];
    if (!st.docDate.trim()) miss.push({ field: 'f-docdate', label: t('pur-doc-date') });
    if (!st.supplierName.trim()) miss.push({ field: 'f-supplier', label: t('pur-supplier') });
    if (st.branchType === 'branch' && !st.branchNo.trim())
        miss.push({ field: 'f-branchcode', label: t('pur-branch-code') });
    if (st.hasVat && !st.docNo.trim()) miss.push({ field: 'f-taxno', label: t('pur-tax-no') });
    if (st.currency !== 'THB' && !(Number(st.fxRate) > 0))
        miss.push({ field: 'f-fx', label: t('pur-fx-rate') });
    return miss;
}

// 校验后在 DOM 上加/去红框(.field.err)· clearErr 在用户改动后调。
export function markErrors(miss: MissingField[]): void {
    document.querySelectorAll('.pur .field.err').forEach((e) => e.classList.remove('err'));
    miss.forEach((m) => document.getElementById(m.field)?.classList.add('err'));
}
