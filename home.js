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
let _engineCheckTimer = null;


// 单次批量上限:v118.27.8.1.15 后 trial 30 / monthly 500 / yearly 800 / lifetime 1000
function getMaxFiles() {
    // v111.2 · 优先用后端 /api/me/plan 返回的 limits.max_upload_files
    try {
        const ps = window._planState;
        if (ps && ps.limits && ps.limits.max_upload_files) {
            return ps.limits.max_upload_files;
        }
        // 后端 plan 字符串兜底(/api/me/plan 还没回 · 用 _userInfo.plan)
        const plan = (_userInfo && _userInfo.plan) || 'trial';
        // super_admin 直接放最高
        if (_userInfo && _userInfo.is_super_admin) return 9999;
        // v118.27.8.1.15 · 全档上调对齐后端 PLAN_CONFIG
        const mapping = {
            'admin': 9999, 'lifetime': 1000, 'yearly': 800, 'monthly': 500, 'trial': 30,
            // 老 plan 名兼容(不会再用·但保险)
            'enterprise': 1000, 'firm': 800, 'pro': 500, 'plus': 30, 'free': 30,
        };
        return mapping[plan] || 30;
    } catch (_) {
        return 30;
    }
}

function getMaxPagesPerFile() {
    try {
        const ps = window._planState;
        if (ps && ps.limits && ps.limits.max_pages_per_file) return ps.limits.max_pages_per_file;
        if (_userInfo && _userInfo.is_super_admin) return 999;
        const plan = (_userInfo && _userInfo.plan) || 'trial';
        return (plan === 'lifetime' || plan === 'enterprise') ? 100 : 50;
    } catch (_) { return 50; }
}

function getMaxMbPerFile() {
    try {
        const ps = window._planState;
        if (ps && ps.limits && ps.limits.max_mb_per_file) return ps.limits.max_mb_per_file;
        if (_userInfo && _userInfo.is_super_admin) return 500;
        const plan = (_userInfo && _userInfo.plan) || 'trial';
        if (plan === 'lifetime' || plan === 'enterprise') return 200;
        return 100;
    } catch (_) { return 100; }
}

const token = localStorage.getItem('mrpilot_token');
if (!token) window.location.href = '/';

// ============================================================
// 工具
// ============================================================
function t(key, params) {
    let s = (I18N[currentLang] && I18N[currentLang][key]) || key;
    if (params) for (const k in params) s = s.replace('{' + k + '}', params[k]);
    return s;
}
function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    })[ch]);
}

// v93 · SVG 线性图标 helper · lucide 风格 · 替代 emoji 保持专业感
function svgIcon(name, size) {
    size = size || 14;
    const paths = {
        refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',
        cache: '<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
        wifiOff: '<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',
        wifiOn: '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
        check: '<path d="M20 6 9 17l-5-5"/>',
        alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
        mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
        folder: '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
        api: '<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',
        copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
        minus: '<line x1="5" y1="12" x2="19" y2="12"/>',
        sparkle: '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>',
    };
    const inner = paths[name] || '';
    return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${inner}</svg>`;
}

// ============================================================
// 自定义确认对话框 · v0.15.6 · 替换浏览器原生 confirm()
// 用法: const ok = await showConfirm('确定删除吗?', { danger: true }); if (!ok) return;
// ============================================================
function showConfirm(msg, opts) {
    opts = opts || {};
    return new Promise((resolve) => {
        const overlay = document.getElementById('confirm-modal');
        const body = document.getElementById('confirm-modal-body');
        const btnOk = document.getElementById('confirm-modal-ok');
        const btnCancel = document.getElementById('confirm-modal-cancel');
        const btnClose = document.getElementById('confirm-modal-close');
        const title = document.getElementById('confirm-modal-title');
        if (!overlay || !body || !btnOk || !btnCancel) {
            // 兜底 · 极端情况下 DOM 不存在就直接当取消,避免页面卡死
            resolve(false); return;
        }
        title.textContent = opts.title || t('confirm-default-title');
        // v118.14 · 支持 promptInput 模式(在 body 里插一个 input · OK 时返回输入值)
        const inputId = opts.promptInput ? ('cm_in_' + Date.now()) : null;
        if (opts.promptInput) {
            const safeMsg = (msg || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
            const safePh = (opts.placeholder || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
            body.innerHTML = `
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${safeMsg}</div>
                <input type="text" id="${inputId}" placeholder="${safePh}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `;
        } else {
            body.textContent = msg || '';
        }
        // danger 样式按钮
        btnOk.className = opts.danger ? 'btn btn-danger' : 'btn btn-primary';
        btnOk.textContent = opts.okText || t('confirm-ok');
        btnCancel.textContent = opts.cancelText || t('confirm-cancel');
        // v118.14 · 支持 hideCancel(单按钮信息提示 · 替代 alert)
        btnCancel.style.display = opts.hideCancel ? 'none' : '';
        overlay.style.display = 'flex';

        const cleanup = (result) => {
            overlay.style.display = 'none';
            btnOk.onclick = null;
            btnCancel.onclick = null;
            btnClose.onclick = null;
            overlay.onclick = null;
            document.removeEventListener('keydown', onKey);
            // 还原 body 给下次用(promptInput 改了 innerHTML)
            if (opts.promptInput) body.innerHTML = '';
            btnCancel.style.display = '';
            resolve(result);
        };
        const getInputVal = () => {
            const i = inputId ? document.getElementById(inputId) : null;
            return i ? i.value : '';
        };
        const onKey = (e) => {
            if (e.key === 'Escape') cleanup(opts.promptInput ? null : false);
            else if (e.key === 'Enter') cleanup(opts.promptInput ? getInputVal() : true);
        };
        btnOk.onclick = () => cleanup(opts.promptInput ? getInputVal() : true);
        btnCancel.onclick = () => cleanup(opts.promptInput ? null : false);
        btnClose.onclick = () => cleanup(opts.promptInput ? null : false);
        overlay.onclick = (e) => { if (e.target === overlay) cleanup(opts.promptInput ? null : false); };
        document.addEventListener('keydown', onKey);
        // 聚焦
        setTimeout(() => {
            if (opts.promptInput) {
                const i = document.getElementById(inputId);
                if (i) i.focus();
            } else {
                btnOk.focus();
            }
        }, 50);
    });
}

// ============================================================
// Session 被踢弹窗 (v118.32.5.5.34 · 替换原 toast+redirect)
// ============================================================
function _showSessionRevokedModal() {
    if (document.getElementById('pn-session-revoked-modal')) return;
    var l = (typeof currentLang === 'string' && currentLang)
            || localStorage.getItem('mrpilot_lang') || 'th';
    var titles = {
        zh: '账号已在其他设备登录',
        en: 'Signed in on another device',
        th: 'บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น',
        ja: '他のデバイスでサインインされました'
    };
    var bodies = {
        zh: '你的账号刚刚在另一台设备上登录\n当前设备已自动退出，请重新登录继续使用。',
        en: 'Your account was just signed in on another device.\nThis device has been logged out automatically.',
        th: 'บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น\nระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่',
        ja: 'お使いのアカウントが別のデバイスでサインインされました。\nこのデバイスは自動的にログアウトされました。'
    };
    var okLabels = { zh: '确定，去登录', en: 'OK, Sign in', th: 'ตกลง เข้าสู่ระบบ', ja: 'OK、ログイン' };
    var lang = titles[l] ? l : 'th';
    var overlay = document.createElement('div');
    overlay.id = 'pn-session-revoked-modal';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;';
    overlay.innerHTML =
        '<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;">' +
            '<div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;">' +
                '<svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg>' +
            '</div>' +
            '<div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">' + titles[lang] + '</div>' +
            '<div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">' + bodies[lang] + '</div>' +
            '<button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">' + okLabels[lang] + '</button>' +
        '</div>';
    document.body.appendChild(overlay);
    document.getElementById('pn-srm-ok').addEventListener('click', function () {
        window.location.href = '/';
    });
}

