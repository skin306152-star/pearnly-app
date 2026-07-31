// 销项开票向导 PO-10 · 纯计算叶子:金额合计 / 泰铢·中文大写 / 合规清单
// 无 DOM 无副作用 · 从 index.html 样稿逐函数移植(算法 verbatim)。被 wizard 主模块 import。

export interface WLine {
    desc: string;
    qty: number | string;
    // null / 空串 = 这一行还没定价(≠ 免费)。两者在票面上是同一个数字,在钱上不是:
    // 前者是漏填,后者是老板拍板送的。混成一个值就没人看得出票开短了。
    price: number | string | null;
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

/**
 * 这个价是人定过的吗。口径与收银台的 pos-cashier.priced 同一份:空 / null / 非数 = 没定过。
 *
 * 人自己打的 0 照旧算定过价 —— 赠品是老板拍板的,票面上写着 ฿0 谁都看得见;这里堵的是系统
 * 替人编出来的 0(`money(null)` 画成 "0.00"、`+l.price || 0` 发出去 0)。同一套判据后端也有
 * 一份(services/sales/issue_gates.amount_gate),前端只是让人早一步看见。
 */
export function priced(v: unknown): boolean {
    if (v === null || v === undefined || String(v).trim() === '') return false;
    return Number.isFinite(Number(v));
}

/** 真会印上票的行。合规清单和 buildPayload 共用这一条,免得「查过的行」和「发出去的行」两套。 */
export function billableLines(st: WState): WLine[] {
    return st.lines.filter((l) => (l.desc || '').trim());
}

/** 一行的净额(数量×单价−折扣 · 不为负)· 合计/购物车/票面预览共用,免得三套算法各自漂。 */
export function lineAmount(l: WLine): number {
    return Math.max(0, (+l.qty || 0) * (Number(l.price) || 0) - (+l.disc || 0));
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
        const lt = lineAmount(l);
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
    // 完整税票/合并单:买方必须齐全且【非匿名】(§86/4)→ 匿名或不齐都不合规(与后端 §B 一致)。
    // 简易票/收据/报价:买方非必填 → N/A。匿名只能开简易票。
    const anon = b.type === 'anonymous';
    const buyerOk = !isFull
        ? true
        : !anon &&
          !!(
              b.name &&
              b.addr &&
              b.tin &&
              (b.type !== 'company' || b.branchType === 'hq' || /^\d{5}$/.test(b.branchNo))
          );
    let tinOk = true;
    if (['company', 'individual'].includes(b.type) && b.tin) tinOk = /^\d{13}$/.test(b.tin);
    if (b.type === 'foreigner' && b.tin) tinOk = /^[A-Za-z0-9]{4,20}$/.test(b.tin);
    const payOk = !payRequired(st) || st.pay.status !== 'unpaid';
    // 上票的行(有品名的那些 · 与 buildPayload 的过滤同一条)每一行都得有价。
    const priceOk = billableLines(st).every((l) => priced(l.price));
    const isTax = isFull || st.docType === 'tax_invoice_simple';
    // key/descKey 用向导自含字典(sales-wizard-i18n)的键名,经 wt() 取文案。
    return [
        {
            key: 'ckBuyer',
            descKey: 'ckBuyerD',
            pass: buyerOk,
            req: isFull,
            na: !isFull,
        },
        {
            key: 'ckTin',
            descKey: 'ckTinD',
            pass: tinOk,
            req: isFull,
            na: st.docType === 'quotation',
        },
        // 报价单也算:฿0 的报价一样是漏填,只是漏的代价晚一点到。
        { key: 'ckPrice', descKey: 'ckPriceD', pass: priceOk, req: true, na: false },
        { key: 'ckVat', descKey: 'ckVatD', pass: true, req: isTax, na: !isTax },
        {
            key: 'ckPay',
            descKey: 'ckPayD',
            pass: payOk,
            req: payRequired(st),
            na: !payRequired(st),
        },
        { key: 'ckSeq', descKey: 'ckSeqD', pass: true, req: true, na: false },
        { key: 'ckWords', descKey: 'ckWordsD', pass: true, req: isTax, na: !isTax },
    ];
}
