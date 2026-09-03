/* Pearnly POS · cost capability, unit conversion, and local persistence redaction. */
(function () {
    const POS = window.POS;

    function visible() {
        const cashier = POS.state.cashier;
        return !!(cashier && cashier.caps && cashier.caps.cost_visible === true);
    }

    function priced(unit) {
        const raw = unit && unit.price;
        if (raw === null || raw === undefined || String(raw).trim() === '') return false;
        return Number.isFinite(Number(raw));
    }

    function forUnit(product, unit) {
        const raw = product && product.avg_cost;
        if (raw === null || raw === undefined || String(raw).trim() === '') return null;
        const baseCost = Number(raw);
        const factor = Number(unit && unit.factor);
        if (!Number.isFinite(baseCost) || !Number.isFinite(factor) || factor <= 0) return null;
        return baseCost * factor;
    }

    function markup(cost) {
        if (!visible()) return '';
        const value =
            cost === null || cost === undefined
                ? POS.t('posui.product.cost_missing')
                : '฿' + POS.fmt(cost);
        return (
            '<div class="cost tnum">' +
            POS.esc(POS.t('posui.product.cost')) +
            ' ' +
            value +
            '</div>'
        );
    }

    function baseUnitFallback(product) {
        if (!product.base_unit || product.matched_unit !== product.base_unit) return null;
        if (!priced({ price: product.base_price })) return null;
        return { unit_name: product.base_unit, price: product.base_price, factor: '1.000' };
    }

    function stripCatalog(items) {
        return (items || []).map((item) => {
            const safe = Object.assign({}, item);
            delete safe.avg_cost;
            return safe;
        });
    }

    function stripCart(items) {
        return (items || []).map((item) => {
            const safe = Object.assign({}, item);
            delete safe.unitCost;
            return safe;
        });
    }

    POS.cost = { visible, priced, forUnit, markup, baseUnitFallback, stripCatalog, stripCart };
})();
