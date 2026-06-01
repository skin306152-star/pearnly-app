// ============================================================
// src/home/erp-mrerp-dms-connect.js · MR.ERP DMS 汽车销售连接器(2026-05-31)
//
// 渲染:自动化 → ERP 对接 → 连接 & 推送日志 sub-tab 顶部 #erp-connect-cards
//   独立 zone [data-mrerp-dms-zone] · 复用 integration-row / int-icon / int-info /
//   int-actions / int-btn-configure / mrerp-card-pill 样式系统(不自创卡片体系)。
// 连接向导:DMS 地址(预填)/ 账号 / 密码 / 连接并保存(测试+保存一键)。
//   保存 adapter=mrerp_dms · config.id_card_auto_push=true · auto_push=false
//   (auto_push 后端还会兜底 false · 防发票自动推送误投 DMS)。
//   凭据明文塞进 config.username_enc/password_enc 字段名 · 路由 kms 加密后落地
//   (前端不加密 · 不留明文)。
//
// 不依赖 static/erp-mrerp-connect.js 内部函数(避免加载顺序耦合)。
// 全局桥(bare):t / escapeHtml / showToast / pearnlyConfirm。token 经 localStorage。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    var DEFAULT_URL = 'https://www.mrerp4sme.com/dms/index.php';
    var _ep = null; // the saved mrerp_dms endpoint (or null)
    var _loaded = false;

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
    function _tk() {
        return localStorage.getItem('mrpilot_token');
    }

    async function _loadEndpoint(force) {
        if (_loaded && !force) return _ep;
        var tk = _tk();
        if (!tk) return null;
        try {
            var r = await fetch('/api/erp/endpoints', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) throw new Error('http_' + r.status);
            var data = await r.json();
            var items = (data && data.items) || [];
            _ep =
                items.find(function (e) {
                    return e && (e.adapter || '').toLowerCase() === 'mrerp_dms';
                }) || null;
            _loaded = true;
        } catch (e) {
            _ep = null;
            _loaded = false;
        }
        return _ep;
    }

    // ─── card ───────────────────────────────────────────
    function _renderCard() {
        var host = document.getElementById('erp-connect-cards');
        if (!host) return;
        var zone = host.querySelector('[data-mrerp-dms-zone]');
        if (!zone) {
            zone = document.createElement('div');
            zone.setAttribute('data-mrerp-dms-zone', '1');
            host.appendChild(zone);
        }

        var ep = _ep;
        var connected = !!(ep && ep.enabled !== false);
        var pill;
        if (!ep) {
            pill =
                '<span class="mrerp-card-pill mrerp-pill-neutral">' +
                _esc(t('dms-card-not-connected')) +
                '</span>';
        } else if (connected) {
            pill =
                '<span class="mrerp-card-pill mrerp-pill-ok">' +
                _esc(t('dms-card-connected')) +
                '</span>';
        } else {
            pill =
                '<span class="mrerp-card-pill mrerp-pill-neutral">' +
                _esc(t('dms-card-disabled-pill')) +
                '</span>';
        }

        var actions;
        if (!ep) {
            actions =
                '<button type="button" class="int-btn-configure" id="btn-dms-connect">' +
                _esc(t('dms-card-connect')) +
                '</button>';
        } else {
            var toggleLabel = connected ? t('dms-card-disable') : t('dms-card-enable');
            // 2026-06-01 · R7 视觉一致:按钮顺序对齐 MR.ERP 财务卡(修改在前 → 启用/停用在最后)。
            // 原顺序 测试→修改→停用 与财务卡的 修改→…→停用 不一致(Codex R2 复测 FAIL)。
            actions =
                '<button type="button" class="int-btn-configure" id="btn-dms-edit">' +
                _esc(t('dms-card-edit')) +
                '</button>' +
                '<button type="button" class="int-btn-configure" id="btn-dms-test">' +
                _esc(t('dms-card-test')) +
                '</button>' +
                '<button type="button" class="int-btn-configure" id="btn-dms-toggle">' +
                _esc(toggleLabel) +
                '</button>';
        }

        zone.innerHTML =
            '<div class="integration-row erp-connect-mrerp-dms' +
            (connected ? ' connected' : '') +
            '">' +
            '<div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/>' +
            '<path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/>' +
            '<circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/>' +
            '</svg>' +
            '</div>' +
            '<div class="int-info">' +
            '<div class="int-name"><span>' +
            _esc(t('dms-card-title')) +
            '</span>' +
            pill +
            '</div>' +
            '<div class="int-desc">' +
            _esc(t('dms-card-desc')) +
            '</div>' +
            '</div>' +
            '<div class="int-actions">' +
            actions +
            '</div>' +
            '</div>';
    }

    // ─── wizard modal ───────────────────────────────────
    function _closeWizard() {
        var ov = document.getElementById('dms-wizard-overlay');
        if (ov) ov.remove();
        document.removeEventListener('keydown', _onEsc);
    }
    function _onEsc(e) {
        if (e.key === 'Escape') _closeWizard();
    }

    function _openWizard() {
        _closeWizard();
        var ep = _ep;
        // 2026-06-01 · DMS 地址写死隐藏(只此一个 DMS 实例)· 向导只露 账号/密码/订车单号前缀。
        var prefix =
            (ep &&
                ep.config &&
                ep.config.booking_defaults &&
                ep.config.booking_defaults.booking_prefix) ||
            'PN';

        var field = function (labelKey, id, type, value, ph) {
            return (
                '<label style="display:block;margin-bottom:12px;">' +
                '<span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">' +
                _esc(t(labelKey)) +
                '</span>' +
                '<input id="' +
                id +
                '" type="' +
                type +
                '" value="' +
                _esc(value || '') +
                '" placeholder="' +
                _esc(ph || '') +
                '" autocomplete="new-password" ' +
                'style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;">' +
                '</label>'
            );
        };

        var ov = document.createElement('div');
        ov.id = 'dms-wizard-overlay';
        ov.style.cssText =
            'position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);' +
            'display:flex;align-items:center;justify-content:center;padding:16px;';
        ov.innerHTML =
            '<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="' +
            'background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;' +
            'padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;">' +
            '<div style="font-size:17px;font-weight:700;margin-bottom:4px;">' +
            _esc(t('dms-wizard-title')) +
            '</div>' +
            '<div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">' +
            _esc(t('dms-card-desc')) +
            '</div>' +
            field('dms-wizard-username', 'dms-w-user', 'text', '', '') +
            field('dms-wizard-password', 'dms-w-pass', 'password', '', '') +
            field('dms-wizard-prefix', 'dms-w-prefix', 'text', prefix, 'PN') +
            '<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div>' +
            '<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;">' +
            '<button type="button" class="btn btn-ghost" id="dms-w-cancel">' +
            _esc(t('dms-wizard-cancel')) +
            '</button>' +
            '<button type="button" class="btn btn-primary" id="dms-w-save">' +
            _esc(t('dms-wizard-save')) +
            '</button>' +
            '</div>' +
            '</div>';
        document.body.appendChild(ov);
        document.addEventListener('keydown', _onEsc);
        ov.addEventListener('click', function (e) {
            if (e.target === ov) _closeWizard();
        });
        var userEl = document.getElementById('dms-w-user');
        if (userEl) userEl.focus();
    }

    function _wizErr(msg) {
        var el = document.getElementById('dms-w-err');
        if (el) {
            el.textContent = msg;
            el.style.display = msg ? '' : 'none';
        }
    }

    async function _saveWizard() {
        // DMS 地址写死(界面已隐藏)· 编辑态沿用已存 system_url,新建用 DEFAULT_URL。
        var url = (_ep && _ep.config && _ep.config.system_url) || DEFAULT_URL;
        var user = (document.getElementById('dms-w-user') || {}).value || '';
        var pass = (document.getElementById('dms-w-pass') || {}).value || '';
        var prefix = (document.getElementById('dms-w-prefix') || {}).value || 'PN';
        url = url.trim();
        user = user.trim();
        if (!url || !user || !pass) {
            _wizErr(t('dms-wizard-required'));
            return;
        }
        var saveBtn = document.getElementById('dms-w-save');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = t('dms-wizard-saving');
        }
        _wizErr('');
        var tk = _tk();
        try {
            // 1. test connection (plaintext creds · in-memory only)
            var tr = await fetch('/api/erp/test-connection', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tk, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    adapter: 'mrerp_dms',
                    config: { system_url: url, username: user, password: pass },
                }),
            });
            var tdata = await tr.json().catch(function () {
                return {};
            });
            if (!tr.ok || !tdata.ok) {
                var fr =
                    (tdata.error_friendly &&
                        (tdata.error_friendly[window.currentLang] || tdata.error_friendly.en)) ||
                    t('dms-connect-fail-generic');
                _wizErr(fr);
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.textContent = t('dms-wizard-save');
                }
                return;
            }

            // 2. save endpoint (route encrypts username_enc/password_enc plaintext)
            var cfg = {
                system_url: url,
                username_enc: user,
                password_enc: pass,
                id_card_auto_push: true,
                booking_defaults: { booking_prefix: prefix.trim() || 'PN' },
            };
            var method, urlPath;
            if (_ep && _ep.id) {
                method = 'PATCH';
                urlPath = '/api/erp/endpoints/' + encodeURIComponent(_ep.id);
            } else {
                method = 'POST';
                urlPath = '/api/erp/endpoints';
            }
            var body =
                method === 'POST'
                    ? {
                          name: 'MR.ERP DMS',
                          adapter: 'mrerp_dms',
                          config: cfg,
                          is_default: false,
                          auto_push: false,
                      }
                    : { config: cfg, auto_push: false };
            var sr = await fetch(urlPath, {
                method: method,
                headers: { Authorization: 'Bearer ' + tk, 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!sr.ok) {
                var sd = await sr.json().catch(function () {
                    return {};
                });
                var code = (sd && sd.detail && (sd.detail.code || sd.detail)) || 'save_failed';
                _wizErr(t('dms-save-fail') + ' (' + _esc(String(code)) + ')');
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.textContent = t('dms-wizard-save');
                }
                return;
            }
            _closeWizard();
            _toast(t('dms-connect-ok'), 'success');
            await _loadEndpoint(true);
            _renderCard();
            // OCR 页模式切换器需要知道现在有 DMS endpoint 了
            if (typeof window._refreshOcrDocMode === 'function') window._refreshOcrDocMode();
        } catch (e) {
            _wizErr(t('dms-connect-fail-generic'));
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = t('dms-wizard-save');
            }
        }
    }

    async function _testSaved() {
        if (!_ep || !_ep.id) return;
        _toast(t('dms-test-running'), 'info');
        var tk = _tk();
        try {
            var r = await fetch(
                '/api/erp/endpoints/' + encodeURIComponent(_ep.id) + '/test-connection?refresh=1',
                { method: 'POST', headers: { Authorization: 'Bearer ' + tk } }
            );
            var d = await r.json().catch(function () {
                return {};
            });
            _toast(
                d && d.ok ? t('dms-test-ok') : t('dms-test-fail'),
                d && d.ok ? 'success' : 'error'
            );
        } catch (e) {
            _toast(t('dms-test-fail'), 'error');
        }
    }

    async function _toggleEnabled() {
        if (!_ep || !_ep.id) return;
        var enabling = _ep.enabled === false;
        if (!enabling) {
            try {
                var ok = await window.pearnlyConfirm(t('dms-confirm-disable'));
                if (!ok) return;
            } catch (e) {}
        }
        var tk = _tk();
        try {
            var r = await fetch('/api/erp/endpoints/' + encodeURIComponent(_ep.id), {
                method: 'PATCH',
                headers: { Authorization: 'Bearer ' + tk, 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enabling }),
            });
            if (!r.ok) throw new Error('http_' + r.status);
            _toast(enabling ? t('dms-enabled-toast') : t('dms-disabled-toast'), 'success');
            await _loadEndpoint(true);
            _renderCard();
            if (typeof window._refreshOcrDocMode === 'function') window._refreshOcrDocMode();
        } catch (e) {
            _toast(t('dms-save-fail'), 'error');
        }
    }

    // ─── bind ───────────────────────────────────────────
    function _onEnterConnectSubtab() {
        _loadEndpoint(true).then(_renderCard);
    }

    document.addEventListener('click', function (ev) {
        if (ev.target.closest('.erp-subtab[data-erp-subtab="connect"]')) {
            setTimeout(_onEnterConnectSubtab, 60);
            return;
        }
        if (ev.target.closest('.auto-nav-item[data-auto-tab="erp"]')) {
            setTimeout(_onEnterConnectSubtab, 90);
            return;
        }
        if (ev.target.closest('#btn-dms-connect') || ev.target.closest('#btn-dms-edit')) {
            ev.preventDefault();
            _openWizard();
            return;
        }
        if (ev.target.closest('#dms-w-cancel')) {
            ev.preventDefault();
            _closeWizard();
            return;
        }
        if (ev.target.closest('#dms-w-save')) {
            ev.preventDefault();
            _saveWizard();
            return;
        }
        if (ev.target.closest('#btn-dms-test')) {
            ev.preventDefault();
            _testSaved();
            return;
        }
        if (ev.target.closest('#btn-dms-toggle')) {
            ev.preventDefault();
            _toggleEnabled();
            return;
        }
    });

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('mrerp-dms-adapter', _renderCard);
    }

    // auto-bootstrap if we land directly on the ERP connect sub-tab
    setTimeout(function () {
        var a = document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]');
        var c = document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');
        if (a && c) _onEnterConnectSubtab();
    }, 250);
})();
