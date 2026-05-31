// ============================================================
// v118.28.1.0 · 测试中心 · 全局错误拦截器(必须最早执行 · 才能拦到所有错误)
// ============================================================
(function () {
    'use strict';
    const BUF_MAX = 200;
    const buf = [];
    function _push(entry) {
        try {
            buf.push(Object.assign({ ts: Date.now() }, entry));
            if (buf.length > BUF_MAX) buf.shift();
            // 通知测试中心红点 + 列表(若已渲染)
            try {
                if (typeof window._tcOnNewLog === 'function') window._tcOnNewLog(entry);
            } catch (_) { /* silent · 测试中心 callback 极少 fail */ }
        } catch (_) { /* silent · log entry 处理外层兜底 */ }
    }
    window._pearnlyTcLogs = buf;
    window._pearnlyTcPush = _push;

    // 1) JS 同步错误
    window.addEventListener('error', function (e) {
        // 资源加载错误 e.target 是元素 · 跳过(信噪比低)
        if (e.target && e.target !== window && (e.target.src || e.target.href)) return;
        _push({
            type: 'js_error',
            summary: String(e.message || 'JS Error').slice(0, 200),
            detail: {
                file: e.filename || '',
                line: e.lineno || 0,
                col: e.colno || 0,
                stack: (e.error && e.error.stack) ? String(e.error.stack).slice(0, 2000) : null,
            },
        });
    }, true);

    // 2) Promise 未捕获
    window.addEventListener('unhandledrejection', function (e) {
        const r = e.reason;
        const msg = (r && r.message) ? r.message : String(r || 'Promise rejected');
        _push({
            type: 'promise_error',
            summary: String(msg).slice(0, 200),
            detail: {
                stack: (r && r.stack) ? String(r.stack).slice(0, 2000) : null,
            },
        });
    });

    // 3) fetch 包装(失败 / 4xx / 5xx / 慢请求 都记)
    const _origFetch = window.fetch;
    if (typeof _origFetch === 'function') {
        window.fetch = function () {
            const args = arguments;
            const t0 = Date.now();
            const url = (typeof args[0] === 'string') ? args[0] : (args[0] && args[0].url) || '?';
            const method = (args[1] && args[1].method) || 'GET';
            const urlClean = String(url).split('?')[0];
            return _origFetch.apply(this, args).then(function (resp) {
                const elapsed = Date.now() - t0;
                if (!resp.ok) {
                    // 失败 · 取响应体片段
                    let bodyPreview = '';
                    try {
                        const clone = resp.clone();
                        clone.text().then(function (txt) {
                            bodyPreview = String(txt || '').slice(0, 500);
                            _push({
                                type: 'api_error',
                                summary: method + ' ' + urlClean + ' → ' + resp.status + ' (' + elapsed + 'ms)',
                                detail: {
                                    url: url, method: method,
                                    status: resp.status,
                                    elapsed_ms: elapsed,
                                    body_preview: bodyPreview,
                                },
                            });
                        }).catch(function () {
                            _push({
                                type: 'api_error',
                                summary: method + ' ' + urlClean + ' → ' + resp.status + ' (' + elapsed + 'ms)',
                                detail: { url: url, method: method, status: resp.status, elapsed_ms: elapsed, body_preview: '(read failed)' },
                            });
                        });
                    } catch (_) {
                        _push({
                            type: 'api_error',
                            summary: method + ' ' + urlClean + ' → ' + resp.status + ' (' + elapsed + 'ms)',
                            detail: { url: url, method: method, status: resp.status, elapsed_ms: elapsed },
                        });
                    }
                } else if (elapsed > 2500) {
                    _push({
                        type: 'api_slow',
                        summary: method + ' ' + urlClean + ' → 慢 ' + elapsed + 'ms',
                        detail: { url: url, method: method, status: resp.status, elapsed_ms: elapsed },
                    });
                }
                return resp;
            }).catch(function (err) {
                const elapsed = Date.now() - t0;
                _push({
                    type: 'api_fail',
                    summary: method + ' ' + urlClean + ' → 网络失败 (' + elapsed + 'ms)',
                    detail: {
                        url: url, method: method, elapsed_ms: elapsed,
                        error: String((err && err.message) || err),
                    },
                });
                throw err;
            });
        };
    }

    // 4) console.error / console.warn 拦截(信噪比中 · 仅取摘要)
    ['error', 'warn'].forEach(function (level) {
        const orig = console[level];
        if (typeof orig !== 'function') return;
        console[level] = function () {
            try {
                const parts = [];
                for (let i = 0; i < arguments.length; i++) {
                    const a = arguments[i];
                    if (typeof a === 'string') parts.push(a);
                    else if (a && a instanceof Error) parts.push(a.message);
                    else {
                        try { parts.push(JSON.stringify(a).slice(0, 300)); }
                        catch (_) { parts.push(String(a)); }
                    }
                }
                _push({
                    type: 'console_' + level,
                    summary: parts.join(' ').slice(0, 200),
                    detail: { full: parts.join(' ').slice(0, 1500) },
                });
            } catch (_) { /* silent · log CustomEvent dispatch 极少 fail */ }
            return orig.apply(console, arguments);
        };
    });
})();

