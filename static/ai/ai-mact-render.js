/*
 * Pearnly AI · ai-mact-render.js · 机器自动改动清单(SA-1)
 *
 * 引擎会在无人确认的情况下改判料件归类、按余额链改写银行行的金额与借贷方向。这些改动
 * 此前只落事件流,任何界面都不呈现——会计看到的是改后的结果,看不到"改过"这件事。本文件
 * 把 order_detail.machine_actions 渲染进交付包页,位置在签字键之前,签字必经。
 *
 * 拆成独立文件而不塞进 ai-pkg-render.js:那边已顶到 500 行铁律线,且这块随 SA-2/SA-3 还会
 * 长(截断标记、推算值、模型救援都要挂进来)。依赖 at()/AI.state/AI.pkgRender,只在浏览器
 * 根挂载;加载顺序见 scripts/build-home-js.mjs。
 */
(function (root) {
    'use strict';

    function esc(s) {
        return root.AI.state.esc(s);
    }

    // kind 是后端内部词汇(non_tax/bank_statement…),会计看不懂。有译名用译名,没有回落原值——
    // 宁可露出内部词也不显示裸 i18n key(at() 缺 key 时原样返回 key)。
    function kindLabel(kind) {
        var key = 'mact_kind_' + kind;
        var label = at(key);
        return label === key ? kind : label;
    }

    function displayName(a) {
        return esc(root.AI.pkgRender.displayFileName(a.name || a.item_id || ''));
    }

    function regroupRowHtml(a) {
        var why =
            a.reason === 'statement_sequence'
                ? '<small>' + esc(at('mact_reason_statement_sequence')) + '</small>'
                : '';
        return (
            '<div class="mact-row"><b>' +
            displayName(a) +
            '</b><span>' +
            esc(
                at('mact_regroup', {
                    from: kindLabel(a.from_kind),
                    to: kindLabel(a.to_kind),
                })
            ) +
            '</span>' +
            why +
            '</div>'
        );
    }

    function bankRowHtml(a) {
        var parts = [];
        if (a.amount_rows) parts.push(at('mact_bank_amount', { n: a.amount_rows }));
        if (a.direction_rows) parts.push(at('mact_bank_direction', { n: a.direction_rows }));
        parts.push(at('mact_bank_meta', { n: a.row_count }));
        return (
            '<div class="mact-row"><b>' +
            displayName(a) +
            '</b><span>' +
            esc(parts.join(' · ')) +
            '</span><small>' +
            esc(at('mact_bank_why')) +
            '</small></div>'
        );
    }

    // 表外的新类型走 default:露出原始 type 让人看见"改过",不冒充银行行。producer 会随
    // SA-2/SA-3 增多(模型救援、截断标记),后端先行发版时签字页宁可粗陋也不能空白或张冠李戴。
    var ROW_RENDERERS = {
        item_regrouped: regroupRowHtml,
        bank_row_autocorrected: bankRowHtml,
    };

    function genericRowHtml(a) {
        return (
            '<div class="mact-row"><b>' +
            displayName(a) +
            '</b><span>' +
            esc(at('mact_generic', { type: a.type || '?' })) +
            '</span></div>'
        );
    }

    function rowHtml(a) {
        return (ROW_RENDERERS[a.type] || genericRowHtml)(a);
    }

    function panelHtml(detail) {
        var actions = (detail || {}).machine_actions || [];
        if (!actions.length) return '';
        return (
            '<div class="panel mact"><div class="hd"><h3>' +
            esc(at('mact_title')) +
            '</h3><span class="note">' +
            esc(at('mact_sub')) +
            '</span></div><div class="bd">' +
            actions.map(rowHtml).join('') +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.mactRender = { panelHtml: panelHtml };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
