/*
 * Pearnly AI · ai-steward-authz-render.js · 智能管家(B3)写授权卡 + 成本封顶提示拼装
 *
 * 吃两块冻结契约(routes/steward_routes.py · B3 第二段):
 *   授权卡 task.authorization / 决断响应 authorization:
 *     { token, tool, title, risk: write|danger, args, status: pending|approved|rejected|
 *       expired, requested_at, expires_at, decided_by, decided_at }
 *   成本封顶 messages 响应可选键 budget:
 *     { code: steward.budget_session_exceeded|steward.budget_task_exceeded|
 *       steward.budget_tenant_exceeded,
 *       cap_thb, spent_thb }(两位小数字符串,decimal 序列化,前端原样展示不做算术)
 *
 * pending 但已过 expires_at 的卡服务端读侧已折成 expired,本层不自己比时间判状态;
 * 倒计时(remainingMs/countdownLabel)只是给人看的进度,归零由挂载层重拉任务收口。
 * token 只在 DOM data 属性里过手(决断时原样回传 body),不落 localStorage。
 *
 * 上半段零 DOM 零 i18n 纯函数(状态/风险→色族、倒计时、参数行、决断错误码→词条),
 * node(tests/unit/test_ai_steward_authz_render.py)直接 require 断言;下半段拼装依赖
 * 全局 at() 与 AI.state/AI.statesRender —— 同 ai-steward-render.js 的双段先例。
 */
