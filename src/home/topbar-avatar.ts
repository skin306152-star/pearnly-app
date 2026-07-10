// ============================================================
// REFACTOR-C1 (2026-05-27) · 顶栏三件套/头像菜单(NAV-IA Phase1)topbar-avatar 从 home.js 抽出为 ES module
//
// 来源:home.js L17087-17447 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global applyLang isSuperAdmin routeTo canManageTeam shouldHideMoney openSettingsModal switchSettingsTab */

// =================================================================
// NAV-IA Phase 1 · 顶栏三件套(2026-05-15 拍板)
// - 头像下拉菜单(右上角 · 替代旧 sidebar-user 入口)
// - 顶栏搜索框(点击 / ⌘K 弹命令面板)
// - Cmd+K 命令面板(13 跳转 + 4 切语言)
// 视觉基准:pearnly_nav_prototype_final.html
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
        // 本函数在 i18n 切换 / cmdk 打开时重跑,故收缩要在这里(role 逻辑之后)兜底,免得被复位显回。
        // settings/shortcuts 无其它门控 → 由本壳独家开关;billing/console 各有 money/team 门控(上方已算),
        // 壳只朝"隐"覆盖,不越权把它们显回来。
        var shellHide = window._avatarShellHide || [];
        var settingsEl = document.getElementById('avatar-menu-settings');
        if (settingsEl)
            settingsEl.style.display = shellHide.indexOf('avatar-menu-settings') >= 0 ? 'none' : '';
        var shortcutsEl = document.getElementById('avatar-menu-shortcuts');
        if (shortcutsEl)
            shortcutsEl.style.display =
                shellHide.indexOf('avatar-menu-shortcuts') >= 0 ? 'none' : '';
        if (shellHide.indexOf('avatar-menu-billing') >= 0) {
            var billEl = document.getElementById('avatar-menu-billing');
            if (billEl) billEl.style.display = 'none';
        }
        if (shellHide.indexOf('avatar-menu-console') >= 0) {
            var consoleEl = document.getElementById('avatar-menu-console');
            if (consoleEl) consoleEl.style.display = 'none';
        }
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
                            localStorage.removeItem('mrpilot_token');
                        } catch (_) {
                            /* silent · localStorage 私模/配额 */
                        }
                        try {
                            localStorage.removeItem('mrpilot_user');
                        } catch (_) {
                            /* silent · localStorage 私模/配额 */
                        }
                        window.location.href = '/login';
                    });
                    break;
            }
        });

        // 暴露给 cmdk 用
        window._closeAvatarPopup = closePopup;
    }

    // ---- Cmd+K 命令面板 ----
    function _cmdkVisibleItems() {
        return ([].slice.call(document.querySelectorAll('.cmdk-item')) as HTMLElement[]).filter(
            function (el) {
                return el.style.display !== 'none';
            }
        );
    }
    function _cmdkSetFocus(idx: number) {
        var items = _cmdkVisibleItems();
        items.forEach(function (i) {
            i.classList.remove('focus');
        });
        if (items[idx]) {
            items[idx].classList.add('focus');
            items[idx].scrollIntoView({ block: 'nearest' });
        }
    }
    function _cmdkMoveFocus(delta: number) {
        var items = _cmdkVisibleItems();
        if (!items.length) return;
        var cur = items.findIndex(function (i) {
            return i.classList.contains('focus');
        });
        if (cur < 0) cur = 0;
        var next = (cur + delta + items.length) % items.length;
        _cmdkSetFocus(next);
    }
    function _cmdkFilter(q: string) {
        q = (q || '').toLowerCase().trim();
        var visibleCount = 0;
        var u = window._userInfo;
        var isSuper =
            typeof isSuperAdmin === 'function' ? isSuperAdmin(u) : !!(u && u.is_super_admin);
        var isTest = false;

        document.querySelectorAll<HTMLElement>('.cmdk-item').forEach(function (item: HTMLElement) {
            // 权限项硬过滤(不显在 cmdk 里 · 不参与计数)
            if (item.dataset.showIfAdmin === '1' && !isSuper) {
                item.style.display = 'none';
                return;
            }
            if (item.dataset.showIfTest === '1' && !isTest) {
                item.style.display = 'none';
                return;
            }

            var text = (item.dataset.cmdkText || item.textContent || '').toLowerCase();
            var show = !q || text.indexOf(q) >= 0;
            item.style.display = show ? '' : 'none';
            item.classList.remove('focus');
            if (show) visibleCount++;
        });

        // section 标题:该区无可见项时隐
        document.querySelectorAll<HTMLElement>('[data-cmdk-section]').forEach(function (
            s: HTMLElement
        ) {
            var n = s.nextElementSibling,
                any = false;
            while (n && !n.hasAttribute('data-cmdk-section')) {
                if (
                    n.classList &&
                    n.classList.contains('cmdk-item') &&
                    (n as HTMLElement).style.display !== 'none'
                ) {
                    any = true;
                    break;
                }
                n = n.nextElementSibling;
            }
            s.style.display = any ? '' : 'none';
        });

        var empty = document.getElementById('cmdk-empty');
        if (empty) empty.style.display = visibleCount === 0 ? 'flex' : 'none';
        _cmdkSetFocus(0);
    }

    window.openCmdk = function openCmdk() {
        var mask = document.getElementById('cmdk-mask');
        if (!mask) return;
        // 关掉头像 popup(避免叠加)
        if (typeof window._closeAvatarPopup === 'function') window._closeAvatarPopup();
        mask.classList.add('show');
        // 重新跑显隐(账号切换后保持正确)
        if (typeof window.applyRoleVisibility === 'function') window.applyRoleVisibility();
        setTimeout(function () {
            var input = document.getElementById('cmdk-input');
            if (!input) return;
            (input as HTMLInputElement).value = '';
            _cmdkFilter('');
            input.focus();
            _cmdkSetFocus(0);
        }, 50);
    };
    window.closeCmdk = function closeCmdk() {
        var mask = document.getElementById('cmdk-mask');
        if (mask) mask.classList.remove('show');
    };

    function _cmdkActivate(item: HTMLElement | null) {
        if (!item) return;
        // 「即将」项:不执行 · toast 提示
        if (item.classList.contains('cmdk-item-locked')) {
            if (typeof showToast === 'function') {
                var msg = typeof t === 'function' ? t('feature-coming-soon') : '即将上线';
                showToast(msg || '即将上线', 'info');
            }
            return;
        }
        var route = item.dataset.cmdkRoute;
        var action = item.dataset.cmdkAction;
        window.closeCmdk!();

        if (route) {
            if (typeof routeTo === 'function') routeTo(route);
            return;
        }
        if (action) {
            if (action === 'open-admin') {
                window.location.href = '/admin/cost';
                return;
            } // v118.44.0 · NAV-IA Phase 8 · 新 admin SPA
            if (action.indexOf('lang-') === 0) {
                var lang = action.slice(5);
                if (typeof applyLang === 'function') applyLang(lang);
            }
        }
    }

    function _initCmdk() {
        var mask = document.getElementById('cmdk-mask');
        var input = document.getElementById('cmdk-input');
        var body = document.getElementById('cmdk-body');
        if (!mask || !input || !body) return;

        // 点 mask 自身关闭(不冒泡到内部)
        mask.addEventListener('click', function (e) {
            if (e.target === mask) window.closeCmdk!();
        });
        var escBtn = document.getElementById('cmdk-esc-btn');
        if (escBtn)
            escBtn.addEventListener('click', function () {
                window.closeCmdk!();
            });

        // 输入过滤
        input.addEventListener('input', function (e) {
            _cmdkFilter((e.target as HTMLInputElement).value);
        });
        input.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                _cmdkMoveFocus(1);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                _cmdkMoveFocus(-1);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                _cmdkActivate(mask!.querySelector('.cmdk-item.focus') as HTMLElement | null);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                window.closeCmdk!();
            }
        });

        // 列表点击委托
        body.addEventListener('click', function (e) {
            var item = (e.target as HTMLElement).closest('.cmdk-item') as HTMLElement | null;
            if (item) _cmdkActivate(item);
        });
        // 鼠标 hover 切焦点
        body.addEventListener('mousemove', function (e) {
            var item = (e.target as HTMLElement).closest('.cmdk-item') as HTMLElement | null;
            if (
                !item ||
                item.style.display === 'none' ||
                item.classList.contains('cmdk-item-locked')
            )
                return;
            _cmdkVisibleItems().forEach(function (i) {
                i.classList.remove('focus');
            });
            item.classList.add('focus');
        });

        // 顶栏搜索框点击 + 键盘可达
        var tbs = document.getElementById('topbar-search');
        if (tbs) {
            tbs.addEventListener('click', function () {
                window.openCmdk!();
            });
            tbs.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    window.openCmdk!();
                }
            });
        }
    }

    // ---- 全局快捷键:⌘K / Ctrl+K 打开 · ESC 关 cmdk → 关 avatar-popup ----
    document.addEventListener('keydown', function (e) {
        // ⌘K / Ctrl+K
        if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
            e.preventDefault();
            window.openCmdk!();
            return;
        }
        // ESC 链:cmdk → avatar-popup(只关一层)
        if (e.key === 'Escape') {
            var mask = document.getElementById('cmdk-mask');
            if (mask && mask.classList.contains('show')) {
                // input 内的 ESC 已由 _initCmdk 处理 · 这里兜底
                window.closeCmdk!();
                return;
            }
            var popup = document.getElementById('avatar-popup');
            if (
                popup &&
                popup.classList.contains('show') &&
                typeof window._closeAvatarPopup === 'function'
            ) {
                window._closeAvatarPopup();
            }
        }
    });

    // ---- OS 探测 · 给顶栏搜索框 kbd 标签切显示 ----
    try {
        var ua = (navigator.userAgent || '').toLowerCase();
        var isMac = ua.indexOf('mac') >= 0 || ua.indexOf('iphone') >= 0 || ua.indexOf('ipad') >= 0;
        if (!isMac) document.body.classList.add('is-windows');
    } catch (_) {
        /* silent · classList 极少 fail */
    }

    // ---- 初始化 ----
    function _init() {
        _initAvatarMenu();
        _initCmdk();
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
