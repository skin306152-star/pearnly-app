/*
 * Pearnly AI · ai-corrob.js · 销项佐证卡(MC1-c.1 / SA-2b)· 只读四态呈现
 *
 * 挂在工单详情(wo 视图)关键数字之下,数据源是 ai-client.js renderWo() 已取到的
 * order_detail().sales_corroboration(c.1 逐票聚合)与 edc_corroboration(SA-2 EDC 结算
 * 聚合),两卡并排、同一套渲染只换文案(_SRC 按 source 取 i18n key)。纯只读——聚合是
 * 佐证/地板,不夺 R2 权威销项;卡上如实呈现「聚合金额 / 覆盖占比 / 缺口点名 / 判据一句话」。
 *
 * 上半段(coveredChipKey/srcVariant)零 DOM/零 i18n,node(tests/unit/test_ai_corrob_pure.py)
 * 直接 require 断言;下半段 HTML 拼装依赖 at()/AI.state/AI.format,只在浏览器根挂载——同
 * ai-recon-render.js 双段先例。数据形状见 services/workorder/steps/sales_aggregate.py 与
 * edc_corroboration.py 的 build_corroboration,本文件只读不改其形状。
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

    // source → 文案族。两卡钱字段同形(net_total/coverage/…),差异只在标题/口径措辞。
    var _SRC = {
        invoice_aggregate: {
            title: 'crb_title',
            invoiced: 'crb_invoiced',
            vat: 'crb_vat_label',
            period: 'crb_period',
            tickets: 'crb_tickets',
            basis: 'crb_basis',
        },
        edc_aggregate: {
            title: 'crb_title_edc',
            invoiced: 'crb_invoiced_edc',
            vat: 'crb_vat_label_edc',
            period: 'crb_period_edc',
            tickets: 'crb_tickets_edc',
            basis: 'crb_basis_edc',
        },
    };
    function srcVariant(crb) {
        var s = (crb && crb.source) || 'invoice_aggregate';
        return _SRC[s] ? s : 'invoice_aggregate';
    }

    var pure = { coveredChipKey: coveredChipKey, srcVariant: srcVariant };
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

    // 点名区:重复票号(已去重不双计)+ 守恒违反(c.1)/ 聚合冲突点名(EDC)。均空则不出行。
    function namedHtml(crb) {
        var out = '';
        var dupes = crb.duplicates || [];
        var viol = crb.conservation_violations || [];
        var conflicts = crb.conflicts || [];
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
        if (conflicts.length) {
            out +=
                '<div class="crb-note crb-viol">' +
                esc(at('crb_conflicts_edc', { n: conflicts.length })) +
                '</div>';
        }
        return out;
    }

    function pageHtml(crb) {
        if (!crb) return '';
        var st = coveredChipKey(crb);
        var k = _SRC[srcVariant(crb)];
        var chip =
            '<span class="chip ' + _STATE[st].cls + '">' + esc(at(_STATE[st].key)) + '</span>';
        var count = at(k.tickets, { n: crb.invoice_count, m: crb.deduped_count });
        var period =
            crb.date_from && crb.date_to ? esc(crb.date_from) + ' – ' + esc(crb.date_to) : '—';
        return (
            '<div class="panel crb"><div class="hd"><h3>' +
            esc(at(k.title)) +
            ' ' +
            chip +
            '</h3></div><div class="bd">' +
            line(at(k.invoiced), money(crb.net_total) + ' · ' + esc(count)) +
            line(at(k.vat), money(crb.vat_total)) +
            line(at(k.period), period) +
            authoritativeHtml(crb) +
            namedHtml(crb) +
            '<div class="crb-basis">' +
            esc(at(k.basis)) +
            '</div>' +
            '</div></div>'
        );
    }

    // container 由 ai-client.js renderWo 传入;crb/edcCrb 是 order_detail() 的
    // sales_corroboration / edc_corroboration(null → 不渲染,前端不假装有聚合数据)。
    function mount(crb, container, edcCrb) {
        if (!container) return;
        container.innerHTML = (crb ? pageHtml(crb) : '') + (edcCrb ? pageHtml(edcCrb) : '');
    }

    root.AI = root.AI || {};
    root.AI.corrob = {
        mount: mount,
        pageHtml: pageHtml,
        coveredChipKey: coveredChipKey,
        srcVariant: srcVariant,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
