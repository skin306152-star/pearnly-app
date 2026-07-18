/*
 * Pearnly AI · ai-review-fold-render.js · 客户页审核队列顶部/尾部信息条(J-C)
 *
 * 两块拼装,都是「主聚焦卡片之外的队列级 chrome」,不属于卡片本身:
 *  - decidedGroupHtml:已判票折叠分组(原生 <details>,不写手工 toggle 状态)——单张聚焦流
 *    (ai-review.js)只走未判票,已判票挪出主流程后靠这里"能看见、能展开、能改判"
 *    (J 闸实锤:Zihao 审完 70 张离开再回来,已判票的 P/S/X 按钮全活着、队列从头重摆)。
 *  - bulkBannerHtml:「全部按建议处理」批量确认横幅(J-C · 客户页版,复用收件箱同一套
 *    AI.reviewVerdict 判定策略与 decisions:batch 端点,不写第二套;真正的批量状态机在
 *    ai-review-bulk.js)。
 *
 * 零 DOM/网络依赖,依赖 window.AI.state/format/reviewQueue,排在 ai-review.js 之前加载。
 */
(function () {
    'use strict';

    function esc(s) {
        return AI.state.esc(s);
    }

    function resultLabel(entry) {
        var key = AI.reviewQueue.decisionChipKey(entry.decision);
        return key ? at(key) : '';
    }

    function decidedRowHtml(entry) {
        var actor = AI.format.actorDisplay(entry.decision && entry.decision.actor);
        return (
            '<div class="rv-decided-row" data-item="' +
            entry.item_id +
            '">' +
            '<span class="rv-decided-row-file">' +
            esc(AI.reviewQueue.fileName(entry.file_ref)) +
            '</span>' +
            '<span class="rv-decided-row-by">' +
            esc(at('rv_decided_row', { actor: actor, result: resultLabel(entry) })) +
            '</span>' +
            '<button type="button" class="btn sm" data-action="rv-revisit" data-item="' +
            entry.item_id +
            '">' +
            esc(at('rv_revisit_btn')) +
            '</button>' +
            '</div>'
        );
    }

    // entries 空(全未判 / 尚无历史裁决)→ 不渲染,折叠组不占位。
    function decidedGroupHtml(entries) {
        if (!entries || !entries.length) return '';
        return (
            '<details class="rv-decided-group">' +
            '<summary>' +
            esc(at('rv_decided_group_summary', { n: entries.length })) +
            '</summary>' +
            '<div class="rv-decided-list">' +
            entries.map(decidedRowHtml).join('') +
            '</div></details>'
        );
    }

    function flagLabel(reason) {
        var key = AI.reviewQueue.flagReasonKey(reason);
        return key ? at(key) : reason;
    }

    // groups = AI.reviewBulk.create().bulkableGroups() 算好的可批量组(通常 0~1 组)。
    // busyFlag 命中的组按钮转「处理中…」禁用,其余组仍可点(不同 flag_reason 互不阻塞)。
    function bulkBannerHtml(groups, busyFlag) {
        if (!groups || !groups.length) return '';
        return (
            '<div class="rv-bulk-banner">' +
            groups
                .map(function (g) {
                    var busy = busyFlag === g.flagReason;
                    return (
                        '<button type="button" class="btn pri sm" data-action="rv-bulk-run" data-flag="' +
                        esc(g.flagReason) +
                        '"' +
                        (busy ? ' disabled' : '') +
                        '>' +
                        esc(
                            busy
                                ? at('riq_bulk_busy')
                                : at('riq_group_hd_bulk', {
                                      n: g.entries.length,
                                      reason: flagLabel(g.flagReason),
                                  })
                        ) +
                        '</button>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function bulkConfirmHtml(group) {
        if (!group) return '';
        return (
            '<div class="pkg-mask on enter rv-confirm-mask">' +
            '<div class="pkg-modal rv-confirm-modal" role="dialog" aria-modal="true" aria-labelledby="rvConfirmTitle">' +
            '<div class="mh"><div><h3 id="rvConfirmTitle">' +
            esc(at('rv_bulk_confirm_title')) +
            '</h3></div><button type="button" class="mclose" data-action="rv-bulk-cancel" aria-label="' +
            esc(at('intake_form_cancel')) +
            '">×</button></div><div class="mb"><p>' +
            esc(at('rv_bulk_confirm_msg', { n: group.entries.length })) +
            '</p><div class="rv-confirm-actions">' +
            '<button type="button" class="btn" data-action="rv-bulk-cancel">' +
            esc(at('intake_form_cancel')) +
            '</button><button type="button" class="btn pri" data-action="rv-bulk-confirm">' +
            esc(at('rv_bulk_confirm_btn', { n: group.entries.length })) +
            '</button></div></div></div></div>'
        );
    }

    window.AI = window.AI || {};
    window.AI.reviewFoldRender = {
        decidedGroupHtml: decidedGroupHtml,
        bulkBannerHtml: bulkBannerHtml,
        bulkConfirmHtml: bulkConfirmHtml,
    };
})();