// ============================================================
// API
// ============================================================
// B4 (2026-05-26) · 业务请求带上当前 workspace 账套主体(=在为哪家公司做账)。
// 后端(B1)选读 X-Workspace-Client-Id · 带不上即 NULL · 不强制 · 不影响发票买方。
// 个人模式 / 未选 → 不发头(返回 {})。
function _wsHeader() {
    try {
        if (typeof window.getActiveWorkspaceClientId === 'function') {
            const id = window.getActiveWorkspaceClientId();
            if (id != null) return { 'X-Workspace-Client-Id': String(id) };
        }
    } catch (_) { /* 切换器未就绪 · 静默 */ }
    return {};
}
async function apiGet(url) {
    const resp = await fetch(url, { headers: { 'Authorization': 'Bearer ' + token, ..._wsHeader() } });
    if (resp.status === 401 || resp.status === 403) {
        // v118.11 · 修 BUG B 员工登录跳着陆页:兼容 string/object detail
        // 原代码只看 detail.code · 但后端经常用 detail="auth.xxx" 字符串 · 导致任何 401/403 都跳
        // 新规则:401 一定跳 · 403 必须 detail 包含 "auth." 才跳 · 否则当业务错误抛出
        const data = await resp.json().catch(() => ({}));
        const detail = data && data.detail;
        let code = '';
        if (typeof detail === 'string') code = detail;
        else if (detail && typeof detail === 'object') code = detail.code || '';
        const isAuthFail = (resp.status === 401) || (typeof code === 'string' && code.indexOf('auth.') >= 0);
        if (isAuthFail) {
            console.warn('[auth-fail-redirect]', url, resp.status, detail);  // 诊断 · 用户截屏给我看
            localStorage.removeItem('mrpilot_token');
            if (code === 'auth.session_revoked') {
                _showSessionRevokedModal();
            } else {
                const _msgKey = (code === 'auth.password_changed_relogin') ? 'alert-password-changed-relogin' : 'alert-session';
                showToast(t(_msgKey), 'error');
                setTimeout(() => { window.location.href = '/'; }, 1500);
            }
            return null;
        }
        // 业务类 403(如 quota.need_api_key)交由调用方处理
        const err = new Error('biz_403'); err.detail = detail; throw err;
    }
    if (!resp.ok) throw new Error('fetch failed');
    return await resp.json();
}
async function apiPost(url, data) {
    const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', ..._wsHeader() },
        body: JSON.stringify(data),
    });
    if (resp.status === 401 || resp.status === 403) {
        // v118.11 · 同 apiGet · 兼容 string/object detail
        const cloned = resp.clone();
        const body = await cloned.json().catch(() => ({}));
        const detail = body && body.detail;
        let code = '';
        if (typeof detail === 'string') code = detail;
        else if (detail && typeof detail === 'object') code = detail.code || '';
        const isAuthFail = (resp.status === 401) || (typeof code === 'string' && code.indexOf('auth.') >= 0);
        if (isAuthFail) {
            console.warn('[auth-fail-redirect]', url, resp.status, detail);
            localStorage.removeItem('mrpilot_token');
            if (code === 'auth.session_revoked') {
                _showSessionRevokedModal();
            } else {
                const _msgKey = (code === 'auth.password_changed_relogin') ? 'alert-password-changed-relogin' : 'alert-session';
                showToast(t(_msgKey), 'error');
                setTimeout(() => { window.location.href = '/'; }, 1500);
            }
            return null;
        }
        // 业务类 403 · 返回原 resp 让调用方处理
        return resp;
    }
    return resp;
}

// v118.10 · PUT helper(/api/me/profile 等)· 返回 {ok: true/false, ...} 而不是 Response
async function apiPut(url, data) {
    try {
        const resp = await fetch(url, {
            method: 'PUT',
            headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', ..._wsHeader() },
            body: JSON.stringify(data),
        });
        if (resp.status === 401 || resp.status === 403) {
            // v118.11 · 同 apiGet · 兼容 string/object detail
            const body = await resp.json().catch(() => ({}));
            const detail = body && body.detail;
            let code = '';
            if (typeof detail === 'string') code = detail;
            else if (detail && typeof detail === 'object') code = detail.code || '';
            const isAuthFail = (resp.status === 401) || (typeof code === 'string' && code.indexOf('auth.') >= 0);
            if (isAuthFail) {
                console.warn('[auth-fail-redirect]', url, resp.status, detail);
                localStorage.removeItem('mrpilot_token');
                if (code === 'auth.session_revoked') {
                    _showSessionRevokedModal();
                } else {
                    const _msgKey = (code === 'auth.password_changed_relogin') ? 'alert-password-changed-relogin' : 'alert-session';
                    showToast(t(_msgKey), 'error');
                    setTimeout(() => { window.location.href = '/'; }, 1500);
                }
                return { ok: false };
            }
            return { ok: false, status: resp.status, detail };
        }
        const body = await resp.json().catch(() => ({}));
        return { ok: resp.ok && body.ok !== false, ...body };
    } catch (e) {
        return { ok: false, error: String(e) };
    }
}
// B4 (2026-05-26) · 暴露给 bundle 模块(workspace-switcher.js · fetch 列表 + 新建客户)。
window.apiGet = apiGet;
window.apiPost = apiPost;

