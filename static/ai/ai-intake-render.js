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

    // 单文件字节上限,与后端 workorder_routes 的 _MAX_MATERIAL_BYTES 对齐——前端先挡一道
    // (省一次注定 413 的往返),后端仍是权威闸(错误码四语呈现同一份文案)。总张数不在这里
    // 挡:splitBatches 已把任意张数切成 ≤BATCH_MAX_FILES 的安全批,每批都远低于后端单请求
    // 上限 _MAX_MATERIAL_FILES=50,故前端不再需要一道总数预检门槛。
    var MAX_BYTES = 20 * 1024 * 1024;

    // 单次请求分批上限(G1 真机:一次传 25 张 ~55MB 撞 prod nginx client_max_body_size 50M,
    // 请求挂死无响应)。35MB 留够安全边际(50M 硬顶打对折出头,扛住 multipart 边界开销);
    // 20 张是既有实测安全值,与字节上限并列独立守——谁先触顶谁切批,两条都守。
    var BATCH_MAX_BYTES = 35 * 1024 * 1024;
    var BATCH_MAX_FILES = 20;

    // 把已通过 validateFiles 的选中文件切成若干批,顺序上传用(每批一次 multipart 请求)。
    // 贪心装箱:文件逐个塞进当前批,一旦加进去就超字节上限或张数上限 → 当前批收口开新批。
    // 单文件不可能超 BATCH_MAX_BYTES(validateFiles 已挡在 MAX_BYTES=20MB < 35MB),但仍按
    // "当前批非空才检查超限" 兜底,防御性地让任何超大单文件也能独占一批而不是死循环。
    function splitBatches(files, maxBytes, maxCount) {
        var capBytes = maxBytes || BATCH_MAX_BYTES;
        var capCount = maxCount || BATCH_MAX_FILES;
        var list = files || [];
        var batches = [];
        var current = [];
        var currentBytes = 0;
        for (var i = 0; i < list.length; i++) {
            var f = list[i];
            var size = (f && f.size) || 0;
            var overBytes = current.length > 0 && currentBytes + size > capBytes;
            var overCount = current.length >= capCount;
            if (overBytes || overCount) {
                batches.push(current);
                current = [];
                currentBytes = 0;
            }
            current.push(f);
            currentBytes += size;
        }
        if (current.length) batches.push(current);
        return batches;
    }

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

    // 上传前端预检:超单文件字节 → 结构化错误 key(与后端 413 码映射同一份四语文案,不各拼
    // 一套)。张数不设上限(见上 MAX_BYTES 注),全通过返回 {ok:true}。
    function validateFiles(files) {
        var list = files || [];
        for (var i = 0; i < list.length; i++) {
            if (list[i] && list[i].size > MAX_BYTES) {
                return { ok: false, errKey: 'err_workorder_file_too_large' };
            }
        }
        return { ok: true };
    }

    // 分批选择累积(2026-07-14 UI 记债 #4):点选/拖拽第二批不该顶替第一批已选文件——
    // 按 name+size 去重(浏览器 File 无稳定 id,同名同字节视为同一份,重选不重复计入),
    // 已选的排前面、新选的追加在后,保持选择顺序可预期。
    function mergeFiles(existing, incoming) {
        var merged = (existing || []).slice();
        var seen = {};
        merged.forEach(function (f) {
            seen[f.name + '|' + f.size] = true;
        });
        (incoming || []).forEach(function (f) {
            var key = f.name + '|' + f.size;
            if (seen[key]) return;
            seen[key] = true;
            merged.push(f);
        });
        return merged;
    }

    function resolveIntakeErrKey(err) {
        if (err && err.status === 401) return 'intake_err_session';
        if (err && err.status === 403) {
            return err.code === 'authz.entrance_scope'
                ? 'intake_err_entrance'
                : 'intake_err_forbidden';
        }
        if (!err || err.status == null) return 'intake_err_network';
        return 'intake_form_invalid';
    }

    var pure = {
        MAX_BYTES: MAX_BYTES,
        BATCH_MAX_BYTES: BATCH_MAX_BYTES,
        BATCH_MAX_FILES: BATCH_MAX_FILES,
        parseAmount: parseAmount,
        buildSalesPayload: buildSalesPayload,
        validateFiles: validateFiles,
        splitBatches: splitBatches,
        mergeFiles: mergeFiles,
        resolveIntakeErrKey: resolveIntakeErrKey,
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

    // 上传中/失败时的真进度后缀(R2F-R3 #4):不论单批多批都拼「已传/共几张」——此前
    // 单批(BATCH_MAX_FILES=20 以内)不拼数字纯转圈,单批一样有真实的"已传 X / 总 N"
    // 可报(uploadDone 由每批 addMaterials 结算后累加,单批时就是 0→N 一步到位,但那一步
    // 也是真数不是假动画)。分批(BATCH_MAX_BYTES/BATCH_MAX_FILES 触顶才切批)时额外拼
    // 「第几批」,数字+分隔符不夹外语词,不新增 i18n 键(复用既有 intake_uploading/
    // 错误文案原句,后面加纯数字进度)。百分比是当前批的字节级上传进度(XHR
    // upload.onprogress),纯数字不需要 i18n。
    function batchProgressSuffix(ctx) {
        if (!ctx.uploadTotal) return '';
        var s = ' (' + (ctx.uploadDone || 0) + '/' + ctx.uploadTotal;
        if (ctx.uploadBatchTotal > 1) {
            s += ' · ' + (ctx.uploadBatchIndex || 0) + '/' + ctx.uploadBatchTotal;
        }
        // <100 才拼:100% 是当前批已送达、服务端校验落盘中的窗口,挂着会被读成
        // 「全部传完」(2026-07-17 复测),此时只留已结算计数更诚实。
        if (ctx.uploadBytesPct != null && ctx.uploadBytesPct < 100) {
            s += ' · ' + ctx.uploadBytesPct + '%';
        }
        return s + ')';
    }

    function uploadProgressText(ctx) {
        return at('intake_uploading') + batchProgressSuffix(ctx);
    }

    // 逐文件回执行:名字 + 状态词。状态颜色类映射 queued→wait / uploading→run /
    // accepted→ok / rejected+failed→bad(令牌色在 ai-intake.css)。
    function perFileListHtml(perFile) {
        if (!perFile || !perFile.length) return '';
        var stKey = {
            queued: 'intake_file_queued',
            uploading: 'intake_file_uploading',
            accepted: 'intake_file_accepted',
            rejected: 'intake_file_rejected',
            failed: 'intake_file_failed',
        };
        var stCls = {
            queued: 'wait',
            uploading: 'run',
            accepted: 'ok',
            rejected: 'bad',
            failed: 'bad',
        };
        var rows = '';
        for (var i = 0; i < perFile.length; i++) {
            rows +=
                '<div class="dz-frow"><span class="dz-fname">' +
                esc(perFile[i].name) +
                '</span><span class="dz-fst ' +
                stCls[perFile[i].status] +
                '">' +
                esc(at(stKey[perFile[i].status])) +
                '</span></div>';
        }
        return '<div class="dz-files">' + rows + '</div>';
    }

    // 拖拽/点选上传区。四态:idle(空)/ 已选文件 / 上传中 / 刚传完(引导重新跑)。
    function dropzoneHtml(ctx) {
        var n = ctx.files.length;
        var errRow = ctx.uploadErrKey
            ? '<div class="intake-err" id="ikUploadErr">' +
              esc(at(ctx.uploadErrKey) + batchProgressSuffix(ctx)) +
              '</div>'
            : '';
        var inner;
        if (ctx.uploading) {
            inner =
                '<div class="dz-inner"><div class="dz-ic uploading" aria-hidden="true">' +
                svg('<path d="M21 12a9 9 0 1 1-6.2-8.5"/>') +
                '</div><div class="dz-t" id="ikUploadProgress" aria-live="polite">' +
                esc(uploadProgressText(ctx)) +
                '</div>' +
                perFileListHtml(ctx.perFile) +
                '</div>';
        } else if (n > 0) {
            var rows = '';
            for (var i = 0; i < n; i++) {
                rows +=
                    '<div class="dz-frow"><span class="dz-fname">' +
                    esc(ctx.files[i].name) +
                    '</span></div>';
            }
            inner =
                '<div class="dz-filled"><div class="dz-count"><b>' +
                n +
                '</b> ' +
                esc(at('intake_files_ready')) +
                '</div><div class="dz-files">' +
                rows +
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
                '</button></div>' +
                perFileListHtml(ctx.perFile);
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
            ? '<div class="intake-err" id="ikFormErr">' +
              esc(at(ctx.formErrKey || 'intake_form_invalid')) +
              '</div>'
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
            (ctx.submitting || ctx.formLocked ? ' disabled' : '') +
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

    // 补料后「重新跑」面:idle → 按钮;waiting → 禁用转述(有真进度就报「识别中/读对账单
    // X/N」而不是空转的省略号,R2F-R3 #5)+「去工单页看进度→」引导(J-2/J-14:上传收齐
    // 自动开跑后不再让用户干瞪眼,给一个"去哪看"的出口);轮询次数用尽 → 诚实说"仍在
    // 后台跑"+手动刷新钮(不假装失败,也不装作没事发生);错 → 人话 + 重试(409"正在跑"
    // 也走这条,同时仍在轮询,不是终态)。
    function rerunHtml(ctx) {
        if (!ctx.dirty && ctx.rerunState !== 'waiting' && !ctx.rerunTimedOut) return '';
        var inner;
        if (ctx.rerunTimedOut) {
            inner =
                '<p class="intake-err">' +
                esc(at('wo_run_timeout_hint')) +
                '</p><button class="btn" data-action="ik-refresh-status">' +
                esc(at('wo_refresh_btn')) +
                '</button>';
        } else if (ctx.rerunState === 'waiting') {
            var waitingLabel = ctx.rerunProgress
                ? root.AI.format.progressLabel(ctx.rerunProgress)
                : at('intake_rerun_waiting');
            inner =
                '<button class="btn pri" disabled>' +
                esc(waitingLabel) +
                '</button>' +
                '<button class="btn sm" data-action="ik-goto-wo">' +
                esc(at('intake_goto_wo')) +
                '</button>';
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
    // 银行流水倒推卡(SA-3b)排在人工填销项表单之上——cardHtml 闸关/无数据时自己返回空串,
    // needsCardHtml() 的既有人工表单标记不受影响(逐字节不变)。
    // IN-0b 四件套(续传横幅/密码供钥卡/盘点条/失败批横幅)全部委托 AI.intakeManifest 拼装
    // (该模块零数据时各自返回空串,不额外分支)——续传横幅+密码卡置顶(需要用户先决断的
    // 事排前面),盘点条+失败批横幅收尾(投料结束后的诚实总结)。
    function intakeHtml(ctx) {
        var bankSales = ctx.needsSales
            ? root.AI.bankSalesRender.cardHtml(
                  ctx.bankSalesSuggestion,
                  ctx.bankSalesUi,
                  ctx.salesCorrob,
                  ctx.edcCorrob
              )
            : '';
        var needs = ctx.needsSales ? bankSales + needsCardHtml(ctx) : '';
        var im = root.AI.intakeManifest;
        var received =
            ctx.materialCount > 0
                ? '<div class="intake-received" role="status">' +
                  esc(at('intake_received_count', { n: ctx.materialCount })) +
                  '</div>'
                : '';
        return (
            '<div class="intake-body">' +
            '<p class="intake-lead">' +
            esc(at('intake_lead')) +
            '</p>' +
            received +
            im.resumeBannerHtml(ctx.resumeBanner) +
            im.passwordCardHtml(ctx.passwordCard) +
            needs +
            '<div class="intake-grid">' +
            dropzoneHtml(ctx) +
            channelsHtml() +
            '</div>' +
            rerunHtml(ctx) +
            im.manifestHtml(ctx.manifest) +
            im.failedBatchesHtml(ctx.failedBatches) +
            '</div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.intakeRender = {
        MAX_BYTES: MAX_BYTES,
        BATCH_MAX_BYTES: BATCH_MAX_BYTES,
        BATCH_MAX_FILES: BATCH_MAX_FILES,
        parseAmount: parseAmount,
        buildSalesPayload: buildSalesPayload,
        validateFiles: validateFiles,
        splitBatches: splitBatches,
        mergeFiles: mergeFiles,
        resolveIntakeErrKey: resolveIntakeErrKey,
        uploadProgressText: uploadProgressText,
        intakeHtml: intakeHtml,
        dropzoneHtml: dropzoneHtml,
        needsCardHtml: needsCardHtml,
        rerunHtml: rerunHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
