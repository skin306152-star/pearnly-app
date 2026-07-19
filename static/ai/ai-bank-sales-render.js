/*
 * Pearnly AI · ai-bank-sales-render.js · 银行流水倒推销项建议(SA-3b)的纯逻辑 + HTML 拼装
 *
 * 数据源:services/workorder/api.py::order_detail 的 bank_sales_suggestion 投影(SA-3a
 * services/workorder/steps/bank_sales_suggest.py::suggest 原样透传,本文件只读不改其形状)。
 * 闸 pearnly_ai_bank_sales_suggest 关 = 键缺席 = cardHtml 返回空串,现有人工填销项表单逐字节
 * 不变。三态契约见该模块顶注:not_applicable(现金型客户)/ 覆盖降级(不出建议值,只读明细)/
 * 可用(三区确认清单 + 一键采用)。
 *
 * 上半段(diffRatio/canApply/groupRows)零 DOM/零 i18n 依赖,node(tests/unit/
 * test_ai_pure_modules.py)直接 require 断言;下半段 HTML 拼装依赖 at()/AI.state/AI.format,
 * 只在浏览器根挂载——同 ai-recon-render.js 双段先例。挂载/交互(折叠/行级裁决/让 AI 预判/
 * 采用建议值)在 ai-intake.js(收料 tab 已有的编排层,本卡是它的一个子区块,不另开 mount)。
 */