// ============================================================
// 语言切换
// ============================================================
function applyLang(lang) {
    // v117 · 防止切语言时看到"左侧先变 / 右侧后变"的分帧顺序
    // 加 class → 同步替换 DOM → 双 rAF 后移除 class · 让所有 i18n 文字一起淡入
    document.body.classList.add('lang-switching');

    // v118.2 · 全局 overlay · 覆盖动态 render 滞后(admin 表格 / 套餐 modal 等)
    const _langOverlay = document.getElementById('lang-switching-overlay');
    if (_langOverlay) _langOverlay.classList.add('show');

    currentLang = lang;
    window._currentLang = lang;  // sync to global so all IIFEs read correct language
    localStorage.setItem('mrpilot_lang', lang);
    document.documentElement.lang = lang;

    // v0.19 · T1 · 同步偏好语言到后端(LINE Bot 等场景用)
    // v118.28.1.1 · debounce 200ms + AbortController · 防用户连续切语言时多次并发
    //   - 之前问题:用户测试 4 语连点 → 4 次 fetch 排队 · 最后到的等 16 秒
    //   - 现在:200ms 内多次切语言 · 只发最新一次 · 旧请求 abort
    try {
        const token = localStorage.getItem('mrpilot_token');
        if (token) {
            // 取消上一次未完成的请求
            if (window.__langSyncCtrl) {
                try { window.__langSyncCtrl.abort(); } catch (_) { /* silent · 已 abort / race */ }
            }
            // 取消上一次 debounce timer
            if (window.__langSyncTimer) {
                clearTimeout(window.__langSyncTimer);
            }
            window.__langSyncTimer = setTimeout(function () {
                window.__langSyncCtrl = new AbortController();
                fetch('/api/me/lang', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token,
                    },
                    body: JSON.stringify({ lang: lang }),
                    signal: window.__langSyncCtrl.signal,
                }).catch(function () {});
            }, 200);
        }
    } catch (e) {}

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (I18N[lang] && I18N[lang][key]) el.textContent = I18N[lang][key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (I18N[lang] && I18N[lang][key]) el.placeholder = I18N[lang][key];
    });

    // v118.28.5 · 顶栏 lang-current / lang-dropdown 已删除 · 改为兜防御 + 同步设置页
    const _langCurrent = document.getElementById('lang-current');
    if (_langCurrent) _langCurrent.textContent = I18N[lang]['lang-name'];
    document.querySelectorAll('#lang-dropdown .dd-item').forEach(item => {
        item.classList.toggle('active', item.dataset.lang === lang);
    });
    // v118.28.5.1 · 设置 → 系统 → 通用设置:同步语言 select 当前选中项
    const _genLangSel = document.getElementById('general-lang');
    if (_genLangSel) _genLangSel.value = lang;

    // 置信度列 tooltip
    const th = document.getElementById('col-conf-th');
    if (th) th.setAttribute('data-tip', t('col-conf-tip'));

    if (_userInfo && typeof window.renderInfoBar === 'function') window.renderInfoBar();
    if (_quota) updateUploadHint();
    // v118.35.0.8 · renderTrialBanner 已废 · 不再调
    // REFACTOR-C1-home-batch5 · renderFileList 已迁 upload-files.js(defer)· bootstrap applyLang 同步调时守卫(此刻 _selectedFiles 空 · 跳过无害)
    if (window.renderFileList) window.renderFileList();
    // REFACTOR-C1-home-batch1 · renderResults 已迁 ocr-results.js(defer)· bootstrap 期 applyLang 同步调时 window 桥可能未就绪 → 守卫(此刻 _results 空 · 跳过无害)
    if (window.renderResults) window.renderResults();
    if (currentRoute === 'settings' && typeof window.renderSettings === 'function') window.renderSettings();

    // v0.10 · 切语言后重渲染所有动态 innerHTML 区(避免残留旧语言)
    // 用 window.xxx 访问避免 TDZ(变量可能还没声明到)
    try {
        if (typeof renderErpEndpointsList === 'function'
            && window._erpEndpoints
            && window._erpEndpoints.length) {
            renderErpEndpointsList();
        }
    } catch (e) {}
    try {
        // A4 (v118.34.19) · 集成主页面也展示推送日志 · 同样需要切语言刷新
        if (typeof loadErpLogs === 'function'
            && (currentRoute === 'automation' || currentRoute === 'integrations')) {
            loadErpLogs();
            if (typeof loadErpTodayStats === 'function') loadErpTodayStats();
        }
    } catch (e) {}
    // v0.17 · M6 · 邮箱抓取 panel 重渲染
    try {
        if (typeof window._rerenderEmailIngest === 'function' && currentRoute === 'automation') {
            window._rerenderEmailIngest();
        }
    } catch (e) {}
    // v0.18 · M10 · 银行对账 panel 重渲染
    //   v118.26.1.2 · 已迁移到 subscribeI18n 总线 · 不再在这里散调用
    //   (保留注释作历史记号 · 之后写新模块照 bank-recon 模式 · 不走这里)
    // 归档编辑器(设置页打开着的话)
    try {
        if (typeof window._rerenderArchiveAll === 'function') {
            window._rerenderArchiveAll();
        }
    } catch (e) {}
    // v118.20.2.1 · 异常栏 chips + list 切语言重渲(不重新发请求 · 用缓存)
    try {
        if (typeof window._rerenderExceptions === 'function' && currentRoute === 'exceptions') {
            window._rerenderExceptions();
        }
    } catch (e) {}
    // v118.22.2.1 · 智能提醒 chips/列表/日志/弹窗切语言重渲
    try {
        if (typeof window._rerenderNotifications === 'function' && currentRoute === 'automation') {
            window._rerenderNotifications();
        }
    } catch (e) {}
    // v118.26.0 · 对账中心切语言重渲(刷「最近对账时间」文案)
    //   v118.26.1.2 · 已迁移到 subscribeI18n 总线 · 不再在这里散调用
    // 历史行
    try {
        if (typeof renderHistoryList === 'function' && currentRoute === 'history') {
            renderHistoryList();
        }
    } catch (e) {}
    // REFACTOR-C1 · 老 home.html admin 布局(admin-users / admin-cost)已整体下线
    //   超管走独立 /admin SPA · home.html admin 路由对所有角色不可达 · 切语言重渲块随之删除
    // v107 · 客户管理页切语言重渲染
    try {
        if (currentRoute === 'clients' && typeof window.loadClientsPage === 'function') {
            window.loadClientsPage();
        }
    } catch (e) {}

    // v118.11 · BUG 4 修复 · 切语言时如果在 team tab 上 · 重新调 loadTeamList 让动态 innerHTML 跟语言走
    try {
        if (currentRoute === 'settings' && typeof loadTeamList === 'function') {
            const activeTeamTab = document.querySelector('.settings-tab[data-tab="team"].active');
            if (activeTeamTab) loadTeamList();
        }
    } catch (e) {}

    // v118.26.1.2 · 统一通知所有用 subscribeI18n 注册的模块
    // (新模块走这条路径 · 不再加散落的 try 块)
    if (Array.isArray(window.__i18nSubs)) {
        for (const sub of window.__i18nSubs) {
            try { sub.fn(); }
            catch (e) { console.warn('[i18n] sub "' + sub.name + '" rerender failed:', e); }
        }
    }

    // v117 · 双 rAF 等浏览器绘制完同步替换的 DOM 后,统一淡入新文字
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            document.body.classList.remove('lang-switching');
        });
    });

    // v118.2 · 等 400ms 后隐藏 overlay · 给异步 fetch (admin 表格 / 套餐 modal) 一点时间完成
    // 比看到 5 秒撕裂体验好很多
    setTimeout(() => {
        const ov = document.getElementById('lang-switching-overlay');
        if (ov) ov.classList.remove('show');
    }, 400);
}

// ============================================================
// 下拉菜单通用
// ============================================================
function setupDropdown(id, onSelect) {
    const dd = document.getElementById(id);
    if (!dd) return;
    const toggle = dd.querySelector('.dd-btn');
    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.dropdown.open').forEach(el => {
            if (el !== dd) el.classList.remove('open');
        });
        dd.classList.toggle('open');
    });
    dd.querySelectorAll('.dd-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            dd.classList.remove('open');
            onSelect(item);
        });
    });
}
document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown.open').forEach(el => el.classList.remove('open'));
});
setupDropdown('lang-dropdown', (item) => applyLang(item.dataset.lang));
// v0.15 · 删除顶部套餐下拉 · 所有用户权限一致


// v118.33.2 NAV-IA Phase 2 · adm-lang-bar IIFE 已删 · admin/超管走「设置 → 通用设置」或 Cmd+K 切 4 语

// ============================================================
// 侧栏 + 路由
// ============================================================
const SIDEBAR_COLLAPSED_KEY = 'mrpilot_sidebar_collapsed';
if (localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1') {
    document.body.classList.add('sidebar-collapsed');
}
document.getElementById('sidebar-toggle').addEventListener('click', () => {
    if (window.innerWidth <= 768) {
        document.body.classList.toggle('sidebar-open');
    } else {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY,
            document.body.classList.contains('sidebar-collapsed') ? '1' : '0');
    }
});

// v86 · 顶栏汉堡按钮(手机端打开侧栏)
document.getElementById('topbar-hamburger')?.addEventListener('click', () => {
    document.body.classList.toggle('sidebar-open');
});
// v86 · 点击遮罩关闭侧栏
document.getElementById('sidebar-overlay')?.addEventListener('click', () => {
    document.body.classList.remove('sidebar-open');
});

// v118.32.5.5.37 NAV-IA Phase 5: automation 页面无侧边栏入口且不可路由 · 银行上传改为对账中心原地上传
const VALID_ROUTES = ['ocr', 'dashboard', 'history', 'integration', 'integrations', 'templates', 'api-keys', 'settings', 'exceptions', 'clients', 'vouchers', 'sales-invoices', 'receivables', 'reconcile', 'cloud', 'test-center'];

function routeTo(route) {
    // REFACTOR-C1 · 老 admin/admin-users/admin-cost 路由已下线(超管走独立 /admin SPA)· 落到 ocr
    if (!VALID_ROUTES.includes(route)) route = 'ocr';
    currentRoute = route;
    // v118.33.5 NAV-IA Phase 5 · 进子项路由 · 自动展开所在折叠组(销项/进项)
    if (typeof window.expandNavGroupForRoute === 'function') {
        window.expandNavGroupForRoute(route);
    }
    // 切页
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const pageId = 'page-' + route;
    const pageEl = document.getElementById(pageId);
    if (pageEl) pageEl.classList.add('active');
    // 侧栏激活
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.route === route);
    });
    // URL hash
    if (location.hash !== '#/' + route) {
        history.replaceState(null, '', '#/' + route);
    }
    // 移动端收起侧栏
    if (window.innerWidth <= 768) document.body.classList.remove('sidebar-open');

    // 特殊页面加载
    if (route === 'settings' && typeof window.renderSettings === 'function') window.renderSettings();
    // REFACTOR-C1-home-batch4 · loadHistoryPage 已迁 history-list.js(defer)· 同 clients 范式守卫;bootstrap 期未就绪由 history-list.js 自举补调
    if (route === 'history' && typeof window.loadHistoryPage === 'function') window.loadHistoryPage();
    // automation 路由已移除 · 银行上传改为对账中心原地弹文件选择器
    if (route === 'clients' && typeof window.loadClientsPage === 'function') window.loadClientsPage();
    // v118.20.2 · 异常栏页面加载
    if (route === 'exceptions' && typeof window.loadExceptionsPage === 'function') window.loadExceptionsPage();
    // v118.26.0 · 对账中心首页加载
    if (route === 'reconcile' && typeof window.loadReconcilePage === 'function') window.loadReconcilePage();
    // v118.28.1.0 · 测试中心
    if (route === 'test-center' && typeof window.loadTestCenterPage === 'function') window.loadTestCenterPage();
    // v118.32.5.5.16 · 首页 dashboard
    if (route === 'dashboard' && typeof window.loadDashboard === 'function') window.loadDashboard();
    // A4 (v118.34.19) · 进集成页 · 默认 cards tab · 同时刷新 erp logs
    // (logs tab 切过去时会再调一次 · 这里是首屏 / 切回时数据保鲜)
    if (route === 'integrations') {
        if (typeof loadErpLogs === 'function') {
            try { loadErpLogs(); } catch (e) {}
        }
        if (typeof loadErpTodayStats === 'function') {
            try { loadErpTodayStats(); } catch (e) {}
        }
    }
}

