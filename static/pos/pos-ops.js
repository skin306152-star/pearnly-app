/*
 * Pearnly POS · pos-ops.js · 屏4 退货/作废(独立于购物车 · 视觉照搬概念稿 04)
 * 今日交易点选退货 + 原路拆退多方式 + 当班作废 + 记录型退款诚实提示。交班在 pos-shift.js。
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
    let refundWay = 'cash'; // 单方式原单的退款方式(走后端兼容路)
    let refundAlloc = {}; // 混合原单:退款方式 → 退款额(正额 · 原路拆退)
    let todayItems = []; // 今日交易(退货/作废入口的单一来源,含 voidable/mixed)

    // 兼容信封两种行形:by-receipt 详情行 id 在 l.id;名可能缺省(详情不带 name)→ 按 product_id 回查。
    function lineId(l) {
        return l.sale_line_id || l.id;
    }
    function lineName(l) {
        if (l.name) return POS.nm(l.name);
        return POS.productName(l.product_id) || l.sell_unit || '';
    }
    // 支付方式四语标签(与收银台收款一致:qr 走 PromptPay,transfer 走转账)。
    function methodLabel(m) {
        return POS.t('posui.pay.' + (m === 'qr' ? 'promptpay' : m));
    }
    function round2(n) {
        return Math.round((Number(n) + Number.EPSILON) * 100) / 100;
    }

    function resetRefund() {
        refundSale = null;
        refundSel = {};
        refundWay = 'cash';
        refundAlloc = {};
        $('refund-receipt').value = '';
        $('refund-step2').classList.remove('on');
        $('refund-step3').classList.remove('on');
        loadToday();
    }
    // 今日交易列表:点一笔即进退货详情(免手输小票号),可作废的当班单带「作废」入口。
    async function loadToday() {
        const body = $('refund-body');
        body.innerHTML = '<div class="state">' + POS.t('posui.loading') + '</div>';
        try {
            todayItems = await POS.data.salesToday();
        } catch (e) {
            body.innerHTML =
                '<div class="state">' + POS.posErrMsg(e.code, 'pos.unexpected') + '</div>';
            return;
        }
        renderToday();
    }
    function renderToday() {
        const body = $('refund-body');
        if (!todayItems.length) {
            body.innerHTML =
                '<div class="state" id="refund-hint">' + POS.t('posui.refund.hint') + '</div>';
            return;
        }
        const rows = todayItems
            .map((it) => {
                const mix = it.mixed ? ' · ' + POS.t('posui.refund.mixed') : '';
                const sub = POS.hm(new Date(it.sold_at)) + ' · ' + methodLabel(it.method) + mix;
                const voidBtn = it.voidable
                    ? '<button class="tvoid" data-void="' +
                      it.id +
                      '">' +
                      POS.t('posui.void.action') +
                      '</button>'
                    : '';
                return (
                    '<div class="titem" data-sale="' +
                    it.id +
                    '"><div class="ti-main"><div class="ti-rc">' +
                    POS.esc(it.receipt_no || '') +
                    '</div><div class="ti-sub">' +
                    sub +
                    '</div></div><div class="ti-amt tnum">฿' +
                    fmt(it.grand_total) +
                    '</div>' +
                    voidBtn +
                    '</div>'
                );
            })
            .join('');
        body.innerHTML =
            '<div class="tlist"><div class="tlist-h">' +
            POS.t('posui.refund.today') +
            '</div>' +
            rows +
            '</div>';
        body.querySelectorAll('.titem[data-sale]').forEach((el) => {
            el.querySelector('.ti-main').onclick = () => openSale(el.dataset.sale);
            const vb = el.querySelector('[data-void]');
            if (vb)
                vb.onclick = (e) => {
                    e.stopPropagation();
                    doVoid(vb.dataset.void);
                };
        });
    }
    async function openSale(saleId) {
        $('refund-body').innerHTML = '<div class="state">' + POS.t('posui.loading') + '</div>';
        try {
            refundSale = await POS.data.saleDetail(saleId);
        } catch (e) {
            $('refund-body').innerHTML =
                '<div class="state">' + POS.posErrMsg(e.code, 'pos.product_not_found') + '</div>';
            return;
        }
        enterDetail();
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
        enterDetail();
    }
    function enterDetail() {
        refundSel = {};
        refundAlloc = {};
        $('refund-step2').classList.add('on');
        $('refund-step3').classList.add('on');
        renderRefund();
    }
    // 原单各支付方式(合并同方式)→ [{method, amount}]。退款默认镜像它原路退。
    function origMethods() {
        const map = {};
        (refundSale.payments || []).forEach((p) => {
            map[p.method] = (map[p.method] || 0) + Number(p.amount);
        });
        return Object.keys(map).map((m) => ({ method: m, amount: map[m] }));
    }
    // 按原单各方式占比把退款额分摊(末位吸收四舍五入余数,保证 Σ==total)。
    function defaultAlloc(methods, total) {
        const alloc = {};
        const origSum = methods.reduce((s, m) => s + m.amount, 0) || 1;
        let acc = 0;
        methods.forEach((m, i) => {
            const a =
                i === methods.length - 1
                    ? round2(total - acc)
                    : round2((total * m.amount) / origSum);
            if (i < methods.length - 1) acc += a;
            alloc[m.method] = a;
        });
        return alloc;
    }
    // 当前退货单是否可作废(单一事实源=今日列表的 voidable;经小票号进来的查不到即不可作废)。
    function currentVoidable() {
        const t = todayItems.find((x) => x.id === String(refundSale.sale.id));
        return t ? t.voidable : false;
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
            '</div>' +
            refundPanel();
        bindRefund();
        updateRefundState();
    }
    // 退款面板:原路退款方式(单方式=只读镜像原单/混合=各方式可微调金额)+ 诚实提示 + 引导。
    function refundPanel() {
        const methods = origMethods();
        const total = refundTotal();
        let wayHtml;
        if (methods.length > 1) {
            refundAlloc = defaultAlloc(methods, total);
            const prows = methods
                .map(
                    (m) =>
                        '<div class="prow"><span class="pm">' +
                        methodLabel(m.method) +
                        '</span><div class="inp"><span>฿</span><input class="tnum ralloc" data-m="' +
                        m.method +
                        '" inputmode="decimal" value="' +
                        fmt(refundAlloc[m.method]) +
                        '"></div></div>'
                )
                .join('');
            wayHtml =
                '<div class="way-orig"><div class="wo-h">' +
                POS.t('posui.refund.orig_way') +
                '</div>' +
                prows +
                '<div class="wo-sum ok" id="refund-alloc-box"><span>' +
                POS.t('posui.refund.alloc_sum') +
                '</span><span class="tnum" id="refund-alloc-sum">฿0.00</span></div></div>';
        } else {
            refundWay = (methods[0] && methods[0].method) || 'cash';
            wayHtml =
                '<div class="way-orig single"><div class="wo-h">' +
                POS.t('posui.refund.orig_way') +
                '</div><div class="prow one"><span class="pm">' +
                POS.tf('posui.refund.orig_to', { m: methodLabel(refundWay) }) +
                '</span></div></div>';
        }
        // 刷卡/转账/PromptPay 退款系统只记账,钱得在刷卡机/银行 App 实际退还 → 诚实提示。
        const notice = methods.some((m) => m.method !== 'cash')
            ? '<div class="pay-note"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v5M12 16h.01"/></svg>' +
              POS.t('posui.refund.record_only') +
              '</div>'
            : '';
        // 引导:当班错单→建议作废(干净回滚一切);已交班/隔日→只能退货(负单)。
        const guide = currentVoidable()
            ? '<div class="guide void"><span>' +
              POS.t('posui.refund.guide_void') +
              '</span><button class="gv-btn" id="refund-void-btn">' +
              POS.t('posui.void.action') +
              '</button></div>'
            : '<div class="guide"><span>' + POS.t('posui.refund.guide_refund') + '</span></div>';
        return (
            '<div class="refund">' +
            wayHtml +
            notice +
            guide +
            '<div class="stock-note"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7L12 3 4 7m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>' +
            POS.t('posui.refund.stock') +
            '</div><div class="total"><span class="l">' +
            POS.t('posui.refund.amount') +
            '</span><span class="v tnum" id="refund-total">฿0.00</span></div><button class="do" id="refund-do" disabled>' +
            POS.t('posui.refund.title') +
            '</button></div>'
        );
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
        // 混合原路拆退:各方式金额可微调,输入即更新分摊并重算 Σ(不整屏重渲,不抢焦点)。
        $('refund-body')
            .querySelectorAll('input.ralloc')
            .forEach((inp) => {
                inp.oninput = () => {
                    refundAlloc[inp.dataset.m] =
                        Number((inp.value || '0').replace(/[^\d.]/g, '')) || 0;
                    updateRefundState();
                };
            });
        const vb = $('refund-void-btn');
        if (vb) vb.onclick = () => doVoid(refundSale.sale.id);
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
    // 混合退款是否已把退款额分摊平(Σ 各方式 == 退款总额)。单方式恒平。
    function allocBalanced(total) {
        if (origMethods().length <= 1) return true;
        const sum = Object.keys(refundAlloc).reduce((s, m) => s + (Number(refundAlloc[m]) || 0), 0);
        return Math.abs(round2(sum) - round2(total)) < 0.005;
    }
    function updateRefundState() {
        const total = refundTotal();
        $('refund-total').textContent = '฿' + fmt(total);
        const box = $('refund-alloc-box');
        if (box) {
            const sum = Object.keys(refundAlloc).reduce(
                (s, m) => s + (Number(refundAlloc[m]) || 0),
                0
            );
            $('refund-alloc-sum').textContent = '฿' + fmt(sum);
            box.className = 'wo-sum ' + (allocBalanced(total) ? 'ok' : 'bad');
        }
        const has = Object.keys(refundSel).length > 0;
        const btn = $('refund-do');
        btn.disabled = !has || !allocBalanced(total);
        btn.textContent = has
            ? POS.tf('posui.refund.confirm', { n: fmt(total) })
            : POS.t('posui.refund.title');
    }
    function refundDone() {
        POS.toast(POS.t('posui.refund.done'));
        POS.showView('main');
        resetRefund();
    }
    function selectedRefundLines() {
        return Object.keys(refundSel).map((lid) => ({
            sale_line_id: lid,
            qty: String(refundSel[lid]),
            _amt:
                refundSel[lid] * Number(refundSale.lines.find((x) => lineId(x) === lid).unit_price),
        }));
    }
    async function doRefund() {
        const lines = selectedRefundLines();
        if (!lines.length) return;
        const total = refundTotal();
        if (!allocBalanced(total)) {
            POS.toast(POS.t('posui.refund.alloc_mismatch'), 'error');
            return;
        }
        // 混合原单→原路拆退各方式(正额,后端取负);单方式→走兼容路只给 refund_method。
        const methods = origMethods();
        let payments = null;
        let method = refundWay;
        if (methods.length > 1) {
            payments = methods
                .map((m) => ({ method: m.method, amount: round2(refundAlloc[m.method] || 0) }))
                .filter((p) => p.amount > 0);
            method = (payments[0] && payments[0].method) || 'cash';
        }
        const btn = $('refund-do');
        const saleId = refundSale.sale.id;
        btn.disabled = true;
        try {
            await POS.data.refund(saleId, lines, method, null, payments);
            refundDone();
        } catch (e) {
            // 授权闸开 + 收银员无权 → 弹店长授权窗,凭据带回重试;其余错误照常提示。
            if (e.code === 'pos.approval_required' && POS.approve) {
                POS.approve.open(
                    (creds) => POS.data.refund(saleId, lines, method, creds, payments),
                    refundDone
                );
                btn.disabled = false;
                return;
            }
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
            btn.disabled = false;
        }
    }
    // 当班作废:有权直作废;授权闸开且收银员无权→店长 PIN 覆盖;非当班/已退过后端兜 void_not_allowed。
    async function doVoid(saleId) {
        const done = () => {
            POS.toast(POS.t('posui.void.done'));
            resetRefund();
        };
        try {
            await POS.data.void(saleId);
            done();
        } catch (e) {
            if (e.code === 'pos.approval_required' && POS.approve) {
                POS.approve.open((creds) => POS.data.void(saleId, creds), done);
                return;
            }
            POS.toast(POS.posErrMsg(e.code, 'pos.unexpected'), 'error');
        }
    }

    function init() {
        $('refund-find-btn').addEventListener('click', findReceipt);
        $('refund-receipt').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') findReceipt();
        });
    }

    POS.ops = { init, resetRefund };
})();