(function (root) {
    'use strict';

    var SALES = 'sales';
    var NON_SALES = 'non_sales';
    var PENDING = 'pending';

    // 交叉佐证差异阈值(方案 §三.3 · 与引擎覆盖降级阈值 _INFLOW_GAP_MAX 同一条材料性线)。
    var DIFF_WARN_RATIO = 0.02;

    var REASON_KEY = {
        zero_movement: 'bxs_reason_zero',
        withdrawal: 'bxs_reason_withdrawal',
        bank_fee: 'bxs_reason_fee',
        cancelled: 'bxs_reason_cancel',
        edc_settlement_matched: 'bxs_reason_edc',
        deposit_unclassified: 'bxs_reason_pending',
    };
    var SOURCE_KEY = {
        rule: 'bxs_source_rule',
        brain: 'bxs_source_brain',
        human: 'bxs_source_human',
    };

    function toNum(v) {
        var n = parseFloat(v);
        return isFinite(n) ? n : null;
    }

    // 相对差比:|a-b| / max(|a|,|b|)(对称,分母为二者较大者,防除零)。任一侧解不出 → null
    // (调用方据此不出佐证行,不假装比较过)。
    function diffRatio(a, b) {
        var x = toNum(a);
        var y = toNum(b);
        if (x == null || y == null) return null;
        var base = Math.max(Math.abs(x), Math.abs(y));
        return base === 0 ? 0 : Math.abs(x - y) / base;
    }

    // 与 SA-2 EDC 聚合(edc_aggregate)/开票销售聚合(invoice_aggregate)并排比较——只在建议
    // 可用(reliable)且对方聚合确有 net_total 时才出一行,零 crb 数据不编造佐证。
    function crossCheckRows(suggestion, salesCrb, edcCrb) {
        if (!suggestion || !suggestion.reliable || suggestion.sales_amount == null) return [];
        var bank = suggestion.sales_amount;
        var out = [];
        [
            ['invoice', salesCrb],
            ['edc', edcCrb],
        ].forEach(function (pair) {
            var kind = pair[0];
            var crb = pair[1];
            if (!crb || crb.net_total == null) return;
            var ratio = diffRatio(bank, crb.net_total);
            out.push({
                kind: kind,
                amount: crb.net_total,
                ratio: ratio,
                warn: ratio != null && ratio > DIFF_WARN_RATIO,
            });
        });
        return out;
    }

    // 「采用建议值」亮起时机(派单契约):reliable 且待确认行清零——cannot_judge 已在引擎侧
    // 折入 pending,人必须裁完才放行。
    function canApply(suggestion) {
        return !!(
            suggestion &&
            suggestion.applicable &&
            suggestion.reliable &&
            Number(suggestion.pending_count) === 0
        );
    }

    function readinessChip(suggestion) {
        var pending = Number(suggestion && suggestion.pending_count) || 0;
        if (canApply(suggestion)) {
            return { cls: 'g', key: 'bxs_state_reliable_chip', vars: null };
        }
        return { cls: 'w', key: 'bxs_state_pending_chip', vars: { n: pending } };
    }

    function groupRows(rows) {
        var out = { sales: [], pending: [], nonSales: [] };
        (rows || []).forEach(function (r) {
            if (r.verdict === SALES) out.sales.push(r);
            else if (r.verdict === NON_SALES) out.nonSales.push(r);
            else out.pending.push(r);
        });
        return out;
    }

    function freshUiState() {
        return {
            open: { sales: false, pending: true, nonSales: true },
            rowBusy: {},
            rowErr: {},
            runBusy: false,
            runErrKey: null,
        };
    }

    var pure = {
        SALES: SALES,
        NON_SALES: NON_SALES,
        PENDING: PENDING,
        DIFF_WARN_RATIO: DIFF_WARN_RATIO,
        REASON_KEY: REASON_KEY,
        SOURCE_KEY: SOURCE_KEY,
        diffRatio: diffRatio,
        crossCheckRows: crossCheckRows,
        canApply: canApply,
        readinessChip: readinessChip,
        groupRows: groupRows,
        freshUiState: freshUiState,
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
    function localizedMessage(message) {
        if (!message) return '';
        var lang = (root.AII18N && root.AII18N.lang) || 'en';
        return message[lang] || message.en || '';
    }

    // 三张流水行清单共用折叠外壳(视觉照抄 ai-recon-render.js 的 .brx-section/.brx-fold,
    // 逻辑不跨模块引用——sectionHtml 在那边未导出,各管各的小函数比强行共享更省心)。
    function foldSection(kind, titleKey, count, open, rowsHtml, emptyKey) {
        var chipCls =
            count === 0 ? 'n' : kind === 'nonSales' ? 'n' : kind === 'pending' ? 'w' : 's';
        var body = count === 0 ? '<p class="brx-empty">' + esc(at(emptyKey)) + '</p>' : rowsHtml;
        return (
            '<div class="brx-section' +
            (open ? ' on' : '') +
            '" data-bxs-kind="' +
            kind +
            '"><button type="button" class="brx-fold" data-action="bxs-fold" data-kind="' +
            kind +
            '"><span>' +
            esc(at(titleKey, { n: count })) +
            '</span><span class="chip ' +
            chipCls +
            '">' +
            count +
            '</span><span class="brx-caret">' +
            (open ? esc(at('brx_collapse')) : esc(at('brx_expand'))) +
            '</span></button><div class="brx-body">' +
            body +
            '</div></div>'
        );
    }

    function rowMetaHtml(row) {
        var reasonKey = REASON_KEY[row.reason];
        return (
            '<span class="bxs-src">' +
            esc(at(SOURCE_KEY[row.source] || 'bxs_source_rule')) +
            '</span>' +
            (reasonKey ? '<span class="bxs-reason">' + esc(at(reasonKey)) + '</span>' : '')
        );
    }

    // 待确认行:销售|非销售 双钮;非销售行:单钮可翻案标记回销售;销售行只读展示
    // (方案 §三.2:确定行不必再互相翻,防 UI 噪声——需要改判走非销售侧的翻案钮)。
    function rowActionsHtml(row, ui) {
        var fp = row.fingerprint;
        var busy = !!ui.rowBusy[fp];
        var btns = '';
        function btn(verdict, labelKey) {
            return (
                '<button type="button" class="btn sm" data-action="bxs-decide" data-fp="' +
                esc(fp) +
                '" data-verdict="' +
                verdict +
                '"' +
                (busy ? ' disabled' : '') +
                '>' +
                esc(busy ? at('bxs_decide_busy') : at(labelKey)) +
                '</button>'
            );
        }
        if (row.verdict === PENDING) {
            btns = btn(SALES, 'bxs_decide_sales') + btn(NON_SALES, 'bxs_decide_nonsales');
        } else if (row.verdict === NON_SALES) {
            btns = btn(SALES, 'bxs_flip_to_sales');
        }
        var err = ui.rowErr[fp] ? '<div class="bxs-err">' + esc(at(ui.rowErr[fp])) + '</div>' : '';
        return (btns ? '<div class="brx-actions">' + btns + '</div>' : '') + err;
    }

    function rowLineHtml(row) {
        var net = (parseFloat(row.deposit) || 0) - (parseFloat(row.withdrawal) || 0);
        return (
            esc(row.date || '—') +
            ' · ' +
            '<span class="num">' +
            money(String(net)) +
            '</span>' +
            (row.description ? ' · ' + esc(row.description) : '')
        );
    }

    function rowHtml(row, ui) {
        return (
            '<div class="brx-row"><span class="brx-tx">' +
            rowLineHtml(row) +
            '</span><div class="bxs-meta">' +
            rowMetaHtml(row) +
            '</div>' +
            rowActionsHtml(row, ui) +
            '</div>'
        );
    }

    // 降级卡逐行只读展示(无决策按钮,见 degradeCardHtml 顶注)。
    function readonlyRowHtml(row) {
        return (
            '<div class="brx-row"><span class="brx-tx">' +
            rowLineHtml(row) +
            '</span><div class="bxs-meta">' +
            rowMetaHtml(row) +
            '</div></div>'
        );
    }

    function summaryLine(label, value) {
        return (
            '<div class="bxs-sum-line"><span class="bxs-sum-lb">' +
            esc(label) +
            '</span><span class="bxs-sum-vl num">' +
            value +
            '</span></div>'
        );
    }

    function crossCheckHtml(rows) {
        if (!rows.length) return '';
        var lines = rows
            .map(function (r) {
                var labelKey = r.kind === 'edc' ? 'bxs_crosscheck_edc' : 'bxs_crosscheck_invoice';
                var pct = root.AI.format.pct(r.ratio);
                var chip = r.warn
                    ? '<span class="chip w">' +
                      esc(at('bxs_crosscheck_diff_warn', { pct: pct })) +
                      '</span>'
                    : '<span class="chip s">' +
                      esc(at('bxs_crosscheck_diff_ok', { pct: pct })) +
                      '</span>';
                return (
                    '<div class="bxs-xc-row"><span class="bxs-xc-lb">' +
                    esc(at(labelKey)) +
                    '</span><span class="bxs-xc-vl num">' +
                    money(r.amount) +
                    '</span>' +
                    chip +
                    '</div>'
                );
            })
            .join('');
        return (
            '<div class="bxs-xc"><div class="bxs-xc-h">' +
            esc(at('bxs_crosscheck_t')) +
            '</div>' +
            lines +
            '</div>'
        );
    }

    function runRowHtml(ui) {
        var err = ui.runErrKey ? '<div class="bxs-err">' + esc(at(ui.runErrKey)) + '</div>' : '';
        return (
            '<div class="bxs-run"><button type="button" class="btn" data-action="bxs-run"' +
            (ui.runBusy ? ' disabled' : '') +
            '>' +
            esc(ui.runBusy ? at('bxs_run_busy') : at('bxs_run_btn')) +
            '</button>' +
            err +
            '</div>'
        );
    }

    function sectionsHtml(grouped, ui, rowFn) {
        return (
            foldSection(
                'sales',
                'bxs_sales_title',
                grouped.sales.length,
                ui.open.sales,
                grouped.sales.map(rowFn).join(''),
                'bxs_sales_empty'
            ) +
            foldSection(
                'pending',
                'bxs_pending_title',
                grouped.pending.length,
                ui.open.pending,
                grouped.pending.map(rowFn).join(''),
                'bxs_pending_empty'
            ) +
            foldSection(
                'nonSales',
                'bxs_nonsales_title',
                grouped.nonSales.length,
                ui.open.nonSales,
                grouped.nonSales.map(rowFn).join(''),
                'bxs_nonsales_empty'
            )
        );
    }

    // 覆盖降级卡(reliable=false):黄灯横幅 + coverage 证据 + 逐行明细只读(不给决策按钮——
    // 建议值本体都不出了,行级裁决改不了「宁缺勿错」的降级结论,交互徒增噪声)。折叠仍吃
    // 真实 ui.open(覆盖降级形态常见大批量行,折叠开关必须真管用,不能摆设——真机曾踩过
    // 硬编码展开态、点了没反应的坑)。
    function degradeCardHtml(suggestion, ui) {
        var cov = suggestion.coverage || {};
        var grouped = groupRows(suggestion.rows);
        var message = localizedMessage(suggestion.message);
        return (
            '<div class="panel bxs-card"><div class="hd"><h3>' +
            esc(at('bxs_title')) +
            '</h3></div><div class="bd">' +
            '<div class="fc-banner w"><span class="chip w">' +
            esc(at('bxs_degrade_t')) +
            '</span><span>' +
            esc(
                message ||
                    at('bxs_degrade_s', {
                        breaks: cov.chain_breaks,
                        amount: money(cov.unexplained_inflow),
                        pct: root.AI.format.pct(cov.inflow_gap_ratio),
                    })
            ) +
            '</span></div>' +
            sectionsHtml(grouped, ui, readonlyRowHtml) +
            '</div></div>'
        );
    }

    // 可用卡(reliable=true):建议值三键摘要 + 交叉佐证 + 三区确认清单(可裁决)+
    // 让 AI 预判(仍有待确认行时)+ 采用建议值(全确认后才亮,派单契约 §「采用建议值」时机)。
    function reliableCardHtml(suggestion, ui, salesCrb, edcCrb) {
        var grouped = groupRows(suggestion.rows);
        var apply = canApply(suggestion);
        var chip = readinessChip(suggestion);
        var xrows = crossCheckRows(suggestion, salesCrb, edcCrb);
        var rowFn = function (r) {
            return rowHtml(r, ui);
        };
        return (
            '<div class="panel bxs-card"><div class="hd"><h3>' +
            esc(at('bxs_title')) +
            ' <span class="chip ' +
            chip.cls +
            '">' +
            esc(at(chip.key, chip.vars)) +
            '</span></h3></div><div class="bd">' +
            '<p class="bxs-sub">' +
            esc(
                at('bxs_counts_line', {
                    total: suggestion.counts.total,
                    sales: suggestion.counts.sales,
                    pending: suggestion.counts.pending,
                    nonsales: suggestion.counts.non_sales,
                })
            ) +
            '</p><div class="bxs-summary">' +
            summaryLine(at('bxs_gross_label'), money(suggestion.gross_total)) +
            summaryLine(at('field_sales_amount'), money(suggestion.sales_amount)) +
            summaryLine(at('field_output_vat'), money(suggestion.output_vat)) +
            '</div>' +
            crossCheckHtml(xrows) +
            sectionsHtml(grouped, ui, rowFn) +
            (grouped.pending.length ? runRowHtml(ui) : '') +
            (!apply && grouped.pending.length
                ? '<p class="bxs-gate-hint">' +
                  esc(at('bxs_pending_gate_hint', { n: grouped.pending.length })) +
                  '</p>'
                : '') +
            '<div class="bxs-actions"><button type="button" class="btn pri" data-action="bxs-apply"' +
            (apply ? '' : ' disabled') +
            '>' +
            esc(at('bxs_apply_btn')) +
            '</button></div>' +
            '</div></div>'
        );
    }

    // not_applicable(现金型客户,硬闸#3):不渲染倒推卡,只留一句四语提示,人工表单原样在下方。
    function notApplicableHtml() {
        return '<p class="bxs-hint">' + esc(at('bxs_not_applicable_hint')) + '</p>';
    }

    // suggestion 为 undefined/null = 闸关(order_detail 无此键)→ 不渲染任何东西,人工表单
    // 逐字节不变(硬闸#4)。三态分支顺序照派单书「实际契约」节:不适用 → 降级 → 可用。
    function cardHtml(suggestion, ui, salesCrb, edcCrb) {
        if (!suggestion) return '';
        if (suggestion.applicable === false) return notApplicableHtml();
        var uiState = ui || freshUiState();
        if (!suggestion.reliable) return degradeCardHtml(suggestion, uiState);
        return reliableCardHtml(suggestion, uiState, salesCrb, edcCrb);
    }

    root.AI = root.AI || {};
    root.AI.bankSalesRender = Object.assign({ cardHtml: cardHtml }, pure);
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