window.addEventListener('hashchange', () => {
    const r = (location.hash || '#/ocr').replace(/^#\//, '');
    routeTo(r);
});

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        // v0.15 · 「即将」菜单项(data-locked="1")给 toast · 不切路由
        if (item.dataset.locked === '1') {
            showToast(t('feature-coming-soon'), 'info');
            return;
        }
        routeTo(item.dataset.route);
    });
});

// v118.33.7.3 · sidebar-cta-upload 已删 · 对齐 prototype_final(prototype sidebar 无 CTA)



// A4 (v118.34.19 · Zihao 2026-05-19 拍板) · 集成主页面顶部 tab 切换
// + "看推送日志 →" 链接(从 ERP 卡片 / 也可来自其他地方)
(function () {
    function _activateIntTopTab(targetKey) {
        const tabs = document.querySelectorAll('#page-integrations .int-top-tab');
        const panels = document.querySelectorAll('#page-integrations .int-top-panel');
        tabs.forEach(t => {
            const k = t.dataset.intTopTab;
            t.classList.toggle('active', k === targetKey);
        });
        panels.forEach(p => {
            const k = p.dataset.intTopPanel;
            p.classList.toggle('active', k === targetKey);
        });
        // 切到 logs · 触发一次 fetch 让用户立刻看到数据
        if (targetKey === 'logs' && typeof loadErpLogs === 'function') {
            try { loadErpLogs(); } catch (e) {}
            if (typeof loadErpTodayStats === 'function') {
                try { loadErpTodayStats(); } catch (e) {}
            }
        }
    }
    // 暴露给 ERP 抽屉「看推送日志 →」按钮调用
    window.activateIntegrationsLogsTab = function () {
        // 如果集成抽屉打开了 · 关掉
        try {
            const drawer = document.getElementById('int-drawer');
            const overlay = document.getElementById('int-drawer-overlay');
            if (drawer) drawer.classList.remove('open');
            if (overlay) overlay.classList.remove('open');
            // 调用现有的关闭逻辑(若存在)清理 panel 归还
            if (typeof window.closeIntegrationDrawer === 'function') {
                window.closeIntegrationDrawer();
            }
        } catch (e) {}
        // 切到集成页 + logs tab
        if (typeof window.navigateTo === 'function') {
            try { window.navigateTo('integrations'); } catch (e) {}
        } else {
            try { location.hash = '#/integrations'; } catch (e) {}
        }
        _activateIntTopTab('logs');
        // 滚顶
        try {
            const page = document.getElementById('page-integrations');
            if (page) page.scrollIntoView({ block: 'start', behavior: 'smooth' });
        } catch (e) {}
    };

    document.addEventListener('click', function (e) {
        // tab 切换
        const tab = e.target.closest('#page-integrations .int-top-tab');
        if (tab) {
            const k = tab.dataset.intTopTab;
            if (k) _activateIntTopTab(k);
            return;
        }
        // 「看推送日志 →」按钮(集成页 ERP 卡片 OR ERP 抽屉内 ERP 连接卡片)
        const logsBtn = e.target.closest('[data-int-action="view-logs"], .int-btn-view-logs');
        if (logsBtn) {
            e.preventDefault();
            e.stopPropagation();
            window.activateIntegrationsLogsTab();
        }
    });

    // 路由切到 #/integrations 时 · 如果 hash 带 ?tab=logs · 自动切 logs
    function _onRouteToIntegrations() {
        const h = (location.hash || '').toLowerCase();
        if (h.includes('integrations') && h.includes('tab=logs')) {
            setTimeout(() => _activateIntTopTab('logs'), 50);
        }
    }
    window.addEventListener('hashchange', _onRouteToIntegrations);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        _onRouteToIntegrations();
    } else {
        document.addEventListener('DOMContentLoaded', _onRouteToIntegrations);
    }
})();

// v118.32.5.5.37 · 集成配置抽屉核心函数
(function () {
    'use strict';

    // 把 .auto-panel 从 drawer body 归还到 .auto-content
    function _returnPanel() {
        const body = document.getElementById('int-drawer-body');
        if (!body) return;
        const autoContent = document.querySelector('.auto-content');
        if (!autoContent) return;
        Array.from(body.querySelectorAll('.auto-panel')).forEach(function (el) {
            el.style.display = '';
            autoContent.appendChild(el);
        });
    }

    window.openIntegrationDrawer = function (tab, title) {
        const drawer = document.getElementById('int-drawer');
        const overlay = document.getElementById('int-drawer-overlay');
        const titleEl = document.getElementById('int-drawer-title');
        const body = document.getElementById('int-drawer-body');
        if (!drawer || !body) return;

        // 先归还上一个 panel
        _returnPanel();

        drawer.dataset.currentTab = tab || '';
        if (titleEl) titleEl.textContent = title || '';
        body.innerHTML = '';

        // anchor → data-auto-panel ID 映射(自动化页面里的 panel 名)
        var _panelIds = { line: 'linebot', folder: 'folder', email: 'email', alert: 'alert', erp: 'erp', bank: 'bank' };
        var panelId = _panelIds[tab] || tab;

        // 把对应的 auto-panel 移入抽屉(DOM move · 保留事件监听)
        const panel = document.querySelector('.auto-panel[data-auto-panel="' + panelId + '"]');
        if (panel) {
            panel.style.display = 'block';
            body.appendChild(panel);
        } else {
            body.innerHTML = '<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>';
        }

        // 打开动画
        drawer.classList.add('open');
        if (overlay) overlay.style.display = 'block';
        document.body.style.overflow = 'hidden';

        // 触发数据加载(panel 已在 DOM 里 · loader 按固定 ID 渲染)
        var loaders = {
            line:   window._loadLineBotPanel,
            folder: window._loadFolderWatcherPanel,
            email:  window._loadEmailIngestPanel,
            alert:  window._loadNotificationsPanel,
            bank:   window._loadBankReconPanel,
        };
        if (loaders[tab]) {
            try { loaders[tab](); } catch (e) { console.warn('[int-drawer] loader error', e); }
        } else if (tab === 'erp') {
            try {
                if (typeof loadErpEndpoints === 'function') loadErpEndpoints();
                if (typeof loadErpLogs === 'function') loadErpLogs();
            } catch (e) { console.warn('[int-drawer] ERP load error', e); }
        }
    };

    window.closeIntegrationDrawer = function () {
        _returnPanel();
        var drawer = document.getElementById('int-drawer');
        var overlay = document.getElementById('int-drawer-overlay');
        if (drawer) {
            drawer.classList.remove('open');
            drawer.dataset.currentTab = '';
        }
        if (overlay) overlay.style.display = 'none';
        document.body.style.overflow = '';
    };

    // 绑定关闭事件
    function _initDrawerEvents() {
        var closeBtn = document.getElementById('int-drawer-close');
        var overlay = document.getElementById('int-drawer-overlay');
        if (closeBtn) closeBtn.addEventListener('click', window.closeIntegrationDrawer);
        if (overlay) overlay.addEventListener('click', window.closeIntegrationDrawer);
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') window.closeIntegrationDrawer();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _initDrawerEvents);
    } else {
        _initDrawerEvents();
    }
})();


// v118.33.2 NAV-IA Phase 2 · _initSidebarUserMenu / renderSidebarUser 已删 · 替代品在右上角头像菜单(avatar-popup · Phase 1 上线)· 设置 / 帮助 / 退出全部从那里走

