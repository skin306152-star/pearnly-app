/*
 * Pearnly POS · pos-ops.js · 屏4 退货 + 屏5 交班(独立于购物车 · 视觉照搬概念稿 04/05)
 * 数据走 window.POS.data(B2 前 mock 兜底);失败统一 posErrMsg。对外 window.POS.ops。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const $ = (id) => document.getElementById(id);
    const fmt = POS.fmt;

    // ════════════════ 屏 4 · 退货 ════════════════
    let refundSale = null;
    let refundSel = {}; // 行 id → 退货数量
    let refundWay = 'cash';

    // 兼容信封两种行形:by-receipt 详情行 id 在 l.id;名可能缺省(详情不带 name)→ 按 product_id 回查。
    function lineId(l) {
        return l.sale_line_id || l.id;
    }
    function lineName(l) {
        if (l.name) return POS.nm(l.name);
        return POS.productName(l.product_id) || l.sell_unit || '';
    }

    function resetRefund() {
        refundSale = null;
        refundSel = {};
        refundWay = 'cash';
        $('refund-receipt').value = '';
        $('refund-step2').classList.remove('on');
        $('refund-step3').classList.remove('on');
        $('refund-body').innerHTML =
            '<div class="state" id="refund-hint">' + POS.t('posui.refund.hint') + '</div>';
    }
    async function findReceipt() {
        const no = ($('refund-receipt').value || '').trim();
        if (!no) return;
        $('refund-body').innerHTML = '<div class="state">' + POS.t('posui.loading') + '</div>';
        try {
            refundSale = await POS.data.findReceipt(no);
        } catch (e) {
            $('refund-body').innerHTML =
                '<div class="state">' + POS.posErrMsg(e.code, 'pos.product_not_found') + '</div>';
            return;
        }
        refundSel = {};
        $('refund-step2').classList.add('on');
        $('refund-step3').classList.add('on');
        renderRefund();
    }
    function renderRefund() {
        const s = refundSale;
        const head = s.sale;
        const paymentSummary = (s.payments || [])
            .map(
                (p) =>
                    POS.t(
                        'posui.shift.method.' + (p.method === 'promptpay' ? 'promptpay' : p.method)
                    ) +
                    ' ฿' +
                    fmt(p.amount)
            )
            .join(' · ');
        const lines = s.lines
            .map((l) => {
                const lid = lineId(l);
                const sel = refundSel[lid] || 0;
                const amt = sel * Number(l.unit_price);
                return (
                    '<div class="line' +
                    (sel > 0 ? ' sel' : '') +
                    '" data-lid="' +
                    lid +
                    '"><div class="chk"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg></div><div class="nm"><div class="n">' +
                    lineName(l) +
                    '</div><div class="u tnum">฿' +
                    fmt(l.unit_price) +
                    ' · ' +
                    POS.t('posui.refund.orig') +
                    ' ' +
                    l.qty +
                    '</div></div><div class="qty"><button data-rdec="' +
                    lid +
                    '">−</button><span class="q tnum">' +
                    (sel || 1) +
                    '</span><button data-rinc="' +
                    lid +
                    '">+</button></div><div class="amt tnum">฿' +
                    fmt(amt) +
                    '</div></div>'
                );
            })
            .join('');
        $('refund-body').innerHTML =
            '<div class="card"><div class="h"><div><div class="a">' +
            head.receipt_no +
            '</div><div class="b">' +
            paymentSummary +
            (head.cashier ? ' · ' + head.cashier : '') +
            '</div></div><div class="paid">' +
            POS.t('posui.refund.paid') +
            '</div></div>' +
            lines +
            '</div><div class="refund"><div class="way"><button data-way="cash" class="active">' +
            POS.t('posui.refund.way.cash') +
            '</button><button data-way="qr">' +
            POS.t('posui.refund.way.qr') +
            '</button></div><div class="stock-note"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7L12 3 4 7m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>' +
            POS.t('posui.refund.stock') +
            '</div><div class="total"><span class="l">' +
            POS.t('posui.refund.amount') +
            '</span><span class="v tnum" id="refund-total">฿0.00</span></div><button class="do" id="refund-do" disabled>' +
            POS.t('posui.refund.title') +
            '</button></div>';
        bindRefund();
        updateRefundTotal();
    }
    function bindRefund() {
        $('refund-body')
            .querySelectorAll('.line[data-lid]')
            .forEach((el) => {
                const lid = el.dataset.lid;
                el.querySelector('.chk').onclick = el.querySelector('.nm').onclick = () =>
                    toggleRefund(lid);
            });
        $('refund-body')
            .querySelectorAll('[data-rdec]')
            .forEach((b) => (b.onclick = () => stepRefund(b.dataset.rdec, -1)));
        $('refund-body')
            .querySelectorAll('[data-rinc]')
            .forEach((b) => (b.onclick = () => stepRefund(b.dataset.rinc, 1)));
        $('refund-body')
            .querySelectorAll('[data-way]')
            .forEach(
                (b) =>
                    (b.onclick = () => {
                        refundWay = b.dataset.way;
                        $('refund-body')
                            .querySelectorAll('[data-way]')
                            .forEach((x) => x.classList.toggle('active', x === b));
                    })
            );
        $('refund-do').onclick = doRefund;
    }
    function origQty(lid) {
        const l = refundSale.lines.find((x) => lineId(x) === lid);
        return l ? Number(l.qty) : 0;
    }
    function toggleRefund(lid) {
        if (refundSel[lid]) delete refundSel[lid];
        else refundSel[lid] = 1;
        renderRefund();
    }
    function stepRefund(lid, d) {
        const cur = refundSel[lid] || 0;
        const next = Math.max(0, Math.min(cur + d, origQty(lid)));
        if (next === 0) delete refundSel[lid];
        else refundSel[lid] = next;
        renderRefund();
    }
    function refundTotal() {
        return refundSale.lines.reduce(
            (s, l) => s + (refundSel[lineId(l)] || 0) * Number(l.unit_price),
            0
        );
    }
    function updateRefundTotal() {
        const total = refundTotal();
        $('refund-total').textContent = '฿' + fmt(total);
        const has = Object.keys(refundSel).length > 0;
        const btn = $('refund-do');
        btn.disabled = !has;
        btn.textContent = has
            ? POS.tf('posui.refund.confirm', { n: fmt(total) })
            : POS.t('posui.refund.title');
    }
    function refundDone() {
        POS.toast(POS.t('posui.refund.done'));
        POS.showView('main');
        resetRefund();
    }
    async function doRefund() {
        const lines = Object.keys(refundSel).map((lid) => ({
            sale_line_id: lid,
            qty: String(refundSel[lid]),
            _amt:
                refundSel[lid] * Number(refundSale.lines.find((x) => lineId(x) === lid).unit_price),
        }));
        if (!lines.length) return;
        const btn = $('refund-do');
        const saleId = refundSale.sale.id;
        btn.disabled = true;
        try {
            await POS.data.refund(saleId, lines, refundWay);
            refundDone();
        } catch (e) {
            // 授权闸开 + 收银员无权 → 弹店长授权窗,凭据带回重试;其余错误照常提示。
            if (e.code === 'pos.approval_required' && POS.approve) {
                POS.approve.open(
                    (creds) => POS.data.refund(saleId, lines, refundWay, creds),
                    refundDone
                );
                btn.disabled = false;
                return;
            }
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
            btn.disabled = false;
        }
    }

    // ════════════════ 屏 5 · 交班日结 ════════════════
    async function renderShift() {
        const wrap = $('shift-wrap');
        wrap.innerHTML = '<div class="state">' + POS.t('posui.loading') + '</div>';
        let d;
        try {
            d = await POS.data.shiftSummary();
        } catch (e) {
            wrap.innerHTML =
                '<div class="state">' + POS.posErrMsg(e.code, 'pos.unexpected') + '</div>';
            return;
        }
        if (!d) {
            wrap.innerHTML = '<div class="state">' + POS.t('posui.shift.none') + '</div>';
            return;
        }
        const sm = d.summary;
        const sh = d.shift;
        const openT = POS.hm(new Date(sh.opened_at));
        const expected = Number(sm.expected_cash);
        wrap.innerHTML =
            '<div class="card"><div class="h"><svg class="ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>' +
            POS.t('posui.shift.cashier') +
            ' ' +
            (state.cashier ? state.cashier.display_name : '') +
            '</div><div class="kv"><span class="k">' +
            POS.t('posui.shift.opened') +
            '</span><span class="v tnum">' +
            openT +
            '</span></div><div class="kv"><span class="k">' +
            POS.t('posui.shift.float') +
            '</span><span class="v tnum">฿' +
            fmt(sh.opening_float) +
            '</span></div><div class="kv"><span class="k">' +
            POS.t('posui.shift.count') +
            '</span><span class="v tnum">' +
            POS.tf('posui.shift.unit.count', { n: sm.sales_count }) +
            '</span></div><div class="kv big"><span class="k">' +
            POS.t('posui.shift.gross') +
            '</span><span class="v tnum">฿' +
            fmt(sm.gross) +
            '</span></div></div>' +
            '<div class="card"><div class="h"><svg class="ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/></svg>' +
            POS.t('posui.shift.bymethod') +
            '</div>' +
            methodRow('green', 'cash', sm.by_method.cash) +
            methodRow('blue', 'promptpay', sm.by_method.promptpay) +
            methodRow('amber', 'card', sm.by_method.card) +
            '</div>' +
            '<div class="card"><div class="h"><svg class="ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>' +
            POS.t('posui.shift.cashbox') +
            '</div><div class="countbox"><div class="kv" style="padding:0 0 10px;border:0;"><span class="k">' +
            POS.t('posui.shift.expected') +
            '</span><span class="v tnum">฿' +
            fmt(expected) +
            '</span></div><label>' +
            POS.t('posui.shift.counted') +
            '</label><div class="inp"><span>฿</span><input class="tnum" id="shift-counted" inputmode="decimal" value="' +
            fmt(expected) +
            '"></div><div class="diff ok" id="shift-diffbox"><span>' +
            POS.t('posui.shift.diff') +
            '</span><span class="v tnum" id="shift-diffval">฿0.00</span></div></div></div>' +
            '<button class="submit" id="shift-submit">' +
            POS.t('posui.shift.submit') +
            '</button>';
        $('shift-counted').addEventListener('input', () => updateDiff(expected));
        $('shift-submit').addEventListener('click', () => submitClose(expected));
        updateDiff(expected);
    }
    function methodRow(color, methodKey, amount) {
        return (
            '<div class="kv"><span class="k pm"><span class="dot" style="background:var(--' +
            color +
            ')"></span>' +
            POS.t('posui.shift.method.' + methodKey) +
            '</span><span class="v tnum">฿' +
            fmt(amount) +
            '</span></div>'
        );
    }
    function updateDiff(expected) {
        const actual = Number(($('shift-counted').value || '0').replace(/[^\d.]/g, '')) || 0;
        const d = actual - expected;
        $('shift-diffval').textContent = (d >= 0 ? '฿' : '−฿') + fmt(Math.abs(d));
        $('shift-diffbox').className = 'diff ' + (Math.abs(d) < 0.005 ? 'ok' : 'bad');
    }
    async function submitClose(expected) {
        const counted = ($('shift-counted').value || '0').replace(/[^\d.]/g, '');
        const btn = $('shift-submit');
        btn.disabled = true;
        try {
            await POS.data.closeShift(counted);
            POS.toast(POS.t('posui.shift.title'));
            state.shift = null;
            POS.showView('login');
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
            btn.disabled = false;
        }
    }

    function init() {
        $('refund-find-btn').addEventListener('click', findReceipt);
        $('refund-receipt').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') findReceipt();
        });
    }

    POS.ops = { init, resetRefund, renderShift };
})();
