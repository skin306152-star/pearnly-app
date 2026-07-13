/*
 * Pearnly AI · ai-fileconv-render.js · K1b 财务文件转换纯逻辑 + HTML 拼装
 *
 * 引擎 K1a(services/fileconv/)PDF→结构化结果的产品化外壳:上传单份 PDF,后端跑
 * convert_pdf 直接回 JSON 摘要(doc_type/status/conserved/stats/issues 前 N 条+总数,
 * 见 routes/fileconv_routes.py)。守恒校验(GL 余额链/银行跑余额/报表合计)全过才敢
 * 显示「可信」大字,有一条不平也逐行点名行号+期望+实际——转换工具不因为"只是导出"
 * 就打折四态诚实。
 *
 * 上半段(validateFile/docTypeKey/issueKindKey)零 DOM/零 i18n 依赖,node
 * (tests/unit/test_ai_fileconv_pure.py)直接 require 断言;下半段 HTML 拼装依赖
 * at()/AI.state/AI.format,只在浏览器根挂载——同 ai-vatcheck-render.js 的双段先例。
 */
(function (root) {
    'use strict';

    // 带文字层 PDF 走纯函数路;扫描件 PDF/图片(jpg/png/webp)走 OCR 路(K1c)。客户端先挡
    // 明显打错的文件类型,省一趟网络往返。
    var ALLOWED_EXT = /\.(pdf|jpe?g|png|webp)$/i;
    var IMAGE_EXT = /\.(jpe?g|png|webp)$/i;

    function validateFile(file) {
        if (!file) return { ok: false, errKey: 'fileconv_err_no_file' };
        if (!ALLOWED_EXT.test(file.name || '')) {
            return { ok: false, errKey: 'fileconv_err_bad_type' };
        }
        return { ok: true };
    }

    function isImageFile(file) {
        return !!file && IMAGE_EXT.test(file.name || '');
    }

    // doc_type(services/fileconv/model.py 四枚举)→ i18n key。未来引擎加新类型忘同步
    // 前端时原样兜底成 generic 文案,不显示原始英文常量吓用户。
    var DOC_TYPE_KEYS = {
        gl_ledger: 'fileconv_doctype_gl_ledger',
        bank_statement: 'fileconv_doctype_bank_statement',
        vat_report: 'fileconv_doctype_vat_report',
        generic_table: 'fileconv_doctype_generic_table',
    };

    function docTypeKey(docType) {
        return DOC_TYPE_KEYS[docType] || 'fileconv_doctype_generic_table';
    }

    // issue.kind(services/fileconv/model.py 守恒校验 + OCR 独立锚)→ i18n key,逐行点名用。
    var ISSUE_KIND_KEYS = {
        gl_balance_chain: 'fileconv_issue_gl_balance_chain',
        running_balance: 'fileconv_issue_running_balance',
        footer_total: 'fileconv_issue_footer_total',
        closing_anchor: 'fileconv_issue_closing_anchor',
    };

    function issueKindKey(kind) {
        return ISSUE_KIND_KEYS[kind] || kind;
    }

    // OCR 读不全/够不到模型 = 结构化拒绝(services/fileconv/model.py),与无文字层同属拒绝态:
    // 横幅走「拒绝」样式,绝不显示「可信」大字。
    var REJECT_STATUSES = {
        no_text_layer: 'fileconv_no_text_layer',
        ocr_incomplete: 'fileconv_ocr_incomplete',
        ocr_unavailable: 'fileconv_ocr_unavailable',
    };

    function isRejected(status) {
        return Object.prototype.hasOwnProperty.call(REJECT_STATUSES, status);
    }

    var pure = {
        validateFile: validateFile,
        isImageFile: isImageFile,
        docTypeKey: docTypeKey,
        issueKindKey: issueKindKey,
        isRejected: isRejected,
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

    var UPLOAD_ICON =
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="2">' +
        '<path d="M12 3v12m0 0 4-4m-4 4-4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>';

    function uploadZoneHtml(ctx) {
        var errHtml = ctx.errKey ? '<div class="intake-err">' + esc(at(ctx.errKey)) + '</div>' : '';
        var body;
        if (ctx.file) {
            body =
                '<div class="dz-filled"><div class="dz-count">' +
                esc(ctx.file.name) +
                '</div><div class="dz-btns">' +
                '<button type="button" class="btn pri" data-action="fc-run"' +
                (ctx.running ? ' disabled' : '') +
                '>' +
                esc(ctx.running ? at('fileconv_running') : at('fileconv_run')) +
                '</button>' +
                '<button type="button" class="btn" data-action="fc-clear-file"' +
                (ctx.running ? ' disabled' : '') +
                '>' +
                esc(at('intake_clear')) +
                '</button></div></div>';
        } else {
            body =
                '<div class="dz-inner" data-action="fc-goto-upload">' +
                '<div class="dz-ic">' +
                UPLOAD_ICON +
                '</div><div class="dz-t">' +
                esc(at('fileconv_drop_t')) +
                '</div><div class="dz-s">' +
                esc(at('fileconv_drop_s')) +
                '</div><button type="button" class="btn" data-action="fc-pick">' +
                esc(at('intake_pick')) +
                '</button></div>';
        }
        return '<div class="dropzone" id="fcDrop" tabindex="0">' + body + '</div>' + errHtml;
    }

    function statRowHtml(label, value) {
        return (
            '<div class="fc-stat-row"><span class="fc-stat-lb">' +
            esc(label) +
            '</span><span class="fc-stat-v">' +
            esc(value) +
            '</span></div>'
        );
    }

    // stats 形状随 doc_type 而变(services/fileconv/validate.py::ledger_stats/tabular_stats)
    // ——只挑双方共有且用户看得懂的字段展示,科目全名列表压成计数(不适合摘要卡)。
    function statsHtml(stats) {
        stats = stats || {};
        var rows = [];
        if (stats.row_count != null) {
            rows.push(statRowHtml(at('fileconv_stat_rows'), stats.row_count));
        }
        if (Array.isArray(stats.accounts)) {
            rows.push(statRowHtml(at('fileconv_stat_accounts'), stats.accounts.length));
        }
        if (stats.opening_balance != null) {
            rows.push(statRowHtml(at('fileconv_stat_opening'), money(stats.opening_balance)));
        }
        if (stats.closing_balance != null) {
            rows.push(statRowHtml(at('fileconv_stat_closing'), money(stats.closing_balance)));
        }
        if (stats.sum_debit != null) {
            rows.push(statRowHtml(at('fileconv_stat_debit'), money(stats.sum_debit)));
        }
        if (stats.sum_credit != null) {
            rows.push(statRowHtml(at('fileconv_stat_credit'), money(stats.sum_credit)));
        }
        if (stats.total_found != null) {
            rows.push(
                statRowHtml(
                    at('fileconv_stat_total_found'),
                    at(stats.total_found ? 'fileconv_yes' : 'fileconv_no')
                )
            );
        }
        return rows.length ? '<div class="fc-stats">' + rows.join('') + '</div>' : '';
    }

    function issueRowHtml(issue) {
        return (
            '<div class="fc-issue"><span class="chip w">' +
            esc(at(issueKindKey(issue.kind))) +
            '</span><span class="fc-issue-body"><b>#' +
            esc(issue.line_no) +
            '</b> ' +
            (issue.account ? esc(issue.account) + ' · ' : '') +
            esc(issue.message) +
            '<span class="fc-issue-diff">' +
            esc(at('fileconv_expected', { v: issue.expected })) +
            ' / ' +
            esc(at('fileconv_actual', { v: issue.actual })) +
            '</span></span></div>'
        );
    }

    function bannerHtml(result) {
        if (isRejected(result.status)) {
            var base = REJECT_STATUSES[result.status];
            return (
                '<div class="fc-banner n"><span class="chip n">' +
                esc(at(base + '_chip')) +
                '</span><span>' +
                esc(at(base + '_s')) +
                '</span></div>'
            );
        }
        return result.conserved
            ? '<div class="fc-banner g"><span class="chip g">' +
                  esc(at('fileconv_conserved_chip')) +
                  '</span><span>' +
                  esc(at('fileconv_conserved_s')) +
                  '</span></div>'
            : '<div class="fc-banner w"><span class="chip w">' +
                  esc(at('fileconv_has_issues_chip')) +
                  '</span><span>' +
                  esc(at('fileconv_has_issues_s', { n: result.issue_count })) +
                  '</span></div>';
    }

    function resultsHtml(result, downloading) {
        result = result || {};
        if (isRejected(result.status)) {
            return bannerHtml(result);
        }
        var issues = result.issues || [];
        var issuesHtml = issues.map(issueRowHtml).join('');
        if (result.issue_count > issues.length) {
            issuesHtml +=
                '<div class="fc-issue-more">' +
                esc(at('fileconv_issues_more', { n: result.issue_count - issues.length })) +
                '</div>';
        }
        var downloadBtn =
            '<button type="button" class="btn pri" data-action="fc-download"' +
            (downloading ? ' disabled' : '') +
            '>' +
            esc(downloading ? at('fileconv_downloading') : at('fileconv_download')) +
            '</button>';
        return (
            bannerHtml(result) +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at(docTypeKey(result.doc_type))) +
            '</h3></div><div class="bd">' +
            statsHtml(result.stats) +
            '</div></div>' +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('fileconv_issues_title')) +
            '</h3></div><div class="bd">' +
            (issuesHtml || '<div class="fc-clean">' + esc(at('fileconv_no_issues')) + '</div>') +
            '</div></div>' +
            '<div class="fc-actions">' +
            downloadBtn +
            '</div>'
        );
    }

    // ctx: {file, running, downloading, errKey, result}——四态:未上传(无 file/result)/
    // 运行中(running)/出错(errKey,骨架已收起)/有结果(result)。骨架屏与上传区共存,
    // 不整块替换掉已选文件名(用户能看见自己选的是哪份),同 ai-vatcheck-render.js 先例。
    function pageHtml(ctx) {
        ctx = ctx || {};
        var zone = uploadZoneHtml(ctx);
        if (ctx.running) {
            // OCR(图片/扫描件)比文字层慢一个量级,加载态诚实标「识别中」不让用户以为卡死。
            var note = isImageFile(ctx.file)
                ? '<div class="fc-ocr-note">' + esc(at('fileconv_ocr_running')) + '</div>'
                : '';
            return zone + note + root.AI.state.loadingHtml();
        }
        if (!ctx.result) return zone;
        return (
            '<div class="fc-done-bar"><span>' +
            esc(at('fileconv_uploaded', { name: ctx.file ? ctx.file.name : '' })) +
            '</span><button type="button" class="btn sm" data-action="fc-reset">' +
            esc(at('fileconv_reset')) +
            '</button></div>' +
            resultsHtml(ctx.result, ctx.downloading)
        );
    }

    root.AI = root.AI || {};
    root.AI.fileconvRender = {
        validateFile: validateFile,
        isImageFile: isImageFile,
        docTypeKey: docTypeKey,
        issueKindKey: issueKindKey,
        isRejected: isRejected,
        pageHtml: pageHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