// ============================================================
// 用户信息 + 配额 + 联系方式
// ============================================================
async function loadAll() {
    try {
        const [u, q, c, p] = await Promise.all([
            apiGet('/api/me'),
            apiGet('/api/ocr/quota'),
            fetch('/api/contact').then(r => r.json()).catch(() => null),
            // v111.2 · 启动时拉 plan limits · 让 getMaxFiles 立即可用
            apiGet('/api/me/plan').catch(() => null),
        ]);
        if (!u || !q) return;
        _userInfo = u;
        // B4 修 (2026-05-26) · 必须同步暴露到 window · workspace-switcher.js(bundle 模块)
        // 的 _isOwner() 读 window._userInfo 判 owner/员工。漏了它 → owner 被当成员工 →
        // 工作模式弹窗错显"你还没有被分配客户,请联系老板分配"(应显示"新建客户")。
        try { window._userInfo = u; } catch (_) { /* silent */ }

        // ============================================================
        // v118.44.0 · NAV-IA Phase 8 · admin layout 独立 SPA 早退分支
        // 当 admin.html 加载时设置 PEARNLY_ADMIN_LAYOUT=true · 此处填充全局态后立即 return
        // 不调任何 home 渲染函数 · 所有 UI 由 admin.js 接管
        // ============================================================
        if (window.PEARNLY_ADMIN_LAYOUT) {
            _quota = q;
            _contact = c;
            if (p) window._planState = p;
            window.PEARNLY_ADMIN_MODE = true;
            // 暴露 _userInfo 给 admin.js / 业务模块用
            try { window._userInfoForAdmin = u; } catch (_) { /* silent · window 属性赋值 */ }
            return;
        }

        // ============================================================
        // v118.28.2 · 超管 /admin URL 独立(对齐 Stripe / Xero / QuickBooks)
        // 规则:
        //   - 普通用户 → 只能进 /home · 偷偷输 /admin 自动弹回
        //   - 超管 → 永远只看 /admin · 误进 /home 自动跳走
        // v118.44.0 · _isAdminPath 加 startsWith('/admin/')· 新 /admin/cost · /admin/users 也算 admin path
        // ============================================================
        try {
            const _isAdminPath = location.pathname === '/admin' || location.pathname.startsWith('/admin/');
            const _isSuper = !!u.is_super_admin;
            if (_isAdminPath && !_isSuper) {
                window.location.replace('/home');
                return;
            }
            if (!_isAdminPath && _isSuper) {
                // v118.44.0 · 超管默认跳新 admin layout(独立 SPA)· 不再跳 /admin(老 home.html 兜底)
                window.location.replace('/admin/cost');
                return;
            }
            window.PEARNLY_ADMIN_MODE = _isAdminPath;
            // REFACTOR-C1 · 老 home.html admin 布局(_isAdminPath 强制 #/admin-users)已下线 ·
            //   home.js 永不在 /admin* 加载(server: /admin/* → admin.html SPA)· _isAdminPath 恒 false ·
            //   仅保留上面「超管误进 /home → 弹回 /admin/cost」的活逻辑。
        } catch(_e) { window.PEARNLY_ADMIN_MODE = false; }

        _quota = q;
        _contact = c;
        if (p) window._planState = p;
        // v118.33.2 NAV-IA Phase 2 · renderSidebarUser 已删 · 头像菜单 renderAvatarMenu 接管(下面 Phase 1 块)
        // v0.15 · 顶部套餐下拉已删 · 不再设置 plan-current-label
        // v118.8 · 顶栏归属感 · 显示用户公司名(归属感 · 不再是 Pearnly 大字)
        renderBrandWorkspace();
        if (typeof window.renderInfoBar === 'function') window.renderInfoBar();
        if (typeof window.renderQuotaBanner === 'function') window.renderQuotaBanner();   // v102 · 配额低/耗尽顶部预警
        // v118.35.0.8 · renderTrialBanner 已废 · credits 系统接管
        if (typeof window.applySidebarVisibility === 'function') window.applySidebarVisibility();
        // NAV-IA Phase 1 · 头像菜单角色显隐 + 渲染(顶栏三件套)
        try {
            if (typeof applyRoleVisibility === 'function') applyRoleVisibility();
            if (typeof renderAvatarMenu === 'function') renderAvatarMenu(u);
        } catch (e) { console.error('[nav-ia phase1] render avatar menu', e); }
        updateUploadHint();
        // REFACTOR-C1-home-batch5 · updateStartButton 已迁 upload-files.js(defer)· 用户初始化期守卫(未就绪跳过·后续 renderFileList 会再同步)
        if (typeof window.updateStartButton === 'function') window.updateStartButton();
        // v118.11 · 员工首次登录强制改密(优先于 onboarding)
        // v118.11.2 · 双保险:即使 sessionStorage 有标记也必须校验当前用户是 member && 非超管
        // 防止跨账号 sessionStorage 污染让超管/老板被误弹(违反交接文档 §9.7 超管反向限制铁律)
        try {
            const mustChangePw = sessionStorage.getItem('pearnly_must_change_pw') === '1';
            const isEmployee = u && u.role === 'member' && !u.is_super_admin;
            if (mustChangePw && isEmployee) {
                showForceChangePasswordModal();
                return; // 阻止继续渲染 onboarding 等 · 改完密码后会刷新页面
            }
            // 标记存在但用户不是员工 · 清掉残留(防止后续切回员工账号被错误触发)
            if (mustChangePw && !isEmployee) {
                try { sessionStorage.removeItem('pearnly_must_change_pw'); } catch(e) {}
            }
        } catch(e) { console.error('force-pw init', e); }
        // v110.7 · 检查是否需要弹欢迎向导(B 方案)
        try { if (typeof window.maybeShowOnboarding === 'function') window.maybeShowOnboarding(u); } catch(e) { console.error('onboarding init', e); }
        // v118.10 · 设置页表单数据预填充
        try { if (typeof window.fillSettingsForms === 'function') window.fillSettingsForms(u); } catch(e) { console.error('settings forms init', e); }
    } catch (e) { console.error(e); }
}


