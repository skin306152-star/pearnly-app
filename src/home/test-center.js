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
(function () {
    'use strict';

    // ---------- 配置 ----------
    const VERSION = 'v118.28.5';
    const LS_RESULTS = 'pearnly_tc_results_' + VERSION;

    // 测试账号 user_id 白名单(skin OAuth · 详见 STATE_PEARNLY.md 账号分工)
    const ALLOWED_USER_IDS = [
        '468b50c1-5593-4fd6-990d-515ce8085563', // skin306152@gmail.com Google OAuth
    ];

    // ---------- v118.28.5.2 测试清单 ----------
    const CHECKLIST = [
        // A · 异常栏 page-head 修复(BUG 1)
        {
            id: 'A1',
            group: 'A · 异常栏 page-head(BUG1)',
            desc: '手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行',
        },
        {
            id: 'A2',
            group: 'A · 异常栏 page-head(BUG1)',
            desc: '副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排',
        },
        {
            id: 'A3',
            group: 'A · 异常栏 page-head(BUG1)',
            desc: '客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度',
        },
        // B · 客户管理 page-head 修复(BUG 2)
        {
            id: 'B1',
            group: 'B · 客户管理 page-head(BUG2)',
            desc: '手机宽度进客户管理 · 标题「客户管理」横排正常',
        },
        {
            id: 'B2',
            group: 'B · 客户管理 page-head(BUG2)',
            desc: '副标题「为每家客户单独归档发票…」横排正常 · 不竖排',
        },
        {
            id: 'B3',
            group: 'B · 客户管理 page-head(BUG2)',
            desc: '「+ 新建客户」按钮换到新一行 · 不挤标题',
        },
        // C · 客户卡片(BUG 3)
        {
            id: 'C1',
            group: 'C · 客户卡片(BUG3)',
            desc: '客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断',
        },
        // D · 历史发票表头(BUG 4)
        {
            id: 'D1',
            group: 'D · 历史表头(BUG4)',
            desc: '手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排',
        },
        {
            id: 'D2',
            group: 'D · 历史表头(BUG4)',
            desc: '行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行',
        },
        // E · 对账客户切换器(BUG 6)
        {
            id: 'E1',
            group: 'E · 对账切换器(BUG6)',
            desc: '手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边',
        },
        { id: 'E2', group: 'E · 对账切换器(BUG6)', desc: '下拉宽度自适应屏幕 · 不超出屏幕右边' },
        // F · 通用设置(本版含 v28.5.1 全部内容 · 顺手回归)
        { id: 'F1', group: 'F · 通用设置回归', desc: '设置 → 个人资料 · 没有「界面语言」4 按钮卡' },
        {
            id: 'F2',
            group: 'F · 通用设置回归',
            desc: '左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于',
        },
        {
            id: 'F3',
            group: 'F · 通用设置回归',
            desc: '系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留',
        },
        // G · 移动端 settings tabs(v28.5.1 chip 风格)
        {
            id: 'G1',
            group: 'G · 移动端 settings(回归)',
            desc: '手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格',
        },
        // H · 现网功能不破
        {
            id: 'H1',
            group: 'H · 回归',
            desc: 'OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作',
        },
        {
            id: 'H2',
            group: 'H · 回归',
            desc: '4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)',
        },
        // I · 三档 viewport
        { id: 'I1', group: 'I · 三档移动 viewport', desc: 'iPhone SE 375 · 上述 BUG 1-6 都修了' },
        { id: 'I2', group: 'I · 三档移动 viewport', desc: 'Galaxy S 360 · 上述 BUG 1-6 都修了' },
        {
            id: 'I3',
            group: 'I · 三档移动 viewport',
            desc: 'iPhone 12 Pro 414 · 上述 BUG 1-6 都修了',
        },
    ];

    // ---------- 状态 ----------
    let _results = {}; // { 'A1': 'pass'|'fail'|'skip', ... }
    let _logFilter = 'all';
    let _bound = false;
    let _renderScheduled = false;

    // ---------- 工具 ----------
    function _t(key, fallback, vars) {
        let s = typeof t === 'function' ? t(key) : null;
        if (!s || s === key) s = fallback;
        if (vars)
            Object.keys(vars).forEach(function (k) {
                s = String(s).replace('{' + k + '}', String(vars[k]));
            });
        return s;
    }

    function _isAllowed() {
        try {
            // URL 参数兜底
            if (location.search.indexOf('test_center=1') >= 0) return true;
            // localStorage 兜底
            if (localStorage.getItem('pearnly_test_mode') === '1') return true;
            // user_id 白名单
            if (_userInfo && _userInfo.id && ALLOWED_USER_IDS.indexOf(String(_userInfo.id)) >= 0)
                return true;
        } catch (_) {}
        return false;
    }

    function _loadResults() {
        try {
            const raw = localStorage.getItem(LS_RESULTS);
            _results = raw ? JSON.parse(raw) : {};
            if (typeof _results !== 'object' || !_results) _results = {};
        } catch (_) {
            _results = {};
        }
    }
    function _saveResults() {
        try {
            localStorage.setItem(LS_RESULTS, JSON.stringify(_results));
        } catch (_) {
            /* silent · localStorage 私模/配额 */
        }
    }

    function _fmtTime(ts) {
        const d = new Date(ts);
        const pad = function (n) {
            return n < 10 ? '0' + n : '' + n;
        };
        return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
    }

    function _esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function _toast(msg, type) {
        try {
            if (typeof showToast === 'function') showToast(msg, type || 'info');
            else alert(msg);
        } catch (_) {
            /* silent · toast 失败兜 alert 也失败 · 外层吞 */
        }
    }

    function _copyToClipboard(text) {
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard
                    .writeText(text)
                    .then(function () {
                        _toast(_t('tc-toast-copied', '已复制到剪贴板'), 'success');
                    })
                    .catch(function () {
                        _fallbackCopy(text);
                    });
            } else {
                _fallbackCopy(text);
            }
        } catch (_) {
            _fallbackCopy(text);
        }
    }
    function _fallbackCopy(text) {
        try {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            const ok = document.execCommand('copy');
            document.body.removeChild(ta);
            _toast(
                ok ? _t('tc-toast-copied', '已复制') : _t('tc-toast-copy-fail', '复制失败'),
                ok ? 'success' : 'error'
            );
        } catch (_) {
            _toast(_t('tc-toast-copy-fail', '复制失败'), 'error');
        }
    }

    // ---------- 渲染:状态条 ----------
    function _renderStatusBar() {
        const acc = document.getElementById('tc-account-chip');
        const prog = document.getElementById('tc-progress-chip');
        if (acc) acc.textContent = (_userInfo && (_userInfo.email || _userInfo.username)) || '—';
        if (prog) {
            const total = CHECKLIST.length;
            const done = CHECKLIST.filter(function (it) {
                return _results[it.id];
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
                const st = _results[it.id] || '';
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
        if (_logFilter === 'all') return true;
        if (_logFilter === 'js_error')
            return entry.type === 'js_error' || entry.type === 'promise_error';
        if (_logFilter === 'api') return entry.type === 'api_error' || entry.type === 'api_fail';
        if (_logFilter === 'api_slow') return entry.type === 'api_slow';
        if (_logFilter === 'console')
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
            c.classList.toggle('active', c.getAttribute('data-filter') === _logFilter);
        });
    }

    // 实时刷新(节流)· 由 _pearnlyTcPush 触发
    function _scheduleLogsRender() {
        if (_renderScheduled) return;
        _renderScheduled = true;
        setTimeout(function () {
            _renderScheduled = false;
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

    // ---------- 复制 markdown ----------
    function _buildResultsMarkdown() {
        const lines = [];
        const now = new Date();
        const acct = (_userInfo && (_userInfo.email || _userInfo.username)) || '—';
        lines.push('# Pearnly ' + VERSION + ' 测试结果');
        lines.push('- 账号:' + acct);
        lines.push('- 时间:' + now.toISOString().replace('T', ' ').slice(0, 19));
        const total = CHECKLIST.length;
        const pass = CHECKLIST.filter(function (it) {
            return _results[it.id] === 'pass';
        }).length;
        const fail = CHECKLIST.filter(function (it) {
            return _results[it.id] === 'fail';
        }).length;
        const skip = CHECKLIST.filter(function (it) {
            return _results[it.id] === 'skip';
        }).length;
        const undone = total - pass - fail - skip;
        lines.push(
            '- 进度:' +
                (pass + fail + skip) +
                ' / ' +
                total +
                ' · ✅ ' +
                pass +
                ' · ❌ ' +
                fail +
                ' · ⏭ ' +
                skip +
                ' · 未测 ' +
                undone
        );
        lines.push('');
        lines.push('| ID | 描述 | 状态 |');
        lines.push('|---|---|---|');
        CHECKLIST.forEach(function (it) {
            const st = _results[it.id];
            const sym = st === 'pass' ? '✅' : st === 'fail' ? '❌' : st === 'skip' ? '⏭' : '⬜';
            lines.push('| ' + it.id + ' | ' + it.desc.replace(/\|/g, '\\|') + ' | ' + sym + ' |');
        });
        // 失败项重点
        const fails = CHECKLIST.filter(function (it) {
            return _results[it.id] === 'fail';
        });
        if (fails.length > 0) {
            lines.push('');
            lines.push('## ❌ 失败项');
            fails.forEach(function (it) {
                lines.push('- **' + it.id + '** · ' + it.desc);
            });
        }
        // 异常日志最近 30 条
        const logs = (window._pearnlyTcLogs || []).slice(-30).reverse();
        if (logs.length > 0) {
            lines.push('');
            lines.push('## 🔴 异常日志(最近 ' + logs.length + ' 条)');
            logs.forEach(function (e) {
                lines.push('- `' + _fmtTime(e.ts) + '` · **' + e.type + '** · ' + e.summary);
                if (e.detail) {
                    let d;
                    try {
                        d = JSON.stringify(e.detail);
                    } catch (_) {
                        d = String(e.detail);
                    }
                    if (d && d !== '{}') lines.push('  - ' + d.slice(0, 600));
                }
            });
        }
        return lines.join('\n');
    }
    function _buildLogsMarkdown(limit) {
        const logs = (window._pearnlyTcLogs || []).slice(-limit).reverse();
        if (logs.length === 0) return '(暂无异常日志)';
        const lines = ['# Pearnly 异常日志(最近 ' + logs.length + ' 条)'];
        const acct = (_userInfo && (_userInfo.email || _userInfo.username)) || '—';
        lines.push('- 账号:' + acct);
        lines.push('- 当前页:' + (currentRoute || '?'));
        lines.push('- UA:' + navigator.userAgent);
        lines.push('');
        logs.forEach(function (e) {
            lines.push('## `' + _fmtTime(e.ts) + '` · ' + e.type);
            lines.push('- ' + e.summary);
            if (e.detail) {
                lines.push('```');
                try {
                    lines.push(JSON.stringify(e.detail, null, 2).slice(0, 2000));
                } catch (_) {
                    lines.push(String(e.detail).slice(0, 2000));
                }
                lines.push('```');
            }
        });
        return lines.join('\n');
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
            _results = {};
            (window._pearnlyTcLogs || []).length = 0;
            _logFilter = 'all';
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
        if (_bound) return;
        const root = document.getElementById('page-test-center');
        if (!root) return;
        _bound = true;

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
                if (_results[id] === kind) delete _results[id];
                else _results[id] = kind;
                _saveResults();
                _renderChecklist();
                _renderStatusBar();
            });
        }

        // 重置勾选
        const rs = document.getElementById('tc-btn-reset-checklist');
        if (rs)
            rs.addEventListener('click', function () {
                _results = {};
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
                _logFilter = c.getAttribute('data-filter') || 'all';
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
    let _checkN = 0;
    const _vTimer = setInterval(function () {
        _checkN++;
        if (_userInfo) {
            _applyVisibility();
            clearInterval(_vTimer);
        }
        if (_checkN > 60) clearInterval(_vTimer); // 30s 超时
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
