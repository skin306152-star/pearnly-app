// ============================================================
// src/home/erp-express-wizard.js · Express 接通向导(P3a · 七步)
//
// 渲染:overlay 向导(选 Express → 装 Agent/生成 token → 选账套[锁 DATAT] →
//   录入方式 RPA/DBF[+风险弹窗] → 字段映射[复用现有] → 测试 → 完成[自动推送默认关])。
// 全站设计令牌(暗夜随令牌)· 不硬编码配色 · 泰语走 t() · 不碰 P1 后端契约。
// 后端开关 ERP_PUSH_ENABLED off 时 token 接口 404 → 优雅提示"未启用",不白屏。
// 由连接卡(erp-express-connect.js)经 window.ExpressWizard.open(ep) 拉起。
// 全局桥(bare):t / escapeHtml / showToast / pearnlyConfirm · token 经 localStorage。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    var ACCOUNT_SETS = [
        { code: 'DATAT', name: '9.ข้อมูลทดสอบ (DATAT)', locked: false },
        { code: 'PDATAT', name: '58ASIA-SPORT (PDATAT)', locked: true },
        { code: 'DATAZ', name: 'Z.ข้อมูลเปล่า (DATAZ)', locked: true },
    ];
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

    // ─── step bodies ────────────────────────────────────
    function _stepper() {
        var out = '';
        for (var i = 1; i <= TOTAL; i++) {
            var cls = i === S.step ? 'active' : i < S.step ? 'done' : '';
            out +=
                '<span class="exp-step-dot ' + cls + '">' + (i < S.step ? '✓' : i) + '</span>';
            if (i < TOTAL) out += '<span class="exp-step-line"></span>';
        }
        return out;
    }

    function _body() {
        if (S.step === 1) return _stepErp();
        if (S.step === 2) return _stepAgent();
        if (S.step === 3) return _stepAccount();
        if (S.step === 4) return _stepMethod();
        if (S.step === 5) return _stepMapping();
        if (S.step === 6) return _stepTest();
        return _stepFinish();
    }

    function _h(hKey: string, subKey: string) {
        return (
            '<div class="exp-step-h">' +
            _esc(_t(hKey)) +
            '</div><div class="exp-step-sub">' +
            _esc(_t(subKey)) +
            '</div>'
        );
    }

    function _stepErp() {
        var opts = [
            { id: 'express', name: 'Express', tag: _t('exp-erp-tag-main'), soon: false },
            { id: 'flowaccount', name: 'FlowAccount', tag: _t('exp-erp-soon'), soon: true },
            { id: 'peak', name: 'PEAK', tag: _t('exp-erp-soon'), soon: true },
            { id: 'xero', name: 'Xero', tag: _t('exp-erp-soon'), soon: true },
        ];
        var grid = opts
            .map(function (o) {
                return (
                    '<div class="exp-erp-opt' +
                    (o.id === 'express' ? ' selected' : o.soon ? ' soon' : '') +
                    '">' +
                    '<div class="exp-erp-name">' +
                    _esc(o.name) +
                    '</div><div class="exp-erp-tag">' +
                    _esc(o.tag) +
                    '</div></div>'
                );
            })
            .join('');
        return _h('exp-s1-h', 'exp-s1-sub') + '<div class="exp-erp-grid">' + grid + '</div>';
    }

    function _stepAgent() {
        var tokenHtml = S.token
            ? '<div class="exp-token-box"><span class="exp-token-val">' +
              _esc(S.token) +
              '</span><button type="button" class="btn btn-ghost btn-tiny" id="exp-copy-token">' +
              _esc(_t('exp-copy')) +
              '</button></div>' +
              '<div class="exp-notice info">' +
              _esc(_t('exp-token-once')) +
              '</div>'
            : '<button type="button" class="btn btn-primary" id="exp-gen-token">' +
              _esc(_t('exp-gen-token')) +
              '</button>';
        var waitCls = S.online ? 'exp-wait online' : 'exp-wait';
        var waitTxt = S.online ? _t('exp-agent-online') : _t('exp-agent-waiting');
        return (
            _h('exp-s2-h', 'exp-s2-sub') +
            '<button type="button" class="btn btn-ghost" id="exp-dl-agent">' +
            _esc(_t('exp-download-agent')) +
            '</button>' +
            '<div style="height:12px"></div>' +
            tokenHtml +
            '<div id="exp-agent-notice"></div>' +
            '<div class="' +
            waitCls +
            '"><span class="exp-wait-dot"></span>' +
            _esc(waitTxt) +
            '</div>'
        );
    }

    function _stepAccount() {
        var list = ACCOUNT_SETS.map(function (a) {
            var sel = a.code === S.accountSet && !a.locked;
            return (
                '<div class="exp-acct-opt' +
                (sel ? ' selected' : '') +
                (a.locked ? ' locked' : '') +
                '" data-acct="' +
                _esc(a.code) +
                '">' +
                '<span class="exp-acct-name">' +
                _esc(a.name) +
                '</span><span class="exp-acct-tag">' +
                _esc(a.locked ? _t('exp-acct-locked') : _t('exp-acct-test')) +
                '</span></div>'
            );
        }).join('');
        return (
            _h('exp-s3-h', 'exp-s3-sub') +
            '<div class="exp-acct-list">' +
            list +
            '</div>' +
            '<div class="exp-notice warn">' +
            _esc(_t('exp-acct-warn')) +
            '</div>'
        );
    }

    function _stepMethod() {
        var card = function (m: string, nameK: string, descK: string) {
            return (
                '<div class="exp-method-card' +
                (S.method === m ? ' selected' : '') +
                '" data-method="' +
                m +
                '"><div class="exp-method-name">' +
                _esc(_t(nameK)) +
                '</div><div class="exp-method-desc">' +
                _esc(_t(descK)) +
                '</div></div>'
            );
        };
        return (
            _h('exp-s4-h', 'exp-s4-sub') +
            '<div class="exp-method-grid">' +
            card('rpa', 'exp-method-rpa', 'exp-method-rpa-desc') +
            card('dbf', 'exp-method-dbf', 'exp-method-dbf-desc') +
            '</div>'
        );
    }

    function _stepMapping() {
        return (
            _h('exp-s5-h', 'exp-s5-sub') +
            '<div class="exp-notice info">' +
            _esc(_t('exp-map-auto')) +
            '</div>' +
            '<button type="button" class="btn btn-ghost" id="exp-open-mappings">' +
            _esc(_t('exp-map-advanced')) +
            '</button>'
        );
    }

    function _stepTest() {
        var row = function (key: string, ok: boolean) {
            return (
                '<div class="exp-check-row"><span class="exp-check-mark' +
                (ok ? '' : ' pending') +
                '">' +
                (ok ? '✓' : '○') +
                '</span>' +
                _esc(_t(key)) +
                '</div>'
            );
        };
        return (
            _h('exp-s6-h', 'exp-s6-sub') +
            '<div class="exp-checklist">' +
            row('exp-test-agent', S.online) +
            row('exp-test-account', true) +
            row('exp-test-mapping', true) +
            '</div>'
        );
    }

    function _stepFinish() {
        return (
            _h('exp-s7-h', 'exp-s7-sub') +
            '<div class="exp-finish-toggle"><div><div class="exp-finish-toggle-label">' +
            _esc(_t('exp-autopush-label')) +
            '</div><div class="exp-finish-toggle-hint">' +
            _esc(_t('exp-autopush-hint')) +
            '</div></div>' +
            '<label class="form-switch-row"><input type="checkbox" id="exp-autopush"' +
            (S.autoPush ? ' checked' : '') +
            '><span class="form-switch-label"></span></label></div>'
        );
    }

    function _foot() {
        var back =
            S.step > 1
                ? '<button type="button" class="btn btn-ghost" id="exp-back">' +
                  _esc(_t('exp-back')) +
                  '</button>'
                : '<button type="button" class="btn btn-ghost" id="exp-cancel">' +
                  _esc(_t('exp-cancel')) +
                  '</button>';
        var nextKey = S.step === TOTAL ? 'exp-done' : 'exp-next';
        var next =
            '<button type="button" class="btn btn-primary" id="exp-next">' +
            _esc(_t(nextKey)) +
            '</button>';
        return (
            '<div class="exp-wiz-foot">' +
            back +
            '<div class="exp-wiz-foot-right">' +
            next +
            '</div></div>'
        );
    }

    function _render() {
        var ov = document.getElementById('exp-wiz-overlay');
        if (!ov) return;
        ov.innerHTML =
            '<div class="exp-wizard" role="dialog" aria-modal="true">' +
            '<div class="exp-wiz-title">' +
            _esc(_t('exp-wizard-title')) +
            '</div>' +
            '<div class="exp-stepper">' +
            _stepper() +
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
            var r = await fetch('/api/erp/endpoints', { headers: { Authorization: 'Bearer ' + _tk() } });
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

    // ─── delegated events ───────────────────────────────
    document.addEventListener('click', function (ev) {
        var tg = ev.target as HTMLElement;
        if (!document.getElementById('exp-wiz-overlay')) return;
        if (tg.closest('#exp-cancel')) return _close();
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
