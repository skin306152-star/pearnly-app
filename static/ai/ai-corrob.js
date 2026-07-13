/*
 * Pearnly AI · ai-corrob.js · 销项佐证卡(MC1-c.1)· 已开票销售逐票聚合的只读四态呈现
 *
 * 挂在工单详情(wo 视图)关键数字之下,数据源是 ai-client.js renderWo() 已取到的
 * order_detail().sales_corroboration(不再发第二次网络请求)。纯只读——本方销项票的逐票
 * 聚合是佐证/地板,不夺 R2 权威销项;卡上如实呈现「已开票金额 / 占比 / 缺口点名 / 判据一句话 /
 * 守恒违反单列」。零交互(逐票确认走人审队列的 S 键,不在本卡)。
 *
 * 上半段(coveredChipKey)零 DOM/零 i18n,node(tests/unit/test_ai_corrob_pure.py)直接
 * require 断言;下半段 HTML 拼装依赖 at()/AI.state/AI.format,只在浏览器根挂载——同
 * ai-recon-render.js 双段先例。数据形状见 services/workorder/steps/sales_aggregate.py::
 * build_corroboration(covered_state/net_total/gap_net/duplicates/conservation_violations…),
 * 本文件只读不改其形状。
 */
(function (root) {
    'use strict';

    // covered_state → chip 的 i18n key + 颜色族(g=绿充分 / w=黄覆盖不全 / n=灰权威未申报)。
    var _STATE = {
        green: { key: 'crb_state_green', cls: 'g' },
        amber: { key: 'crb_state_amber', cls: 'w' },
        needs: { key: 'crb_state_needs', cls: 'n' },
    };
    function coveredChipKey(crb) {
        var st = (crb && crb.covered_state) || 'needs';
        return _STATE[st] ? st : 'needs';
    }

    var pure = { coveredChipKey: coveredChipKey };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }
    function money(v) {
        return v == null || v === '' ? '—' : root.AI.format.money(v);
    }
    function pct(coverage) {
        var n = parseFloat(coverage);
        return isFinite(n) ? (n * 100).toFixed(1) + '%' : '—';
    }

    function line(label, value) {
        return (
            '<div class="crb-line"><span class="crb-lb">' +
            esc(label) +
            '</span><span class="crb-vl">' +
            value +
            '</span></div>'
        );
    }

    // 权威对比区:有权威 → 缺口 + 占比点名(黄/绿);无权威 → needs 提示(不编造缺口)。
    function authoritativeHtml(crb) {
        if (crb.covered_state === 'needs' || crb.authoritative_net == null) {
            return '<div class="crb-needs">' + esc(at('crb_needs_hint')) + '</div>';
        }
        return (
            line(at('crb_vs_authoritative'), money(crb.authoritative_net)) +
            line(
                at('crb_gap'),
                '<span class="crb-gap">' +
                    money(crb.gap_net) +
                    '</span> · ' +
                    esc(at('crb_coverage', { pct: pct(crb.coverage) }))
            )
        );
    }

    // 点名区:重复票号(已去重不双计)+ 守恒违反(票面不自洽单列人审)。均为空则不出行。
    function namedHtml(crb) {
        var out = '';
        var dupes = crb.duplicates || [];
        var viol = crb.conservation_violations || [];
        if (dupes.length) {
            out +=
                '<div class="crb-note">' +
                esc(at('crb_dupes', { list: dupes.join('、') })) +
                '</div>';
        }
        if (viol.length) {
            out +=
                '<div class="crb-note crb-viol">' +
                esc(at('crb_violations', { list: viol.join('、') })) +
                '</div>';
        }
        return out;
    }

    function pageHtml(crb) {
        if (!crb) return '';
        var st = coveredChipKey(crb);
        var chip =
            '<span class="chip ' + _STATE[st].cls + '">' + esc(at(_STATE[st].key)) + '</span>';
        var count = at('crb_tickets', { n: crb.invoice_count, m: crb.deduped_count });
        var period =
            crb.date_from && crb.date_to ? esc(crb.date_from) + ' – ' + esc(crb.date_to) : '—';
        return (
            '<div class="panel crb"><div class="hd"><h3>' +
            esc(at('crb_title')) +
            ' ' +
            chip +
            '</h3></div><div class="bd">' +
            line(at('crb_invoiced'), money(crb.net_total) + ' · ' + esc(count)) +
            line(at('crb_vat_label'), money(crb.vat_total)) +
            line(at('crb_period'), period) +
            authoritativeHtml(crb) +
            namedHtml(crb) +
            '<div class="crb-basis">' +
            esc(at('crb_basis')) +
            '</div>' +
            '</div></div>'
        );
    }

    // container 由 ai-client.js renderWo 传入;crb 是 order_detail().sales_corroboration
    // (null → 不渲染,前端不假装有已开票数据)。
    function mount(crb, container) {
        if (!container) return;
        container.innerHTML = crb ? pageHtml(crb) : '';
    }

    root.AI = root.AI || {};
    root.AI.corrob = { mount: mount, pageHtml: pageHtml, coveredChipKey: coveredChipKey };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
