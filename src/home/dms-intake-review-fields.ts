// ============================================================
// 录入工作台 · 复核屏字段规则块(从 dms-intake-review.ts 抽出控行数)
//   复核预览字段 / 对手方方向判定 / 散客票豁免 / 必填 warn 集。
//   只放纯函数与常量,不碰 DOM 与流程态(renderReview 归 dms-intake-review.ts)。
// ============================================================
import type { Dict } from './dms-intake-invoice.js';

// 复核预览字段(复用 OCR 抽屉字段标签键)
export const REV_REST: Array<[string, string]> = [
    ['invoice_number', 'drawer-lbl-invoice'],
    // 票面原文(泰国票面印佛历)· 保存走 PUT /api/history 由后端按它反推公历 date
    ['date_raw', 'drawer-lbl-date'],
    ['subtotal', 'drawer-lbl-subtotal'],
    ['vat', 'drawer-lbl-vat'],
];

// 对手方在哪一侧看方向:销项是买方,进项是卖方。此前写死 seller_*,销项票于是"名称/税号空 +
// 需确认",看着像识别失败,其实数据在 buyer_*。标签随方向写清买卖双方(字段键 → exc-fld-*)。
export function partyKeys(f: Dict): { name: string; tax: string; other: string; otherTax: string } {
    return String(f.direction || '') === 'sales'
        ? { name: 'buyer_name', tax: 'buyer_tax', other: 'seller_name', otherTax: 'seller_tax' }
        : { name: 'seller_name', tax: 'seller_tax', other: 'buyer_name', otherTax: 'buyer_tax' };
}
export function partyLabel(k: string): string {
    return 'exc-fld-' + (k.endsWith('_tax') ? k.slice(0, -4) + '-tax' : k.slice(0, -5));
}
export function revCore(f: Dict): Array<[string, string]> {
    const p = partyKeys(f);
    return [[p.name, partyLabel(p.name)], [p.tax, partyLabel(p.tax)], ...REV_REST];
}
export function revMore(f: Dict): Array<[string, string]> {
    const p = partyKeys(f);
    return [
        ['total_amount', 'drawer-lbl-total'],
        [p.other, partyLabel(p.other)],
        [p.otherTax, partyLabel(p.otherTax)],
        ['wht_amount', 'drawer-lbl-wht-amount'],
    ];
}
// 散客票(销项 ABB 简化税票 / 收据)票面本无买方身份:买方税号空是常态,不当必填标「需确认」;
// 完整税票 / 方向不明不享受此豁免,仍照旧要求当前方向税号。
export const ANON_BUYER_DOCS = new Set(['simplified_tax_invoice', 'receipt']);
export function isAnonBuyerDoc(f: Dict): boolean {
    return f.direction === 'sales' && ANON_BUYER_DOCS.has(String(f.document_type || ''));
}
export function warnFields(f: Dict): Set<string> {
    const s = new Set<string>();
    const req = ['invoice_number', 'total_amount'];
    if (!isAnonBuyerDoc(f)) req.push(partyKeys(f).tax);
    for (const k of req) if (!String(f[k] || '').trim()) s.add(k);
    return s;
}
