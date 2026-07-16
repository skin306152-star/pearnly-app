/*
 * Pearnly AI · ai-desk-compose-render.js · FD-0d 总台输入区 + 手动开单面板 HTML 拼装
 *
 * 拆自 ai-desk-render.js(单文件 <500 行铁律,同 ai-profile-render.js/
 * ai-profile-panels-render.js 先例):消息卡在那边,这里管「怎么把料/目标喂进去」——
 * 上传区(desk 自建 dropzone)、目标输入条、手动开单兜底表单、上下文条。
 *
 * 依赖 AI.deskRender(clientOptionsHtml/periodOptionsHtml/intentOptionsHtml/
 * confirmReady 已在那边导出)+ at()/AI.state,只在浏览器根挂载,零 node 纯函数段
 * (这里全是 DOM 挂载用 HTML 拼装,状态判定已在 ai-desk-render.js 测过)。
 */
(function (root) {
    'use strict';
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }
    function R() {
        return root.AI.deskRender;
    }

    var UPLOAD_ICON =
        '<svg viewBox="0 0 24 24" fill="none" stroke-width="2">' +
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>';

    // 上传区(拖拽/点选),desk 自建 dropzone——不能字面复用 ai-intake-render.js 的
    // dropzoneHtml():那份固定 id="ikDrop"/data-action="ik-*",与客户独立页的收料 tab
    // (cv-intake,DOM 常驻)同屏可能同时存在,重复 id 会冲突。校验/合批逻辑(validateFiles/
    // mergeFiles)仍原样复用 AI.intakeRender,只有这层 HTML 骨架另写(视觉同款:同一批
    // .dropzone/.dz-*/.file-strip/.fchip CSS 类,ai-intake.css 已随 bundle 加载)。
    function deskDropzoneHtml(ctx) {
        var n = (ctx.pendingFiles || []).length;
        var errRow = ctx.uploadErrKey
            ? '<div class="intake-err">' + esc(at(ctx.uploadErrKey)) + '</div>'
            : '';
        var inner;
        if (n > 0) {
            var chips = '';
            for (var i = 0; i < Math.min(n, 60); i++) chips += '<span class="fchip"></span>';
            inner =
                '<div class="dz-filled"><div class="dz-count"><b>' +
                n +
                '</b> ' +
                esc(at('intake_files_ready')) +
                '</div><div class="file-strip">' +
                chips +
                '</div><button type="button" class="btn" data-action="desk-clear-files">' +
                esc(at('intake_clear')) +
                '</button></div>';
        } else {
            inner =
                '<div class="dz-inner"><div class="dz-ic">' +
                UPLOAD_ICON +
                '</div><div class="dz-t">' +
                esc(at('fd_drop_t')) +
                '</div><div class="dz-s">' +
                esc(at('fd_drop_s')) +
                '</div><button type="button" class="btn" data-action="desk-pick">' +
                esc(at('intake_pick')) +
                '</button></div>';
        }
        return (
            '<div class="dropzone fd-dropzone" id="deskDrop" tabindex="0" role="button" aria-label="' +
            esc(at('fd_drop_t')) +
            '">' +
            inner +
            '</div>' +
            errRow
        );
    }

    // 目标输入条(§2.2 底部固定条):上传区 + 文本输入 + 发送,手机 sticky bottom(CSS)。
    function composerHtml(ctx) {
        var hasContent = (ctx.pendingFiles || []).length > 0 || !!(ctx.utterance || '').trim();
        var sendDisabled = ctx.sending || !hasContent;
        return (
            '<div class="fd-composer">' +
            deskDropzoneHtml(ctx) +
            '<div class="fd-input-row">' +
            '<input type="text" id="fdUtteranceInput" class="fd-input" maxlength="500" placeholder="' +
            esc(at('fd_input_ph')) +
            '" value="' +
            esc(ctx.utterance || '') +
            '"><button type="button" class="btn pri" data-action="desk-send"' +
            (sendDisabled ? ' disabled' : '') +
            '>' +
            esc(ctx.sending ? at('fd_sending') : at('fd_send_btn')) +
            '</button></div>' +
            '<button type="button" class="fd-manual-link" data-action="desk-open-manual">' +
            esc(at('fd_manual_link')) +
            '</button></div>'
        );
    }

    // 手动开单兜底面板(施工总册 §2.2「不可谈判」):三选一(客户/期间/意图)+ 复用
    // composer 同一块上传区(不第二套 dropzone,pendingFiles 是共享态)——大脑挂/闸关时
    // 这条路径独立于 interpret 端点,零共享故障面。
    function manualPanelHtml(state) {
        var m = state.manual || {};
        if (!m.open) return '';
        var sel = m.selection || {};
        var errHtml = m.errKey ? '<div class="intake-err">' + esc(at(m.errKey)) + '</div>' : '';
        // 复用既有草稿(reuseContractId,通常来自降级卡的「手动开单」)不必再选文件——
        // 那份合同的料已经暂存在服务端;否则要求 composer 当前累积的 pendingFiles 非空。
        var hasFiles = !!m.reuseContractId || (state.pendingFiles || []).length > 0;
        var ready = R().confirmReady(sel) && hasFiles;
        var hint = m.reuseContractId ? at('fd_manual_hint_reuse') : at('fd_manual_hint');
        return (
            '<div class="panel fd-card fd-manual"><div class="hd"><h3>' +
            esc(at('fd_manual_title')) +
            '</h3></div><div class="bd"><p class="fd-manual-hint">' +
            esc(hint) +
            '</p><div class="fd-row">' +
            '<label class="fd-lb">' +
            esc(at('fd_field_client')) +
            '<select id="fdManualClientSel">' +
            R().clientOptionsHtml(state.clients, sel.clientId, 'fd_pick_client') +
            '</select></label>' +
            '<label class="fd-lb">' +
            esc(at('fd_field_period')) +
            '<select id="fdManualPeriodSel">' +
            R().periodOptionsHtml(sel.period) +
            '</select></label>' +
            '<label class="fd-lb">' +
            esc(at('fd_field_intent')) +
            '<select id="fdManualIntentSel">' +
            R().intentOptionsHtml(sel.intent) +
            '</select></label></div>' +
            errHtml +
            '<div class="fd-actions">' +
            '<button type="button" class="btn pri" data-action="desk-manual-submit"' +
            (ready && !m.submitting ? '' : ' disabled') +
            '>' +
            esc(m.submitting ? at('fd_confirming') : at('fd_manual_submit_btn')) +
            '</button><button type="button" class="btn" data-action="desk-manual-cancel">' +
            esc(at('fd_manual_cancel_btn')) +
            '</button></div></div></div>'
        );
    }

    // 上下文条(§2.2:客户 picker,可空 = 看全租户消息流)。选中即重拉 feed(过滤该客户
    // 历史),不影响下一份新合同的客户建议(那仍由大脑 interpret 或人点合同卡决定)。
    function contextBarHtml(state) {
        return (
            '<div class="fd-context-bar">' +
            '<select id="fdCtxClientSel">' +
            R().clientOptionsHtml(state.clients, state.contextClientId, 'fd_ctx_all_clients') +
            '</select></div>'
        );
    }

    function pageHtml(state) {
        return (
            contextBarHtml(state) +
            '<div class="fd-feed" id="fdFeed">' +
            R().feedHtml(state.turns, state.contractCtx) +
            manualPanelHtml(state) +
            '</div>' +
            composerHtml(state)
        );
    }

    root.AI = root.AI || {};
    root.AI.deskComposeRender = {
        deskDropzoneHtml: deskDropzoneHtml,
        composerHtml: composerHtml,
        manualPanelHtml: manualPanelHtml,
        contextBarHtml: contextBarHtml,
        pageHtml: pageHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
