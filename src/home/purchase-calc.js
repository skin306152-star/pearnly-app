/*
 * Pearnly 商户采购 · purchase-calc.js · 进项录入即时合计(屏10)
 *
 * 合计链(对标设计稿 Pearnly_采购_UI预览/10):税前小计 → 折扣 → 进项税 VAT → 含税合计 → 预扣税 WHT → 实付供应商。
 * 录入时本地即时重算给用户即时反馈;保存后以后端 /docs 返回的合计为权威(钱字段 Decimal · 后端为准)。
 * 全程按「分」整数运算 + 半偶数舍入(镜像 pos-totals.js / Decimal ROUND_HALF_EVEN),防浮点 ±1 分漂移
 * (餐厅服务费逐步取整教训)。VAT/WHT 逐行取整后求和,非先汇总后取整。
 *
 * src/home ESM scope(src/package.json type:module):import { computePurchaseTotals } from './purchase-calc.js'。
 * 测试 tests/unit/test_purchase_calc.py 用真 node 动态 import 跑本文件对照设计稿黄金值守门。
 */

// 元 → 分(整数),半偶数舍入,镜像 Decimal.quantize('0.01')
function q2c(dollars) {
    const v = dollars * 100;
    const f = Math.floor(v);
    const diff = v - f;
    if (diff > 0.5) return f + 1;
    if (diff < 0.5) return f;
    return f % 2 === 0 ? f : f + 1; // 恰好 .5 → 取偶
}
function c2s(cents) {
    return (cents / 100).toFixed(2);
}
function num(x) {
    const n = Number(x);
    return isFinite(n) ? n : 0;
}

// lines: [{ qty, unit_price, discount, vat_rate, wht_rate }]
// opts:  { doc_discount, rounding }  （均可空 · 默认 0）
export function computePurchaseTotals(lines, opts) {
    const o = opts || {};
    let subtotalC = 0; // 税前小计(行净额合计)
    let vatC = 0; // 进项税(逐行取整)
    let whtC = 0; // 预扣税(逐行取整)

    (lines || []).forEach(function (ln) {
        const grossC = q2c(num(ln.qty) * num(ln.unit_price));
        const lineDiscC = q2c(num(ln.discount));
        const netC = Math.max(0, grossC - lineDiscC);
        subtotalC += netC;
        vatC += q2c((netC / 100) * (num(ln.vat_rate) / 100));
        whtC += q2c((netC / 100) * (num(ln.wht_rate) / 100));
    });

    const docDiscC = q2c(num(o.doc_discount));
    const roundingC = q2c(num(o.rounding));
    const baseC = Math.max(0, subtotalC - docDiscC); // 税前 − 整单折扣
    const grandC = baseC + vatC + roundingC; // 含税合计
    const netPayableC = grandC - whtC; // 实付供应商 = 含税 − 代扣 WHT

    return {
        subtotal: c2s(subtotalC),
        discount_total: c2s(docDiscC),
        vat_amount: c2s(vatC),
        grand_total: c2s(grandC),
        wht_amount: c2s(whtC),
        rounding: c2s(roundingC),
        net_payable: c2s(netPayableC),
        grand_total_cents: grandC,
    };
}
