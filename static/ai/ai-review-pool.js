/*
 * Pearnly AI · ai-review-pool.js · D2-S9 审核队列第四动作「推 LINE 待问」状态机
 *
 * 拆出独立于 ai-review.js 主状态(避免单文件<500 铁律超线):按 item_id 持有
 * {open, busy, errKey, done},与裁决态(S.local)平行独立、互不干扰——推待问池
 * 不是裁决,不走 A/E/X 乐观回滚那一套。create() 每次 mount() 会话各开一份新实例,
 * 天然隔离「已切走的旧会话回调落地」(调用方仍需按自己的 session 快照判活,见
 * ai-review.js stageToPool 的 S!==session 卫哨,同 decide() 先例)。
 */
(function () {
    'use strict';

    function create() {
        var pool = {};

        function forItem(itemId) {
            if (!pool[itemId]) {
                pool[itemId] = { open: false, busy: false, errKey: null, done: false };
            }
            return pool[itemId];
        }

        // 已在 done/busy 态时忽略(避免重复展开选择面板 / 请求飞行中又开一份)。
        // 返回值供调用方决定要不要重渲染。
        function toggle(itemId) {
            var p = forItem(itemId);
            if (p.done || p.busy) return false;
            p.open = !p.open;
            p.errKey = null;
            return true;
        }

        // onSettle 在 busy 置位后立即调一次(渲染 busy 态),网络落地再调一次(渲染终态)。
        function stage(api, orderId, entry, questionType, onSettle) {
            var payload = AI.reviewQueue.buildStagePayload(entry, questionType);
            if (!payload) return;
            var p = forItem(entry.item_id);
            p.busy = true;
            p.errKey = null;
            onSettle();
            api.stageQuestion(orderId, payload)
                .then(function () {
                    p.busy = false;
                    p.open = false;
                    p.done = true;
                    onSettle();
                })
                .catch(function (err) {
                    p.busy = false;
                    var key = AI.api.mapApiErrorKey(err && err.code);
                    p.errKey = key !== 'err_generic' && at(key) !== key ? key : 'err_generic';
                    onSettle();
                });
        }

        return { forItem: forItem, toggle: toggle, stage: stage };
    }

    window.AI = window.AI || {};
    window.AI.reviewPool = { create: create };
})();