// v118.11 · 员工首次登录 · 强制改密 modal · 不可关闭 · 改完才能用产品
function showForceChangePasswordModal() {
    document.querySelectorAll('.force-pw-overlay').forEach(el => el.remove());
    const overlay = document.createElement('div');
    overlay.className = 'force-pw-overlay';
    overlay.innerHTML = `
        <div class="force-pw-modal">
            <div class="force-pw-head">
                <div class="force-pw-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                </div>
                <div class="force-pw-title">${escapeHtml(t('force-pw-title') || '首次登录 · 请修改初始密码')}</div>
                <div class="force-pw-sub">${escapeHtml(t('force-pw-sub') || '老板设置的临时密码不安全 · 请立即修改')}</div>
            </div>
            <div class="force-pw-body">
                <div class="force-pw-field">
                    <label>${escapeHtml(t('force-pw-old') || '临时密码(老板告知您的)')}</label>
                    <input type="password" class="force-pw-input" id="force-pw-old" autocomplete="current-password">
                </div>
                <div class="force-pw-field">
                    <label>${escapeHtml(t('force-pw-new') || '新密码(至少 8 位 · 字母 + 数字)')}</label>
                    <input type="password" class="force-pw-input" id="force-pw-new" autocomplete="new-password">
                </div>
                <div class="force-pw-field">
                    <label>${escapeHtml(t('force-pw-new2') || '再次输入新密码')}</label>
                    <input type="password" class="force-pw-input" id="force-pw-new2" autocomplete="new-password">
                </div>
                <div class="force-pw-msg" id="force-pw-msg"></div>
            </div>
            <div class="force-pw-foot">
                <button class="btn btn-primary" type="button" id="force-pw-submit">${escapeHtml(t('force-pw-submit') || '修改并继续')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('show'));
    setTimeout(() => { const inp = document.getElementById('force-pw-old'); if (inp) inp.focus(); }, 200);

    const submitBtn = overlay.querySelector('#force-pw-submit');
    submitBtn.addEventListener('click', async () => {
        const oldPw = document.getElementById('force-pw-old').value;
        const newPw = document.getElementById('force-pw-new').value;
        const newPw2 = document.getElementById('force-pw-new2').value;
        const msgEl = document.getElementById('force-pw-msg');
        msgEl.textContent = ''; msgEl.classList.remove('error');

        if (!oldPw || !newPw) {
            msgEl.textContent = t('msg-fill-all') || '请填写所有字段';
            msgEl.classList.add('error'); return;
        }
        if (newPw !== newPw2) {
            msgEl.textContent = t('force-pw-mismatch') || '两次密码不一致';
            msgEl.classList.add('error'); return;
        }
        if (newPw.length < 8) {
            msgEl.textContent = t('pwd-too-short') || '密码至少 8 位';
            msgEl.classList.add('error'); return;
        }
        if (/^\d+$/.test(newPw)) {
            msgEl.textContent = t('pwd-too-weak-numeric') || '不能是纯数字 · 请加入字母';
            msgEl.classList.add('error'); return;
        }
        if (!(/[a-zA-Z]/.test(newPw) && /\d/.test(newPw))) {
            msgEl.textContent = t('pwd-too-weak') || '密码至少 8 位 · 字母 + 数字';
            msgEl.classList.add('error'); return;
        }
        if (newPw === oldPw) {
            msgEl.textContent = t('pwd-same-as-old') || '新密码不能和临时密码相同';
            msgEl.classList.add('error'); return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = t('msg-saving') || '保存中...';
        try {
            const resp = await fetch('/api/me/change_password', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
            });
            const body = await resp.json().catch(() => ({}));
            if (!resp.ok) {
                const code = (body && body.detail) || 'unknown';
                const map = {
                    'wrong_old_password': t('force-pw-wrong-old') || '临时密码不对',
                    'password_too_short': t('pwd-too-short') || '密码至少 8 位',
                    'password_too_weak': t('pwd-too-weak') || '密码至少 8 位 · 字母 + 数字',
                };
                msgEl.textContent = map[code] || (t('force-pw-fail') || '修改失败');
                msgEl.classList.add('error');
                submitBtn.disabled = false;
                submitBtn.textContent = t('force-pw-submit') || '修改并继续';
                return;
            }
            // 成功 · 清除标记 · 关闭 modal · 重新加载用户信息
            try { sessionStorage.removeItem('pearnly_must_change_pw'); } catch(e) {}
            showToast(t('force-pw-success') || '密码修改成功', 'success');
            overlay.classList.remove('show');
            setTimeout(() => {
                overlay.remove();
                // 重新走一遍初始化(让 onboarding 等正常跑)
                location.reload();
            }, 600);
        } catch (e) {
            msgEl.textContent = t('force-pw-fail') || '修改失败';
            msgEl.classList.add('error');
            submitBtn.disabled = false;
            submitBtn.textContent = t('force-pw-submit') || '修改并继续';
        }
    });
    // 阻止 ESC 关闭(强制)
    overlay.addEventListener('click', (e) => { if (e.target === overlay) e.stopPropagation(); });
}

// v118.10 · 设置页 · tab 点击绑定 + 持久化恢复
(function initSettingsTabs() {
    function bind() {
        const tabs = document.querySelectorAll('.settings-tab');
        if (!tabs.length) { setTimeout(bind, 200); return; }
        tabs.forEach(t => {
            t.addEventListener('click', () => switchSettingsTab(t.dataset.tab));
        });
        // 恢复上次 tab(若 tab 因权限隐藏 · 退回 profile)
        let saved = null;
        try { saved = localStorage.getItem('mrpilot_settings_tab'); } catch(e){}
        if (saved) {
            const target = document.querySelector(`.settings-tab[data-tab="${saved}"]`);
            if (target && target.style.display !== 'none') {
                switchSettingsTab(saved);
                return;
            }
        }
        switchSettingsTab('profile');
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else { bind(); }
})();


// v118.10 · 绑定保存按钮
(function bindSettingsForms() {
    function bind() {
        const p = document.getElementById('btn-save-profile');
        const c = document.getElementById('btn-save-company');
        if (!p && !c) { setTimeout(bind, 200); return; }
        if (p) p.addEventListener('click', saveProfile);
        if (c) c.addEventListener('click', saveCompany);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else { bind(); }
})();

// v118.28.5.1 · 设置 → 系统 → 通用设置(语言 + 时区 + 日期格式 + 数字格式)

// v118.8 · 顶栏 brand-workspace · 显示用户公司名 / 姓名 / fallback
function renderBrandWorkspace() {
    const el = document.getElementById('brand-workspace');
    if (!el || !_userInfo) return;
    const u = _userInfo;
    // v118.8.2 · 智能 cleanup · 防 username/name 字段被设成完整 email 字符串
    function clean(s) {
        if (!s || typeof s !== 'string') return null;
        s = s.trim();
        if (!s) return null;
        // 看起来是 email · 取前缀
        if (s.includes('@') && s.indexOf('@') > 0 && s.indexOf('.') > s.indexOf('@')) {
            return s.split('@')[0];
        }
        return s;
    }
    // v118.8.1 · 多字段 fallback 链 · 防后端字段名不一致 / 注册时未填
    const tryFields = [
        u.company_name, u.company, u.tenant_name, u.organization, u.org_name,
        u.name, u.full_name, u.display_name,
        // 这些可能是 email · 用 clean() 截前缀
        u.username, u.email,
    ];
    let name = null;
    for (const f of tryFields) {
        const c = clean(f);
        if (c) { name = c; break; }
    }
    if (!name) name = t('brand-workspace-fallback') || '我的工作台';
    el.textContent = name;
    el.title = name;
    el.removeAttribute('data-i18n');
    // v118.8.1 · 调试用 · 出问题时在 console 看 _userInfo 实际字段
    if (!u.company_name && !u.company) {
        console.debug('[Pearnly] brand-workspace fallback to:', name, '· _userInfo fields:', Object.keys(u));
    }
}


// v0.15 · renderPlanDropdown 已废弃 · 顶部套餐下拉删除


function updateUploadHint() {
    if (!_quota) return;
    document.getElementById('upload-hint').textContent = t('upload-hint', {
        pages: getMaxPagesPerFile(),   // v111.2 · 用 plan limits
        mb:    getMaxMbPerFile(),       // v111.2 · 用 plan limits
        files: getMaxFiles(),
    });
}

// ============================================================
// 升级弹窗(对比表)
// ============================================================
function _planDisplayLabel(plan) {
    // v0.12 · plan 的显示名(不直接用 plan.toUpperCase)
    if (plan === 'monthly')  return t('plan-monthly-name') || 'Monthly';
    if (plan === 'lifetime') return t('plan-lifetime-name') || 'Lifetime';
    if (plan === 'free')     return t('plan-free-name') || 'Free';
    if (plan === 'plus')     return 'Plus';
    if (plan === 'pro')      return 'Pro';
    return plan.charAt(0).toUpperCase() + plan.slice(1);
}

// v118.35.0.9 · 升级 modal 已永久下线 · 函数从 home.js 物理移除 · 相关 DOM 监听器也删干净

// 全局 data-upgrade 按钮 · v0.15 不再触发升级窗 · 静默忽略
document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-upgrade]');
    if (el) {
        e.preventDefault();
        // no-op · 以前会弹升级窗
    }
});


// ============================================================
// 侧栏锁定项点击
// ============================================================
document.querySelectorAll('.nav-item[data-locked]').forEach(item => {
    item.addEventListener('click', (e) => {
        const route = item.dataset.route;
        const badge = item.querySelector('.nav-badge');
        const text = badge ? badge.textContent.toLowerCase() : '';
        // 已经在 routeTo 里了,锁定的页面会显示占位和升级按钮
    });
});

// ============================================================
// 文件选择
// ============================================================



function startEnginePolling() {
    stopEnginePolling();
    _engineCheckTimer = setInterval(async () => {
        try {
            const h = await fetch('/api/health').then(r => r.json());
            if (h.ocr_ready) stopEnginePolling();
        } catch {}
    }, 10000);
}
function stopEnginePolling() {
    if (_engineCheckTimer) { clearInterval(_engineCheckTimer); _engineCheckTimer = null; }
}






// 事件代理:抽屉内 RD 按钮点击(校验 / 同步 / 锁图标升级提示)
document.getElementById('drawer-body').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-rd-action]');
    if (btn) {
        const action = btn.dataset.rdAction;
        const side = btn.dataset.rdSide;
        if (action === 'verify') callRdVerify(side);
        else if (action === 'sync') callRdSync(side);
        return;
    }
    const lockBtn = e.target.closest('.rd-btn-locked');
    if (lockBtn) {
        showToast(t('feature-contact-us'), 'info');
        return;
    }
    // v0.8.1 · 归档名一键复制
    const copyBtn = e.target.closest('[data-archive-copy]');
    if (copyBtn) {
        const name = copyBtn.dataset.archiveCopy;
        navigator.clipboard?.writeText(name).then(() => {
            showToast(t('copied'), 'success');
        }).catch(() => {
            showToast(t('copy-failed'), 'error');
        });
    }
});

document.getElementById('drawer-close').addEventListener('click', () => closeDrawer());
document.getElementById('drawer-mask').addEventListener('click', () => closeDrawer());
// v118.17 · drawer-diagnose 按钮已删 · 此处监听器同步移除(否则 getElementById 返 null · addEventListener 报错卡死整个 home.js)

function openDiagnoseDialog() {
    const r = _results[_drawerIdx];
    if (!r) return;
    // 收集能展示的所有原始数据
    const data = {
        filename: r.filename,
        engine: r.engine,
        page_count: r.page_count,
        elapsed_ms: r.elapsed_ms,
        confidence: r.confidence,
        archive_name: r.archive_name,
        category_tag: r.category_tag,
        merged_fields: r.merged_fields,
        pages: r.pages,  // 完整的 Gemini 原始返回
    };
    const json = JSON.stringify(data, null, 2);

    const modal = document.createElement('div');
    modal.className = 'log-detail-modal';
    modal.innerHTML = `
        <div class="log-detail-box" style="max-width:780px;">
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px;vertical-align:-4px;"><circle cx="10" cy="10" r="7"/><path d="M10 7v4M10 13v0.5"/></svg>
                    ${escapeHtml(t('diagnose-title'))}
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>
            <div style="padding: 6px 0 12px; font-size:12px; color: var(--ink-3);">
                ${escapeHtml(t('diagnose-hint'))}
            </div>
            <div class="diagnose-actions">
                <button class="btn btn-ghost btn-tiny" id="btn-diag-copy">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="4" width="8" height="8" rx="1"/><path d="M10 2H3a1 1 0 00-1 1v7" stroke-linecap="round"/></svg>
                    <span>${escapeHtml(t('diagnose-copy'))}</span>
                </button>
            </div>
            <pre class="diagnose-json">${escapeHtml(json)}</pre>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.classList.contains('log-detail-close')) {
            modal.remove();
        }
    });
    document.getElementById('btn-diag-copy').addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(json);
            showToast(t('diagnose-copied'), 'success');
        } catch (e) {
            showToast(t('diagnose-copy-fail'), 'error');
        }
    });
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // v118.35.0.9 · 升级 modal 已下线 · 只剩 drawer 处理
        if (document.getElementById('drawer').classList.contains('show')) closeDrawer();
    }
});

