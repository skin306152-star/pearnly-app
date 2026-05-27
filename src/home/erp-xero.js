// ============================================================
// REFACTOR-C1 (2026-05-27) · Xero 连接卡片 erp-xero 从 home.js 抽出为 ES module
//
// 来源:home.js L17322-17873 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
// ============================================================
// v118.27.4 · Xero 连接卡片 + 推按钮注入
// 渲染:自动化 → ERP 对接 → 连接 & 推送日志 sub-tab 顶部 #erp-connect-cards
// 推按钮:历史抽屉 saveBar 内 · 跟 ERP 按钮并排
// ============================================================
/* global escapeHtml, _results, _drawerIdx */
(function () {
    'use strict';

    let _status = null;
    let _statusLoaded = false;
    let _bound = false;

    function _esc(s) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function _toast(msg, kind) {
        try {
            if (typeof showToast === 'function') showToast(msg, kind || 'info');
        } catch (e) {}
    }

    function _isOwner() {
        const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
        return !!(u && (u.role === 'owner' || u.is_super_admin));
    }

    function _getCurrentHistory() {
        try {
            const r = (typeof _results !== 'undefined' ? _results : [])[
                typeof _drawerIdx !== 'undefined' ? _drawerIdx : -1
            ];
            return r || null;
        } catch (e) {
            return null;
        }
    }

    function _isHistoryExceptional(h) {
        if (!h) return false;
        const st = String(h.status || '').toLowerCase();
        return st === 'exception' || st === 'exception_pending' || st === 'rejected';
    }

    async function _loadStatus(force) {
        if (_statusLoaded && !force) return _status;
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return null;
        try {
            const r = await fetch('/api/erp/xero/status', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) throw new Error('http_' + r.status);
            _status = await r.json();
            _statusLoaded = true;
        } catch (e) {
            _status = { configured: false, connected: false, organisations: [] };
            _statusLoaded = false;
        }
        return _status;
    }

    // ─── 连接卡片渲染 ──────────────────────────────────
    // v118.34.5 (Zihao 2026-05-19 拍板) · 用户截图反馈 Xero 卡片跟
    // MR.ERP / FlowAccount 风格不一致 · 一比一复刻 .integration-row 样式
    // (跟 Google Drive / LINE Bot / Gmail 那种卡片完全一样的 class).
    //
    // 已连接状态下,组织列表 + auto-push toggle + 断开按钮 改成行内的
    // 小卡片附属 region · 不再大块占用纵向空间。
    function _renderCard() {
        const host = document.getElementById('erp-connect-cards');
        if (!host) return;
        const s = _status;

        // Status pill — same class system as MR.ERP card.
        let pill,
            configured = !!s,
            connected = false;
        if (!s) {
            pill =
                '<span class="mrerp-card-pill mrerp-pill-neutral">' +
                _esc(t('xero-card-not-connected')) +
                '</span>';
        } else if (!s.configured) {
            pill =
                '<span class="mrerp-card-pill mrerp-pill-neutral">' +
                _esc(t('xero-card-not-configured')) +
                '</span>';
        } else if (s.connected) {
            connected = true;
            pill =
                '<span class="mrerp-card-pill mrerp-pill-ok">' +
                _esc(t('xero-card-connected')) +
                '</span>';
        } else {
            pill =
                '<span class="mrerp-card-pill mrerp-pill-neutral">' +
                _esc(t('xero-card-not-connected')) +
                '</span>';
        }

        // v118.34.35 · Xero 卡片对齐 MR.ERP 模式 · 真启用/停用 toggle
        // 未配置 / 未连接 OAuth → 连接 Xero 按钮 (启动 OAuth flow)
        // 已连接 → 启用/停用 toggle (= auto_push) + 修改 按钮 (展开 details)
        let actionHtml = '';
        if (!s || !s.configured) {
            actionHtml =
                '<button type="button" class="int-btn-configure" id="btn-xero-connect">' +
                _esc(t('xero-connect-btn')) +
                '</button>';
        } else if (!s.connected) {
            if (_isOwner()) {
                actionHtml =
                    '<button type="button" class="int-btn-configure" id="btn-xero-connect">' +
                    _esc(t('xero-connect-btn')) +
                    '</button>';
            }
        } else {
            // 已连接 · "启用/停用" toggle 控制 auto_push · "修改" 展开 details 面板
            const ap = !!s.auto_push;
            const toggleLabel = ap ? t('card-btn-disable') : t('card-btn-enable');
            const toggleClass = ap
                ? 'mrerp-card-toggle mrerp-card-toggle-disable'
                : 'mrerp-card-toggle mrerp-card-toggle-enable';
            actionHtml =
                '<button type="button" class="' +
                toggleClass +
                '" id="btn-xero-toggle-enabled" ' +
                'data-xero-enabled="' +
                (ap ? '1' : '0') +
                '" ' +
                'title="' +
                _esc(ap ? t('erp-auto-push-on-tip') : t('erp-auto-push-off-tip')) +
                '">' +
                _esc(toggleLabel) +
                '</button>' +
                '<button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">' +
                _esc(t('card-btn-edit')) +
                '</button>';
        }

        // Description text — keep it short, matching .int-desc pattern.
        const descKey = s && s.connected ? 'xero-card-desc-connected' : 'xero-card-desc-default';
        // Fall back to a sensible default if descKey isn't in the dict.
        const descFallback =
            s && s.connected
                ? t('xero-card-connected') || 'Connected · default org will receive pushes'
                : 'Cloud accounting · push invoices to your default Xero org';
        const desc = (function () {
            const v = t(descKey);
            return v === descKey ? descFallback : v;
        })();

        // Build the main row using Pearnly's existing class system.
        let html =
            '<div class="integration-row erp-connect-xero' +
            (connected ? ' connected' : '') +
            '">' +
            '<div class="int-icon ic-xero">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="12" cy="12" r="9"/>' +
            '<circle cx="9" cy="10" r="1.3" fill="currentColor"/>' +
            '<circle cx="15" cy="14" r="1.3" fill="currentColor"/>' +
            '<path d="M9 14l6-4"/>' +
            '</svg>' +
            '</div>' +
            '<div class="int-info">' +
            '<div class="int-name">' +
            '<span>' +
            _esc(t('xero-card-title') || 'Xero') +
            '</span>' +
            pill +
            '</div>' +
            '<div class="int-desc">' +
            _esc(desc) +
            '</div>' +
            '</div>' +
            '<div class="int-actions">' +
            actionHtml +
            '</div>' +
            '</div>';

        // Connected · attached "details" region below the row (orgs
        // selector + auto-push toggle + disconnect). Renders only when
        // _isOwner() AND we toggled it open via #btn-xero-edit-toggle.
        if (s && s.configured && s.connected && _isOwner()) {
            const orgs = s.organisations || [];
            let detailsBody = '';
            if (orgs.length > 0) {
                detailsBody +=
                    '<div class="erp-cc-meta">' +
                    _esc((t('xero-org-count') || '').replace('{n}', String(orgs.length))) +
                    '</div>';
                detailsBody +=
                    '<div class="erp-cc-org-label">' + _esc(t('xero-default-org')) + ':</div>';
                detailsBody += '<div class="erp-cc-orgs">';
                orgs.forEach(function (o) {
                    detailsBody +=
                        '<label class="erp-cc-org-row">' +
                        '<input type="radio" name="xero-default-org" value="' +
                        _esc(o.id) +
                        '"' +
                        (o.is_default ? ' checked' : '') +
                        '>' +
                        '<span class="erp-cc-org-name">' +
                        _esc(o.organisation_name || o.organisation_id) +
                        '</span>' +
                        '</label>';
                });
                detailsBody += '</div>';
                const ap = !!s.auto_push;
                const apTip = ap ? t('erp-auto-push-on-tip') : t('erp-auto-push-off-tip');
                detailsBody +=
                    '<div class="erp-cc-auto-push" title="' +
                    _esc(apTip) +
                    '">' +
                    '<label class="erp-cc-toggle">' +
                    '<input type="checkbox" id="xero-auto-push-toggle"' +
                    (ap ? ' checked' : '') +
                    '>' +
                    '<span class="erp-cc-toggle-slider"></span>' +
                    '<span class="erp-cc-toggle-label">' +
                    _esc(t('erp-auto-push-label')) +
                    '</span>' +
                    '</label></div>';
                detailsBody +=
                    '<div class="erp-cc-actions">' +
                    '<button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">' +
                    _esc(t('xero-disconnect-btn')) +
                    '</button>' +
                    '</div>';
            }
            // Hidden by default; #btn-xero-edit-toggle toggles its display.
            html +=
                '<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">' +
                detailsBody +
                '</div>';
        }

        // Surgical replacement — find any prior Xero markup and swap.
        const old = host.querySelector('.erp-connect-xero');
        const oldDetails = host.querySelector('#erp-xero-details');
        if (oldDetails) oldDetails.remove();
        if (old) {
            old.outerHTML = html;
        } else {
            host.insertAdjacentHTML('afterbegin', html);
        }

        // Bind the new edit-toggle button.
        const editBtn = document.getElementById('btn-xero-edit-toggle');
        if (editBtn) {
            editBtn.addEventListener('click', function (e) {
                e.preventDefault();
                const det = document.getElementById('erp-xero-details');
                if (!det) return;
                det.style.display = det.style.display === 'none' ? '' : 'none';
            });
        }

        // v118.34.35 · 启用/停用 toggle (= auto_push) · 对齐 MR.ERP 模式
        const toggleBtn = document.getElementById('btn-xero-toggle-enabled');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', async function (e) {
                e.preventDefault();
                if (toggleBtn.disabled) return;
                const currentlyEnabled = toggleBtn.getAttribute('data-xero-enabled') === '1';
                const next = !currentlyEnabled;
                // 停用要二次确认 (新发票将不再推送)
                if (!next) {
                    try {
                        const ok = await window.pearnlyConfirm(t('card-toggle-disable-confirm'));
                        if (!ok) return;
                    } catch (e2) {
                        /* fallback: 无 confirm 直接继续 */
                    }
                }
                toggleBtn.disabled = true;
                await _onToggleAutoPush(next, null);
            });
        }
    }

    async function _onConnect() {
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        try {
            const r = await fetch('/api/erp/xero/auth/start', {
                method: 'GET',
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) {
                let detail = 'unknown';
                try {
                    detail = (await r.json()).detail || 'unknown';
                } catch (e) {}
                const errKey = String(detail)
                    .replace(/^xero\./, '')
                    .toLowerCase();
                _toast(
                    t('xero-push-fail').replace('{err}', t('xero-err-' + errKey) || detail),
                    'error'
                );
                return;
            }
            const data = await r.json();
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            }
        } catch (e) {
            _toast(t('xero-push-fail').replace('{err}', e.message || 'network'), 'error');
        }
    }

    async function _onDisconnect() {
        const ok = await window.pearnlyConfirm(t('xero-disconnect-confirm'));
        if (!ok) return;
        const tk = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/erp/xero/disconnect', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) throw new Error('http_' + r.status);
            await _loadStatus(true);
            _renderCard();
        } catch (e) {
            _toast(t('xero-push-fail').replace('{err}', e.message), 'error');
        }
    }

    async function _onSelectOrg(tokenId) {
        const tk = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/erp/xero/select_org', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + tk,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token_id: tokenId }),
            });
            if (!r.ok) throw new Error('http_' + r.status);
            await _loadStatus(true);
            _renderCard();
        } catch (e) {
            _toast(t('xero-push-fail').replace('{err}', e.message), 'error');
        }
    }

    // v27.8.1.3 · 切自动推送开关
    async function _onToggleAutoPush(on, checkboxEl) {
        const tk = localStorage.getItem('mrpilot_token');
        if (checkboxEl) checkboxEl.disabled = true;
        try {
            const r = await fetch('/api/erp/xero/auto-push', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + tk,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ on: !!on }),
            });
            if (!r.ok) {
                let detail = 'unknown';
                try {
                    detail = (await r.json()).detail || 'unknown';
                } catch (e) {}
                throw new Error(detail);
            }
            _toast(on ? t('erp-auto-push-toggled-on') : t('erp-auto-push-toggled-off'), 'success');
            // 刷状态 + 重渲(更新 tooltip)
            _statusLoaded = false;
            await _loadStatus(true);
            _renderCard();
        } catch (e) {
            // 回滚 checkbox 状态
            if (checkboxEl) checkboxEl.checked = !on;
            _toast(
                t('erp-auto-push-toggle-fail').replace('{err}', e.message || 'network'),
                'error'
            );
        } finally {
            if (checkboxEl) checkboxEl.disabled = false;
        }
    }

    // ─── 历史抽屉「推到 Xero」按钮注入 ──────────────────
    async function _injectPushBtn() {
        const saveBar = document.getElementById('drawer-history-save');
        if (!saveBar) return;
        if (saveBar.querySelector('#btn-xero-push')) return;
        // v118.27.5 · 统一推送按钮存在时 · 老 Xero 按钮不再注入
        if (saveBar.querySelector('#pn-push-wrap')) return;

        await _loadStatus(false);
        // v118.27.5.2 · race fix · await 期间统一按钮可能已被注入 · 重新 check
        if (saveBar.querySelector('#pn-push-wrap')) return;
        if (saveBar.querySelector('#btn-xero-push')) return;
        const r = _getCurrentHistory();
        const hid = r && (r._historyId || r.history_id);
        if (!hid) return;

        let disabled = false;
        let titleKey = 'xero-push-tip';
        if (!_status || !_status.configured) {
            disabled = true;
            titleKey = 'xero-err-not_configured';
        } else if (!_status.connected) {
            disabled = true;
            titleKey = 'xero-push-disabled-no-conn';
        } else if (_isHistoryExceptional(r)) {
            disabled = true;
            titleKey = 'xero-push-disabled-exc';
        }

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.id = 'btn-xero-push';
        btn.className = 'btn btn-ghost' + (disabled ? ' disabled' : '');
        btn.disabled = disabled;
        btn.title = t(titleKey) || '';
        btn.innerHTML =
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' +
            '<circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg>' +
            '<span style="margin-left:4px;">' +
            _esc(t('xero-push-btn')) +
            '</span>';
        btn.addEventListener('click', _onPush);

        const pushErpBtn = document.getElementById('btn-push-erp');
        if (pushErpBtn && pushErpBtn.parentNode) {
            pushErpBtn.parentNode.insertBefore(btn, pushErpBtn.nextSibling);
        } else {
            saveBar.insertBefore(btn, saveBar.firstChild);
        }
    }

    async function _onPush() {
        const r = _getCurrentHistory();
        const hid = r && (r._historyId || r.history_id);
        if (!hid) return;
        const btn = document.getElementById('btn-xero-push');
        if (btn) {
            btn.disabled = true;
            btn.classList.add('loading');
        }
        const tk = localStorage.getItem('mrpilot_token');
        try {
            const resp = await fetch('/api/erp/xero/push/' + encodeURIComponent(hid), {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!resp.ok) {
                let detail = 'unknown';
                try {
                    detail = (await resp.json()).detail || 'unknown';
                } catch (e) {}
                const errKey = String(detail)
                    .replace(/^xero\./, '')
                    .toLowerCase();
                const friendly = t('xero-' + errKey);
                const showText = friendly && friendly !== 'xero-' + errKey ? friendly : detail;
                _toast(t('xero-push-fail').replace('{err}', showText), 'error');
                return;
            }
            _toast(t('xero-push-ok'), 'success');
        } catch (e) {
            _toast(t('xero-push-fail').replace('{err}', e.message || 'network'), 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('loading');
            }
        }
    }

    // ─── 进入「连接 & 推送日志」sub-tab 时拉数据 ─────────
    async function _onEnterConnectSubtab() {
        await _loadStatus(true);
        _renderCard();
        _loadGlobalPushMode();
    }

    // P1b · 全局「ERP 自动处理方式」· 账户级 · 对所有端点统一生效。
    async function _loadGlobalPushMode() {
        const sel = document.getElementById('erp-global-push-mode');
        if (!sel) return;
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        try {
            const r = await fetch('/api/settings/erp-push-mode', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (r.ok) {
                const d = await r.json();
                if (d.mode) {
                    sel.value = d.mode;
                    sel.dataset.prev = d.mode;
                }
            }
        } catch (e) {
            /* 静默 · 保留默认 smart */
        }
    }

    async function _onChangeGlobalPushMode(sel) {
        const mode = sel.value;
        const tk = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/settings/erp-push-mode', {
                method: 'PUT',
                headers: { Authorization: 'Bearer ' + tk, 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode }),
            });
            if (r.ok) {
                sel.dataset.prev = mode;
                _toast(t('pref-erp-mode-saved'), 'success');
            } else {
                sel.value = sel.dataset.prev || 'smart';
                _toast(t('pref-save-failed'), 'error');
            }
        } catch (e) {
            sel.value = sel.dataset.prev || 'smart';
            _toast(t('pref-save-failed'), 'error');
        }
    }

    // ─── OAuth 回调 redirect 后的提示(URL hash 含 ?xero=ok|err)
    function _checkCallbackResult() {
        try {
            const h = String(window.location.hash || '');
            if (h.indexOf('xero=ok') >= 0) {
                const m = h.match(/n=(\d+)/);
                const n = m ? m[1] : '1';
                _toast((t('xero-toast-redirected-ok') || '').replace('{n}', n), 'success');
                // 清掉 hash query
                history.replaceState(null, '', window.location.pathname + '#automation');
                _loadStatus(true).then(_renderCard);
            } else if (h.indexOf('xero=err') >= 0) {
                _toast(t('xero-toast-redirected-err'), 'error');
                history.replaceState(null, '', window.location.pathname + '#automation');
            }
        } catch (e) {}
    }

    function _bind() {
        if (_bound) return;
        _bound = true;

        document.addEventListener('click', function (ev) {
            // 进入 ERP 对接 → connect sub-tab
            const subBtn = ev.target.closest('.erp-subtab[data-erp-subtab="connect"]');
            if (subBtn) {
                setTimeout(_onEnterConnectSubtab, 50);
                return;
            }
            // 进入 ERP 对接 panel(自动化 nav)
            const erpAutoTab = ev.target.closest('.auto-nav-item[data-auto-tab="erp"]');
            if (erpAutoTab) {
                setTimeout(_onEnterConnectSubtab, 80);
                return;
            }
            // 卡片按钮
            if (ev.target.closest('#btn-xero-connect')) {
                ev.preventDefault();
                _onConnect();
                return;
            }
            if (ev.target.closest('#btn-xero-disconnect')) {
                ev.preventDefault();
                _onDisconnect();
                return;
            }
        });

        document.addEventListener('change', function (ev) {
            if (ev.target && ev.target.matches('input[name="xero-default-org"]')) {
                _onSelectOrg(ev.target.value);
            }
            // v27.8.1.3 · auto-push toggle
            if (ev.target && ev.target.id === 'xero-auto-push-toggle') {
                _onToggleAutoPush(ev.target.checked, ev.target);
            }
            // P1b · 全局 ERP 自动处理方式 select
            if (ev.target && ev.target.id === 'erp-global-push-mode') {
                _onChangeGlobalPushMode(ev.target);
            }
        });

        // 监听历史抽屉 + 注入 Xero 推按钮
        const drawerBody = function () {
            return document.getElementById('drawer-body');
        };
        try {
            const observer = new MutationObserver(function () {
                if (
                    document.getElementById('drawer-history-save') &&
                    !document.getElementById('btn-xero-push')
                ) {
                    _injectPushBtn();
                }
            });
            const target = drawerBody();
            if (target) {
                observer.observe(target, { childList: true, subtree: true });
            } else {
                const bodyOb = new MutationObserver(function () {
                    const b = drawerBody();
                    if (b) {
                        observer.observe(b, { childList: true, subtree: true });
                        bodyOb.disconnect();
                    }
                });
                bodyOb.observe(document.body, { childList: true, subtree: true });
            }
        } catch (e) {}

        // 页面加载时 · 检查 OAuth callback 提示
        setTimeout(_checkCallbackResult, 500);
    }

    function _rerenderAll() {
        if (_status) _renderCard();
        const btn = document.getElementById('btn-xero-push');
        if (btn) {
            const span = btn.querySelector('span');
            if (span) span.textContent = t('xero-push-btn');
        }
    }

    _bind();
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('xero-adapter', _rerenderAll);
    }
    // v27.8.1.2 · 修「老板按钮 30 秒空白」bug · 之前 setTimeout 600ms 太短
    // 改 polling _userInfo 就绪 + 进 sub-tab 时主动渲(connect tab 默认 active)
    async function _waitForUserInfo(maxMs) {
        const start = Date.now();
        while (Date.now() - start < (maxMs || 5000)) {
            // _userInfo 是文件作用域 let · IIFE 走作用域链可访问
            if (typeof _userInfo !== 'undefined' && _userInfo && _userInfo.id) return _userInfo;
            await new Promise((r) => setTimeout(r, 80));
        }
        return null;
    }
    async function _autoBootstrap() {
        // 等 _userInfo 拿到 · 再渲卡(_isOwner 才能返回正确值)
        await _waitForUserInfo(5000);
        const a = document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]');
        const c = document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');
        if (a && c) await _onEnterConnectSubtab();
    }
    setTimeout(_autoBootstrap, 200);
})();
