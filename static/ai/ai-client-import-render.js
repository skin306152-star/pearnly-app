/*
 * Pearnly AI · ai-client-import-render.js · IN-0d 客户名录批量导入纯逻辑 + HTML 拼装
 *
 * 上半段(validateFile/chipClassForStatus/errKeyFor/previewCounts/resultCounts)零 DOM/
 * 零 i18n 依赖,node(tests/unit/test_ai_client_import_pure.py)直接 require 断言;下半段
 * HTML 拼装依赖 at()/AI.state.esc,只在浏览器根挂载(同 ai-vatcheck-render.js 的双段
 * 先例,guard 只判 root 是否存在,不判 root.document——node 里 root=globalThis 也是
 * truthy,配合测试里 stub 的 global.at/global.AI.state.esc 可直接跑)。
 *
 * 三态 chip:valid/created → g(绿);skip → n(中性灰,税号已存在);error → b(红,缺 name/
 * 税号格式错/泰文名闸/pos_only 一号一店闸)——沿用 ai-shell.css 既有 .chip.g/.n/.b 令牌
 * 类,不新增 CSS。真正的挂载/上传/网络调用在 ai-client-import.js,排在本文件之后加载。
 */
(function (root) {
    'use strict';

    var ALLOWED_EXT = /\.(xlsx|xls|csv)$/i;

    function validateFile(file) {
        if (!file) return { ok: false, errKey: 'client_import_err_no_file' };
        if (!ALLOWED_EXT.test(file.name || '')) {
            return { ok: false, errKey: 'client_import_err_bad_type' };
        }
        return { ok: true };
    }

    // valid(预览将建)/created(已建)同归绿;skip 中性;error 红。未知状态兜底中性,不假装成功。
    function chipClassForStatus(status) {
        if (status === 'valid' || status === 'created') return 'g';
        if (status === 'skip') return 'n';
        if (status === 'error') return 'b';
        return 'n';
    }

    // 错误码 → i18n key 的确定性映射。与 ai-api.js::mapApiErrorKey 同一条公式,独立实现
    // (同 ai-client-new.js::mod11Check 顶注先例:两处各自实现同一算法,不为省一行耦合
    // 模块加载顺序)。
    function errKeyFor(code) {
        if (!code) return 'err_generic';
        return 'err_' + String(code).replace(/\./g, '_');
    }

    function previewCounts(preview) {
        var rows = preview || [];
        return {
            total: rows.length,
            valid: rows.filter(function (r) {
                return r.status === 'valid';
            }).length,
            skip: rows.filter(function (r) {
                return r.status === 'skip';
            }).length,
            error: rows.filter(function (r) {
                return r.status === 'error';
            }).length,
        };
    }

    function resultCounts(results) {
        var rows = results || [];
        return {
            total: rows.length,
            created: rows.filter(function (r) {
                return r.status === 'created';
            }).length,
            skip: rows.filter(function (r) {
                return r.status === 'skip';
            }).length,
            error: rows.filter(function (r) {
                return r.status === 'error';
            }).length,
        };
    }

    var pure = {
        validateFile: validateFile,
        chipClassForStatus: chipClassForStatus,
        errKeyFor: errKeyFor,
        previewCounts: previewCounts,
        resultCounts: resultCounts,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为 HTML 拼装(依赖 at()/AI.state.esc,guard 只判 root)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    var UPLOAD_ICON =
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="2">' +
        '<path d="M12 3v12m0 0 4-4m-4 4-4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>';

    function fileZoneHtml(ctx) {
        var errHtml = ctx.errKey ? '<div class="intake-err">' + esc(at(ctx.errKey)) + '</div>' : '';
        var body;
        if (ctx.file) {
            body =
                '<div class="dz-filled"><div class="dz-count">' +
                esc(ctx.file.name) +
                '</div><div class="dz-btns">' +
                '<button type="button" class="btn" data-action="ci-clear-file"' +
                (ctx.parsing ? ' disabled' : '') +
                '>' +
                esc(at('intake_clear')) +
                '</button></div></div>';
        } else {
            body =
                '<div class="dz-inner" data-action="ci-goto-upload">' +
                '<div class="dz-ic">' +
                UPLOAD_ICON +
                '</div><div class="dz-t">' +
                esc(at('client_import_drop_t')) +
                '</div><div class="dz-s">' +
                esc(at('client_import_drop_s')) +
                '</div><button type="button" class="btn" data-action="ci-pick">' +
                esc(at('intake_pick')) +
                '</button></div>';
        }
        return '<div class="dropzone" id="ciDrop" tabindex="0">' + body + '</div>' + errHtml;
    }

    function countsChipsHtml(primaryN, counts, labels) {
        var chips = ['<span class="chip g">' + esc(at(labels.ok, { n: primaryN })) + '</span>'];
        if (counts.skip) {
            chips.push(
                '<span class="chip n">' + esc(at(labels.skip, { n: counts.skip })) + '</span>'
            );
        }
        if (counts.error) {
            chips.push(
                '<span class="chip b">' + esc(at(labels.err, { n: counts.error })) + '</span>'
            );
        }
        return '<div class="ci-counts">' + chips.join('') + '</div>';
    }

    function rowLineHtml(row) {
        var chip = chipClassForStatus(row.status);
        var reasonHtml = row.reason
            ? '<span class="ci-reason">' + esc(at(errKeyFor(row.reason))) + '</span>'
            : '';
        return (
            '<tr class="ci-row">' +
            '<td>' +
            esc(row.name || '—') +
            '</td><td>' +
            esc(row.tax_id || '—') +
            '</td><td><span class="chip ' +
            chip +
            '">' +
            esc(at('client_import_status_' + row.status)) +
            '</span>' +
            reasonHtml +
            '</td></tr>'
        );
    }

    function rowTableHtml(rows) {
        return (
            '<div class="mx-scroll"><table class="mx-table"><thead><tr><th>' +
            esc(at('client_import_col_name')) +
            '</th><th>' +
            esc(at('client_import_col_tax_id')) +
            '</th><th>' +
            esc(at('client_import_col_status')) +
            '</th></tr></thead><tbody>' +
            rows.map(rowLineHtml).join('') +
            '</tbody></table></div>'
        );
    }

    // 预览表:上传后表头识别成功的逐行三态(valid/skip/error)+ 计数条 + 确认/取消按钮。
    function previewTableHtml(preview) {
        var counts = previewCounts(preview);
        return (
            countsChipsHtml(counts.valid, counts, {
                ok: 'client_import_preview_valid_n',
                skip: 'client_import_preview_skip_n',
                err: 'client_import_preview_error_n',
            }) +
            rowTableHtml(preview) +
            '<div class="ci-actions">' +
            '<button type="button" class="btn" data-action="ci-cancel">' +
            esc(at('intake_clear')) +
            '</button>' +
            '<button type="button" class="btn pri" data-action="ci-confirm"' +
            (counts.valid ? '' : ' disabled') +
            '>' +
            esc(at('client_import_confirm_btn', { n: counts.valid })) +
            '</button></div>'
        );
    }

    // 结果卡:commit 后逐行最终态(created/skip/error)+ 计数条 + 关闭/再导一份按钮。
    function resultCardHtml(results) {
        var counts = resultCounts(results);
        return (
            '<div class="ci-result-hd">' +
            esc(at('client_import_result_title')) +
            '</div>' +
            countsChipsHtml(counts.created, counts, {
                ok: 'client_import_result_created_n',
                skip: 'client_import_result_skip_n',
                err: 'client_import_result_error_n',
            }) +
            rowTableHtml(results) +
            '<div class="ci-actions">' +
            '<button type="button" class="btn" data-action="ci-reset">' +
            esc(at('client_import_import_another')) +
            '</button>' +
            '<button type="button" class="btn pri" data-action="ci-close">' +
            esc(at('client_import_done_btn')) +
            '</button></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.clientImportRender = {
        validateFile: validateFile,
        chipClassForStatus: chipClassForStatus,
        errKeyFor: errKeyFor,
        previewCounts: previewCounts,
        resultCounts: resultCounts,
        fileZoneHtml: fileZoneHtml,
        previewTableHtml: previewTableHtml,
        resultCardHtml: resultCardHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
