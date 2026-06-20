// ============================================================
// src/home/erp-express-wizard.js · Express 接通向导(P3a · 双栏七步 · 照原型 .wizard)
//
// 左栏竖排步骤面板 + 右栏步骤内容:选 Express → 装 Agent/生成 token → 选账套[锁 DATAT]
//   → 录入方式 RPA/DBF[+风险弹窗] → 字段映射[复用现有] → 测试 → 完成[自动推送默认关]。
// 全站设计令牌(暗夜随令牌)· 泰语走 t() · token 接口 404 → 优雅提示"未启用"不白屏。
// 由连接卡经 window.ExpressWizard.open(ep) 拉起 · 全局桥:t / escapeHtml / showToast。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    var TOTAL = 7;

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
        S = {
            step: 1,
            ep: ep || null,
            id: ep && ep.id ? ep.id : null,
            method: (ep && ep.config && ep.config.method) || 'rpa',
            dbfAck: false,
            accountSet: 'DATAT',
            autoPush: false,
            token: '',
            online: false,
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
    }

    // ─── 左栏竖排步骤面板(照原型 .wizard-side · 令牌着色)─────
    // prettier-ignore
    var STEP_LABELS = ['exp-step-1','exp-step-2','exp-step-3','exp-step-4','exp-step-5','exp-step-6','exp-step-7'];
    function _sideSteps() {
        var out = '';
        for (var i = 1; i <= TOTAL; i++) {
            var cls = i === S.step ? 'active' : i < S.step ? 'done' : '';
            var num = i < S.step ? '✓' : String(i);
            out +=
                '<div class="exp-step ' +
                cls +
                '"><span class="exp-step-num">' +
                num +
                '</span><span class="exp-step-label">' +
                _esc(_t(STEP_LABELS[i - 1])) +
                '</span></div>';
        }
        return out;
    }

    function _body() {
        var st = (window as any).ExpressSteps;
        return st ? st.render(S.step, { S: S, t: _t, esc: _esc }) : '';
    }

    function _foot() {
        // 底栏:左「保存草稿」· 右「上一步 / 下一步」(照原型 .wizard-footer)。
        var draft =
            '<button type="button" class="btn btn-ghost" id="exp-save-draft">' +
            _esc(_t('exp-save-draft')) +
            '</button>';
        var back =
            S.step > 1
                ? '<button type="button" class="btn btn-ghost" id="exp-back">' +
                  _esc(_t('exp-back')) +
                  '</button>'
                : '';
        var nextKey = S.step === TOTAL ? 'exp-done' : 'exp-next';
        var next =
            '<button type="button" class="btn btn-primary" id="exp-next">' +
            _esc(_t(nextKey)) +
            '</button>';
        return (
            '<div class="exp-wiz-footer">' +
            draft +
            '<div class="exp-wiz-foot-right">' +
            back +
            next +
            '</div></div>'
        );
    }

    function _render() {
        // 双栏宽弹窗(照原型 .wizard):左栏竖排步骤面板 + 右栏步骤内容 + 底栏。
        var ov = document.getElementById('exp-wiz-overlay');
        if (!ov) return;
        ov.innerHTML =
            '<div class="exp-wizard" role="dialog" aria-modal="true">' +
            '<div class="exp-wiz-side">' +
            '<div class="exp-wiz-side-title">' +
            _esc(_t('exp-wiz-side-title')) +
            '</div>' +
            '<div class="exp-wiz-side-sub">' +
            _esc(_t('exp-wiz-side-sub')) +
            '</div>' +
            '<div class="exp-steps">' +
            _sideSteps() +
            '</div></div>' +
            '<div class="exp-wiz-main">' +
            '<div class="exp-wiz-content">' +
            _body() +
            '</div>' +
            _foot() +
            '</div></div>';
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
                    config: { account_set: 'DATAT', method: S.method },
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
            var seen = ep && ep.config && ep.config.agent_last_seen_at;
            var online = seen ? Date.now() - new Date(seen).getTime() < 180000 : false;
            if (online && !S.online) {
                S.online = true;
                if (S.step === 2) _render();
            }
        } catch (e) {}
    }

    async function _copyToken() {
        try {
            await navigator.clipboard.writeText(S.token);
            _toast(_t('exp-copied'), 'success');
        } catch (e) {}
    }

    function _dbfRiskGate(): Promise<boolean> {
        // 录入方式 DBF 风险确认弹窗(brief P7)· 勾选"我已了解风险"才放行 · 独立文件。
        var rk = (window as any).ExpressDbfRisk;
        if (rk && typeof rk.confirm === 'function') return rk.confirm();
        return Promise.resolve(false);
    }

    function _openMappings() {
        _close();
        var btn = document.querySelector('.erp-subtab[data-erp-subtab="mappings"]') as HTMLElement;
        if (btn) btn.click();
    }

    async function _finish() {
        var id = await _ensureEndpoint();
        if (id) {
            try {
                await fetch('/api/erp/endpoints/' + encodeURIComponent(id), {
                    method: 'PATCH',
                    headers: _auth(),
                    body: JSON.stringify({
                        config: { account_set: 'DATAT', method: S.method },
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

    async function _next() {
        if (S.step === TOTAL) {
            _finish();
            return;
        }
        S.step++;
        _render();
    }

    async function _saveDraft() {
        // 保存草稿:落一条未完成连接(已建则保留)· 关闭 · 刷新卡片(显「未完成」)。
        await _ensureEndpoint();
        _close();
        _toast(_t('exp-draft-saved'), 'info');
        _refreshCard();
    }

    // ─── delegated events ───────────────────────────────
    document.addEventListener('click', function (ev) {
        var tg = ev.target as HTMLElement;
        if (!document.getElementById('exp-wiz-overlay')) return;
        if (tg.closest('#exp-cancel')) return _close();
        if (tg.closest('#exp-save-draft')) return _saveDraft();
        if (tg.closest('#exp-back')) {
            S.step = Math.max(1, S.step - 1);
            return _render();
        }
        if (tg.closest('#exp-next')) return _next();
        if (tg.closest('#exp-gen-token')) return _genToken();
        if (tg.closest('#exp-copy-token')) return _copyToken();
        if (tg.closest('#exp-dl-agent')) return _toast(_t('exp-download-soon'), 'info');
        if (tg.closest('#exp-open-mappings')) return _openMappings();
        var acct = tg.closest('.exp-acct-opt') as HTMLElement;
        if (acct && !acct.classList.contains('locked')) {
            S.accountSet = acct.getAttribute('data-acct') || 'DATAT';
            return _render();
        }
        var method = tg.closest('.exp-method-card') as HTMLElement;
        if (method) {
            var m = method.getAttribute('data-method') || 'rpa';
            if (m === 'dbf') {
                _dbfRiskGate().then(function (ok) {
                    if (ok) {
                        S.method = 'dbf';
                        S.dbfAck = true;
                        _render();
                    }
                });
            } else {
                S.method = 'rpa';
                _render();
            }
            return;
        }
    });

    document.addEventListener('change', function (ev) {
        var tg = ev.target as HTMLElement;
        if (tg && tg.id === 'exp-autopush') S.autoPush = (tg as HTMLInputElement).checked;
    });

    (window as any).ExpressWizard = { open: open };
})();
