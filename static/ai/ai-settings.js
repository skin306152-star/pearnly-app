/*
 * Pearnly AI · ai-settings.js · 设置(EN-clients · 侧栏「设置」转正)编排 + HTML 拼装
 *
 * 最薄版(主窗拍板:就三样,不镀金)——语言切换(复用既有 atSetLang/mrpilot_lang 机制,
 * 同 console.js 的 langSeg 先例,视觉复用 .view-toggle/.vt-btn 而非重画一套分段控件)
 * + 当前账号信息(GET /api/me 已有的 email/tenant_name,零新增后端)+ 退出登录
 * (复用 AI.api.logout() + 清 token,回调交给 ai.js,同 AI.gate.mountInvited 的
 * onLogout 先例)。单文件小、编排与拼装未拆(参照 ai-financials.js 同等体量的先例,
 * 未设独立 node 纯函数测试文件——本页无值得单测的业务逻辑,E2E 覆盖交互)。
 *
 * 语言切换后整页 reload(不做局部重渲染):侧栏/多层嵌套视图的文案分散在十余个模块,
 * 局部刷新容易漏掉某个未挂载视图的文案,reload 保证零遗漏——设置页低频操作,
 * reload 的成本可接受(同多数 SaaS 后台的语言切换取舍)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;

    function body() {
        return $('stBody');
    }

    function esc(s) {
        return AI.state.esc(s);
    }

    function langSegHtml() {
        return (
            '<div class="view-toggle" id="stLangSeg">' +
            (window.AII18N.supported || [])
                .map(function (lang) {
                    return (
                        '<button type="button" class="vt-btn' +
                        (lang === window.AII18N.lang ? ' on' : '') +
                        '" data-lang="' +
                        lang +
                        '">' +
                        esc(at('settings_lang_' + lang)) +
                        '</button>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function accountRowHtml(labelKey, value) {
        return (
            '<div class="cell"><div class="lb">' +
            esc(at(labelKey)) +
            '</div><div class="v">' +
            esc(value || '—') +
            '</div></div>'
        );
    }

    function render() {
        var me = S.me;
        body().innerHTML =
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('settings_lang_title')) +
            '</h3></div><div class="bd">' +
            langSegHtml() +
            '</div></div>' +
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('settings_account_title')) +
            '</h3></div><div class="bd"><div class="wosum">' +
            accountRowHtml('settings_account_email', me && me.email) +
            accountRowHtml('settings_account_tenant', me && me.tenant_name) +
            '</div></div></div>' +
            '<button type="button" class="btn" data-action="settings-logout">' +
            esc(at('settings_logout_btn')) +
            '</button>';
    }

    function loadMe() {
        body().innerHTML = AI.state.loadingHtml();
        var session = S;
        S.api
            .getMe()
            .then(function (me) {
                if (S !== session) return;
                S.me = me;
                render();
            })
            .catch(function () {
                if (S !== session) return;
                body().innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body().querySelector('[data-action="retry"]');
                if (btn) btn.onclick = loadMe;
            });
    }

    function switchLang(lang) {
        window.atSetLang(lang);
        window.location.reload();
    }

    function doLogout() {
        S.api
            .logout()
            .catch(function () {
                /* 登出接口失败不阻断本地清态——token 反正要清,服务端会话过期也无妨 */
            })
            .then(function () {
                if (S.onLogout) S.onLogout();
            });
    }

    function onClick(e) {
        var langBtn = e.target.closest('[data-lang]');
        if (langBtn) {
            switchLang(langBtn.getAttribute('data-lang'));
            return;
        }
        if (e.target.closest('[data-action="settings-logout"]')) doLogout();
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        $('v-settings').addEventListener('click', onClick);
    }

    // opts.onLogout 由 ai.js 注入(清 token + 回到登录门面,同 AI.gate.mountInvited 先例)。
    function mount(api, opts) {
        S = { api: api, me: null, onLogout: (opts && opts.onLogout) || null };
        wireOnce();
        loadMe();
    }

    window.AI = window.AI || {};
    window.AI.settings = { mount: mount };
})();
