// ============================================================
// REFACTOR-C1 (2026-05-27) · 顶栏三件套/头像菜单(NAV-IA Phase1)topbar-avatar 从 home.js 抽出为 ES module
//
// 来源:home.js L17087-17447 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global isSuperAdmin routeTo canManageTeam shouldHideMoney openSettingsModal switchSettingsTab */

// =================================================================
// NAV-IA Phase 1 · 顶栏头像下拉菜单(2026-05-15 拍板)
// - 头像下拉菜单(右上角 · 替代旧 sidebar-user 入口)
// 命名空间:avatar-menu-* (v118.33.2 Phase 2 已清掉旧 sidebar-user-popup)
// =================================================================
(function () {
    'use strict';

    // ---- 角色显隐(暴露到 window · loadAll 在 9734 行会调) ----
    // v118.35.0.7 · 没 user info 时强制隐藏 admin/test/special · 不再 early-return
    // 让特权入口"默认看不见"(home.html 4 处也已 style=display:none 兜底)
    // 防止普通账号刚登录的窗口期看到"管理员后台"按钮
    window.applyRoleVisibility = function applyRoleVisibility() {
        var u = window._userInfo;
        var canTeam = false,
            hideMoney = true,
            isSuper = false,
            isTest = false;
        if (u) {
            canTeam =
                typeof canManageTeam === 'function'
                    ? canManageTeam(u)
                    : !!(u.role === 'owner' || u.is_super_admin);
            hideMoney =
                typeof shouldHideMoney === 'function'
                    ? shouldHideMoney(u)
                    : u.role === 'member' && !u.is_super_admin;
            isSuper = typeof isSuperAdmin === 'function' ? isSuperAdmin(u) : !!u.is_super_admin;
        }

        document.querySelectorAll<HTMLElement>('[data-show-if-team]').forEach(function (
            el: HTMLElement
        ) {
            el.style.display = canTeam ? '' : 'none';
        });
        document.querySelectorAll<HTMLElement>('[data-show-if-money]').forEach(function (
            el: HTMLElement
        ) {
            el.style.display = hideMoney ? 'none' : '';
        });
        document.querySelectorAll<HTMLElement>('[data-show-if-admin]').forEach(function (
            el: HTMLElement
        ) {
            el.style.display = isSuper ? '' : 'none';
        });
        document.querySelectorAll<HTMLElement>('[data-show-if-test]').forEach(function (
            el: HTMLElement
        ) {
            el.style.display = isTest ? '' : 'none';
        });
        var anySpecial = isSuper || isTest;
        document.querySelectorAll<HTMLElement>('[data-show-if-special]').forEach(function (
            el: HTMLElement
        ) {
            el.style.display = anySpecial ? '' : 'none';
        });

        // 业态白名单收缩头像菜单(module-nav 据 business_type 写 _avatarShellHide · nav-presets 定名单)。
        // 本函数在 i18n 切换时重跑,故收缩要在这里(role 逻辑之后)兜底,免得被复位显回。
        // settings/shortcuts 无其它门控 → 由本壳独家开关;billing/console 各有 money/team 门控(上方已算),
        // 壳只朝"隐"覆盖,不越权把它们显回来。
        var shellHide = window._avatarShellHide || [];
        // 壳独家双向开关:这两项无其它门控 → 命中则隐、未命中则显回,壳是唯一事实源。
        var SHELL_TOGGLE = ['avatar-menu-settings', 'avatar-menu-shortcuts'];
        SHELL_TOGGLE.forEach(function (id) {
            var el = document.getElementById(id);
            if (el) el.style.display = shellHide.indexOf(id) >= 0 ? 'none' : '';
        });
        // 只朝"隐"覆盖:这两项各有 money/team 门控(上方 role 逻辑已算),壳命中才压隐,绝不显回越权。
        var SHELL_HIDE_ONLY = ['avatar-menu-billing', 'avatar-menu-console'];
        SHELL_HIDE_ONLY.forEach(function (id) {
            if (shellHide.indexOf(id) < 0) return;
            var el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    };

    // ---- 渲染头像 + 名字 + 邮箱(复用 renderSidebarUser 同款 letter/avatar_url 逻辑) ----
    window.renderAvatarMenu = function renderAvatarMenu(u) {
        if (!u) return;
        var btn = document.getElementById('avatar-btn');
        var nameEl = document.getElementById('avatar-popup-name');
        var emailEl = document.getElementById('avatar-popup-email');
        if (!btn || !nameEl || !emailEl) return;
        var email = (u.username || '').trim();
        var namePart = email.split('@')[0] || email || '—';
        var letter = (email.charAt(0) || '?').toUpperCase();
        var av = (u.avatar_url || '').trim();
        if (av) {
            var safeUrl = av.replace(/"/g, '&quot;');
            var safeLetter = letter.replace(/'/g, "\\'");
            btn.innerHTML =
                '<img src="' +
                safeUrl +
                '" alt="' +
                letter +
                '" referrerpolicy="no-referrer" onerror="this.parentNode.textContent=\'' +
                safeLetter +
                '\'">';
        } else {
            btn.textContent = letter;
        }
        nameEl.textContent = namePart;
        emailEl.textContent = email || '—';
        btn.setAttribute('title', email || '');
        // 侧栏底部用户卡(Claude 式 · 2026-06-10)与顶栏头像同源填充
        var sbAva = document.getElementById('sb-user-ava');
        var sbName = document.getElementById('sb-user-name');
        var sbMail = document.getElementById('sb-user-mail');
        if (sbAva) sbAva.textContent = letter;
        if (sbName) sbName.textContent = namePart;
        if (sbMail) sbMail.textContent = email || '—';
    };

    // ---- 头像 popup 交互 ----
    function _initAvatarMenu() {
        var wrap = document.getElementById('avatar-wrap');
        var btn = document.getElementById('avatar-btn');
        var popup = document.getElementById('avatar-popup');
        if (!wrap || !btn || !popup) return;

        var sbUser = document.getElementById('sb-user');

        function closePopup() {
            popup!.classList.remove('show');
            popup!.classList.remove('from-sidebar');
            btn!.setAttribute('aria-expanded', 'false');
        }
        function openPopup() {
            popup!.classList.add('show');
            btn!.setAttribute('aria-expanded', 'true');
        }

        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            if (popup!.classList.contains('show')) closePopup();
            else openPopup();
        });

        // 侧栏底部用户卡 → 同一菜单 · 贴左下弹出(Claude 式)
        if (sbUser)
            sbUser.addEventListener('click', function (e) {
                e.stopPropagation();
                if (popup!.classList.contains('show')) closePopup();
                else {
                    popup!.classList.add('from-sidebar');
                    openPopup();
                }
            });

        // 外部点击关闭(仅当 popup 开着 + 点击点不在 wrap/用户卡 内)
        document.addEventListener('click', function (e) {
            var n = e.target as Node | null;
            if (
                popup!.classList.contains('show') &&
                !wrap!.contains(n) &&
                !(sbUser && sbUser.contains(n))
            ) {
                closePopup();
            }
        });

        // 9 项 data-action 事件委托
        popup.addEventListener('click', function (e) {
            var item = (e.target as HTMLElement).closest(
                '.avatar-popup-item'
            ) as HTMLElement | null;
            if (!item) return;
            var action = item.dataset.action;
            if (action === 'theme') {
                // 暗夜模式开关:翻面 + 持久化 · 不关菜单让用户看到开关状态
                if (typeof window.toggleTheme === 'function') window.toggleTheme();
                return;
            }
            closePopup();

            switch (action) {
                case 'settings':
                    if (typeof openSettingsModal === 'function') openSettingsModal();
                    else if (typeof routeTo === 'function') routeTo('settings');
                    break;
                case 'billing':
                    if (typeof openSettingsModal === 'function') openSettingsModal();
                    else if (typeof routeTo === 'function') routeTo('settings');
                    setTimeout(function () {
                        if (typeof switchSettingsTab === 'function') switchSettingsTab('plan');
                    }, 50);
                    break;
                case 'shortcuts':
                    if (typeof showToast === 'function') {
                        var msg = typeof t === 'function' ? t('feature-coming-soon') : '即将上线';
                        showToast(msg || '即将上线', 'info');
                    }
                    break;
                case 'admin':
                    // v118.44.0 NAV-IA Phase 8 · 跳新 admin SPA(独立 layout)· 不再走老 /admin = home.html
                    window.location.href = '/admin/cost';
                    break;
                case 'help':
                    var helpModal = document.getElementById('help-modal');
                    if (helpModal) helpModal.style.display = 'flex';
                    break;
                case 'logout':
                    Promise.resolve(
                        typeof window.revokeSessionToken === 'function'
                            ? window.revokeSessionToken()
                            : undefined
                    ).finally(function () {
                        try {
                            // 入口提示(pearnly_entry)登出即清:壳的权威是 token.entry,不留旧门痕迹。
                            localStorage.removeItem('mrpilot_token');
                            localStorage.removeItem('mrpilot_user');
                            localStorage.removeItem('pearnly_entry');
                        } catch (_) {
                            /* silent · localStorage 私模/配额 */
                        }
                        window.location.href = window.loginUrl!();
                    });
                    break;
            }
        });

        // 关闭头像 popup 暴露到 window(ESC 兜底用)。
        window._closeAvatarPopup = closePopup;
    }

    // ---- ESC 关 avatar-popup(仅剩一层) ----
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            var popup = document.getElementById('avatar-popup');
            if (popup && popup.classList.contains('show')) {
                if (typeof window._closeAvatarPopup === 'function') {
                    window._closeAvatarPopup();
                }
            }
        }
    });

    // ---- 初始化 ----
    function _init() {
        _initAvatarMenu();
        // i18n 切换时:刷一次显隐(隐藏项重新计算 · 不动文本)
        if (typeof window.subscribeI18n === 'function') {
            window.subscribeI18n('nav-ia-phase1-role', function () {
                try {
                    if (typeof window.applyRoleVisibility === 'function')
                        window.applyRoleVisibility();
                } catch (_) {}
            });
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }
})();
