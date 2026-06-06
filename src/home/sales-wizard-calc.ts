// 销项开票向导 PO-10 · 纯计算叶子:金额合计 / 泰铢·中文大写 / 合规清单
// 无 DOM 无副作用 · 从 index.html 样稿逐函数移植(算法 verbatim)。被 wizard 主模块 import。

export interface WLine {
    desc: string;
    qty: number | string;
    price: number | string;
    disc: number | string;
    vat: boolean;
    custom?: boolean;
    save?: boolean;
    product_id?: string;
}
export interface WBuyer {
    type: 'company' | 'individual' | 'foreigner' | 'anonymous';
    name: string;
    addr: string;
    tin: string;
    branchType: 'hq' | 'branch';
    branchNo: string;
    verified?: boolean;
}
export interface WState {
    docType: string;
    sellerIdx: number;
    buyer: WBuyer;
    lines: WLine[];
    hdisc: number | string;
    vatRate: number | string;
    whtRate: number | string;
    pay: {
        status: 'paid' | 'partial' | 'unpaid';
        method: string;
        date: string;
        paidAmt: number | string | null;
    };
    issueDate: string;
    dueDate: string;
    be: boolean;
    paper: 'a4' | 'a5' | 'pos';
    docLang: 'th' | 'th_en' | 'th_zh';
    layout: 'single' | 'pair';
    draftId?: string | null;
}

export const FULL_TAX = ['tax_invoice', 'tax_invoice_receipt']; // 完整税票 → 买方必须齐全
const NEEDS_PAY = ['receipt', 'tax_invoice_receipt']; // 须已收款

export function payRequired(st: WState): boolean {
    return NEEDS_PAY.includes(st.docType);
}
export function payApplicable(st: WState): boolean {
    return st.docType !== 'quotation';
}

export function money(v: number): string {
    return (Math.round(v * 100) / 100).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

export interface Totals {
    sub: number;
    hd: number;
    subAfter: number;
    vat: number;
    wht: number;
    grand: number;
}
export function calc(st: WState): Totals {
    let sub = 0;
    let vatBase = 0;
    st.lines.forEach((l) => {
        const lt = Math.max(0, (+l.qty || 0) * (+l.price || 0) - (+l.disc || 0));
        sub += lt;
        if (l.vat) vatBase += lt;
    });
    const hd = Math.min(+st.hdisc || 0, sub);
    const ratio = sub > 0 ? (sub - hd) / sub : 1;
    vatBase *= ratio;
    const subAfter = sub - hd;
    const vat = (vatBase * (+st.vatRate || 0)) / 100;
    const wht = (subAfter * (+st.whtRate || 0)) / 100;
    const grand = subAfter + vat - wht;
    return { sub, hd, subAfter, vat, wht, grand };
}

// 泰铢大写(จำนวนเงินตัวอักษร)· 移植样稿 readBig 路径
function readMillionsGroup(s: string): string {
    const num = ['', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า'];
    const pos = ['', 'สิบ', 'ร้อย', 'พัน', 'หมื่น', 'แสน'];
    let r = '';
    const len = s.length;
    for (let i = 0; i < len; i++) {
        const d = +s[i];
        const p = len - 1 - i;
        if (d === 0) continue;
        if (p === 1 && d === 1) r += 'สิบ';
        else if (p === 1 && d === 2) r += 'ยี่สิบ';
        else if (p === 0 && d === 1 && len > 1) r += 'เอ็ด';
        else r += num[d] + pos[p];
    }
    return r;
}
function readBig(x: number): string {
    if (x === 0) return 'ศูนย์';
    const groups: string[] = [];
    let s = String(x);
    while (s.length > 6) {
        groups.unshift(s.slice(-6));
        s = s.slice(0, -6);
    }
    groups.unshift(s);
    let res = '';
    groups.forEach((g, idx) => {
        const val = +g;
        if (val === 0) return;
        res += readMillionsGroup(String(val));
        const left = groups.length - 1 - idx;
        for (let k = 0; k < left; k++) res += 'ล้าน';
    });
    return res;
}
export function bahtText(n: number): string {
    n = Math.round(n * 100) / 100;
    const bahts = Math.floor(n);
    const satang = Math.round((n - bahts) * 100);
    let txt = readBig(bahts) + 'บาท';
    txt += satang === 0 ? 'ถ้วน' : readBig(satang) + 'สตางค์';
    return txt;
}
// 中文大写(演示)· 移植样稿 cnText
export function cnText(n: number): string {
    n = Math.round(n * 100) / 100;
    const i = Math.floor(n);
    const s = Math.round((n - i) * 100);
    const d = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'];
    const u = ['', '拾', '佰', '仟'];
    const g = ['', '万', '亿'];
    const read4 = (x: number) => {
        let r = '';
        const str = String(x);
        for (let k = 0; k < str.length; k++) {
            const dig = +str[k];
            const p = str.length - 1 - k;
            if (dig === 0) {
                if (!r.endsWith('零') && r) r += '零';
            } else r += d[dig] + u[p];
        }
        return r.replace(/零+$/, '');
    };
    const big = (x: number) => {
        if (x === 0) return '零';
        const parts: string[] = [];
        let str = String(x);
        while (str.length > 4) {
            parts.unshift(str.slice(-4));
            str = str.slice(0, -4);
        }
        parts.unshift(str);
        let r = '';
        parts.forEach((p, idx) => {
            const v = +p;
            const gi = parts.length - 1 - idx;
            if (v !== 0) r += read4(v) + g[gi];
            else if (r && !r.endsWith('零')) r += '零';
        });
        return r.replace(/零+$/, '');
    };
    let txt = big(i) + '泰铢';
    txt += s === 0 ? '整' : d[Math.floor(s / 10)] + '角' + (s % 10 ? d[s % 10] + '分' : '');
    return txt;
}

export interface Check {
    key: string;
    descKey: string;
    pass: boolean;
    req: boolean;
    na: boolean;
}
export function compliance(st: WState): Check[] {
    const b = st.buyer;
    const isFull = FULL_TAX.includes(st.docType);
    const buyerOk = isFull
        ? !!(
              b.name &&
              b.addr &&
              b.tin &&
              (b.type !== 'company' || b.branchType === 'hq' || /^\d{5}$/.test(b.branchNo))
          )
        : true;
    let tinOk = true;
    if (['company', 'individual'].includes(b.type) && b.tin) tinOk = /^\d{13}$/.test(b.tin);
    if (b.type === 'foreigner' && b.tin) tinOk = /^[A-Za-z0-9]{4,20}$/.test(b.tin);
    const payOk = !payRequired(st) || st.pay.status !== 'unpaid';
    const isTax = isFull || st.docType === 'tax_invoice_simple';
    return [
        { key: 'sw-ck-buyer', descKey: 'sw-ck-buyer-d', pass: buyerOk, req: isFull, na: !isFull },
        {
            key: 'sw-ck-tin',
            descKey: 'sw-ck-tin-d',
            pass: tinOk,
            req: isFull,
            na: st.docType === 'quotation',
        },
        { key: 'sw-ck-vat', descKey: 'sw-ck-vat-d', pass: true, req: isTax, na: !isTax },
        {
            key: 'sw-ck-pay',
            descKey: 'sw-ck-pay-d',
            pass: payOk,
            req: payRequired(st),
            na: !payRequired(st),
        },
        { key: 'sw-ck-seq', descKey: 'sw-ck-seq-d', pass: true, req: true, na: false },
        { key: 'sw-ck-words', descKey: 'sw-ck-words-d', pass: true, req: isTax, na: !isTax },
    ];
}
