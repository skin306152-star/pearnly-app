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

    function statusChip(entry, local) {
        if (local && local.state === 'pending') {
            return chip('w', at('rv_chip_pending'));
        }
        if (local && local.state === 'failed') {
            return chip('b', local.errKey ? at(local.errKey) : at('err_generic'));
        }
        var localKey = local && AI.reviewQueue.decisionChipKey(local.decision);
        var key = localKey || AI.reviewQueue.decisionChipKey(entry.decision);
        if (key) return chip(_CHIP_CLASS[key], at(key));
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

    // 一个金额字段的显示值(J-C · IMG_2647 尸检:收件箱此前硬传 null effectiveDecision,
    // 改数后卡片仍显旧 OCR 读数)。corrected(与原读数不同的人工改值)加「已人工修正」徽标 +
    // 原读数小字旁注;未改的字段就是原读数本身,不挂徽标(状态诚实,不制造假阳性)。
    function correctedCell(field) {
        return (
            money(field.value) +
            (field.corrected
                ? ' <span class="chip w">' + esc(at('rv_manually_corrected')) + '</span>'
                : '')
        );
    }

    function correctedTextCell(field) {
        return (
            txt(field.value) +
            (field.corrected
                ? ' <span class="chip w">' + esc(at('rv_manually_corrected')) + '</span>'
                : '')
        );
    }

    // 契约 §5:改判过的票再进队列,表格要显 decision.values(裁决数),不是干等一行
    // 「已由谁判」小字却还摆着 AI 原读数误导人。net/vat/grand_total 三字段各自独立比对
    // (J-A 建议值三字段改数态落地后,不再只有 VAT 能被人工改过);face_value/exclude
    // 就是原读数本身,不用另显。
    function fieldRows(read, effectiveDecision) {
        read = read || {};
        var net = AI.reviewQueue.decidedValue(effectiveDecision, 'net', read.subtotal);
        var vat = AI.reviewQueue.decidedValue(effectiveDecision, 'vat', read.vat);
        var grand = AI.reviewQueue.decidedValue(
            effectiveDecision,
            'grand_total',
            read.total_amount
        );
        var invoiceNumber = AI.reviewQueue.decidedValue(
            effectiveDecision,
            'invoice_number',
            read.invoice_number
        );
        var invoiceDate = AI.reviewQueue.decidedValue(
            effectiveDecision,
            'invoice_date',
            read.invoice_date
        );
        return (
            '<tr><td class="lb">' +
            esc(at('rv_field_supplier')) +
            '</td><td class="vl">' +
            txt(read.seller_tax) +
            '</td></tr>' +
            '<tr><td class="lb">' +
            esc(at('rv_field_net')) +
            '</td><td class="vl num">' +
            correctedCell(net) +
            '</td></tr>' +
            '<tr class="rv-vat-row"><td class="lb">' +
            esc(at('rv_field_vat_face')) +
            '</td><td class="vl num" id="rvVatDisplay">' +
            correctedCell(vat) +
            '</td></tr>' +
            '<tr><td class="lb">' +
            esc(at('rv_field_total')) +
            '</td><td class="vl num">' +
            correctedCell(grand) +
            '</td></tr>' +
            '<tr><td class="lb">' +
            esc(at('rv_field_invno')) +
            '</td><td class="vl">' +
            correctedTextCell(invoiceNumber) +
            '</td></tr>' +
            '<tr><td class="lb">' +
            esc(at('rv_field_date')) +
            '</td><td class="vl">' +
            correctedTextCell(invoiceDate) +
            '</td></tr>'
        );
    }

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

    function amountActions() {
        return renderActionButtons(_AMOUNT_ACTION_DEFS);
    }

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

    function cardHtml(ctx) {
        var entry = ctx.entry;
        var read = entry.ocr_read || {};
        var isDir = AI.reviewQueue.isDirectionTicket(entry);
        var effectiveDecision = (ctx.local && ctx.local.decision) || entry.decision;
        // 方向票不进「改数」态(E),只定向;金额票编辑时隐藏动作行。
        var narrative = AI.reviewVerdict.narrativeOf(entry.verdict_hint, entry.flag_reason);
        var dirText = narrative.key
            ? at(narrative.key, narrative.vars)
            : narrative.fallbackText || at('rv_dir_prompt');
        var dirNote = isDir ? '<div class="rv-dir-note">' + esc(dirText) + '</div>' : '';
        var actionsHtml = ctx.editing ? '' : isDir ? directionActions() : amountActions();
        // 改数态统一显示票号、日期与三项金额；有确定性建议时额外标注建议来源。
        var editHtml = ctx.editing ? AI.reviewSuggest.editFormHtml(ctx) : '';
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
            // 三段计数器不再用卡片位置冒充进度；已处理折叠后单独报告待处理/已处理/总数。
            '<span class="note" id="rvCounter" style="margin-left:auto">' +
            esc(
                at('rv_counter', {
                    k: ctx.undecidedRemaining,
                    d: ctx.totalCount - ctx.undecidedRemaining,
                    n: ctx.totalCount,
                })
            ) +
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

    function clearedHtml(n, m, rerunState, blockedInfo, rerunProgress) {
        var waitingLabel = rerunProgress
            ? AI.format.progressLabel(rerunProgress)
            : at('rv_rerun_waiting');
        var systemBlocked = blockedInfo && blockedInfo.system;
        var materialBlocked = blockedInfo && blockedInfo.needs && blockedInfo.needs.length;
        var materialList = materialBlocked
            ? blockedInfo.needs.map(AI.format.fieldLabel).join('、')
            : '';
        var btn = '';
        if (rerunState === 'waiting') {
            btn = '<button class="btn pri" disabled>' + esc(waitingLabel) + '</button>';
        } else if (materialBlocked) {
            btn =
                '<button class="btn pri" data-action="rv-go-intake">' +
                esc(at('pkg_go_intake_btn')) +
                '</button>';
        } else {
            btn =
                '<button class="btn pri" data-action="rv-rerun">' +
                esc(at(systemBlocked ? 'retry' : 'rv_rerun')) +
                '</button>';
        }
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
                (materialBlocked
                    ? esc(at('card_needs_list', { list: materialList }))
                    : systemBlocked
                      ? esc(
                            at('system_blocked_detail', {
                                list: blockedInfo.reasons.join('、'),
                            })
                        )
                      : esc(at('rv_still_blocked')) +
                        (blockedInfo.reasons.length
                            ? '：' + esc(blockedInfo.reasons.join('、'))
                            : '')) +
                '</p>';
            if (blockedInfo.hasQueue) {
                blocked +=
                    '<button class="btn sm" data-action="rv-back-to-queue">' +
                    esc(at('back_dash')) +
                    '</button>';
            }
        }
        var chipKey = blockedInfo
            ? materialBlocked
                ? 'chip_needs_materials'
                : systemBlocked
                  ? 'status_system_failed'
                  : 'status_stuck'
            : rerunState === 'waiting'
              ? 'rv_review_complete_running'
              : 'rv_queue_cleared_t';
        return (
            '<div class="panel"><div class="bd rv-done">' +
            '<span class="chip ' +
            (materialBlocked ? 'w' : blockedInfo ? 'b' : 'g') +
            '">' +
            esc(at(chipKey)) +
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
