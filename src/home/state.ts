// REFACTOR-C1-home-batch9g2 · 应用引导/全局状态(从 home.js 抽出 · 消除 home.js 巨石的最后一步)
//
// main.js 的【第 1 个】import:在任何 sibling 模块 eval 前完成
//   ① 全局错误拦截器(wrap fetch/console/error · 测试中心诊断)
//   ② i18n 订阅总线(window.subscribeI18n / __i18nSubs)
//   ③ 全局共享状态 init 到 window.*(currentLang/_userInfo/_results/... · ~40 模块裸读写经全局对象解析)
//   ④ token 读取(无 token 的拦截已由 home.html <head> 内联鉴权闸更早处理)
//
// 关键:home.js 删除后,模块里裸读/裸写 currentLang/_results 等 = 经全局对象解析到这里 init 的 window.X
// (经典脚本顶层 let 的全局词法桥已不存在 · 改用 window 属性桥 · 机制已真浏览器验证)。
// I18N 由 static/i18n-data.js(sync · 早于 bundle)挂 window.I18N · 模块裸读 I18N 直接命中 · 此处不重复。

// ============================================================
// 测试中心 · 全局错误拦截器(bundle 第 1 个 eval · 早于任何真实 fetch)
// ============================================================
(function () {
    'use strict';
    const BUF_MAX = 200;
    const buf: any[] = [];
    function _push(entry: any) {
        try {
            buf.push(Object.assign({ ts: Date.now() }, entry));
            if (buf.length > BUF_MAX) buf.shift();
            // 通知测试中心红点 + 列表(若已渲染)
            try {
                if (typeof window._tcOnNewLog === 'function') window._tcOnNewLog(entry);
            } catch (_) {
                /* silent · 测试中心 callback 极少 fail */
            }
        } catch (_) {
            /* silent · log entry 处理外层兜底 */
        }
    }
    window._pearnlyTcLogs = buf;
    window._pearnlyTcPush = _push;

    // 1) JS 同步错误
    window.addEventListener(
        'error',
        function (e) {
            // 资源加载错误 e.target 是元素 · 跳过(信噪比低)
            if (
                e.target &&
                e.target !== window &&
                ((e.target as any).src || (e.target as any).href)
            )
                return;
            _push({
                type: 'js_error',
                summary: String(e.message || 'JS Error').slice(0, 200),
                detail: {
                    file: e.filename || '',
                    line: e.lineno || 0,
                    col: e.colno || 0,
                    stack: e.error && e.error.stack ? String(e.error.stack).slice(0, 2000) : null,
                },
            });
        },
        true
    );

    // 2) Promise 未捕获
    window.addEventListener('unhandledrejection', function (e) {
        const r = e.reason;
        const msg = r && r.message ? r.message : String(r || 'Promise rejected');
        _push({
            type: 'promise_error',
            summary: String(msg).slice(0, 200),
            detail: {
                stack: r && r.stack ? String(r.stack).slice(0, 2000) : null,
            },
        });
    });

    // 3) fetch 包装(失败 / 4xx / 5xx / 慢请求 都记)
    const _origFetch = window.fetch;
    if (typeof _origFetch === 'function') {
        window.fetch = function () {
            const args = arguments;
            const t0 = Date.now();
            const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '?';
            const method = (args[1] && args[1].method) || 'GET';
            const urlClean = String(url).split('?')[0];
            return _origFetch
                .apply(this, args as any)
                .then(function (resp) {
                    const elapsed = Date.now() - t0;
                    if (!resp.ok) {
                        // 失败 · 取响应体片段
                        let bodyPreview = '';
                        try {
                            const clone = resp.clone();
                            clone
                                .text()
                                .then(function (txt) {
                                    bodyPreview = String(txt || '').slice(0, 500);
                                    _push({
                                        type: 'api_error',
                                        summary:
                                            method +
                                            ' ' +
                                            urlClean +
                                            ' → ' +
                                            resp.status +
                                            ' (' +
                                            elapsed +
                                            'ms)',
                                        detail: {
                                            url: url,
                                            method: method,
                                            status: resp.status,
                                            elapsed_ms: elapsed,
                                            body_preview: bodyPreview,
                                        },
                                    });
                                })
                                .catch(function () {
                                    _push({
                                        type: 'api_error',
                                        summary:
                                            method +
                                            ' ' +
                                            urlClean +
                                            ' → ' +
                                            resp.status +
                                            ' (' +
                                            elapsed +
                                            'ms)',
                                        detail: {
                                            url: url,
                                            method: method,
                                            status: resp.status,
                                            elapsed_ms: elapsed,
                                            body_preview: '(read failed)',
                                        },
                                    });
                                });
                        } catch (_) {
                            _push({
                                type: 'api_error',
                                summary:
                                    method +
                                    ' ' +
                                    urlClean +
                                    ' → ' +
                                    resp.status +
                                    ' (' +
                                    elapsed +
                                    'ms)',
                                detail: {
                                    url: url,
                                    method: method,
                                    status: resp.status,
                                    elapsed_ms: elapsed,
                                },
                            });
                        }
                    } else if (elapsed > 2500) {
                        _push({
                            type: 'api_slow',
                            summary: method + ' ' + urlClean + ' → 慢 ' + elapsed + 'ms',
                            detail: {
                                url: url,
                                method: method,
                                status: resp.status,
                                elapsed_ms: elapsed,
                            },
                        });
                    }
                    return resp;
                })
                .catch(function (err) {
                    const elapsed = Date.now() - t0;
                    _push({
                        type: 'api_fail',
                        summary: method + ' ' + urlClean + ' → 网络失败 (' + elapsed + 'ms)',
                        detail: {
                            url: url,
                            method: method,
                            elapsed_ms: elapsed,
                            error: String((err && err.message) || err),
                        },
                    });
                    throw err;
                });
        };
    }

    // 4) console.error / console.warn 拦截(信噪比中 · 仅取摘要)
    ['error', 'warn'].forEach(function (level) {
        const orig = console[level as keyof Console] as any;
        if (typeof orig !== 'function') return;
        console[level as keyof Console] = function () {
            try {
                const parts = [];
                for (let i = 0; i < arguments.length; i++) {
                    const a = arguments[i];
                    if (typeof a === 'string') parts.push(a);
                    else if (a && a instanceof Error) parts.push(a.message);
                    else {
                        try {
                            parts.push(JSON.stringify(a).slice(0, 300));
                        } catch (_) {
                            parts.push(String(a));
                        }
                    }
                }
                _push({
                    type: 'console_' + level,
                    summary: parts.join(' ').slice(0, 200),
                    detail: { full: parts.join(' ').slice(0, 1500) },
                });
            } catch (_) {
                /* silent · log CustomEvent dispatch 极少 fail */
            }
            return orig.apply(console, arguments);
        };
    });
})();

