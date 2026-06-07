/*
 * Pearnly POS · pos-totals.js · 离线本地算价(与服务端 services/sales/totals.py 等价)
 *
 * 离线开单时收银要立刻看到应收/找零并出小票(08 ADR-4),不能等网络;联网同步时服务端用
 * totals.py 权威复算。两套规则必须一致,否则同一单线下显示与入库金额分歧。本文件逐步镜像
 * compute_totals:行级 + 整单折扣、VAT 价内/价外,全程按「分」整数运算 + 半偶数舍入(对齐
 * Python Decimal 默认 ROUND_HALF_EVEN),避免浮点漂移。等价性由 tests/unit/test_pos_local_totals.py
 * 用真 node 跑本文件对照 totals.py 守门。
 *
 * 浏览器:挂 window.POS.totals;node(测试):module.exports。
 */
(function (root) {
    // 元 → 分(整数),半偶数舍入,镜像 Decimal.quantize('0.01')
    function q2c(dollars) {
        const v = dollars * 100;
        const fl = Math.floor(v);
        const diff = v - fl;
        let n;
        if (Math.abs(diff - 0.5) < 1e-9) n = fl % 2 === 0 ? fl : fl + 1;
        else n = Math.round(v);
        return n;
    }
    function c2s(cents) {
        const neg = cents < 0;
        const a = Math.abs(cents);
        const s = Math.floor(a / 100) + '.' + String(a % 100).padStart(2, '0');
        return neg ? '-' + s : s;
    }
    function num(v) {
        const n = Number(v);
        return isFinite(n) ? n : 0;
    }
    function hasValue(v) {
        return v !== null && v !== undefined && v !== '' && num(v) !== 0;
    }

    // lines: [{ qty, unit_price, discount, discount_pct?, vat_applicable }]
    // opts:  { vat_rate, wht_rate?, header_discount_amount?, header_discount_pct?, price_includes_vat? }
    function localTotals(lines, opts) {
        opts = opts || {};
        const vr = num(opts.vat_rate);
        const wr = num(opts.wht_rate);
        const incl = !!opts.price_includes_vat;

        let subtotalPre = 0; // 分
        let discTotal = 0;
        const norm = [];
        for (const ln of lines || []) {
            const qty = num(ln.qty != null ? ln.qty : 1);
            const price = num(ln.unit_price);
            const grossC = q2c(qty * price);
            let discC;
            if (hasValue(ln.discount_pct))
                discC = q2c((grossC / 100) * (num(ln.discount_pct) / 100));
            else discC = q2c(num(ln.discount));
            if (discC > grossC) discC = grossC;
            const lineTotalC = grossC - discC;
            subtotalPre += lineTotalC;
            discTotal += discC;
            norm.push({ vat_applicable: ln.vat_applicable !== false, line_total_c: lineTotalC });
        }

        // 整单折扣:pct 优先,否则绝对额;夹在 [0, subtotal]
        let headerC;
        if (hasValue(opts.header_discount_pct))
            headerC = q2c((subtotalPre / 100) * (num(opts.header_discount_pct) / 100));
        else headerC = q2c(num(opts.header_discount_amount));
        if (headerC < 0) headerC = 0;
        if (headerC > subtotalPre) headerC = subtotalPre;

        // VAT base:整单折扣按应税额比例摊
        const taxableC = norm.reduce((s, n) => s + (n.vat_applicable ? n.line_total_c : 0), 0);
        let vatBaseC;
        if (headerC === 0 || subtotalPre === 0) {
            vatBaseC = taxableC;
        } else {
            const shareC = q2c(((headerC / 100) * (taxableC / 100)) / (subtotalPre / 100));
            vatBaseC = taxableC - shareC;
            if (vatBaseC < 0) vatBaseC = 0;
        }

        let vatC, subtotalAfterC;
        if (incl) {
            vatC = q2c((vatBaseC / 100) * (vr / (100 + vr)));
            subtotalAfterC = subtotalPre - headerC - vatC;
        } else {
            vatC = q2c((vatBaseC / 100) * (vr / 100));
            subtotalAfterC = subtotalPre - headerC;
        }
        const whtC = q2c((subtotalAfterC / 100) * (wr / 100));
        const grandC = subtotalAfterC + vatC - whtC;

        return {
            subtotal: c2s(subtotalPre),
            discount_total: c2s(discTotal),
            header_discount_amount: c2s(headerC),
            vat_amount: c2s(vatC),
            grand_total: c2s(grandC),
            grand_total_cents: grandC,
        };
    }

    const api = { localTotals: localTotals, _q2c: q2c, _c2s: c2s };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.POS = root.POS || {};
        root.POS.totals = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
