/*
 * Pearnly AI · ai-vatcheck-render.js · N1 销项税报告三查纯逻辑 + HTML 拼装
 *
 * 上半段(padWidth/compressRanges/formatNumberRanges/familyHasIssues/allClear/
 * validateFile)零 DOM/零 i18n 依赖,node(tests/unit/test_ai_vatcheck_pure.py)
 * 直接 require 断言;下半段 HTML 拼装依赖 at()/AI.state/AI.format,只在浏览器根
 * 挂载——同 ai-recon-render.js 的双段先例。真正的挂载/上传/网络调用在
 * ai-vatcheck.js,排在本文件之后加载。
 *
 * 数据源:POST /api/vat_report_checks/run 的响应(services/vat/vat_report_checks.py
 * ::run_report_checks 经 to_jsonable 出线),本文件只读不改其形状,三查算法(缺号/
 * 乱序/买家聚合/期间)一行不碰——纯只读渲染。
 */
(function (root) {
    'use strict';

    // 数字连号族的补零宽度:取家族内 invoice_numbers 尾号位数的众数(同后端
    // _modal_length 的取舍逻辑),显示缺号/重复号时贴回原票面位数(00520 而非 520)。
    function padWidth(family) {
        var lens = {};
        (family.invoice_numbers || []).forEach(function (s) {
            var m = /(\d+)$/.exec(String(s || ''));
            if (m) lens[m[1].length] = (lens[m[1].length] || 0) + 1;
        });
        var best = 0;
        var bestCount = -1;
        Object.keys(lens).forEach(function (k) {
            if (lens[k] > bestCount) {
                bestCount = lens[k];
                best = Number(k);
            }
        });
        return best;
    }

    function padNum(n, width) {
        var s = String(n);
        while (s.length < width) s = '0' + s;
        return s;
    }

    // 连续整数压成区间(缺号/重复号常常成串,压完再展示才不会甩一屏裸数字出来。
    function compressRanges(nums) {
        var sorted = (nums || []).slice().sort(function (a, b) {
            return a - b;
        });
        var ranges = [];
        var i = 0;
        while (i < sorted.length) {
            var start = sorted[i];
            var end = start;
            while (i + 1 < sorted.length && sorted[i + 1] === end + 1) {
                end = sorted[i + 1];
                i++;
            }
            ranges.push([start, end]);
            i++;
        }
        return ranges;
    }

    function formatNumberRanges(nums, width) {
        return compressRanges(nums)
            .map(function (r) {
                var a = padNum(r[0], width);
                var b = padNum(r[1], width);
                return r[0] === r[1] ? a : a + '-' + b;
            })
            .join(', ');
    }

    // 一个号型族只要缺号/乱序/重复/格式笔误任一非空即算"有事要看"(作废票不算——
    // 那是中性提示,单独一张清单,见方案拍板 2)。
    function familyHasIssues(fam) {
        fam = fam || {};
        var missing = (fam.missing || fam.missing_days || []).length > 0;
        var dup = (fam.duplicates || fam.duplicate_days || []).length > 0;
        var ooo = (fam.out_of_order || []).length > 0;
        var fmt = (fam.format_anomalies || []).length > 0;
        return missing || dup || ooo || fmt;
    }

    // 三查全绿的判定:所有号型族都干净 + 无期间异常(顶层横幅用)。
    function allClear(result) {
        result = result || {};
        var families = (result.sequence || {}).families || [];
        var noFamilyIssue = !families.some(familyHasIssues);
        var noOutOfPeriod = !((result.period || {}).out_of_period || []).length;
        return noFamilyIssue && noOutOfPeriod;
    }

    var ALLOWED_EXT = /\.(pdf|xlsx|xls|jpe?g|png)$/i;

    function validateFile(file) {
        if (!file) return { ok: false, errKey: 'vatcheck_err_no_file' };
        if (!ALLOWED_EXT.test(file.name || '')) {
            return { ok: false, errKey: 'vatcheck_err_bad_type' };
        }
        return { ok: true };
    }

    var pure = {
        padWidth: padWidth,
        compressRanges: compressRanges,
        formatNumberRanges: formatNumberRanges,
        familyHasIssues: familyHasIssues,
        allClear: allClear,
        validateFile: validateFile,
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
                '<button type="button" class="btn pri" data-action="vc-run"' +
                (ctx.running ? ' disabled' : '') +
                '>' +
                esc(ctx.running ? at('vatcheck_running') : at('vatcheck_run')) +
                '</button>' +
                '<button type="button" class="btn" data-action="vc-clear-file"' +
                (ctx.running ? ' disabled' : '') +
                '>' +
                esc(at('intake_clear')) +
                '</button></div></div>';
        } else {
            body =
                '<div class="dz-inner" data-action="vc-goto-upload">' +
                '<div class="dz-ic">' +
                UPLOAD_ICON +
                '</div><div class="dz-t">' +
                esc(at('vatcheck_drop_t')) +
                '</div><div class="dz-s">' +
                esc(at('vatcheck_drop_s')) +
                '</div><button type="button" class="btn" data-action="vc-pick">' +
                esc(at('intake_pick')) +
                '</button></div>';
        }
        return '<div class="dropzone" id="vcDrop" tabindex="0">' + body + '</div>' + errHtml;
    }

    function issueLineHtml(labelKey, text) {
        return (
            '<div class="vc-issue"><span class="chip w">' +
            esc(at(labelKey)) +
            '</span><span class="vc-issue-list">' +
            esc(text) +
            '</span></div>'
        );
    }

    function familyBlockHtml(fam) {
        var isDate = fam.type === 'date_coded';
        var width = isDate ? 0 : padWidth(fam);
        var missingNums = (isDate ? fam.missing_days : fam.missing) || [];
        var dupNums = (isDate ? fam.duplicate_days : fam.duplicates) || [];
        var oooList = fam.out_of_order || [];
        var fmtList = fam.format_anomalies || [];
        var issues = [];
        if (missingNums.length) {
            issues.push(
                issueLineHtml(
                    isDate ? 'vatcheck_flag_missing_days' : 'vatcheck_flag_missing',
                    formatNumberRanges(missingNums, width)
                )
            );
        }
        if (oooList.length) {
            issues.push(issueLineHtml('vatcheck_flag_out_of_order', oooList.join(', ')));
        }
        if (dupNums.length) {
            issues.push(
                issueLineHtml(
                    isDate ? 'vatcheck_flag_dup_days' : 'vatcheck_flag_dup',
                    formatNumberRanges(dupNums, width)
                )
            );
        }
        if (fmtList.length) {
            issues.push(issueLineHtml('vatcheck_flag_format', fmtList.join(', ')));
        }
        var bodyHtml = issues.length
            ? issues.join('')
            : '<div class="vc-clean">' + esc(at('vatcheck_family_clean')) + '</div>';
        var headChip = issues.length
            ? '<span class="chip w">' + issues.length + '</span>'
            : '<span class="chip g">' + esc(at('vatcheck_ok_short')) + '</span>';
        return (
            '<div class="vc-family"><div class="vc-family-hd"><b>' +
            esc(fam.label) +
            '</b><span class="note">' +
            esc(at('vatcheck_family_count', { n: fam.count })) +
            '</span>' +
            headChip +
            '</div>' +
            bodyHtml +
            '</div>'
        );
    }

    function voidListHtml(voidInvoices) {
        if (!voidInvoices || !voidInvoices.length) return '';
        var rows = voidInvoices
            .map(function (v) {
                return (
                    '<div class="vc-void-row">' +
                    esc(v.invoice_no || '—') +
                    (v.date ? ' · ' + esc(v.date) : '') +
                    '</div>'
                );
            })
            .join('');
        return (
            '<div class="vc-void"><div class="vc-void-hd">' +
            '<span class="chip n">' +
            esc(at('vatcheck_void_title', { n: voidInvoices.length })) +
            '</span><span class="note">' +
            esc(at('vatcheck_void_note')) +
            '</span></div>' +
            rows +
            '</div>'
        );
    }

    function buyerRowHtml(b) {
        return (
            '<tr><td>' +
            esc(b.buyer_name || '—') +
            '</td><td>' +
            esc(b.tax_id || '—') +
            '</td><td class="num">' +
            b.invoice_count +
            '</td><td class="num">' +
            money(b.net_total) +
            '</td><td class="num">' +
            money(b.vat_total) +
            '</td></tr>'
        );
    }

    function buyerTableHtml(buyerSummary) {
        var buyers = (buyerSummary || {}).buyers || [];
        var grand = (buyerSummary || {}).grand_total || {};
        if (!buyers.length) {
            return '<p class="vc-empty">' + esc(at('vatcheck_buyers_empty')) + '</p>';
        }
        return (
            '<div class="mx-scroll"><table class="mx-table"><thead><tr><th>' +
            esc(at('vatcheck_col_buyer')) +
            '</th><th>' +
            esc(at('vatcheck_col_tax_id')) +
            '</th><th>' +
            esc(at('vatcheck_col_count')) +
            '</th><th>' +
            esc(at('vatcheck_col_net')) +
            '</th><th>' +
            esc(at('vatcheck_col_vat')) +
            '</th></tr></thead><tbody>' +
            buyers.map(buyerRowHtml).join('') +
            '<tr class="vc-grand"><td>' +
            esc(at('vatcheck_grand_total')) +
            '</td><td>—</td><td class="num">' +
            (grand.invoice_count || 0) +
            '</td><td class="num">' +
            money(grand.net_total) +
            '</td><td class="num">' +
            money(grand.vat_total) +
            '</td></tr></tbody></table></div>'
        );
    }

    function periodLabel(period) {
        period = period || {};
        if (!period.period_year || !period.period_month) return '—';
        return (
            period.period_year + '-' + (period.period_month < 10 ? '0' : '') + period.period_month
        );
    }

    function periodBlockHtml(period) {
        period = period || {};
        var rows = period.out_of_period || [];
        if (!rows.length) {
            return (
                '<div class="vc-clean">' +
                esc(at('vatcheck_period_clean', { period: periodLabel(period) })) +
                '</div>'
            );
        }
        return (
            '<div class="vc-period-rows">' +
            rows
                .map(function (r) {
                    return issueLineHtml(
                        'vatcheck_flag_out_of_period',
                        (r.invoice_no || '—') + ' · ' + (r.date || '—')
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function bannerHtml(result) {
        return allClear(result)
            ? '<div class="vc-banner g"><span class="chip g">' +
                  esc(at('vatcheck_all_clear_chip')) +
                  '</span><span>' +
                  esc(at('vatcheck_all_clear_s')) +
                  '</span></div>'
            : '<div class="vc-banner w"><span class="chip w">' +
                  esc(at('vatcheck_has_issues_chip')) +
                  '</span><span>' +
                  esc(at('vatcheck_has_issues_s')) +
                  '</span></div>';
    }

    function resultsHtml(result) {
        result = result || {};
        var seq = result.sequence || {};
        var families = seq.families || [];
        var familiesHtml = families.length
            ? families.map(familyBlockHtml).join('')
            : '<p class="vc-empty">' + esc(at('vatcheck_no_families')) + '</p>';
        return (
            bannerHtml(result) +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('vatcheck_sequence_title')) +
            '</h3></div><div class="bd">' +
            familiesHtml +
            voidListHtml(seq.void_invoices) +
            '</div></div>' +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('vatcheck_buyers_title')) +
            '</h3></div><div class="bd">' +
            buyerTableHtml(result.buyer_summary) +
            '</div></div>' +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('vatcheck_period_title')) +
            '</h3><span class="note">' +
            esc(at('vatcheck_period_note', { period: periodLabel(result.period) })) +
            '</span></div><div class="bd">' +
            periodBlockHtml(result.period) +
            '</div></div>'
        );
    }

    // ctx: {file, running, errKey, result}——四态:未上传(无 file/result)/ 运行中(running)/
    // 出错(errKey,骨架已收起)/ 有结果(result)。骨架屏(running)与上传区共存,不整块替换掉
    // 已选文件名(用户能看见自己选的是哪份)。
    function pageHtml(ctx) {
        ctx = ctx || {};
        var zone = uploadZoneHtml(ctx);
        if (ctx.running) return zone + root.AI.state.loadingHtml();
        if (!ctx.result) return zone;
        return (
            '<div class="vc-done-bar"><span>' +
            esc(at('vatcheck_uploaded', { name: ctx.file ? ctx.file.name : '' })) +
            '</span><button type="button" class="btn sm" data-action="vc-reset">' +
            esc(at('vatcheck_reset')) +
            '</button></div>' +
            resultsHtml(ctx.result)
        );
    }

    root.AI = root.AI || {};
    root.AI.vatcheckRender = {
        padWidth: padWidth,
        compressRanges: compressRanges,
        formatNumberRanges: formatNumberRanges,
        familyHasIssues: familyHasIssues,
        allClear: allClear,
        validateFile: validateFile,
        pageHtml: pageHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