(function (root) {
    'use strict';

    var AUTHZ_STATUSES = ['pending', 'approved', 'rejected', 'expired'];

    // 契约:pending→警告橙(等人来点)/ approved→成功绿 / rejected→错误红 / expired→禁用灰。
    var AUTHZ_FAMILY = { pending: 'warn', approved: 'ok', rejected: 'err', expired: 'off' };

    // 决断端点错误码 → 词条。404/403/409 各自说清"卡怎么了 + 下一步去哪",不糊一句失败。
    var DECIDE_ERR_KEYS = {
        'steward.authz_expired': 'stw_authz_err_expired',
        'steward.authz_used': 'stw_authz_err_used',
        'steward.authz_stale': 'stw_authz_err_stale',
        'steward.authz_mismatch': 'stw_authz_err_mismatch',
        'authz.forbidden': 'stw_authz_err_forbidden',
        'steward.not_found': 'stw_authz_err_notfound',
    };

    var BUDGET_SESSION = 'steward.budget_session_exceeded';
    var BUDGET_TASK = 'steward.budget_task_exceeded';
    var BUDGET_TENANT = 'steward.budget_tenant_exceeded';

    function authzFamily(status) {
        return AUTHZ_FAMILY[status] || 'empty';
    }

    function authzStatusKey(status) {
        return AUTHZ_STATUSES.indexOf(status) >= 0 ? 'stw_authz_' + status : 'stw_authz_unknown';
    }

    // 风险二值闭集(write|danger)。契约外的值按 danger 兜底:写授权卡上宁可吓人一跳,
    // 不给一张风险被淡化的卡(与状态兜「未知」相反 —— 这里少吓 = 放行风险)。
    function riskFamily(risk) {
        return risk === 'write' ? 'warn' : 'err';
    }

    function riskKey(risk) {
        return risk === 'write' ? 'stw_authz_risk_write' : 'stw_authz_risk_danger';
    }

    function remainingMs(expiresAt, nowMs) {
        var t = Date.parse(String(expiresAt || ''));
        if (!isFinite(t)) return 0;
        return Math.max(0, t - (isFinite(nowMs) ? nowMs : Date.now()));
    }

    // 剩余毫秒 → m:ss(倒计时只到分钟级,TTL 默认 5 分钟,不摆小时位)。
    function countdownLabel(ms) {
        var total = Math.max(0, Math.floor(Number(ms) / 1000) || 0);
        var sec = total % 60;
        return Math.floor(total / 60) + ':' + (sec < 10 ? '0' : '') + sec;
    }

    // args 是「工具槽名 → 标量字符串」的平面对象(后端已接地),按键序摆行给人复核。
    function argEntries(args) {
        if (!args || typeof args !== 'object' || Array.isArray(args)) return [];
        return Object.keys(args).map(function (k) {
            return { k: k, v: String(args[k] == null ? '' : args[k]) };
        });
    }

    function decideErrKey(code) {
        return DECIDE_ERR_KEYS[code] || 'err_generic';
    }

    // 会话级超限才给「开新会话继续」的出口(该级按会话计,新会话即重新起算);
    // 任务级出路在 reply 人话里(改小范围再试),租户日额级开新会话也没用 —— 都不给按钮。
    function isSessionBudget(code) {
        return code === BUDGET_SESSION;
    }

    function isBudgetCode(code) {
        return code === BUDGET_SESSION || code === BUDGET_TASK || code === BUDGET_TENANT;
    }

    var pure = {
        AUTHZ_STATUSES: AUTHZ_STATUSES,
        authzFamily: authzFamily,
        authzStatusKey: authzStatusKey,
        riskFamily: riskFamily,
        riskKey: riskKey,
        remainingMs: remainingMs,
        countdownLabel: countdownLabel,
        argEntries: argEntries,
        decideErrKey: decideErrKey,
        isSessionBudget: isSessionBudget,
        isBudgetCode: isBudgetCode,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器拼装(依赖 at()/AI.state/AI.statesRender,node 不调用)=====
    if (!root || typeof root.document === 'undefined') return;

    function esc(s) {
        return AI.state.esc(s);
    }

    function argsHtml(args) {
        var rows = argEntries(args);
        if (!rows.length) return '';
        return (
            '<div class="stw-authz-args-hd">' +
            esc(at('stw_authz_args_hd')) +
            '</div><dl class="stw-authz-args">' +
            rows
                .map(function (r) {
                    return '<dt>' + esc(r.k) + '</dt><dd>' + esc(r.v) + '</dd>';
                })
                .join('') +
            '</dl>'
        );
    }

    // pending 卡的动作区:批准(主按钮)+ 拒绝 + 倒计时。busy 时双双禁用防双击
    //(后端 token 单次单用是硬闸,这里只是别让人白点第二下)。
    function actionsHtml(auth, busy) {
        var dis = busy ? ' disabled' : '';
        var cd = countdownLabel(remainingMs(auth.expires_at));
        return (
            '<div class="stw-authz-actions"><button type="button" class="btn pri" ' +
            'data-action="stw-authz-approve" data-token="' +
            esc(auth.token) +
            '"' +
            dis +
            '>' +
            esc(at('stw_authz_approve')) +
            '</button><button type="button" class="btn" data-action="stw-authz-reject" data-token="' +
            esc(auth.token) +
            '"' +
            dis +
            '>' +
            esc(at('stw_authz_reject')) +
            '</button><span class="stw-authz-cd" id="stwAuthzCd">' +
            esc(at('stw_authz_countdown', { t: cd })) +
            '</span></div>'
        );
    }

    // 授权卡。说清「要做什么(title 后端已人话化)+ 风险 + 参数」,pending 给两个动作,
    // 过期给重来的路,已决断如实盖章 —— 卡的状态永远来自后端,前端不自己翻状态。
    // 决断/取消的错误行由面板层统一渲染(ai-steward-render.js actionErr),卡内不重复。
    function cardHtml(auth, opts) {
        opts = opts || {};
        if (!auth) return '';
        var status = auth.status;
        var head =
            '<div class="stw-authz-hd"><span class="stw-authz-t">' +
            esc(at('stw_authz_hd')) +
            '</span>' +
            AI.statesRender.badgeHtml(authzFamily(status), at(authzStatusKey(status)), {
                pulse: status === 'pending',
            }) +
            AI.statesRender.badgeHtml(riskFamily(auth.risk), at(riskKey(auth.risk))) +
            '</div>';
        var body = '<div class="stw-authz-title">' + esc(auth.title || auth.tool || '') + '</div>';
        body += argsHtml(auth.args);
        if (status === 'pending') {
            body += actionsHtml(auth, !!opts.busy);
        } else if (status === 'expired') {
            body += '<div class="stw-authz-hint">' + esc(at('stw_authz_expired_hint')) + '</div>';
        }
        return '<div class="stw-authz">' + head + body + '</div>';
    }

    // 成本封顶提示(消息脚下):已用/上限如实并排(数字来自后端 decimal 字符串,原样印),
    // 会话级给「开新会话继续」出口 —— reply 人话在气泡里,这块只补机器数与下一步。
    function budgetHtml(budget) {
        if (!budget || !isBudgetCode(budget.code)) return '';
        var action = isSessionBudget(budget.code)
            ? '<button type="button" class="btn sm" data-action="stw-new-session">' +
              esc(at('stw_budget_new_session')) +
              '</button>'
            : '';
        return (
            '<div class="stw-budget">' +
            esc(at('stw_budget_spent', { spent: budget.spent_thb, cap: budget.cap_thb })) +
            action +
            '</div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardAuthzRender = Object.assign(
        { cardHtml: cardHtml, budgetHtml: budgetHtml },
        pure
    );
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
