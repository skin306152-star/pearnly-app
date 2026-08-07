/*
 * Pearnly AI · ai-steward-chat-render.js · 会话流外壳 + 输入条(S1 改版)
 *
 * 两块:①会话页外壳(会话侧栏 + 主列:页头/消息流/输入条,≤800px 侧栏收成抽屉);
 * ②输入条(自动长高 textarea + 回形针 + 发送/停止一颗键)。消息流本体在
 * ai-steward-flow-render.js,侧栏在 ai-steward-sessions-render.js。
 *
 * 发送键的三形态由挂载层判定后传入(mode):
 *   send        平时(能不能点由送出闸 syncSendGate 动态定)
 *   stop        当前任务在跑且可取消 → 点了停任务
 *   stop-locked 在跑的写活(后端 409 不可停)→ 键诚实置灰 + title 说为什么
 *
 * 上半段零 DOM 零 i18n 纯函数(角色→气泡类、送出态闭集、可送出判据),
 * node 直接 require 断言;下半段拼装依赖全局 at()/AI.state —— 双段先例同前。
 */
(function (root) {
    'use strict';

    var MSG_ROLES = ['user', 'steward'];
    // 本地送出态(不是后端字段):optimistic 上屏的用户气泡在 sending→sent/failed 之间走,
    // 失败留在原地可重发,不静默吞掉用户打的字。
    var SEND_STATES = ['sent', 'sending', 'failed'];

    // 发送键形态闭集。集合外的值按 send 兜底 —— 键不能消失,消失=没法说话。
    var SEND_MODES = ['send', 'stop', 'stop-locked'];

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

    function sendMode(mode) {
        return SEND_MODES.indexOf(mode) >= 0 ? mode : 'send';
    }

    var pure = {
        MSG_ROLES: MSG_ROLES,
        SEND_STATES: SEND_STATES,
        SEND_MODES: SEND_MODES,
        roleClass: roleClass,
        sendState: sendState,
        normalizeText: normalizeText,
        canSend: canSend,
        sendMode: sendMode,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器拼装(依赖 at()/AI.state,node 不调用)=====
    if (!root || typeof root.document === 'undefined') return;

    function esc(s) {
        return AI.state.esc(s);
    }

    var SEND_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" ' +
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M12 19V5M5 12l7-7 7 7"/></svg>';
    var STOP_SVG =
        '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
        '<rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
    var MENU_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
        'stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>';

    // 会话页外壳。侧栏/页头标题/消息流/输入条四个坑位由挂载层分别填 ——
    // 整壳只画一次,之后各坑独立重画,不互相冲(输入框里打了一半的字是不可再生资源)。
    function shellHtml() {
        return (
            '<div class="stw-chat">' +
            '<div class="stw-scrim" id="stwScrim" hidden></div>' +
            '<aside class="stw-side" id="stwSide"></aside>' +
            '<div class="stw-chat-main">' +
            '<header class="stw-chat-hd">' +
            '<button type="button" class="stw-menu-btn" id="stwMenuBtn" data-action="stw-drawer" ' +
            'aria-label="' +
            esc(at('stw_open_sessions')) +
            '">' +
            MENU_SVG +
            '</button>' +
            '<div class="stw-chat-title" id="stwChatTitle"></div>' +
            '<span class="stw-chat-tag">' +
            esc(at('stw_title')) +
            '</span></header>' +
            '<div class="stw-feed-wrap" id="stwFeedWrap">' +
            '<div class="stw-feed" id="stwFeed"></div></div>' +
            '<div class="stw-composer-wrap"><div class="stw-composer" id="stwComposer"></div></div>' +
            '</div></div>'
        );
    }

    function sendBtnHtml(mode) {
        var m = sendMode(mode);
        if (m === 'stop') {
            return (
                '<button type="button" class="stw-send-btn stop" id="stwSendBtn" ' +
                'data-action="stw-stop" aria-label="' +
                esc(at('stw_stop')) +
                '" title="' +
                esc(at('stw_stop')) +
                '">' +
                STOP_SVG +
                '</button>'
            );
        }
        if (m === 'stop-locked') {
            return (
                '<button type="button" class="stw-send-btn stop" id="stwSendBtn" disabled ' +
                'aria-label="' +
                esc(at('stw_stop_locked')) +
                '" title="' +
                esc(at('stw_stop_locked')) +
                '">' +
                STOP_SVG +
                '</button>'
            );
        }
        // 可不可点由 syncSendGate 按送出闸动态设,初始按禁用画(空输入送不出去)。
        return (
            '<button type="button" class="stw-send-btn" id="stwSendBtn" data-action="stw-send" ' +
            'disabled aria-label="' +
            esc(at('stw_send')) +
            '" title="' +
            esc(at('stw_send')) +
            '">' +
            SEND_SVG +
            '</button>'
        );
    }

    // 输入条。ctx = { busy, errText, attach(附件盘视图), mode(发送键形态), value(重画时
    // 保住已打的字) }。附件口读不到限额时回形针整个不摆(点了必失败的按钮更糟)。
    function composerHtml(ctx) {
        ctx = ctx || {};
        var attach = ctx.attach || {};
        var AR = AI.stewardAttachRender;
        var err = ctx.errText ? '<div class="stw-err">' + esc(ctx.errText) + '</div>' : '';
        var note = at(attach.limits ? 'stw_composer_note_files' : 'stw_composer_note');
        return (
            err +
            '<div class="stw-comp-card">' +
            AR.trayHtml(attach) +
            '<div class="stw-comp-row">' +
            AR.pickerHtml(attach) +
            '<textarea id="stwInput" class="stw-input" rows="1" placeholder="' +
            esc(at(attach.limits ? 'stw_input_ph_files' : 'stw_input_ph')) +
            '"' +
            (ctx.busy ? ' disabled' : '') +
            '>' +
            esc(ctx.value || '') +
            '</textarea>' +
            sendBtnHtml(ctx.mode) +
            '</div></div>' +
            '<div class="stw-comp-note">' +
            esc(note) +
            '</div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardChatRender = Object.assign(
        {
            shellHtml: shellHtml,
            composerHtml: composerHtml,
            sendBtnHtml: sendBtnHtml,
        },
        pure
    );
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
