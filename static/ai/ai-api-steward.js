/*
 * Pearnly AI · ai-api-steward.js · 智能管家(B2-M1/B3)八端点的后端调用薄层(拆自 ai-api.js)
 *
 * 单文件<500 行铁律:ai-api.js 已在预算线上,管家端点自成一族、依赖面只有 call 一个
 * 闭包量 —— 同 ai-api-desk.js/ai-api-payroll.js 先例拆出去,调用方感知不到这层拆分。
 *
 * 契约(前缀 /api/ai/steward,网页会话认证,权限比照 /ai):
 *   GET  /status                     → {enabled}
 *   POST /sessions                   → {session_id}
 *   GET  /sessions/{sid}             → {session_id, messages[], current_task_id?}
 *   POST /sessions/{sid}/messages    → {message_id, reply, task_id?, budget?}
 *   GET  /tasks/{tid}                → 左窗任务数据(见 ai-steward-render.js 顶注)
 *   POST /tasks/{tid}/cancel         → 同左窗任务数据(幂等 · 已收尾的原样返回)
 *   POST /authorizations/approve     → {task_id, authorization}(body {token})
 *   POST /authorizations/reject      → 同上(token 走 body 不进 URL/访问日志)
 */
(function (root) {
    'use strict';

    var BASE = '/api/ai/steward';

    function create(call) {
        return {
            // 闸探针(pearnly_ai_steward · tenant 级默认关):闸关也回 200 {enabled:false},
            // 不走 404 —— 照 getDeskStatus 先例,免得闸关用户每开一次 /ai 就吃一条 404。
            getStewardStatus: function () {
                return call('GET', BASE + '/status');
            },
            createStewardSession: function () {
                return call('POST', BASE + '/sessions');
            },
            getStewardSession: function (sessionId) {
                return call('GET', BASE + '/sessions/' + encodeURIComponent(sessionId));
            },
            sendStewardMessage: function (sessionId, text) {
                return call(
                    'POST',
                    BASE + '/sessions/' + encodeURIComponent(sessionId) + '/messages',
                    {
                        text: text,
                    }
                );
            },
            getStewardTask: function (taskId) {
                return call('GET', BASE + '/tasks/' + encodeURIComponent(taskId));
            },
            cancelStewardTask: function (taskId) {
                return call('POST', BASE + '/tasks/' + encodeURIComponent(taskId) + '/cancel');
            },
            // 决断二端点共形(body 只有 token):approve 要 tax.filing.approve,reject 只要
            // view —— 权限差异在后端判,这里不预判(403 由挂载层翻人话)。
            decideStewardAuthz: function (approve, token) {
                return call('POST', BASE + '/authorizations/' + (approve ? 'approve' : 'reject'), {
                    token: token,
                });
            },
        };
    }

    if (typeof module !== 'undefined' && module.exports) module.exports = { create: create };
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiSteward = { create: create };
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
