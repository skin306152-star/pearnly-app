/*
 * Pearnly AI · ai-financials-render.js · 月度报表包(G1b)BS/PL/TB 三件套 + 账龄/折旧
 * 四态降级只读视图纯逻辑 + HTML 拼装
 *
 * 上半段(balanceState/equityDisplayRows)零 DOM/零 i18n 依赖,node
 * (tests/unit/test_ai_financials_pure.py)直接 require 断言;下半段依赖 at()/AI.state/
 * AI.format,只在浏览器根挂载——同 ai-shadow-render.js 的双段先例。
 *
 * 数据源:services/workorder/api.py::order_detail 的 financials 字段,原样透传
 * services/accounting/workorder_financials.py::build_financials——本文件只读不改其形状,
 * 复式规则引擎/books 变换层一行不碰(G1a 影子非第二账本护栏原样延续到报表视图层)。
 */
(function (root) {
    'use strict';

    // 配平判定 → 胶囊态(cls 沿用全局 .chip 色族:g=配平/w=有差异)。balanced 缺失(非
    // true/false)理论不该发生(api.py::_financials 已把没有 balance_sheet 键的残影过滤成
    // null)——仍不假装平,直接落警示态。
    function balanceState(balanced) {
        return balanced === true
            ? { cls: 'g', key: 'fin_balanced_chip' }
            : { cls: 'w', key: 'fin_unbalanced_chip' };
    }

    // 权益节展示行 = 预置权益科目(单月常为空,无留存收益科目)+ 本期损益一行恒显示
    // (current_earnings,即使为 0 也列出)。BS 视觉配平硬约束:禁止只渲染空 equity 数组
    // 导致「资产≠负债+权益」的错觉——用户必须看到本期净利已计入权益方。current_earnings
    // 不是预置科目(无科目码/双语名),呈现层用固定 i18n key 标注。
    function equityDisplayRows(bs) {
        bs = bs || {};
        var rows = (bs.equity || []).map(function (r) {
            return {
                code: r.code,
                name_zh: r.name_zh,
                name_th: r.name_th,
                amount: r.amount,
                current_earnings: false,
            };
        });
        rows.push({
            code: null,
            name_zh: null,
            name_th: null,
            amount: bs.current_earnings,
            current_earnings: true,
        });
        return rows;
    }

    var pure = {
        balanceState: balanceState,
        equityDisplayRows: equityDisplayRows,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.format,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }
    function money(v) {
        return v == null || v === '' ? '—' : root.AI.format.money(v);
    }
    function curLang() {
        return (root.AII18N && root.AII18N.lang) || 'zh';
    }
    // 科目中泰名走 coa_preset 单一事实源,无 en/ja 独立译名——th 语言取泰文名,
    // 其余三语(zh/en/ja)统一回退中文名(会计科目码本身就是工作语言,同 at() 的
    // D[lang]→D.zh 回退口径)。
    function acctName(row) {
        if (!row) return '';
        return curLang() === 'th'
            ? row.name_th || row.name_zh || ''
            : row.name_zh || row.name_th || '';
    }

    // ============ 折叠区壳(五分区共用:bs/pl/tb/aging/depreciation)============

    function foldSectionHtml(kind, headerHtml, open, bodyHtml) {
        return (
            '<div class="fin-section' +
            (open ? ' on' : '') +
            '" data-fin-kind="' +
            kind +
            '">' +
            '<button type="button" class="fin-fold" data-action="fin-fold" data-kind="' +
            kind +
            '">' +
            headerHtml +
            '<span class="fin-caret">' +
            (open ? esc(at('brx_collapse')) : esc(at('brx_expand'))) +
            '</span>' +
            '</button>' +
            '<div class="fin-body">' +
            bodyHtml +
            '</div>' +
            '</div>'
        );
    }

    // ============ 科目金额表(资产/负债/权益/收入/费用共用同一 {code,name,amount} 形状)==

    function acctRowHtml(r) {
        var label = r.current_earnings
            ? '<i>' + esc(at('fin_bs_current_earnings')) + '</i>'
            : esc(r.code) + ' ' + esc(acctName(r));
        return (
            '<tr' +
            (r.current_earnings ? ' class="fin-earnings-row"' : '') +
            '><td>' +
            label +
            '</td><td class="num">' +
            money(r.amount) +
            '</td></tr>'
        );
    }

    function acctTableHtml(rows, emptyKey) {
        rows = rows || [];
        if (!rows.length) return '<p class="fin-empty">' + esc(at(emptyKey)) + '</p>';
        return (
            '<div class="mx-scroll"><table class="mx-table"><thead><tr>' +
            '<th>' +
            esc(at('shadow_col_name')) +
            '</th><th class="num">' +
            esc(at('shadow_col_amount')) +
            '</th></tr></thead><tbody>' +
            rows.map(acctRowHtml).join('') +
            '</tbody></table></div>'
        );
    }

    // 标题 + 配平徽章头(BS/TB 共用);小节标题 + 科目表(资产/负债/权益/收入/费用共用)。
    function chipHeaderHtml(titleKey, state) {
        return (
            '<span>' +
            esc(at(titleKey)) +
            '</span><span class="chip ' +
            state.cls +
            '">' +
            esc(at(state.key)) +
            '</span>'
        );
    }

    function subtitleTable(subtitleKey, rows, emptyKey) {
        return (
            '<p class="fin-subtitle">' +
            esc(at(subtitleKey)) +
            '</p>' +
            acctTableHtml(rows, emptyKey)
        );
    }

    // ============ 资产负债表 ============

    function bsSectionHtml(bs, open) {
        bs = bs || {};
        var header = chipHeaderHtml('fin_bs_title', balanceState(bs.balanced));
        var body =
            '<p class="fin-note">' +
            esc(
                at('fin_bs_totals_note', {
                    assets: money(bs.asset_total),
                    liabilities: money(bs.liability_total),
                    equity: money(bs.equity_total),
                })
            ) +
            '</p>' +
            subtitleTable('fin_bs_assets', bs.assets, 'fin_bs_empty') +
            subtitleTable('fin_bs_liabilities', bs.liabilities, 'fin_bs_empty') +
            subtitleTable('fin_bs_equity', equityDisplayRows(bs), 'fin_bs_empty');
        return foldSectionHtml('bs', header, open, body);
    }

    // ============ 损益表 ============

    function plSectionHtml(pl, open) {
        pl = pl || {};
        var header =
            '<span>' +
            esc(at('fin_pl_title')) +
            '</span><span class="note" style="margin-left:auto">' +
            esc(at('fin_pl_net_profit', { amount: money(pl.net_profit) })) +
            '</span>';
        var body =
            subtitleTable('fin_pl_revenue', pl.revenue, 'fin_pl_empty') +
            subtitleTable('fin_pl_expense', pl.expense, 'fin_pl_empty');
        return foldSectionHtml('pl', header, open, body);
    }

    // ============ 试算平衡表 ============

    function tbRowHtml(r) {
        return (
            '<tr><td>' +
            esc(r.code) +
            ' ' +
            esc(acctName(r)) +
            '</td><td class="num">' +
            money(r.debit) +
            '</td><td class="num">' +
            money(r.credit) +
            '</td></tr>'
        );
    }

    function tbSectionHtml(tb, open) {
        tb = tb || {};
        var header = chipHeaderHtml('fin_tb_title', balanceState(tb.balanced));
        var rows = tb.rows || [];
        var body =
            '<p class="fin-note">' +
            esc(at('fin_tb_totals_note', { debit: money(tb.debit), credit: money(tb.credit) })) +
            '</p>' +
            (rows.length === 0
                ? '<p class="fin-empty">' + esc(at('fin_tb_empty')) + '</p>'
                : '<div class="mx-scroll"><table class="mx-table"><thead><tr>' +
                  '<th>' +
                  esc(at('shadow_col_name')) +
                  '</th><th class="num">' +
                  esc(at('shadow_col_debit')) +
                  '</th><th class="num">' +
                  esc(at('shadow_col_credit')) +
                  '</th></tr></thead><tbody>' +
                  rows.map(tbRowHtml).join('') +
                  '</tbody></table></div>');
        return foldSectionHtml('tb', header, open, body);
    }

    // ============ 账龄 / 折旧(四态诚实降级:source=="not_wired" → 中性占位,不编假表)===

    function notWiredSectionHtml(kind, open, titleKey, noteKey) {
        var header =
            '<span>' +
            esc(at(titleKey)) +
            '</span><span class="chip n">' +
            esc(at('fin_not_wired_chip')) +
            '</span>';
        var body = '<p class="fin-note">' + esc(at(noteKey)) + '</p>';
        return foldSectionHtml(kind, header, open, body);
    }

    // ============ 顶层组装 ============

    // ui: {open:{bs,pl,tb,aging,depreciation}}(ai-financials.js 持有的折叠态)。
    function pageHtml(financials, ui) {
        if (!financials) {
            return (
                '<div class="panel"><div class="hd"><h3>' +
                esc(at('fin_title')) +
                '</h3></div><div class="bd">' +
                root.AI.state.emptyHtml({
                    title: at('fin_disabled_t'),
                    sub: at('fin_disabled_s'),
                }) +
                '</div></div>'
            );
        }
        var unclassified = financials.unclassified_accounts || [];
        var hint = unclassified.length
            ? '<p class="fin-hint">' +
              esc(at('fin_unclassified_hint', { n: unclassified.length })) +
              '</p>'
            : '';
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('fin_title')) +
            (financials.period
                ? '<span class="note" style="margin-left:auto">' +
                  esc(at('fin_period_label', { period: financials.period })) +
                  '</span>'
                : '') +
            '</h3></div><div class="bd fin-body-wrap">' +
            hint +
            bsSectionHtml(financials.balance_sheet, ui.open.bs) +
            plSectionHtml(financials.profit_loss, ui.open.pl) +
            tbSectionHtml(financials.trial_balance, ui.open.tb) +
            notWiredSectionHtml(
                'aging',
                ui.open.aging,
                'fin_aging_title',
                'fin_aging_not_wired_note'
            ) +
            notWiredSectionHtml(
                'depreciation',
                ui.open.depreciation,
                'fin_depreciation_title',
                'fin_depreciation_not_wired_note'
            ) +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.financialsRender = {
        balanceState: balanceState,
        equityDisplayRows: equityDisplayRows,
        pageHtml: pageHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
