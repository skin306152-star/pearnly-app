/*
 * Pearnly AI · ai-intake-render.js · 收料视图(W4 补料流)的纯校验 + HTML 拼装
 *
 * 双导出(同 ai-format.js UMD 先例):浏览器挂 window.AI.intakeRender(HTML 拼装用 at()/
 * AI.state,离不开运行时),node 走 module.exports 只测无 DOM 依赖的纯校验(parseAmount /
 * buildSalesPayload / validateFiles)。真正的上传/表单/续跑编排在 ai-intake.js,那部分靠
 * DOM/fetch 时序,由 W4 E2E 守;这里把「填的数合不合法、文件超没超限」抽成可脱管单测的纯函数。
 */
(function (root) {
    'use strict';

    // 补料上限,与后端 workorder_routes 的 _MAX_MATERIAL_FILES / _MAX_MATERIAL_BYTES 对齐——
    // 前端先挡一道(省一次注定 413 的往返),后端仍是权威闸(错误码四语呈现同一份文案)。
    var MAX_FILES = 50;
    var MAX_BYTES = 20 * 1024 * 1024;

    // 金额串 → 规范化十进制串(非负,最多两位小数,去千分位)或 null。销项销售额/税额不应为负,
    // 故不认负号(与后端 _valid_amount 的非负约束同口径)。真正的 Decimal 换算在后端,前端只挡形。
    // 共享解析在 ai-format.js(同 ai-review-queue.js 的 parseVat 先例,两处曾各自写同一条正则)。
    function parseAmount(raw) {
        return root.AI.format.parseAmount(raw, false);
    }

    // 人工填销项表单 → POST /sales-summary 的 body。两个金额都合法才成;任一不合法返回 null,
    // 调用方据此就地报错、不发请求(同 buildDecisionPayload 先例)。note 原样带上(后端截长校验)。
    function buildSalesPayload(salesRaw, vatRaw, note) {
        var sales = parseAmount(salesRaw);
        var vat = parseAmount(vatRaw);
        if (sales === null || vat === null) return null;
        return { sales_amount: sales, output_vat: vat, note: String(note == null ? '' : note) };
    }

    // 上传前端预检:超文件数/超单文件字节 → 结构化错误 key(与后端 413 码映射同一份四语文案,
    // 不各拼一套)。全通过返回 {ok:true}。
    function validateFiles(files) {
        var list = files || [];
        if (list.length > MAX_FILES) return { ok: false, errKey: 'err_workorder_too_many_files' };
        for (var i = 0; i < list.length; i++) {
            if (list[i] && list[i].size > MAX_BYTES) {
                return { ok: false, errKey: 'err_workorder_file_too_large' };
            }
        }
        return { ok: true };
    }

    var pure = {
        MAX_FILES: MAX_FILES,
        MAX_BYTES: MAX_BYTES,
        parseAmount: parseAmount,
        buildSalesPayload: buildSalesPayload,
        validateFiles: validateFiles,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }
    function svg(inner) {
        return '<svg viewBox="0 0 24 24" fill="none" stroke-width="2">' + inner + '</svg>';
    }

    // 拖拽/点选上传区。四态:idle(空)/ 已选文件 / 上传中 / 刚传完(引导重新跑)。
    function dropzoneHtml(ctx) {
        var n = ctx.files.length;
        var errRow = ctx.uploadErrKey
            ? '<div class="intake-err" id="ikUploadErr">' + esc(at(ctx.uploadErrKey)) + '</div>'
            : '';
        var inner;
        if (ctx.uploading) {
            inner =
                '<div class="dz-inner"><div class="dz-ic">' +
                svg('<path d="M21 12a9 9 0 1 1-6.2-8.5"/>') +
                '</div><div class="dz-t">' +
                esc(at('intake_uploading')) +
                '</div></div>';
        } else if (n > 0) {
            var chips = '';
            for (var i = 0; i < Math.min(n, 60); i++) chips += '<span class="fchip"></span>';
            inner =
                '<div class="dz-filled"><div class="dz-count"><b>' +
                n +
                '</b> ' +
                esc(at('intake_files_ready')) +
                '</div><div class="file-strip">' +
                chips +
                '</div><div class="dz-btns">' +
                '<button class="btn pri" data-action="ik-upload">' +
                esc(at('intake_start')) +
                '</button>' +
                '<button class="btn" data-action="ik-clear-files">' +
                esc(at('intake_clear')) +
                '</button></div></div>';
        } else {
            inner =
                '<div class="dz-inner"><div class="dz-ic">' +
                svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>') +
                '</div><div class="dz-t">' +
                esc(at('intake_drop_t')) +
                '</div><div class="dz-s">' +
                esc(at('intake_drop_s')) +
                '</div><button class="btn" data-action="ik-pick">' +
                esc(at('intake_pick')) +
                '</button></div>';
        }
        return (
            '<div class="dropzone" id="ikDrop" tabindex="0" role="button" aria-label="' +
            esc(at('intake_drop_t')) +
            '">' +
            inner +
            '</div>' +
            errRow
        );
    }

    // 其它进料口:状态诚实(M1 §5 降级表)——LINE / 专属邮箱未开通,数字源直读仅 xlsx 可用。
    function channelsHtml() {
        function row(icClass, icSvg, title, sub, chipCls, chipKey) {
            return (
                '<div class="chan"><div class="chan-ic ' +
                icClass +
                '">' +
                icSvg +
                '</div><div class="chan-tx"><b>' +
                esc(title) +
                '</b><small>' +
                esc(sub) +
                '</small></div><span class="chip ' +
                chipCls +
                '">' +
                esc(at(chipKey)) +
                '</span></div>'
            );
        }
        return (
            '<div class="chan-list"><div class="chan-h">' +
            esc(at('intake_chan_h')) +
            '</div>' +
            row(
                'line',
                'L',
                at('intake_chan_line_t'),
                at('intake_chan_line_s'),
                'n',
                'intake_status_off'
            ) +
            row(
                '',
                svg('<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>'),
                at('intake_chan_mail_t'),
                at('intake_chan_mail_s'),
                'n',
                'intake_status_off'
            ) +
            row(
                '',
                svg('<path d="M3 3v18h18M7 14l4-4 4 4 5-5"/>'),
                at('intake_chan_digital_t'),
                at('intake_chan_digital_s'),
                'w',
                'intake_status_xlsx'
            ) +
            '<div class="chan-note">' +
            esc(at('intake_chan_note')) +
            '</div></div>'
        );
    }

    // 人工填销项表单(缺 sales_summary 时的第二条路)。两个金额 + 凭据备注,Enter 提交 Esc 取消。
    function salesFormHtml(ctx) {
        var errRow = ctx.formErr
            ? '<div class="intake-err" id="ikFormErr">' + esc(at('intake_form_invalid')) + '</div>'
            : '';
        var submitLabel = ctx.submitting ? at('intake_form_submitting') : at('intake_form_submit');
        return (
            '<form class="sales-form" id="ikSalesForm" novalidate>' +
            '<div class="sf-row"><label class="sf-lb" for="ikSales">' +
            esc(at('field_sales_amount')) +
            '</label>' +
            '<input class="sf-in num" id="ikSales" inputmode="decimal" autocomplete="off" value="' +
            esc(ctx.salesValue || '') +
            '"></div>' +
            '<div class="sf-row"><label class="sf-lb" for="ikVat">' +
            esc(at('field_output_vat')) +
            '</label>' +
            '<input class="sf-in num" id="ikVat" inputmode="decimal" autocomplete="off" value="' +
            esc(ctx.vatValue || '') +
            '"></div>' +
            '<div class="sf-row"><label class="sf-lb" for="ikNote">' +
            esc(at('intake_form_note')) +
            '</label>' +
            '<input class="sf-in" id="ikNote" maxlength="500" placeholder="' +
            esc(at('intake_form_note_ph')) +
            '" value="' +
            esc(ctx.noteValue || '') +
            '"></div>' +
            errRow +
            '<div class="sf-hint">' +
            esc(at('intake_form_hint')) +
            '</div>' +
            '<div class="sf-btns">' +
            '<button type="submit" class="btn pri"' +
            (ctx.submitting ? ' disabled' : '') +
            ' data-action="ik-form-submit">' +
            esc(submitLabel) +
            '</button>' +
            '<button type="button" class="btn" data-action="ik-form-cancel">' +
            esc(at('intake_form_cancel')) +
            '</button></div></form>'
        );
    }

    // 缺 sales_summary 的补料卡:两条路(上传 POS 导出 / 人工填销项)。formOpen 时展开表单。
    function needsCardHtml(ctx) {
        var body = ctx.formOpen
            ? salesFormHtml(ctx)
            : '<div class="needs-paths">' +
              '<button class="btn" data-action="ik-goto-upload">' +
              esc(at('intake_path_upload')) +
              '</button>' +
              '<button class="btn pri" data-action="ik-open-form">' +
              esc(at('intake_path_manual')) +
              '</button></div>';
        return (
            '<div class="panel needs-card"><div class="hd"><h3>' +
            esc(at('intake_needs_t')) +
            ' <span class="chip w">' +
            esc(at('chip_needs_materials')) +
            '</span></h3></div>' +
            '<div class="bd"><p class="needs-sub">' +
            esc(at('intake_needs_s')) +
            '</p>' +
            body +
            '</div></div>'
        );
    }

    // 补料后「重新跑」面(idle → 按钮;waiting → 禁用转述;错 → 人话 + 重试)。
    function rerunHtml(ctx) {
        if (!ctx.dirty && ctx.rerunState !== 'waiting') return '';
        var inner;
        if (ctx.rerunState === 'waiting') {
            inner =
                '<button class="btn pri" disabled>' + esc(at('intake_rerun_waiting')) + '</button>';
        } else {
            inner =
                '<button class="btn pri" data-action="ik-rerun">' +
                esc(at('intake_rerun')) +
                '</button>';
        }
        var err = ctx.rerunErrKey
            ? '<p class="intake-err">' + esc(at(ctx.rerunErrKey)) + '</p>'
            : '';
        return (
            '<div class="panel rerun-card"><div class="bd rerun-body">' +
            '<p>' +
            esc(at('intake_rerun_hint')) +
            '</p>' +
            err +
            inner +
            '</div></div>'
        );
    }

    // 收料主视图。needsSales 时补料卡置顶;上传区 + 进料口并列;末尾重新跑面。
    function intakeHtml(ctx) {
        var needs = ctx.needsSales ? needsCardHtml(ctx) : '';
        return (
            '<div class="intake-body">' +
            '<p class="intake-lead">' +
            esc(at('intake_lead')) +
            '</p>' +
            needs +
            '<div class="intake-grid">' +
            dropzoneHtml(ctx) +
            channelsHtml() +
            '</div>' +
            rerunHtml(ctx) +
            '</div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.intakeRender = {
        MAX_FILES: MAX_FILES,
        MAX_BYTES: MAX_BYTES,
        parseAmount: parseAmount,
        buildSalesPayload: buildSalesPayload,
        validateFiles: validateFiles,
        intakeHtml: intakeHtml,
        dropzoneHtml: dropzoneHtml,
        needsCardHtml: needsCardHtml,
        rerunHtml: rerunHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
