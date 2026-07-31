/* Pearnly DMS · 启动入口(闸判定 + i18n 应用 + 壳导航)· 移植 /ai boot 范式。
 * 闸行为:启动调门禁探针(GET /api/dms/session · 只跑入口守卫),就地渲染三种门面——
 *   无 token 或 401 → 登录卡;探针 404/403(未受邀/非 dms 入口)→ 邀请制提示;
 *   探针 5xx / 断网 → 服务不可用提示 + 重试。分档判据在 DXGATE.classifyBootFailure。
 * 通过闸的用户走双视图工作台(录入 / 记录);连接配置在录入页底部连接卡内,不设独立面。 */
(function (root) {
    'use strict';
    var $ = function (id) {
        return document.getElementById(id);
    };
    var LANGS = ['zh', 'th', 'en', 'ja'];
    var currentView = 'intake';
    var chromeWired = false;
    var isOwner = false;

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
        // 花名册 owner-only:非 owner 误触(理论上 nav 已藏)回落录入,不空挂。
        if (name === 'roster' && !isOwner) name = 'intake';
        currentView = name;
        ['intake', 'records', 'roster', 'billing'].forEach(function (v) {
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
        } else if (name === 'roster') {
            root.DXROSTER.mount('#dms-view-roster');
        } else if (name === 'billing') {
            root.DXBILLING.mount('#dms-view-billing');
        }
        window.scrollTo(0, 0);
    }

    // 「操作员」花名册 nav 仅 owner 可见(探针 is_owner);员工/非 owner 会话藏之。
    function applyOwnerNav() {
        var nav = document.querySelector('.dms-nav-item[data-view="roster"]');
        if (nav) nav.style.display = isOwner ? '' : 'none';
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

    function enterApp(session) {
        isOwner = !!(session && session.is_owner);
        root.__dmsIsOwner = isOwner; // 记录页 owner 视角(C6)据此走全租户 + 操作员归属列。
        showShell();
        wireChrome();
        applyOwnerNav();
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

    // 服务器故障/断网:留在原地给重试,不冒充权限判定,也不删令牌(退出登录是次动作)。
    function showUnavailable(kind, status) {
        showGate();
        root.DXGATE.mountUnavailable($('gateRoot'), {
            kind: kind,
            status: status,
            onRetry: function () {
                boot();
            },
            onLogout: function () {
                localStorage.removeItem('mrpilot_token');
                boot();
            },
        });
    }

    // 探针判成 denied(404/403 = 闸关/非 dms 入口)时,借 /api/me 分辨"token 失效"与"未受邀"。
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
            .then(function (session) {
                enterApp(session || {});
            })
            .catch(function (err) {
                var outcome = root.DXGATE.classifyBootFailure(err);
                if (outcome === 'expired') {
                    localStorage.removeItem('mrpilot_token');
                    showLogin();
                    return;
                }
                if (outcome === 'denied') {
                    resolveGateClosed(api);
                    return;
                }
                showUnavailable(outcome, err && err.status);
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})(typeof self !== 'undefined' ? self : this);
