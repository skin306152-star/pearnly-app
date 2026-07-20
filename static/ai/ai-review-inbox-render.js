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

    // 浏览器本地今天(YYYY-MM-DD):逾期是展示级判断非钱路径,不追时区精度(§5 拍板)。
    function localTodayIso() {
        var t = new Date();
        return (
            t.getFullYear() +
            '-' +
            ('0' + (t.getMonth() + 1)).slice(-2) +
            '-' +
            ('0' + t.getDate()).slice(-2)
        );
    }

    // 到期日 < 今天标红(Canon §三:到期压力是「要你处理」的必带件,此前逾期无任何视觉)。
    function dueLine(order) {
        var d = order.next_due_efiling || order.next_due_paper;
        if (!d) return esc(at('riq_wo_due_none'));
        var txt = esc(at('riq_wo_due', { date: d }));
        return String(d) < localTodayIso() ? '<span class="riq-overdue">' + txt + '</span>' : txt;
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

    // 卡住提示条读未决数(清单 #2):status!=='review' 只说结构性停在 stuck,不说异常票据
    // 还剩几张没裁——口径与 flaggedChipHtml 的 undecided_count 一致,不照总数判断致与徽章矛盾。
    function orderUndecidedTotal(order) {
        return (order.flagged_groups || []).reduce(function (sum, g) {
            return sum + (typeof g.undecided_count === 'number' ? g.undecided_count : g.count || 0);
        }, 0);
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

    // 签批渲染判定(纯函数 · P0-1):order.signoff 是后端投影(单一事实源)。
    //   done   = 已复核 chip(ui.signedNote 乐观刚签,或投影 fresh=!stale)
    //   hidden = 制单人强制态收起(gate.hideSignoff)
    //   stale  = 复核后引擎重跑过数字,需重签(投影 stale)
    //   button = 常态可签
    // 判定以投影优先(正常重跑后签批态能回读点亮),ui.signedNote 只做点击后的乐观补充。
    function signoffMode(order, ui, hideSignoff) {
        ui = ui || {};
        var proj = order.signoff;
        if (ui.signedNote || (proj && !proj.stale)) return 'done';
        if (hideSignoff) return 'hidden';
        return proj && proj.stale ? 'stale' : 'button';
    }

    // 签批 chip / 钮 + stale 提示的 HTML 拼装(判定见 signoffMode)。返回 {btn, staleNote}。
    function signoffCellHtml(order, ui, gate, blocked) {
        var mode = signoffMode(order, ui, gate.hideSignoff);
        if (mode === 'done') {
            var doneText =
                ui.signedNote ||
                at('riq_signoff_done', { actor: AI.format.actorDisplay(order.signoff.actor) });
            return { btn: '<span class="chip g">' + esc(doneText) + '</span>', staleNote: '' };
        }
        if (mode === 'hidden') return { btn: '', staleNote: '' };
        var btn =
            '<button type="button" class="btn sm pri" data-action="riq-signoff" data-wo="' +
            order.work_order_id +
            '"' +
            (blocked || ui.signoffBusy ? ' disabled' : '') +
            '>' +
            esc(ui.signoffBusy ? at('riq_signoff_busy') : at('riq_signoff_btn')) +
            '</button>';
        var staleNote =
            mode === 'stale'
                ? '<p class="riq-signoff-stale">' + esc(at('riq_signoff_stale')) + '</p>'
                : '';
        return { btn: btn, staleNote: staleNote };
    }

    // ui: {signoffBusy, signedNote, archiveBusy, archivedNote, rejectBusy, sodErr,
    //      selfDeclareBusy, selfDeclared, receiptBusy, receiptNote}
    function woActionsHtml(order, ui) {
        ui = ui || {};
        var blocked = order.status !== 'review'; // stuck(还有待裁决)不给签批,避免签个空
        var gate = sodGate(order, ui);
        // 按钮层级(§5 · 2026-07-17):高频动作「复核通过」当主态;「签批冻结」是低频
        // 收尾动作,降回普通钮——此前主态挂在冻结上,把人往终局动作上引。
        var signoff = signoffCellHtml(order, ui, gate, blocked);
        var signoffBtn = signoff.btn;
        var archiveBtn = ui.archivedNote
            ? '<span class="chip g">' + esc(ui.archivedNote) + '</span>'
            : !gate.archiveAllowed
              ? ''
              : '<button type="button" class="btn sm" data-action="riq-archive" data-wo="' +
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
            signoff.staleNote +
            receiptRow +
            sodErr +
            '<div class="riq-sod-strip">' +
            '<span class="note">' +
            esc(at('riq_self_declare_hint')) +
            '</span>' +
            selfDeclareBtn +
            '</div>' +
            (blocked && orderUndecidedTotal(order) > 0
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

    // S3 契约 B(2026-07-17):running 工单不再从队列消失——卡体只显「AI 在跑」状态行
    // (胶囊 + 当前步 + 最后活动),签批/冻结/驳回一律不出:引擎正在重算,签了也是签空。
    function runningBodyHtml(order) {
        return (
            '<div class="note">' +
            AI.format.chipHtml(order.status) +
            ' · ' +
            esc(AI.format.stepLabel(order.current_step)) +
            ' · ' +
            esc(at('wo_last_active', { t: AI.format.relAgo(order.updated_at, Date.now()) })) +
            '</div>'
        );
    }

    function workOrderCardHtml(client, order, ui) {
        ui = ui || {};
        var running = order.status === 'running';
        var reworkChip = order.is_rework
            ? '<span class="chip w">' + esc(at('riq_rework_badge')) + '</span>'
            : '';
        return (
            '<div class="panel riq-wo' +
            (running ? ' riq-running' : '') +
            '" data-wo="' +
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
            (running
                ? runningBodyHtml(order)
                : flaggedChipsHtml(order) + woActionsHtml(order, ui) + rejectFormHtml(order, ui)) +
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
    // 逐张裁决卡的拼装(读值/判据人话/置信度徽标/动作行)拆到 ai-review-inbox-item-render.js
    // (单文件<500 铁律),本文件只管分组头 + 已判折叠的编排。

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

    // 已判项折叠(J-C):isDecided 两分,未判照旧摊开;已判挪进 <details>,展开仍是同一张
    // 裁决卡(AI.reviewInboxItem.card,Accept/Edit/Exclude latest-wins 改判照旧可点),
    // 默认收起不占屏。
    function cardsOf(items, ui, archivedIds) {
        return items
            .map(function (item) {
                return AI.reviewInboxItem.card(item, ui, archivedIds);
            })
            .join('');
    }

    // 分组头人话副行(§5 · 2026-07-17):黑话组名(勾稽红灯/方向不明…)下补一句大白话
    // 说清「为什么要人管 + 该干什么」。flag_reason 可能带冒号后缀(band 等),同
    // flagReasonKey 取冒号前段;词典没这条(如 ocr_error)整行不渲染,不硬编。
    function groupExplHtml(flagReason) {
        var key = 'riq_expl_' + String(flagReason || '').split(':')[0];
        var text = at(key);
        if (text === key) return '';
        return '<div class="riq-expl">' + esc(text) + '</div>';
    }

    function groupHtml(group, ui, archivedIds) {
        ui = ui || {};
        archivedIds = archivedIds || {};
        var actionableCount = group.items.filter(function (item) {
            return !archivedIds[item.work_order_id];
        }).length;
        var canBulk = AI.reviewVerdict.groupCanBulk(group.items);
        var split = AI.reviewQueue.splitByDecision(group.items, ui.local);
        var itemsHtml = cardsOf(split.undecided, ui, archivedIds);
        var decidedHtml = split.decided.length
            ? '<details class="riq-decided-group"><summary>' +
              esc(at('rv_decided_group_summary', { n: split.decided.length })) +
              '</summary><div class="riq-items">' +
              cardsOf(split.decided, ui, archivedIds) +
              '</div></details>'
            : '';
        return (
            '<div class="panel riq-group" data-flag="' +
            esc(group.flagReason) +
            '">' +
            groupHeaderHtml(group, canBulk, ui.busy, actionableCount) +
            groupExplHtml(group.flagReason) +
            '<div class="bd"><div class="riq-items">' +
            itemsHtml +
            '</div>' +
            decidedHtml +
            '</div></div>'
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
        orderUndecidedTotal: orderUndecidedTotal,
        signoffMode: signoffMode,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.reviewInboxRender = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
