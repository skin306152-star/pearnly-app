/*
 * Pearnly AI · ai-gate.js · 未登录/未受邀两种门面(登录卡 + 邀请制提示)
 *
 * Zihao 拍板(Z1-a · 2026-07-10):boot 探针原来对 401/404 无差别整页跳 /home——
 * 现改就地渲染,不再假装 AI 工作台不存在。两条门面(挂载/判别由 ai.js boot() 编排):
 *   A. 无 token 或 token 失效(401)→ 登录卡,走现有 POST /api/login
 *   B. token 有效但工单闸探针 404(/api/me 200 而 listOrders 404)→ 邀请制提示
 * 硬性红线(Zihao 截图点名删除):卡面禁注册入口 / Google 登录 / LINE 登录 / 服务条款行——
 * 这是独立 AI 工作台的邀请制前脸,不是主站获客着陆页,少即是对,不比样式。
 *
 * 纯函数(表单校验 / 错误 key 解析)与 DOM 挂载共存一个文件(<500 行铁律内合并,不另立
 * ai-gate-render.js)——node 单测直接 require 取 UMD 导出的纯函数那一半。
 */
(function (root) {
    'use strict';

    var LANGS = ['zh', 'th', 'en', 'ja'];
    var LANG_LABEL = { zh: '中文', th: 'ไทย', en: 'EN', ja: '日本語' };

    // ============ 纯函数(node 可测,零 DOM 依赖) ============

    function validateLoginInput(username, password) {
        var u = String(username == null ? '' : username).trim();
        var p = String(password == null ? '' : password);
        if (!u || !p) return { ok: false, errKey: 'gate_err_required' };
        return { ok: true };
    }

    // err 来自 ai-api.js call() 的拒绝值:API 错误(4xx/5xx)带 .status/.code;网络失败
    // (fetch 本身 reject,如断网)两者皆无——两类必须分开报人话(状态诚实:别把断网
    // 说成"密码错")。返回的 key 未必存在于词典(调用方按 t() 回落 err_generic)。
    function resolveLoginErrorKey(err) {
        if (!err || err.status == null) return 'gate_err_network';
        return 'err_' + String(err.code || 'generic').replace(/\./g, '_');
    }

    // ============ HTML 拼装 ============

    function esc(s) {
        if (root && root.AI && root.AI.state && typeof root.AI.state.esc === 'function') {
            return root.AI.state.esc(s);
        }
        return String(s == null ? '' : s);
    }

    function t(key) {
        return typeof root.at === 'function' ? root.at(key) : key;
    }

    function icon(pathD) {
        return '<svg viewBox="0 0 24 24" fill="none" stroke-width="2">' + pathD + '</svg>';
    }
    var IC_MAIL = icon('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>');
    var IC_CHAT = icon(
        '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z"/>'
    );
    var IC_PHONE = icon(
        '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.6a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.5-1.2a2 2 0 0 1 2.1-.5c.8.3 1.7.5 2.6.6a2 2 0 0 1 1.8 2Z"/>'
    );
    var IC_HELP = icon(
        '<circle cx="12" cy="12" r="10"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.5-2 2-2 3.5"/><path d="M12 17h.01"/>'
    );
    var IC_LOCK = icon('<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>');

    function langbarHtml() {
        var current = root.AII18N && root.AII18N.lang;
        var btns = LANGS.map(function (l) {
            var on = current === l ? ' on' : '';
            return (
                '<button type="button" class="gate-lang-btn' +
                on +
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
            '<div class="word"><b>Pearnly</b> <em>AI</em></div></div>'
        );
    }

    // 联系卡照产品现有那张:Email / @pearnly LINE / 电话——同一份内容两种门面共用。
    function helpCardHtml() {
        return (
            '<aside class="gate-help" aria-label="Pearnly support">' +
            '<div class="gh-head"><span class="gh-ic">' +
            IC_HELP +
            '</span><strong>' +
            esc(t('gate_help_title')) +
            '</strong></div>' +
            '<div class="gh-grid">' +
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
            '</h1>' +
            '<p class="gate-sub">' +
            esc(t('gate_welcome_sub')) +
            '</p>' +
            '<form id="gateLoginForm" class="gate-form" autocomplete="on" novalidate>' +
            '<div class="gf-row">' +
            '<label for="gateUsername">' +
            esc(t('gate_username_label')) +
            '</label>' +
            '<input id="gateUsername" name="username" type="text" autocomplete="username" placeholder="' +
            esc(t('gate_username_ph')) +
            '" />' +
            '</div>' +
            '<div class="gf-row">' +
            '<label for="gatePassword">' +
            esc(t('gate_password_label')) +
            '</label>' +
            '<input id="gatePassword" name="password" type="password" autocomplete="current-password" placeholder="' +
            esc(t('gate_password_ph')) +
            '" />' +
            '</div>' +
            '<div class="gf-split">' +
            '<label class="gf-check"><input id="gateRemember" type="checkbox" checked /> <span>' +
            esc(t('gate_remember_label')) +
            '</span></label>' +
            '<a class="gf-link" id="gateForgotLink" href="/login" target="_blank" rel="noopener">' +
            esc(t('gate_forgot_link')) +
            '</a>' +
            '</div>' +
            '<button class="btn pri gf-submit" id="gateSubmitBtn" type="submit">' +
            esc(t('gate_login_btn')) +
            '</button>' +
            '<div class="gf-msg" id="gateMsg" role="status" aria-live="polite"></div>' +
            '</form>' +
            '</div>' +
            helpCardHtml() +
            '</div>'
        );
    }

    function invitedHtml() {
        return (
            '<div class="gate-wrap">' +
            '<div class="gate-card gate-card-invite">' +
            brandHtml() +
            '<div class="gate-invite-ic">' +
            IC_LOCK +
            '</div>' +
            '<h1 class="gate-h1" id="gateInviteTitle">' +
            esc(t('gate_invite_title')) +
            '</h1>' +
            '<p class="gate-sub" id="gateInviteBody">' +
            esc(t('gate_invite_body')) +
            '</p>' +
            '<button class="btn" id="gateLogoutBtn" type="button">' +
            esc(t('gate_logout_btn')) +
            '</button>' +
            '</div>' +
            helpCardHtml() +
            '</div>'
        );
    }

    // ============ DOM 挂载 ============

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
            var lang = btn.getAttribute('data-gate-lang');
            if (typeof root.atSetLang === 'function') root.atSetLang(lang);
            onChange();
        });
    }

    function mountLogin(container, opts) {
        opts = opts || {};
        var api = opts.api;
        container.innerHTML = loginHtml();
        // 切语言 = 整卡重渲染(登录卡尚无跨语言保留输入值的必要,表单本就短)。
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
    if (root) {
        root.AI = root.AI || {};
        root.AI.gate = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
