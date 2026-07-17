/* Pearnly DMS · LINE 独立通道绑定卡(DL-4b)· 挂在录入页连接卡(dx-erp-cards-zone)下方。
 * 未绑定:说明步骤 + 加好友链接 + 生成绑定码(6 位大字 + 到期倒计时,过期自动灰掉可重生成)。
 * 已绑定:显示 display_name/bound_at + 解绑(体系内确认弹窗 pearnlyConfirm 后 DELETE)。
 * 后端契约见 routes/dms_routes.py:POST bind-code / GET|DELETE binding(DL-1)。挂 window.DXLINE。 */
(function (root) {
    'use strict';
    var authHeaders = root.DXAPI.authHeaders;
    var FRIEND_URL = 'https://line.me/R/ti/p/@264tuqln';

    function t(k) {
        return typeof root.t === 'function' ? root.t(k) : k;
    }
    function esc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(s == null ? '' : s)
            : String(s);
    }
    function toast(m, k) {
        if (typeof root.showToast === 'function') root.showToast(m, k || 'info');
    }

    var _host = null;
    var _timer = null;
    // 单一事实源:phase ∈ loading/error/unbound/bound;code 态另存(倒计时靠它重渲染,不重抓)。
    var S = { phase: 'loading', row: null, code: '', expiresAt: null };

    function clearTimer() {
        if (_timer) {
            clearInterval(_timer);
            _timer = null;
        }
    }
    function fmtDate(v) {
        if (!v) return '—';
        var d = new Date(v);
        if (isNaN(d.getTime())) return String(v);
        var p = function (n) {
            return (n < 10 ? '0' : '') + n;
        };
        return (
            d.getFullYear() +
            '-' +
            p(d.getMonth() + 1) +
            '-' +
            p(d.getDate()) +
            ' ' +
            p(d.getHours()) +
            ':' +
            p(d.getMinutes())
        );
    }
    function remainLabel(expiresAt) {
        var ms = expiresAt.getTime() - Date.now();
        if (ms <= 0) return null;
        var sec = Math.floor(ms / 1000);
        var m = Math.floor(sec / 60),
            s = sec % 60;
        return m + ':' + (s < 10 ? '0' : '') + s;
    }

    // 卡片是 title/body/action 三区 grid(见 dms-intake.css):动作按钮(生成绑定码/
    // 解绑)独立于内容流之外,桌面端搬到标题同一行右侧(贴近 MR.ERP DMS 卡 icon+
    // info+acts 布局),手机端仍按行堆叠在最下方——纯 CSS 换区,DOM 结构不用按视口分叉。
    function shell(bodyHtml, actionHtml) {
        return (
            '<div class="dms-line-card"><div class="dms-line-h">' +
            esc(t('dms-line-title')) +
            '</div><div class="dms-line-body">' +
            bodyHtml +
            '</div>' +
            (actionHtml || '') +
            '</div>'
        );
    }
    function loadingHtml() {
        return '<p class="dms-line-muted">' + esc(t('dms-line-loading')) + '</p>';
    }
    function errorHtml() {
        return (
            '<p class="dms-line-muted">' +
            esc(t('dms-line-error')) +
            '</p><button type="button" class="btn small" id="dms-line-retry">' +
            esc(t('dms-line-retry')) +
            '</button>'
        );
    }
    function friendLinkHtml() {
        return (
            '<a class="dms-line-friend" href="' +
            esc(FRIEND_URL) +
            '" target="_blank" rel="noopener noreferrer">' +
            esc(t('dms-line-addfriend')) +
            '</a>'
        );
    }
    function unboundBodyHtml() {
        var expired = S.expiresAt && !remainLabel(S.expiresAt);
        var codeZone = S.code
            ? '<div class="dms-line-code' +
              (expired ? ' expired' : '') +
              '">' +
              esc(S.code) +
              '</div><div class="dms-line-countdown" id="dms-line-countdown"></div>'
            : '';
        return (
            '<ol class="dms-line-steps"><li>' +
            esc(t('dms-line-step1')) +
            '</li><li>' +
            esc(t('dms-line-step2')) +
            '</li><li>' +
            esc(t('dms-line-step3')) +
            '</li></ol>' +
            friendLinkHtml() +
            '<div id="dms-line-code-zone" class="dms-line-code-zone">' +
            codeZone +
            '</div>'
        );
    }
    function unboundActionHtml() {
        return (
            '<button type="button" class="btn primary dms-line-gen dms-line-action" id="dms-line-gen-btn">' +
            esc(t(S.code ? 'dms-line-regenerate' : 'dms-line-gen-btn')) +
            '</button>'
        );
    }
    function boundBodyHtml() {
        return (
            '<div class="dms-line-bound"><div class="dms-line-bname">' +
            esc(S.row.display_name || '') +
            '</div><div class="dms-line-bmeta">' +
            esc(t('dms-line-bound-since')) +
            ' ' +
            esc(fmtDate(S.row.bound_at)) +
            '</div></div>'
        );
    }
    function boundActionHtml() {
        return (
            '<button type="button" class="btn dms-line-unbind dms-line-action" id="dms-line-unbind-btn">' +
            esc(t('dms-line-unbind-btn')) +
            '</button>'
        );
    }

    function render() {
        if (!_host) return;
        var bodyHtml, actionHtml;
        if (S.phase === 'loading') {
            bodyHtml = loadingHtml();
            actionHtml = '';
        } else if (S.phase === 'error') {
            bodyHtml = errorHtml();
            actionHtml = '';
        } else if (S.phase === 'bound') {
            bodyHtml = boundBodyHtml();
            actionHtml = boundActionHtml();
        } else {
            bodyHtml = unboundBodyHtml();
            actionHtml = unboundActionHtml();
        }
        _host.innerHTML = shell(bodyHtml, actionHtml);
        wire();
        if (S.phase === 'unbound' && S.expiresAt) startCountdown();
    }

    function wire() {
        var retry = document.getElementById('dms-line-retry');
        if (retry) retry.addEventListener('click', load);
        var gen = document.getElementById('dms-line-gen-btn');
        if (gen) gen.addEventListener('click', genCode);
        var unbind = document.getElementById('dms-line-unbind-btn');
        if (unbind) unbind.addEventListener('click', onUnbind);
    }

    // ── 倒计时(过期自动灰掉,不重抓服务器;重渲复用同一 S,不打断用户在页面上的其它操作) ──
    function startCountdown() {
        clearTimer();
        tick();
        _timer = setInterval(tick, 1000);
    }
    function tick() {
        var el = document.getElementById('dms-line-countdown');
        if (!el || !S.expiresAt) {
            clearTimer();
            return;
        }
        var label = remainLabel(S.expiresAt);
        if (!label) {
            clearTimer();
            var codeEl = document.querySelector('.dms-line-code');
            if (codeEl) codeEl.classList.add('expired');
            el.textContent = t('dms-line-expired');
            return;
        }
        el.textContent = t('dms-line-expires') + ' ' + label;
    }

    // ── 数据加载 / 生成码 / 解绑 ──
    function load() {
        clearTimer();
        S.phase = 'loading';
        render();
        fetch('/api/dms/line/binding', { headers: authHeaders() })
            .then(function (r) {
                if (!r.ok) return Promise.reject(new Error('http_' + r.status));
                return r.json();
            })
            .then(function (d) {
                if (d && d.bound) {
                    S.phase = 'bound';
                    S.row = d;
                } else {
                    S.phase = 'unbound';
                    S.row = null;
                    S.code = '';
                    S.expiresAt = null;
                }
                render();
            })
            .catch(function () {
                S.phase = 'error';
                render();
            });
    }
    function genCode() {
        var btn = document.getElementById('dms-line-gen-btn');
        if (btn) btn.disabled = true;
        fetch('/api/dms/line/bind-code', { method: 'POST', headers: authHeaders(true) })
            .then(function (r) {
                if (!r.ok) return Promise.reject(new Error('http_' + r.status));
                return r.json();
            })
            .then(function (d) {
                S.code = d.code || '';
                S.expiresAt = d.expires_at ? new Date(d.expires_at) : null;
                render();
            })
            .catch(function () {
                if (btn) btn.disabled = false;
                toast(t('dms-line-gen-fail'), 'error');
            });
    }
    function onUnbind() {
        if (typeof root.pearnlyConfirm !== 'function') return;
        root.pearnlyConfirm(t('dms-line-unbind-confirm')).then(function (ok) {
            if (!ok) return;
            var btn = document.getElementById('dms-line-unbind-btn');
            if (btn) btn.disabled = true;
            fetch('/api/dms/line/binding', { method: 'DELETE', headers: authHeaders() })
                .then(function (r) {
                    if (!r.ok) throw new Error('http_' + r.status);
                    load();
                })
                .catch(function () {
                    if (btn) btn.disabled = false;
                    toast(t('dms-line-unbind-fail'), 'error');
                });
        });
    }

    // 语言切换由调用方(dms-intake.js 的 subscribeI18n 回调)整壳重渲后再调 mount()
    // 触发,同 DXERP.renderCards() 先例——不在本模块自注册,避免旧 host 引用失效后
    // 空跑一次(整壳重渲会替换 #dx-line-card 节点,旧引用已从 DOM 摘除)。
    function mount(hostSel) {
        _host = document.querySelector(hostSel);
        if (_host) load();
    }

    root.DXLINE = { mount: mount };
})(typeof self !== 'undefined' ? self : this);
