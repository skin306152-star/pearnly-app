/*
 * Pearnly AI · ai-settings.js · 设置(语言 + 账号 + 退出)· 左下角用户块浮层
 *
 * 2026-07-26 从独立侧栏页搬进浮层(Zihao 拍板):设置是三样低频动作,占一条主导航
 * 位不划算——收进用户块下,跟主流 SaaS 的头像菜单同位置,用户不用学新地方。
 * 原 #/settings 路由与 v-settings 页面一并撤掉(见 ai-router.js 顶注)。
 *
 * 本模块自己拥有触发器与浮层:ai.js 只调一次 mountUserMenu(api, opts),开关/取数/
 * 外部点击关闭/Esc 关闭都在这儿——省得外壳替它记浮层状态,两处状态必漂。
 *
 * 语言切换后整页 reload(不做局部重渲染):侧栏/多层嵌套视图的文案分散在十余个模块,
 * 局部刷新容易漏掉某个未挂载视图的文案,reload 保证零遗漏——低频操作,成本可接受。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;

    function pop() {
        return $('userPop');
    }
    function trigger() {
        return $('footUser');
    }
    function body() {
        return $('stBody');
    }

    function esc(s) {
        return AI.state.esc(s);
    }

    function isOpen() {
        return !pop().hasAttribute('hidden');
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

    function close() {
        pop().setAttribute('hidden', '');
        trigger().setAttribute('aria-expanded', 'false');
    }

    // 每次打开都重拉 /api/me:浮层生命周期短,拿陈旧的邮箱/事务所名冒充当前值不诚实。
    function open() {
        pop().removeAttribute('hidden');
        trigger().setAttribute('aria-expanded', 'true');
        loadMe();
    }

    function onTriggerClick(e) {
        e.stopPropagation();
        if (isOpen()) close();
        else open();
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
                close();
                if (S.onLogout) S.onLogout();
            });
    }

    function onPopClick(e) {
        e.stopPropagation();
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
        trigger().addEventListener('click', onTriggerClick);
        pop().addEventListener('click', onPopClick);
        document.addEventListener('click', function () {
            if (isOpen()) close();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && isOpen()) {
                close();
                trigger().focus();
            }
        });
    }

    // ai.js 每次 renderChrome 都调:api 换新(重登录)时要跟着换,监听只挂一次。
    // opts.onLogout 由 ai.js 注入(清 token + 回登录门面,同 AI.gate.mountInvited 先例)。
    function mountUserMenu(api, opts) {
        S = { api: api, me: null, onLogout: (opts && opts.onLogout) || null };
        wireOnce();
    }

    window.AI = window.AI || {};
    window.AI.settings = { mountUserMenu: mountUserMenu };
})();
