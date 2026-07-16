/* Pearnly DMS · 登录/未受邀两种门面(登录卡 + 邀请制提示)· 移植自 ai-gate.js。
 * 编排/判别由 dms-boot.js 的 boot() 做:
 *   无 token 或 401 → 登录卡(走 POST /api/login,entry:'dms');
 *   token 有效但 DMS 闸探针 404/403(未受邀/非 dms 入口)→ 邀请制提示。
 * 硬红线(同 /ai):卡面禁注册 / Google / LINE / 忘记密码——邀请制前脸,少即是对。 */
(function (root) {
    'use strict';

    var LANGS = ['zh', 'th', 'en', 'ja'];
    var LANG_LABEL = { zh: '中文', th: 'ไทย', en: 'EN', ja: '日本語' };

    // ── 纯函数(node 可测,零 DOM) ──
    function validateLoginInput(username, password) {
        var u = String(username == null ? '' : username).trim();
        var p = String(password == null ? '' : password);
        if (!u || !p) return { ok: false, errKey: 'gate_err_required' };
        return { ok: true };
    }
    function resolveLoginErrorKey(err) {
        if (!err || err.status == null) return 'gate_err_network';
        return 'err_' + String(err.code || 'generic').replace(/\./g, '_');
    }

    function t(key) {
        return typeof root.dt === 'function' ? root.dt(key) : key;
    }
    function esc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(s)
            : String(s == null ? '' : s);
    }

    function icon(pathD) {
        return '<svg viewBox="0 0 24 24" fill="none" stroke-width="2">' + pathD + '</svg>';
    }
    var IC_MAIL = icon('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>');
    var IC_CHAT = icon('<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z"/>');
    var IC_PHONE = icon(
        '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.6a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.5-1.2a2 2 0 0 1 2.1-.5c.8.3 1.7.5 2.6.6a2 2 0 0 1 1.8 2Z"/>'
    );
    var IC_HELP = icon(
        '<circle cx="12" cy="12" r="10"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.5-2 2-2 3.5"/><path d="M12 17h.01"/>'
    );
    var IC_LOCK = icon(
        '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'
    );

    function langbarHtml() {
        var current = root.DXI18N && root.DXI18N.lang;
        var btns = LANGS.map(function (l) {
            return (
                '<button type="button" class="gate-lang-btn' +
                (current === l ? ' on' : '') +
                '" data-gate-lang="' +
                l +
                '">' +
                LANG_LABEL[l] +
                '</button>'
            );
        }).join('');
        return '<div class="gate-langbar" role="tablist" aria-label="Language">' + btns + '</div>';
    }
    function brandHtml() {
        return (
            '<div class="gate-brand"><div class="mono">P</div>' +
            '<div class="word"><b>Pearnly</b> <em>DMS</em></div></div>'
        );
    }
    function helpCardHtml() {
        return (
            '<aside class="gate-help" aria-label="Pearnly support">' +
            '<div class="gh-head"><span class="gh-ic">' +
            IC_HELP +
            '</span><strong>' +
            esc(t('gate_help_title')) +
            '</strong></div><div class="gh-grid">' +
            '<a class="gh-item" href="mailto:hello@pearnly.com"><span class="gh-dot email">' +
            IC_MAIL +
            '</span><span>Email</span></a>' +
            '<a class="gh-item" href="https://line.me/R/ti/p/@pearnly" target="_blank" rel="noopener"><span class="gh-dot line">' +
            IC_CHAT +
            '</span><span>@pearnly</span></a>' +
            '<a class="gh-item" href="tel:0868892228"><span class="gh-dot phone">' +
            IC_PHONE +
            '</span><span>086-889-2228</span></a>' +
            '</div></aside>'
        );
    }

    function loginHtml() {
        return (
            '<div class="gate-wrap">' +
            langbarHtml() +
            '<div class="gate-card">' +
            brandHtml() +
            '<h1 class="gate-h1">' +
            esc(t('gate_welcome_title')) +
            '</h1><p class="gate-sub">' +
            esc(t('gate_welcome_sub')) +
            '</p>' +
            '<form id="gateLoginForm" class="gate-form" autocomplete="on" novalidate>' +
            '<div class="gf-row"><label for="gateUsername">' +
            esc(t('gate_username_label')) +
            '</label>' +
            '<input id="gateUsername" name="username" type="text" autocomplete="username" placeholder="' +
            esc(t('gate_username_ph')) +
            '" /></div>' +
            '<div class="gf-row"><label for="gatePassword">' +
            esc(t('gate_password_label')) +
            '</label>' +
            '<input id="gatePassword" name="password" type="password" autocomplete="current-password" placeholder="' +
            esc(t('gate_password_ph')) +
            '" /></div>' +
            '<div class="gf-split"><label class="gf-check"><input id="gateRemember" type="checkbox" checked /> <span>' +
            esc(t('gate_remember_label')) +
            '</span></label></div>' +
            '<button class="btn pri gf-submit" id="gateSubmitBtn" type="submit">' +
            esc(t('gate_login_btn')) +
            '</button>' +
            '<div class="gf-msg" id="gateMsg" role="status" aria-live="polite"></div>' +
            '</form></div>' +
            helpCardHtml() +
            '</div>'
        );
    }

    function invitedHtml() {
        return (
            '<div class="gate-wrap"><div class="gate-card gate-card-invite">' +
            brandHtml() +
            '<div class="gate-invite-ic">' +
            IC_LOCK +
            '</div><h1 class="gate-h1">' +
            esc(t('gate_invite_title')) +
            '</h1><p class="gate-sub">' +
            esc(t('gate_invite_body')) +
            '</p>' +
            '<button class="btn" id="gateLogoutBtn" type="button">' +
            esc(t('gate_logout_btn')) +
            '</button></div>' +
            helpCardHtml() +
            '</div>'
        );
    }

    // ── DOM 挂载 ──
    function setMsg(container, text, kind) {
        var el = container.querySelector('#gateMsg');
        if (!el) return;
        el.textContent = text || '';
        el.className = 'gf-msg' + (kind ? ' ' + kind : '');
    }
    function setBusy(btn, busy, busyLabel, idleLabel) {
        if (!btn) return;
        btn.disabled = busy;
        btn.textContent = busy ? busyLabel : idleLabel;
    }
    function wireLangbar(container, onChange) {
        var bar = container.querySelector('.gate-langbar');
        if (!bar) return;
        bar.addEventListener('click', function (e) {
            var btn = e.target.closest('[data-gate-lang]');
            if (!btn) return;
            if (typeof root.dtSetLang === 'function')
                root.dtSetLang(btn.getAttribute('data-gate-lang'));
            onChange();
        });
    }

    function mountLogin(container, opts) {
        opts = opts || {};
        var api = opts.api;
        container.innerHTML = loginHtml();
        wireLangbar(container, function () {
            mountLogin(container, opts);
        });
        var form = container.querySelector('#gateLoginForm');
        var submitBtn = container.querySelector('#gateSubmitBtn');
        var submitting = false;
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            if (submitting) return;
            var username = container.querySelector('#gateUsername').value;
            var password = container.querySelector('#gatePassword').value;
            var remember = container.querySelector('#gateRemember').checked;
            var check = validateLoginInput(username, password);
            if (!check.ok) {
                setMsg(container, t(check.errKey), 'error');
                return;
            }
            submitting = true;
            setMsg(container, '', '');
            setBusy(submitBtn, true, t('gate_login_btn_busy'), t('gate_login_btn'));
            api.login(username, password, remember)
                .then(function (data) {
                    submitting = false;
                    if (!data || !data.access_token) {
                        setBusy(submitBtn, false, t('gate_login_btn_busy'), t('gate_login_btn'));
                        setMsg(container, t('err_generic'), 'error');
                        return;
                    }
                    root.localStorage.setItem('mrpilot_token', data.access_token);
                    // 入口提示(pre-auth 冷启动/退出分流用)· 壳权威仍是 token.entry='dms'。
                    try {
                        root.localStorage.setItem('pearnly_entry', 'dms');
                    } catch (_) {
                        /* silent */
                    }
                    if (typeof opts.onSuccess === 'function') opts.onSuccess(data);
                })
                .catch(function (err) {
                    submitting = false;
                    setBusy(submitBtn, false, t('gate_login_btn_busy'), t('gate_login_btn'));
                    var key = resolveLoginErrorKey(err);
                    var msg = t(key);
                    setMsg(container, msg !== key ? msg : t('err_generic'), 'error');
                });
        });
    }

    function mountInvited(container, opts) {
        opts = opts || {};
        container.innerHTML = invitedHtml();
        container.querySelector('#gateLogoutBtn').addEventListener('click', function () {
            if (typeof opts.onLogout === 'function') opts.onLogout();
        });
    }

    var api = {
        validateLoginInput: validateLoginInput,
        resolveLoginErrorKey: resolveLoginErrorKey,
        mountLogin: mountLogin,
        mountInvited: mountInvited,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.DXGATE = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
