/*
 * Pearnly AI · ai-review-render.js · 人审队列(W3)的 HTML 拼装 + toast
 *
 * 同 ai-kanban-render.js 先例:拼 HTML + 少量样式判断,值得单独断言的逻辑(过滤/分级/
 * payload 构造)已经在 ai-review-queue.js 被单测覆盖,这里不再重复测。唯一带 DOM 的例外
 * 是 showToast/hideToast(挂 document.body 的全局提示,审核队列与收件箱两个编排层共用,
 * 见函数注释)。依赖 window.AI.state/format/reviewQueue/viewer 与全局 at(),故必须排在
 * 它们之后、ai-review.js 之前加载。
 */
(function () {
    'use strict';

    function esc(s) {
        return AI.state.esc(s);
    }
    function money(v) {
        return v == null || v === '' ? '—' : AI.format.money(v);
    }
    function txt(v) {
        return v ? esc(v) : '—';
    }

    // 已裁决票的 chip class:accepted/recalc 用 good,excluded 用 faint(灰)——
    // 同 v4 状态族用法(good=顺畅,warn=处理中,crit=卡点)。pending/failed 走各自的
    // 硬编码分支(见 statusChip),不经这张表。
    var _CHIP_CLASS = {
        rv_chip_accepted: 'g',
        rv_chip_recalc: 's',
        rv_chip_excluded: 'n',
        rv_chip_dir_purchase: 'g',
        rv_chip_dir_sales: 's',
        rv_chip_dir_nontax: 'n',
    };

    function chip(cls, label) {
        return '<span class="chip ' + cls + '">' + esc(label) + '</span>';
    }

    // 该卡当前该显示的 chip:本地乐观态优先于服务端 decision(乐观 UI 立即可见);
    // 都没有则显 flag_reason 严重度分级(尚未裁决)。
    function statusChip(entry, local) {
        if (local && local.state === 'pending') {
            return chip('w', at('rv_chip_pending'));
        }
        if (local && local.state === 'failed') {
            // errKey 命中具体错误码就显对应文案,没有就退化通用失败——同 decide().catch
            // 里给 toast 挑文案的同一份 local.errKey(chip 与 toast 同源,不各拼一套)。
            return chip('b', local.errKey ? at(local.errKey) : at('err_generic'));
        }
        var localKey = local && AI.reviewQueue.decisionChipKey(local.decision);
        var key = localKey || AI.reviewQueue.decisionChipKey(entry.decision);
        if (key) return chip(_CHIP_CLASS[key], at(key));
        // 严重度读后端 verdict_hint.severity(政策单一事实源在 services/workorder/verdict.py);
        // 缺 hint(未知原因)诚实回落 crit,与 severity_of 未知→crit 同口径。
        var sev = (entry.verdict_hint && entry.verdict_hint.severity) || 'crit';
        var reasonKey = AI.reviewQueue.flagReasonKey(entry.flag_reason);
        var reasonLabel = reasonKey ? at(reasonKey) : entry.flag_reason || '';
        return chip(sev === 'crit' ? 'b' : 'w', reasonLabel);
    }

    function decidedByLine(entry, local) {
        var d = (local && local.decision) || entry.decision;
        if (!d || !d.decision) return '';
        var at_ = String(d.at || '')
            .slice(0, 16)
            .replace('T', ' ');
        var actor = AI.format.actorDisplay(d.actor); // 服务端回显 "user:<uuid>" → 短八位
        return (
            '<p class="rv-decided-by">' +
            esc(at('rv_decided_by', { actor: actor, at: at_ })) +
            '</p>'
        );
    }

    // 契约 §5:改判过的票再进队列,表格要显 decision.values(裁决数),不是干等一行
    // 「已由谁判」小字却还摆着 AI 原读数误导人。recalc 时 VAT 行主显裁决值,原 OCR 读数
    // 降级成同格小字旁注;face_value/exclude 就是原读数本身,不用另显。
    function fieldRows(read, effectiveDecision) {
        read = read || {};
        var vatMain = read.vat;
        var vatNote = '';
        if (
            effectiveDecision &&
            effectiveDecision.decision === 'recalc' &&
            effectiveDecision.values &&
            effectiveDecision.values.vat
        ) {
            vatMain = effectiveDecision.values.vat;
            if (String(vatMain) !== String(read.vat)) {
                vatNote = '<br><small>AI ' + money(read.vat) + '</small>';
            }
        }
        return (
            '<tr><td class="lb">' +
            esc(at('rv_field_supplier')) +
            '</td><td class="vl">' +
            txt(read.seller_tax) +
            '</td></tr>' +
            '<tr><td class="lb">' +
            esc(at('rv_field_net')) +
            '</td><td class="vl num">' +
            money(read.subtotal) +
            '</td></tr>' +
            '<tr class="rv-vat-row"><td class="lb">' +
            esc(at('rv_field_vat_face')) +
            '</td><td class="vl num" id="rvVatDisplay">' +
            money(vatMain) +
            vatNote +
            '</td></tr>' +
            '<tr><td class="lb">' +
            esc(at('rv_field_total')) +
            '</td><td class="vl num">' +
            money(read.total_amount) +
            '</td></tr>' +
            '<tr><td class="lb">' +
            esc(at('rv_field_invno')) +
            '</td><td class="vl">' +
            txt(read.invoice_number) +
            '</td></tr>'
        );
    }

    // 动作按钮定义表:A/E/X(金额票)与 P/S/X(方向票)两组共用同一套拼接逻辑
    // (actionButton/renderActionButtons/kbdLine),不再各写一份重复 HTML 拼接。命名避开
    // cardHtml 里已有的局部变量 actionsHtml(动作行拼好的 HTML 字符串),不与之同名撞混。
    // 收件箱(ai-review-inbox-render.js)经导出面复用同两张表,data-action 前缀参数化。
    var _AMOUNT_ACTION_DEFS = [
        { action: 'rv-accept', key: 'rv_key_accept', kbd: 'A', cls: 'ok' },
        { action: 'rv-edit', key: 'rv_key_edit', kbd: 'E', cls: '' },
        { action: 'rv-exclude', key: 'rv_key_exclude', kbd: 'X', cls: 'no' },
    ];
    // X 语义在方向票模式下是「非税票」而非「剔除」,提示条(dirNote)明示,按钮定义表不重叠含义。
    var _DIRECTION_ACTION_DEFS = [
        { action: 'rv-dir-purchase', key: 'rv_key_dir_purchase', kbd: 'P', cls: 'ok' },
        { action: 'rv-dir-sales', key: 'rv_key_dir_sales', kbd: 'S', cls: '' },
        { action: 'rv-dir-nontax', key: 'rv_key_dir_nontax', kbd: 'X', cls: 'no' },
    ];

    // opts(收件箱行内按钮用):actionPrefix 换掉 rv- 前缀(riq-*)、btnClass 覆盖语义色
    // (行内统一 btn sm)、itemId 附 data-item(聚合页一屏多卡,靠它定位是哪张票)。
    function actionButton(def, opts) {
        opts = opts || {};
        var action = opts.actionPrefix ? def.action.replace(/^rv-/, opts.actionPrefix) : def.action;
        var cls = opts.btnClass || (def.cls ? 'btn ' + def.cls : 'btn');
        return (
            '<button type="button" class="' +
            cls +
            '" data-action="' +
            action +
            '"' +
            (opts.itemId ? ' data-item="' + opts.itemId + '"' : '') +
            '>' +
            esc(at(def.key)) +
            ' <span class="kbd">' +
            def.kbd +
            '</span></button>'
        );
    }

    function renderActionButtons(defs) {
        return (
            '<div class="rv-actions" id="rvActions">' +
            defs
                .map(function (def) {
                    return actionButton(def);
                })
                .join('') +
            '</div>'
        );
    }

    // 金额票动作行(A 采纳 / E 改数 / X 剔除)。
    function amountActions() {
        return renderActionButtons(_AMOUNT_ACTION_DEFS);
    }

    // 方向票动作行(P 进项 / S 销项 / X 非税)。
    function directionActions() {
        return renderActionButtons(_DIRECTION_ACTION_DEFS);
    }

    function kbdLine(isDir) {
        var labels = (isDir ? _DIRECTION_ACTION_DEFS : _AMOUNT_ACTION_DEFS).map(function (def) {
            return esc(at(def.key)) + ' <span class="kbd">' + def.kbd + '</span>';
        });
        return (
            '<p class="rv-kbdline">' +
            labels.join(' · ') +
            ' · <span class="kbd">←</span><span class="kbd">→</span></p>'
        );
    }

    // D2-S9:审核队列第四动作「推 LINE 待问」(A/E/X 之外·不串键盘裁决流)。pool:
    // {open, busy, errKey, done} | undefined,按 item_id 独立持有(同 local 的乘载方式)。
    var _POOL_QTYPES = ['direction', 'amount', 'drop', 'freeform'];
    function poolPanelHtml(pool) {
        pool = pool || {};
        if (pool.done) {
            return (
                '<div class="rv-pool"><span class="chip s">' +
                esc(at('rv_pool_done')) +
                '</span></div>'
            );
        }
        var toggleBtn =
            '<button type="button" class="btn sm" data-action="rv-pool-toggle"' +
            (pool.busy ? ' disabled' : '') +
            '>' +
            esc(at('rv_key_pool')) +
            ' <span class="kbd">Q</span></button>';
        if (!pool.open) return '<div class="rv-pool">' + toggleBtn + '</div>';
        var options = _POOL_QTYPES
            .map(function (qt) {
                return (
                    '<button type="button" class="btn sm" data-action="rv-pool-pick" data-qtype="' +
                    qt +
                    '"' +
                    (pool.busy ? ' disabled' : '') +
                    '>' +
                    esc(at('pool_qtype_' + qt)) +
                    '</button>'
                );
            })
            .join('');
        var err = pool.errKey ? '<div class="rv-pool-err">' + esc(at(pool.errKey)) + '</div>' : '';
        return (
            '<div class="rv-pool on">' +
            toggleBtn +
            '<div class="rv-pool-options">' +
            esc(at('rv_pool_pick_hint')) +
            options +
            '</div>' +
            err +
            '</div>'
        );
    }

    // ctx: {entry, idx, total, local, editing, editErr, editValue, pool}
    function cardHtml(ctx) {
        var entry = ctx.entry;
        var read = entry.ocr_read || {};
        var isDir = AI.reviewQueue.isDirectionTicket(entry);
        var effectiveDecision = (ctx.local && ctx.local.decision) || entry.decision;
        // 方向票不进「改数」态(E),只定向;金额票编辑时隐藏动作行。
        var dirNote = isDir
            ? '<div class="rv-dir-note">' + esc(at('rv_dir_prompt')) + '</div>'
            : '';
        var actionsHtml = ctx.editing ? '' : isDir ? directionActions() : amountActions();
        var editHtml = ctx.editing
            ? '<div class="rv-edit" id="rvEdit">' +
              '<label class="rv-edit-lb" for="rvVatInput">' +
              esc(at('rv_field_vat_face')) +
              '</label>' +
              // editValue 必经 startEdit 赋值(entry.ocr_read.vat 或先前裁决值,至少是
              // 空串)才会进这个分支——editing 为 true 时它不会是 null,不用再兜底。
              '<input class="rv-vat-input num" id="rvVatInput" inputmode="decimal" value="' +
              esc(ctx.editValue) +
              '">' +
              '<div class="rv-edit-hint">' +
              esc(at('rv_edit_hint')) +
              '</div>' +
              (ctx.editErr
                  ? '<div class="rv-edit-err" id="rvEditErr">' +
                    esc(at('rv_edit_vat_required')) +
                    '</div>'
                  : '') +
              '</div>'
            : '';
        var poolHtml = ctx.editing ? '' : poolPanelHtml(ctx.pool);
        return (
            '<h2 class="rv-title">' +
            esc(at('review_title')) +
            '</h2>' +
            '<div class="rv-grid" id="rvGrid">' +
            '<div>' +
            '<div class="panel rv-orig-hd"><div class="bd">' +
            '<span class="rv-orig-lb">' +
            esc(at('rv_orig_label')) +
            '</span>' +
            '</div></div>' +
            '<div class="rv-imgwrap" id="rvImgWrap">' +
            AI.viewer.imageViewerHtml({
                hint: at('imgv_hint'),
                noimg: at('imgv_noimg'),
                loading: at('imgv_loading'),
            }) +
            '</div>' +
            '</div>' +
            '<div>' +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('rv_ai_read')) +
            ' ' +
            statusChip(entry, ctx.local) +
            '<span class="note" style="margin-left:auto">' +
            (ctx.idx + 1) +
            ' / ' +
            ctx.total +
            '</span></h3></div>' +
            '<div class="bd">' +
            dirNote +
            '<table class="fldt">' +
            fieldRows(read, effectiveDecision) +
            '</table>' +
            decidedByLine(entry, ctx.local) +
            actionsHtml +
            editHtml +
            poolHtml +
            '</div></div>' +
            '</div></div>' +
            kbdLine(isDir)
        );
    }

    // 空态(队列本就 0 张·契约 §6 "好事态")。
    function emptyOkHtml() {
        return (
            '<div class="panel"><div class="bd rv-done">' +
            '<span class="chip g">' +
            esc(at('review_empty_ok_t')) +
            '</span>' +
            '<p>' +
            esc(at('review_empty_ok_s')) +
            '</p>' +
            '<button class="btn pri" data-action="rv-goto-pkg">' +
            esc(at('tab_pkg')) +
            '</button>' +
            '</div></div>'
        );
    }

    // 队列走完(契约 §4)。blockedInfo: {reasons:[], hasQueue, timedOut?} | null;
    // rerunState: 'idle'|'waiting';rerunProgress: classify 步 {processed,total} | null
    // (R2F-R3 #5:等待态有真进度就报「识别中 X/N」,轮询超时诚实说"仍在后台跑"而不是
    // 让 blockedInfo 空 reasons 的沉默态冒充"卡住需要你判断")。
    function clearedHtml(n, m, rerunState, blockedInfo, rerunProgress) {
        var waitingLabel = rerunProgress
            ? at('wo_classify_progress', {
                  done: rerunProgress.processed,
                  total: rerunProgress.total,
              })
            : at('rv_rerun_waiting');
        var btn =
            rerunState === 'waiting'
                ? '<button class="btn pri" disabled>' + esc(waitingLabel) + '</button>'
                : '<button class="btn pri" data-action="rv-rerun">' +
                  esc(at('rv_rerun')) +
                  '</button>';
        var blocked = '';
        if (blockedInfo && blockedInfo.timedOut) {
            blocked =
                '<p class="rv-blocked">' +
                esc(at('wo_run_timeout_hint')) +
                '</p><button class="btn sm" data-action="rv-refresh-status">' +
                esc(at('wo_refresh_btn')) +
                '</button>';
        } else if (blockedInfo) {
            blocked =
                '<p class="rv-blocked">' +
                esc(at('rv_still_blocked')) +
                (blockedInfo.reasons.length ? '：' + esc(blockedInfo.reasons.join('、')) : '') +
                '</p>';
            if (blockedInfo.hasQueue) {
                blocked +=
                    '<button class="btn sm" data-action="rv-back-to-queue">' +
                    esc(at('back_dash')) +
                    '</button>';
            }
        }
        return (
            '<div class="panel"><div class="bd rv-done">' +
            '<span class="chip g">' +
            esc(at('rv_queue_cleared_t')) +
            '</span>' +
            '<div class="big">' +
            esc(at('rv_queue_cleared_s', { n: n, m: m })) +
            '</div>' +
            blocked +
            btn +
            '</div></div>'
        );
    }

    function toastHtml(message, showUndo) {
        return (
            '<div class="toast" id="rvToast">' +
            esc(message) +
            (showUndo
                ? ' · <button class="rv-toast-undo" data-action="rv-undo">' +
                  esc(at('rv_undo')) +
                  '</button>'
                : '') +
            '</div>'
        );
    }

    // ============ toast(挂 document.body,3 秒 undo / 4 秒失败提示) ============
    // 审核队列(ai-review.js)与收件箱(ai-review-inbox.js)此前各持一份近逐字实现;
    // 计时器句柄收敛到这里(全局同刻至多一个 #rvToast),编排层只传文案 + 各自的 undo
    // 回调(队列回滚上一张 / 收件箱撤销批量)。
    var UNDO_TOAST_MS = 3000;
    var FAIL_TOAST_MS = 4000;
    var toastTimer = null;

    function showToast(message, undoFn) {
        hideToast();
        var div = document.createElement('div');
        div.innerHTML = toastHtml(message, !!undoFn);
        var el = div.firstChild;
        document.body.appendChild(el);
        requestAnimationFrame(function () {
            el.classList.add('on');
        });
        if (undoFn) {
            var undoBtn = el.querySelector('[data-action="rv-undo"]');
            if (undoBtn)
                undoBtn.onclick = function () {
                    undoFn();
                    hideToast();
                };
        }
        toastTimer = setTimeout(hideToast, undoFn ? UNDO_TOAST_MS : FAIL_TOAST_MS);
    }

    function hideToast() {
        if (toastTimer) {
            clearTimeout(toastTimer);
            toastTimer = null;
        }
        var el = document.getElementById('rvToast');
        if (el) el.parentNode.removeChild(el);
    }

    // R4 税号错录守护卡:守护闸判「登记税号疑似录错」时弹「票上都是 X,登记 Y」+ 一键改正重锚
    // (有 settings.workspace.manage 权限走按钮;无权限诚实降级提示找老板改,不摆假按钮)。
    // 同账套通常只一个税号嫌疑,一次呈现一张;非该类型 alert 不渲染(通用投影的向后兼容)。
    function taxidAlertHtml(alerts, opts) {
        if (!alerts || !alerts.length) return '';
        var a = alerts[0];
        if (a.type !== 'taxid_typo_suspected') return '';
        opts = opts || {};
        var msg = esc(
            at('rv_taxid_alert_msg', { suspected: a.suspected, registered: a.registered })
        );
        var action;
        if (!opts.canManage) {
            action = '<span class="rv-taxid-hint">' + esc(at('rv_taxid_need_manager')) + '</span>';
        } else if (opts.busy) {
            action = '<button class="btn pri" disabled>' + esc(at('rv_taxid_fixing')) + '</button>';
        } else {
            action =
                '<button class="btn pri" data-action="rv-taxid-realign">' +
                esc(at('rv_taxid_fix_btn')) +
                '</button>';
        }
        var err = opts.errKey
            ? '<div class="rv-taxid-err">' + esc(at('rv_taxid_fix_fail')) + '</div>'
            : '';
        return (
            '<div class="rv-taxid-alert" role="alert"><div class="rv-taxid-msg">' +
            msg +
            '</div>' +
            action +
            err +
            '</div>'
        );
    }

    window.AI = window.AI || {};
    window.AI.reviewRender = {
        cardHtml: cardHtml,
        emptyOkHtml: emptyOkHtml,
        clearedHtml: clearedHtml,
        taxidAlertHtml: taxidAlertHtml,
        toastHtml: toastHtml,
        showToast: showToast,
        hideToast: hideToast,
        fieldRows: fieldRows,
        actionButton: actionButton,
        AMOUNT_ACTION_DEFS: _AMOUNT_ACTION_DEFS,
        DIRECTION_ACTION_DEFS: _DIRECTION_ACTION_DEFS,
    };
})();
