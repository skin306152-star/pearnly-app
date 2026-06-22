// ============================================================
// src/home/erp-express-wizard.js · Express 接通向导弹窗(重设计 v2 · 照搬结构/流程/交互)
//
// 照搬 pearnly_express_modal_redesign_v2.html:双栏弹窗(左流程轨 3 步 + 进度卡 / 右内容滚动
// 区 step1-3 + 自动推送 + 高级折叠)+ 头部 mini-status + 底部完成 gating。结构/分步/交互/文案
// 一字照搬,仅:CSS 走令牌、字符图标→线性 SVG、class 加 exp- 前缀、演示桩接真接口。
//
// 真接口:生成密钥 = POST /agent-token;连上 = 心跳轮询(agent_last_seen_at);账套 = 读
// heartbeat 上报的 reported_account_sets;完成 = PATCH endpoint(account_set + auto_push)。
// body 一次渲染,状态由 updateUI 定点更新(保平滑滚动);由连接卡 ExpressWizard.open(ep) 拉起。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    var IC_CLOSE =
        '<svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4l8 8M12 4l-8 8"/></svg>';

    var S: any = null;

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
    function _toast(msg: string) {
        try {
            if (typeof showToast === 'function') showToast(msg, 'info');
        } catch (e) {}
    }
    function _tk() {
        return localStorage.getItem('mrpilot_token');
    }
    function _auth() {
        return { Authorization: 'Bearer ' + _tk(), 'Content-Type': 'application/json' };
    }
    function $(id: string) {
        return document.getElementById(id);
    }

    function _close() {
        if (S && S.poll) clearInterval(S.poll);
        var ov = $('exp-wiz-overlay');
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
            downloaded: false,
            generated: false,
            connected: false,
            account: cfg && cfg.account_set ? String(cfg.account_set) : null, // 账套唯一键 = PATH(小助手上报)
            accountName: cfg && cfg.account_company ? String(cfg.account_company) : null, // 显示用真公司名
            push: !(ep && ep.auto_push === false), // 默认开启(照搬文案「默认开启」)
            token: '',
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
        _renderShell();
        updateUI();
        if (S.id) _startPoll(); // 编辑既有连接:进来即探在线
    }

    function _renderShell() {
        var ov = $('exp-wiz-overlay');
        if (!ov) return;
        var st = (window as any).ExpressSteps;
        var body = st ? st.render({ S: S, t: _t, esc: _esc }) : '';
        ov.innerHTML =
            '<section class="exp-modal" role="dialog" aria-modal="true" aria-labelledby="exp-modal-title">' +
            '<header class="exp-modal-header"><div class="exp-mh-title">' +
            '<div class="exp-mh-icon">Ex</div><div>' +
            '<h2 class="exp-mh-h2" id="exp-modal-title">' +
            _esc(_t('exp-wizard-title')) +
            '</h2><p class="exp-mh-lead">' +
            _esc(_t('exp-s1-sub')) +
            '</p></div></div><div class="exp-mh-actions">' +
            '<div class="exp-topstatus" id="exp-topstatus"><span class="exp-pulse"></span><span class="exp-ts-text"></span></div>' +
            '<button class="exp-iconbtn" id="exp-close" aria-label="' +
            _esc(_t('exp-cancel')) +
            '">' +
            IC_CLOSE +
            '</button></div></header>' +
            body +
            '<footer class="exp-footer"><div class="exp-footer-note" id="exp-footer-note"></div>' +
            '<div class="exp-footer-actions">' +
            '<button class="exp-secondary" id="exp-cancel">' +
            _esc(_t('exp-cancel')) +
            '</button><button class="exp-primary" id="exp-done" disabled>' +
            _esc(_t('exp-done')) +
            '</button></div></footer></section>';
    }

    // ─── updateUI(照搬源 · 定点更新)──────────────────────────
    function _badge(id: string, key: string, kind: string) {
        var el = $(id);
        if (el) {
            el.textContent = _t(key);
            el.className = 'exp-badge ' + kind;
        }
    }
    function _rail(id: string, cls: string) {
        var el = $(id);
        if (!el) return;
        el.classList.remove('done', 'waiting');
        if (cls) el.classList.add(cls);
    }
    function _txt(id: string, v: string) {
        var el = $(id);
        if (el) el.textContent = v;
    }

    function updateUI() {
        if (!S) return;
        // 小助手连上(heartbeat)本身就证明装好了 → step1 不强制下载。
        var step1done = !!(S.downloaded || S.connected);
        var completed = (step1done ? 1 : 0) + (S.connected ? 1 : 0) + (S.account ? 1 : 0);
        var bar = $('exp-bar');
        if (bar) bar.style.width = (completed / 3) * 100 + '%';

        if (step1done) {
            _badge('exp-badge1', 'exp-badge-done', 'done');
            _rail('exp-rail1', 'done');
            if (S.downloaded) {
                _txt('exp-download', _t('exp-download-done'));
                _txt('exp-download-hint', _t('exp-download-hint-2'));
            }
            _badge(
                'exp-badge2',
                S.connected
                    ? 'exp-badge-connected'
                    : S.generated
                      ? 'exp-badge-generated'
                      : 'exp-badge-gen-ready',
                S.connected ? 'done' : 'waiting'
            );
            _rail('exp-rail2', S.connected ? 'done' : 'waiting');
        } else {
            _badge('exp-badge1', 'exp-badge-todo', 'waiting');
            _rail('exp-rail1', 'waiting');
            _badge('exp-badge2', 'exp-badge-wait-prev', 'todo');
            _rail('exp-rail2', '');
        }

        var ts = $('exp-topstatus');
        _fillAcctMirror();
        if (S.connected) {
            _badge(
                'exp-badge3',
                S.account ? 'exp-badge-selected' : 'exp-badge-can-select',
                S.account ? 'done' : 'waiting'
            );
            _rail('exp-rail3', S.account ? 'done' : 'waiting');
            if (ts) ts.classList.add('online');
        } else {
            _badge('exp-badge3', 'exp-badge-wait-conn', 'todo');
            _rail('exp-rail3', '');
            if (ts) ts.classList.remove('online');
        }
        if (ts) {
            var tx = ts.querySelector('.exp-ts-text');
            if (tx)
                tx.textContent = _t(S.connected ? 'exp-topstatus-online' : 'exp-topstatus-waiting');
        }

        if (S.generated) {
            var cb = $('exp-codebox');
            if (cb) cb.style.display = 'grid';
        }

        var pt = $('exp-pushtoggle') as HTMLInputElement;
        if (pt) pt.checked = !!S.push;

        var left = 3 - completed;
        _txt(
            'exp-progress-title',
            left === 0 ? _t('exp-prog-done') : _t('exp-prog-left').replace('{n}', String(left))
        );
        var ptKey = !S.downloaded
            ? 'exp-prog-text-1'
            : !S.connected
              ? 'exp-prog-text-2'
              : !S.account
                ? 'exp-prog-text-3'
                : S.push
                  ? 'exp-prog-text-push-on'
                  : 'exp-prog-text-push-off';
        _txt('exp-progress-text', _t(ptKey));

        var done = $('exp-done') as HTMLButtonElement;
        var ready = !!(S.connected && S.account); // 下载不再是硬门;连上 + 账套已选即可完成
        if (done) done.disabled = !ready;
        _txt('exp-footer-note', _t(ready ? 'exp-footer-note-ready' : 'exp-footer-note-todo'));
    }

    function _fillAcctMirror() {
        var el = $('exp-acct-mirror');
        if (!el) return;
        if (S.account) {
            el.className = 'exp-account-mirror selected';
            // 显示真公司名(account_company);account_set 现为账套 PATH·不适合给客户看。
            var shown = S.accountName || S.account;
            el.textContent = _t('exp-acct-selected-mirror').replace('{x}', String(shown)) + ' ✓';
        } else {
            el.className = 'exp-account-mirror waiting';
            el.textContent = _t('exp-acct-wait-select');
        }
    }

    function _scrollToStep(target: string) {
        var scroller = $('exp-scroll');
        var el = $(target);
        if (scroller && el) scroller.scrollTo({ top: el.offsetTop - 18, behavior: 'smooth' });
        var links = document.querySelectorAll('.exp-step-link');
        for (var i = 0; i < links.length; i++) links[i].classList.remove('active');
        var active = document.querySelector('[data-target="' + target + '"]');
        if (active) active.classList.add('active');
    }

    // ─── 真接口 ──────────────────────────────────────────────
    async function _ensureEndpoint() {
        if (S.id) return S.id;
        try {
            var r = await fetch('/api/erp/endpoints', {
                method: 'POST',
                headers: _auth(),
                body: JSON.stringify({
                    name: 'Express',
                    adapter: 'express',
                    // account_set 不在此硬塞:唯一真相源 = 小助手所选账套(经 heartbeat 上报存入 config)。
                    config: { method: 'dbf' },
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
        var el = $('exp-agent-notice');
        if (el) el.innerHTML = '<div class="exp-notice ' + kind + '">' + _esc(msg) + '</div>';
    }

    async function _downloadAgent() {
        var btn = $('exp-download') as HTMLButtonElement;
        if (btn) btn.disabled = true;
        try {
            var r = await fetch('/api/companion/installer', {
                headers: { Authorization: 'Bearer ' + _tk() },
            });
            if (!r.ok) {
                _toast(_t(r.status === 404 ? 'exp-download-not-ready' : 'exp-download-fail'));
                if (btn) btn.disabled = false;
                return;
            }
            var blob = await r.blob();
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'PearnlyCompanion-Setup.exe';
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(function () {
                URL.revokeObjectURL(url);
            }, 4000);
            S.downloaded = true;
            updateUI();
            _toast(_t('exp-toast-downloaded'));
            setTimeout(function () {
                _scrollToStep('exp-step2');
            }, 200);
        } catch (e) {
            _toast(_t('exp-download-fail'));
            if (btn) btn.disabled = false;
        }
    }

    async function _genToken() {
        // 下载不再是硬门:已装客户(没点下载)也能直接生成密钥。
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
            _txt('exp-codeval', S.token);
            S.generated = true;
            updateUI();
            _toast(_t('exp-toast-key-generated'));
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
            // 账套唯一真相源 = 小助手上报的 cfg.account_set(= 账套 PATH·唯一键);显示用真公司名。
            var selected = cfg.account_set ? String(cfg.account_set) : null;
            var selectedName = cfg.account_company ? String(cfg.account_company) : null;
            var changed = false;
            if (online && !S.connected) {
                S.connected = true;
                changed = true;
            }
            if (selected !== S.account || selectedName !== S.accountName) {
                S.account = selected;
                S.accountName = selectedName;
                changed = true;
            }
            if (changed) updateUI();
        } catch (e) {}
    }

    async function _copy() {
        try {
            await navigator.clipboard.writeText(S.token || ($('exp-codeval')?.textContent ?? ''));
            _toast(_t('exp-toast-copied'));
        } catch (e) {
            _toast(_t('exp-toast-copy-manual'));
        }
    }

    async function _finish() {
        var id = await _ensureEndpoint();
        if (id) {
            try {
                // account_set 以小助手上报为准(heartbeat 已存),finish 只确认连接 + 自动推送开关。
                await fetch('/api/erp/endpoints/' + encodeURIComponent(id), {
                    method: 'PATCH',
                    headers: _auth(),
                    body: JSON.stringify({ auto_push: S.push }),
                });
            } catch (e) {}
        }
        _close();
        _toast(_t('exp-setup-done'));
        try {
            var ec = (window as any).ExpressConnect;
            if (ec && ec.refresh) ec.refresh();
        } catch (e) {}
    }

    // ─── 事件(委托)─────────────────────────────────────────
    document.addEventListener('click', function (ev) {
        if (!$('exp-wiz-overlay')) return;
        var tg = ev.target as HTMLElement;
        if (tg.closest('#exp-close') || tg.closest('#exp-cancel')) return _close();
        if (tg.closest('#exp-done')) return _finish();
        if (tg.closest('#exp-generate')) return _genToken();
        if (tg.closest('#exp-copy')) return _copy();
        if (tg.closest('#exp-download')) {
            _downloadAgent();
            return;
        }
        if (tg.closest('#exp-skip-download')) {
            // 已装客户:标记 step1 完成,不触发下载。
            S.downloaded = true;
            updateUI();
            _scrollToStep('exp-step2');
            return;
        }
        var link = tg.closest('.exp-step-link') as HTMLElement;
        if (link) return _scrollToStep(link.getAttribute('data-target') || 'exp-step1');
        var fold = tg.closest('[data-fold]') as HTMLElement;
        if (fold) {
            var panel = $(fold.getAttribute('data-fold') || '');
            if (panel) panel.classList.toggle('collapsed');
            return;
        }
        if (tg.closest('#exp-direct-help-btn')) {
            ev.preventDefault();
            ev.stopPropagation();
            var hp = $('exp-direct-help');
            var btn = $('exp-direct-help-btn');
            if (hp && btn) {
                var show = !hp.classList.contains('show');
                hp.classList.toggle('show', show);
                hp.setAttribute('aria-hidden', show ? 'false' : 'true');
                btn.textContent = _t(show ? 'exp-direct-help-hide' : 'exp-direct-help-show');
            }
            return;
        }
    });

    document.addEventListener('change', function (ev) {
        var tg = ev.target as HTMLElement;
        if (tg && tg.id === 'exp-pushtoggle' && S) {
            S.push = (tg as HTMLInputElement).checked;
            updateUI();
            _toast(_t(S.push ? 'exp-toast-push-on' : 'exp-toast-push-off'));
        }
    });

    (window as any).ExpressWizard = { open: open };
})();
