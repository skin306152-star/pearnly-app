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

    // 双栏骨架(左=执行状态,右=对话)。挂载层只管往两个坑里填,不在编排文件里拼 HTML。
    function shellHtml() {
        return (
            '<div class="stw-grid"><section class="stw-col stw-left"><h3 class="stw-col-hd">' +
            esc(at('stw_pane_task')) +
            '</h3><div id="stwLeft"></div></section><section class="stw-col stw-right">' +
            '<h3 class="stw-col-hd">' +
            esc(at('stw_pane_chat')) +
            '</h3><div id="stwRight"></div></section></div>'
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
        // 这一轮带的原件永久留在气泡下面(会话重建时后端把 attachments 一并回来)。
        // 纯文件手势下 text 是空串,气泡本体不渲染 —— 否则是一个空框吊着几个文件。
        var files = AI.stewardAttachRender.bubbleFilesHtml(msg.attachments);
        var foot = msgFootHtml(msg);
        var bubble =
            msg.text || !files
                ? '<div class="stw-bubble">' + esc(msg.text || '') + foot + '</div>'
                : foot;
        return (
            '<div class="stw-msg ' +
            cls +
            '"><div class="stw-who">' +
            esc(at(msg.role === 'user' ? 'stw_you' : 'stw_agent')) +
            '</div>' +
            files +
            bubble +
            budget +
            '</div>'
        );
    }

    // 空态指路 = 直接把四条能问的话摆成可点的 chips。此前还压着一个标题(「还没说话」——
    // 在评价用户,不给出路)和一行把同样两条问法再写一遍的说明文字:三层说同一件事,而
    // 唯一能点的只有 chips。留 chips 就够。
    function emptyFeedHtml() {
        return '<div class="stw-feed-empty">' + chipsHtml() + '</div>';
    }

    function feedHtml(messages) {
        var list = messages || [];
        if (!list.length) return emptyFeedHtml();
        return '<div class="stw-feed">' + list.map(msgHtml).join('') + '</div>';
    }

    // ctx.attach 是附件盘视图(AI.stewardAttach.view());没有附件口时它是 null,
    // composer 退回纯文字形态 —— 不摆一个点了必失败的回形针。
    function composerHtml(ctx) {
        ctx = ctx || {};
        var busy = !!ctx.busy;
        var attach = ctx.attach || {};
        var AR = AI.stewardAttachRender;
        // 还在传就不许送:排队送等于把「立即应承」改成等 30 秒(契约不能这么改)。
        var blocked = busy || AR.hasUploading(attach.chips);
        var err = ctx.errText ? '<div class="stw-err">' + esc(ctx.errText) + '</div>' : '';
        // 注脚只说输入框自己给不出的那件事(文件能拖能粘)。没有附件口就没什么可补的 ——
        // 「会改数据的要先批准」已经写在页头,注脚再说一遍就是同屏第二遍。
        var note = attach.limits
            ? '<div class="stw-composer-note">' + esc(at('stw_composer_note_files')) + '</div>'
            : '';
        return (
            '<div class="stw-composer">' +
            err +
            AR.trayHtml(attach) +
            '<div class="stw-bar-row">' +
            AR.pickerHtml(attach) +
            '<input id="stwInput" class="stw-bar-input" type="text" placeholder="' +
            esc(at(attach.limits ? 'stw_input_ph_files' : 'stw_input_ph')) +
            '"' +
            (busy ? ' disabled' : '') +
            ' /><button type="button" class="btn pri sm" data-action="stw-send"' +
            (blocked ? ' disabled' : '') +
            '>' +
            esc(at('stw_send')) +
            '</button></div>' +
            note +
            '</div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardChatRender = Object.assign(
        {
            barHtml: barHtml,
            shellHtml: shellHtml,
            chipsHtml: chipsHtml,
            feedHtml: feedHtml,
            composerHtml: composerHtml,
        },
        pure
    );
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
