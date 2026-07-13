/*
 * Pearnly AI · ai-payroll-annual-render.js · ภ.ง.ด.1ก 年度聚合面板纯逻辑 + HTML 拼装
 * (批次 H 收尾件)
 *
 * 拆自 ai-payroll-render.js(单文件 <500 行铁律 · 该文件已在预算线上)——月度进料工具卡
 * (H1b)的小扩:选好客户 + 佛历年度,聚合该年度所有已提交月度行(services/payroll/pnd1a.
 * aggregate_year)出 Σ支付/Σ预扣 + issues,再下载键入底稿 xlsx。与月度状态机互不依赖,
 * 独立四态面板由 ai-payroll.js 的 render() 常驻拼在页面末尾。
 *
 * 上传件(ใบแนบ/FORMAT กลาง 的 1ก 年报变体)未经官方样本核实,只给键入底稿一个下载
 * 入口(见 services/payroll/pnd1a.py 模块顶注「上传件降级」)——面板固定展示这层诚实
 * 说明,不留会计猜为什么少了两个按钮。
 *
 * 上半段(defaultTaxYear/isTaxYearValid)零 DOM/零 i18n 依赖,node 直接 require 断言;
 * 下半段 HTML 拼装依赖 at()/AI.state/AI.format/AI.payrollRender.issueRowHtml,只在浏览器
 * 根挂载——同 ai-payroll-render.js 的双段先例。排在 ai-payroll-render.js 之后、
 * ai-payroll.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function (root) {
    'use strict';

    // 佛历当年(4 位)——年度选择器默认值。
    function defaultTaxYear(now) {
        var d = now || new Date();
        return String(d.getFullYear() + 543);
    }

    function isTaxYearValid(taxYear) {
        return /^\d{4}$/.test(String(taxYear || ''));
    }

    var pure = { defaultTaxYear: defaultTaxYear, isTaxYearValid: isTaxYearValid };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.format,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }
    function money(v) {
        return v == null || v === '' ? '—' : root.AI.format.money(v);
    }

    function statRowHtml(labelKey, value) {
        return (
            '<div class="fc-stat-row"><span class="fc-stat-lb">' +
            esc(at(labelKey)) +
            '</span><span class="fc-stat-v">' +
            value +
            '</span></div>'
        );
    }

    function summaryHtml(ctx) {
        var s = ctx.annualSummary;
        var issuesHtml = s.issues.length
            ? s.issues.map(root.AI.payrollRender.issueRowHtml).join('')
            : '<div class="fc-clean">' + esc(at('fileconv_no_issues')) + '</div>';
        return (
            '<div class="pr-stats">' +
            statRowHtml('payroll_annual_stat_employees', esc(s.employee_count)) +
            statRowHtml('payroll_stat_paid', money(s.totals.paid_amount)) +
            statRowHtml('payroll_stat_wht', money(s.totals.wht_amount)) +
            '</div>' +
            issuesHtml +
            '<div class="pr-actions"><button type="button" class="btn" data-action="pr-annual-download"' +
            (ctx.annualDownloading ? ' disabled' : '') +
            '>' +
            esc(
                ctx.annualDownloading
                    ? at('payroll_downloading')
                    : at('payroll_download_annual_keying')
            ) +
            '</button></div>'
        );
    }

    // 四态:未生成(无 annualSummary,只有年度选择器)/ 生成中(annualLoading)/ 出错
    // (annualErrKey,含「该年无数据」404 与「年份格式不对」400)/ 已生成(汇总 + issues +
    // 下载)。
    function panelHtml(ctx) {
        var errHtml = ctx.annualErrKey
            ? '<div class="intake-err">' + esc(at(ctx.annualErrKey)) + '</div>'
            : '';
        var canRun = ctx.clientId && isTaxYearValid(ctx.annualYear) && !ctx.annualLoading;
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('payroll_annual_title')) +
            '</h3></div><div class="bd">' +
            '<div class="pr-payer-note">' +
            esc(at('payroll_annual_upload_note')) +
            '</div>' +
            '<div class="pr-setup-row"><label class="pr-lb">' +
            esc(at('payroll_annual_year_label')) +
            '<input id="prAnnualYearInput" type="text" placeholder="2569" maxlength="4" value="' +
            esc(ctx.annualYear || '') +
            '" /></label>' +
            '<button type="button" class="btn" data-action="pr-annual-summary"' +
            (canRun ? '' : ' disabled') +
            '>' +
            esc(ctx.annualLoading ? at('payroll_committing') : at('payroll_annual_run')) +
            '</button></div>' +
            errHtml +
            (ctx.annualSummary ? summaryHtml(ctx) : '') +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.payrollAnnualRender = Object.assign({ panelHtml: panelHtml }, pure);
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
