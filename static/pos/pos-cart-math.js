/* Pearnly POS · 购物车税额展示与本地预览成交。 */
(function () {
    const POS = window.POS;
    const $ = (id) => document.getElementById(id);

    function calculate(lines, discount) {
        const subtotal = (lines || []).reduce((sum, line) => sum + line.price * line.qty, 0);
        const mode = discount.mode || 'none';
        return POS.totals.localTotals(
            (lines || []).map((line) => ({
                qty: line.qty,
                unit_price: line.price,
                discount: 0,
                vat_applicable: line.vat_applicable !== false,
            })),
            {
                vat_rate: POS.pay.vatRate(),
                price_includes_vat: POS.pay.inclVat(),
                header_discount_amount:
                    mode === 'amount' ? Math.max(0, Math.min(discount.amount || 0, subtotal)) : 0,
                header_discount_pct: mode === 'pct' ? discount.pct || 0 : 0,
            }
        );
    }

    function discountTotal(totals) {
        return Number(totals.discount_total) + Number(totals.header_discount_amount);
    }

    function paint(totals, itemCount, hasItems) {
        const grand = Number(totals.grand_total);
        $('cart-subtotal').textContent = POS.fmt(totals.subtotal);
        $('cart-disc-amt').textContent = POS.fmt(discountTotal(totals));
        if (POS.pay.isVatRegistered()) {
            $('cart-vat-label').textContent = POS.t(
                POS.pay.inclVat() ? 'posui.cart.vat.included' : 'posui.cart.vat.excluded'
            );
            $('cart-vat-value').style.display = '';
            $('cart-vat-amt').textContent = POS.fmt(totals.vat_amount);
        } else {
            $('cart-vat-label').textContent = POS.t('posui.cart.vat.unregistered');
            $('cart-vat-value').style.display = 'none';
        }
        $('cart-grand').textContent = POS.fmt(grand);
        $('cart-pay-btn').disabled = !hasItems || totals.grand_total_cents <= 0;
        $('cart-zero-note').hidden = !hasItems || totals.grand_total_cents > 0;
        $('cart-pay-btn').title =
            hasItems && totals.grand_total_cents <= 0 ? POS.t('posui.cart.zero') : '';
        $('cart-peek-count').textContent = itemCount;
        $('cart-peek-grand').textContent = POS.fmt(grand);
        return grand;
    }

    function saleMeta(totals) {
        return {
            subtotal: totals.subtotal,
            discount_total: discountTotal(totals).toFixed(2),
            vat_amount: totals.vat_amount,
            doc_kind: POS.pay.isVatRegistered() ? 'abbrev_tax_invoice' : 'receipt',
            price_includes_vat: POS.pay.inclVat(),
        };
    }

    function blockZero(grand) {
        if (grand > 0) return false;
        POS.toast(POS.t('posui.cart.zero'), 'error');
        return true;
    }

    function receiptMeta(sale, snapshot) {
        return {
            subtotal: sale.subtotal != null ? sale.subtotal : snapshot.subtotal,
            discount_total:
                sale.discount_total != null ? sale.discount_total : snapshot.discount_total,
            grand_total: sale.grand_total != null ? sale.grand_total : snapshot.grand.toFixed(2),
            vat_amount: sale.vat_amount != null ? sale.vat_amount : snapshot.vat_amount,
            doc_kind: sale.doc_kind || snapshot.doc_kind,
            price_includes_vat:
                sale.price_includes_vat != null
                    ? sale.price_includes_vat
                    : snapshot.price_includes_vat,
        };
    }

    function mockSale(payload) {
        const lines = payload.lines.map((line) => ({
            qty: line.qty,
            unit_price: line.unit_price,
            discount: line.line_discount,
            vat_applicable: line.vat_applicable !== false,
        }));
        const totals = POS.totals.localTotals(lines, {
            vat_rate: POS.pay.vatRate(),
            price_includes_vat: POS.pay.inclVat(),
            header_discount_amount:
                payload.header_discount.type === 'amount' ? payload.header_discount.value : 0,
            header_discount_pct:
                payload.header_discount.type === 'pct' ? payload.header_discount.value : 0,
        });
        if (totals.grand_total_cents <= 0) throw new POS.PosErr('pos.zero_total', 422, null, true);
        const grand = Number(totals.grand_total);
        const paid = payload.payments.reduce((sum, payment) => sum + Number(payment.amount), 0);
        return {
            sale: Object.assign(
                {
                    id: POS.uuid(),
                    receipt_no: 'RCP-LOCAL-' + Math.floor(Math.random() * 90000 + 10000),
                    grand_total: totals.grand_total,
                    paid_total: paid.toFixed(2),
                    change_amount: Math.max(0, paid - grand).toFixed(2),
                    status: 'completed',
                },
                saleMeta(totals)
            ),
            stock_applied: true,
            deduped: false,
        };
    }

    POS.cartMath = { calculate, paint, saleMeta, receiptMeta, mockSale, blockZero };
})();
