// ============================================================
// src/home/erp-express-wizard.js · Express 接通向导(单弹窗一屏 · 对齐桌面交互草稿)
//
// 一屏走完:装小助手 → 生成配对码 + 复制(粘进小助手回连)→ 连上后选账套
//   (读小助手心跳上报的账套)→ 自动推送(默认开)→ 完成。后台默认直写(method=dbf),
//   用户不看「录入方式」选择;字段映射/测试后台自动,异常进待确认,不在配置里出现。
// 全站设计令牌(暗夜随令牌)· 泰语走 t() · token 接口 404 → 优雅提示「未启用」不白屏。
// 由连接卡经 window.ExpressWizard.open(ep) 拉起 · 全局桥:t / escapeHtml / showToast。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    var S: any = null; // wizard state

    function _esc(s: any) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function _t(k: string) {
        try {
            var v = typeof t === 'function' ? t(k) : k;
            return v || k;
        } catch (e) {
            return k;
        }
    }
    function _toast(msg: any, kind?: any) {
        try {
            if (typeof showToast === 'function') showToast(msg, kind || 'info');
        } catch (e) {}
    }
    function _tk() {
        return localStorage.getItem('mrpilot_token');
    }
    function _auth() {
        return { Authorization: 'Bearer ' + _tk(), 'Content-Type': 'application/json' };
    }

    function _close() {
        if (S && S.poll) clearInterval(S.poll);
        var ov = document.getElementById('exp-wiz-overlay');
        if (ov) ov.remove();
        document.removeEventListener('keydown', _onEsc);
        S = null;
    }
    function _onEsc(e: KeyboardEvent) {
        if (e.key === 'Escape') _close();
    }

    function open(ep?: any) {
        _close();
        var cfg = (ep && ep.config) || {};
        S = {
            ep: ep || null,
            id: ep && ep.id ? ep.id : null,
            accountSet: cfg.account_set || null,
            accounts: cfg.account_set ? [String(cfg.account_set)] : [],
            autoPush: ep && typeof ep.auto_push === 'boolean' ? ep.auto_push : true,
            token: '',
            online: false,
            explainerOpen: false,
            advancedOpen: false,
            poll: null,
        };
        var ov = document.createElement('div');
        ov.id = 'exp-wiz-overlay';
        ov.className = 'exp-wiz-overlay';
        document.body.appendChild(ov);
        document.addEventListener('keydown', _onEsc);
        ov.addEventListener('click', function (e) {
            if (e.target === ov) _close();
        });
        _render();
        if (S.id) _startPoll(); // 编辑既有连接:进来即探小助手是否在线
    }

    function _body() {
        var st = (window as any).ExpressSteps;
        return st ? st.render({ S: S, t: _t, esc: _esc }) : '';
    }

    function _foot() {
        var ready = !!(S.online && S.accountSet);
        var cancel =
            '<button type="button" class="btn btn-ghost" id="exp-cancel">' +
            _esc(_t('exp-cancel')) +
            '</button>';
        var done =
            '<button type="button" class="btn btn-primary" id="exp-finish"' +
            (ready ? '' : ' disabled') +
            '>' +
            _esc(_t('exp-done')) +
            '</button>';
        return (
            '<div class="exp-wiz-footer">' +
            cancel +
            '<div class="exp-wiz-foot-right">' +
            done +
            '</div></div>'
        );
    }

    function _render() {
        // 单栏弹窗(复用 .exp-risk-modal 单栏卡):标题 + 引导 + 一屏内容 + 底栏。
        var ov = document.getElementById('exp-wiz-overlay');
        if (!ov) return;
        ov.innerHTML =
            '<div class="exp-risk-modal" role="dialog" aria-modal="true">' +
            '<div class="exp-wiz-title">' +
            _esc(_t('exp-wizard-title')) +
            '</div><div class="exp-step-sub">' +
            _esc(_t('exp-s1-sub')) +
            '</div>' +
            _body() +
            _foot() +
            '</div>';
    }

    // ─── actions ────────────────────────────────────────
    async function _ensureEndpoint() {
        if (S.id) return S.id;
        try {
            var r = await fetch('/api/erp/endpoints', {
                method: 'POST',
                headers: _auth(),
                body: JSON.stringify({
                    name: 'Express',
                    adapter: 'express',
                    config: { account_set: 'DATAT', method: 'dbf' },
                    is_default: false,
                    auto_push: false,
                }),
            });
            if (!r.ok) return null;
            var d = await r.json();
            S.id = d && d.id;
            S.ep = d;
            return S.id;
        } catch (e) {
            return null;
        }
    }

    function _notice(kind: string, msg: string) {
        var el = document.getElementById('exp-agent-notice');
        if (el) el.innerHTML = '<div class="exp-notice ' + kind + '">' + _esc(msg) + '</div>';
    }

    async function _genToken() {
        var id = await _ensureEndpoint();
        if (!id) {
            _notice('danger', _t('exp-token-fail'));
            return;
        }
        try {
            var r = await fetch('/api/erp/endpoints/' + encodeURIComponent(id) + '/agent-token', {
                method: 'POST',
                headers: _auth(),
            });
            if (r.status === 404) {
                _notice('warn', _t('exp-token-disabled'));
                return;
            }
            if (!r.ok) {
                _notice('danger', _t('exp-token-fail'));
                return;
            }
            var d = await r.json();
            S.token = (d && d.token) || '';
            _render();
            _startPoll();
        } catch (e) {
            _notice('danger', _t('exp-token-fail'));
        }
    }

    function _startPoll() {
        if (S.poll) clearInterval(S.poll);
        S.poll = setInterval(_checkAgent, 5000);
        _checkAgent();
    }
    async function _checkAgent() {
        try {
            var r = await fetch('/api/erp/endpoints', {
                headers: { Authorization: 'Bearer ' + _tk() },
            });
            if (!r.ok) return;
            var d = await r.json();
            var ep = ((d && d.items) || []).find(function (e: any) {
                return e && (e.adapter || '').toLowerCase() === 'express';
            });
            if (!ep) return;
            var cfg = ep.config || {};
            var seen = cfg.agent_last_seen_at;
            var online = seen ? Date.now() - new Date(seen).getTime() < 180000 : false;
            var acct = cfg.account_set ? String(cfg.account_set) : '';
            var accounts = acct ? [acct] : [];
            var changed =
                online !== S.online || accounts.join(',') !== (S.accounts || []).join(',');
            S.online = online;
            S.accounts = accounts;
            // 自动选中小助手心跳上报的账套(目前后台单账套 · 多账套探测是后续 companion 活)。
            if (online && acct && !S.accountSet) S.accountSet = acct;
            if (changed) _render();
        } catch (e) {}
    }

    async function _copyToken() {
        try {
            await navigator.clipboard.writeText(S.token);
            _toast(_t('exp-copied'), 'success');
        } catch (e) {}
    }

    async function _finish() {
        var id = await _ensureEndpoint();
        if (id) {
            try {
                await fetch('/api/erp/endpoints/' + encodeURIComponent(id), {
                    method: 'PATCH',
                    headers: _auth(),
                    body: JSON.stringify({
                        config: { account_set: S.accountSet || 'DATAT', method: 'dbf' },
                        auto_push: S.autoPush,
                    }),
                });
            } catch (e) {}
        }
        _close();
        _toast(_t('exp-setup-done'), 'success');
        _refreshCard();
    }

    function _refreshCard() {
        try {
            var ec = (window as any).ExpressConnect;
            if (ec && ec.refresh) ec.refresh();
        } catch (e) {}
    }

    // ─── delegated events ───────────────────────────────
    document.addEventListener('click', function (ev) {
        var tg = ev.target as HTMLElement;
        if (!document.getElementById('exp-wiz-overlay')) return;
        if (tg.closest('#exp-cancel')) return _close();
        if (tg.closest('#exp-finish')) return _finish();
        if (tg.closest('#exp-gen-token')) return _genToken();
        if (tg.closest('#exp-copy-token')) return _copyToken();
        if (tg.closest('#exp-dl-agent')) return _toast(_t('exp-download-soon'), 'info');
        if (tg.closest('#exp-how-toggle')) {
            S.explainerOpen = !S.explainerOpen;
            return _render();
        }
        if (tg.closest('#exp-adv-toggle')) {
            S.advancedOpen = !S.advancedOpen;
            return _render();
        }
        if (tg.closest('.exp-method-card[data-method="rpa-soon"]'))
            return _toast(_t('exp-method-soon-note'), 'info');
        var acct = tg.closest('.exp-acct-opt') as HTMLElement;
        if (acct) {
            S.accountSet = acct.getAttribute('data-acct') || S.accountSet;
            return _render();
        }
    });

    document.addEventListener('change', function (ev) {
        var tg = ev.target as HTMLElement;
        if (tg && tg.id === 'exp-autopush') S.autoPush = (tg as HTMLInputElement).checked;
    });

    (window as any).ExpressWizard = { open: open };
})();
