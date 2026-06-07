/*
 * Pearnly POS 餐厅业态 · pos-restaurant-ops.js · 屏3 厨房单 KOT + 屏4 埋单结账(整桌/按项/AA + 服务费)
 * 承 pos-restaurant.js(POS.restaurant)。厨房板轮询 /api/pos/restaurant/kitchen + 状态流转;埋单走
 * request-bill → bill 预览 → checkout(复用零售收款/小票/税票)。视觉照搬概念稿 03/04;失败统一 posErrMsg。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const $ = (id) => document.getElementById(id);
    const fmt = POS.fmt;
    const R = (POS.restaurant = POS.restaurant || {});
    const ws = () => state.workspaceClientId;

    Object.assign(R.data, {
        kitchen: () =>
            POS.apiFetch('GET', '/api/pos/restaurant/kitchen?workspace_client_id=' + ws()),
        kotStatus: (kid, status) =>
            POS.apiFetch('POST', '/api/pos/restaurant/kot/' + kid + '/status', {
                workspace_client_id: ws(),
                status,
            }),
        requestBill: (sid) =>
            POS.apiFetch('POST', '/api/pos/restaurant/sessions/' + sid + '/request-bill', {
                workspace_client_id: ws(),
            }),
        billPreview: (sid, mode, lineIds, ways) => {
            let p =
                '/api/pos/restaurant/sessions/' +
                sid +
                '/bill?workspace_client_id=' +
                ws() +
                '&mode=' +
                mode +
                '&service_rate=10';
            (lineIds || []).forEach((id) => (p += '&line_ids=' + id));
            if (ways) p += '&ways=' + ways;
            return POS.apiFetch('GET', p);
        },
        checkout: (sid, payload) =>
            POS.apiFetch(
                'POST',
                '/api/pos/restaurant/sessions/' + sid + '/checkout',
                Object.assign({ workspace_client_id: ws() }, payload)
            ),
    });
    const RD = R.data;

    // ════════════════ 屏 3 · 厨房单 KOT ════════════════
    let kitchenTimer = null;

    async function renderKitchen() {
        const grid = $('rk-grid');
        if (!grid) return;
        let data;
        try {
            data = await RD.kitchen();
        } catch (e) {
            grid.innerHTML =
                '<div class="kempty">' + POS.posErrMsg(e.code, 'pos.unexpected') + '</div>';
            return;
        }
        const s = data.stat || { pending: 0, cooking: 0, late: 0 };
        $('rk-stat').textContent = POS.t('posui.rest.kot.stat')
            .replace('{p}', s.pending)
            .replace('{c}', s.cooking)
            .replace('{l}', s.late);
        const tickets = data.tickets || [];
        if (!tickets.length) {
            grid.innerHTML = '<div class="kempty">' + POS.t('posui.rest.kot.empty') + '</div>';
            return;
        }
        grid.innerHTML = tickets.map(ticketCard).join('');
        grid.querySelectorAll('[data-kot]').forEach((b) =>
            b.addEventListener('click', () => kot(b.dataset.kot, b.dataset.act))
        );
    }

    function ticketCard(t) {
        const cls = 'tk' + (t.status === 'cooking' ? ' cooking' : '') + (t.late ? ' late' : '');
        const tm = (t.late ? '⚠ ' : '⏱ ') + (t.minutes || 0) + ' ' + POS.t('posui.rest.min');
        const items = (t.items || [])
            .map(
                (it) =>
                    '<div class="it"><span class="q">' +
                    Number(it.qty) +
                    '×</span>' +
                    POS.nm(it.name) +
                    (it.note ? '<span class="nt">' + it.note + '</span>' : '') +
                    '</div>'
            )
            .join('');
        const act =
            t.status === 'new'
                ? '<button class="btn start" data-kot="' +
                  t.id +
                  '" data-act="cooking">' +
                  POS.t('posui.rest.kot.start') +
                  '</button>'
                : '<button class="btn done" data-kot="' +
                  t.id +
                  '" data-act="done">' +
                  POS.t('posui.rest.kot.done') +
                  '</button>';
        return (
            '<div class="' +
            cls +
            '"><div class="h"><span class="no">' +
            (t.table_name || '') +
            '</span><span class="tm">' +
            tm +
            '</span></div><div class="items">' +
            items +
            '</div><div class="act">' +
            act +
            '</div></div>'
        );
    }

    async function kot(kid, act) {
        try {
            await RD.kotStatus(kid, act);
            renderKitchen();
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        }
    }

    R.renderKitchen = function () {
        renderKitchen();
        if (kitchenTimer) clearInterval(kitchenTimer);
        kitchenTimer = setInterval(() => {
            const v = $('view-rkitchen');
            if (v && v.classList.contains('is-active')) renderKitchen();
            else if (kitchenTimer) {
                clearInterval(kitchenTimer);
                kitchenTimer = null;
            }
        }, 10000);
    };

    // ════════════════ 屏 4 · 埋单结账 ════════════════
    let bill = null; // { sid, lines, mode, selected:Set, ways, payment, totals, sale }

    R.openBill = async function (session) {
        const s = session.session;
        bill = {
            sid: s.id,
            mode: 'whole',
            selected: new Set(),
            ways: s.party_size || 2,
            payment: 'cash',
            lines: [],
            sale: null,
        };
        $('rb-title').textContent = s.table_name + ' · ' + POS.t('posui.rest.bill.title');
        $('rb-sub').textContent =
            (s.party_size || 0) +
            ' ' +
            POS.t('posui.rest.seats') +
            ' · ' +
            (s.minutes || 0) +
            ' ' +
            POS.t('posui.rest.min') +
            (state.cashier ? ' · ' + state.cashier.display_name : '');
        $('rb-err').textContent = '';
        setPaidState(false);
        try {
            await RD.requestBill(bill.sid);
        } catch (_) {}
        let prev;
        try {
            prev = await RD.billPreview(bill.sid, 'whole', null, null);
        } catch (e) {
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
            return;
        }
        bill.lines = prev.lines || [];
        bill.selected = new Set(bill.lines.map((l) => l.line_id));
        setMode('whole', prev);
        renderLines();
        $('rt-bill-mask').classList.add('show');
    };

    function setMode(mode, prev) {
        bill.mode = mode;
        document
            .querySelectorAll('#rb-split button')
            .forEach((b) => b.classList.toggle('on', b.dataset.mode === mode));
        $('rb-modal').classList.toggle('byitem', mode === 'by_item');
        if (mode === 'whole') bill.selected = new Set(bill.lines.map((l) => l.line_id));
        if (prev) applyTotals(prev);
        else refreshTotals();
    }

    function renderLines() {
        $('rb-lines').innerHTML = bill.lines
            .map((l) => {
                const sel = bill.selected.has(l.line_id) ? ' sel' : '';
                return (
                    '<div class="ln' +
                    sel +
                    '" data-lid="' +
                    l.line_id +
                    '"><div class="chk"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg></div>' +
                    '<div class="nm">' +
                    POS.nm(l.name) +
                    '</div><span class="q tnum">×' +
                    Number(l.qty) +
                    '</span><span class="amt tnum">฿' +
                    fmt(l.line_total) +
                    '</span></div>'
                );
            })
            .join('');
        $('rb-lines')
            .querySelectorAll('.ln')
            .forEach((el) => el.addEventListener('click', () => toggleLine(el.dataset.lid)));
    }

    function toggleLine(lid) {
        if (bill.mode !== 'by_item') return;
        if (bill.selected.has(lid)) bill.selected.delete(lid);
        else bill.selected.add(lid);
        renderLines();
        refreshTotals();
    }

    async function refreshTotals() {
        const ids = bill.mode === 'by_item' ? Array.from(bill.selected) : null;
        if (bill.mode === 'by_item' && !ids.length) {
            applyTotals(null);
            return;
        }
        try {
            const prev = await RD.billPreview(
                bill.sid,
                bill.mode,
                ids,
                bill.mode === 'aa' ? bill.ways : null
            );
            applyTotals(prev);
        } catch (e) {
            applyTotals(null);
        }
    }

    function applyTotals(p) {
        bill.totals = p;
        $('rb-subtotal').textContent = fmt(p ? p.subtotal : 0);
        $('rb-service').textContent = fmt(p ? p.service_charge : 0);
        $('rb-service-rate').textContent = p ? p.service_rate : '10';
        $('rb-vat').textContent = fmt(p ? p.vat_amount : 0);
        $('rb-grand').textContent = fmt(p ? p.grand_total : 0);
        const split = p && p.split;
        $('rb-split-row').style.display = split ? 'flex' : 'none';
        if (split) {
            $('rb-ways').textContent = split.ways;
            $('rb-share').textContent = fmt(split.per_share);
        }
        $('rb-pay').textContent = POS.t('posui.rest.bill.pay').replace(
            '{amt}',
            '฿' + fmt(p ? p.grand_total : 0)
        );
        $('rb-pay').disabled = !p || Number(p.grand_total) <= 0;
    }

    function setPm(m) {
        bill.payment = m;
        document
            .querySelectorAll('#rb-pm button')
            .forEach((b) => b.classList.toggle('on', b.dataset.pm === m));
    }

    async function doCheckout() {
        if (!bill.totals) return;
        const btn = $('rb-pay');
        btn.disabled = true;
        $('rb-err').textContent = '';
        const payload = {
            client_uuid: POS.uuid(),
            shift_id: state.shift ? state.shift.id : null,
            terminal_id: state.terminalId,
            mode: bill.mode,
            line_ids: bill.mode === 'by_item' ? Array.from(bill.selected) : null,
            ways: bill.mode === 'aa' ? bill.ways : null,
            service_rate: '10',
            price_includes_vat: true,
            payments: [{ method: bill.payment, amount: bill.totals.grand_total }],
            sold_at: new Date().toISOString(),
        };
        try {
            const res = await RD.checkout(bill.sid, payload);
            bill.sale = res.sale;
            POS.toast(POS.t('posui.rest.paid.toast'));
            printReceipt(res.sale.id);
            if (res.session && res.session.status !== 'closed') {
                await reopenRemaining();
            } else {
                setPaidState(true);
            }
        } catch (e) {
            $('rb-err').textContent = POS.posErrMsg(e.code, 'pos.unexpected');
            btn.disabled = false;
        }
    }

    async function reopenRemaining() {
        let prev;
        try {
            prev = await RD.billPreview(bill.sid, 'whole', null, null);
        } catch (_) {
            closeBill(true);
            return;
        }
        bill.lines = prev.lines || [];
        bill.selected = new Set(bill.lines.map((l) => l.line_id));
        setMode('whole', prev);
        renderLines();
    }

    function setPaidState(paid) {
        $('rb-pay').style.display = paid ? 'none' : '';
        $('rb-done').style.display = paid ? '' : 'none';
        document.querySelectorAll('#rb-split, #rb-pm').forEach((el) => {
            el.style.opacity = paid ? '.5' : '';
            el.style.pointerEvents = paid ? 'none' : '';
        });
    }

    function closeBill(refresh) {
        $('rt-bill-mask').classList.remove('show');
        if (refresh) {
            POS.showView('rtables');
            R.renderTables();
        }
    }

    function printReceipt(saleId) {
        if (!saleId || POS.allowMock()) return;
        fetch('/api/pos/sales/' + saleId + '/receipt-pdf', {
            headers: state.token ? { Authorization: 'Bearer ' + state.token } : {},
        })
            .then((r) => (r.ok ? r.blob() : Promise.reject()))
            .then((b) => {
                const url = URL.createObjectURL(b);
                window.open(url, '_blank');
                setTimeout(() => URL.revokeObjectURL(url), 60000);
            })
            .catch(() => {});
    }

    // ── 紧凑税票弹窗(复用 fullTaxInvoice 接口)──
    let taxType = 'company';
    function openTax() {
        if (!bill || !bill.sale) {
            POS.toast(POS.t('posui.rest.tax.pay_first'));
            return;
        }
        taxType = 'company';
        ['rt-tax-name', 'rt-tax-taxid', 'rt-tax-address'].forEach((id) => ($(id).value = ''));
        $('rt-tax-err').textContent = '';
        applyTaxType();
        $('rt-tax-mask').classList.add('show');
    }
    function applyTaxType() {
        document
            .querySelectorAll('#rt-tax-seg button')
            .forEach((b) => b.classList.toggle('on', b.dataset.bt === taxType));
        $('rt-tax-namelabel').textContent = POS.t(
            taxType === 'company' ? 'posui.tax.f.company' : 'posui.tax.f.name'
        );
        updateTaxSubmit();
    }
    function updateTaxSubmit() {
        const name = ($('rt-tax-name').value || '').trim();
        const tid = ($('rt-tax-taxid').value || '').replace(/\D/g, '');
        $('rt-tax-submit').disabled = taxType === 'company' ? !name || tid.length !== 13 : !name;
    }
    async function submitTax() {
        const tid = ($('rt-tax-taxid').value || '').replace(/\D/g, '');
        const buyer = {
            party_type: taxType,
            name: ($('rt-tax-name').value || '').trim() || null,
            tax_id: tid || null,
            branch_type: taxType === 'company' ? 'head' : null,
            address: ($('rt-tax-address').value || '').trim() || null,
        };
        const btn = $('rt-tax-submit');
        btn.disabled = true;
        try {
            await POS.data.fullTaxInvoice(bill.sale.id, buyer);
            $('rt-tax-mask').classList.remove('show');
            POS.toast(POS.t('posui.tax.done'));
        } catch (e) {
            if (e.code === 'pos.already_upgraded') {
                $('rt-tax-mask').classList.remove('show');
                POS.toast(POS.posErrMsg('pos.already_upgraded'), 'error');
            } else {
                $('rt-tax-err').textContent = POS.posErrMsg(e.code, 'pos.tax_id_invalid');
                btn.disabled = false;
            }
        }
    }

    R.initOps = function () {
        $('rk-back').addEventListener('click', () => {
            POS.showView('rtables');
            R.renderTables();
        });
        $('rb-close').addEventListener('click', () => closeBill(false));
        $('rb-done').addEventListener('click', () => closeBill(true));
        document.querySelectorAll('#rb-split button').forEach((b) =>
            b.addEventListener('click', () => {
                setMode(b.dataset.mode, null);
                renderLines();
            })
        );
        document
            .querySelectorAll('#rb-pm button')
            .forEach((b) => b.addEventListener('click', () => setPm(b.dataset.pm)));
        $('rb-pay').addEventListener('click', doCheckout);
        $('rb-tax').addEventListener('click', openTax);
        $('rt-tax-close').addEventListener('click', () =>
            $('rt-tax-mask').classList.remove('show')
        );
        $('rt-tax-cancel').addEventListener('click', () =>
            $('rt-tax-mask').classList.remove('show')
        );
        $('rt-tax-submit').addEventListener('click', submitTax);
        document.querySelectorAll('#rt-tax-seg button').forEach((b) =>
            b.addEventListener('click', () => {
                taxType = b.dataset.bt;
                applyTaxType();
            })
        );
        $('rt-tax-name').addEventListener('input', updateTaxSubmit);
        $('rt-tax-taxid').addEventListener('input', updateTaxSubmit);
    };
})();
