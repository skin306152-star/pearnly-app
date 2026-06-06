// 销项开票向导 PO-10 · 发票预览(核对步用)· 从 index.html 样稿移植
// 文档语言(印在票上的语言)独立于界面语言;省纸正副本同页;热敏窄版。
/* global escapeHtml */
import { type WState, calc, money, bahtText, cnText, payApplicable } from './sales-wizard-calc.js';
import { getSellers } from './sales-wizard-io.js';

// 印在票面的字段标签(th / en / zh · 不走 UI i18n · 跟随单据语言设置)
const DOCL: Record<string, { th: string; en: string; zh: string }> = {
    no: { th: 'เลขที่', en: 'No.', zh: '号码' },
    date: { th: 'วันที่', en: 'Date', zh: '日期' },
    seller: { th: 'ผู้ขาย', en: 'Seller', zh: '卖方' },
    buyer: { th: 'ผู้ซื้อ', en: 'Buyer', zh: '买方' },
    desc: { th: 'รายการ', en: 'Description', zh: '商品' },
    qty: { th: 'จำนวน', en: 'Qty', zh: '数量' },
    price: { th: 'ราคา', en: 'Price', zh: '单价' },
    disc: { th: 'ส่วนลด', en: 'Discount', zh: '折扣' },
    amount: { th: 'จำนวนเงิน', en: 'Amount', zh: '金额' },
    subtotal: { th: 'มูลค่า', en: 'Subtotal', zh: '小计' },
    grand: { th: 'รวมทั้งสิ้น', en: 'Grand Total', zh: '合计' },
    words: { th: 'ตัวอักษร', en: 'In words', zh: '大写' },
    paid: { th: 'การรับเงิน', en: 'Payment', zh: '收款' },
    wht: { th: 'หัก ณ ที่จ่าย', en: 'WHT', zh: '预扣税' },
    signSeller: { th: 'ผู้รับเงิน / ผู้มีอำนาจ', en: 'Authorized', zh: '收款人/授权' },
    signBuyer: { th: 'ผู้ซื้อ', en: 'Buyer', zh: '买方签收' },
};
function dl(st: WState, k: string): string {
    const o = DOCL[k];
    if (st.docLang === 'th') return o.th;
    return o.th + ' / ' + (st.docLang === 'th_zh' ? o.zh : o.en);
}

const DOC_LABEL: Record<string, string> = {
    tax_invoice_receipt: 'ใบกำกับภาษี/ใบเสร็จรับเงิน · Tax Invoice / Receipt',
    tax_invoice: 'ใบกำกับภาษี · Tax Invoice',
    tax_invoice_simple: 'ใบกำกับภาษีอย่างย่อ · Simplified',
    receipt: 'ใบเสร็จรับเงิน · Receipt',
    quotation: 'ใบเสนอราคา · Quotation',
};
const METHODS_TH: Record<string, string> = {
    cash: 'เงินสด',
    transfer: 'โอน',
    promptpay: 'พร้อมเพย์',
    card: 'บัตร',
    cheque: 'เช็ค',
};

function fmtDate(st: WState, d: string): string {
    if (!d) return '-';
    if (st.be) {
        const p = d.split('-');
        return +p[0] + 543 + '-' + p[1] + '-' + p[2];
    }
    return d;
}

