// src/home/erp-express-wizard.js · Express 接通向导弹窗(照搬 pearnly_express_modal_redesign_v2)
// 双栏:左 3 步流程轨+进度卡 / 右 step1-3+自动推送+高级折叠。body 一次渲染·updateUI 定点更新。
// 接口:生成密钥 POST /agent-token · 连上=心跳轮询 agent_last_seen_at · 账套=heartbeat 上报 · 完成=PATCH endpoint。由连接卡 ExpressWizard.open(ep) 拉起。
/* global escapeHtml */
(function () {
    'use strict';

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

    // 同步背后端点卡(它无自轮询·只 tab 点击刷新),免「向导已连接/卡仍离线」过期快照(铁律#12)。
    function _syncCard() {
        try {
            var ec = (window as any).ExpressConnect;
            if (ec && ec.refresh) ec.refresh();
        } catch (e) {}
    }

    function _close() {
        if (S && S.poll) clearInterval(S.poll);
        var ov = $('exp-wiz-overlay');
        if (ov) ov.remove();
        document.removeEventListener('keydown', _onEsc);
        S = null;
        _syncCard();
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
            pushMode:
                ep && ep.auto_push === false
                    ? 'manual'
                    : (cfg && cfg.autonomy) === 'auto'
                      ? 'full'
                      : 'standard',
            // 科目映射:小助手上报的科目表(下拉数据源)+ 已存的 6 个科目码(预选)。
            accounts: Array.isArray(cfg && cfg.reported_accounts) ? cfg.reported_accounts : [],
            acc: {
                revenue_acc: (cfg && cfg.revenue_acc) || '',
                ar_acc: (cfg && cfg.ar_acc) || '',
                vat_output_acc: (cfg && cfg.vat_output_acc) || '',
                fallback_acc: (cfg && cfg.fallback_acc) || '',
                ap_acc: (cfg && cfg.ap_acc) || '',
                vat_input_acc: (cfg && cfg.vat_input_acc) || '',
            },
            token: '', // 本会话刚生成的明文(只此一次·可显隐复制)
            // 长效密钥模型:配过的连接 config 带 agent_token_tail → 重开只显掩码,不诱导重置。
            hasKey: !!(cfg && cfg.agent_token_tail),
            tail: (cfg && cfg.agent_token_tail) || '',
            device: (cfg && cfg.agent_device_name) || '', // 连上的电脑名(链接设备身份)
            keyRevealed: true, // 刚生成时默认显示(便于复制),点眼睛切换
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
        ov.innerHTML = st ? st.renderShell({ S: S, t: _t, esc: _esc }) : '';
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
        (window as any).ExpressSteps.fillAcctMirror(S, _t);
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
            if (tx) {
                var base = _t(S.connected ? 'exp-topstatus-online' : 'exp-topstatus-waiting');
                tx.textContent = S.connected && S.device ? base + ' · ' + S.device : base; // 显示连的是哪台电脑
            }
        }

        _keyArea();

        var pm = document.querySelector(
            'input[name="exp-pushmode"][value="' + S.pushMode + '"]'
        ) as HTMLInputElement;
        if (pm) pm.checked = true;

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

    // 展示辅助(密钥区/账套镜像/滚动)抽到 ExpressSteps(编排/展示分离·见 erp-express-steps)。
    function _keyArea() {
        (window as any).ExpressSteps.renderKeyArea(S, _t);
    }
    function _toggleEye() {
        if (!S || !S.token) return;
        S.keyRevealed = !S.keyRevealed;
        _keyArea();
    }
    function _scrollToStep(target: string) {
        (window as any).ExpressSteps.scrollToStep(target);
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
        // 下载地址以云端 latest.json 为唯一发布源(release 脚本更新它·小助手自动更新也读它)→
        // 永远指向最新安装包,发版不必再手动 bump 前端 ?v=。取不到则回落到兜底直链;
        // 兜底用时间戳破缓存(不留会过期的手动 ?v=),保证回落也取到当前已部署的安装包。
        var SETUP_URL = '/static/companion/PearnlyCompanion-Setup.exe?t=' + Date.now();
        try {
            var lr = await fetch('/static/companion/latest.json?t=' + Date.now());
            if (lr.ok) {
                var meta = await lr.json();
                if (meta && meta.url) SETUP_URL = String(meta.url);
            }
        } catch (e) {}
        try {
            var head = await fetch(SETUP_URL, { method: 'HEAD' });
            if (!head.ok) {
                _toast(_t(head.status === 404 ? 'exp-download-not-ready' : 'exp-download-fail'));
                if (btn) btn.disabled = false;
                return;
            }
            var a = document.createElement('a');
            a.href = SETUP_URL;
            a.download = 'PearnlyCompanion-Setup.exe';
            document.body.appendChild(a);
            a.click();
            a.remove();
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
        // 长效密钥:已配过 → 这是「重置」危险动作(旧密钥作废·所有已配电脑掉线),强确认。
        var isReset = !!(S.hasKey || S.token);
        if (isReset && (window as any).showConfirm) {
            var ok = await (window as any).showConfirm(_t('exp-regen-warn'), { danger: true });
            if (!ok) return;
        }
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
                body: JSON.stringify({ reset: isReset }),
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
            S.tail = (d && d.tail) || S.tail;
            S.hasKey = true;
            S.generated = true;
            S.keyRevealed = true;
            updateUI();
            _toast(_t(isReset ? 'exp-toast-key-reset' : 'exp-toast-key-generated'));
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
            var dev = cfg.agent_device_name ? String(cfg.agent_device_name) : '';
            var changed = false;
            if (online !== S.connected) {
                S.connected = online;
                changed = true;
            }
            if (dev !== S.device) {
                S.device = dev;
                changed = true;
            }
            if (selected !== S.account || selectedName !== S.accountName) {
                S.account = selected;
                S.accountName = selectedName;
                changed = true;
            }
            if (changed) {
                updateUI();
                _syncCard(); // 在线状态翻转 → 背后端点卡立即同步,不等用户重点 tab
            }
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
                if (S.push) {
                    await fetch(
                        '/api/erp/endpoints/' + encodeURIComponent(id) + '/express-autonomy',
                        {
                            method: 'PATCH',
                            headers: _auth(),
                            body: JSON.stringify({
                                autonomy: S.pushMode === 'full' ? 'auto' : 'standard',
                            }),
                        }
                    );
                }
                // 科目映射现由小助手选定并随心跳上报(网页只读镜像),finish 不再写科目。
            } catch (e) {}
        }
        _close();
        _toast(_t('exp-setup-done'));
    }

    // ─── 事件(委托)─────────────────────────────────────────
    document.addEventListener('click', function (ev) {
        if (!$('exp-wiz-overlay')) return;
        var tg = ev.target as HTMLElement;
        if (tg.closest('#exp-close') || tg.closest('#exp-cancel')) return _close();
        if (tg.closest('#exp-done')) return _finish();
        if (tg.closest('#exp-generate')) return _genToken();
        if (tg.closest('#exp-eye')) return _toggleEye();
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
        if (tg && (tg as HTMLInputElement).name === 'exp-pushmode' && S) {
            S.pushMode = (tg as HTMLInputElement).value;
            S.push = S.pushMode !== 'manual';
            updateUI();
            _toast(_t('exp-toast-mode-saved'));
        }
    });

    (window as any).ExpressWizard = { open: open };
})();
