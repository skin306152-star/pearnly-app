/*
 * Pearnly AI · ai-review-inbox-render.js · 全所审核收件箱(MC1-b2)纯 HTML 拼装
 *
 * 方案:桌面\pearnly ai\设计稿\MC1b-审核队列与签批闭环-方案.md §2 b2。三分区聚合页
 * 中「待审工单」(工单卡+签批闭环按钮)与「异常票据」(按 flag_reason 跨工单分组的
 * 裁决卡三件套)两块的拼装在本文件;「客户待答」原样复用 ai-client-pool-render.js,
 * 不重拼。零 DOM/网络依赖(同 ai-review-render.js 先例),依赖 window.AI.state/format/
 * reviewQueue/reviewVerdict 与全局 at(),编排在 ai-review-inbox.js。
 */
(function (root) {
    'use strict';

    function esc(s) {
        return AI.state.esc(s);
    }
    function txt(v) {
        return v ? esc(v) : '—';
    }

    // ============ 待审工单卡(签批闭环三步按钮化) ============

    function dueLine(order) {
        var d = order.next_due_efiling || order.next_due_paper;
        return d ? esc(at('riq_wo_due', { date: d })) : esc(at('riq_wo_due_none'));
    }

    // 徽章数只数未决件(清单 #4):裁决落库不改 item.status,引擎重跑前 count 不掉,照显总数
    // 给人「白裁了」错觉。undecided_count 是后端按最新裁决现算的诚实余数——有已裁的追加
    // 「已裁 n」,全裁完转灰底只读;缺字段(旧响应)回落总数,行为同旧版。
    function flaggedChipHtml(g) {
        var key = AI.reviewQueue.flagReasonKey(g.flag_reason);
        var label = key ? at(key) : g.flag_reason;
        var undecided = typeof g.undecided_count === 'number' ? g.undecided_count : g.count;
        var decided = g.decided_count || 0;
        var decidedNote = decided ? ' · ' + esc(at('riq_flag_decided', { n: decided })) : '';
        if (!undecided && decided) {
            return '<span class="chip n">' + esc(label) + decidedNote + '</span>';
        }
        return (
            '<span class="chip ' +
            (g.severity === 'crit' ? 'b' : 'w') +
            '">' +
            undecided +
            ' × ' +
            esc(label) +
            decidedNote +
            '</span>'
        );
    }

    function flaggedChipsHtml(order) {
        if (!order.flagged_groups.length) return '';
        return (
            '<div class="riq-wo-flags">' +
            order.flagged_groups.map(flaggedChipHtml).join('') +
            '</div>'
        );
    }

    // SoD proactive 显隐(F9):order.sod = {enforced, is_preparer, has_independent_review,
    // self_declared}——后端权威投影。制单人在强制态下签批/冻结会撞 422/409,提前收起按钮不让
    // 白点(后端仍是权威闸)。缺 sod 投影(旧调用方/未接线)则不做 proactive 收起,行为不变。
    function sodGate(order, ui) {
        var sod = order.sod;
        var proactive = !!sod;
        var declared = !!(ui.selfDeclared || (sod && sod.self_declared));
        var archiveAllowed =
            !proactive ||
            !sod.enforced ||
            declared ||
            (!sod.is_preparer && sod.has_independent_review);
        return {
            hideSignoff: proactive && sod.enforced && sod.is_preparer,
            archiveAllowed: archiveAllowed,
            declared: declared,
            // 声明制逃生门:强制态下当前登录态过不了冻结闸(制单人自审/缺独立复核)才提示声明,
            // 非强制态沿用旧行为(常显),已声明则收起改显 chip。
            showSelfDeclare: !declared && (!proactive || (sod.enforced && !archiveAllowed)),
        };
    }

    // ui: {signoffBusy, signedNote, archiveBusy, archivedNote, rejectBusy, sodErr,
    //      selfDeclareBusy, selfDeclared, receiptBusy, receiptNote}
    function woActionsHtml(order, ui) {
        ui = ui || {};
        var blocked = order.status !== 'review'; // stuck(还有待裁决)不给签批,避免签个空
        var gate = sodGate(order, ui);
        var signoffBtn = ui.signedNote
            ? '<span class="chip g">' + esc(ui.signedNote) + '</span>'
            : gate.hideSignoff
              ? ''
              : '<button type="button" class="btn sm" data-action="riq-signoff" data-wo="' +
                order.work_order_id +
                '"' +
                (blocked || ui.signoffBusy ? ' disabled' : '') +
                '>' +
                esc(ui.signoffBusy ? at('riq_signoff_busy') : at('riq_signoff_btn')) +
                '</button>';
        var archiveBtn = ui.archivedNote
            ? '<span class="chip g">' + esc(ui.archivedNote) + '</span>'
            : !gate.archiveAllowed
              ? ''
              : '<button type="button" class="btn sm pri" data-action="riq-archive" data-wo="' +
                order.work_order_id +
                '"' +
                (blocked || ui.archiveBusy ? ' disabled' : '') +
                '>' +
                esc(ui.archiveBusy ? at('riq_archive_busy') : at('riq_archive_btn')) +
                '</button>';
        var rejectBtn = ui.archivedNote
            ? ''
            : '<button type="button" class="btn sm no" data-action="riq-reject-open" data-wo="' +
              order.work_order_id +
              '">' +
              esc(at('riq_reject_btn')) +
              '</button>';
        var receiptRow = ui.archivedNote
            ? '<div class="riq-receipt">' +
              '<label class="btn sm">' +
              esc(ui.receiptBusy ? at('riq_receipt_busy') : at('riq_receipt_btn')) +
              '<input type="file" class="riq-receipt-input" data-wo="' +
              order.work_order_id +
              '" style="display:none"' +
              (ui.receiptBusy ? ' disabled' : '') +
              '></label>' +
              (ui.receiptNote ? '<span class="chip g">' + esc(ui.receiptNote) + '</span>' : '') +
              '</div>'
            : '';
        var sodErr = ui.sodErr ? '<p class="riq-sod-err">' + esc(ui.sodErr) + '</p>' : '';
        var selfDeclareBtn = ui.archivedNote
            ? ''
            : gate.declared
              ? '<span class="chip s">' + esc(at('riq_self_declared')) + '</span>'
              : gate.showSelfDeclare
                ? '<button type="button" class="btn sm" data-action="riq-self-declare" data-wo="' +
                  order.work_order_id +
                  '"' +
                  (ui.selfDeclareBusy ? ' disabled' : '') +
                  '>' +
                  esc(at('riq_self_declare_btn')) +
                  '</button>'
                : '';
        return (
            '<div class="riq-wo-steps">' +
            signoffBtn +
            archiveBtn +
            rejectBtn +
            '</div>' +
            receiptRow +
            sodErr +
            '<div class="riq-sod-strip">' +
            '<span class="note">' +
            esc(at('riq_self_declare_hint')) +
            '</span>' +
            selfDeclareBtn +
            '</div>' +
            (blocked
                ? '<p class="riq-wo-blocked-note">' + esc(at('riq_wo_needs_review')) + '</p>'
                : '')
        );
    }

    function rejectFormHtml(order, ui) {
        if (!ui || !ui.rejectOpen) return '';
        return (
            '<div class="riq-reject-form">' +
            '<label>' +
            esc(at('riq_reject_reason_label')) +
            '</label>' +
            '<textarea class="riq-reject-textarea" data-wo="' +
            order.work_order_id +
            '" maxlength="500">' +
            esc(ui.rejectValue || '') +
            '</textarea>' +
            (ui.rejectErr
                ? '<div class="riq-reject-err">' + esc(at('riq_reject_reason_required')) + '</div>'
                : '') +
            '<div class="riq-reject-actions">' +
            '<button type="button" class="btn sm no" data-action="riq-reject-submit" data-wo="' +
            order.work_order_id +
            '"' +
            (ui.rejectBusy ? ' disabled' : '') +
            '>' +
            esc(ui.rejectBusy ? at('riq_reject_busy') : at('riq_reject_submit')) +
            '</button>' +
            '<button type="button" class="btn sm" data-action="riq-reject-cancel" data-wo="' +
            order.work_order_id +
            '">' +
            esc(at('riq_reject_cancel')) +
            '</button>' +
            '</div></div>'
        );
    }

    function workOrderCardHtml(client, order, ui) {
        ui = ui || {};
        var reworkChip = order.is_rework
            ? '<span class="chip w">' + esc(at('riq_rework_badge')) + '</span>'
            : '';
        return (
            '<div class="panel riq-wo" data-wo="' +
            order.work_order_id +
            '">' +
            '<div class="hd"><h3>' +
            esc(
                client.client_name ||
                    at('riq_wo_client_fallback', { id: client.workspace_client_id })
            ) +
            ' <span class="note">' +
            txt(client.client_tax_id) +
            '</span>' +
            reworkChip +
            '<span class="note" style="margin-left:auto">' +
            esc(order.period) +
            ' · ' +
            dueLine(order) +
            '</span></h3></div>' +
            '<div class="bd">' +
            flaggedChipsHtml(order) +
            woActionsHtml(order, ui) +
            rejectFormHtml(order, ui) +
            '</div></div>'
        );
    }

    function woSectionHtml(clients, uiByOrder) {
        if (!clients.length) {
            return AI.state.emptyHtml({ title: at('riq_wo_empty_t'), sub: at('riq_wo_empty_s') });
        }
        return clients
            .map(function (c) {
                return c.orders
                    .map(function (o) {
                        return workOrderCardHtml(c, o, uiByOrder[o.work_order_id]);
                    })
                    .join('');
            })
            .join('');
    }

    // ============ 异常票据(跨工单按 flag_reason 分组的裁决卡三件套) ============
    // 读值表格复用 ai-review-render.js 的 fieldRows(传 null effectiveDecision 走原读数
    // 路径)——收件箱裁决卡与单工单人审卡是同一张五行读值表,不再各拼一份。

    // 判据人话:narrative_key 有值走 i18n 模板,否则诚实回退 flag_reason 原文(verdict.py
    // 顶注约定 + ai-review-verdict.js narrativeOf)。
    function narrativeHtml(item) {
        var n = AI.reviewVerdict.narrativeOf(item.verdict_hint, item.flag_reason);
        var text = n.key ? at(n.key, n.vars) : n.fallbackText;
        return '<p class="riq-narrative">' + esc(text) + '</p>';
    }

    function confidenceChipHtml(item) {
        var c = (item.verdict_hint && item.verdict_hint.confidence) || 'low';
        return (
            '<span class="chip ' +
            AI.reviewVerdict.confidenceChipClass(c) +
            '">' +
            esc(at(AI.reviewVerdict.confidenceLabelKey(c))) +
            '</span>'
        );
    }

    function itemStatusHtml(local) {
        if (!local) return '';
        if (local.state === 'pending')
            return '<span class="chip w">' + esc(at('rv_chip_pending')) + '</span>';
        if (local.state === 'failed') {
            return (
                '<span class="chip b">' +
                esc(local.errKey ? at(local.errKey) : at('err_generic')) +
                '</span>'
            );
        }
        return '';
    }

    // 一张 flagged 件的裁决动作行:方向票(kind=sales_doc / flag_reason 前缀命中方向)
    // 走 P/S/N;其余(金额/OCR 质量类)走 Accept/Edit(内联改数)/Exclude——键位/文案取
    // ai-review-render.js 的按钮定义表(同一份,data-action 前缀参数化成 riq-*),只是
    // 脱离单卡聚焦,改成组内行内按钮(btn sm + data-item)。
    function itemActionsHtml(item, itemUi) {
        itemUi = itemUi || {};
        var isDir = AI.reviewQueue.isDirectionTicket(item);
        if (isDir) {
            return (
                '<div class="riq-item-actions">' +
                actionRowHtml(AI.reviewRender.DIRECTION_ACTION_DEFS, item.item_id) +
                viewImgBtn(item) +
                '</div>'
            );
        }
        if (itemUi.editing) {
            return (
                '<div class="riq-item-actions riq-item-recalc">' +
                '<input class="riq-vat-input" type="text" inputmode="decimal" data-item="' +
                item.item_id +
                '" value="' +
                esc(itemUi.editValue || '') +
                '">' +
                actionBtn({ action: 'riq-recalc-submit', key: 'rv_key_edit', kbd: 'Enter' }, item) +
                (itemUi.editErr
                    ? '<span class="riq-item-err">' + esc(at('rv_edit_vat_required')) + '</span>'
                    : '') +
                '</div>'
            );
        }
        return (
            '<div class="riq-item-actions">' +
            actionRowHtml(AI.reviewRender.AMOUNT_ACTION_DEFS, item.item_id) +
            viewImgBtn(item) +
            '</div>'
        );
    }

    function actionBtn(def, item) {
        return AI.reviewRender.actionButton(def, {
            actionPrefix: 'riq-',
            btnClass: 'btn sm',
            itemId: item.item_id,
        });
    }

    function actionRowHtml(defs, itemId) {
        return defs
            .map(function (def) {
                return actionBtn(def, { item_id: itemId });
            })
            .join('');
    }

    function viewImgBtn(item) {
        if (!item.file_ref) return '';
        return (
            '<button type="button" class="btn sm" data-action="riq-view-img" data-wo="' +
            item.work_order_id +
            '" data-item="' +
            item.item_id +
            '">' +
            esc(at('riq_view_img_btn')) +
            '</button>'
        );
    }

    // 裁决卡三件套:读值(fldt)/判据人话(riq-narrative)/置信度徽标(chip)——三者都是
    // isVisible 断言的直接对象,不藏进折叠面板。冻结单的件(frozen)收起全部裁决钮改只读
    // 徽章(清单 #3 · 四态诚实:后端 archive 只读闸会拒,UI 不许先摆出可点的样子),
    // 原图查看是只读动作照留。
    function itemCardHtml(item, itemUi, local, frozen) {
        var doneChip =
            local && local.state && local.state !== 'pending' && local.state !== 'failed'
                ? '<span class="chip g">' + esc(at('rv_chip_accepted')) + '</span>'
                : '';
        var actionsHtml = frozen
            ? '<div class="riq-item-actions"><span class="chip s">' +
              esc(at('riq_item_frozen')) +
              '</span>' +
              viewImgBtn(item) +
              '</div>'
            : itemActionsHtml(item, itemUi || {});
        return (
            '<div class="riq-item" data-item="' +
            item.item_id +
            '">' +
            '<div class="riq-item-hd">' +
            '<span class="riq-item-file">' +
            esc(AI.reviewQueue.fileName(item.file_ref)) +
            '</span>' +
            confidenceChipHtml(item) +
            itemStatusHtml(local) +
            doneChip +
            '<span class="note" style="margin-left:auto">' +
            esc(item.client_name) +
            ' · ' +
            esc(item.period) +
            '</span>' +
            '</div>' +
            '<table class="fldt riq-fldt">' +
            AI.reviewRender.fieldRows(item.ocr_read, null) +
            '</table>' +
            narrativeHtml(item) +
            actionsHtml +
            '</div>'
        );
    }

    // actionableCount = 组内未冻结件数:批量/排除按钮只对它们生效,全冻结的组两钮都收,
    // 头部只留只读徽章(不给「60 张待批量」的假承诺)。
    function groupHeaderHtml(group, canBulk, busy, actionableCount) {
        var key = AI.reviewQueue.flagReasonKey(group.flagReason);
        var label = key ? at(key) : group.flagReason;
        var sevCls = group.severity === 'crit' ? 'b' : 'w';
        var bulkPill =
            actionableCount === 0
                ? '<span class="chip s">' + esc(at('riq_item_frozen')) + '</span>'
                : canBulk
                  ? '<button type="button" class="btn pri riq-group-bulk" data-action="riq-bulk" data-flag="' +
                    esc(group.flagReason) +
                    '"' +
                    (busy ? ' disabled' : '') +
                    '>' +
                    esc(
                        busy
                            ? at('riq_bulk_busy')
                            : at('riq_group_hd_bulk', { n: actionableCount, reason: label })
                    ) +
                    ' <span class="kbd">A</span></button>'
                  : '<span class="riq-group-manual">' +
                    esc(at('riq_group_hd_manual', { n: group.items.length, reason: label })) +
                    '</span>';
        var excludeBtn =
            actionableCount === 0
                ? ''
                : '<button type="button" class="btn sm" data-action="riq-exclude-all" data-flag="' +
                  esc(group.flagReason) +
                  '"' +
                  (busy ? ' disabled' : '') +
                  '>' +
                  esc(at('riq_group_exclude_all')) +
                  ' <span class="kbd">X</span></button>';
        return (
            '<div class="hd riq-group-hd">' +
            '<h3><span class="chip ' +
            sevCls +
            '">' +
            group.items.length +
            '</span>' +
            bulkPill +
            '<span class="note" style="margin-left:auto">' +
            excludeBtn +
            '</span></h3></div>'
        );
    }

    function groupHtml(group, ui, archivedIds) {
        ui = ui || {};
        archivedIds = archivedIds || {};
        var actionableCount = group.items.filter(function (item) {
            return !archivedIds[item.work_order_id];
        }).length;
        var canBulk = AI.reviewVerdict.groupCanBulk(group.items);
        var itemsHtml = group.items
            .map(function (item) {
                return itemCardHtml(
                    item,
                    ui.itemUi && ui.itemUi[item.item_id],
                    ui.local && ui.local[item.item_id],
                    !!archivedIds[item.work_order_id]
                );
            })
            .join('');
        return (
            '<div class="panel riq-group" data-flag="' +
            esc(group.flagReason) +
            '">' +
            groupHeaderHtml(group, canBulk, ui.busy, actionableCount) +
            '<div class="bd"><div class="riq-items">' +
            itemsHtml +
            '</div></div></div>'
        );
    }

    function flaggedSectionHtml(groups, uiByFlag, archivedIds) {
        if (!groups.length) {
            return AI.state.emptyHtml({
                title: at('riq_flagged_empty_t'),
                sub: at('riq_flagged_empty_s'),
            });
        }
        return groups
            .map(function (g) {
                return groupHtml(g, uiByFlag[g.flagReason], archivedIds);
            })
            .join('');
    }

    var api = {
        woSectionHtml: woSectionHtml,
        flaggedSectionHtml: flaggedSectionHtml,
        workOrderCardHtml: workOrderCardHtml,
        groupHtml: groupHtml,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.reviewInboxRender = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
