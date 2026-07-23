/*
 * Pearnly AI · ai-review-inbox-item-render.js · 收件箱单张 flagged 件裁决卡 HTML
 *
 * 拆出独立于 ai-review-inbox-render.js(单文件<500 铁律,同 ai-review-pool.js 先例):
 * 「异常票据」分组里逐张裁决卡(读值/判据人话/置信度徽标/动作行)的拼装收在这,
 * groupHtml(分组头 + 已判折叠)留在主文件。读值表格复用 ai-review-render.js 的
 * fieldRows(effectiveDecision 走 latest-wins 口径),动作按钮定义表也复用同一份
 * (data-action 前缀参数化成 riq-*),不重拼第二套。零 DOM/网络依赖,排在
 * ai-review-inbox-render.js 之前加载。
 */
(function (root) {
    'use strict';

    function esc(s) {
        return AI.state.esc(s);
    }

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

    // 一张 flagged 件的裁决动作行:方向票(kind=sales_doc / flag_reason 前缀命中方向)
    // 走 P/S/N;其余(金额/OCR 质量类)走 Accept/Edit(内联改数)/Exclude——键位/文案取
    // ai-review-render.js 的按钮定义表(同一份,data-action 前缀参数化成 riq-*),只是
    // 脱离单卡聚焦,改成组内行内按钮(btn sm + data-item)。
    function itemActionsHtml(item, itemUi) {
        itemUi = itemUi || {};
        // 佐证件(银行流水/GL/EDC):没有票面可采纳、也不该被「剔除」——单键确认即放行。
        if (AI.reviewQueue.isCorroborationItem(item)) {
            return (
                '<div class="riq-item-actions">' +
                actionRowHtml(AI.reviewRender.CORROBORATION_ACTION_DEFS, item.item_id) +
                viewImgBtn(item) +
                '</div>'
            );
        }
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

    // 裁决卡三件套:读值(fldt)/判据人话(riq-narrative)/置信度徽标(chip)——三者都是
    // isVisible 断言的直接对象,不藏进折叠面板。冻结单的件(frozen)收起全部裁决钮改只读
    // 徽章(清单 #3 · 四态诚实:后端 archive 只读闸会拒,UI 不许先摆出可点的样子),
    // 原图查看是只读动作照留。
    function itemCardHtml(item, itemUi, local, frozen) {
        // J-C · IMG_2647 尸检:此前硬传 null,改数落库后卡片仍显旧 OCR 读数——改读最新裁决
        // (session-local 优先,否则后端投影,同 ai-review-render.js::cardHtml 同一份口径)。
        var effectiveDecision = (local && local.decision) || item.decision;
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
            // 佐证件没有票面钱字段:渲染读值表只会得到一列「—」,四态诚实上是「不适用」
            // 而非「空值」,直接不摆这张表。
            (AI.reviewQueue.isCorroborationItem(item)
                ? ''
                : '<table class="fldt riq-fldt">' +
                  AI.reviewRender.fieldRows(item.ocr_read, effectiveDecision) +
                  '</table>') +
            narrativeHtml(item) +
            actionsHtml +
            '</div>'
        );
    }

    // 便捷包装:groupHtml(ai-review-inbox-render.js)按 {item, ui, archivedIds} 三元组
    // 逐张拼卡,不用每处都手写 itemUi/local/frozen 三个字段的取值表达式。
    function card(item, ui, archivedIds) {
        ui = ui || {};
        archivedIds = archivedIds || {};
        return itemCardHtml(
            item,
            ui.itemUi && ui.itemUi[item.item_id],
            ui.local && ui.local[item.item_id],
            !!archivedIds[item.work_order_id]
        );
    }

    var api = { cardHtml: itemCardHtml, card: card };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.reviewInboxItem = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
