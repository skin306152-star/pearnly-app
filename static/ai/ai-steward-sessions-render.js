/*
 * Pearnly AI · ai-steward-sessions-render.js · 会话历史侧栏拼装(S1 会话流改版)
 *
 * 吃 GET /api/ai/steward/sessions 的 {sessions: [{session_id, title, last_active_at}]}。
 * 当前会话若还没说过话(服务端列表按「有消息」过滤),列表顶部补一条「新对话」活动项 ——
 * 用户看得见自己现在在哪,不因为还没开口就凭空消失。
 *
 * 行内两个 hover 动作:重命名(就地改成输入框,Enter 存 Esc 撤)与删除(两段式:
 * 先换成「删除/取消」确认排,不弹窗 —— 删的是自己的工作记录,一次误触的代价是可控的,
 * 但仍要一次明确的第二击)。动作在 ai-steward-sessions.js,本层只拼 HTML。
 *
 * 上半段零 DOM 零 i18n 纯函数(标题显示/活动项判定),node 直接 require 断言;
 * 下半段拼装依赖全局 at()/AI.state —— 同 ai-states-render.js 的双段先例。
 */
(function (root) {
    'use strict';

    var MAX_SHOWN_TITLE = 40;

    // 标题显示:空 = 还没说话的新会话,交回调用方用「新对话」词条;超长省尾
    //(标题来自首句,头部才是信息位 —— 与文件名省中间不同)。
    function displayTitle(title) {
        var t = String(title == null ? '' : title)
            .replace(/\s+/g, ' ')
            .trim();
        if (!t) return '';
        return t.length > MAX_SHOWN_TITLE ? t.slice(0, MAX_SHOWN_TITLE - 1) + '…' : t;
    }

    // 列表投影:活动会话不在服务端列表里(还没说话)时,顶部补一条 pseudo 项。
    function listEntries(sessions, activeId) {
        var list = (sessions || []).slice();
        var inList = list.some(function (s) {
            return s && s.session_id === activeId;
        });
        if (activeId && !inList) {
            list.unshift({ session_id: activeId, title: '', draft: true });
        }
        return list;
    }

    var pure = {
        MAX_SHOWN_TITLE: MAX_SHOWN_TITLE,
        displayTitle: displayTitle,
        listEntries: listEntries,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器拼装(依赖 at()/AI.state,node 不调用)=====
    if (!root || typeof root.document === 'undefined') return;

    function esc(s) {
        return AI.state.esc(s);
    }

    var PLUS_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" ' +
        'stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';
    // 折叠/展开会话历史面板(2026-08-07)。图标不随态改变——展开态靠 aria-expanded
    // 说给屏幕阅读器,人眼靠面板本身收没收(同一颗按钮两个方向都点它,不必猜哪颗)。
    var SIDE_TOGGLE_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>';
    var PEN_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5z"/></svg>';

    function renameRowHtml(s) {
        return (
            '<div class="stw-sess-rename"><input id="stwSessRename" class="stw-bar-input" ' +
            'type="text" maxlength="120" value="' +
            esc(s.title || '') +
            '" aria-label="' +
            esc(at('stw_sess_rename')) +
            '" /></div>'
        );
    }

    function confirmRowHtml(s, busy) {
        return (
            '<div class="stw-sess-confirm"><span class="stw-sess-confirm-t">' +
            esc(at('stw_sess_delete_confirm')) +
            '</span><button type="button" class="btn sm danger" data-action="stw-sess-del-yes" ' +
            'data-sid="' +
            esc(s.session_id) +
            '"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(at('stw_sess_confirm_del')) +
            '</button><button type="button" class="btn sm" data-action="stw-sess-del-no"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(at('stw_sess_cancel')) +
            '</button></div>'
        );
    }

    function itemHtml(s, ctx) {
        var active = s.session_id === ctx.activeId;
        if (ctx.renamingId === s.session_id) return renameRowHtml(s);
        if (ctx.deletingId === s.session_id) return confirmRowHtml(s, ctx.busy);
        var title = displayTitle(s.title) || at('stw_sess_untitled');
        // 草稿项(还没说话)没有可改的名字、也没有可删的历史 —— 不给动作钮。
        var acts = s.draft
            ? ''
            : '<span class="stw-sess-acts">' +
              '<button type="button" class="stw-sess-act" data-action="stw-sess-rename" ' +
              'data-sid="' +
              esc(s.session_id) +
              '" title="' +
              esc(at('stw_sess_rename')) +
              '" aria-label="' +
              esc(at('stw_sess_rename')) +
              '">' +
              PEN_SVG +
              '</button>' +
              '<button type="button" class="stw-sess-act del" data-action="stw-sess-del" ' +
              'data-sid="' +
              esc(s.session_id) +
              '" title="' +
              esc(at('stw_sess_delete')) +
              '" aria-label="' +
              esc(at('stw_sess_delete')) +
              '">×</button></span>';
        return (
            '<div class="stw-sess' +
            (active ? ' on' : '') +
            '"><button type="button" class="stw-sess-t" data-action="stw-sess-open" data-sid="' +
            esc(s.session_id) +
            '" title="' +
            esc(s.title || '') +
            '">' +
            esc(title) +
            '</button>' +
            acts +
            '</div>'
        );
    }

    function listHtml(ctx) {
        if (ctx.loading) return AI.state.loadingHtml();
        if (ctx.error) {
            return AI.state.errorHtml({
                title: at('stw_sessions_err_t'),
                sub: at('stw_sessions_err_s'),
                retryLabel: at('stw_retry'),
                retryName: 'stw-sess-reload',
            });
        }
        var entries = listEntries(ctx.sessions, ctx.activeId);
        if (!entries.length) {
            return '<div class="stw-sess-empty">' + esc(at('stw_sessions_empty')) + '</div>';
        }
        return entries
            .map(function (s) {
                return itemHtml(s, ctx);
            })
            .join('');
    }

    // 侧栏骨架:新对话按钮 + 折叠 toggle + 历史列表 + 余额脚注(读得到才显示;余额是
    // 给人看的参考,拿不到就整行不摆,不编数字)。折叠态由 ai-steward-view.js 把
    // ctx.collapsed 同时落在 #stwSide 的 class 上(见该文件 renderSide)——CSS 只认
    // 那个 class,这里的 aria-expanded 只管无障碍语义。
    function sidebarHtml(ctx) {
        ctx = ctx || {};
        var budget = ctx.budget && ctx.budget.session && ctx.budget.session.cap_thb;
        var foot = budget
            ? '<div class="stw-side-foot">' +
              esc(
                  at('stw_budget_line', {
                      spent: AI.format.money(ctx.budget.session.spent_thb),
                      cap: AI.format.money(ctx.budget.session.cap_thb),
                  })
              ) +
              '</div>'
            : '';
        return (
            '<div class="stw-side-hd"><button type="button" class="btn stw-new-chat" ' +
            'data-action="stw-new-session">' +
            PLUS_SVG +
            '<span class="stw-side-label">' +
            esc(at('stw_new_chat')) +
            '</span></button><button type="button" class="stw-side-toggle" ' +
            'data-action="stw-side-toggle" aria-expanded="' +
            (ctx.collapsed ? 'false' : 'true') +
            '" aria-label="' +
            esc(at('stw_side_toggle')) +
            '" title="' +
            esc(at('stw_side_toggle')) +
            '">' +
            SIDE_TOGGLE_SVG +
            '</button></div>' +
            '<div class="stw-side-sec">' +
            esc(at('stw_sessions_hd')) +
            '</div><nav class="stw-sess-list" id="stwSessList">' +
            listHtml(ctx) +
            '</nav>' +
            foot
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardSessionsRender = Object.assign({ sidebarHtml: sidebarHtml }, pure);
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