function invoiceHTML(st: WState, kind: 'original' | 'copy'): string {
    const s = getSellers()[st.sellerIdx] || {
        name: '',
        tax_id: '',
        address: '',
        branch: '',
        phone: '',
    };
    const b = st.buyer;
    const c = calc(st);
    const tinLabel =
        b.type === 'individual' ? 'เลขบัตรประชาชน' : b.type === 'foreigner' ? 'Passport' : 'Tax ID';
    const buyerName = b.name || (b.type === 'anonymous' ? 'ลูกค้าทั่วไป' : '-');
    const buyerLines =
        b.type === 'anonymous' && !b.name
            ? ''
            : `<div class="sw-pl">${escapeHtml(b.addr) || ''}</div><div class="sw-pl">${tinLabel}: ${escapeHtml(b.tin) || '-'}</div>
               ${b.type === 'company' ? `<div class="sw-pl">${b.branchType === 'hq' ? 'สำนักงานใหญ่' : 'สาขาที่ ' + (escapeHtml(b.branchNo) || '-')}</div>` : ''}`;
    const items = st.lines
        .map(
            (l, i) =>
                `<tr><td>${i + 1}</td><td>${escapeHtml(l.desc) || '-'}</td><td class="r">${money(+l.qty || 0)}</td><td class="r">${money(+l.price || 0)}</td><td class="r">${+l.disc > 0 ? '-' + money(+l.disc) : '-'}</td><td class="r">${money(Math.max(0, (+l.qty || 0) * (+l.price || 0) - (+l.disc || 0)))}</td></tr>`
        )
        .join('');
    const payBox =
        payApplicable(st) && st.pay.status !== 'unpaid'
            ? `<div class="sw-inv-pay"><b>${dl(st, 'paid')}:</b> ${METHODS_TH[st.pay.method] || st.pay.method} · ${fmtDate(st, st.pay.date)} · ${st.pay.status === 'partial' ? '฿ ' + money(+(st.pay.paidAmt || 0)) : '฿ ' + money(c.grand)}</div>`
            : '';
    const words = st.docLang === 'th_zh' ? cnText(c.grand) : bahtText(c.grand);
    const isCopy = kind === 'copy';
    const badge = isCopy
        ? st.docLang === 'th'
            ? 'สำเนา'
            : 'สำเนา / Copy'
        : st.docLang === 'th'
          ? 'ต้นฉบับ'
          : 'ต้นฉบับ / Original';
    return `<div class="sw-invoice ${st.paper === 'pos' ? 'pos' : ''} ${st.layout === 'pair' ? 'half' : ''}">
        <div class="sw-copybadge ${isCopy ? 'copy' : ''}">${badge}</div>
        <h3>${DOC_LABEL[st.docType]}</h3>
        <div class="sw-docno">${dl(st, 'no')}: — &nbsp;·&nbsp; ${dl(st, 'date')}: ${fmtDate(st, st.issueDate)}${st.be ? ' (พ.ศ.)' : ''}</div>
        <div class="sw-inv-parties">
            <div><div class="sw-ptitle">${dl(st, 'seller')}</div>
                <div class="sw-pname">${escapeHtml(s.name || '')}</div><div class="sw-pl">${escapeHtml(s.address || '')}</div>
                <div class="sw-pl">Tax ID: ${escapeHtml(s.tax_id || '-')} · ${escapeHtml(s.branch || '')}</div></div>
            <div><div class="sw-ptitle">${dl(st, 'buyer')}</div>
                <div class="sw-pname">${escapeHtml(buyerName)}</div>${buyerLines}</div>
        </div>
        <table class="sw-inv-items">
            <thead><tr><th>#</th><th>${dl(st, 'desc')}</th><th class="r">${dl(st, 'qty')}</th><th class="r">${dl(st, 'price')}</th><th class="r">${dl(st, 'disc')}</th><th class="r">${dl(st, 'amount')}</th></tr></thead>
            <tbody>${items}</tbody>
        </table>
        <div class="sw-inv-tot">
            <div class="sw-tr"><span>${dl(st, 'subtotal')}</span><span>${money(c.subAfter)}</span></div>
            <div class="sw-tr"><span>VAT ${st.vatRate}%</span><span>${money(c.vat)}</span></div>
            ${c.wht > 0 ? `<div class="sw-tr"><span>${dl(st, 'wht')}</span><span>-${money(c.wht)}</span></div>` : ''}
            <div class="sw-tr g"><span>${dl(st, 'grand')}</span><span>฿ ${money(c.grand)}</span></div>
        </div>
        <div class="sw-inv-words"><b>${dl(st, 'words')}:</b> ${words}</div>
        ${payBox}
        <div class="sw-inv-sign"><div class="s">${dl(st, 'signSeller')}</div><div class="s">${dl(st, 'signBuyer')}</div></div>
    </div>`;
}

export function previewArea(st: WState, tearLabel: string, tearIcon: string): string {
    if (st.layout === 'pair' && st.paper !== 'pos') {
        return `<div class="sw-pairwrap">${invoiceHTML(st, 'original')}
            <div class="sw-tear"><span>${tearIcon} ${escapeHtml(tearLabel)}</span></div>
            ${invoiceHTML(st, 'copy')}</div>`;
    }
    return invoiceHTML(st, 'original');
}
