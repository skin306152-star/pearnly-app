// ============================================================
// REFACTOR-C1 (2026-05-25) · 测试中心(Test Center)从 home.js 抽出为 ES module
//
// 来源:home.js v118.28.1.0 的「测试中心」IIFE(L17441-17937 · skin 白名单 only)
// 加载顺序:home.html <script src=home.js>(sync)先跑 → 本 module(Vite bundle ·
//   type=module defer)后跑 · 所以 home.js 暴露的全局(t / escapeHtml / apiGet /
//   showToast / _userInfo / currentRoute / window._pearnlyTcLogs / subscribeI18n)
//   在本 module 执行(setInterval 轮询 + 用户进 #/test-center 调 window.loadTestCenterPage)
//   时已就绪。
// 入口:window.loadTestCenterPage(home.js 路由 L832 经 window 调)·
//   window._tcOnNewLog(错误拦截器经 window 调)· window._tcApplyVisibility(no-op 兼容)。
// verbatim 搬迁 · 0 改逻辑(仅 prettier 重排格式)。
// ============================================================
// ============================================================
// v118.28.1.0 · 测试中心(Test Center · TC)
//   - 入口:user_id 白名单 OR ?test_center=1 OR localStorage.pearnly_test_mode='1'
//   - 区 1:测试清单(localStorage 持久化勾选)
//   - 区 2:异常日志(从 _pearnlyTcLogs 读 · 实时刷新)
//   - 区 4:工具(健康检查 / 清空 session / 强制刷客户缓存)
//   - 复制到剪贴板:markdown 格式 · 一键贴给 Claude
//   - subscribeI18n 注册 · 切语言重渲
// ============================================================
import {
    LS_RESULTS,
    CHECKLIST,
    S,
    _t,
    _loadResults,
    _saveResults,
    _fmtTime,
    _esc,
    _toast,
    _copyToClipboard,
    _buildResultsMarkdown,
    _buildLogsMarkdown,
} from './test-center-base.js'; // REFACTOR-WB-modularize · 数据/状态/工具/markdown
(function () {
    'use strict';
    // ---------- 渲染:状态条 ----------
    function _renderStatusBar() {
        const acc = document.getElementById('tc-account-chip');
        const prog = document.getElementById('tc-progress-chip');
        if (acc) acc.textContent = (_userInfo && (_userInfo.email || _userInfo.username)) || '—';
        if (prog) {
            const total = CHECKLIST.length;
            const done = CHECKLIST.filter(function (it) {
                return S.results[it.id];
            }).length;
            prog.textContent = done + ' / ' + total;
        }
    }

    // ---------- 渲染:测试清单 ----------
    function _renderChecklist() {
        const wrap = document.getElementById('tc-checklist-body');
        if (!wrap) return;
        const groups = {};
        CHECKLIST.forEach(function (it) {
            if (!groups[it.group]) groups[it.group] = [];
            groups[it.group].push(it);
        });
        const html = [];
        Object.keys(groups).forEach(function (g) {
            html.push('<div class="tc-checklist-group">');
            html.push('<div class="tc-checklist-group-title">' + _esc(g) + '</div>');
            groups[g].forEach(function (it) {
                const st = S.results[it.id] || '';
                const cls = st ? 'is-' + st : '';
                html.push(
                    '<div class="tc-check-item ' +
                        cls +
                        '" data-id="' +
                        _esc(it.id) +
                        '">' +
                        '<div class="tc-check-id">' +
                        _esc(it.id) +
                        '</div>' +
                        '<div class="tc-check-desc">' +
                        _esc(it.desc) +
                        '</div>' +
                        '<div class="tc-check-actions">' +
                        _statusBtn(it.id, 'pass', st) +
                        _statusBtn(it.id, 'fail', st) +
                        _statusBtn(it.id, 'skip', st) +
                        '</div>' +
                        '</div>'
                );
            });
            html.push('</div>');
        });
        wrap.innerHTML = html.join('');
    }
    function _statusBtn(id, kind, current) {
        const isActive = current === kind;
        const icons = {
            pass: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',
            fail: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',
            skip: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>',
        };
        const titles = {
            pass: _t('tc-status-pass', '通过'),
            fail: _t('tc-status-fail', '失败'),
            skip: _t('tc-status-skip', '跳过'),
        };
        return (
            '<button type="button" class="tc-status-btn ' +
            (isActive ? 'is-active ' + kind : '') +
            '" data-id="' +
            _esc(id) +
            '" data-kind="' +
            kind +
            '" title="' +
            _esc(titles[kind]) +
            '">' +
            icons[kind] +
            '</button>'
        );
    }

    // ---------- 渲染:异常日志 ----------
    function _matchFilter(entry) {
        if (S.logFilter === 'all') return true;
        if (S.logFilter === 'js_error')
            return entry.type === 'js_error' || entry.type === 'promise_error';
        if (S.logFilter === 'api') return entry.type === 'api_error' || entry.type === 'api_fail';
        if (S.logFilter === 'api_slow') return entry.type === 'api_slow';
        if (S.logFilter === 'console')
            return entry.type === 'console_error' || entry.type === 'console_warn';
        return true;
    }
    function _renderLogs() {
        const wrap = document.getElementById('tc-logs-body');
        const cnt = document.getElementById('tc-logs-count');
        if (!wrap) return;
        const all = (window._pearnlyTcLogs || []).slice().reverse(); // 最新在前
        const filtered = all.filter(_matchFilter);
        if (cnt) cnt.textContent = String(all.length);

        if (filtered.length === 0) {
            wrap.innerHTML =
                '<div class="tc-logs-empty">' + _esc(_t('tc-logs-empty', '暂无异常')) + '</div>';
            return;
        }
        const html = filtered
            .slice(0, 100)
            .map(function (e) {
                const detail =
                    typeof e.detail === 'object'
                        ? JSON.stringify(e.detail, null, 2)
                        : String(e.detail || '');
                return (
                    '<div class="tc-log-item t-' +
                    _esc(e.type) +
                    '" data-ts="' +
                    e.ts +
                    '">' +
                    '<span class="tc-log-time">' +
                    _fmtTime(e.ts) +
                    '</span>' +
                    '<span class="tc-log-type">' +
                    _esc(e.type) +
                    '</span>' +
                    '<div class="tc-log-summary">' +
                    _esc(e.summary) +
                    '<div class="tc-log-detail">' +
                    _esc(detail) +
                    '</div>' +
                    '</div>' +
                    '</div>'
                );
            })
            .join('');
        wrap.innerHTML = html;

        // 同步过滤器 chip
        document.querySelectorAll('#tc-logs-filter .tc-filter-chip').forEach(function (c) {
            c.classList.toggle('active', c.getAttribute('data-filter') === S.logFilter);
        });
    }

    // 实时刷新(节流)· 由 _pearnlyTcPush 触发
    function _scheduleLogsRender() {
        if (S.renderScheduled) return;
        S.renderScheduled = true;
        setTimeout(function () {
            S.renderScheduled = false;
            const onPage =
                currentRoute === 'test-center' &&
                document.getElementById('page-test-center') &&
                document.getElementById('page-test-center').classList.contains('active');
            if (onPage) _renderLogs();
            _renderNavBadge();
        }, 200);
    }
    window._tcOnNewLog = _scheduleLogsRender;

    function _renderNavBadge() {
        const badge = document.getElementById('nav-test-badge');
        if (!badge) return;
        const errCount = (window._pearnlyTcLogs || []).filter(function (e) {
            return (
                e.type === 'js_error' ||
                e.type === 'promise_error' ||
                e.type === 'api_error' ||
                e.type === 'api_fail' ||
                e.type === 'console_error'
            );
        }).length;
        if (errCount > 0) {
            badge.style.display = '';
            badge.textContent = errCount > 99 ? '99+' : String(errCount);
        } else {
            badge.style.display = 'none';
        }
    }

    function _rerenderAll() {
        _renderStatusBar();
        _renderChecklist();
        _renderLogs();
        _renderNavBadge();
    }

    // ---------- 工具按钮 ----------
    function _toolHealthCheck() {
        const t0 = Date.now();
        fetch('/api/health')
            .then(function (r) {
                const ms = Date.now() - t0;
                if (r.ok)
                    _toast(_t('tc-toast-health-ok', '后端健康 ✓ {ms}ms', { ms: ms }), 'success');
                else
                    _toast(
                        _t('tc-toast-health-fail', '后端无响应') + ' (' + r.status + ')',
                        'error'
                    );
            })
            .catch(function () {
                _toast(_t('tc-toast-health-fail', '后端无响应'), 'error');
            });
    }
    function _toolClearSession() {
        try {
            localStorage.removeItem(LS_RESULTS);
            localStorage.removeItem('pearnly_current_client_id');
            S.results = {};
            (window._pearnlyTcLogs || []).length = 0;
            S.logFilter = 'all';
            if (typeof window.setCurrentClientId === 'function') {
                // 显式触发派发(已经在 setCurrentClientId 内做了)
            }
        } catch (_) {}
        _rerenderAll();
        _toast(_t('tc-toast-cleared', 'session 状态已清空'), 'success');
    }
    function _toolReloadClients() {
        try {
            // 复用 settings/clients 的 loadClientsCache(IIFE 内不直接暴露,用 fetch 旁路)
            fetch('/api/clients', {
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            })
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    window._clientsCache = data.clients || [];
                    if (typeof window._refreshClientSwitcher === 'function')
                        window._refreshClientSwitcher();
                    if (typeof window._refreshExcClientFilter === 'function')
                        window._refreshExcClientFilter();
                    _toast(
                        '客户缓存已刷新 · ' + (data.clients || []).length + ' 个客户',
                        'success'
                    );
                })
                .catch(function () {
                    _toast('刷新失败', 'error');
                });
        } catch (_) {}
    }

    // ---------- 绑定 ----------
    function _bindOnce() {
        if (S.bound) return;
        const root = document.getElementById('page-test-center');
        if (!root) return;
        S.bound = true;

        // 清单 · 状态按钮(委托)
        const cl = document.getElementById('tc-checklist-body');
        if (cl) {
            cl.addEventListener('click', function (e) {
                const btn = e.target.closest('.tc-status-btn');
                if (!btn) return;
                const id = btn.getAttribute('data-id');
                const kind = btn.getAttribute('data-kind');
                if (!id || !kind) return;
                // 同状态再点 = 取消
                if (S.results[id] === kind) delete S.results[id];
                else S.results[id] = kind;
                _saveResults();
                _renderChecklist();
                _renderStatusBar();
            });
        }

        // 重置勾选
        const rs = document.getElementById('tc-btn-reset-checklist');
        if (rs)
            rs.addEventListener('click', function () {
                S.results = {};
                _saveResults();
                _renderChecklist();
                _renderStatusBar();
            });

        // 复制全部
        const ca = document.getElementById('tc-btn-copy-all');
        if (ca)
            ca.addEventListener('click', function () {
                _copyToClipboard(_buildResultsMarkdown());
            });

        // 复制日志
        const cl2 = document.getElementById('tc-btn-copy-logs');
        if (cl2)
            cl2.addEventListener('click', function () {
                _copyToClipboard(_buildLogsMarkdown(30));
            });

        // 清空日志
        const clr = document.getElementById('tc-btn-clear-logs');
        if (clr)
            clr.addEventListener('click', function () {
                (window._pearnlyTcLogs || []).length = 0;
                _renderLogs();
                _renderNavBadge();
            });

        // 日志过滤器
        const flt = document.getElementById('tc-logs-filter');
        if (flt)
            flt.addEventListener('click', function (e) {
                const c = e.target.closest('.tc-filter-chip');
                if (!c) return;
                S.logFilter = c.getAttribute('data-filter') || 'all';
                _renderLogs();
            });

        // 日志条目点击展开
        const lb = document.getElementById('tc-logs-body');
        if (lb)
            lb.addEventListener('click', function (e) {
                const it = e.target.closest('.tc-log-item');
                if (!it) return;
                it.classList.toggle('expanded');
            });

        // 工具
        const h = document.getElementById('tc-tool-health');
        if (h) h.addEventListener('click', _toolHealthCheck);
        const cs = document.getElementById('tc-tool-clear-session');
        if (cs) cs.addEventListener('click', _toolClearSession);
        const rc = document.getElementById('tc-tool-reload-clients');
        if (rc) rc.addEventListener('click', _toolReloadClients);
    }

    // ---------- 显隐控制 ----------
    // v118.33.2 NAV-IA Phase 2 · sidebar 测试组 nav-group-test 已删(入口走头像菜单)· 此函数保留外壳兼容外部调用 · 内部空跑
    function _applyVisibility() {
        /* no-op · sidebar 测试组 DOM 已删 */
    }
    window._tcApplyVisibility = _applyVisibility;

    // 监听用户登录信息就绪(_userInfo 在 fetchUserInfo 之后才有 · 用 setInterval 轻量轮询)
    const _vTimer = setInterval(function () {
        S.checkN++;
        if (_userInfo) {
            _applyVisibility();
            clearInterval(_vTimer);
        }
        if (S.checkN > 60) clearInterval(_vTimer); // 30s 超时
    }, 500);

    // ---------- 主入口 ----------
    window.loadTestCenterPage = function () {
        _loadResults();
        _bindOnce();
        _rerenderAll();
    };

    // i18n 订阅 · 切语言重渲(若当前在测试中心页)
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('test-center', function () {
            _renderNavBadge();
            const onPage =
                currentRoute === 'test-center' &&
                document.getElementById('page-test-center') &&
                document.getElementById('page-test-center').classList.contains('active');
            if (onPage) _rerenderAll();
        });
    }
})();