// ============================================================
// i18n 订阅总线(根治"切语言不刷新")· 模块加载时 subscribeI18n('名', 重渲) · applyLang 末尾统一通知
// ============================================================
window.__i18nSubs = window.__i18nSubs || [];
window.subscribeI18n = function (name, fn) {
    if (typeof fn !== 'function') {
        console.warn('[i18n] subscribeI18n: fn must be function · name=' + name);
        return;
    }
    // 同名只注册一次(防 IIFE 重复执行 · 重复挂钩)
    const exist = (window.__i18nSubs as any[]).find((s: any) => s.name === name);
    if (exist) {
        exist.fn = fn;
        return;
    }
    (window.__i18nSubs as any[]).push({ name: String(name || '?'), fn: fn });
};

// ============================================================
// 全局共享状态(原 home.js 顶层 let · 改 window.* 属性桥 · 模块裸读写经全局对象解析命中)
// ============================================================
window.currentLang = localStorage.getItem('mrpilot_lang') || 'th';
window._currentLang = window.currentLang; // 历史别名 · 部分 IIFE 读它
window.currentRoute = 'dms-intake';
window._userInfo = null;
window._quota = null;
window._contact = null;
window._selectedFiles = [];
window._results = [];
window._sortKey = null;
window._sortDir = 'asc';
window._searchKeyword = '';
window._drawerIdx = -1;
window._drawerAlreadyPushed = false;
window._historyState = {
    page: 0,
    pageSize: 20,
    total: 0,
    keyword: '',
    range: 90,
    items: [],
    loading: false,
};
window._historySelected = new Set();
window._erpEndpoints = [];

// token 读取(无 token 的硬拦截由 home.html <head> 内联鉴权闸更早处理 · 这里只暴露给模块用)
window.token = localStorage.getItem('mrpilot_token') as string;
