/*
 * Pearnly AI · ai-review-bulk.js · 客户页审核队列「全部按建议处理」批量确认状态机(J-C)
 *
 * 拆出独立于 ai-review.js 主状态(单文件<500 铁律,同 ai-review-pool.js 先例):按
 * flag_reason 分组算出可批量组(复用 AI.reviewVerdict.groupCanBulk/bulkDecisionTemplate,
 * 与收件箱 ai-review-inbox-flagged.js::runGroupBatch 同一份判定单一事实源,不重造),持有
 * busy/错误态,真正落库调用既有 POST .../decisions:batch 端点(AI.api.batchDecisions,与
 * 收件箱同一份,不写第二套)。危险操作确认走原生 window.confirm(四语文案,同
 * ai-profile.js::root_confirm 先例),不建自定义弹窗组件。
 */
(function () {
    'use strict';

    function create() {
        var st = { busyFlag: null, errKey: null, lastTemplate: null };

        // 未判队列按 flag_reason 分组,只留「组内 >1 张且后端给了安全默认动作、置信度均非
        // 低」的组(AI.reviewVerdict.groupCanBulk 单一事实源)。已判票(entry.decision 或
        // session-local 已定)不计入——它们已经不需要批量。
        function bulkableGroups(queue, local) {
            var byReason = {};
            (queue || []).forEach(function (e) {
                if (AI.reviewQueue.isDecided(e, local && local[e.item_id])) return;
                (byReason[e.flag_reason] = byReason[e.flag_reason] || []).push(e);
            });
            return Object.keys(byReason)
                .map(function (r) {
                    return { flagReason: r, entries: byReason[r] };
                })
                .filter(function (g) {
                    return g.entries.length > 1 && AI.reviewVerdict.groupCanBulk(g.entries);
                });
        }

        // 一步确认(window.confirm 四语文案)→ 通过才发请求;取消 = 零请求,状态不变。
        // onSettle 在 busy 置位后立即调一次(渲染 busy 态),网络落地再调一次(渲染终态),
        // 同 ai-review-pool.js::stage 的回调节奏。
        function confirmAndRun(api, orderId, group, onSettle) {
            if (st.busyFlag) return;
            if (!window.confirm(at('rv_bulk_confirm_msg', { n: group.entries.length }))) return;
            var template = AI.reviewVerdict.bulkDecisionTemplate(group.entries[0]);
            if (!template) return;
            var decisions = group.entries.map(function (e) {
                return Object.assign({ item_id: e.item_id }, template);
            });
            st.busyFlag = group.flagReason;
            st.errKey = null;
            st.lastTemplate = template;
            onSettle(null);
            api.batchDecisions(orderId, decisions)
                .then(function (res) {
                    st.busyFlag = null;
                    onSettle(res);
                })
                .catch(function (err) {
                    st.busyFlag = null;
                    var key = AI.api.mapApiErrorKey(err && err.code);
                    st.errKey = key !== 'err_generic' && at(key) !== key ? key : 'err_generic';
                    onSettle(null);
                });
        }

        return {
            state: function () {
                return st;
            },
            bulkableGroups: bulkableGroups,
            confirmAndRun: confirmAndRun,
        };
    }

    window.AI = window.AI || {};
    window.AI.reviewBulk = { create: create };
})();
