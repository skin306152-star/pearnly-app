/*
 * Pearnly AI · ai-steward-chat-render.js · 智能管家(B2-M1)右窗对话流 + 工作台命令条
 *
 * 两处是同一件事的两个尺寸:命令条是「收起态」的输入口(工作台顶部,只有一行输入 +
 * 高频 chips),对话流是「展开态」(#/steward)。快捷 chips 的闭集两处共用一份,
 * 不各写一份文案(改一处漂一处是碎片化的起手式)。
 *
 * 上半段零 DOM 零 i18n 纯函数(角色→气泡类、送出态闭集、可送出判据、chips 闭集),
 * node 直接 require 断言;下半段拼装依赖全局 at()/AI.state —— 同 ai-states-render.js
 * 的双段先例。管家气泡的正文全部来自后端返回的 reply,本层不生成任何业务措辞。
 */
(function (root) {
    'use strict';

    var MSG_ROLES = ['user', 'steward'];
    // 本地送出态(不是后端字段):optimistic 上屏的用户气泡在 sending→sent/failed 之间走,
    // 失败留在原地可重发,不静默吞掉用户打的字。
    var SEND_STATES = ['sent', 'sending', 'failed'];

    // 高频快捷问法闭集(工作台命令条 + 对话空态各用一次)。四条都是能被参数接地的问法
    // (期间/状态/天数),不放「SM 这期做到哪了」这类写死客户名的——不是每个租户都有 SM。
    var QUICK_KEYS = [
        'stw_quick_missing',
        'stw_quick_review',
        'stw_quick_pushfail',
        'stw_quick_progress',
    ];

    function roleClass(role) {
        return role === 'user' ? 'me' : 'agent';
    }

    function sendState(state) {
        return SEND_STATES.indexOf(state) >= 0 ? state : 'sent';
    }

    function normalizeText(text) {
        return String(text == null ? '' : text).trim();
    }

    // 空白串与"上一句还在路上"都不许再送:重复送出会在后端多开一个任务。
    function canSend(text, busy) {
        return !busy && normalizeText(text).length > 0;
    }

    var pure = {
        MSG_ROLES: MSG_ROLES,
        SEND_STATES: SEND_STATES,
        QUICK_KEYS: QUICK_KEYS,
        roleClass: roleClass,
        sendState: sendState,
        normalizeText: normalizeText,
        canSend: canSend,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器拼装(依赖 at()/AI.state,node 不调用)=====
    if (!root || typeof root.document === 'undefined') return;

    function esc(s) {
        return AI.state.esc(s);
    }

    function chipsHtml() {
        return (
            '<div class="stw-chips">' +
            QUICK_KEYS.map(function (k) {
                var label = at(k);
                return (
                    '<button type="button" class="chip stw-chip" data-action="stw-quick" data-text="' +
                    esc(label) +
                    '">' +
                    esc(label) +
                    '</button>'
                );
            }).join('') +
            '</div>'
        );
    }

    // 工作台顶部命令条(收起态)。闸关时整条由 ai-steward-bar.js 不渲染,不是靠这里判空。
    function barHtml() {
        return (
            '<div class="stw-bar-row"><input id="stwBarInput" class="stw-bar-input" type="text" ' +
            'placeholder="' +
            esc(at('stw_bar_ph')) +
            '" /><button type="button" class="btn pri sm" data-action="stw-bar-go">' +
            esc(at('stw_bar_go')) +
            '</button></div>' +
            chipsHtml()
        );
    }

    function msgFootHtml(msg) {
        var state = sendState(msg.state);
        if (state === 'sending') {
            return (
                '<div class="stw-msg-foot">' +
                AI.statesRender.dotsHtml('off') +
                esc(at('stw_msg_sending')) +
                '</div>'
            );
        }
        if (state === 'failed') {
            return (
                '<div class="stw-msg-foot">' +
                AI.statesRender.badgeHtml('err', at('stw_msg_failed')) +
                '<button type="button" class="stw-linkbtn" data-action="stw-resend" data-mid="' +
                esc(msg.local_id || '') +
                '">' +
                esc(at('stw_msg_resend')) +
                '</button></div>'
            );
        }
        // 管家回复带 task_id:给一个回到那条任务的入口(一个会话里会有多条任务,
        // 点旧消息能把左窗切回那次执行)。
        if (msg.task_id) {
            return (
                '<div class="stw-msg-foot"><button type="button" class="stw-linkbtn" ' +
                'data-action="stw-open-task" data-tid="' +
                esc(msg.task_id) +
                '">' +
                esc(at('stw_open_task')) +
                '</button></div>'
            );
        }
        return '';
    }

    function msgHtml(msg) {
        var cls = roleClass(msg.role);
        // 超限轮的回复气泡下面挂预算块(已用/上限 + 会话级的「开新会话」出口):
        // reply 人话说为什么停,这块给数字和下一步 —— 两者都来自后端,本层不算钱。
        var budget = msg.budget ? AI.stewardAuthzRender.budgetHtml(msg.budget) : '';
        return (
            '<div class="stw-msg ' +
            cls +
            '"><div class="stw-who">' +
            esc(at(msg.role === 'user' ? 'stw_you' : 'stw_agent')) +
            '</div><div class="stw-bubble">' +
            esc(msg.text || '') +
            msgFootHtml(msg) +
            '</div>' +
            budget +
            '</div>'
        );
    }

    // 空态指路:不摆空白,直接把四条能问的话摆出来(四态诚实 · 空态必须指路)。
    function emptyFeedHtml() {
        return (
            '<div class="stw-feed-empty"><div class="stw-feed-empty-t">' +
            esc(at('stw_feed_empty_t')) +
            '</div><div class="stw-feed-empty-s">' +
            esc(at('stw_feed_empty_s')) +
            '</div>' +
            chipsHtml() +
            '</div>'
        );
    }

    function feedHtml(messages) {
        var list = messages || [];
        if (!list.length) return emptyFeedHtml();
        return '<div class="stw-feed">' + list.map(msgHtml).join('') + '</div>';
    }

    function composerHtml(ctx) {
        var busy = !!(ctx && ctx.busy);
        var err = ctx && ctx.errText ? '<div class="stw-err">' + esc(ctx.errText) + '</div>' : '';
        return (
            '<div class="stw-composer">' +
            err +
            '<div class="stw-bar-row"><input id="stwInput" class="stw-bar-input" type="text" ' +
            'placeholder="' +
            esc(at('stw_input_ph')) +
            '"' +
            (busy ? ' disabled' : '') +
            ' /><button type="button" class="btn pri sm" data-action="stw-send"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(at('stw_send')) +
            '</button></div><div class="stw-composer-note">' +
            esc(at('stw_composer_note')) +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardChatRender = Object.assign(
        {
            barHtml: barHtml,
            chipsHtml: chipsHtml,
            feedHtml: feedHtml,
            composerHtml: composerHtml,
        },
        pure
    );
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
