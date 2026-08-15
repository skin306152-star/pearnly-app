/*
 * static/daily/daily-gate.js · Daily 门禁层(登录卡 / 邀请提示 / 故障态 / boot)
 *
 * 照 ai-gate.js 分档:401 → 内嵌登录卡(entry=daily)·
 *   404 → 未受邀提示 · 5xx/断网 → 可重试故障态 · 200 → 放行 loadMonth。
 * 纯逻辑在 daily-core.js(DailyCore),UI 主壳在 daily.js,本文件只做门禁。
 */
(function (root) {
    'use strict';

    var LANG_LABEL = { th: 'ไทย', en: 'EN', zh: '中', ja: '日' };
    var state = root.DailyCore.state;
    var t = root.DailyCore.t;
    var api = root.DailyCore.api;
    var saveToken = root.DailyCore.saveToken;
    var clearToken = root.DailyCore.clearToken;
    var readToken = root.DailyCore.readToken;
    var readLang = root.DailyCore.readLang;
    var persistLang = root.DailyCore.persistLang;
    var LANGS = root.DailyCore.LANGS;
    var monthId = root.DailyCore.monthId;
    var monthOptions = root.DailyCore.monthOptions;
    var escapeHtml = root.DailyCore.escapeHtml;

    function setLang(lang) {
        state.lang = LANGS.indexOf(lang) >= 0 ? lang : 'th';
        persistLang(state.lang);
        applyStaticI18n();
        if (state.gate === 'app') {
            root.DailyApp.rerender();
        } else {
            renderGate();
        }
    }

    function boot() {
        setLang(readLang());

        var now = new Date();
        state.months = monthOptions(now);
        state.monthId = monthId(now.getFullYear(), now.getMonth() + 1);

        state.token = readToken();
        if (!state.token) {
            state.gate = 'login';
            renderGate();
            return;
        }
        api('/api/daily/session').then(function (res) {
            if (res.status === 200) {
                state.gate = 'app';
                root.DailyApp.loadMonth();
            } else if (res.status === 401) {
                clearToken();
                state.gate = 'login';
                renderGate();
            } else if (res.status >= 500 || res.status === 408 || res.status === 429) {
                state.gate = 'unavailable';
                renderGate();
            } else if (res.status === null) {
                state.gate = 'offline';
                renderGate();
            } else {
                state.gate = 'invited';
                renderGate();
            }
        });
    }

    function submitLogin(username, password) {
        var u = String(username == null ? '' : username).trim();
        var p = String(password == null ? '' : password);
        if (!u || !p) {
            gateError('daily.gate.err_required');
            return;
        }
        api('/api/login', {
            method: 'POST',
            json: { username: u, password: p, entry: 'daily' },
        }).then(function (res) {
            if (res.status === 200 && res.body && res.body.token) {
                saveToken(res.body.token);
                boot();
            } else {
                gateError(res.status == null ? 'daily.gate.err_network' : 'daily.gate.err_generic');
            }
        });
    }

    function gateError(key) {
        var el = root.document.getElementById('gateError');
        if (el) el.textContent = t(key);
    }

    function renderGate() {
        var rootEl = root.document.getElementById('appRoot');
        var langRoot = root.document.getElementById('gateRoot');
        if (!rootEl || !langRoot) return;
        rootEl.innerHTML = '';
        langRoot.innerHTML = gateHtml();
        applyStaticI18n();
        if (state.gate === 'login') {
            var form = langRoot.querySelector('form');
            if (form) {
                form.addEventListener('submit', function (ev) {
                    ev.preventDefault();
                    submitLogin(form.username.value, form.password.value);
                });
            }
        }
    }

    function gateHtml() {
        var langbar =
            '<div class="langbar">' +
            LANGS.map(function (l) {
                return (
                    '<button type="button" class="lang-btn' +
                    (l === state.lang ? ' on' : '') +
                    '" data-lang="' +
                    l +
                    '">' +
                    LANG_LABEL[l] +
                    '</button>'
                );
            }).join('') +
            '</div>';
        if (state.gate === 'login') {
            return (
                langbar +
                '<div class="gate-card">' +
                '<h1>' +
                escapeHtml(t('daily.title')) +
                '</h1>' +
                '<p class="gate-sub" data-i18n="daily.eyebrow"></p>' +
                '<form class="gate-form">' +
                '<input name="username" autocomplete="username" data-i18n-placeholder="daily.gate.username">' +
                '<input name="password" type="password" autocomplete="current-password" data-i18n-placeholder="daily.gate.password">' +
                '<p class="gate-error" id="gateError"></p>' +
                '<button type="submit" data-i18n="daily.gate.login"></button>' +
                '</form></div>'
            );
        }
        var cfg = {
            invited: ['daily.gate.invited_title', 'daily.gate.invited_body', false],
            unavailable: ['daily.gate.unavailable_title', 'daily.gate.unavailable_body', true],
            offline: ['daily.gate.offline_title', 'daily.gate.offline_body', true],
        }[state.gate] || ['daily.gate.err_generic', 'daily.gate.err_generic', true];
        return (
            langbar +
            '<div class="gate-card">' +
            '<h1>' +
            escapeHtml(t(cfg[0])) +
            '</h1>' +
            '<p class="gate-body">' +
            escapeHtml(t(cfg[1])) +
            '</p>' +
            (cfg[2]
                ? '<button type="button" class="gate-retry" data-retry data-i18n="daily.gate.retry"></button>'
                : '') +
            (state.token
                ? '<button type="button" class="gate-logout" data-logout data-i18n="daily.gate.logout"></button>'
                : '') +
            '</div>'
        );
    }

    function applyStaticI18n() {
        var nodes = root.document.querySelectorAll('[data-i18n]');
        for (var i = 0; i < nodes.length; i++) {
            nodes[i].textContent = t(nodes[i].getAttribute('data-i18n'));
        }
        var placeholders = root.document.querySelectorAll('[data-i18n-placeholder]');
        for (var j = 0; j < placeholders.length; j++) {
            placeholders[j].setAttribute(
                'placeholder',
                t(placeholders[j].getAttribute('data-i18n-placeholder'))
            );
        }
        var langBtns = root.document.querySelectorAll('[data-lang]');
        for (var k = 0; k < langBtns.length; k++) {
            langBtns[k].className =
                langBtns[k].getAttribute('data-lang') === state.lang ? 'lang-btn on' : 'lang-btn';
        }
    }

    root.DailyGate = {
        boot: boot,
        setLang: setLang,
        renderGate: renderGate,
        applyStaticI18n: applyStaticI18n,
    };
})(typeof window !== 'undefined' ? window : globalThis);
