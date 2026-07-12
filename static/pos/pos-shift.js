/*
 * Pearnly POS · pos-shift.js · 屏5 交班日结(视觉照搬概念稿 05)
 * 数据走 window.POS.data(B2 前 mock 兜底);失败统一 posErrMsg。对外 window.POS.shift。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const $ = (id) => document.getElementById(id);
    const fmt = POS.fmt;

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
        // 未结班中途看=X 报表(班中小计);连号 #N 让收银员与老板对得上同一张班。
        const seqTag =
            sh.shift_seq != null
                ? '<span class="seq">· ' +
                  POS.tf('posui.shift.seq', { n: sh.shift_seq }) +
                  '</span>'
                : '';
        wrap.innerHTML =
            '<div class="card"><div class="h"><svg class="ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>' +
            POS.t('posui.shift.cashier') +
            ' ' +
            POS.esc(state.cashier ? state.cashier.display_name : '') +
            ' ' +
            seqTag +
            '<span class="xtag">' +
            POS.t('posui.shift.xtag') +
            '</span></div><div class="kv"><span class="k">' +
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

    POS.shift = { renderShift };
})();