// ============================================================
// Pearnly · I18N Dictionary (zh/en/th/ja)
// ============================================================
const I18N = window.I18N;  // REFACTOR-C1(2026-05-25)· I18N 字典已抽到 static/i18n-data.js · home.html 在 home.js 前 sync 加载 window.I18N
// ============================================================
// Pearnly · Home JS (v0.3.5)
// 侧栏 + Hash 路由 + 套餐对比弹窗 + 权限控制
// ============================================================

// I18N 字典会被另外 concat 进来
// ============================================================
// v118.26.1.2 · i18n 订阅总线(根治"切语言不刷新"反复出现的 bug)
// ============================================================
//
// 背景:Pearnly 的 i18n 是"声明式 + 命令式"两套机制:
//   1) HTML 标签 data-i18n 静态文案 → applyLang() 自动扫 DOM 替换 ✓
//   2) JS 用 t() 拼 innerHTML 动态文案 → 切语言后字符串已经写死了 · 必须模块自己重渲
//
// 历史方案(分散注册):每个模块暴露 window._rerenderXXX · applyLang 里散落 try 块逐个调
// 痛点:写新模块时 ① 暴露 _rerender ② 在 applyLang 加 try 钩子 ③ 钩子内调全部
//       3 步任意 1 步漏 = 切语言新 bug(已经发生 ≥ 5 次)
//
// 新方案(订阅总线):
//   模块加载时调 subscribeI18n('模块名', _rerenderAll)
//   切语言时 applyLang 末尾统一遍历 __i18nSubs · 自动通知所有订阅者
//
// 铁律(写进 DESIGN_SYSTEM.md):
//   任何用 t() 函数动态生成 innerHTML 的 IIFE 模块 · 必须在加载时调用
//   window.subscribeI18n('模块名', 重渲函数) · 否则切语言 = 旧文案残留
//
// 配套:scripts/check_i18n.py(发版前 lint · 扫漏注册)
// ============================================================
window.__i18nSubs = window.__i18nSubs || [];
window.subscribeI18n = function(name, fn) {
    if (typeof fn !== 'function') {
        console.warn('[i18n] subscribeI18n: fn must be function · name=' + name);
        return;
    }
    // 同名只注册一次(防 IIFE 重复执行 · 重复挂钩)
    const exist = window.__i18nSubs.find(s => s.name === name);
    if (exist) { exist.fn = fn; return; }
    window.__i18nSubs.push({ name: String(name || '?'), fn: fn });
};