// v0.15 · 自定义模板 · 扁平权限下解锁 · 功能还没做 · 先显示 toast
// v118.27.5.3 · 占位按钮已 hidden(被 split 下拉取代)· 留事件防 JS 报错
const _btnCustomTpl = document.getElementById('btn-custom-template');
if (_btnCustomTpl) _btnCustomTpl.addEventListener('click', () => {
    showToast(t('cs-coming-soon'), 'info');
});




// v118.35.0.16 · BYO Gemini Key 全套(loadGeminiKeyInfo/saveGeminiKey/testGeminiKey/clearGeminiKey + setApiKeyMsg) 物理删除


// 事件绑定(页面加载时只绑一次)
document.addEventListener('DOMContentLoaded', () => {
    // v118.35.0.16 · BYO Gemini Key 按钮事件绑定永久下线

    // v92 · Bug 7 · 断网横幅
    installNetworkBanner();
});

// v92 · Bug 7 · 断网横幅初始化
function installNetworkBanner() {
    let banner = document.getElementById('offline-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'offline-banner';
        banner.className = 'offline-banner';
        banner.style.display = 'none';
        document.body.insertBefore(banner, document.body.firstChild);
    }
    function updateBanner() {
        if (navigator.onLine === false) {
            banner.innerHTML = svgIcon('wifiOff', 14) + '<span>' + escapeHtml(t('offline-banner')) + '</span>';
            banner.classList.remove('is-online');
            banner.classList.add('is-offline');
            banner.style.display = 'flex';
        } else {
            // 先展示"已恢复" 2 秒 · 再隐藏
            if (banner.classList.contains('is-offline')) {
                banner.innerHTML = svgIcon('wifiOn', 14) + '<span>' + escapeHtml(t('online-reconnected')) + '</span>';
                banner.classList.remove('is-offline');
                banner.classList.add('is-online');
                setTimeout(() => {
                    banner.style.display = 'none';
                    banner.classList.remove('is-online');
                }, 2000);
            } else {
                banner.style.display = 'none';
            }
        }
    }
    window.addEventListener('online', updateBanner);
    window.addEventListener('offline', updateBanner);
    updateBanner();  // 页面加载时立即检查
}


// ============================================================
// 启动
// ============================================================
// v118.44.0.5 · 顶层调用包 try-catch · 防 admin layout 下 applyLang/routeTo 抛错让后续 IIFE 不被注册
//   (现象:home.js L13585 applyLang null.classList → JS 引擎停止解析后续顶层语句 → admin-cost IIFE 不跑 → window.loadAdminCostPage 不存在)
try { applyLang(currentLang); } catch (e) { console.warn('[boot] applyLang failed', e); }

