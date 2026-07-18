/* Pearnly DMS · 启动入口(闸判定 + i18n 应用 + 壳导航)· 移植 /ai boot 范式。
 * 闸行为:启动调门禁探针(GET /api/dms/session · 只跑入口守卫),就地渲染两种门面——
 *   无 token 或 401 → 登录卡;token 有效但探针 404/403(未受邀/非 dms 入口)→ 邀请制提示。
 * 通过闸的用户走双视图工作台(录入 / 记录);连接配置在录入页底部连接卡内,不设独立面。 */
(function (root) {
    'use strict';
    var $ = function (id) {
        return document.getElementById(id);
    };
    var LANGS = ['zh', 'th', 'en', 'ja'];
    var currentView = 'intake';
    var chromeWired = false;

    function applyTexts() {
        document.querySelectorAll('[data-dt]').forEach(function (el) {
            el.textContent = root.dt(el.getAttribute('data-dt'));
        });
        try {
            document.documentElement.lang = (root.DXI18N && root.DXI18N.lang) || 'th';
        } catch (e) {
            /* noop */
        }
    }
    function highlightLang() {
        var cur = root.DXI18N && root.DXI18N.lang;
        document.querySelectorAll('[data-dms-lang]').forEach(function (b) {
            b.classList.toggle('on', b.getAttribute('data-dms-lang') === cur);
        });
    }

    // ── 视图切换 ──
    function mountView(name) {
        currentView = name;
        ['intake', 'records', 'billing'].forEach(function (v) {
            var sec = $('dms-view-' + v);
            if (sec) sec.classList.toggle('on', v === name);
        });
        document.querySelectorAll('.dms-nav-item').forEach(function (n) {
            n.classList.toggle('on', n.getAttribute('data-view') === name);
        });
        if (name === 'intake') {
            root.DX.mountIntake();
        } else if (name === 'records') {
            root.DXRECORDS.mount('#dms-view-records');
        } else if (name === 'billing') {
            root.DXBILLING.mount('#dms-view-billing');
        }
        window.scrollTo(0, 0);
    }

    function wireChrome() {
        if (chromeWired) return;
        chromeWired = true;
        document.querySelectorAll('.dms-nav-item').forEach(function (n) {
            n.addEventListener('click', function () {
                mountView(n.getAttribute('data-view'));
            });
        });
        var bar = document.querySelector('.dms-langbar');
        if (bar)
            bar.addEventListener('click', function (e) {
                var btn = e.target.closest('[data-dms-lang]');
                if (!btn) return;
                var lang = btn.getAttribute('data-dms-lang');
                if (LANGS.indexOf(lang) < 0) return;
                root.dtSetLang(lang);
                applyTexts();
                highlightLang();
                mountView(currentView);
            });
        var logout = $('dmsLogout');
        if (logout)
            logout.addEventListener('click', function () {
                // 清 token(pearnly_entry 保留 'dms' 供退出/冷启动分流回 /dms)。
                localStorage.removeItem('mrpilot_token');
                boot();
            });
    }

    // 录入向导「查看记录」→ 切记录视图(单一导航事实源)。
    root._dmsGoRecords = function () {
        mountView('records');
    };

    // ── 门面 / 工作台切换 ──
    function showShell() {
        $('gateRoot').classList.remove('on');
        $('gateRoot').innerHTML = '';
        $('dmsShell').style.display = '';
        $('dmsShell').classList.add('on');
    }
    function showGate() {
        $('dmsShell').style.display = 'none';
        $('dmsShell').classList.remove('on');
        $('gateRoot').classList.add('on');
    }

    function enterApp() {
        showShell();
        wireChrome();
        applyTexts();
        highlightLang();
        mountView(currentView);
    }
    function showLogin() {
        showGate();
        root.DXGATE.mountLogin($('gateRoot'), {
            api: root.DXAPI.create(),
            onSuccess: function () {
                boot();
            },
        });
    }
    function showInvited() {
        showGate();
        root.DXGATE.mountInvited($('gateRoot'), {
            onLogout: function () {
                localStorage.removeItem('mrpilot_token');
                boot();
            },
        });
    }

    // 探针非 401(404/403 = 闸关/非 dms 入口)时,借 /api/me 分辨"token 失效"与"未受邀"。
    function resolveGateClosed(api) {
        api.getMe()
            .then(function () {
                showInvited();
            })
            .catch(function () {
                localStorage.removeItem('mrpilot_token');
                showLogin();
            });
    }

    function boot() {
        applyTexts();
        highlightLang();
        var token = localStorage.getItem('mrpilot_token');
        if (!token) {
            showLogin();
            return;
        }
        var api = root.DXAPI.create();
        api.probe()
            .then(function () {
                enterApp();
            })
            .catch(function (err) {
                if (err && err.status === 401) {
                    localStorage.removeItem('mrpilot_token');
                    showLogin();
                    return;
                }
                resolveGateClosed(api);
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})(typeof self !== 'undefined' ? self : this);