// ============================================================
// 状态
// ============================================================
let currentLang = localStorage.getItem('mrpilot_lang') || 'th';
window._currentLang = currentLang;  // expose to IIFEs that can't access closure variable
let currentRoute = 'ocr';
let _userInfo = null;
let _quota = null;
let _contact = null;
let _selectedFiles = [];
let _results = [];
let _sortKey = null;
let _sortDir = 'asc';
let _searchKeyword = '';
let _drawerIdx = -1;
let _drawerAlreadyPushed = false;



const token = localStorage.getItem('mrpilot_token');
if (!token) window.location.href = '/';






// v0.15 · 删除顶部套餐下拉 · 所有用户权限一致


// v118.33.2 NAV-IA Phase 2 · adm-lang-bar IIFE 已删 · admin/超管走「设置 → 通用设置」或 Cmd+K 切 4 语






// v118.33.2 NAV-IA Phase 2 · _initSidebarUserMenu / renderSidebarUser 已删 · 替代品在右上角头像菜单(avatar-popup · Phase 1 上线)· 设置 / 帮助 / 退出全部从那里走





// v118.28.5.1 · 设置 → 系统 → 通用设置(语言 + 时区 + 日期格式 + 数字格式)



// v0.15 · renderPlanDropdown 已废弃 · 顶部套餐下拉删除



// ============================================================
// 升级弹窗(对比表)
// ============================================================

// v118.35.0.9 · 升级 modal 已永久下线 · 函数从 home.js 物理移除 · 相关 DOM 监听器也删干净




// ============================================================
// 文件选择
// ============================================================
















// v118.35.0.16 · BYO Gemini Key 全套(loadGeminiKeyInfo/saveGeminiKey/testGeminiKey/clearGeminiKey + setApiKeyMsg) 物理删除







// ============================================================
// 第 5.3 批 · 历史记录页
// ============================================================

const _historyState = {
    page: 0,
    pageSize: 20,
    total: 0,
    keyword: '',
    range: 90,
    items: [],
    loading: false,
};


// v0.16 · 历史记录多选删除状态(页面级 · 切页/搜索/刷新都会清空)
const _historySelected = new Set();




// ============================================================
// v0.6.1 · 自动化页(ERP 端点管理)
// ============================================================
let _erpEndpoints = [];
window._erpEndpoints = _erpEndpoints;


















// ============================================================
// v109.1 END
// ============================================================




// v113 · expose I18N · 给将来可能的外部脚本用
try { window.I18N = I18N; } catch(e) {}






// ============================================================
// B4 (2026-05-26) · 旧顶栏客户切换器(ClientSwitcher · 全 app 买方过滤器)已移除 ·
//   被 workspace 工作模式切换器取代(src/home/workspace-switcher.js · 右上角唯一入口)。
//   - window.getCurrentClientId 不再定义 · 余下消费者(history 2987 / dashboard 4872)
//     均有 typeof===function 守卫 → 自动降级"显示全部"· 不崩。
//   - 旧 'pearnly:client-changed' 事件的派发/监听随 IIFE 一起删除(自包含)。
//   - 旧 cs-* DOM 标签 + CSS 成为死代码(harmless · C2 清 home.css 时一并删)。
// ============================================================

// ============================================================
// REFACTOR-C1(2026-05-25)· 测试中心(Test Center)已抽到 src/home/test-center.js
//   (ES module · Vite bundle → static/dist/main.js · 经 window.loadTestCenterPage 入口)
// ============================================================











// ============================================================
// v118.32.5.5.24 · 屎山清理:删除 v118.27.5.4 老版本检测横幅(pn-version-banner)
// 已被 static/version-banner.js 替代(顶部弹窗 · 4 语 release_notes)
// 整段移除 · IIFE / DOM / 配套 CSS / 行为全删
// ============================================================



// ============================================================
// v27.8.1.14b.3 · 删 14b.2 加的 banner / 历史页死下拉
// 顶栏客户切换器是 Single Source of Truth · 不再多入口
// ============================================================