// hash 路由初始化
try {
    const initialRoute = (location.hash || '#/ocr').replace(/^#\//, '');
    routeTo(VALID_ROUTES.includes(initialRoute) ? initialRoute : 'ocr');
} catch (e) { console.warn('[boot] routeTo failed', e); }

// v118.33.10.1 · reconcile 页初始 hash 时 loadReconcilePage(module · defer)还未注册 · setTimeout 0 补一次调用
setTimeout(() => {
    if (currentRoute === 'reconcile' && typeof window.loadReconcilePage === 'function') {
        window.loadReconcilePage();
    }
}, 0);

loadAll();


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

// 通用:渲染页头右侧的信息条(Plan 徽章 + 月用量进度)· 参考识别页风格
function renderPageHeadInfo(containerId) {
    const el = document.getElementById(containerId);
    if (!el || !_userInfo) return;

    const plan = _userInfo.plan || 'free';
    const planLabel = plan.charAt(0).toUpperCase() + plan.slice(1);

    let usageHtml = '';
    if (plan === 'free' && _quota && _quota.ip_daily_limit) {
        const used = _quota.ip_used_today || 0;
        const total = _quota.ip_daily_limit;
        const pct = Math.min(100, (used / total) * 100);
        const cls = pct >= 90 ? 'danger' : (pct >= 70 ? 'warn' : '');
        usageHtml = `
            <div class="info-chip">
                <span class="chip-label">${t('info-daily')}</span>
                <span class="chip-value">${used} / ${total}</span>
                <div class="mini-bar"><div class="mini-bar-fill ${cls}" style="width:${pct}%"></div></div>
            </div>
        `;
    } else if (_userInfo.tenant_quota) {
        // v109.4 · 改用 tenant_used/tenant_quota · 跟其他组件对齐
        const used = _userInfo.tenant_used || 0;
        const total = _userInfo.tenant_quota;
        const pct = Math.min(100, (used / total) * 100);
        const cls = pct >= 90 ? 'danger' : (pct >= 70 ? 'warn' : '');
        usageHtml = `
            <div class="info-chip">
                <span class="chip-label">${t('info-monthly')}</span>
                <span class="chip-value">${used} / ${total}</span>
                <div class="mini-bar"><div class="mini-bar-fill ${cls}" style="width:${pct}%"></div></div>
            </div>
        `;
    }

    el.innerHTML = `
        <div class="info-chip">
            <span class="chip-value plan-${plan}">${planLabel}</span>
        </div>
        ${usageHtml}
    `;
}

// v0.16 · 历史记录多选删除状态(页面级 · 切页/搜索/刷新都会清空)
const _historySelected = new Set();




// ============================================================
// v0.6.1 · 自动化页(ERP 端点管理)
// ============================================================
let _erpEndpoints = [];
window._erpEndpoints = _erpEndpoints;












/* ============================================================
 * v0.19 · T1 · LINE Bot 面板
 * ============================================================ */
(function () {
    let _codeTimer = null;       // 过期倒计时
    let _pollTimer = null;       // 绑定状态轮询
    let _currentCode = null;
    let _currentExpiresAt = null;

    function $(id) { return document.getElementById(id); }

    async function load() {
        clearTimers();
        hideError();
        await refreshStatus();
    }

    async function refreshStatus() {
        try {
            const token = localStorage.getItem('mrpilot_token');
            const resp = await fetch('/api/line/binding', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!resp.ok) {
                showError(t('linebot-err-status'));
                return;
            }
            const data = await resp.json();
            if (data.bound) {
                renderBound(data);
            } else {
                await renderUnbound();
            }
        } catch (e) {
            showError(t('linebot-err-status'));
        }
    }

    function renderBound(data) {
        stopPolling();
        $('linebot-unbound').style.display = 'none';
        $('linebot-bound').style.display = 'block';

        const pill = $('linebot-status-summary');
        if (pill) {
            pill.textContent = t('linebot-status-bound');
            pill.style.background = '#D1FAE5';
            pill.style.color = '#065F46';
        }

        const nameEl = $('linebot-bound-name');
        if (nameEl) nameEl.textContent = data.line_display_name || '(LINE User)';

        const avatarEl = $('linebot-avatar');
        if (avatarEl) {
            if (data.line_picture_url) {
                avatarEl.src = data.line_picture_url;
                avatarEl.style.display = '';
            } else {
                avatarEl.style.display = 'none';
            }
        }

        const sinceEl = $('linebot-bound-since');
        if (sinceEl && data.bound_at) {
            sinceEl.textContent = new Date(data.bound_at).toLocaleString();
        }
    }

    async function renderUnbound() {
        $('linebot-bound').style.display = 'none';
        $('linebot-unbound').style.display = 'block';

        const pill = $('linebot-status-summary');
        if (pill) {
            pill.textContent = t('linebot-status-unbound');
            pill.style.background = '#FEE2E2';
            pill.style.color = '#B91C1C';
        }

        await fetchNewCode();
        startPolling();
    }

    async function fetchNewCode() {
        try {
            const token = localStorage.getItem('mrpilot_token');
            const resp = await fetch('/api/line/binding-code', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!resp.ok) {
                showError(t('linebot-err-code'));
                return;
            }
            const data = await resp.json();
            _currentCode = data.code;
            _currentExpiresAt = new Date(data.expires_at).getTime();
            renderCode(data);
        } catch (e) {
            showError(t('linebot-err-code'));
        }
    }

    function renderCode(data) {
        const codeEl = $('linebot-code');
        if (codeEl) codeEl.textContent = data.code;

        // Bot ID
        const idEl = $('linebot-bot-id');
        if (idEl) {
            idEl.textContent = data.bot_basic_id || t('linebot-bot-id-missing');
        }

        // QR 码:如果后端配了 LINE_BOT_FRIEND_URL · 用 Google Chart API 生成 QR
        const qrBox = $('linebot-qr');
        if (qrBox) {
            if (data.bot_friend_url) {
                const qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data=' + encodeURIComponent(data.bot_friend_url);
                qrBox.classList.remove('empty');
                qrBox.innerHTML = '<img src="' + qrUrl + '" alt="LINE Bot QR">';
            } else {
                qrBox.classList.add('empty');
                qrBox.innerHTML = '';
            }
        }

        // 倒计时
        startCountdown();
    }

    function startCountdown() {
        if (_codeTimer) clearInterval(_codeTimer);
        const expEl = $('linebot-code-expires');

        function tick() {
            if (!_currentExpiresAt) return;
            const ms = _currentExpiresAt - Date.now();
            if (ms <= 0) {
                if (expEl) {
                    expEl.textContent = t('linebot-code-expired');
                    expEl.classList.add('expiring');
                }
                const codeEl = $('linebot-code');
                if (codeEl) codeEl.style.opacity = '0.4';
                clearInterval(_codeTimer);
                _codeTimer = null;
                return;
            }
            const total = Math.floor(ms / 1000);
            const m = Math.floor(total / 60);
            const s = total % 60;
            if (expEl) {
                expEl.textContent = t('linebot-code-expires-in').replace('{m}', m).replace('{s}', String(s).padStart(2, '0'));
                if (ms < 60000) expEl.classList.add('expiring');
                else expEl.classList.remove('expiring');
            }
        }
        tick();
        _codeTimer = setInterval(tick, 1000);
    }

    function startPolling() {
        stopPolling();
        // 每 4 秒轮询一次绑定状态
        _pollTimer = setInterval(async () => {
            try {
                const token = localStorage.getItem('mrpilot_token');
                const resp = await fetch('/api/line/binding', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (!resp.ok) return;
                const data = await resp.json();
                if (data.bound) {
                    renderBound(data);
                }
            } catch (e) {
                // 静默 · 下一轮再试
            }
        }, 4000);
    }

    function stopPolling() {
        if (_pollTimer) {
            clearInterval(_pollTimer);
            _pollTimer = null;
        }
    }

    function clearTimers() {
        if (_codeTimer) { clearInterval(_codeTimer); _codeTimer = null; }
        stopPolling();
    }

    function showError(msg) {
        const box = $('linebot-error');
        if (box) {
            box.textContent = msg;
            box.style.display = 'block';
        }
    }

    function hideError() {
        const box = $('linebot-error');
        if (box) box.style.display = 'none';
    }

    async function unbind() {
        const ok = await showConfirm(t('linebot-unbind-confirm'), { danger: true });
        if (!ok) return;
        try {
            const token = localStorage.getItem('mrpilot_token');
            const resp = await fetch('/api/line/binding', {
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!resp.ok) {
                showError(t('linebot-err-unbind'));
                return;
            }
            await load();
        } catch (e) {
            showError(t('linebot-err-unbind'));
        }
    }

    // 事件绑定
    document.addEventListener('click', (e) => {
        const refreshBtn = e.target.closest('#linebot-code-refresh');
        if (refreshBtn) {
            e.preventDefault();
            hideError();
            fetchNewCode();
            return;
        }
        const unbindBtn = e.target.closest('#linebot-unbind');
        if (unbindBtn) {
            e.preventDefault();
            unbind();
            return;
        }
    });

    // 暴露给 switchAutomationTab
    window._loadLineBotPanel = load;
})();






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
// v118.27.0.1 · 全局确认弹窗(替代原生 confirm · 跟 Pearnly 整体 UI 一致)
// 用法:pearnlyConfirm(消息, 标题?).then(ok => { if (ok) { ... } })
// ============================================================
window.pearnlyConfirm = function (message, title) {
    return new Promise(function (resolve) {
        const overlay = document.getElementById('pearnly-confirm-modal');
        const titleEl = document.getElementById('pearnly-confirm-title');
        const msgEl = document.getElementById('pearnly-confirm-msg');
        const okBtn = document.getElementById('pearnly-confirm-ok');
        const cancelBtn = document.getElementById('pearnly-confirm-cancel');
        const closeBtn = document.getElementById('pearnly-confirm-close');
        if (!overlay || !msgEl || !okBtn || !cancelBtn) {
            // 兜底:DOM 不在时退回原生 confirm
            resolve(window.confirm(message));
            return;
        }
        if (titleEl) {
            titleEl.textContent = title || (typeof t === 'function' ? t('confirm-default-title') : 'Please confirm');
        }
        msgEl.textContent = message || '';
        overlay.style.display = 'flex';
        function cleanup(result) {
            overlay.style.display = 'none';
            okBtn.removeEventListener('click', onOk);
            cancelBtn.removeEventListener('click', onCancel);
            if (closeBtn) closeBtn.removeEventListener('click', onCancel);
            overlay.removeEventListener('click', onBgClick);
            document.removeEventListener('keydown', onKey);
            resolve(result);
        }
        function onOk()     { cleanup(true); }
        function onCancel() { cleanup(false); }
        function onBgClick(ev) { if (ev.target === overlay) cleanup(false); }
        function onKey(ev) {
            if (ev.key === 'Escape') cleanup(false);
            else if (ev.key === 'Enter') cleanup(true);
        }
        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
        if (closeBtn) closeBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onBgClick);
        document.addEventListener('keydown', onKey);
        // 焦点放到「取消」上(避免误触确定)
        setTimeout(function () { try { cancelBtn.focus(); } catch (e) {} }, 50);
    });
};







// ============================================================
// v118.32.5.5.24 · 屎山清理:删除 v118.27.5.4 老版本检测横幅(pn-version-banner)
// 已被 static/version-banner.js 替代(顶部弹窗 · 4 语 release_notes)
// 整段移除 · IIFE / DOM / 配套 CSS / 行为全删
// ============================================================



// ============================================================
// v27.8.1.14b.3 · 删 14b.2 加的 banner / 历史页死下拉
// 顶栏客户切换器是 Single Source of Truth · 不再多入口
// ============================================================













