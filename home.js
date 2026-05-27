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

// ============================================================
// v118.12 · 用户角色原子判断函数(全局唯一来源)
// 所有 UI 显隐、权限判断都基于这 6 个 · 不再散落写 if (role==='xxx')
// 参数 u 默认用 _userInfo · 可传别人(超管查别人时用)
// ============================================================
function isSuperAdmin(u) { u = u || _userInfo; return !!(u && u.is_super_admin); }
function isOwner(u)      { u = u || _userInfo; return !!u && (u.role === 'owner' || isSuperAdmin(u)); }
function isEmployee(u)   { u = u || _userInfo; return !!u && u.role === 'member' && !isSuperAdmin(u); }
function isTrial(u)      { u = u || _userInfo; return !!u && (u.effective_plan === 'trial' || u.plan === 'trial') && !isSuperAdmin(u); }
function isLifetime(u)   { u = u || _userInfo; return !!u && u.tenant_type === 'byo_api'; }
// 钱相关 UI 是否应该隐藏(员工就该看不到)· 这是核心铁律 · v118.12 主菜
function shouldHideMoney(u)   { return isEmployee(u); }
function canManageTeam(u)     { return isOwner(u); }
function canManageApiKey(u)   { return isOwner(u) && isLifetime(u); }
// 兼容旧代码 · 老的 isMoneyHidden 别处可能用 · 保留别名
window.isMoneyHidden = shouldHideMoney;
// ============================================================

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

    if (_userInfo) renderInfoBar();
    if (_quota) updateUploadHint();
    // v118.35.0.8 · renderTrialBanner 已废 · 不再调
    renderFileList();
    renderResults();
    if (currentRoute === 'settings') renderSettings();

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
    // v24 · 用户管理页(admin)· 切语言后表格内容重渲染 · 徽章/按钮/统计跟随
    // v109.4 · 改成新的 admin-users
    // v118.3 · 切语言时先用缓存数据立即重渲整页(零滞后) · 再后台 fetch 更新数据
    try {
        if (currentRoute === 'admin-users') {
            // 立即重渲(同步 · 用缓存)· 切语言瞬间所有内容已是新文字
            if (typeof window.__rerenderAdmPage === 'function') {
                window.__rerenderAdmPage();
            }
            // 后台异步 fetch · 数据可能更新但语言已对
            if (typeof window.loadAdminUsersPage === 'function') {
                window.loadAdminUsersPage();
            }
        }
        // v111.3 · 用户详情抽屉打开中 · 重新拉数据 + 重渲染(否则上次语言残留)
        const adrOverlay = document.getElementById('adm-drawer-overlay');
        if (adrOverlay && adrOverlay.dataset.uid && typeof window.__adm_open_user_drawer === 'function') {
            window.__adm_open_user_drawer(adrOverlay.dataset.uid);
        }
    } catch (e) {}
    // v106 · 成本面板切语言后重新渲染(把 innerHTML 里的 i18n key 文字刷新)
    try {
        if (currentRoute === 'admin-cost' && typeof window.loadAdminCostPage === 'function') {
            window.loadAdminCostPage();
        }
    } catch (e) {}
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

// v118.28.5.1 · 设置 → 系统 → 通用设置 · 语言 select 切换(替代旧 set-lang-row 4 按钮卡)
(function () {
    const sel = document.getElementById('general-lang');
    if (!sel) return;
    sel.addEventListener('change', (e) => {
        const lang = e.target.value;
        if (lang) applyLang(lang);
    });
    const _curLang = (typeof currentLang === 'string' && currentLang) || localStorage.getItem('mrpilot_lang') || 'th';
    sel.value = _curLang;
})();

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
const VALID_ROUTES = ['ocr', 'dashboard', 'history', 'integration', 'integrations', 'templates', 'api-keys', 'settings', 'admin-cost', 'admin-users', 'exceptions', 'clients', 'vouchers', 'sales-invoices', 'receivables', 'reconcile', 'cloud', 'test-center'];

function routeTo(route) {
    // v109.4 · 老 admin 路由迁移到 admin-users(数据更全 · 字段对齐多租户)
    if (route === 'admin') route = 'admin-users';

    // v109.4 · 防越权:非 super_admin 访问 admin-* 路由直接重定向回 ocr
    if ((route === 'admin-users' || route === 'admin-cost') &&
        _userInfo && !_userInfo.is_super_admin) {
        route = 'ocr';
    }

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
    if (route === 'settings') renderSettings();
    if (route === 'history') loadHistoryPage();
    // automation 路由已移除 · 银行上传改为对账中心原地弹文件选择器
    if (route === 'admin-cost' && typeof window.loadAdminCostPage === 'function') window.loadAdminCostPage();
    if (route === 'admin-users' && typeof window.loadAdminUsersPage === 'function') window.loadAdminUsersPage();
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

// v118.33.7.8 · 修 X 关闭 BUG · Phase 2 删 sidebar-user 时把 help-modal close 逻辑误删 · 这里独立绑回
(function () {
    function _bindHelpModal() {
        const helpModal = document.getElementById('help-modal');
        const helpClose = document.getElementById('help-modal-close');
        if (!helpModal) return;
        if (helpClose && !helpClose.dataset.bound) {
            helpClose.addEventListener('click', function () {
                helpModal.style.display = 'none';
            });
            helpClose.dataset.bound = '1';
        }
        if (!helpModal.dataset.maskBound) {
            helpModal.addEventListener('click', function (e) {
                if (e.target === helpModal) helpModal.style.display = 'none';
            });
            helpModal.dataset.maskBound = '1';
        }
        // ESC 关闭
        if (!window._helpModalEscBound) {
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && helpModal.style.display === 'flex') {
                    helpModal.style.display = 'none';
                }
            });
            window._helpModalEscBound = true;
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _bindHelpModal);
    } else {
        _bindHelpModal();
    }
})();

// v118.32.5.5.37 NAV-IA Phase 5 收尾 · 集成页「配置」按钮 → 右侧抽屉(不再跳 automation 路由)
// anchor→drawer tab 映射(google-drive/sheets 走原 inline 展开 · 不拦截)
(function () {
    const _anchorMap = { line: 'line', folder: 'folder', gmail: 'email', erp: 'erp', alert: 'alert' };
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.int-btn-configure');
        if (!btn) return;
        const row = btn.closest('.integration-row');
        const anchor = row ? row.dataset.intAnchor : null;
        if (anchor && _anchorMap[anchor]) {
            const nameEl = row.querySelector('.int-name');
            const title = nameEl ? (nameEl.textContent || nameEl.innerText || '').trim() : '配置';
            if (typeof window.openIntegrationDrawer === 'function') {
                window.openIntegrationDrawer(_anchorMap[anchor], title);
            }
        }
        // google-drive / google-sheets 走原有 inline 展开逻辑 · 不拦截
    });
})();

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

// v118.33.5 NAV-IA Phase 5 · sidebar 可折叠业务流分组(销项▼/进项▼ · LS 持久化)
(function () {
    const NAV_COLLAPSE_KEY = 'mrpilot_nav_collapsed';
    // 路由→组 映射:点哪个子项 · 哪个组自动展开
    const ROUTE_GROUP_MAP = {
        'ocr': 'sales', 'history': 'sales', 'reconcile': 'sales',
        'sales-invoices': 'sales', 'receivables': 'sales',
        'vouchers': 'expense',
    };
    function _getState() {
        try {
            const raw = localStorage.getItem(NAV_COLLAPSE_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch (e) { return {}; }
    }
    function _setState(state) {
        try { localStorage.setItem(NAV_COLLAPSE_KEY, JSON.stringify(state)); } catch (e) {}
    }
    function _applyState() {
        const state = _getState();
        document.querySelectorAll('.nav-collapsible').forEach(function (group) {
            const key = group.dataset.collapsible;
            if (state[key]) group.classList.add('collapsed');
            else group.classList.remove('collapsed');
        });
    }
    function _toggle(key) {
        const state = _getState();
        state[key] = !state[key];
        _setState(state);
        _applyState();
    }
    // 默认:首次访问 · 销项展开(日常)· 进项折叠(Phase 6 才填全)
    (function _ensureDefault() {
        const state = _getState();
        let changed = false;
        if (state.sales === undefined) { state.sales = false; changed = true; }
        if (state.expense === undefined) { state.expense = true; changed = true; }
        if (changed) _setState(state);
    })();
    _applyState();
    // 绑定 toggle 按钮
    document.querySelectorAll('.nav-group-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            _toggle(btn.dataset.toggleGroup);
        });
    });
    // 暴露给 routeTo:进某个子项路由时自动展开所在组
    window.expandNavGroupForRoute = function (route) {
        const group = ROUTE_GROUP_MAP[route];
        if (!group) return;
        const state = _getState();
        if (state[group]) {
            state[group] = false;
            _setState(state);
            _applyState();
        }
    };
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

            // v118.28.2.1 · admin mode 启动 force 路由到「用户管理」
            // 防止 localStorage 残留 / 浏览器 hash 把 Earn 带到客户业务页(如 settings/learned)
            if (_isAdminPath) {
                try { localStorage.removeItem('mrpilot_settings_tab'); } catch(_){ /* silent · localStorage 私模/配额 */ }
                const _h = location.hash || '';
                const _adminAllowedRoutes = ['#/admin-users', '#/admin-cost', '#/settings'];
                if (!_adminAllowedRoutes.some(r => _h.startsWith(r))) {
                    location.hash = '#/admin-users';
                }
            }
        } catch(_e) { window.PEARNLY_ADMIN_MODE = false; }

        _quota = q;
        _contact = c;
        if (p) window._planState = p;
        // v118.33.2 NAV-IA Phase 2 · renderSidebarUser 已删 · 头像菜单 renderAvatarMenu 接管(下面 Phase 1 块)
        // v0.15 · 顶部套餐下拉已删 · 不再设置 plan-current-label
        // v118.8 · 顶栏归属感 · 显示用户公司名(归属感 · 不再是 Pearnly 大字)
        renderBrandWorkspace();
        renderInfoBar();
        renderQuotaBanner();   // v102 · 配额低/耗尽顶部预警
        // v118.35.0.8 · renderTrialBanner 已废 · credits 系统接管
        applySidebarVisibility();
        // NAV-IA Phase 1 · 头像菜单角色显隐 + 渲染(顶栏三件套)
        try {
            if (typeof applyRoleVisibility === 'function') applyRoleVisibility();
            if (typeof renderAvatarMenu === 'function') renderAvatarMenu(u);
        } catch (e) { console.error('[nav-ia phase1] render avatar menu', e); }
        updateUploadHint();
        updateStartButton();
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
        try { maybeShowOnboarding(u); } catch(e) { console.error('onboarding init', e); }
        // v118.10 · 设置页表单数据预填充
        try { fillSettingsForms(u); } catch(e) { console.error('settings forms init', e); }
    } catch (e) { console.error(e); }
}

// v118.10 · 设置页 · 二级 tab 切换
function switchSettingsTab(tabName) {
    if (!tabName) return;
    // v118.12.3 · 员工守卫:阻止切到隐藏的 tab(team/api/plan/company)
    // 防止 localStorage 恢复 + 老板用过 team 后员工登录被带到 team panel
    try {
        if (typeof shouldHideMoney === 'function' && shouldHideMoney(_userInfo)) {
            if (['team', 'api', 'plan', 'company'].indexOf(tabName) >= 0) {
                tabName = 'profile';
                try { localStorage.setItem('mrpilot_settings_tab', 'profile'); } catch(e){}
            }
        }
    } catch (e) { /* noop */ }
    document.querySelectorAll('.settings-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.tab === tabName);
    });
    document.querySelectorAll('.settings-pane').forEach(p => {
        p.classList.toggle('active', p.dataset.pane === tabName);
    });
    try { localStorage.setItem('mrpilot_settings_tab', tabName); } catch(e){}
    // v118.10.1 · 切到 about / notifications 时调对应 load 函数(渲染联系方式 / 偏好开关)
    try {
        if (tabName === 'about' && typeof window.loadAboutPanel === 'function') window.loadAboutPanel();
        if (tabName === 'notifications' && typeof window.loadPrefsSettings === 'function') window.loadPrefsSettings();
        // v118.10.2 · 切到 team tab 时加载员工列表
        if (tabName === 'team') loadTeamList();
        // v118.21.2 · 切到 learned tab 时加载学习规则
        if (tabName === 'learned' && typeof window.loadLearnedRules === 'function') window.loadLearnedRules();
        // v118.35.0.14 · 切到 plan tab 时重渲 credits 计费卡 · 否则首次打开 modal
        // 之后切 tab 来回 · #settings-info 内容会消失(原 bug: 套餐&用量 panel 空白)
        if (tabName === 'plan' && typeof renderSettings === 'function') renderSettings();
    } catch (e) { console.warn('settings tab side effect failed:', e); }
}

// v118.10.2 · 团队管理 · 加载员工列表
async function loadTeamList() {
    const loadingEl = document.getElementById('team-loading');
    const listEl = document.getElementById('team-list');
    const emptyEl = document.getElementById('team-empty');
    const countEl = document.getElementById('team-count');
    if (!listEl) return;
    if (loadingEl) loadingEl.style.display = '';
    listEl.style.display = 'none';
    if (emptyEl) emptyEl.style.display = 'none';
    try {
        const r = await apiGet('/api/team/employees');
        const employees = (r && r.employees) || [];
        if (loadingEl) loadingEl.style.display = 'none';
        if (countEl) countEl.textContent = (t('team-count') || '共 {n} 名员工').replace('{n}', employees.length);
        if (employees.length === 0) {
            if (emptyEl) emptyEl.style.display = '';
            return;
        }
        listEl.style.display = '';
        listEl.innerHTML = employees.map(e => {
            const lastLogin = e.last_login_at ? new Date(e.last_login_at).toLocaleDateString() : (t('team-never-login') || '从未登录');
            const statusCls = e.is_active === false ? 'team-status-off' : 'team-status-on';
            const statusText = e.is_active === false ? (t('team-status-disabled') || '已禁用') : (t('team-status-active') || '正常');
            const emailLine = e.email ? `<span class="team-meta-sep">·</span><span>${escapeHtml(e.email)}</span>` : '';
            return `
            <div class="team-card" data-employee-id="${escapeHtml(e.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((e.username || '?')[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(e.username || '')}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${statusCls}"></span>
                            <span>${escapeHtml(statusText)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t('team-last-login') || '上次登录')}: ${escapeHtml(lastLogin)}</span>
                            ${emailLine}
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml((t('team-assigned-clients') || '已分配 {n} 客户').replace('{n}', e.assigned_client_count || 0))}</span>
                        </div>
                    </div>
                </div>
                <div class="team-card-actions">
                    <button class="btn btn-ghost btn-small" data-assign-clients="${escapeHtml(e.id)}" data-name="${escapeHtml(e.username || '')}">
                        ${escapeHtml(t('team-assign-clients') || '分配客户')}
                    </button>
                    <button class="btn btn-ghost btn-small" data-reset-pwd-employee="${escapeHtml(e.id)}" data-name="${escapeHtml(e.username || '')}" title="${escapeHtml(t('team-reset-pwd') || '重置密码')}">
                        ${escapeHtml(t('team-reset-pwd') || '重置密码')}
                    </button>
                    <button class="btn btn-ghost btn-small" data-toggle-employee="${escapeHtml(e.id)}" data-active="${e.is_active === false ? 'false' : 'true'}">
                        ${escapeHtml(e.is_active === false ? (t('team-enable') || '启用') : (t('team-disable') || '禁用'))}
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger-text" data-remove-employee="${escapeHtml(e.id)}" data-name="${escapeHtml(e.username || '')}">
                        ${escapeHtml(t('team-remove') || '移除')}
                    </button>
                </div>
            </div>`;
        }).join('');
    } catch (err) {
        console.error('loadTeamList failed:', err);
        if (loadingEl) loadingEl.textContent = (t('team-load-failed') || '加载失败');
    }
}

// v118.10.2 · 团队管理 · 添加员工 modal + 提交
// v118.10.3 · 升级为真正的 modal(替代浏览器 prompt 丑陋弹窗)
async function showAddEmployeeModal() {
    // 移除旧 modal(避免重复)
    document.querySelectorAll('.add-emp-overlay').forEach(el => el.remove());
    const overlay = document.createElement('div');
    overlay.className = 'add-emp-overlay';
    overlay.innerHTML = `
        <div class="add-emp-modal">
            <div class="add-emp-head">
                <div class="add-emp-title">${escapeHtml(t('team-add') || '添加员工')}</div>
                <button class="add-emp-close" type="button" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="add-emp-body">
                <div class="add-emp-field">
                    <label>${escapeHtml(t('team-modal-username') || '员工用户名')}</label>
                    <input type="text" class="add-emp-input" id="add-emp-username" placeholder="${escapeHtml(t('team-modal-username-ph') || 'employee01')}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t('team-modal-username-hint') || '3-50 位 · 字母 / 数字 / 下划线 / 点 / 横线 · 唯一')}</div>
                </div>
                <div class="add-emp-field">
                    <label>${escapeHtml(t('team-modal-email') || '邮箱(选填)')}</label>
                    <input type="email" class="add-emp-input" id="add-emp-email" placeholder="${escapeHtml(t('team-modal-email-ph') || 'employee@example.com')}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t('team-modal-email-hint') || '选填 · 用于忘记密码时邮件重置 · 留空则只能由老板重置')}</div>
                </div>
                <div class="add-emp-field">
                    <label>${escapeHtml(t('team-modal-password') || '初始密码')}</label>
                    <input type="text" class="add-emp-input" id="add-emp-password" placeholder="${escapeHtml(t('team-modal-password-ph') || '至少 8 位 · 字母 + 数字')}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t('team-modal-password-hint') || '员工首次登录后会被强制修改密码')}</div>
                </div>
                <div class="add-emp-msg" id="add-emp-msg"></div>
            </div>
            <div class="add-emp-foot">
                <button class="btn btn-ghost" type="button" id="add-emp-cancel">${escapeHtml(t('btn-cancel') || '取消')}</button>
                <button class="btn btn-primary" type="button" id="add-emp-submit">${escapeHtml(t('team-add') || '添加员工')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('show'));
    setTimeout(() => { const inp = document.getElementById('add-emp-username'); if (inp) inp.focus(); }, 200);

    function close() {
        overlay.classList.remove('show');
        setTimeout(() => overlay.remove(), 220);
    }
    overlay.querySelector('.add-emp-close').addEventListener('click', close);
    overlay.querySelector('#add-emp-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

    overlay.querySelector('#add-emp-submit').addEventListener('click', async () => {
        const usernameEl = document.getElementById('add-emp-username');
        const emailEl = document.getElementById('add-emp-email');
        const passwordEl = document.getElementById('add-emp-password');
        const msgEl = document.getElementById('add-emp-msg');
        const submitBtn = document.getElementById('add-emp-submit');
        const username = (usernameEl.value || '').trim();
        const email = (emailEl.value || '').trim();
        const password = passwordEl.value || '';
        msgEl.textContent = '';
        msgEl.classList.remove('error');

        if (!username || username.length < 3) {
            msgEl.textContent = t('team-modal-err-username') || '用户名至少 3 位';
            msgEl.classList.add('error'); return;
        }
        if (!/^[a-zA-Z0-9_.\-]+$/.test(username)) {
            msgEl.textContent = t('team-modal-err-username-fmt') || '只能用字母 / 数字 / 下划线 / 点 / 横线';
            msgEl.classList.add('error'); return;
        }
        // v118.11 · 邮箱选填 · 但填了就要格式正确
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            msgEl.textContent = t('msg-email-invalid') || '邮箱格式不对';
            msgEl.classList.add('error'); return;
        }
        // v118.11 · 密码强度本地预检(后端再校验一次,这里给即时反馈)
        if (password.length < 8) {
            msgEl.textContent = t('pwd-too-short') || '密码至少 8 位';
            msgEl.classList.add('error'); return;
        }
        if (/^\d+$/.test(password)) {
            msgEl.textContent = t('pwd-too-weak-numeric') || '不能是纯数字 · 请加入字母';
            msgEl.classList.add('error'); return;
        }
        if (!(/[a-zA-Z]/.test(password) && /\d/.test(password))) {
            msgEl.textContent = t('pwd-too-weak') || '密码至少 8 位 · 字母 + 数字';
            msgEl.classList.add('error'); return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = t('msg-saving') || '保存中...';
        try {
            const payload = { username, password };
            if (email) payload.email = email;
            const resp = await apiPost('/api/team/employees', payload);
            const body = resp ? await resp.json().catch(() => ({})) : {};
            if (resp && resp.ok && body && body.ok) {
                showToast(t('team-added') || '员工已添加', 'success');
                close();
                loadTeamList();
                return;
            }
            const code = (body && body.detail) || 'unknown';
            const msgMap = {
                'team.username_exists': t('team-username-exists') || '用户名已被占用',
                'team.email_exists': t('team-email-exists') || '邮箱已被占用',
                'team.create_failed':  t('team-create-failed') || '创建失败',
                'team.only_owner_or_super': t('team-no-permission') || '无权限',
                'team.no_tenant': t('team-no-tenant') || '请先升级账号',
                'pwd.too_short': t('pwd-too-short') || '密码至少 8 位',
                'pwd.too_weak_numeric': t('pwd-too-weak-numeric') || '不能是纯数字',
                'pwd.too_weak_common': t('pwd-too-weak-common') || '这个密码太常见 · 请换一个',
                'pwd.too_weak': t('pwd-too-weak') || '密码至少 8 位 · 字母 + 数字',
            };
            msgEl.textContent = msgMap[code] || (t('team-create-failed') || '创建失败') + ' (' + code + ')';
            msgEl.classList.add('error');
        } catch (e) {
            msgEl.textContent = t('team-create-failed') || '创建失败';
            msgEl.classList.add('error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = t('team-add') || '添加员工';
        }
    });

    // ESC 关闭
    function onKey(e) { if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onKey); } }
    document.addEventListener('keydown', onKey);
}

// v118.10.2 · 团队管理 · 启用/禁用 + 移除
async function toggleEmployeeActive(employeeId, makeActive) {
    try {
        const resp = await fetch(`/api/team/employees/${encodeURIComponent(employeeId)}/active`, {
            method: 'PATCH',
            headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: !!makeActive }),
        });
        if (resp.ok) { loadTeamList(); return; }
        showToast(t('team-toggle-failed') || '操作失败', 'error');
    } catch (e) { showToast(t('team-toggle-failed') || '操作失败', 'error'); }
}
async function removeEmployee(employeeId, username) {
    // v118.11 · 用系统 modal 替代浏览器原生 confirm() · 兼容 {name}/{n} 占位符
    const tpl = t('team-confirm-remove') || '确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录';
    const msg = tpl.replace('{name}', username).replace('{n}', username);
    const ok = await showConfirm(msg, { danger: true, okText: t('team-remove') });
    if (!ok) return;
    try {
        const resp = await fetch(`/api/team/employees/${encodeURIComponent(employeeId)}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (resp.ok) { showToast(t('team-removed') || '已移除', 'success'); loadTeamList(); return; }
        showToast(t('team-remove-failed') || '移除失败', 'error');
    } catch (e) { showToast(t('team-remove-failed') || '移除失败', 'error'); }
}

// v118.11 · 重置员工密码 · 系统生成 12 位强随机密码 · 一次性弹窗给老板
async function resetEmployeePassword(employeeId, username) {
    const confirmTpl = t('team-reset-pwd-confirm') || '给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码';
    const msg = confirmTpl.replace('{name}', username).replace('{n}', username);
    const ok = await showConfirm(msg, { okText: t('team-reset-link-send-btn') || '发送链接' });
    if (!ok) return;
    try {
        const resp = await fetch(`/api/team/employees/${encodeURIComponent(employeeId)}/reset-password`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
        });
        const body = await resp.json().catch(() => ({}));
        // 没渠道:员工既无邮箱也无 LINE
        if (resp.status === 400 && body.detail === 'team.reset_no_channel') {
            showToast(t('team-reset-no-channel') || '员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置', 'error');
            return;
        }
        if (!resp.ok) {
            showToast(t('team-reset-pwd-fail') || '发送失败', 'error');
            return;
        }
        if (body.channel === 'line' || body.channel === 'email') {
            const tpl = t('team-reset-link-sent') || '改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效';
            const chName = body.channel === 'line' ? 'LINE' : (t('team-reset-via-email') || '邮箱');
            showToast(tpl.replace('{ch}', chName), 'success');
            return;
        }
        showToast(t('team-reset-pwd-fail') || '发送失败', 'error');
    } catch (e) {
        showToast(t('team-reset-pwd-fail') || '发送失败', 'error');
    }
}

// v118.11 · 显示重置后的新临时密码 · 大字体 + 复制按钮
function showResetPwdResult(username, newPassword) {
    document.querySelectorAll('.reset-pwd-overlay').forEach(el => el.remove());
    const overlay = document.createElement('div');
    overlay.className = 'reset-pwd-overlay';
    overlay.innerHTML = `
        <div class="reset-pwd-modal">
            <div class="reset-pwd-head">
                <div class="reset-pwd-title">${escapeHtml(t('team-reset-pwd') || '重置密码')} · ${escapeHtml(username)}</div>
            </div>
            <div class="reset-pwd-warn">${escapeHtml(t('team-reset-pwd-shown-once') || '新临时密码 · 仅显示一次 · 请立即复制告知员工')}</div>
            <div class="reset-pwd-pwd-row">
                <code class="reset-pwd-pwd" id="reset-pwd-value">${escapeHtml(newPassword)}</code>
                <button class="btn btn-ghost" type="button" id="reset-pwd-copy-btn">${escapeHtml(t('team-reset-pwd-copy') || '复制')}</button>
            </div>
            <div class="reset-pwd-foot">
                <button class="btn btn-primary" type="button" id="reset-pwd-close-btn">${escapeHtml(t('team-reset-pwd-close') || '我已复制 · 关闭')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('show'));

    const copyBtn = overlay.querySelector('#reset-pwd-copy-btn');
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(newPassword);
            copyBtn.textContent = t('team-reset-pwd-copied') || '已复制';
            setTimeout(() => { copyBtn.textContent = t('team-reset-pwd-copy') || '复制'; }, 1500);
        } catch (e) {
            // fallback · 选中文本
            const sel = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(document.getElementById('reset-pwd-value'));
            sel.removeAllRanges(); sel.addRange(range);
        }
    });
    overlay.querySelector('#reset-pwd-close-btn').addEventListener('click', () => {
        overlay.classList.remove('show');
        setTimeout(() => overlay.remove(), 220);
    });
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

// v118.10.2 · 团队管理 · 事件代理(点击 add / toggle / remove 按钮)
document.addEventListener('click', (e) => {
    if (e.target.closest('#btn-add-employee')) { e.preventDefault(); showAddEmployeeModal(); return; }
    const tg = e.target.closest('[data-toggle-employee]');
    if (tg) { e.preventDefault(); toggleEmployeeActive(tg.dataset.toggleEmployee, tg.dataset.active === 'false'); return; }
    const rm = e.target.closest('[data-remove-employee]');
    if (rm) { e.preventDefault(); removeEmployee(rm.dataset.removeEmployee, rm.dataset.name || ''); return; }
    // v118.11 · 重置密码按钮
    const rs = e.target.closest('[data-reset-pwd-employee]');
    if (rs) { e.preventDefault(); resetEmployeePassword(rs.dataset.resetPwdEmployee, rs.dataset.name || ''); return; }
    // v118.28.1 · 分配客户按钮
    const ac = e.target.closest('[data-assign-clients]');
    if (ac) { e.preventDefault(); if (typeof window.openAssignClientsModal === 'function') window.openAssignClientsModal(ac.dataset.assignClients, ac.dataset.name || ''); return; }
});

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

// v118.10 · 设置页 · 预填充个人资料 + 公司信息表单
function fillSettingsForms(u) {
    if (!u) return;
    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val || '';
    };
    set('profile-username', u.username || '');
    set('profile-email', u.username || '');   // 当前后端 email == username
    set('profile-fullname', u.full_name || '');
    set('profile-phone', u.phone || '');
    set('profile-country', u.country || 'TH');
    set('profile-line', u.line_id || '');
    set('company-name', u.company_name || '');
    set('company-volume', u.monthly_volume || '');
    set('company-role', u.user_role || u.role_self || '');
}

// v118.10 · 保存个人资料
async function saveProfile() {
    const btn = document.getElementById('btn-save-profile');
    const msg = document.getElementById('profile-save-msg');
    if (!btn) return;
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span>${t('msg-saving') || '保存中...'}</span>`;
    if (msg) { msg.textContent = ''; msg.classList.remove('error'); }
    try {
        const payload = {
            full_name: (document.getElementById('profile-fullname') || {}).value || '',
            phone:     (document.getElementById('profile-phone') || {}).value || '',
            country:   (document.getElementById('profile-country') || {}).value || 'TH',
            line_id:   (document.getElementById('profile-line') || {}).value || '',
        };
        const r = await apiPut('/api/me/profile', payload);
        if (r && r.ok) {
            if (msg) msg.textContent = t('msg-saved') || '已保存';
            // 刷新用户信息(让顶栏公司名 / 姓名同步)
            try {
                const fresh = await apiGet('/api/me');
                _userInfo = fresh;
                try { window._userInfo = fresh; } catch (_) { /* silent · workspace-switcher 读它判 owner */ }
                renderBrandWorkspace();
            } catch(e){}
        } else {
            throw new Error('save failed');
        }
    } catch (e) {
        if (msg) { msg.textContent = t('msg-save-failed') || '保存失败'; msg.classList.add('error'); }
    } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
        setTimeout(() => { if (msg) msg.textContent = ''; }, 3000);
    }
}

// v118.10 · 保存公司信息
async function saveCompany() {
    const btn = document.getElementById('btn-save-company');
    const msg = document.getElementById('company-save-msg');
    if (!btn) return;
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span>${t('msg-saving') || '保存中...'}</span>`;
    if (msg) { msg.textContent = ''; msg.classList.remove('error'); }
    try {
        const payload = {
            company_name:   (document.getElementById('company-name') || {}).value || '',
            monthly_volume: (document.getElementById('company-volume') || {}).value || '',
            role:           (document.getElementById('company-role') || {}).value || '',
        };
        const r = await apiPut('/api/me/profile', payload);
        if (r && r.ok) {
            if (msg) msg.textContent = t('msg-saved') || '已保存';
            // 刷新顶栏公司名(关键体验)
            try {
                const fresh = await apiGet('/api/me');
                _userInfo = fresh;
                try { window._userInfo = fresh; } catch (_) { /* silent · workspace-switcher 读它判 owner */ }
                renderBrandWorkspace();
            } catch(e){}
        } else {
            throw new Error('save failed');
        }
    } catch (e) {
        if (msg) { msg.textContent = t('msg-save-failed') || '保存失败'; msg.classList.add('error'); }
    } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
        setTimeout(() => { if (msg) msg.textContent = ''; }, 3000);
    }
}

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
// 当前阶段:语言走 applyLang 全通路 · 其他三项前端 localStorage 占位
// 后端 schema 留给 v118.29.x 一起加(避免本版引入空 schema)
(function generalSettingsModule() {
    'use strict';

    const LS_TZ     = 'pearnly_general_tz';
    const LS_DATE   = 'pearnly_general_date_format';
    const LS_NUMBER = 'pearnly_general_number_format';

    const DEFAULTS = {
        tz: 'Asia/Bangkok',
        date: 'YYYY-MM-DD',
        number: 'comma_dot',
    };

    function _loadGeneral() {
        const tz = document.getElementById('general-tz');
        const dt = document.getElementById('general-date');
        const nm = document.getElementById('general-number');
        if (!tz || !dt || !nm) return;
        try {
            tz.value = localStorage.getItem(LS_TZ)     || DEFAULTS.tz;
            dt.value = localStorage.getItem(LS_DATE)   || DEFAULTS.date;
            nm.value = localStorage.getItem(LS_NUMBER) || DEFAULTS.number;
        } catch (e) {
            tz.value = DEFAULTS.tz;
            dt.value = DEFAULTS.date;
            nm.value = DEFAULTS.number;
        }
    }

    async function _saveGeneral() {
        const btn = document.getElementById('btn-save-general');
        const msg = document.getElementById('general-save-msg');
        if (!btn) return;
        const orig = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span>' + (t('msg-saving') || '保存中...') + '</span>';
        if (msg) { msg.textContent = ''; msg.classList.remove('error'); }
        try {
            const tz = (document.getElementById('general-tz')     || {}).value || DEFAULTS.tz;
            const dt = (document.getElementById('general-date')   || {}).value || DEFAULTS.date;
            const nm = (document.getElementById('general-number') || {}).value || DEFAULTS.number;
            try {
                localStorage.setItem(LS_TZ, tz);
                localStorage.setItem(LS_DATE, dt);
                localStorage.setItem(LS_NUMBER, nm);
            } catch (e) {}
            window._pearnlyGeneral = { tz: tz, date_format: dt, number_format: nm };
            if (msg) msg.textContent = t('msg-saved') || '已保存';
        } catch (e) {
            if (msg) { msg.textContent = t('msg-save-failed') || '保存失败'; msg.classList.add('error'); }
        } finally {
            btn.disabled = false;
            btn.innerHTML = orig;
            setTimeout(function () { if (msg) msg.textContent = ''; }, 3000);
        }
    }

    function _bind() {
        const btn = document.getElementById('btn-save-general');
        if (!btn) { setTimeout(_bind, 200); return; }
        if (btn._pearnlyGenBound) return;
        btn._pearnlyGenBound = true;
        btn.addEventListener('click', _saveGeneral);
        _loadGeneral();
    }

    function _rerenderAll() {
        _loadGeneral();
        const sel = document.getElementById('general-lang');
        if (sel) {
            const cur = (typeof currentLang === 'string' && currentLang) || localStorage.getItem('mrpilot_lang') || 'th';
            sel.value = cur;
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _bind);
    } else { _bind(); }

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('settings-general', _rerenderAll);
    }
})();

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

// v102 · 顶部配额预警 banner 渲染
// v109.4 · 统一用 tenant_used/tenant_quota · 跟顶栏 chip / 设置页 / 用户管理表对齐
function renderQuotaBanner() {
    const el = document.getElementById('quota-banner');
    if (!el) return;
    if (!_userInfo) { el.style.display = 'none'; return; }

    // 超管 / 自带 key 用户:不显示 banner
    if (_userInfo.is_super_admin || _userInfo.tenant_type === 'admin' || _userInfo.tenant_type === 'byo_api') {
        el.style.display = 'none';
        return;
    }

    let used = 0, total = 0;
    if (_userInfo.plan === 'free' && _quota && _quota.ip_daily_limit) {
        used = _quota.ip_used_today || 0;
        total = _quota.ip_daily_limit;
    } else if (_userInfo.tenant_quota != null && _userInfo.tenant_quota > 0) {
        // v109.4 · 优先 tenant 字段
        used = _userInfo.tenant_used || 0;
        total = _userInfo.tenant_quota;
    } else if (_userInfo.monthly_quota && _userInfo.monthly_quota > 0) {
        // v109.4 · 兜底用 user 表字段
        used = _userInfo.used_this_month || 0;
        total = _userInfo.monthly_quota;
    } else {
        // 没配额信息 · 不显示 banner
        el.style.display = 'none';
        return;
    }

    if (total <= 0) { el.style.display = 'none'; return; }

    const remaining = Math.max(0, total - used);
    const pct = (used / total) * 100;

    // 用户主动关闭过当天的 banner · 不再弹(localStorage 当日 key)
    const todayKey = 'quota_banner_dismiss_' + new Date().toISOString().slice(0, 10);
    if (localStorage.getItem(todayKey)) { el.style.display = 'none'; return; }

    let cls, msg;
    if (remaining === 0) {
        cls = 'danger';
        msg = t('quota-banner-exhausted');
    } else if (pct >= 90) {
        cls = 'danger';
        msg = t('quota-banner-very-low', { n: remaining });
    } else if (pct >= 70) {
        cls = 'warn';
        msg = t('quota-banner-low', { n: remaining });
    } else {
        el.style.display = 'none';
        return;
    }

    el.className = 'quota-banner ' + cls;
    el.innerHTML = `
        <span class="quota-banner-icon">${svgIcon('alert', 18)}</span>
        <span class="quota-banner-msg">${escapeHtml(msg)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t('quota-banner-dismiss'))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `;
    el.style.display = 'flex';
    const closeBtn = el.querySelector('.quota-banner-close');
    if (closeBtn) closeBtn.addEventListener('click', () => {
        localStorage.setItem(todayKey, '1');
        el.style.display = 'none';
    });
}

// v118.35.0.9 · renderTrialBanner 函数从 home.js 完全删除(v0.8 noop · v0.9 物理移除)·
// 没有调用站还在调它 · 函数不存在也不会报错 · trial-banner div 由 CSS 默认 display:none 兜底

function applySidebarVisibility() {
    // v118.8 · 试用临近到期横幅 · 7 天试用 · 剩 3 天提示 · 剩 1 天警示 · 过期红色
    if (typeof window.renderTrialBanner !== 'function') {
        window.renderTrialBanner = renderTrialBanner;
    }
    // v0.15 · 扁平权限 · 所有用户看到相同的侧栏
    // v118.12 · 全部改用 6 原子函数(isSuperAdmin / isOwner / isEmployee / shouldHideMoney / canManageTeam / canManageApiKey)
    const u = _userInfo;
    if (!u) return;
    const _hideMoney = shouldHideMoney(u);
    const _canTeam = canManageTeam(u);
    const _canApiKey = canManageApiKey(u);

    // 模板 / API Key 主导航 · 目前还没实现 · 保持"即将上线"样式
    const tplNav = document.querySelector('.nav-item[data-route="templates"]');
    if (tplNav) { tplNav.classList.remove('locked-for-plan'); tplNav.removeAttribute('data-locked-target'); }
    const apiNav = document.querySelector('.nav-item[data-route="api-keys"]');
    if (apiNav) { apiNav.classList.remove('locked-for-plan'); apiNav.removeAttribute('data-locked-target'); }
    const tplBtn = document.getElementById('btn-custom-template');
    if (tplBtn) { tplBtn.style.display = ''; tplBtn.classList.remove('locked-for-plan'); }

    // v22 · 超管下拉(顶栏):仅超管可见
    const adminDropdown = document.getElementById('admin-dropdown');
    if (adminDropdown) adminDropdown.style.display = isSuperAdmin(u) ? '' : 'none';

    // v118.33.2 NAV-IA Phase 2 · sidebar 底部「成本追踪 / 用户管理 / 测试 / adm-lang-bar」整体已删 · 显隐逻辑搬到头像菜单 applyRoleVisibility · 这里只剩顶栏超管下拉

    // ============================================================
    // v118.12 · 设置页 6 个 tab 显隐(原子函数驱动)
    // ============================================================
    // 团队管理:仅 owner / 超管
    const teamTab = document.querySelector('.settings-tab[data-tab="team"]');
    if (teamTab) teamTab.style.display = _canTeam ? '' : 'none';
    const teamPanel = document.querySelector('.settings-panel[data-settings-panel="team"]');
    if (teamPanel) teamPanel.dataset.permHidden = _canTeam ? '0' : '1';

    // API & 密钥:仅买断 owner / 超管
    const apiTab = document.querySelector('.settings-tab[data-tab="api"]');
    if (apiTab) apiTab.style.display = (_canApiKey || isSuperAdmin(u)) ? '' : 'none';

    // 套餐 & 用量:员工隐藏
    const planTab = document.querySelector('.settings-tab[data-tab="plan"]');
    if (planTab) planTab.style.display = _hideMoney ? 'none' : '';

    // v118.12 · 公司信息 tab:员工隐藏(公司是事务所属性 · 跟员工无关)
    const companyTab = document.querySelector('.settings-tab[data-tab="company"]');
    if (companyTab) companyTab.style.display = _hideMoney ? 'none' : '';

    // ============================================================
    // v118.12 · 顶栏 / 全局 banner / 升级按钮 · 员工全部隐藏
    // ============================================================
    // info-bar 配额 chip(顶栏右侧 "X/Y 张")
    const infoBar = document.getElementById('info-bar');
    if (infoBar) infoBar.style.display = _hideMoney ? 'none' : '';

    // trial-banner(7 天试用倒计时横幅)
    const trialBanner = document.getElementById('trial-banner');
    if (trialBanner && _hideMoney) trialBanner.style.display = 'none';

    // plan-banner(v109.3 IIFE 那个 fixed 顶部横幅)
    const planBanner = document.getElementById('plan-banner');
    if (planBanner && _hideMoney) {
        planBanner.style.display = 'none';
        document.body.classList.remove('has-plan-banner');
    }

    // v118.35.0.9 · 升级按钮全局 click 绑定永久下线 · 直接隐藏所有 .btn-upgrade / .topbar-upgrade / [data-upgrade-cta]
    document.querySelectorAll('[data-upgrade-cta], .btn-upgrade, .topbar-upgrade').forEach(el => {
        el.style.display = 'none';
    });

    // body class · 让 CSS 可以基于角色做额外样式收尾(比如员工进设置默认 active 不在公司信息)
    document.body.classList.toggle('role-employee', isEmployee(u));
    document.body.classList.toggle('role-owner', isOwner(u));
    document.body.classList.toggle('role-super', isSuperAdmin(u));

    // v118.12.3 · 关键修复:如果当前 active tab 是被隐藏的(localStorage 恢复了员工无权访问的 tab)
    // 强制切回 profile · 否则员工会看到 team panel 内容 + 调 API 被 403
    try {
        const activeTab = document.querySelector('.settings-tab.active');
        if (activeTab && activeTab.style.display === 'none') {
            if (typeof window.switchSettingsTab === 'function') {
                window.switchSettingsTab('profile');
            } else if (typeof switchSettingsTab === 'function') {
                switchSettingsTab('profile');
            }
        }
    } catch (e) { console.warn('[v118.12.3] failed to fix active tab:', e); }

    // ============================================================
    // v118.28.2 · 超管 /admin 视图模式
    //   - 显示红色顶部 banner
    //   - 砍所有非超管 nav(普通用户那一套 OCR / 历史 / 设置 全隐)
    //   - 砍顶栏客户切换器(平台管理员视角不需要切租户)
    // ============================================================
    if (window.PEARNLY_ADMIN_MODE) {
        const banner = document.getElementById('admin-mode-banner');
        if (banner) banner.style.display = 'flex';

        document.querySelectorAll('.nav-item').forEach(item => {
            if (!item.classList.contains('nav-admin-only')) {
                item.style.display = 'none';
            }
        });
        document.querySelectorAll('.nav-group').forEach(group => {
            if (!group.classList.contains('nav-group-admin-only')) {
                group.style.display = 'none';
            }
        });
        const cs = document.getElementById('client-switcher');
        if (cs) cs.style.display = 'none';
        document.body.classList.add('admin-mode');

        // v118.28.2.1 · 设置页里只保留超管自己用得上的 tab
        // 砍掉:公司信息 / 团队管理 / 套餐 / 归档规则 / 学习规则 / API 密钥 / 通用设置 / 访问日志
        // 保留:个人资料 / 账户安全 / 通知偏好 / 联系我们
        const _adminSettingsAllowed = ['profile', 'security', 'notifications', 'about'];
        document.querySelectorAll('.settings-tab').forEach(tab => {
            const name = tab.dataset.tab;
            if (name && !_adminSettingsAllowed.includes(name)) {
                tab.style.display = 'none';
            }
        });
        document.querySelectorAll('.settings-pane').forEach(pane => {
            const name = pane.dataset.pane;
            if (name && !_adminSettingsAllowed.includes(name)) {
                pane.style.display = 'none';
            }
        });
        // 隐藏所有 tab 都被砍掉的分组标题(防止"公司"标题下空荡荡)
        document.querySelectorAll('.settings-nav-group').forEach(group => {
            const visibleTabs = group.querySelectorAll('.settings-tab');
            const anyVisible = Array.from(visibleTabs).some(t => t.style.display !== 'none');
            if (!anyVisible) group.style.display = 'none';
        });
    }
}

// v0.15 · renderPlanDropdown 已废弃 · 顶部套餐下拉删除

function renderInfoBar() {
    const user = _userInfo;
    const bar = document.getElementById('info-bar');
    // v118.12 · 员工:配额 chip 是钱相关 · 短路返回(applySidebarVisibility 也设了 display:none 双保险)
    if (!user || shouldHideMoney(user)) {
        if (bar) bar.innerHTML = '';
        return;
    }

    // v87 · 用多租户正确字段 tenant_type 判断(之前用的 account_type 是老字段 · 建号时可能错)
    // shared_api = 月付共用 key · byo_api = 买断自带 key · admin = 超管
    let usageHtml = '';
    const tt = user.tenant_type;
    if (tt === 'byo_api') {
        // 买断自带 key
        if (user.has_own_gemini_key) {
            // 已填 key · 不限
            usageHtml = `
                <div class="info-chip">
                    <span class="chip-value chip-value-lifetime">${escapeHtml(t('info-unlimited-own-key'))}</span>
                </div>
            `;
        } else {
            // 未填 key · 提示
            usageHtml = `
                <div class="info-chip chip-warn">
                    <span class="chip-value">${escapeHtml(t('info-need-api-key'))}</span>
                </div>
            `;
        }
    } else if (tt === 'admin' || user.is_super_admin) {
        // 超管 · 无配额概念
        usageHtml = `
            <div class="info-chip">
                <span class="chip-value chip-value-lifetime">${escapeHtml(t('info-unlimited-own-key'))}</span>
            </div>
        `;
    } else {
        // shared_api · 月付共用 key(默认分支 · trial 也走这条)
        // v109.4 · 优先 tenant 字段 · 缺失回退 user 字段
        const used = (user.tenant_used != null) ? user.tenant_used : (user.used_this_month || 0);
        const total = (user.tenant_quota != null && user.tenant_quota > 0)
            ? user.tenant_quota
            : (user.monthly_quota || 0);
        const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0;
        let cls = '';
        if (pct >= 95) cls = 'danger';
        else if (pct >= 80) cls = 'warn';
        if (total > 0) {
            usageHtml = `
                <div class="info-chip">
                    <span class="chip-label">${escapeHtml(t('info-monthly'))}</span>
                    <span class="chip-value">${used} / ${total}</span>
                    <div class="mini-bar"><div class="mini-bar-fill ${cls}" style="width:${pct}%"></div></div>
                </div>
            `;
        } else {
            // 完全无配额信息 · 不显示 chip
            usageHtml = '';
        }
    }

    if (bar) bar.innerHTML = usageHtml;
}

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
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
['dragover', 'dragenter'].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
});
['dragleave', 'drop'].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
});

// v113 · 上传入口:拍摄(原生相机) + 上传图片(相册/本地 PDF)
// v113 · 删除 scanner.js · 整套浏览器内 OpenCV 实时检测移除
(function initUploadEntries() {
    const altRow = document.getElementById('upload-alt-row');
    const galInput = document.getElementById('gallery-input');
    const camInput = document.getElementById('camera-input');
    if (!altRow) return;

    // 移动端 + 桌面都显示
    altRow.style.display = '';

    // v113 · 拍摄票据 · 调原生相机 · 进 _cameraBuffer 流程
    const btnScanDoc = document.getElementById('btn-scan-doc');
    if (btnScanDoc && camInput) {
        btnScanDoc.addEventListener('click', async () => {
            // 显示拍摄贴士(用户可勾"不再提示"绕过)
            const skipTips = localStorage.getItem('mrpilot_camera_tips_skip') === '1';
            if (!skipTips) {
                const ok = await showCameraTips();
                if (!ok) return;
            }
            // 触发原生相机
            camInput.click();
        });
        // 拍照 input change · 每次返回 1 张 · 进 buffer
        camInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files || []);
            e.target.value = '';
            if (files.length === 0) return;
            for (const f of files) {
                await handleCameraImages([f], 'camera');
            }
        });
    }

    // v113 · 上传图片 · 走相册 · 多选 · 直接合并入流程
    const btnUploadPic = document.getElementById('btn-upload-pic');
    if (btnUploadPic && galInput) {
        btnUploadPic.addEventListener('click', () => galInput.click());
    }

    const onPick = (source) => async (e) => {
        const files = Array.from(e.target.files || []);
        e.target.value = '';
        if (files.length === 0) return;
        // v113 · 选图可能混 PDF · 拆开走两条路
        const pdfs = files.filter(f => f.type === 'application/pdf' || /\.pdf$/i.test(f.name));
        const imgs = files.filter(f => !pdfs.includes(f));
        if (pdfs.length > 0) await handleDirectPdfFiles(pdfs);
        if (imgs.length > 0) await handleCameraImages(imgs, source);
    };
    galInput && galInput.addEventListener('change', onPick('gallery'));
})();

// v113 · 用户从相册选了 PDF · 直接进 _selectedFiles · 不需要转换
async function handleDirectPdfFiles(pdfFiles) {
    for (const f of pdfFiles) {
        _selectedFiles.push({
            file: f,
            name: f.name,
            size: f.size,
            status: 'waiting', errorKey: null, errorParams: null,
        });
    }
    const maxFiles = getMaxFiles();
    if (_selectedFiles.length > maxFiles) {
        showAlert('warn', t('alert-file-count', { n: maxFiles }));
        _selectedFiles = _selectedFiles.slice(0, maxFiles);
    }
    renderFileList();
    updateStartButton();
}

// v0.17 · 拍照贴士弹窗 · 返回 Promise<bool>
function showCameraTips() {
    return new Promise(resolve => {
        const overlay = document.getElementById('camera-tips-modal');
        const btnOk = document.getElementById('camera-tips-ok');
        const btnCancel = document.getElementById('camera-tips-cancel');
        const chkSkip = document.getElementById('camera-tips-skip');
        if (!overlay || !btnOk) { resolve(true); return; }
        // 默认不勾选"不再提示"
        if (chkSkip) chkSkip.checked = false;
        overlay.style.display = 'flex';
        const cleanup = (go) => {
            overlay.style.display = 'none';
            if (chkSkip && chkSkip.checked) {
                localStorage.setItem('mrpilot_camera_tips_skip', '1');
            }
            btnOk.onclick = null;
            if (btnCancel) btnCancel.onclick = null;
            overlay.onclick = null;
            document.removeEventListener('keydown', onKey);
            resolve(go);
        };
        const onKey = (e) => { if (e.key === 'Escape') cleanup(false); };
        btnOk.onclick = () => cleanup(true);
        if (btnCancel) btnCancel.onclick = () => cleanup(false);
        overlay.onclick = (e) => { if (e.target === overlay) cleanup(false); };
        document.addEventListener('keydown', onKey);
        setTimeout(() => btnOk.focus(), 50);
    });
}

// v0.17 · 图片质量快速检查:返回 {warnings:[], width, height, brightness}
// 采样:缩到 64×64 算平均亮度(太小误差大 / 太大耗时),用 canvas
async function analyzeImageQuality(imgFile) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onerror = () => resolve({ warnings: [], width: 0, height: 0, brightness: 128 });
        reader.onload = () => {
            const img = new Image();
            img.onerror = () => resolve({ warnings: [], width: 0, height: 0, brightness: 128 });
            img.onload = () => {
                const warnings = [];
                const w = img.naturalWidth, h = img.naturalHeight;
                if (w < 1000 || h < 1000) warnings.push('low_res');
                try {
                    const cv = document.createElement('canvas');
                    cv.width = 64; cv.height = 64;
                    const ctx = cv.getContext('2d');
                    ctx.drawImage(img, 0, 0, 64, 64);
                    const data = ctx.getImageData(0, 0, 64, 64).data;
                    let sum = 0, n = 0;
                    for (let i = 0; i < data.length; i += 4) {
                        // 感知亮度加权(Rec.601 近似)
                        sum += 0.299*data[i] + 0.587*data[i+1] + 0.114*data[i+2];
                        n++;
                    }
                    const brightness = n ? sum / n : 128;
                    if (brightness < 70) warnings.push('too_dark');
                    else if (brightness > 235) warnings.push('too_bright');
                    resolve({ warnings, width: w, height: h, brightness });
                } catch (e) {
                    resolve({ warnings, width: w, height: h, brightness: 128 });
                }
            };
            img.src = reader.result;
        };
        reader.readAsDataURL(imgFile);
    });
}

// v0.17 · 把拍的图转成 PDF 后塞进现有 _selectedFiles 流程
// v0.17 · M3 · 连拍缓冲区(多张合并成 1 个 PDF)
// v118.27.8.1.14e · 缓冲区现在也接相册多选 · 让用户在浮条上自己选合并 vs 分别
let _cameraBuffer = [];  // { file, quality: {warnings, ...} }
let _cameraBufferSource = null;  // 'camera' | 'gallery' · 决定浮条「继续」按钮触发哪个 input

async function handleCameraImages(imageFiles, source) {
    hideAlerts();
    if (!imageFiles || imageFiles.length === 0) return;

    // 等 jsPDF 加载
    if (typeof window.jspdf === 'undefined' || !window.jspdf.jsPDF) {
        showToast(t('camera-loading'), 'info');
        for (let i = 0; i < 30; i++) {
            await new Promise(r => setTimeout(r, 100));
            if (window.jspdf && window.jspdf.jsPDF) break;
        }
        if (!window.jspdf || !window.jspdf.jsPDF) {
            showToast(t('camera-lib-fail'), 'error');
            return;
        }
    }

    // 拍照单张(source='camera' 且 1 张)→ 进缓冲区 · 显示浮条
    if (source === 'camera' && imageFiles.length === 1) {
        const f = imageFiles[0];
        let q = {};
        try { q = await analyzeImageQuality(f); } catch (e) {}
        _cameraBuffer.push({ file: f, quality: q });
        _cameraBufferSource = 'camera';
        renderCameraBufferBar();
        return;
    }

    // v118.27.8.1.14e · 相册多选 ≥2 张 · 或 buffer 已有图(用户点"继续选"追加)
    // → 进缓冲区 · 浮条让用户选「分别识别(默认)」或「合并为 1 个 PDF」
    // 痛点修复:之前强制合并 · 80%+ 场景用户是想批量传不同发票 · 默认合并是错的
    if (source === 'gallery' && (imageFiles.length >= 2 || _cameraBuffer.length > 0)) {
        for (const f of imageFiles) {
            let q = {};
            try { q = await analyzeImageQuality(f); } catch (e) {}
            _cameraBuffer.push({ file: f, quality: q });
        }
        _cameraBufferSource = 'gallery';
        renderCameraBufferBar();
        return;
    }

    // 相册单张(且 buffer 为空)→ 直接 1 张 = 1 个独立 PDF · 不打扰
    await flushImagesAsSeparatePdfs(imageFiles);
}

// 把一组图合并成 1 个 PDF · 加入 _selectedFiles
async function flushImagesAsOnePdf(imageFiles) {
    const warningSet = new Set();
    for (const f of imageFiles) {
        try {
            const q = await analyzeImageQuality(f);
            (q.warnings || []).forEach(w => warningSet.add(w));
        } catch (e) {}
    }
    try {
        const pdfFile = await imagesToPdf(imageFiles);
        if (pdfFile) {
            _selectedFiles.push({
                file: pdfFile,
                name: pdfFile.name,
                size: pdfFile.size,
                status: 'waiting', errorKey: null, errorParams: null,
            });
        }
    } catch (err) {
        console.error('[camera] convert failed', err);
        showToast(t('camera-convert-fail'), 'error');
        return;
    }

    const maxFiles = getMaxFiles();
    if (_selectedFiles.length > maxFiles) {
        showAlert('warn', t('alert-file-count', { n: maxFiles }));
        _selectedFiles = _selectedFiles.slice(0, maxFiles);
    }

    renderFileList();
    updateStartButton();
    showToast(t('camera-added-merged', { n: imageFiles.length }), 'success');

    if (warningSet.size > 0) {
        setTimeout(() => {
            if (warningSet.has('too_dark')) showToast(t('camera-quality-dark'), 'warn');
            else if (warningSet.has('low_res')) showToast(t('camera-quality-lowres'), 'warn');
            else if (warningSet.has('too_bright')) showToast(t('camera-quality-overexposed'), 'warn');
        }, 1000);
    }
}

// 浮条(拍照单张后 · 或相册多选后显示 · 让用户选合并/分别识别/继续添加)
// v118.27.8.1.14e · 按 _cameraBufferSource 决定:
//   camera 来源(拍照)→ 默认合并(常见场景:正反面/多页税单) · 「继续拍」触发 camera-input
//   gallery 来源(相册)→ 默认分别(常见场景:批量传不同发票) · 「继续选」触发 gallery-input
function renderCameraBufferBar() {
    let bar = document.getElementById('camera-buffer-bar');
    if (_cameraBuffer.length === 0) {
        if (bar) bar.remove();
        _cameraBufferSource = null;
        return;
    }
    if (!bar) {
        bar = document.createElement('div');
        bar.id = 'camera-buffer-bar';
        bar.className = 'camera-buffer-bar';
        document.body.appendChild(bar);
    }
    const n = _cameraBuffer.length;
    const showSep = n >= 2;
    const isGallery = _cameraBufferSource === 'gallery';
    const moreLabel = isGallery ? t('camera-buffer-more-gallery') : t('camera-buffer-more');

    // 主/副按钮分配:
    //   单张:仅一个「完成」按钮(合并 = 分别 = 1 个 PDF · 行为一致)
    //   多张相册:主 = 分别识别(默认) · 副 = 合并
    //   多张拍照:主 = 合并完成(默认) · 副 = 分别识别
    let actionsHtml;
    if (!showSep) {
        actionsHtml = `<button type="button" class="btn btn-primary btn-sm" data-cbb-action="merge">${escapeHtml(t('camera-buffer-done'))}</button>`;
    } else if (isGallery) {
        // 相册多选 · 默认分别
        actionsHtml = `
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="merge">${escapeHtml(t('camera-buffer-done-merge'))}</button>
            <button type="button" class="btn btn-primary btn-sm" data-cbb-action="separate">${escapeHtml(t('camera-buffer-done-separate', { n }))}</button>
        `;
    } else {
        // 拍照多张 · 默认合并(保留原行为)
        actionsHtml = `
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="separate">${escapeHtml(t('camera-buffer-done-separate', { n }))}</button>
            <button type="button" class="btn btn-primary btn-sm" data-cbb-action="merge">${escapeHtml(t('camera-buffer-done-merge'))}</button>
        `;
    }

    bar.innerHTML = `
        <div class="cbb-count">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7h4l2-2h6l2 2h4a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V8a1 1 0 011-1z"/>
                <circle cx="12" cy="13" r="4"/>
            </svg>
            <span>${escapeHtml(t('camera-buffer-count', { n }))}</span>
        </div>
        <div class="cbb-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="discard">${escapeHtml(t('camera-buffer-discard'))}</button>
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="more">${escapeHtml(moreLabel)}</button>
            ${actionsHtml}
        </div>
    `;

    bar.querySelector('[data-cbb-action="discard"]').onclick = () => {
        _cameraBuffer = [];
        _cameraBufferSource = null;
        renderCameraBufferBar();
    };
    bar.querySelector('[data-cbb-action="more"]').onclick = () => {
        // 按来源触发对应 input · 桌面端 camera-input 退化成文件选择器一样能用
        const inputId = isGallery ? 'gallery-input' : 'camera-input';
        const input = document.getElementById(inputId);
        if (input) input.click();
    };
    const mergeBtn = bar.querySelector('[data-cbb-action="merge"]');
    if (mergeBtn) {
        mergeBtn.onclick = async () => {
            const files = _cameraBuffer.map(x => x.file);
            _cameraBuffer = [];
            _cameraBufferSource = null;
            renderCameraBufferBar();
            await flushImagesAsOnePdf(files);
        };
    }
    const sepBtn = bar.querySelector('[data-cbb-action="separate"]');
    if (sepBtn) {
        sepBtn.onclick = async () => {
            const files = _cameraBuffer.map(x => x.file);
            _cameraBuffer = [];
            _cameraBufferSource = null;
            renderCameraBufferBar();
            await flushImagesAsSeparatePdfs(files);
        };
    }
}

// v118.27.8.1.14e · 注册 i18n 订阅 · 切语言时浮条立刻重渲
if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('camera-buffer-bar', () => {
        if (_cameraBuffer.length > 0) renderCameraBufferBar();
    });
}

// v113 · 把每张图分别转成独立 PDF · 加进 _selectedFiles
async function flushImagesAsSeparatePdfs(imageFiles) {
    const warningSet = new Set();
    let okCount = 0;
    for (const f of imageFiles) {
        try {
            const q = await analyzeImageQuality(f);
            (q.warnings || []).forEach(w => warningSet.add(w));
            const pdfFile = await imagesToPdf([f]);
            if (pdfFile) {
                _selectedFiles.push({
                    file: pdfFile,
                    name: pdfFile.name,
                    size: pdfFile.size,
                    status: 'waiting', errorKey: null, errorParams: null,
                });
                okCount++;
            }
        } catch (err) {
            console.error('[camera] separate convert failed', err);
        }
    }
    if (okCount === 0) {
        showToast(t('camera-convert-fail'), 'error');
        return;
    }
    const maxFiles = getMaxFiles();
    if (_selectedFiles.length > maxFiles) {
        showAlert('warn', t('alert-file-count', { n: maxFiles }));
        _selectedFiles = _selectedFiles.slice(0, maxFiles);
    }
    renderFileList();
    updateStartButton();
    showToast(t('camera-added-separate', { n: okCount }), 'success');

    if (warningSet.size > 0) {
        setTimeout(() => {
            if (warningSet.has('too_dark')) showToast(t('camera-quality-dark'), 'warn');
            else if (warningSet.has('low_res')) showToast(t('camera-quality-lowres'), 'warn');
            else if (warningSet.has('too_bright')) showToast(t('camera-quality-overexposed'), 'warn');
        }, 1000);
    }
}

// v0.17 · 单张图片 → PDF(自动按图片比例设置页面)
// v0.17 · M3 · 多张图片合并成一个 PDF(每张图独占一页)
// 单张也走这个函数 · 保持向后兼容
async function imagesToPdf(imgFiles) {
    if (!imgFiles || imgFiles.length === 0) return null;
    const { jsPDF } = window.jspdf;
    // A4 尺寸(mm)
    const pageW = 210, pageH = 297;
    const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'p' });

    for (let i = 0; i < imgFiles.length; i++) {
        const imgFile = imgFiles[i];
        const { dataUrl, naturalW, naturalH } = await _readImage(imgFile);
        if (i > 0) pdf.addPage('a4', 'p');
        const ratio = naturalW / naturalH;
        let drawW = pageW - 10;
        let drawH = drawW / ratio;
        if (drawH > pageH - 10) {
            drawH = pageH - 10;
            drawW = drawH * ratio;
        }
        const x = (pageW - drawW) / 2;
        const y = (pageH - drawH) / 2;
        const fmt = (imgFile.type === 'image/png') ? 'PNG' : 'JPEG';
        pdf.addImage(dataUrl, fmt, x, y, drawW, drawH, undefined, 'FAST');
    }
    const blob = pdf.output('blob');
    const now = new Date();
    const ts = now.getFullYear().toString()
        + String(now.getMonth()+1).padStart(2,'0')
        + String(now.getDate()).padStart(2,'0')
        + String(now.getHours()).padStart(2,'0')
        + String(now.getMinutes()).padStart(2,'0')
        + String(now.getSeconds()).padStart(2,'0');
    const suffix = imgFiles.length > 1 ? `_${imgFiles.length}p` : '';
    return new File([blob], `photo_${ts}${suffix}.pdf`, { type: 'application/pdf' });
}

function _readImage(imgFile) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = reject;
        reader.onload = () => {
            const img = new Image();
            img.onerror = reject;
            img.onload = () => resolve({
                dataUrl: reader.result,
                naturalW: img.naturalWidth,
                naturalH: img.naturalHeight,
            });
            img.src = reader.result;
        };
        reader.readAsDataURL(imgFile);
    });
}

// 保留旧函数名(其他调用点可能还用)· 内部走新函数
async function imageFileToPdf(imgFile) {
    return imagesToPdf([imgFile]);
}

// v118.35.0.3 · 主上传区接收 PDF / 图片 / Excel / CSV / Word — 跟 #file-input
// accept 属性 + drop-hint 文案对齐 · 之前只接 PDF 是个老遗留过滤(底层 OCR
// pipeline 已经多 schema 支持所有格式 / 后端 /api/ocr/recognize 也接全格式)
const _SUPPORTED_UPLOAD_EXT = /\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;
function _isImageFile(f) {
    return (f.type && f.type.startsWith('image/')) || /\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(f.name);
}
function _isPdfFile(f) {
    return f.type === 'application/pdf' || /\.pdf$/i.test(f.name);
}
function _isSupportedUpload(f) {
    return _isPdfFile(f) || _isImageFile(f) || _SUPPORTED_UPLOAD_EXT.test(f.name);
}

function handleFiles(fileList) {
    hideAlerts();
    const all = Array.from(fileList);
    const supported = all.filter(_isSupportedUpload);
    if (supported.length !== all.length) {
        showAlert('warn', t('alert-unsupported-format'));
    }

    // 图片走 imagesToPdf 通道(保留拍照单张缓冲条 UX),其他(PDF / Excel / CSV /
    // Word / TXT)直接入 _selectedFiles · 后端走 multi-format pipeline
    const directFiles = supported.filter(f => !_isImageFile(f));
    const imageFiles  = supported.filter(_isImageFile);

    const existing = new Set(_selectedFiles.map(f => f.name + '_' + f.size));
    for (const f of directFiles) {
        const key = f.name + '_' + f.size;
        if (!existing.has(key)) {
            _selectedFiles.push({
                file: f, name: f.name, size: f.size,
                status: 'waiting', errorKey: null, errorParams: null,
            });
            existing.add(key);
        }
    }

    if (imageFiles.length > 0) {
        // 复用相册多选路径 · 默认每张图独立成 1 个 PDF · 用户可在浮条里改"合并"
        try {
            handleCameraImages(imageFiles, 'gallery');
        } catch (err) {
            console.error('[upload] image route failed', err);
        }
    }

    const maxFiles = getMaxFiles();
    if (_selectedFiles.length > maxFiles) {
        showAlert('warn', t('alert-file-count', { n: maxFiles }));
        _selectedFiles = _selectedFiles.slice(0, maxFiles);
    }

    renderFileList();
    updateStartButton();
    fileInput.value = '';
}

// 文件列表展开状态(false = 紧凑滚动框)
let _fileListExpanded = false;

function renderFileList() {
    const list = document.getElementById('file-list');
    // v118.44.0.2 · admin layout 没有 #file-list DOM · 加防御避免 applyLang 抛错 / lang-switching class 残留
    if (!list) return;
    if (_selectedFiles.length === 0) {
        list.classList.remove('has-files');
        list.innerHTML = '';
        return;
    }
    list.classList.add('has-files');

    const total = _selectedFiles.length;
    const processing = _selectedFiles.filter(f => f.status === 'processing' || f.status === 'retrying').length;
    const success = _selectedFiles.filter(f => f.status === 'success').length;
    const error = _selectedFiles.filter(f => f.status === 'error').length;

    let progressText = `<span class="count">${escapeHtml(t('file-list-total', { n: total }))}</span>`;
    const parts = [];
    if (processing) parts.push(`<span style="color: var(--accent, #111111);">${processing} ${escapeHtml(t('status-processing'))}</span>`);
    if (success)    parts.push(`<span style="color: var(--success, #059669);">${success} ${escapeHtml(t('status-success'))}</span>`);
    if (error)      parts.push(`<span style="color: var(--danger, #dc2626);">${error} ${escapeHtml(t('status-error'))}</span>`);
    if (parts.length) progressText += ' · ' + parts.join(' · ');

    const toggleLabel = _fileListExpanded ? t('file-list-collapse') : t('file-list-expand');

    const itemsHtml = _selectedFiles.map((f, idx) => {
        let statusText = t('status-' + f.status);
        if (f.status === 'retrying') statusText = t('status-retrying');
        if (f.status === 'error' && f.errorKey) {
            statusText = t(f.errorKey, f.errorParams || {});
        }
        const spinner = (f.status === 'processing' || f.status === 'retrying') ? '<span class="spinner"></span>' : '';
        // v92 · Bug 7 · 失败文件显示重试按钮
        const retryBtn = (f.status === 'error' && f.canRetry)
            ? `<button class="file-retry-btn" data-retry-idx="${idx}" title="${escapeHtml(t('upload-retry-btn'))}">${svgIcon('refresh', 12)}<span>${escapeHtml(t('upload-retry-btn'))}</span></button>`
            : '';
        // v92 · Bug 8 · 缓存命中标签
        const cacheBadge = (f.status === 'success' && f.fromCache)
            ? `<span class="file-cache-badge">${svgIcon('cache', 11)}<span>${escapeHtml(t('cache-hit-badge'))}</span></span>`
            : '';
        return `
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</span>
                ${cacheBadge}
                <span class="file-status ${f.status}">${spinner}${statusText}</span>
                ${retryBtn}
            </li>
        `;
    }).join('');

    list.innerHTML = `
        <div class="file-list-head">
            <div>${progressText}</div>
            ${total > 5 ? `<button class="toggle" id="file-list-toggle">${escapeHtml(toggleLabel)}</button>` : ''}
        </div>
        <ul class="file-list-body${_fileListExpanded ? ' expanded' : ''}" id="file-list-body">
            ${itemsHtml}
        </ul>
    `;

    const toggleBtn = document.getElementById('file-list-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            _fileListExpanded = !_fileListExpanded;
            renderFileList();
        });
    }

    // v92 · Bug 7 · 重试按钮事件委托
    const body = document.getElementById('file-list-body');
    if (body && !body.dataset.retryBound) {
        body.dataset.retryBound = '1';
        body.addEventListener('click', async (e) => {
            const btn = e.target.closest('.file-retry-btn');
            if (!btn) return;
            const idx = parseInt(btn.dataset.retryIdx || '-1', 10);
            if (idx < 0 || idx >= _selectedFiles.length) return;
            const f = _selectedFiles[idx];
            if (!f || f.status !== 'error') return;
            // 手动重试 · 不走自动重试逻辑(传 isAutoRetry = true 阻止二次自动重试)
            if (typeof window._reprocessFile === 'function') {
                await window._reprocessFile(f, true);
            }
        });
    }
}

function updateStartButton() {
    const btnStart = document.getElementById('btn-start');
    const btnClear = document.getElementById('btn-clear');
    const btnExport = document.getElementById('btn-export');
    const hasWaiting = _selectedFiles.some(f => f.status === 'waiting');
    btnStart.disabled = _selectedFiles.length === 0 || !hasWaiting;
    btnClear.disabled = _selectedFiles.length === 0 && _results.length === 0;
    btnExport.disabled = _results.length === 0;
}

// 清空
document.getElementById('btn-clear').addEventListener('click', () => {
    _selectedFiles = [];
    _results = [];
    renderFileList();
    renderResults();
    updateStartButton();
    hideAlerts();
});

// ============================================================
// 开始识别
// ============================================================
document.getElementById('btn-start').addEventListener('click', async () => {
    hideAlerts();
    document.getElementById('btn-start').disabled = true;

    // 只有 Free 用户需要检查 EasyOCR 引擎是否就绪(Plus/Pro 走 Gemini 秒响应)
    if (_userInfo && _userInfo.plan === 'free') {
        const health = await fetch('/api/health').then(r => r.json()).catch(() => null);
        if (health && !health.ocr_ready) {
            showAlert('info', t('alert-loading-engine'));
            startEnginePolling();
        }
    }

    // v118.20.1.6 · 并行处理多 PDF · 提到 6 路(后端单 PDF 内已 3 并发 · 总并发 ≤ Gemini 60 RPM · Tier 2 安全)
    const pendingFiles = _selectedFiles.filter(f => f.status === 'waiting');
    const PARALLEL_LIMIT = 6;

    async function processOneFile(f, isAutoRetry) {
        // v118.20.6 · 用户已点停止 · 把待跑文件标 cancelled 跳过
        if (window._ocrAborted) {
            f.status = 'cancelled';
            f.errorKey = null;
            renderFileList();
            return {};
        }
        f.status = isAutoRetry ? 'retrying' : 'processing';
        f.canRetry = false;  // 重置重试标记
        renderFileList();

        // v92 · Bug 7 · 90 秒超时(AbortController)
        const ctrl = new AbortController();
        const timeoutId = setTimeout(() => ctrl.abort('timeout'), 90000);
        // v118.20.6 · 注册到全局 · 用户点停止时一次性 abort 所有 in-flight
        window._ocrCtrls = window._ocrCtrls || new Set();
        window._ocrCtrls.add(ctrl);

        try {
            const form = new FormData();
            form.append('file', f.file, f.name);
            // v27.8.1.13a · 右上角客户切换器选中时 · 自动归属到该客户
            try {
                if (typeof window.getCurrentClientId === 'function') {
                    const _cid = window.getCurrentClientId();
                    if (_cid != null) form.append('client_id', String(_cid));
                }
            } catch (_e) {}
            const resp = await fetch('/api/ocr/recognize', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: form,
                signal: ctrl.signal,
            });
            clearTimeout(timeoutId);
            window._ocrCtrls.delete(ctrl);

            if (resp.status === 401 || resp.status === 403) {
                // v0.15.6 · 只有真正 auth 失败才跳登录 · 其他 403(如 need_api_key)走业务错误展示
                const cloned = resp.clone();
                const body = await cloned.json().catch(() => ({}));
                const _det = body && body.detail;
                const code = (typeof _det === 'string') ? _det : ((_det && _det.code) || '');
                if (!code || code.startsWith('auth.')) {
                    localStorage.removeItem('mrpilot_token');
                    if (code === 'auth.session_revoked') {
                        _showSessionRevokedModal();
                    } else {
                        const _mk = (code === 'auth.password_changed_relogin') ? 'alert-password-changed-relogin' : 'alert-session';
                        showToast(t(_mk), 'error');
                        setTimeout(() => { window.location.href = '/'; }, 1200);
                    }
                    return { abort: true };
                }
                if (code === 'quota.need_api_key') {
                    showToast(t('err.quota.need_api_key'), 'error');
                }
                // 让下方 !resp.ok 分支接手,展示在文件卡片上
            }

            if (!resp.ok) {
                const data = await resp.json().catch(() => ({}));
                const detail = data.detail;
                if (typeof detail === 'string') {
                    f.errorKey = 'err.' + detail; f.errorParams = null;
                } else if (detail && detail.code) {
                    f.errorKey = 'err.' + detail.code;
                    f.errorParams = { ...detail, mb: _quota.max_file_size_mb };
                } else {
                    f.errorKey = 'err.unknown'; f.errorParams = null;
                }
                // v118.20.6 · HTTP 状态码兜底分类(detail 没说清时按 status 归类)
                if (f.errorKey === 'err.unknown' || f.errorKey === 'err.ocr.engine_error') {
                    if (resp.status === 429) f.errorKey = 'err.rate_limit';
                    else if (resp.status === 502 || resp.status === 503 || resp.status === 504) f.errorKey = 'err.gemini_overloaded';
                    else if (resp.status >= 500) f.errorKey = 'err.server';
                }
                f.status = 'error';
                // v92 · Bug 7 · 服务端错误可以重试(除了格式/大小等用户侧问题)
                f.canRetry = !/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(f.errorKey || '');
                renderFileList();
                return {};
            }

            const data = await resp.json();
            f.status = 'success';
            // v92 · Bug 8 · 标记缓存命中
            f.fromCache = !!data.from_cache;

            const merged = mergeFields(data.pages);
            const confidence = data.confidence ||
                ((merged.items && merged.items.length > 0) ? 'high' : 'low');

            _results.push({
                filename: data.filename,
                pages: data.pages,
                page_count: data.page_count,
                elapsed_ms: data.elapsed_ms,
                engine: data.engine,
                merged_fields: merged,
                edits: {},
                confidence: confidence,
                history_id: data.history_id,
                history_ids: data.history_ids || [],       // v0.11
                invoice_count: data.invoice_count || 1,    // v0.11
                invoices: data.invoices || [],             // v118.27.5.1 · 多发票拆分修复 · 每张独立 fields
                archive_name: data.archive_name || null,
                category_tag: data.category_tag || null,
                auto_pushed: !!data.auto_pushed,
                typhoon_enhanced: !!data.typhoon_enhanced,           // v0.12
                typhoon_pages: data.typhoon_pages || [],             // v0.12
                from_cache: !!data.from_cache,                       // v92 · Bug 8
            });

            // v0.11 · 识别到多张发票时额外提示
            if (data.invoice_count && data.invoice_count > 1) {
                showToast(t('multi-invoice-toast', {
                    file: data.filename,
                    n: data.invoice_count,
                }), 'success');
            }

            // P0 修 (2026-05-26) · 同页多票防静默漏:后端检测到某页发票号候选数 >
            // 实际识别数 → 明确警告用户"可能漏识别发票 · 请人工核对"· 不静默成功。
            if (data.missed_invoice_warnings && data.missed_invoice_warnings.length) {
                const _pages = data.missed_invoice_warnings
                    .map(function (w) { return w.page; })
                    .filter(function (p) { return p != null; });
                showToast(
                    t('missed-invoice-warn', {
                        file: data.filename,
                        pages: _pages.join(', '),
                    }),
                    'warn',
                    8000,
                );
                console.warn('[OCR] possible missed invoice(s)', data.missed_invoice_warnings);
            }

            // v0.12 · Typhoon 增援提示
            if (data.typhoon_enhanced && data.typhoon_pages && data.typhoon_pages.length) {
                showToast(t('typhoon-enhanced-toast', {
                    file: data.filename,
                    n: data.typhoon_pages.length,
                }), 'success');
            }

            // v103 · 引擎降级链提示 · Gemini 不可用时静默切换 · 用户至少知道
            if (data.fallback_used) {
                const chain = data.engine_chain || [];
                const usedEngine = data.engine || '';
                let key;
                if (usedEngine === 'typhoon_nvidia') key = 'fallback-typhoon-nvidia-toast';
                else if (usedEngine === 'easyocr')   key = 'fallback-easyocr-toast';
                else                                  key = 'fallback-generic-toast';
                showToast(t(key, { file: data.filename }), 'warn');
                console.info('[OCR Chain]', chain);
            }

            // v92 · Bug 8 · 缓存命中提示
            if (data.from_cache) {
                showToast(t('cache-hit-toast', { file: data.filename }), 'info');
            }

            // v0.13 · 重复发票警告 · 入队 · 等本批所有文件处理完后统一弹窗
            if (data.duplicate_warnings && data.duplicate_warnings.length) {
                if (!window._dupQueue) window._dupQueue = [];
                for (const w of data.duplicate_warnings) {
                    window._dupQueue.push({ filename: data.filename, ...w });
                }
            }

            // v0.9 · 自动推送提示(右下 toast)
            // A2 (Zihao 2026-05-19 拍板) · 改 info 颜色 + 文案明示"已开始 ·
            // 结果看推送日志" · auto_pushed 只是"已入队 asyncio.create_task"
            // 不是"已完成" · 显示 success 绿色会跟实际失败的推送日志矛盾.
            if (data.auto_pushed) {
                showToast(t('auto-push-fired', { file: data.filename }), 'info');
            }

            if (data.quota && data.quota.used_this_month != null && _userInfo) {
                // v109.4 · 同步更新两套字段 · 让所有用量显示都即时刷新
                _userInfo.used_this_month = data.quota.used_this_month;
                _userInfo.tenant_used = data.quota.used_this_month;
                renderInfoBar();
                renderQuotaBanner();
            }

            renderFileList();
            renderResults();
            updateStartButton();
            return {};
        } catch (e) {
            clearTimeout(timeoutId);
            try { window._ocrCtrls && window._ocrCtrls.delete(ctrl); } catch(_) { /* silent · Set 已删 */ }
            // v0.10.1 · 区分错误类型 · v92 · Bug 7 · 加超时
            console.error('[Upload] failed for', f.file.name, e);
            const isAbort = e && (e.name === 'AbortError' || e === 'timeout');
            const isTimeout = isAbort && (ctrl.signal.reason === 'timeout' || e === 'timeout');
            const isNetwork = e && e.message && /NetworkError|Failed to fetch/i.test(e.message);
            // v118.20.6 · 用户主动停止 · 不算错误 · 不重试 · 不入失败汇总
            const isCancelled = isAbort && (ctrl.signal.reason === 'user_stop' || window._ocrAborted);

            if (isCancelled) {
                f.status = 'cancelled';
                f.errorKey = null;
                f.canRetry = false;
                renderFileList();
                return {};
            }
            if (isTimeout) {
                f.errorKey = 'err.timeout';
            } else if (isAbort) {
                f.errorKey = 'err.aborted';
            } else if (isNetwork) {
                f.errorKey = 'err.network';
            } else {
                f.errorKey = 'err.unknown';
                f.errorParams = { msg: e && e.message ? e.message : String(e) };
            }
            f.status = 'error';
            // v92 · Bug 7 · 网络/超时错误可自动重试 1 次(用户停止后不重试)
            if (!isAutoRetry && !window._ocrAborted && (isNetwork || isTimeout) && navigator.onLine !== false) {
                f.canRetry = true;
                renderFileList();
                // 静默等 2 秒 · 自动重试 1 次
                await new Promise(r => setTimeout(r, 2000));
                if (f.status === 'error' && navigator.onLine !== false && !window._ocrAborted) {
                    return processOneFile(f, true);
                }
            }
            f.canRetry = true;  // 自动重试也失败 · 仍允许手动重试
            renderFileList();
            return {};
        }
    }
    // v92 · Bug 7 · 暴露给重试按钮事件委托使用
    window._reprocessFile = processOneFile;

    // 滑动窗口并行调度:始终保持 PARALLEL_LIMIT 个任务在跑
    let cursor = 0;
    let aborted = false;
    async function worker() {
        while (cursor < pendingFiles.length && !aborted && !window._ocrAborted) {
            const my = cursor++;
            const r = await processOneFile(pendingFiles[my]);
            if (r && r.abort) { aborted = true; return; }
        }
    }
    // v118.20.6 · 显示「停止识别」按钮 · 隐藏「开始识别」
    window._ocrAborted = false;
    window._ocrCtrls = window._ocrCtrls || new Set();
    const btnStartEl = document.getElementById('btn-start');
    const btnStopEl = document.getElementById('btn-stop');
    if (btnStartEl) btnStartEl.style.display = 'none';
    if (btnStopEl) btnStopEl.style.display = '';

    // v118.27.8.1.15 · 大批量(>100 张)进度条 + 关页警告 + 首次一次性提示
    try { if (typeof window._bigBatchStart === 'function') window._bigBatchStart(pendingFiles); } catch(_) { /* silent · 进度条 callback 极少 fail */ }

    const workers = [];
    for (let i = 0; i < Math.min(PARALLEL_LIMIT, pendingFiles.length); i++) {
        workers.push(worker());
    }
    await Promise.all(workers);

    // v118.27.8.1.15 · 批量结束 · 拆进度条 + 拆关页警告
    try { if (typeof window._bigBatchStop === 'function') window._bigBatchStop(); } catch(_) { /* silent · 进度条 callback 极少 fail */ }

    // v118.20.6 · 还原按钮显示 · 清理状态
    if (btnStartEl) btnStartEl.style.display = '';
    if (btnStopEl) btnStopEl.style.display = 'none';
    const wasAborted = !!window._ocrAborted;
    window._ocrAborted = false;
    window._ocrCtrls.clear();

    updateStartButton();
    stopEnginePolling();
    if (document.getElementById('alert-info').classList.contains('show')) {
        showAlert('info', t('alert-engine-ready'));
        setTimeout(hideAlerts, 2000);
    }

    // v118.20.6 · 完成后汇总 toast(成功 N · 失败按类型分组 · 用户主动停止时不弹错误类)
    try {
        const sum = { success: 0, cancelled: 0, network: 0, timeout: 0, quota: 0, overloaded: 0, rate: 0, other: 0 };
        for (const f of pendingFiles) {
            if (f.status === 'success') sum.success++;
            else if (f.status === 'cancelled') sum.cancelled++;
            else if (f.status === 'error') {
                const k = f.errorKey || '';
                if (k === 'err.network')                                  sum.network++;
                else if (k === 'err.timeout' || k === 'err.aborted')      sum.timeout++;
                else if (k.indexOf('quota') >= 0 || k === 'err.monthly_limit_exceeded') sum.quota++;
                else if (k === 'err.gemini_overloaded' || k === 'err.server') sum.overloaded++;
                else if (k === 'err.rate_limit')                          sum.rate++;
                else                                                       sum.other++;
            }
        }
        const total = pendingFiles.length;
        if (wasAborted) {
            showToast(_summaryAbortedToast(sum, total), 'warn', 4000);
        } else if (total > 1 && (sum.network + sum.timeout + sum.quota + sum.overloaded + sum.rate + sum.other) > 0) {
            showToast(_summaryFailToast(sum), 'error', 4500);
        }
    } catch(_) { /* silent · summary toast 失败外层兜底 */ }

    // v0.13 · 批量识别完成后 · 弹重复警告对话框(逐个处理)
    if (window._dupQueue && window._dupQueue.length) {
        showDuplicateDialog();
    }
});

// v118.20.6 · 汇总 toast 文案(中断态 / 失败态)
function _summaryAbortedToast(sum, total) {
    return t('ocr-summary-aborted')
        .replace('{success}', sum.success)
        .replace('{cancelled}', sum.cancelled)
        .replace('{total}', total);
}
function _summaryFailToast(sum) {
    const parts = [];
    if (sum.success)    parts.push(t('ocr-summary-success').replace('{n}', sum.success));
    if (sum.network)    parts.push(t('ocr-summary-network').replace('{n}', sum.network));
    if (sum.timeout)    parts.push(t('ocr-summary-timeout').replace('{n}', sum.timeout));
    if (sum.quota)      parts.push(t('ocr-summary-quota').replace('{n}', sum.quota));
    if (sum.overloaded) parts.push(t('ocr-summary-overloaded').replace('{n}', sum.overloaded));
    if (sum.rate)       parts.push(t('ocr-summary-rate').replace('{n}', sum.rate));
    if (sum.other)      parts.push(t('ocr-summary-other').replace('{n}', sum.other));
    return parts.join(' · ');
}

// v118.20.6 · 「停止识别」按钮事件 · 中断 in-flight + 标 abort
document.addEventListener('click', (e) => {
    if (!e.target.closest('#btn-stop')) return;
    if (window._ocrAborted) return;  // 防双击
    window._ocrAborted = true;
    if (window._ocrCtrls && window._ocrCtrls.size) {
        window._ocrCtrls.forEach(c => { try { c.abort('user_stop'); } catch(_) { /* silent · 已 abort */ } });
    }
    const btnStopEl = document.getElementById('btn-stop');
    if (btnStopEl) btnStopEl.disabled = true;
    if (typeof showToast === 'function') showToast(t('ocr-stop-toast'), 'warn', 2000);
    setTimeout(() => { if (btnStopEl) btnStopEl.disabled = false; }, 800);
});

// v0.13 · 重复发票警告对话框(逐张处理 · 用户操作完一条 → 显示下一条)
function showDuplicateDialog() {
    if (!window._dupQueue || !window._dupQueue.length) return;
    const w = window._dupQueue.shift();

    const isExact = w.level === 'exact';
    const titleKey = isExact ? 'dup-title-exact' : 'dup-title-likely';
    const descKey = isExact ? 'dup-desc-exact' : 'dup-desc-likely';
    const titleColor = isExact ? '#DC2626' : '#D97706';
    const titleBg = isExact ? '#FEE2E2' : '#FEF3C7';

    const fmtAmt = (v) => v != null ? Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—';
    const fmtDate = (v) => v || '—';
    const fmtCreated = (v) => {
        try { const d = new Date(v); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; }
        catch { return v; }
    };
    const partLabel = w.invoice_total > 1
        ? ` · ${t('invoice-part-of', { i: w.invoice_index, n: w.invoice_total })}`
        : '';

    const matchedFieldsHtml = (w.matched_fields || []).map(k => {
        const lbl = t('dup-field-' + k.replace('_', '-')) || k;
        return `<span class="dup-field-chip">${escapeHtml(lbl)}</span>`;
    }).join(' ');

    const modal = document.createElement('div');
    modal.className = 'log-detail-modal';
    modal.innerHTML = `
        <div class="log-detail-box dup-dialog">
            <div class="dup-head" style="background:${titleBg};">
                <div class="dup-title" style="color:${titleColor};">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:22px;height:22px;vertical-align:-5px;margin-right:6px;">
                        <path d="M10 2.5L1 17h18L10 2.5z"/><path d="M10 8v4M10 14v0.5"/>
                    </svg>
                    ${escapeHtml(t(titleKey))}
                </div>
                <button class="log-detail-close dup-close" type="button">✕</button>
            </div>
            <div class="dup-body">
                <div class="dup-desc">${escapeHtml(t(descKey))}</div>
                <div class="dup-source">
                    <div class="dup-source-label">${escapeHtml(t('dup-current-file'))}${escapeHtml(partLabel)}</div>
                    <div class="dup-source-name">${escapeHtml(w.filename)}</div>
                </div>
                <div class="dup-matched-label">${escapeHtml(t('dup-matched-on'))} ${matchedFieldsHtml}</div>
                <table class="dup-compare">
                    <thead>
                        <tr>
                            <th></th>
                            <th>${escapeHtml(t('dup-this-one'))}</th>
                            <th>${escapeHtml(t('dup-existing-one'))}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>${escapeHtml(t('dup-field-invoice-no'))}</td><td>${escapeHtml(w.current.invoice_no || '—')}</td><td>${escapeHtml(w.match.invoice_no || '—')}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-invoice-date'))}</td><td>${escapeHtml(fmtDate(w.current.invoice_date))}</td><td>${escapeHtml(fmtDate(w.match.invoice_date))}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-seller-name'))}</td><td>${escapeHtml(w.current.seller_name || '—')}</td><td>${escapeHtml(w.match.seller_name || '—')}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-total-amount'))}</td><td>${fmtAmt(w.current.total_amount)}</td><td>${fmtAmt(w.match.total_amount)}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-original-file'))}</td><td>—</td><td>${escapeHtml(w.match.filename || '—')}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-uploaded-at'))}</td><td>—</td><td>${escapeHtml(fmtCreated(w.match.created_at))}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="dup-actions">
                <button class="btn btn-ghost btn-tiny" data-action="view">${escapeHtml(t('dup-action-view'))}</button>
                <button class="btn btn-danger btn-tiny" data-action="delete">${escapeHtml(t('dup-action-delete'))}</button>
                <button class="btn btn-primary btn-tiny" data-action="keep">${escapeHtml(t('dup-action-keep'))}</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    const close = () => {
        modal.remove();
        // 处理下一条
        if (window._dupQueue && window._dupQueue.length) {
            setTimeout(showDuplicateDialog, 200);
        }
    };
    modal.querySelector('.dup-close').addEventListener('click', close);

    modal.querySelector('[data-action="view"]').addEventListener('click', () => {
        // 跳到历史页 · 打开原记录抽屉
        const matchId = w.match.id;
        window.location.hash = '#/history';
        setTimeout(() => {
            if (typeof openHistoryDrawer === 'function') openHistoryDrawer(matchId);
        }, 400);
        close();
    });

    modal.querySelector('[data-action="delete"]').addEventListener('click', async () => {
        // 删除"刚刚新建的这条"(因为是重复 · 用户决定不要)
        const newId = w.new_history_id;
        if (!newId) {
            close();
            return;
        }
        try {
            const resp = await fetch(`/api/history/${encodeURIComponent(newId)}`, {
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + token },
            });
            if (resp.ok) {
                showToast(t('dup-deleted-toast'), 'success');
            } else {
                showToast(t('dup-delete-failed'), 'error');
            }
        } catch (e) {
            showToast(t('dup-delete-failed'), 'error');
        }
        close();
    });

    modal.querySelector('[data-action="keep"]').addEventListener('click', close);
}

function mergeFields(pages) {
    const result = {
        invoice_number: null, date: null, total_amount: null, tax_ids: [],
        seller_name: '', seller_tax: '', seller_addr: '',
        buyer_name: '', buyer_tax: '', buyer_addr: '',
        subtotal: '', vat: '', notes: '', items: [],
    };
    // 只取主页(非副本/重复页)
    const primaryPages = pages.filter(p => !p.is_duplicate && !p.is_copy);
    const sourcePages = primaryPages.length > 0 ? primaryPages : pages;
    for (const p of sourcePages) {
        const f = p.fields || {};
        // 标量字段:取第一个非空值
        if (!result.invoice_number && f.invoice_number) result.invoice_number = f.invoice_number;
        if (!result.date && f.date) result.date = f.date;
        if (!result.total_amount && f.total_amount) result.total_amount = f.total_amount;
        if (!result.subtotal && f.subtotal) result.subtotal = f.subtotal;
        if (!result.vat && f.vat) result.vat = f.vat;
        if (!result.seller_name && f.seller_name) result.seller_name = f.seller_name;
        if (!result.seller_tax && f.seller_tax) result.seller_tax = f.seller_tax;
        if (!result.seller_addr && f.seller_addr) result.seller_addr = f.seller_addr;
        if (!result.buyer_name && f.buyer_name) result.buyer_name = f.buyer_name;
        if (!result.buyer_tax && f.buyer_tax) result.buyer_tax = f.buyer_tax;
        if (!result.buyer_addr && f.buyer_addr) result.buyer_addr = f.buyer_addr;
        if (!result.notes && f.notes) result.notes = f.notes;
        // 数组字段:合并所有页
        if (Array.isArray(f.items) && f.items.length) result.items.push(...f.items);
        if (Array.isArray(f.tax_ids)) result.tax_ids.push(...f.tax_ids);
    }
    // 兜底:若 seller_tax / buyer_tax 仍空,从 tax_ids 取
    result.tax_ids = [...new Set(result.tax_ids)];
    if (!result.seller_tax && result.tax_ids[0]) result.seller_tax = result.tax_ids[0];
    if (!result.buyer_tax && result.tax_ids[1]) result.buyer_tax = result.tax_ids[1];
    return result;
}

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

// ============================================================
// 结果渲染
// ============================================================
function renderResults() {
    const card = document.getElementById('results-card');
    if (_results.length === 0) {
        card.classList.remove('show');
        return;
    }
    card.classList.add('show');

    // 顶部统计条:发票数 · 识别成功率 · 合计金额(一行)
    // v118.20.1.6 · 改用「识别成功率」语义(以前的「高置信」会误导用户跳过复核)
    let totalSum = 0;
    _results.forEach(r => {
        const v = parseFloat(r.merged_fields.total_amount);
        if (!isNaN(v)) totalSum += v;
    });
    const totalFiles = (_selectedFiles && _selectedFiles.length) || _results.length;
    const successCount = _results.length;
    const successRate = totalFiles > 0 ? Math.round((successCount / totalFiles) * 100) : 0;
    const totalFmt = totalSum.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    document.getElementById('results-head-stats').innerHTML = `
        <div class="rh-stat">
            <span class="rh-stat-value">${successCount}</span>
            <span class="rh-stat-label">${t('stats-invoices')}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t('stats-total')}</span>
            <span class="rh-stat-value">฿ ${totalFmt}</span>
        </div>
    `;

    // 过滤 + 排序
    let rows = _results.map((r, idx) => ({ ...r, _idx: idx }));
    if (_searchKeyword) {
        const kw = _searchKeyword.toLowerCase();
        rows = rows.filter(r =>
            (r.filename || '').toLowerCase().includes(kw) ||
            (r.merged_fields.invoice_number || '').toLowerCase().includes(kw)
        );
    }
    if (_sortKey) {
        rows.sort((a, b) => {
            let va, vb;
            if (_sortKey === 'filename') { va = a.filename; vb = b.filename; }
            else if (_sortKey === 'invoice_no') { va = a.merged_fields.invoice_number; vb = b.merged_fields.invoice_number; }
            else if (_sortKey === 'invoice_date') { va = a.merged_fields.date; vb = b.merged_fields.date; }
            else if (_sortKey === 'total') { va = parseFloat(a.merged_fields.total_amount) || 0; vb = parseFloat(b.merged_fields.total_amount) || 0; }
            else if (_sortKey === 'confidence') { va = a.confidence; vb = b.confidence; }
            else { va = ''; vb = ''; }
            if (va < vb) return _sortDir === 'asc' ? -1 : 1;
            if (va > vb) return _sortDir === 'asc' ? 1 : -1;
            return 0;
        });
    }

    const tbody = document.getElementById('results-tbody');
    tbody.innerHTML = rows.map((r, visibleIdx) => {
        const f = r.merged_fields;
        const emptyCell = `<span class="empty-cell">${t('empty-val')}</span>`;
        const confTipKey = 'conf-tip-' + (r.confidence || 'low');
        const confLabelKey = 'conf-' + (r.confidence || 'low');
        const confTip = t(confTipKey);
        const confLabel = t(confLabelKey);
        return `
            <tr data-idx="${r._idx}">
                <td class="num">${visibleIdx + 1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${f.invoice_number ? escapeHtml(f.invoice_number) : emptyCell}</td>
                <td class="date">${f.date ? escapeHtml(f.date) : emptyCell}</td>
                <td class="amount">${f.total_amount ? Number(f.total_amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : emptyCell}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(confTip)}">${confLabel}</span></td>
            </tr>
        `;
    }).join('');

    document.querySelectorAll('#results-table th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.dataset.sort === _sortKey) th.classList.add('sort-' + _sortDir);
    });

    tbody.querySelectorAll('tr').forEach(tr => {
        tr.addEventListener('click', () => {
            const idx = parseInt(tr.dataset.idx, 10);
            openDrawer(idx);
        });
    });
}

// 排序点击
document.querySelectorAll('#results-table th').forEach(th => {
    if (th.classList.contains('no-sort')) return;
    th.addEventListener('click', () => {
        const key = th.dataset.sort;
        if (_sortKey === key) _sortDir = _sortDir === 'asc' ? 'desc' : 'asc';
        else { _sortKey = key; _sortDir = 'asc'; }
        renderResults();
    });
});

// v0.11 · 识别页搜索:防抖 + 清除按钮 + 匹配计数
let _resultsSearchTimer = null;
document.getElementById('search-input').addEventListener('input', (e) => {
    const val = e.target.value;
    document.getElementById('search-clear').style.display = val ? '' : 'none';
    clearTimeout(_resultsSearchTimer);
    _resultsSearchTimer = setTimeout(() => {
        _searchKeyword = val.trim();
        renderResults();
        updateResultsMatchCount();
    }, 200);
});
document.getElementById('search-clear').addEventListener('click', () => {
    const input = document.getElementById('search-input');
    input.value = '';
    _searchKeyword = '';
    document.getElementById('search-clear').style.display = 'none';
    renderResults();
    updateResultsMatchCount();
    input.focus();
});

function updateResultsMatchCount() {
    const el = document.getElementById('search-matches');
    if (!el) return;
    if (!_searchKeyword) { el.textContent = ''; return; }
    const kw = _searchKeyword.toLowerCase();
    let n = 0;
    for (const r of _results) {
        const hay = [
            r.filename,
            r.merged_fields?.invoice_number,
            r.merged_fields?.seller_name,
            r.merged_fields?.buyer_name,
        ].filter(Boolean).join(' ').toLowerCase();
        if (hay.includes(kw)) n++;
    }
    el.textContent = t('search-matches', { n });
}

// ============================================================
// 抽屉
// ============================================================
function openDrawer(idx) {
    _drawerIdx = idx;
    const r = _results[idx];
    if (!r) return;

    document.getElementById('drawer-title').textContent = r.filename;

    // 副标题:页数 + 耗时 + 缓存标记(隐藏引擎档位 · v0.15.6)
    const isCached = (r.engine === 'cache' || r.from_cache);
    const timeText = isCached ? t('badge-cached-hint') : `${(r.elapsed_ms/1000).toFixed(1)}s`;
    document.getElementById('drawer-sub').innerHTML = `
        <span>${r.page_count} ${t('pages-unit')} · ${escapeHtml(timeText)}</span>
        ${isCached ? `<span class="engine-badge cached">${escapeHtml(t('badge-cached'))}</span>` : ''}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `;
    updateDrawerEditCount();

    const canEdit = _userInfo && _userInfo.can_edit_fields;
    const canVerifyTax = _userInfo && _userInfo.can_verify_tax;

    const f = r.merged_fields;
    const body = document.getElementById('drawer-body');

    const readonlyBanner = canEdit ? '' : `
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t('readonly-banner')}</span>
        </div>
    `;

    const taxBadge = canVerifyTax ? '' : `<span class="tax-badge unverified" data-tip="${escapeHtml(t('tax-tip-unverified'))}">${t('tax-unverified')}</span>`;

    body.innerHTML = `
        ${readonlyBanner}

        <!-- v118.19 · 决策区(C 位) · 会计每张发票真正要做的两个决策 -->
        <div class="drawer-decision-zone">
            <div class="drawer-decision-title">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="3.5" cy="3" r="1.4"/>
                    <circle cx="3.5" cy="13" r="1.4"/>
                    <circle cx="12.5" cy="8" r="1.4"/>
                    <path d="M3.5 4.4v7.2"/>
                    <path d="M3.5 8h7.6"/>
                </svg>
                <span>${escapeHtml(t('drawer-decision-title'))}</span>
            </div>
            <div class="drawer-decision-grid">
                <!-- 归属客户(左) -->
                <div class="drawer-client-card" data-field-wrap="client_id">
                    <div class="drawer-client-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 14v-1.2a2.4 2.4 0 00-2.4-2.4H4a2.4 2.4 0 00-2.4 2.4V14"/>
                            <circle cx="6.4" cy="5.2" r="2.4"/>
                        </svg>
                        <span>${escapeHtml(t('drawer-client-label'))}</span>
                    </div>
                    <div class="drawer-client-body">
                        <select class="drawer-client-select" id="drawer-client-select" ${canEdit ? '' : 'disabled'}>
                            <option value="">${escapeHtml(t('drawer-client-none'))}</option>
                        </select>
                        <button class="drawer-client-add" id="drawer-client-add" type="button" title="${escapeHtml(t('client-new'))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M7 2v10M2 7h10"/></svg>
                        </button>
                    </div>
                </div>

                <!-- 记账科目(右) · 学过的发亮 -->
                <div class="drawer-suggest-card" data-field-wrap="category_tag">
                    <div class="drawer-suggest-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M2 4a1 1 0 011-1h4l2 2h5a1 1 0 011 1v6a1 1 0 01-1 1H3a1 1 0 01-1-1V4z"/>
                        </svg>
                        <span>${escapeHtml(t('drawer-suggest-category'))}</span>
                        ${(f.category || r.category_tag)
                            ? `<span class="drawer-suggest-learned" id="drawer-cat-learned-tag" title="${escapeHtml(t('drawer-suggest-learned-tip'))}">${escapeHtml(t('drawer-suggest-learned'))}</span>`
                            : `<span class="drawer-suggest-empty">${escapeHtml(t('drawer-suggest-empty'))}</span>`}
                    </div>
                    <div class="drawer-suggest-body">
                        <input type="text" class="drawer-suggest-input" id="drawer-cat-input" data-field="category_tag"
                               list="drawer-cat-datalist"
                               placeholder="${escapeHtml(t('drawer-suggest-placeholder'))}"
                               value="${escapeHtml((r.edits && r.edits.category_tag !== undefined ? r.edits.category_tag : (f.category || r.category_tag)) || '')}"
                               ${canEdit ? '' : 'readonly'}>
                        <datalist id="drawer-cat-datalist"></datalist>
                    </div>
                </div>
            </div>
            <div class="drawer-decision-hint">${escapeHtml(t('drawer-suggest-hint'))}</div>
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 2h8l3 3v13H5z"/><path d="M13 2v3h3"/><path d="M8 10h6M8 13h6"/></svg>
                ${t('drawer-sec-basic')}
            </div>
            ${renderField('invoice_number', 'drawer-lbl-invoice', f.invoice_number, 'input', canEdit)}
            ${renderField('date', 'drawer-lbl-date', f.date, 'input', canEdit)}
            ${(f.date_raw && f.date_raw !== f.date) ? `<div class="date-raw-hint" title="${escapeHtml(t('drawer-date-raw-tip'))}">${escapeHtml(t('drawer-date-raw-label'))}: ${escapeHtml(f.date_raw)}</div>` : ''}
            ${renderField('subtotal', 'drawer-lbl-subtotal', f.subtotal, 'input', canEdit)}
            ${renderField('vat', 'drawer-lbl-vat', f.vat, 'input', canEdit)}
            ${renderField('total_amount', 'drawer-lbl-total', f.total_amount, 'input', canEdit)}
            ${(f.wht_amount || f.wht_rate) ? `
                ${renderField('wht_amount', 'drawer-lbl-wht-amount', f.wht_amount, 'input', canEdit, renderWhtBadge(f.wht_rate))}
            ` : ''}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t('drawer-sec-seller')}
            </div>
            ${renderField('seller_name', 'drawer-lbl-name', f.seller_name, 'input', canEdit)}
            ${renderField('seller_tax', 'drawer-lbl-tax', f.seller_tax, 'input', canEdit, taxBadge, renderRdActions('seller'))}
            ${renderField('seller_addr', 'drawer-lbl-addr', f.seller_addr, 'textarea', canEdit)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t('drawer-sec-buyer')}
            </div>
            ${renderField('buyer_name', 'drawer-lbl-name', f.buyer_name, 'input', canEdit)}
            ${renderField('buyer_tax', 'drawer-lbl-tax', f.buyer_tax, 'input', canEdit, taxBadge, renderRdActions('buyer'))}
            ${renderField('buyer_addr', 'drawer-lbl-addr', f.buyer_addr, 'textarea', canEdit)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t('drawer-sec-items')}
            </div>
            ${f.items && f.items.length > 0 ? renderItems(f.items) : `<div class="drawer-items-empty">${t('drawer-items-empty')}</div>`}
        </div>

        <div class="drawer-section">
            ${renderField('notes', 'drawer-lbl-notes', f.notes, 'textarea', canEdit)}
        </div>

        <details class="raw-text">
            <summary>${t('raw-text')}</summary>
            <pre>${escapeHtml(r.pages.map(p => `--- Page ${p.page || p.page_number || '?'} ---\n${p.raw_text || p.text || ''}`).join('\n\n'))}</pre>
        </details>
    `;

    if (canEdit) {
        body.querySelectorAll('[data-field]').forEach(input => {
            input.addEventListener('input', onFieldEdit);
        });
    } else {
        // v0.15 · 扁平权限下所有人都能编辑 · 此分支保留只读状态(不再弹升级)
        body.querySelectorAll('[data-field]').forEach(input => {
            input.setAttribute('readonly', 'readonly');
        });
    }

    document.getElementById('drawer-mask').classList.add('show');
    document.getElementById('drawer').classList.add('show');

    // 识别页抽屉底部推 ERP 按钮(历史模式由另一个函数 injectHistorySaveButton 处理)
    injectOcrPushButton();

    // v118.16 · 修 BUG · 识别中心抽屉打开时也填充客户下拉(之前漏调 · 单据记录抽屉有但识别中心没有)
    if (typeof window.bindDrawerClient === 'function') {
        const hid = r._historyId || r.history_id || null;
        window.bindDrawerClient(hid, r.client_id || null);
    }

    // v118.18 · 推荐分类 datalist 自动补全(用过的科目)
    if (typeof window.fillCategoryDatalist === 'function') {
        window.fillCategoryDatalist();
    }

    // v118.19 · 键盘流 · 如果记账科目为空 · 自动 focus 让会计直接键盘录入
    // 之所以 focus 科目而不是客户:学过的供应商客户通常自动绑定 · 科目才是会计每天主动填的字段
    setTimeout(() => {
        const catInput = document.getElementById('drawer-cat-input');
        if (catInput && !catInput.value && !catInput.readOnly) {
            catInput.focus();
        }
    }, 80);
}

function renderWhtBadge(rate) {
    if (!rate) return '';
    return `<span class="wht-badge">${escapeHtml(rate)}%</span>`;
}

function renderField(key, labelKey, value, type, canEdit, badgeHtml, actionsHtml) {
    const r = _results[_drawerIdx];
    const editedValue = r && r.edits[key] !== undefined ? r.edits[key] : value;
    const edited = r && r.edits[key] !== undefined && r.edits[key] !== value;
    const valEscaped = escapeHtml(editedValue ?? '');
    const readonlyCls = canEdit ? '' : 'readonly';
    const inputHtml = type === 'textarea'
        ? `<textarea data-field="${key}" rows="2">${valEscaped}</textarea>`
        : `<input type="text" data-field="${key}" value="${valEscaped}">`;
    return `
        <div class="drawer-field ${edited ? 'edited' : ''} ${readonlyCls}" data-field-wrap="${key}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(labelKey)}
                ${badgeHtml || ''}
                ${actionsHtml ? `<span class="drawer-field-actions">${actionsHtml}</span>` : ''}
            </label>
            ${inputHtml}
        </div>
    `;
}

// 渲染税号字段右上角的 RD 按钮(校验 + 同步)
function renderRdActions(side) {
    // side: 'seller' 或 'buyer'
    const canVerify = _userInfo && _userInfo.can_verify_tax;
    if (!canVerify) {
        // Free 用户:显示锁标(点击触发升级弹窗)
        return `<button class="rd-btn-locked" data-upgrade="plus" type="button" title="${escapeHtml(t('rd-tip-upgrade'))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="7" width="10" height="7" rx="1"/><path d="M5 7V5a3 3 0 016 0v2"/></svg>
        </button>`;
    }
    return `
        <button class="rd-btn rd-btn-verify" data-rd-action="verify" data-rd-side="${side}" type="button">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8l3 3 7-7"/></svg>
            ${t('rd-btn-verify')}
        </button>
        <button class="rd-btn rd-btn-sync" data-rd-action="sync" data-rd-side="${side}" type="button">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8a5 5 0 019-3l1.5 1.5M13 8a5 5 0 01-9 3L2.5 9.5M13 3v3h-3M3 13v-3h3"/></svg>
            ${t('rd-btn-sync')}
        </button>
        <span class="rd-status" data-rd-status="${side}"></span>
    `;
}

function renderItems(items) {
    return `
        <div class="drawer-items-header">
            <div>${t('drawer-item-name')}</div>
            <div>${t('drawer-item-qty')}</div>
            <div>${t('drawer-item-price')}</div>
            <div>${t('drawer-item-sub')}</div>
        </div>
        ${items.map(it => `
            <div class="drawer-item-row">
                <div>${escapeHtml(it.name || '')}</div>
                <div>${escapeHtml(it.qty || it.quantity || '')}</div>
                <div>${escapeHtml(it.price || it.unit_price || '')}</div>
                <div>${escapeHtml(it.subtotal || it.total || '')}</div>
            </div>
        `).join('')}
    `;
}

// ============================================================
// 第 5.1 批 · 泰国 RD 税务 API 调用
// ============================================================

// 独立 fetch(不走 apiPost · 避免 403 被误踢)
async function rdFetch(url, payload) {
    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (resp.status === 401) {
            localStorage.removeItem('mrpilot_token');
            const _bd = await resp.json().catch(() => ({}));
            const _dc = typeof _bd.detail === 'string' ? _bd.detail : ((_bd.detail && _bd.detail.code) || '');
            if (_dc === 'auth.session_revoked') { _showSessionRevokedModal(); return null; }
            window.location.href = '/';
            return null;
        }
        return await resp.json();
    } catch (e) {
        return { ok: false, error: 'network' };
    }
}

function _rdErrKey(code) {
    const map = {
        'invalid_format': 'rd-err-format',
        'not_found':      'rd-err-not-found',
        'rd_unreachable': 'rd-err-unreachable',
        'parse_error':    'rd-err-unknown',
        'network':        'rd-err-unreachable',
    };
    return map[code] || 'rd-err-unknown';
}

function _getFieldValue(key) {
    const el = document.querySelector(`[data-field="${key}"]`);
    return el ? (el.value || '').trim() : '';
}

function _setRdStatus(side, html, cls) {
    const el = document.querySelector(`[data-rd-status="${side}"]`);
    if (!el) return;
    el.innerHTML = html;
    el.className = 'rd-status' + (cls ? ' ' + cls : '');
}

async function callRdVerify(side) {
    const taxField = side === 'seller' ? 'seller_tax' : 'buyer_tax';
    const taxId = _getFieldValue(taxField);
    _setRdStatus(side, t('rd-verifying'), 'loading');
    const r = await rdFetch('/api/rd/verify', { tax_id: taxId });
    if (!r) return;
    if (!r.ok) {
        _setRdStatus(side, t(_rdErrKey(r.error)), 'error');
        return;
    }
    const valid = r.data && r.data.valid;
    if (valid) {
        _setRdStatus(side,
            `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t('rd-status-valid'))}`,
            'valid'
        );
    } else {
        _setRdStatus(side, t('rd-status-invalid'), 'invalid');
    }
}

async function callRdSync(side) {
    const taxField = side === 'seller' ? 'seller_tax' : 'buyer_tax';
    const taxId = _getFieldValue(taxField);
    _setRdStatus(side, t('rd-syncing'), 'loading');
    const r = await rdFetch('/api/rd/lookup', { tax_id: taxId, branch: 0 });
    if (!r) return;
    if (!r.ok) {
        _setRdStatus(side, t(_rdErrKey(r.error)), 'error');
        return;
    }
    _setRdStatus(side,
        `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t('rd-status-valid'))}`,
        'valid'
    );
    openRdSyncModal(side, r.data);
}

// ============================================================
// RD 同步对比弹窗
// ============================================================
function openRdSyncModal(side, official) {
    const nameKey = side === 'seller' ? 'seller_name' : 'buyer_name';
    const addrKey = side === 'seller' ? 'seller_addr' : 'buyer_addr';
    const curName = _getFieldValue(nameKey);
    const curAddr = _getFieldValue(addrKey);

    // 对比行:只有「官方有值 且 与当前不同」才纳入对比
    const rows = [];
    if (official.name && official.name !== curName) {
        rows.push({ field: nameKey, label: t('rd-field-name'), current: curName, official: official.name });
    }
    if (official.address && official.address !== curAddr) {
        rows.push({ field: addrKey, label: t('rd-field-address'), current: curAddr, official: official.address });
    }
    // branch_label 和 postcode 当作提示信息,不自动覆盖
    const extraInfo = [];
    if (official.branch_label) extraInfo.push(`<strong>${t('rd-field-branch')}:</strong> ${escapeHtml(official.branch_label)}`);
    if (official.post_code) extraInfo.push(`<strong>${t('rd-field-postcode')}:</strong> ${escapeHtml(official.post_code)}`);

    let modal = document.getElementById('rd-sync-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'rd-sync-modal';
        modal.className = 'rd-modal-mask';
        document.body.appendChild(modal);
    }

    if (rows.length === 0) {
        modal.innerHTML = `
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t('rd-modal-title'))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    <div class="rd-modal-no-diff">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12l5 5 9-9"/></svg>
                        ${escapeHtml(t('rd-modal-no-diff'))}
                    </div>
                    ${extraInfo.length ? `<div class="rd-modal-extra">${extraInfo.join(' · ')}</div>` : ''}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-close>${escapeHtml(t('rd-modal-cancel'))}</button>
                </div>
            </div>
        `;
    } else {
        const rowsHtml = rows.map((row, i) => `
            <label class="rd-diff-row">
                <input type="checkbox" data-rd-apply data-field="${row.field}" data-value="${escapeHtml(row.official)}" checked>
                <div class="rd-diff-label">${escapeHtml(row.label)}</div>
                <div class="rd-diff-col rd-diff-current">
                    <div class="rd-diff-col-label">${escapeHtml(t('rd-modal-current'))}</div>
                    <div class="rd-diff-val">${escapeHtml(row.current || '—')}</div>
                </div>
                <div class="rd-diff-arrow">→</div>
                <div class="rd-diff-col rd-diff-official">
                    <div class="rd-diff-col-label">${escapeHtml(t('rd-modal-official'))}</div>
                    <div class="rd-diff-val">${escapeHtml(row.official)}</div>
                </div>
            </label>
        `).join('');
        modal.innerHTML = `
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t('rd-modal-title'))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    ${rowsHtml}
                    ${extraInfo.length ? `<div class="rd-modal-extra">${extraInfo.join(' · ')}</div>` : ''}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t('rd-modal-cancel'))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t('rd-modal-apply'))}</button>
                </div>
            </div>
        `;
    }

    modal.classList.add('show');

    const closeModal = () => modal.classList.remove('show');
    modal.querySelector('.rd-modal-close').addEventListener('click', closeModal);
    modal.querySelectorAll('[data-rd-modal-close]').forEach(b => b.addEventListener('click', closeModal));
    modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });

    const applyBtn = modal.querySelector('[data-rd-modal-apply]');
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            const r = _results[_drawerIdx];
            if (!r) { closeModal(); return; }
            modal.querySelectorAll('[data-rd-apply]:checked').forEach(cb => {
                const field = cb.dataset.field;
                const value = cb.dataset.value;
                r.edits[field] = value;
                r.merged_fields[field] = value;
                const input = document.querySelector(`[data-field="${field}"]`);
                if (input) input.value = value;
                const wrap = document.querySelector(`[data-field-wrap="${field}"]`);
                if (wrap) wrap.classList.add('edited');
            });
            updateDrawerEditCount();
            renderResults();
            closeModal();
        });
    }
}


function onFieldEdit(e) {
    const key = e.target.dataset.field;
    const val = e.target.value;
    const r = _results[_drawerIdx];
    const original = r.merged_fields[key];
    if (val === (original ?? '')) delete r.edits[key];
    else {
        r.edits[key] = val;
        r.merged_fields[key] = val;
    }
    const wrap = document.querySelector(`[data-field-wrap="${key}"]`);
    if (wrap) wrap.classList.toggle('edited', r.edits[key] !== undefined);
    updateDrawerEditCount();
    renderResults();
}

function updateDrawerEditCount() {
    const r = _results[_drawerIdx];
    const n = r ? Object.keys(r.edits).length : 0;
    const el = document.getElementById('drawer-edit-count-sub');
    if (el) el.textContent = n > 0 ? t('drawer-edit-count', { n }) : '';
}

// 识别页抽屉打开时也注入「推 ERP」按钮 · v105.2 · 改放抽屉头部 · 不再遮内容明细
//
// v118.34.34 (Zihao 2026-05-19 拍板 · 批 2 改动 4) · 推送按钮动态显示:
//   0 个启用 endpoint → 按钮整个不渲染(没必要 tease 用户)
//   1 个启用 endpoint → 按钮 label = "推送到 {name}" · 单击直推
//   ≥2 个启用 endpoint → 按钮 label = "推送到 ERP ▾" · 单击展开 endpoint 选择 popover
//
// 注意:_erpEndpoints 不包含 Xero · Xero 有独立按钮 (btn-xero-push)
// 由 erp-xero IIFE 单独注入 · 我们这里只管 webhook / mrerp / flowaccount 系列.
function injectOcrPushButton() {
    const r = _results[_drawerIdx];
    if (!r || r._historyMode) return;
    if (!_userInfo || !_userInfo.can_push_erp) return;
    if (!r._historyId && !r.history_id) return;
    const historyId = r._historyId || r.history_id;

    const header = document.querySelector('.drawer-header');
    if (!header || document.getElementById('drawer-ocr-push-btn')) return;

    // v118.34.34 · 只展示 enabled 的 endpoint · _erpEndpoints 是全局缓存.
    const enabledEps = (window._erpEndpoints || _erpEndpoints || []).filter(function (ep) {
        return ep && ep.enabled !== false;
    });

    // 0 enabled → 不渲染按钮. 用户去 ERP 对接 tab 先连一个再说.
    if (enabledEps.length === 0) return;

    // 创建按钮 · 插在诊断按钮之前(诊断 / 关闭按钮已在 header 末尾)
    const btn = document.createElement('button');
    btn.id = 'drawer-ocr-push-btn';
    btn.className = 'drawer-push-btn';

    // Button label / behavior depends on enabled-endpoint count.
    let label;
    if (enabledEps.length === 1) {
        // Single endpoint · 直接显示推到那个 endpoint 的 name.
        const epName = enabledEps[0].name || enabledEps[0].adapter || 'ERP';
        label = t('btn-push-to-name', { name: epName });
        btn.title = label;
    } else {
        // ≥2 endpoints · 通用 label + 下拉箭头.
        label = t('btn-push-erp') + ' ▾';
        btn.title = t('btn-push-erp-pick-tip');
    }
    btn.innerHTML = `
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(label)}</span>
    `;

    btn.addEventListener('click', function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        if (enabledEps.length === 1) {
            // 单 endpoint · 直推 · 后端按 default 选(只有 1 个 enabled 就是它).
            pushOcrToErp(historyId, enabledEps[0].id);
        } else {
            // 多 endpoint · 打开 picker popover.
            openOcrPushPicker(btn, historyId, enabledEps);
        }
    });

    // 插在第一个 drawer-diagnose 之前
    const diagnose = header.querySelector('.drawer-diagnose');
    if (diagnose) {
        header.insertBefore(btn, diagnose);
    } else {
        header.appendChild(btn);
    }
}

// v118.34.34 · 多 endpoint picker · 简单 popover · 复用 history-popover CSS.
function openOcrPushPicker(anchor, historyId, enabledEps) {
    // 先关掉已有 popover
    document.querySelectorAll('.drawer-push-picker').forEach(n => n.remove());

    const rect = anchor.getBoundingClientRect();
    const pop = document.createElement('div');
    pop.className = 'drawer-push-picker history-popover';
    pop.style.position = 'fixed';
    pop.style.top = (rect.bottom + 6) + 'px';
    pop.style.left = Math.max(8, rect.right - 240) + 'px';
    pop.style.minWidth = '220px';
    pop.style.zIndex = '12000';

    const rows = enabledEps.map(function (ep) {
        const name = escapeHtml(ep.name || ep.adapter || 'ERP');
        const adapter = escapeHtml((ep.adapter || '').toLowerCase());
        const isDef = ep.is_default;
        const defBadge = isDef
            ? '<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">' + escapeHtml(t('ep-default')) + '</span>'
            : '';
        return '<button type="button" data-ep-id="' + escapeHtml(ep.id) + '" '
            + 'style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;">'
            + '<span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">' + adapter + '</span>' + name + defBadge + '</span>'
            + '</button>';
    }).join('');
    pop.innerHTML = rows;
    document.body.appendChild(pop);

    const closePop = () => {
        pop.remove();
        document.removeEventListener('click', onDoc, true);
    };
    const onDoc = (e) => {
        if (!pop.contains(e.target) && e.target !== anchor && !anchor.contains(e.target)) closePop();
    };
    setTimeout(() => document.addEventListener('click', onDoc, true), 0);

    pop.addEventListener('click', (e) => {
        const b = e.target.closest('[data-ep-id]');
        if (!b) return;
        const epId = b.getAttribute('data-ep-id');
        closePop();
        pushOcrToErp(historyId, epId);
    });
}

async function pushOcrToErp(historyId, endpointId) {
    const btn = document.getElementById('drawer-ocr-push-btn');
    if (btn) btn.disabled = true;
    try {
        const body = { history_id: historyId };
        if (endpointId) body.endpoint_id = endpointId;
        const resp = await fetch('/api/erp/push', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (!resp.ok) {
            const code = (data && data.detail) ? data.detail : 'err.unknown';
            if (code === 'erp.no_default_endpoint') {
                showToast(t('erp-push-no-endpoint'), 'warn');
            } else if (code === 'erp.endpoint_disabled') {
                // v118.34.34 · endpoint 在 click 和 push 之间被另一个 tab 停用了 ·
                // 提示用户去 ERP 对接 tab 启用 + 刷新 endpoints 缓存.
                showToast(t('erp-push-disabled-tip') || t('card-disabled-tip') || 'Endpoint disabled', 'warn');
                if (typeof window._refreshErpEndpointsCache === 'function') {
                    window._refreshErpEndpointsCache();
                }
            } else {
                showToast(t('erp-push-fail', { err: code }), 'fail');
            }
            return;
        }
        if (data.ok) {
            showToast(t('erp-push-ok', { name: data.endpoint_name || '' }));
        } else {
            showToast(t('erp-push-fail', { err: data.error_msg || 'unknown' }), 'fail');
        }
    } catch (e) {
        showToast(t('erp-push-fail', { err: e.message }), 'fail');
    } finally {
        if (btn) btn.disabled = false;
    }
}

function closeDrawer() {
    document.getElementById('drawer-mask').classList.remove('show');
    document.getElementById('drawer').classList.remove('show');
    // 清理抽屉底部的按钮栏(下次打开会重新注入)
    const existingHistoryBar = document.getElementById('drawer-history-save');
    if (existingHistoryBar) existingHistoryBar.remove();
    const existingOcrBar = document.getElementById('drawer-ocr-push');
    if (existingOcrBar) existingOcrBar.remove();
    // v105.2 · 清掉头部推送按钮
    const headerPushBtn = document.getElementById('drawer-ocr-push-btn');
    if (headerPushBtn) headerPushBtn.remove();
    _drawerIdx = -1;
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

document.getElementById('drawer-close').addEventListener('click', closeDrawer);
document.getElementById('drawer-mask').addEventListener('click', closeDrawer);
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

// ============================================================
// Excel 导出 · v118.27.6 · 4 模板统一(跟单据记录批量导出对齐 · 砍 ERP 录入格式)
// ============================================================
const _EXPORT_TEMPLATES = [
    { id: 'input_vat',       nameKey: 'tpl-input-vat',           descKey: 'tpl-input-vat-desc',       badge: 'recommended' },
    { id: 'standard',        nameKey: 'tpl-standard',            descKey: 'tpl-standard-desc' },
    { id: 'sales_detail_th', nameKey: 'export-tpl-sales-detail', descKey: 'export-tpl-sales-detail-desc', badge: 'new' },
    { id: 'print',           nameKey: 'tpl-print',               descKey: 'tpl-print-desc' },
];
function _getCurrentExportTpl() {
    try {
        const v = localStorage.getItem('pn_export_tpl') || 'input_vat';
        // 兼容旧值:erp 已砍 · 老用户存了 erp 的回退到 input_vat
        if (v === 'erp') return 'input_vat';
        return v;
    } catch (e) { return 'input_vat'; }
}
function _setCurrentExportTpl(id) {
    try { localStorage.setItem('pn_export_tpl', id || 'input_vat'); } catch (e) {}
}
function _getTplDef(id) {
    return _EXPORT_TEMPLATES.find(x => x.id === id) || _EXPORT_TEMPLATES[0];
}

async function _runExport(templateId) {
    if (_results.length === 0) return;
    templateId = templateId || 'input_vat';

    const btn = document.getElementById('btn-export');
    if (btn) { btn.disabled = true; btn.classList.add('loading'); }

    try {
        let resp;
        let defaultName = `pearnly-export-${Date.now()}.xlsx`;

        if (templateId === 'sales_detail_th') {
            // v118.27.6 · 泰国销售明细走 /api/ocr/export(我自己的模板系统)
            // v118.27.5.1 · 多发票拆分修复 · 一个文件含多张发票时 · 拆 N 行 · 不再合并丢字段
            const flatRecords = [];
            for (const r of _results) {
                const invs = (r.invoices && r.invoices.length > 0) ? r.invoices : null;
                if (invs && invs.length > 1) {
                    for (let i = 0; i < invs.length; i++) {
                        const inv = invs[i] || {};
                        flatRecords.push({
                            filename: r.filename + ' #' + (i + 1) + '/' + invs.length,
                            engine: r.engine,
                            merged_fields: inv.fields || {},
                        });
                    }
                } else {
                    flatRecords.push({
                        filename: r.filename,
                        engine: r.engine,
                        merged_fields: r.merged_fields,
                    });
                }
            }
            resp = await apiPost('/api/ocr/export', {
                records: flatRecords,
                lang: currentLang,
                template: 'sales_detail_th',
            });
        } else {
            // input_vat / standard / print → /api/reports/history/batch_export(老接口 · reports_router)
            // 用 _results 里的 history_ids(OCR 完已自动入库)
            const historyIds = [];
            for (const r of _results) {
                if (r.history_ids && Array.isArray(r.history_ids)) {
                    historyIds.push(...r.history_ids);
                } else if (r.history_id) {
                    historyIds.push(r.history_id);
                }
            }
            if (historyIds.length === 0) {
                showToast(t('toast-export-error'), 'error');
                return;
            }
            const tok = localStorage.getItem('mrpilot_token');
            resp = await fetch('/api/reports/history/batch_export', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + tok,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    template: templateId,
                    lang: currentLang,
                    history_ids: historyIds,
                    client_id: null,
                }),
            });
            defaultName = `pearnly-${templateId}-${Date.now()}.xlsx`;
        }

        if (!resp) return;
        if (!resp.ok) {
            let detail = 'HTTP ' + resp.status;
            try {
                const err = await resp.json();
                if (err && err.detail) detail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
            } catch (e) { console.warn('[export] resp.json err.detail parse failed:', e); }
            const key = typeof detail === 'string' && detail.indexOf('.') > 0 ? 'err.' + detail : null;
            showToast(key ? t(key) : (t('toast-export-error') + ' · ' + detail), 'error');
            return;
        }
        const blob = await resp.blob();
        // 优先从 Content-Disposition / X-Filename 读
        let filename = defaultName;
        const xfn = resp.headers.get('X-Filename');
        if (xfn) filename = xfn;
        else {
            const cd = resp.headers.get('Content-Disposition') || '';
            const m1 = cd.match(/filename\*=UTF-8''([^;]+)/i);
            if (m1) {
                try { filename = decodeURIComponent(m1[1]); } catch (_) { /* silent · RFC 5987 decode · 用默认 filename */ }
            }
        }
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(t('toast-export-success'), 'success');
    } catch (e) {
        console.error(e);
        showToast(t('toast-export-error'), 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.classList.remove('loading'); }
    }
}

document.getElementById('btn-export').addEventListener('click', () => {
    _runExport(_getCurrentExportTpl());
});

// ─── 模板下拉 ──────────────────
function _renderExportDropdown() {
    const wrap = document.getElementById('export-split-wrap');
    if (!wrap) return;
    let dd = document.getElementById('export-dropdown');
    if (dd) { dd.remove(); return; }
    dd = document.createElement('div');
    dd.id = 'export-dropdown';
    dd.className = 'export-dropdown';
    const cur = _getCurrentExportTpl();
    const items = _EXPORT_TEMPLATES.map(tpl => {
        const badgeHtml =
            tpl.badge === 'recommended' ? `<span class="export-dd-badge badge-rec">${escapeHtml(t('report-recommended'))}</span>` :
            tpl.badge === 'new' ? `<span class="export-dd-badge badge-new">${escapeHtml(t('tpl-badge-new'))}</span>` :
            '';
        return `
            <div class="export-dd-item ${tpl.id === cur ? 'active' : ''}" data-tpl="${tpl.id}">
                <div class="export-dd-row">
                    <span class="export-dd-name">${escapeHtml(t(tpl.nameKey))}</span>
                    ${badgeHtml}
                    ${tpl.id === cur ? '<span class="export-dd-check">✓</span>' : ''}
                </div>
                <div class="export-dd-desc">${escapeHtml(t(tpl.descKey))}</div>
            </div>
        `;
    }).join('');
    // v118.27.6 · 自定义模板入口收下拉底部 · disabled 标"即将"
    const customRow = `
        <div class="export-dd-divider"></div>
        <div class="export-dd-item export-dd-custom" data-tpl="__custom" title="${escapeHtml(t('tpl-custom-coming'))}">
            <div class="export-dd-row">
                <span class="export-dd-name">+ ${escapeHtml(t('tpl-custom-new'))}</span>
                <span class="export-dd-badge badge-soon">${escapeHtml(t('cs-coming-soon'))}</span>
            </div>
        </div>
    `;
    dd.innerHTML = items + customRow;
    wrap.appendChild(dd);
}
function _closeExportDropdown() {
    const dd = document.getElementById('export-dropdown');
    if (dd) dd.remove();
}
const _btnExpArrow = document.getElementById('btn-export-arrow');
if (_btnExpArrow) {
    _btnExpArrow.addEventListener('click', (e) => {
        e.stopPropagation();
        if (_btnExpArrow.disabled) return;
        _renderExportDropdown();
    });
}
document.addEventListener('click', (e) => {
    const item = e.target.closest('.export-dd-item');
    if (item) {
        const tplId = item.getAttribute('data-tpl');
        // v118.27.6 · 自定义模板入口 · 暂未开放 · toast 「即将上线」 · 不切模板不导出
        if (tplId === '__custom') {
            _closeExportDropdown();
            showToast(t('cs-coming-soon'), 'info');
            return;
        }
        _setCurrentExportTpl(tplId);
        _closeExportDropdown();
        _runExport(tplId);
        return;
    }
    if (e.target.closest('#btn-export-arrow')) return;
    _closeExportDropdown();
});

// 当 _results 变化时(开始识别 / 清空)同步 disable arrow
function _syncExportArrow() {
    const arrow = document.getElementById('btn-export-arrow');
    const main = document.getElementById('btn-export');
    if (arrow && main) arrow.disabled = main.disabled;
}
// 监听 export 主按钮的 disabled 变化(简单 polling · 兼容老逻辑)
setInterval(_syncExportArrow, 300);

// ============================================================
// 设置页
// ============================================================
function renderSettings() {
    if (!_userInfo) return;

    // v118.1 · 不论超管/普通用户都先加载联系我们 + 首选项(原 v118 放函数末尾 · 超管路径提前 return 跑不到)
    if (typeof window.loadAboutPanel === 'function') window.loadAboutPanel();
    if (typeof window.loadPrefsSettings === 'function') window.loadPrefsSettings();

    const el = document.getElementById('settings-info');
    if (!el) return;
    const u = _userInfo;

    // v85 · 超管不显示订阅/配额/有效期 · 只显示身份标识
    if (u.is_super_admin) {
        el.innerHTML = `
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t('settings-username')}</td><td style="padding:8px 0;">${escapeHtml(u.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t('settings-role')}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t('settings-role-super-admin'))}</strong></td></tr>
            </table>
        `;
        // v118.10.3 · 超管也显示 API Key 卡片(测试 + 管理需要 · 即使本身不走 Gemini)
        const apiKeyCard = document.getElementById('api-key-card');
        if (apiKeyCard) apiKeyCard.style.display = '';
        return;
    }

    // v118.35.0.9 · 所有非超管用户(包括 byo_api · monthly · yearly · lifetime · free)
    // 全部走 credits 计费方式渲染 · DB 已批量迁移到 plan='credits'(v0.9 R6) ·
    // 设置页只显示:用户名 + 计费方式 + 价格说明 · 不再显示订阅类型/配额/有效期表格
    _renderCreditsSettings(u, el);

    // v118.35.0.16 · BYO Gemini Key 已永久下线 · credits 系统接管

    // v87 · API Key 卡片只对买断账号(tenant_type=byo_api)显示
    // 月付(shared_api)共用系统 key · 不能也不需要填
    // v118.10.2 · 超管(Earn)也能看(测试 + 管理需要)
    const apiKeyCard = document.getElementById('api-key-card');
    if (apiKeyCard) {
        const showCard = (tt === 'byo_api') || (_userInfo && _userInfo.is_super_admin);
        apiKeyCard.style.display = showCard ? '' : 'none';
    }
}

// ============================================================
// v118.35.0.9 · credits 计费 · 设置页极简渲染
// 只显示:用户名 + 计费方式 + 价格说明小字
// 余额卡 / 充值按钮搬到首页 KPI 卡 · 这里不再重复
// ============================================================
function _renderCreditsSettings(u, el) {
    // v118.35.0.13 · 3 行: 用户名 + 计费方式 + 价格说明 · keys 跟用户规范命名对齐
    const username = escapeHtml(u.username || u.email || '');
    el.innerHTML = `
        <table style="width:100%; font-size:13px; border-collapse: collapse;">
            <tr>
                <td style="color:#a0aec0; padding:8px 0; width:140px;">${escapeHtml(t('settings-username'))}</td>
                <td style="padding:8px 0;">${username}</td>
            </tr>
            <tr>
                <td style="color:#a0aec0; padding:8px 0;">${escapeHtml(t('settings-billing-mode-title'))}</td>
                <td style="padding:8px 0;"><strong>${escapeHtml(t('settings-billing-mode'))}</strong></td>
            </tr>
            <tr>
                <td colspan="2" style="color:#a0aec0; padding:8px 0; font-size:12px;">
                    ${escapeHtml(t('settings-billing-pricing'))}
                </td>
            </tr>
        </table>
    `;
}


// v118.35.0.16 · BYO Gemini Key 全套(loadGeminiKeyInfo/saveGeminiKey/testGeminiKey/clearGeminiKey + setApiKeyMsg) 物理删除


async function refreshUserInfo() {
    try {
        const resp = await fetch('/api/me', {
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (resp.ok) {
            _userInfo = await resp.json();
            try { window._userInfo = _userInfo; } catch (_) { /* silent · workspace-switcher 读它判 owner */ }
        }
    } catch (e) {}
}

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
// 提示
// ============================================================
function showAlert(type, msg) {
    const box = document.getElementById('alert-' + type);
    if (!box) return;
    document.getElementById('alert-' + type + '-text').textContent = msg;
    box.classList.add('show');
}
function hideAlerts() {
    ['info', 'warn', 'error'].forEach(t => {
        document.getElementById('alert-' + t).classList.remove('show');
    });
}
// [TECH_DEBT §2 P0] 2026-05-15 · 删除 showToast 重复定义(line 13461 旧版)
//   旧版签名 (msg, type) 被 line 14894 新版 (msg, kind, duration) 完全覆盖
//   276 处调用点全部兼容新版(已用脚本核 type 参数:'' / error / info / success 全在新版 kind 白名单)

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

// v83 · 修复刷新 admin 页卡「加载中」:IIFE 里的 loadAdminUsersPage 赋值晚于此处启动
// v109.4 · 老 admin 已删 · 改成 admin-users
// setTimeout 0 让 IIFE 先跑完 · 再补一次特殊页加载
setTimeout(() => {
    if (currentRoute === 'admin-users' && typeof window.loadAdminUsersPage === 'function') {
        window.loadAdminUsersPage();
    }
    // v118.33.10.1 · reconcile 页初始 hash 时 loadReconcilePage 还未注册 · 补一次调用
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

function updateHistoryBatchBar() {
    const bar = document.getElementById('history-batch-bar');
    const countEl = document.getElementById('history-batch-count');
    const checkAll = document.getElementById('history-check-all');
    if (!bar || !countEl) return;

    const n = _historySelected.size;
    if (n > 0) {
        bar.style.display = '';
        countEl.textContent = t('history-batch-count', { n });
    } else {
        bar.style.display = 'none';
    }

    // "全选" checkbox 三态:全选/部分/全不选
    if (checkAll) {
        const items = _historyState.items || [];
        if (items.length === 0) {
            checkAll.checked = false;
            checkAll.indeterminate = false;
        } else {
            const selectedInPage = items.filter(r => _historySelected.has(r.id)).length;
            checkAll.checked = selectedInPage === items.length;
            checkAll.indeterminate = selectedInPage > 0 && selectedInPage < items.length;
        }
    }
}

function clearHistorySelection() {
    _historySelected.clear();
    updateHistoryBatchBar();
}

async function loadHistoryPage() {
    if (!_userInfo) {
        setTimeout(() => loadHistoryPage(), 300);
        return;
    }
    const freeBlock = document.getElementById('history-free-block');
    const main = document.getElementById('history-main');
    const empty = document.getElementById('history-empty');
    if (!freeBlock || !main || !empty) {
        console.warn('[History] container missing');
        return;
    }

    if (!_userInfo.can_view_history) {
        freeBlock.style.display = '';
        main.style.display = 'none';
        empty.style.display = 'none';
        return;
    }
    freeBlock.style.display = 'none';

    _historyState.loading = true;
    try {
        const offset = _historyState.page * _historyState.pageSize;
        const params = new URLSearchParams({
            limit: _historyState.pageSize,
            offset: offset,
        });
        if (_historyState.keyword) params.set('keyword', _historyState.keyword);
        // v118.28.0 · 顶栏客户切换器过滤(唯一来源 · 14b.3 后删除了重复 UI)
        const cid = (typeof window.getCurrentClientId === 'function') ? window.getCurrentClientId() : null;
        if (cid) params.set('client_id', String(cid));
        const resp = await fetch(`/api/history?${params}`, {
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (resp.status === 401) {
            localStorage.removeItem('mrpilot_token');
            const _bd = await resp.json().catch(() => ({}));
            const _dc = typeof _bd.detail === 'string' ? _bd.detail : ((_bd.detail && _bd.detail.code) || '');
            if (_dc === 'auth.session_revoked') { _showSessionRevokedModal(); return; }
            window.location.href = '/';
            return;
        }
        const data = await resp.json();
        _historyState.items = data.items || [];
        _historyState.total = data.total || 0;
        // 拉到新一页后 · 只保留当前页里仍然存在的那些选中项
        const currentIds = new Set(_historyState.items.map(r => r.id));
        for (const id of Array.from(_historySelected)) {
            if (!currentIds.has(id)) _historySelected.delete(id);
        }
        renderHistoryList();
    } catch (e) {
        console.error('load history failed', e);
    } finally {
        _historyState.loading = false;
    }
}

function renderHistoryList() {
    const main = document.getElementById('history-main');
    const empty = document.getElementById('history-empty');
    const items = _historyState.items;

    // v0.11 · 更新匹配计数
    const matchesEl = document.getElementById('history-search-matches');
    if (matchesEl) {
        matchesEl.textContent = _historyState.keyword
            ? t('search-matches', { n: _historyState.total })
            : '';
    }

    if (items.length === 0 && _historyState.total === 0 && !_historyState.keyword) {
        main.style.display = 'none';
        empty.style.display = '';
        return;
    }
    main.style.display = '';
    empty.style.display = 'none';

    // 头部统计
    let highCount = 0;
    items.forEach(r => { if (r.confidence === 'high') highCount++; });
    const avgConfPct = items.length > 0 ? Math.round((highCount / items.length) * 100) : 0;

    document.getElementById('history-stats').innerHTML = `
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t('history-total', { n: _historyState.total }))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t('history-avg-conf', { p: avgConfPct }))}</span>
        </div>
    `;

    // 列表
    const tbody = document.getElementById('history-tbody');
    if (items.length === 0) {
        tbody.innerHTML = `<div class="history-row-empty">${escapeHtml(t('history-empty-title'))}</div>`;
    } else {
        tbody.innerHTML = items.map(r => {
            const dt = new Date(r.created_at);
            const mm = String(dt.getMonth() + 1).padStart(2, '0');
            const dd = String(dt.getDate()).padStart(2, '0');
            const hh = String(dt.getHours()).padStart(2, '0');
            const mi = String(dt.getMinutes()).padStart(2, '0');
            const dateStr = `${mm}-${dd} ${hh}:${mi}`;

            const origName = escapeHtml(r.filename || '');
            const shortOrig = origName.length > 50 ? origName.substring(0, 50) + '…' : origName;
            // v89 · 主标题:发票号优先(会计最关心的业务标识)· 否则原文件名截断
            //       归档名(archive_name)不在列表显示 · 只用于 ZIP 导出文件名
            const mainName = r.invoice_no ? escapeHtml(r.invoice_no) : shortOrig;
            const subtitleParts = [];
            if (r.seller_name) subtitleParts.push(escapeHtml(r.seller_name));
            // 如果主标题是发票号 · 副标题补上原文件名(截短版)· 方便用户仍能按文件名找
            if (r.invoice_no && r.filename) subtitleParts.push(shortOrig);
            const subtitle = subtitleParts.join(' · ') || '-';

            const categoryBadge = r.category_tag
                ? `<span class="history-badge category">${escapeHtml(r.category_tag)}</span>`
                : '';

            // v0.11 · 多发票拆分角标(同一个 PDF 拆成 N 张时显示 "2/3")
            const multiBadge = (r.source_total && r.source_total > 1)
                ? `<span class="history-badge multi">${escapeHtml(t('invoice-part-of', { i: r.source_index || 1, n: r.source_total }))}</span>`
                : '';

            const amount = r.total_amount !== null && r.total_amount !== undefined
                ? Number(r.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                : `<span class="history-cell-amount-empty">—</span>`;

            // v102 · 统一未识别指示 · 扫描关键字段缺失
            const missingFields = [];
            if (r.total_amount === null || r.total_amount === undefined) missingFields.push(t('field-amount'));
            if (!r.invoice_no) missingFields.push(t('field-invoice-no'));
            if (!r.invoice_date) missingFields.push(t('field-invoice-date'));
            if (!r.seller_name) missingFields.push(t('field-seller-name'));
            const reviewBadge = missingFields.length > 0
                ? `<span class="history-needs-review" data-review="${escapeHtml(r.id)}" title="${escapeHtml(t('history-needs-review-tip') + ' · ' + missingFields.join(' · '))}" role="button" aria-label="${escapeHtml(t('history-needs-review-tip'))}">${svgIcon('alert', 14)}</span>`
                : '';

            const editedBadge = r.edited
                ? `<span class="history-badge edited">${escapeHtml(t('history-edited', { n: r.edit_count || 1 }))}</span>`
                : '';

            const smartBadge = r.smart_assigned_flag
                ? `<span class="history-badge smart-assigned" title="${escapeHtml(t('history-smart-assigned'))}">${svgIcon('sparkle', 11)}</span>`
                : '';

            const confClass = r.confidence === 'high' ? 'high' : (r.confidence === 'medium' ? 'mid' : 'low');
            const confLabel = r.confidence === 'high' ? t('conf-high') : (r.confidence === 'medium' ? t('conf-medium') : t('conf-low'));
            const confBadge = `<span class="history-badge conf-${confClass}">${escapeHtml(confLabel)}</span>`;

            // v95 · 来源标签 · 邮件抓取 / 文件夹监听 / API 显示 SVG · 默认 manual 不显示
            let sourceBadge = '';
            const src = r.source || 'manual';
            if (src === 'email') {
                sourceBadge = `<span class="history-badge source source-email" title="${escapeHtml(t('history-source-email'))}">${svgIcon('mail', 11)}<span>${escapeHtml(t('history-source-email'))}</span></span>`;
            } else if (src === 'folder') {
                sourceBadge = `<span class="history-badge source source-folder" title="${escapeHtml(t('history-source-folder'))}">${svgIcon('folder', 11)}<span>${escapeHtml(t('history-source-folder'))}</span></span>`;
            } else if (src === 'api') {
                sourceBadge = `<span class="history-badge source source-api" title="${escapeHtml(t('history-source-api'))}">${svgIcon('api', 11)}<span>${escapeHtml(t('history-source-api'))}</span></span>`;
            }

            return `
                <div class="history-row" data-hid="${escapeHtml(r.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(r.id)}" ${_historySelected.has(r.id) ? 'checked' : ''} aria-label="select">
                    </div>
                    <div class="history-cell-date">${dateStr}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${mainName} ${categoryBadge} ${multiBadge} ${sourceBadge} ${smartBadge}</div>
                        <div class="history-cell-subtitle">${subtitle}</div>
                    </div>
                    <div class="history-cell-amount">${amount}</div>
                    <div class="history-cell-conf">${confBadge}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(r.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    // v0.16 · 渲染后同步选择状态(含批量工具栏、"全选"checkbox 的三态)
    updateHistoryBatchBar();

    // 分页信息
    const from = items.length > 0 ? _historyState.page * _historyState.pageSize + 1 : 0;
    const to = _historyState.page * _historyState.pageSize + items.length;
    document.getElementById('history-pager-info').textContent =
        t('history-pager', { from, to, total: _historyState.total });

    // 分页按钮
    document.getElementById('history-prev').disabled = _historyState.page === 0;
    document.getElementById('history-next').disabled =
        (_historyState.page + 1) * _historyState.pageSize >= _historyState.total;
}

// 点击行 → 打开抽屉查看/编辑
async function openHistoryDrawer(historyId) {
    try {
        const resp = await fetch(`/api/history/${encodeURIComponent(historyId)}`, {
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (!resp.ok) return;
        const detail = await resp.json();

        // 构造与识别页一致的 result 对象,复用同一个抽屉
        const merged = mergeFields(detail.pages || []);
        const fakeResult = {
            filename: detail.filename,
            pages: detail.pages,
            page_count: detail.page_count,
            elapsed_ms: detail.elapsed_ms,
            engine: 'history',
            merged_fields: merged,
            edits: {},
            confidence: detail.confidence,
            archive_name: detail.archive_name || null,
            category_tag: detail.category_tag || null,
            _historyId: detail.id,
            _historyMode: true,
            client_id: detail.client_id || null,    // v107 · 客户归属
        };
        // 推入 _results 末尾,打开抽屉后记下索引便于保存
        _results.push(fakeResult);
        _drawerIdx = _results.length - 1;
        openDrawer(_drawerIdx);

        // 额外加一个「保存修改」按钮(覆盖到抽屉底部)
        injectHistorySaveButton();

        // v107 · 绑定客户下拉(从 detail 拿当前 client_id)
        if (typeof window.bindDrawerClient === 'function') {
            window.bindDrawerClient(detail.id, detail.client_id || null);
        }

        // P0-2: 异步检查是否已推送过(不阻塞抽屉渲染)
        _checkDrawerPushStatus(detail.id);
    } catch (e) {
        console.error('open history detail failed', e);
    }
}

// v91 · 从「缺金额 · 补金额」按钮进入 · 自动聚焦金额输入框 · 会计直接敲数字保存
async function openHistoryDrawerAndFocusAmount(historyId) {
    await openHistoryDrawer(historyId);
    // 下一帧 focus · 确保 drawer DOM 已渲染 + transition 已起步
    requestAnimationFrame(() => {
        const inp = document.querySelector('[data-field="total_amount"]');
        if (!inp) return;
        try { inp.focus(); } catch (e) {}
        try { inp.select(); } catch (e) {}
        try { inp.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) {}
    });
}

function injectHistorySaveButton() {
    const body = document.getElementById('drawer-body');
    if (!body || document.getElementById('drawer-history-save')) return;
    const saveBar = document.createElement('div');
    saveBar.id = 'drawer-history-save';
    saveBar.className = 'drawer-history-save-bar';
    saveBar.innerHTML = `
        <button class="btn btn-ghost" id="btn-push-erp" title="${escapeHtml(t('btn-push-erp'))}" style="display:none;">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 8h9M8 5l3 3-3 3"/>
                <rect x="11" y="3" width="3" height="10" rx="1"/>
            </svg>
            <span>${escapeHtml(t('btn-push-erp'))}</span>
        </button>
        <span id="drawer-erp-pushed-badge" style="display:none;align-items:center;gap:4px;font-size:12px;font-weight:600;color:#059669;background:#D1FAE5;padding:3px 8px;border-radius:20px;white-space:nowrap;">
            <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:10px;height:10px;flex-shrink:0;"><path d="M2 6l3 3 5-5"/></svg>
            ${escapeHtml(t('erp-pushed-badge'))}
        </span>
        <div style="flex:1"></div>
        <button class="btn btn-primary" id="btn-save-history">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3 3 7-7"/></svg>
            <span>${escapeHtml(t('history-save'))}</span>
        </button>
    `;
    body.appendChild(saveBar);
    document.getElementById('btn-save-history').addEventListener('click', saveHistoryEdits);
    document.getElementById('btn-push-erp').addEventListener('click', pushHistoryToErp);
}

// P0-2: 检查该发票是否已成功推送过 ERP
async function _checkDrawerPushStatus(historyId) { /* stub */ }

async function pushHistoryToErp() {
    showToast(t('erp-push-coming-soon') || 'ERP 推送即将开放，敬请期待', 'info');
}

async function saveHistoryEdits() {
    const r = _results[_drawerIdx];
    if (!r || !r._historyId) return;
    // 把 edits 回填到 pages 的第一页 fields(简化:只改第一页主字段,展示层)
    const newPages = JSON.parse(JSON.stringify(r.pages || []));
    if (newPages.length > 0) {
        const firstMainIdx = newPages.findIndex(p => !p.is_duplicate && !p.is_copy);
        const idx = firstMainIdx >= 0 ? firstMainIdx : 0;
        const f = newPages[idx].fields || (newPages[idx].fields = {});
        // v0.17 · M2 · category_tag 是前端字段名 · 后端 db 用 fields.category · 兼容映射
        const editsForFields = { ...r.edits };
        if (editsForFields.category_tag !== undefined) {
            editsForFields.category = editsForFields.category_tag;
            delete editsForFields.category_tag;
        }
        Object.assign(f, editsForFields);
    }

    const btn = document.getElementById('btn-save-history');
    if (btn) btn.disabled = true;
    try {
        const resp = await fetch(`/api/history/${encodeURIComponent(r._historyId)}`, {
            method: 'PUT',
            headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify({ pages: newPages }),
        });
        if (!resp.ok) throw new Error('save failed');
        showAlert('info', t('history-save-ok'));
        setTimeout(hideAlerts, 1500);
        closeDrawer();
        // 从 _results 移除临时追加的那条
        if (r._historyMode) _results.pop();
        // 刷列表
        loadHistoryPage();
    } catch (e) {
        showAlert('error', t('history-save-fail'));
        if (btn) btn.disabled = false;
    }
}

// 「...」菜单(简单版:直接 confirm 对话框流程)
function openHistoryMenu(historyId, anchor) {
    // 先关掉已有的 menu
    document.querySelectorAll('.history-popover').forEach(n => n.remove());
    const rect = anchor.getBoundingClientRect();
    // v0.16 · 从行数据里取发票号 · 决定"复制发票号"是否可用
    const rec = (_historyState.items || []).find(r => r.id === historyId);
    const invNo = rec && rec.invoice_no ? String(rec.invoice_no) : '';
    // v114 · 是否有 PDF 留底 · 决定「下载 PDF」是否启用
    const hasPdf = rec && rec.has_pdf === true;

    const menu = document.createElement('div');
    menu.className = 'history-popover';
    menu.innerHTML = `
        <button data-act="copy-invno" ${invNo ? '' : 'disabled'}>${escapeHtml(t('history-menu-copy-invno'))}</button>
        <button data-act="download-pdf" ${hasPdf ? '' : 'disabled'}>${escapeHtml(t('history-menu-download-pdf'))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t('history-menu-delete'))}</button>
    `;
    menu.style.top = (rect.bottom + 4) + 'px';
    menu.style.left = (rect.right - 160) + 'px';
    document.body.appendChild(menu);

    const closeMenu = () => { menu.remove(); document.removeEventListener('click', onDocClick, true); };
    const onDocClick = (e) => {
        if (!menu.contains(e.target) && e.target !== anchor) closeMenu();
    };
    setTimeout(() => document.addEventListener('click', onDocClick, true), 0);

    menu.addEventListener('click', async (e) => {
        const btn = e.target.closest('[data-act]');
        if (!btn || btn.disabled) return;
        const act = btn.dataset.act;
        closeMenu();
        if (act === 'copy-invno') {
            if (!invNo) return;
            try {
                await navigator.clipboard.writeText(invNo);
                showToast(t('history-copy-invno-ok', { no: invNo }), 'success');
            } catch (err) {
                // clipboard API 被禁或 http 环境 · 降级 · textarea + execCommand
                try {
                    const ta = document.createElement('textarea');
                    ta.value = invNo;
                    ta.style.position = 'fixed'; ta.style.opacity = '0';
                    document.body.appendChild(ta); ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    showToast(t('history-copy-invno-ok', { no: invNo }), 'success');
                } catch (e2) {
                    showToast(t('history-copy-invno-fail'), 'error');
                }
            }
        } else if (act === 'download-pdf') {
            // v114 · 下载 PDF 留底
            // v115 · 加 loading toast(因为大文件可能要 30s+ · 用户需要立即反馈)
            const dismissLoading = showToast(t('history-download-pdf-loading'), 'loading', 0);
            try {
                const resp = await fetch(`/api/history/${encodeURIComponent(historyId)}/pdf`, {
                    headers: { 'Authorization': 'Bearer ' + token },
                });
                if (!resp.ok) throw new Error('download failed');
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = (rec && rec.filename) ? (rec.filename.endsWith('.pdf') ? rec.filename : rec.filename + '.pdf') : 'invoice.pdf';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(url), 5000);
                dismissLoading();
                showToast(t('history-download-pdf-ok'), 'success');
            } catch (err) {
                dismissLoading();
                showToast(t('history-download-pdf-fail'), 'error');
            }
        } else if (act === 'delete') {
            const ok = await showConfirm(t('history-confirm-delete'), { danger: true });
            if (!ok) return;
            try {
                const resp = await fetch(`/api/history/${encodeURIComponent(historyId)}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': 'Bearer ' + token },
                });
                if (!resp.ok) throw new Error();
                showAlert('info', t('history-delete-ok'));
                setTimeout(hideAlerts, 1500);
                loadHistoryPage();
            } catch {
                showAlert('error', t('history-delete-fail'));
            }
        }
    });
}

// 事件绑定
(function initHistoryPage() {
    document.addEventListener('click', (e) => {
        const row = e.target.closest('.history-row');
        const menuBtn = e.target.closest('[data-hmenu]');
        if (menuBtn) {
            e.stopPropagation();
            openHistoryMenu(menuBtn.dataset.hmenu, menuBtn);
            return;
        }
        // v102 · 点统一「需复核」⚠ 直接打开抽屉(原 fill-amount 改名为 review)
        const reviewBtn = e.target.closest('[data-review]');
        if (reviewBtn) {
            e.stopPropagation();
            openHistoryDrawer(reviewBtn.dataset.review);
            return;
        }
        // v91 · 旧「补金额」入口 · v102 已统一到 review · 兼容旧标签保留
        const fillBtn = e.target.closest('[data-fill-amount]');
        if (fillBtn) {
            e.stopPropagation();
            openHistoryDrawerAndFocusAmount(fillBtn.dataset.fillAmount);
            return;
        }
        // v0.16 · 点 checkbox 不触发抽屉
        if (e.target.closest('.history-row-check') || e.target.closest('.history-cell-check')) {
            return;
        }
        if (row && !e.target.closest('[data-hmenu]')) {
            openHistoryDrawer(row.dataset.hid);
        }
    });

    // v0.16 · 单行 checkbox 勾选(用 change 更稳 · 委托到 tbody)
    const tbody = document.getElementById('history-tbody');
    if (tbody) {
        tbody.addEventListener('change', (e) => {
            const cb = e.target.closest('.history-row-check');
            if (!cb) return;
            const hid = cb.dataset.hid;
            if (cb.checked) _historySelected.add(hid);
            else _historySelected.delete(hid);
            updateHistoryBatchBar();
        });
    }

    // v0.16 · "全选"checkbox · 只作用于当前页
    const checkAll = document.getElementById('history-check-all');
    if (checkAll) {
        checkAll.addEventListener('change', (e) => {
            const on = e.target.checked;
            for (const r of _historyState.items) {
                if (on) _historySelected.add(r.id);
                else _historySelected.delete(r.id);
            }
            // 同步 DOM 里所有复选框
            document.querySelectorAll('.history-row-check').forEach(el => { el.checked = on; });
            updateHistoryBatchBar();
        });
    }

    // v0.16 · 取消选择
    const cancelBtn = document.getElementById('history-batch-cancel');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            clearHistorySelection();
            document.querySelectorAll('.history-row-check').forEach(el => { el.checked = false; });
        });
    }

    // v0.16 · 批量删除
    const batchDelBtn = document.getElementById('history-batch-delete');
    if (batchDelBtn) {
        batchDelBtn.addEventListener('click', async () => {
            const n = _historySelected.size;
            if (n === 0) return;
            const ok = await showConfirm(t('history-batch-confirm', { n }), { danger: true });
            if (!ok) return;
            const ids = Array.from(_historySelected);
            try {
                const resp = await fetch('/api/history/batch-delete', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + token,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ ids }),
                });
                if (!resp.ok) throw new Error('batch delete failed');
                const data = await resp.json();
                showToast(t('history-batch-done', { n: data.deleted || 0 }), 'success');
                clearHistorySelection();
                loadHistoryPage();
            } catch (e) {
                console.error('batch delete', e);
                showToast(t('history-batch-fail'), 'error');
            }
        });
    }

    let searchTimer = null;
    document.getElementById('history-search').addEventListener('input', (e) => {
        const val = e.target.value;
        document.getElementById('history-search-clear').style.display = val ? '' : 'none';
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            _historyState.keyword = val.trim();
            _historyState.page = 0;
            clearHistorySelection();
            loadHistoryPage();
        }, 300);
    });
    document.getElementById('history-search-clear').addEventListener('click', () => {
        const input = document.getElementById('history-search');
        input.value = '';
        _historyState.keyword = '';
        _historyState.page = 0;
        clearHistorySelection();
        document.getElementById('history-search-clear').style.display = 'none';
        loadHistoryPage();
        input.focus();
    });

    document.getElementById('history-range').addEventListener('change', (e) => {
        _historyState.range = parseInt(e.target.value, 10);
        _historyState.page = 0;
        clearHistorySelection();
        loadHistoryPage();
    });

    document.getElementById('history-prev').addEventListener('click', () => {
        if (_historyState.page > 0) {
            _historyState.page--;
            clearHistorySelection();
            loadHistoryPage();
        }
    });
    document.getElementById('history-next').addEventListener('click', () => {
        if ((_historyState.page + 1) * _historyState.pageSize < _historyState.total) {
            _historyState.page++;
            clearHistorySelection();
            loadHistoryPage();
        }
    });
})();


// ============================================================
// v0.6.1 · 自动化页(ERP 端点管理)
// ============================================================
let _erpEndpoints = [];
window._erpEndpoints = _erpEndpoints;
let _epEditingId = null; // 当前编辑中的 endpoint id,null = 新增模式

async function loadAutomationPage() {
    if (!_userInfo) {
        // v0.10.1 · 用户信息还没拿回来,等 300ms 再试一次
        setTimeout(() => loadAutomationPage(), 300);
        return;
    }
    const freeBlock = document.getElementById('automation-free-block');
    const main = document.getElementById('automation-main');
    if (!freeBlock || !main) {
        console.warn('[Automation] container missing');
        return;
    }

    if (!_userInfo.can_push_erp) {
        freeBlock.style.display = '';
        main.style.display = 'none';
        return;
    }
    freeBlock.style.display = 'none';
    main.style.display = '';

    // v0.10 · 默认打开 ERP tab
    switchAutomationTab('erp');

    await loadErpEndpoints();
    loadErpLogs();
}

function switchAutomationTab(tabKey) {
    document.querySelectorAll('.auto-nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.autoTab === tabKey);
    });
    document.querySelectorAll('.auto-panel').forEach(panel => {
        panel.classList.toggle('active', panel.dataset.autoPanel === tabKey);
    });
    // v0.17 · M6 · 邮箱抓取 tab 首次进入时拉数据
    if (tabKey === 'email' && typeof window._loadEmailIngestPanel === 'function') {
        window._loadEmailIngestPanel();
        // v95 · 进入邮箱 tab · 启动 30s 自动刷新日志
        if (typeof window._startEmailLogAutoRefresh === 'function') {
            window._startEmailLogAutoRefresh();
        }
    } else if (typeof window._stopEmailLogAutoRefresh === 'function') {
        // 离开邮箱 tab · 停止自动刷新
        window._stopEmailLogAutoRefresh();
    }
    // v0.18 · M10 · 银行对账 tab 首次进入时拉数据
    if (tabKey === 'bank' && typeof window._loadBankReconPanel === 'function') {
        window._loadBankReconPanel();
    }
    // v0.19 · T1 · LINE Bot tab 首次进入时拉数据
    if (tabKey === 'linebot' && typeof window._loadLineBotPanel === 'function') {
        window._loadLineBotPanel();
    }
    // v118.22.2 · 智能提醒 tab 首次进入时拉数据
    if (tabKey === 'alert' && typeof window._loadNotificationsPanel === 'function') {
        window._loadNotificationsPanel();
    }
    // v95 · 文件夹监听 tab 首次进入时初始化
    if (tabKey === 'folder' && typeof window._loadFolderWatcherPanel === 'function') {
        window._loadFolderWatcherPanel();
    }
}

let _logFilter = { key: 'all', val: '' };
// v118.25.1 · 推送日志多选状态(批量重推)
let _erpSelected = new Set();

async function loadErpLogs(silent) {
    const listEl = document.getElementById('erp-logs-list');
    if (!listEl) return;

    // v0.10 · 立即显示 loading 态 · 让用户知道点到了(silent=自动轮询刷新·不闪 loading)
    if (!silent) listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-loading'))}</div>`;

    // 今日统计同步刷新(不等)
    loadErpTodayStats();

    try {
        const params = new URLSearchParams({ limit: '30' });
        if (_logFilter.key === 'status') params.set('status', _logFilter.val);
        if (_logFilter.key === 'trigger') params.set('trigger', _logFilter.val);
        // 批 3 改动 6 (v118.34.34) · adapter filter chip (mrerp / xero / flowaccount).
        if (_logFilter.key === 'adapter') params.set('adapter', _logFilter.val);
        const resp = await fetch(`/api/erp/logs?${params}`, {
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (!resp.ok) {
            listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
            return;
        }
        const data = await resp.json();
        const items = data.items || [];
        // 有「推送中(pending)」行 → 4s 后静默再拉一次 · 让状态原地翻成 ✓/✗(2026-05-26)·
        // 无 pending 或离开页面(下次 listEl 不在直接 return)即自动停。
        if (window._erpLogPollTimer) { clearTimeout(window._erpLogPollTimer); window._erpLogPollTimer = null; }
        if (items.some(function (l) { return l.status === 'pending'; })) {
            window._erpLogPollTimer = setTimeout(function () { loadErpLogs(true); }, 4000);
        }
        if (items.length === 0) {
            listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-empty'))}</div>`;
            return;
        }
        // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 表头行 + 全选 checkbox.
        // 问题 D (v118.34.25) · 改成: 全选含 success log (批量删除清历史) ·
        // 仅 retrying 中的行不可选(防跟 worker 撞). 批量重试 server-side
        // 自动 skip success · 不会重复推.
        const selectableIds = items
            .filter(function (l) {
                var isR = l.status === 'failed' && l.next_retry_at
                    && (new Date(l.next_retry_at).getTime() > Date.now() - 60000);
                return !isR;
            })
            .map(function (l) { return l.id; });
        const headerRow = '<div class="erp-log-row erp-log-row-header" data-log-header>'
            + (selectableIds.length > 0
                ? `<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t('erp-log-select-all-tip'))}">`
                : `<span class="erp-log-cb-spacer"></span>`)
            + `<span class="log-time">${escapeHtml(t('erp-log-col-time'))}</span>`
            + `<span class="log-status">${escapeHtml(t('erp-log-col-status'))}</span>`
            + `<span class="log-tag-header">${escapeHtml(t('erp-log-col-trigger'))}</span>`
            + `<span class="log-invoice">${escapeHtml(t('erp-log-col-invoice'))}</span>`
            // P1-C 后端列 (2026-05-26) · 工作空间(账套归属)· join ocr_history.workspace_client_id
            + `<span class="log-workspace">${escapeHtml(t('erp-log-col-workspace'))}</span>`
            // 批 1 改动 5 (v118.34.33) · 新增 "发票买方" 列 · 跟 "发票卖方" 分开
            + `<span class="log-client">${escapeHtml(t('erp-log-col-client'))}</span>`
            + `<span class="log-seller">${escapeHtml(t('erp-log-col-seller'))}</span>`
            // 改动 8 · "ERP" 列(走哪个 endpoint)
            + `<span class="log-erp">${escapeHtml(t('erp-log-col-erp'))}</span>`
            // 临时任务 (Zihao 2026-05-26) · 通用「ERP 单号」列(external_doc_no · 不写死 MR.ERP)
            + `<span class="log-doc">${escapeHtml(t('erp-log-col-doc'))}</span>`
            + `<span class="log-http">${escapeHtml(t('erp-log-col-http'))}</span>`
            + `<span class="log-elapsed">${escapeHtml(t('erp-log-col-elapsed'))}</span>`
            // 固定宽操作列(重试按钮)· 每行都有 · 保证列对齐(修:失败行 ↻ 把右侧列挤歪)
            + '<span class="log-actions"></span>'
            + '</div>';
        listEl.innerHTML = headerRow + items.map(log => {
            const time = new Date(log.created_at);
            const timeStr = `${String(time.getMonth()+1).padStart(2,'0')}-${String(time.getDate()).padStart(2,'0')} ${String(time.getHours()).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`;
            // v118.25 · 三态:success / retrying(failed + 有 next_retry_at)/ failed(终态)
            const isRetrying = log.status === 'failed'
                && log.next_retry_at
                && (new Date(log.next_retry_at).getTime() > Date.now() - 60000); // 兜底:就算稍微过了点也算重试中(worker 几秒就到)
            let statusClass, statusIcon, statusLabel;
            if (log.status === 'pending') {
                // 识别后立刻写的「推送中」· 旋转图标 · 推完会原地变 ✓/✗(2026-05-26)
                statusClass = 'retrying';
                statusIcon = '⟳';
                statusLabel = t('erp-status-pending');
            } else if (log.status === 'success') {
                statusClass = 'ok';
                statusIcon = '✓';
                statusLabel = t('erp-status-success');
            } else if (log.status === 'skipped_dup') {
                // 去重跳过(同发票同端点已成功推过)· 不是失败 · 中性「已存在」·
                // 该行带原 ERP 单号(docCell 会显)· 旧逻辑掉进 else 显红叉误导用户(Codex P1)
                statusClass = 'skipped';
                statusIcon = '⏭';
                statusLabel = t('erp-status-skipped');
            } else if (isRetrying) {
                statusClass = 'retrying';
                statusIcon = '↻';
                statusLabel = t('erp-status-retrying');
            } else {
                statusClass = 'fail';
                statusIcon = '✗';
                statusLabel = t('erp-status-failed');
            }
            let triggerTag;
            if (log.trigger === 'auto') triggerTag = `<span class="log-tag auto">${escapeHtml(t('log-tag-auto'))}</span>`;
            else if (log.trigger === 'retry') triggerTag = `<span class="log-tag retry">${escapeHtml(t('log-tag-retry'))}</span>`;
            else triggerTag = `<span class="log-tag manual">${escapeHtml(t('log-tag-manual'))}</span>`;
            // v118.25 · 重试信息 · 重新设计(2026-05-26 Zihao 报对齐 bug):不再做成
            // 行内变宽 chip(会把后面的列挤歪 · 失败行尤其明显)· 改成挂在状态图标的
            // tooltip 里(retryInfo)· 行布局只保留固定宽的操作列 · 列永远对齐。
            let retryInfo = '';
            const rc = log.retry_count || 0;
            const mr = log.max_retries || 3;
            if (isRetrying) {
                const nextMs = new Date(log.next_retry_at).getTime() - Date.now();
                const nextMin = Math.max(0, Math.round(nextMs / 60000));
                const nextLabel = nextMin <= 0
                    ? t('erp-retry-next-soon')
                    : t('erp-retry-next-min', { n: nextMin });
                const attemptLabel = t('erp-retry-attempt', { n: rc, max: mr });
                retryInfo = `${attemptLabel} · ${nextLabel}`;
            } else if (log.status === 'failed' && rc >= mr && !log.next_retry_at) {
                retryInfo = t('erp-retry-exhausted', { n: rc });
            }
            // v118.25 · 重试中不显示手动重推按钮(避免和 worker 撞);失败终态才显示
            const retryBtn = (log.status === 'failed' && !isRetrying)
                ? `<button class="log-retry-btn" data-log-retry="${escapeHtml(log.id)}" title="${escapeHtml(t('log-retry-title'))}">↻</button>`
                : '';
            // 问题 D (Zihao 2026-05-19 拍板 · v118.34.25) · 全选要含 success.
            // 原:只 failed 终态可选(重试中防抢 · success 没意义)
            // 改:重试中仍不可选(防跟 worker 撞)· success 可选(批量删除清历史用)·
            //     批量重试 server-side 跳过 success (skipped++) · 已实现.
            const canSelect = !isRetrying;
            const checked = _erpSelected.has(log.id) ? 'checked' : '';
            const cb = canSelect
                ? `<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(log.id)}" ${checked}>`
                : `<span class="erp-log-cb-spacer"></span>`;
            // 发票买方列(Zihao 2026-05-26)· 显 OCR 真买方名(发票上印的买方)·
            // 不是 Pearnly client 名(旧逻辑显 client_name → 未归属时误显 skin)。
            // 优先 ocr_buyer_name(发票真买方)→ 退回 client_name(已归属客户)→ 未归属灰字。
            const buyerName = (log.ocr_buyer_name || '').trim() || (log.client_name || '').trim();
            const clientCell = buyerName
                ? `<span class="log-client" title="${escapeHtml(buyerName)}">${escapeHtml(buyerName.substring(0, 18))}</span>`
                : `<span class="log-client log-client-empty" title="${escapeHtml(t('erp-log-client-unassigned-tip'))}">${escapeHtml(t('erp-log-client-unassigned'))}</span>`;
            // 工作空间/账套列 = 发票卖方自动分拣结果(Zihao 2026-05-26)。
            // 切换器只是查看过滤器、不决定归属;seller 没匹配到 workspace → 显「未归属/待确认卖方」
            //(不再显「个人事务」,避免误以为切换器决定归属)。
            const wsCell = log.workspace_name
                ? `<span class="log-workspace">${escapeHtml((log.workspace_name || '').substring(0, 16))}</span>`
                : `<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t('erp-log-ws-unresolved-tip'))}">${escapeHtml(t('erp-log-ws-unresolved'))}</span>`;
            // 改动 8 (v118.34.33) · ERP 列 · endpoint 名(用户起的)
            const erpCell = log.endpoint_name
                ? `<span class="log-erp">${escapeHtml((log.endpoint_name || '').substring(0, 14))}</span>`
                : `<span class="log-erp log-erp-deleted">${escapeHtml(t('erp-log-endpoint-deleted'))}</span>`;
            // 临时任务 (Zihao 2026-05-26) · 通用「ERP 单号」列。后端日志 API 已派生
            // external_doc_no/external_url(不写死 MR.ERP)。优先级:
            //   有 external_url → 「打开」链接
            //   否则有 external_doc_no → 可复制单号(点击复制 · 不触发 row 详情)
            //   否则 status=success 但空 → "ERP 未返回单号"(不留白)
            //   否则(失败等)→ "-"
            const extDocNo = (log.external_doc_no || '').trim();
            const extUrl = (log.external_url || '').trim();
            let docCell;
            if (extUrl) {
                docCell = `<span class="log-doc"><a href="${escapeHtml(extUrl)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(extDocNo || '')}">${escapeHtml(t('erp-log-doc-open'))}</a></span>`;
            } else if (extDocNo) {
                docCell = `<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(extDocNo)}" title="${escapeHtml(t('erp-log-doc-copy-tip'))}">${escapeHtml(extDocNo.substring(0, 18))}</span>`;
            } else if (log.status === 'success') {
                docCell = `<span class="log-doc log-doc-missing" title="${escapeHtml(t('erp-log-doc-missing-tip'))}">${escapeHtml(t('erp-log-doc-missing'))}</span>`;
            } else {
                docCell = `<span class="log-doc log-doc-empty">-</span>`;
            }
            return `
                <div class="erp-log-row ${statusClass}" data-log-detail="${escapeHtml(log.id)}">
                    ${cb}
                    <span class="log-time">${timeStr}</span>
                    <span class="log-status" title="${escapeHtml(statusLabel + (retryInfo ? ' · ' + retryInfo : ''))}">${statusIcon}</span>
                    ${triggerTag}
                    <span class="log-invoice">${escapeHtml(log.invoice_no || '-')}</span>
                    ${wsCell}
                    ${clientCell}
                    <span class="log-seller">${escapeHtml((log.seller_name || '').substring(0, 20))}</span>
                    ${erpCell}
                    ${docCell}
                    <span class="log-http">HTTP ${log.http_status || '-'}</span>
                    <span class="log-elapsed">${log.elapsed_ms}ms</span>
                    <span class="log-actions">${retryBtn}</span>
                </div>
            `;
        }).join('');
        // v118.25.1 · 重新渲染后 · 修剪掉已经不在列表里的选中项 + 刷新批量栏
        const visibleIds = new Set(items.map(x => x.id));
        for (const id of Array.from(_erpSelected)) {
            if (!visibleIds.has(id)) _erpSelected.delete(id);
        }
        _refreshErpBatchBar();
    } catch (e) {
        console.error('load erp logs failed', e);
        listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
    }
}

async function loadErpTodayStats() {
    const el = document.getElementById('erp-logs-today-stats');
    if (!el) return;
    try {
        const resp = await fetch('/api/erp/stats/today', {
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (!resp.ok) { el.textContent = ''; return; }
        const s = await resp.json();
        if (!s.total) {
            el.textContent = t('erp-stats-today-empty');
            el.className = 'erp-logs-today-stats';
            return;
        }
        const rate = s.total > 0 ? Math.round((s.success / s.total) * 100) : 0;
        const cls = s.failed > 0 ? 'has-fail' : '';
        el.className = 'erp-logs-today-stats ' + cls;
        el.innerHTML = t('erp-stats-today', {
            total: s.total, success: s.success, failed: s.failed, rate,
        });
    } catch (e) {}
}

// v118.25.1 · 批量栏可见性 + 计数刷新
function _refreshErpBatchBar() {
    const bar = document.getElementById('erp-logs-batch-bar');
    const countEl = document.getElementById('erp-logs-batch-count');
    // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 同步表头全选 checkbox 状态.
    // none → unchecked · all → checked · partial → indeterminate.
    const headerCb = document.querySelector('[data-log-select-all]');
    if (headerCb) {
        const visibleCbs = document.querySelectorAll('[data-log-cb]');
        const total = visibleCbs.length;
        const sel = _erpSelected.size;
        if (sel === 0) {
            headerCb.checked = false;
            headerCb.indeterminate = false;
        } else if (sel >= total) {
            headerCb.checked = true;
            headerCb.indeterminate = false;
        } else {
            headerCb.checked = false;
            headerCb.indeterminate = true;
        }
    }
    if (!bar || !countEl) return;
    const n = _erpSelected.size;
    if (n === 0) {
        bar.style.display = 'none';
        return;
    }
    bar.style.display = '';
    countEl.textContent = t('erp-batch-selected', { n });
}

// v118.25.1 · 批量重推执行 · 调 /api/erp/logs/batch-retry · 提示成功/失败/跳过计数
async function _runErpBatchRetry() {
    console.info('[ErpBatch] retry triggered · selected=', _erpSelected.size);
    const ids = Array.from(_erpSelected);
    if (ids.length === 0) {
        showToast(t('erp-batch-empty-warn'), 'warn');
        return;
    }
    const ok = await showConfirm(t('erp-batch-confirm', { n: ids.length }));
    if (!ok) return;
    try {
        const resp = await fetch('/api/erp/logs/batch-retry', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ log_ids: ids }),
        });
        if (!resp.ok) {
            showToast(t('erp-logs-error'), 'error');
            return;
        }
        const r = await resp.json();
        const msg = t('erp-batch-result', {
            ok: r.succeeded || 0,
            fail: r.failed || 0,
            skip: r.skipped || 0,
        });
        const kind = (r.failed && r.failed > 0) ? 'warn' : 'success';
        showToast(msg, kind);
        _erpSelected.clear();
        loadErpLogs();
    } catch (e) {
        console.error('batch retry failed', e);
        showToast(t('erp-logs-error'), 'error');
    }
}

// Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除执行
async function _runErpBatchDelete() {
    console.info('[ErpBatch] delete triggered · selected=', _erpSelected.size);
    const ids = Array.from(_erpSelected);
    if (ids.length === 0) {
        showToast(t('erp-batch-empty-warn'), 'warn');
        return;
    }
    const ok = await showConfirm(
        t('erp-batch-delete-confirm', { n: ids.length }),
        { danger: true },
    );
    if (!ok) return;
    try {
        const resp = await fetch('/api/erp/logs/batch-delete', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ log_ids: ids }),
        });
        if (!resp.ok) {
            showToast(t('erp-logs-error'), 'error');
            return;
        }
        const r = await resp.json();
        // 问题 C (Zihao 2026-05-19 拍板 · v118.34.25) · 立即从 DOM 移除被删 row ·
        // 不等 reload · 用户视觉立刻反馈"消失了". 然后再 reload 拉新数据填充
        // (DB 还有别的 log · 自动接着显示 · 不是"日志又弹出来"的 bug · 是正常分页).
        ids.forEach(function (id) {
            var row = document.querySelector('[data-log-detail="' + id + '"]');
            if (row) row.remove();
        });
        // 立即 hide batch bar(_erpSelected.clear 后 _refreshErpBatchBar 也会做 ·
        // 但提前 hide 防止短暂残留视觉).
        var bar = document.getElementById('erp-logs-batch-bar');
        if (bar) bar.style.display = 'none';
        showToast(
            t('erp-batch-delete-result', {
                n: r.deleted || 0, skip: r.skipped || 0,
            }),
            (r.deleted > 0) ? 'success' : 'warn',
        );
        _erpSelected.clear();
        // 延迟 500ms reload · 让用户先看到 "消失了" 效果 + toast · 再拉新数据
        setTimeout(loadErpLogs, 500);
    } catch (e) {
        console.error('batch delete failed', e);
        showToast(t('erp-logs-error'), 'error');
    }
}

// Bug 5 fix (v118.34.23) · defensive: 直接绑定到按钮 + 也保留事件委托
// 防 IIFE document-level handler 某些情况下没接管. 用 capture phase 保证 fire.
(function _bindErpBatchButtonsDirect() {
    function _bind() {
        var btnRetry = document.getElementById('btn-erp-batch-retry');
        var btnDelete = document.getElementById('btn-erp-batch-delete');
        var btnClear = document.getElementById('btn-erp-batch-clear');
        if (btnRetry && !btnRetry.dataset.boundDirect) {
            btnRetry.addEventListener('click', function (e) {
                e.preventDefault(); e.stopPropagation();
                _runErpBatchRetry();
            });
            btnRetry.dataset.boundDirect = '1';
        }
        if (btnDelete && !btnDelete.dataset.boundDirect) {
            btnDelete.addEventListener('click', function (e) {
                e.preventDefault(); e.stopPropagation();
                _runErpBatchDelete();
            });
            btnDelete.dataset.boundDirect = '1';
        }
        if (btnClear && !btnClear.dataset.boundDirect) {
            btnClear.addEventListener('click', function (e) {
                e.preventDefault(); e.stopPropagation();
                _erpSelected.clear();
                document.querySelectorAll('.erp-log-cb').forEach(function (x) { x.checked = false; });
                _refreshErpBatchBar();
            });
            btnClear.dataset.boundDirect = '1';
        }
    }
    // Bind at DOM ready + also on every tab switch / log load via mutation observer.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _bind);
    } else {
        _bind();
    }
    // 兜底: 隔 2s 重试 binding(防早期 DOM 还没渲染)
    setTimeout(_bind, 2000);
    setTimeout(_bind, 5000);
    window._bindErpBatchButtons = _bind;
})();

// 临时任务 (Zihao 2026-05-26) · 复制 ERP 单号(列表 / 凭证弹窗共用)·
// 带 clipboard API 失败时的 textarea+execCommand 降级(http 环境 / 权限禁用)。
async function copyErpDocNo(docNo) {
    docNo = (docNo || '').trim();
    if (!docNo) return;
    try {
        await navigator.clipboard.writeText(docNo);
        showToast(t('erp-doc-copy-ok', { no: docNo }), 'success');
    } catch (err) {
        try {
            const ta = document.createElement('textarea');
            ta.value = docNo;
            ta.style.position = 'fixed'; ta.style.opacity = '0';
            document.body.appendChild(ta); ta.select();
            document.execCommand('copy');
            ta.remove();
            showToast(t('erp-doc-copy-ok', { no: docNo }), 'success');
        } catch (e2) {
            showToast(t('erp-doc-copy-fail'), 'error');
        }
    }
}

async function showLogDetail(logId) {
    // v0.10 · 立即弹窗显示 loading · 再请求
    const modal = document.createElement('div');
    modal.className = 'log-detail-modal';
    modal.innerHTML = `
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t('log-detail-loading'))}</div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', async (e) => {
        if (e.target === modal || e.target.classList.contains('log-detail-close')) {
            modal.remove();
            return;
        }
        // 临时任务 (Zihao 2026-05-26) · 凭证弹窗里的复制 ERP 单号
        const copyEl = e.target.closest('[data-receipt-copy]');
        if (copyEl) {
            copyErpDocNo(copyEl.dataset.receiptCopy);
            return;
        }
        // 失败态建议动作 · 跳转后关弹窗
        const actEl = e.target.closest('[data-receipt-action]');
        if (actEl) {
            const act = actEl.dataset.receiptAction;
            if (act === 'retry') {
                retryPushLog(actEl.dataset.logId);
            } else if (act === 'exceptions') {
                if (typeof routeTo === 'function') routeTo('exceptions');
            } else if (act === 'mappings') {
                if (typeof routeTo === 'function') routeTo('integrations');
            }
            modal.remove();
            return;
        }
    });

    try {
        const resp = await fetch(`/api/erp/logs/${encodeURIComponent(logId)}`, {
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (!resp.ok) { modal.remove(); return; }
        const log = await resp.json();

        // 临时任务 (Zihao 2026-05-26) · 把"成功/失败提示"升级成"ERP 推送凭证弹窗"。
        // 端点名优先用后端 join 出来的 endpoint_name(详情 API 已带),兜底查本地 cache。
        const ep = _erpEndpoints.find(x => x.id === log.endpoint_id);
        const epName = log.endpoint_name
            || (ep ? ep.name : (log.endpoint_id ? t('erp-log-endpoint-deleted') : '-'));
        const adapter = (log.endpoint_adapter || (ep && ep.adapter) || '').toLowerCase();

        const time = new Date(log.created_at).toLocaleString();
        const triggerText = log.trigger === 'auto' ? t('log-tag-auto')
            : log.trigger === 'retry' ? t('log-tag-retry')
            : t('log-tag-manual');

        const reqJson = log.request_body ? JSON.stringify(log.request_body, null, 2) : t('erp-receipt-no-tech');
        const respBody = log.response_body || t('erp-receipt-no-tech');

        const isOk = log.status === 'success';
        // P2-10: 成功推送时友好显示行数
        let respDisplay = (typeof respBody === 'string') ? respBody : JSON.stringify(respBody, null, 2);
        if (isOk) {
            try {
                const rj = (typeof log.response_body === 'string') ? JSON.parse(log.response_body) : (log.response_body || {});
                const rows = rj.row_count || (Array.isArray(rj.imported_rows) ? rj.imported_rows.length : 0);
                if (rows > 0) respDisplay = t('log-push-rows').replace('{n}', String(rows));
            } catch (e) { /* 保留原始 */ }
        }

        // 通用 ERP 单号字段(后端日志 API 派生 · 不写死 MR.ERP)
        const extDocNo = (log.external_doc_no || '').trim();
        const extUrl = (log.external_url || '').trim();
        const extHint = (log.external_doc_hint || '').trim();

        // 发票买方(OCR 真买方名优先 · 退回已归属 client_name)+ 卖家 + 金额格式化
        const clientName = (log.ocr_buyer_name || '').trim() || log.client_name || '-';
        const sellerName = log.seller_name || '-';
        let amountStr = '-';
        const amtNum = Number(log.total_amount);
        if (log.total_amount != null && log.total_amount !== '' && !isNaN(amtNum)) {
            amountStr = amtNum.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        const summaryText = isOk ? t('erp-receipt-title-ok') : t('erp-receipt-title-fail');
        const summaryIcon = isOk ? '✓' : '✗';

        // 凭证主体:一行一项 key-value(label 固定宽 · value 自适应 · 见 .erp-receipt-row CSS)
        const rowsHtml = [];
        const addRow = (label, valueHtml) => {
            rowsHtml.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(label)}</span>
                    <span class="erp-receipt-val">${valueHtml}</span>
                </div>`);
        };
        // 成功 + 失败都显示:发票号 / ERP 系统 / Pearnly 客户 / 卖家 / 推送时间 / 耗时。
        // 仅成功额外显示:ERP 单号(带复制)+ 金额(失败时没单号没金额 · 不留空行)。
        addRow(t('erp-receipt-invoice-no'), `<strong>${escapeHtml(log.invoice_no || '-')}</strong>`);
        addRow(t('erp-receipt-erp-name'), escapeHtml(epName));

        if (isOk) {
            // ERP 单号行:有单号 → 单号 + 复制按钮;成功但空 → "未生成 ERP 单号"
            let docValHtml;
            if (extDocNo) {
                docValHtml = `<strong class="erp-receipt-docno">${escapeHtml(extDocNo)}</strong>`
                    + `<button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(extDocNo)}" title="${escapeHtml(t('erp-doc-copy-tip'))}">${escapeHtml(t('erp-receipt-copy-btn'))}</button>`;
            } else {
                docValHtml = `<span class="erp-receipt-docno-missing">${escapeHtml(t('erp-log-doc-missing'))}</span>`;
            }
            addRow(t('erp-receipt-doc-no'), docValHtml);
        }

        addRow(t('erp-receipt-client'), escapeHtml(clientName));
        addRow(t('erp-receipt-seller'), escapeHtml(sellerName));
        if (isOk) {
            addRow(t('erp-receipt-amount'), escapeHtml(amountStr));
        }
        addRow(t('erp-receipt-time'), escapeHtml(time));
        addRow(t('erp-receipt-elapsed'), escapeHtml((log.elapsed_ms != null ? log.elapsed_ms : '-') + 'ms'));

        // 主操作按钮:有 external_url → 打开 ERP;否则有单号 → 复制 ERP 单号
        let primaryActionHtml = '';
        if (isOk && extUrl) {
            primaryActionHtml = `<a class="erp-receipt-primary-btn" href="${escapeHtml(extUrl)}" target="_blank" rel="noopener">${escapeHtml(t('erp-receipt-open-erp'))}</a>`;
        } else if (isOk && extDocNo) {
            primaryActionHtml = `<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(extDocNo)}">${escapeHtml(t('erp-receipt-copy-docno'))}</button>`;
        }

        // adapter 专属提示(MR.ERP:去哪搜单号)· 仅成功 + 有单号 + 提示码时显示
        let hintHtml = '';
        if (isOk && extDocNo && extHint) {
            const hintKey = 'erp-receipt-hint-' + extHint;
            const hintText = t(hintKey);
            if (hintText && hintText !== hintKey) {
                // 铁律:线性 SVG 图标 · 不用 emoji
                const infoIc = `<svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
                hintHtml = `<div class="erp-receipt-hint">${infoIc}<span>${escapeHtml(hintText)}</span></div>`;
            }
        }

        // 失败态:错误码 + 友好原因 + 建议动作
        let failBlockHtml = '';
        if (!isOk) {
            const errCodeMatch = (log.error_msg || '').match(/ERR_[A-Z0-9_]+/);
            const errCode = errCodeMatch ? errCodeMatch[0] : '';
            // P2-C (B7) · 优先后端 4 语友好原因(不裸透泰文)· 没命中再回退 humanizeError(网络错误)
            const _efLang = (typeof currentLang === 'string' && currentLang) || window._currentLang || 'th';
            const _ef = log.error_friendly && log.error_friendly[_efLang];
            const friendly = _ef || (log.error_msg ? humanizeError(log.error_msg) : t('erp-receipt-no-error'));
            const isMappingErr = /ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(log.error_msg || '');
            const canRetry = !!(log.history_id && log.endpoint_id);
            const actionBtns = [];
            actionBtns.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t('erp-receipt-act-exceptions'))}</button>`);
            if (isMappingErr) {
                actionBtns.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t('erp-receipt-act-mapping'))}</button>`);
            }
            if (canRetry) {
                actionBtns.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(log.id)}">${escapeHtml(t('erp-receipt-act-retry'))}</button>`);
            }
            failBlockHtml = `
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t('erp-receipt-fail-reason'))}</div>
                <div class="erp-receipt-fail-box">
                    ${errCode ? `<div class="erp-receipt-errcode">${escapeHtml(errCode)}</div>` : ''}
                    <div class="erp-receipt-friendly">${escapeHtml(friendly)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t('erp-receipt-suggest'))}</div>
                <div class="erp-receipt-actions">${actionBtns.join('')}</div>`;
        }

        modal.querySelector('.log-detail-box').innerHTML = `
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${isOk ? 'ok' : 'fail'}">${summaryIcon}</span>
                    ${escapeHtml(summaryText)}
                    <span class="log-tag ${log.trigger}">${escapeHtml(triggerText)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${rowsHtml.join('')}
            </div>

            ${hintHtml}
            ${primaryActionHtml ? `<div class="erp-receipt-primary-wrap">${primaryActionHtml}</div>` : ''}
            ${failBlockHtml}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t('erp-receipt-tech-toggle'))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${log.http_status || '-'}</span>
                    <span>${log.elapsed_ms}ms</span>
                    <span>${escapeHtml(t('log-detail-attempt', { n: log.attempt || 1 }))}</span>
                </div>
                <div class="log-detail-section" style="margin-top:12px;">
                    <div class="log-detail-label">${escapeHtml(t('log-detail-request-human'))}</div>
                    <pre>${escapeHtml(reqJson)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t('log-detail-response-human'))}</div>
                    <pre>${escapeHtml(respDisplay)}</pre>
                </div>
            </details>
        `;
    } catch (e) {
        console.error(e);
        modal.remove();
    }
}

// v118.35.0.23 · 把后端 HTTPException detail 转成人话(防 [object Object])
// detail 可能是: string / {code, ...其它字段} / pydantic errors[] / 其它对象
function _humanizeBackendError(detail, fallback) {
    if (detail == null) return fallback || '操作失败';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        // pydantic ValidationError
        const first = detail[0] || {};
        if (first.msg) return first.msg;
        return fallback || '请求格式错误';
    }
    if (typeof detail === 'object') {
        // 优先按 code 走 i18n: 'err.<code>'
        if (detail.code) {
            const k = 'err.' + detail.code;
            try {
                const tr = t(k, detail);
                if (tr && tr !== k) return tr;
            } catch (e) { console.warn('[i18n] t() failed for key:', k, e); }
            return detail.code;
        }
        if (detail.message) return detail.message;
        if (detail.error)   return detail.error;
        if (detail.detail && typeof detail.detail === 'string') return detail.detail;
        try { return JSON.stringify(detail).slice(0, 160); } catch (_) {}
    }
    return fallback || String(detail);
}

function humanizeError(raw) {
    if (!raw) return '';
    const r = String(raw);
    if (/ECONNREFUSED|Connection refused/i.test(r)) return '连接被拒绝 · ERP 地址可能错了,或服务没启动';
    // 问题 A (Zihao 2026-05-19 拍板 · v118.34.25) · 去掉 ">10s" 过时数字
    // (实际 wait_for_selector 30s · retry 3 次 · 累计 ~90s)
    if (/listing fetch failed|wait_for_selector/i.test(r)) return '拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试';
    if (/ETIMEDOUT|timeout/i.test(r))                return '连接超时 · MR.ERP 响应慢 · 稍后再试';
    if (/ENOTFOUND|getaddrinfo/i.test(r))            return '域名解析失败 · ERP 地址拼错了';
    if (/certificate|SSL/i.test(r))                  return 'SSL 证书问题 · ERP 站点证书异常';
    if (/401|Unauthorized/i.test(r))                 return 'HTTP 401 · 认证失败,检查 Token 是否正确';
    if (/403|Forbidden/i.test(r))                    return 'HTTP 403 · 权限不足,ERP 拒绝访问';
    if (/404|Not Found/i.test(r))                    return 'HTTP 404 · URL 路径不存在';
    if (/^5\d\d/.test(r) || /500|502|503|504/.test(r)) return 'ERP 服务器错误 · 不是你的问题,等会儿再试';
    return r;
}

async function retryPushLog(logId) {
    try {
        const resp = await fetch(`/api/erp/logs/${encodeURIComponent(logId)}/retry`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
        });
        const data = await resp.json().catch(() => ({}));
        if (resp.ok && data.ok) {
            showToast(t('log-retry-ok'), 'success');
        } else {
            showToast(t('log-retry-fail') + ' · HTTP ' + (data.http_status || resp.status), 'error');
        }
        loadErpLogs();
        loadErpEndpoints();
    } catch (e) {
        showToast(t('log-retry-fail'), 'error');
    }
}

async function loadErpEndpoints() {
    try {
        const resp = await fetch('/api/erp/endpoints', {
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (resp.status === 401) {
            localStorage.removeItem('mrpilot_token');
            const _bd = await resp.json().catch(() => ({}));
            const _dc = typeof _bd.detail === 'string' ? _bd.detail : ((_bd.detail && _bd.detail.code) || '');
            if (_dc === 'auth.session_revoked') { _showSessionRevokedModal(); return; }
            window.location.href = '/';
            return;
        }
        const data = await resp.json();
        _erpEndpoints = data.items || [];
        window._erpEndpoints = _erpEndpoints;
        renderErpEndpointsList();
    } catch (e) {
        console.error('load endpoints failed', e);
    }
}

// v118.34.34 (批 2 改动 7) · 外部模块 (erp-mrerp-connect.js) 调
// PATCH /api/erp/endpoints/:id 切 enabled 后,要让 home.js 的全局
// _erpEndpoints 同步 · 不然 OCR drawer 推送按钮还在用旧 list (会显示
// 已停用的 endpoint 在 picker 里).
window._refreshErpEndpointsCache = function () {
    return loadErpEndpoints();
};

// v0.17 · M5 · 今日 ERP 推送统计 · 显示在 ERP 对接 tab 头部
async function loadErpTodayStats() {
    const host = document.getElementById('erp-today-stats');
    if (!host) return;
    host.innerHTML = '';
    try {
        const resp = await fetch('/api/erp/stats/today', {
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (!resp.ok) return;
        const data = await resp.json();
        const total = data.total || 0;
        const success = data.success || 0;
        const failed = data.failed || 0;
        const autoCnt = data.auto_cnt || 0;
        if (total === 0) {
            host.innerHTML = `<span class="erp-today-empty">${escapeHtml(t('erp-today-none'))}</span>`;
            return;
        }
        const parts = [];
        parts.push(`<span class="erp-today-item"><strong>${total}</strong> ${escapeHtml(t('erp-today-total'))}</span>`);
        if (success > 0) parts.push(`<span class="erp-today-item ok"><strong>${success}</strong> ${escapeHtml(t('erp-today-success'))}</span>`);
        if (failed > 0) parts.push(`<span class="erp-today-item fail"><strong>${failed}</strong> ${escapeHtml(t('erp-today-failed'))}</span>`);
        if (autoCnt > 0) parts.push(`<span class="erp-today-item auto"><strong>${autoCnt}</strong> ${escapeHtml(t('erp-today-auto'))}</span>`);
        host.innerHTML = parts.join('');
    } catch (e) {
        console.warn('loadErpTodayStats failed', e);
    }
}

function renderErpEndpointsList() {
    const list = document.getElementById('erp-endpoints-list');
    const summary = document.getElementById('erp-status-summary');
    const addBtn = document.getElementById('btn-add-endpoint');

    if (!list) {
        console.warn('erp-endpoints-list 容器不存在');
        return;
    }

    // v0.8 · 按 endpoints_limit 灰化新增按钮
    if (addBtn && _userInfo) {
        const limit = _userInfo.endpoints_limit;
        if (limit !== -1 && _erpEndpoints.length >= limit) {
            addBtn.disabled = true;
            addBtn.title = t('ep-limit-reached', { limit });
            addBtn.classList.add('btn-disabled-plus');
        } else {
            addBtn.disabled = false;
            addBtn.title = '';
            addBtn.classList.remove('btn-disabled-plus');
        }
    }

    if (_erpEndpoints.length === 0) {
        list.innerHTML = `<div class="erp-empty">${escapeHtml(t('ep-list-empty'))}</div>`;
        if (summary) {
            summary.textContent = t('auto-status-none');
            summary.className = 'auto-status-pill none';
        }
        return;
    }

    const autoOn = _erpEndpoints.some(e => e.auto_push && e.enabled);
    if (summary) {
        summary.textContent = t('auto-status-active', {
            n: _erpEndpoints.length,
            mode: autoOn ? t('auto-status-on') : t('auto-status-off'),
        });
        summary.className = 'auto-status-pill ' + (autoOn ? 'active' : 'ready');
    }
    // v0.17 · M5 · 异步加载今日统计 · 追加到 summary 区域下方
    loadErpTodayStats();

    list.innerHTML = _erpEndpoints.map(ep => {
        const cfg = ep.config || {};
        const url = escapeHtml(cfg.url || '');
        const hasToken = !!cfg._token_set;
        const enabled = ep.enabled !== false;

        const badges = [];
        if (ep.is_default) badges.push(`<span class="ep-badge default">${escapeHtml(t('ep-default'))}</span>`);
        if (ep.auto_push) badges.push(`<span class="ep-badge auto">${escapeHtml(t('ep-auto-push-on'))}</span>`);
        if (!enabled) badges.push(`<span class="ep-badge disabled">${escapeHtml(t('ep-disabled'))}</span>`);

        const stats = [];
        if (ep.success_count > 0) stats.push(`<span class="ep-stat ok">${escapeHtml(t('ep-success', { n: ep.success_count }))}</span>`);
        if (ep.failure_count > 0) stats.push(`<span class="ep-stat fail">${escapeHtml(t('ep-failure', { n: ep.failure_count }))}</span>`);

        return `
            <div class="erp-endpoint" data-ep-id="${escapeHtml(ep.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(ep.name)}</div>
                        <div class="ep-badges">${badges.join('')}</div>
                    </div>
                    <div class="ep-url">${url || '-'}</div>
                    <div class="ep-stats">${stats.join(' · ')}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(ep.id)}">
                        <span>${escapeHtml(t('ep-edit'))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(ep.id)}">
                        <span>${escapeHtml(t('ep-delete'))}</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    // v0.8.1 · 列表下方显示上限提示(根据 plan)
    if (_userInfo && _userInfo.endpoints_limit !== -1) {
        const usedN = _erpEndpoints.length;
        const limit = _userInfo.endpoints_limit;
        const plan = _userInfo.plan;
        const hint = document.createElement('div');
        hint.className = 'erp-limit-hint';
        if (plan === 'free') {
            hint.innerHTML = `${escapeHtml(t('ep-free-limit-hint', { used: usedN, limit }))} <a data-upgrade="plus">${escapeHtml(t('upgrade-to-plus'))}</a>`;
        } else {
            hint.textContent = t('ep-plus-limit-hint', { used: usedN, limit });
        }
        list.appendChild(hint);
    }
}

// 打开新增对话框
function openEndpointModal(editingId) {
    _epEditingId = editingId || null;
    const modal = document.getElementById('endpoint-modal');
    const titleEl = document.getElementById('endpoint-modal-title');
    titleEl.textContent = editingId ? t('ep-modal-title-edit') : t('ep-modal-title-new');

    const nameEl = document.getElementById('ep-name');
    const urlEl = document.getElementById('ep-url');
    const tokenEl = document.getElementById('ep-token');
    const isDefEl = document.getElementById('ep-is-default');
    const autoPushEl = document.getElementById('ep-auto-push');
    const resultEl = document.getElementById('ep-test-result');

    resultEl.style.display = 'none';
    resultEl.textContent = '';

    // 清掉上次遗留的错误提示
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.remove();

    if (editingId) {
        const ep = _erpEndpoints.find(e => e.id === editingId);
        if (!ep) return;
        nameEl.value = ep.name || '';
        urlEl.value = (ep.config || {}).url || '';
        tokenEl.value = (ep.config || {})._token_set ? (ep.config.token || '') : '';
        tokenEl.placeholder = (ep.config || {})._token_set ? '（已保存 · 留空保持不变）' : t('ep-token-ph');
        isDefEl.checked = !!ep.is_default;
        autoPushEl.checked = !!ep.auto_push;
    } else {
        nameEl.value = '';
        urlEl.value = '';
        tokenEl.value = '';
        tokenEl.placeholder = t('ep-token-ph');
        isDefEl.checked = _erpEndpoints.length === 0; // 第一个默认选中
        // v118.27.8.1.15 · 新建 endpoint 默认开启自动推送(0 操作上 ERP)· 老 endpoint 不变(走 14132 读 ep.auto_push)
        autoPushEl.checked = true;
    }

    // v0.15 · 扁平权限 · 所有人都能自动推送
    const autoPushRow = autoPushEl.closest('.form-switch-row');
    autoPushEl.disabled = false;
    if (autoPushRow) {
        autoPushRow.classList.remove('disabled-plus');
        autoPushRow.title = '';
        autoPushRow.style.cursor = '';
        autoPushRow.onclick = null;
        const b = autoPushRow.querySelector('.plus-badge');
        if (b) b.remove();
    }

    modal.style.display = '';
    setTimeout(() => nameEl.focus(), 50);
}

function closeEndpointModal() {
    document.getElementById('endpoint-modal').style.display = 'none';
    _epEditingId = null;
    // 关闭时清错误提示,避免下次打开残留
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.remove();
}

function _sanitizeUrl(raw) {
    // v0.9.1 · 清理常见"复制糟粕"(Copy to clipboard / 空格后跟可疑词)
    if (!raw) return '';
    let u = raw.trim();
    // 只保留到第一个空格前(URL 不能含空格)
    const spIdx = u.search(/\s/);
    if (spIdx >= 0) u = u.slice(0, spIdx);
    return u;
}

function readEndpointForm() {
    const name = document.getElementById('ep-name').value.trim();
    const url = _sanitizeUrl(document.getElementById('ep-url').value);
    const tokenVal = document.getElementById('ep-token').value;
    const isDefault = document.getElementById('ep-is-default').checked;
    const autoPush = document.getElementById('ep-auto-push').checked;

    const config = { url };
    // token:编辑模式下如果留空,发 "***" 占位(后端会保留旧值);否则发新值
    if (_epEditingId) {
        if (tokenVal) config.token = tokenVal;
    } else {
        if (tokenVal) config.token = tokenVal;
    }

    return { name, url, tokenVal, isDefault, autoPush, config };
}

async function testEndpointConnection() {
    const { name, url, config } = readEndpointForm();
    const resultEl = document.getElementById('ep-test-result');
    if (!url) {
        resultEl.style.display = '';
        resultEl.className = 'form-test-result fail';
        resultEl.textContent = t('ep-required');
        return;
    }
    resultEl.style.display = '';
    resultEl.className = 'form-test-result running';
    resultEl.textContent = t('ep-test-running');

    try {
        const resp = await fetch('/api/erp/test-connection', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify({ adapter: 'webhook', config }),
        });
        const data = await resp.json();
        if (data.success) {
            resultEl.className = 'form-test-result ok';
            resultEl.textContent = t('ep-test-ok', { status: data.http_status, ms: data.elapsed_ms });
        } else {
            resultEl.className = 'form-test-result fail';
            resultEl.textContent = t('ep-test-fail', { err: data.error_msg || 'unknown' });
        }
    } catch (e) {
        resultEl.className = 'form-test-result fail';
        resultEl.textContent = t('ep-test-fail', { err: e.message });
    }
}

async function saveEndpoint() {
    const form = readEndpointForm();
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.style.display = 'none';

    if (!form.name || !form.url) {
        showEpSaveError(t('ep-required'));
        return;
    }
    const payload = {
        name: form.name,
        adapter: 'webhook',
        config: form.config,
        is_default: form.isDefault,
        auto_push: form.autoPush,
    };

    const btn = document.getElementById('btn-ep-save');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.classList.add('loading');

    try {
        let resp;
        if (_epEditingId) {
            resp = await fetch(`/api/erp/endpoints/${encodeURIComponent(_epEditingId)}`, {
                method: 'PATCH',
                headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        } else {
            resp = await fetch('/api/erp/endpoints', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        }
        if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            const detail = errData.detail || `HTTP ${resp.status}`;
            throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        }
        // 成功 · 静默关窗 + 小 toast
        closeEndpointModal();
        showToast(t('ep-save-ok'));
        loadErpEndpoints();
    } catch (e) {
        showEpSaveError(`${t('ep-save-fail')} · ${e.message || 'unknown'}`);
    } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
        btn.innerHTML = originalText;
    }
}

function showEpSaveError(msg) {
    let box = document.getElementById('ep-save-error');
    if (!box) {
        const foot = document.querySelector('#endpoint-modal .modal-foot');
        if (!foot) return;
        box = document.createElement('div');
        box.id = 'ep-save-error';
        box.className = 'ep-inline-error';
        foot.parentNode.insertBefore(box, foot);
    }
    box.textContent = msg;
    box.style.display = '';
}

// 简易 toast(右下角冒泡 · 2.5 秒自动消失 · 不阻塞交互)
function showToast(msg, kind, duration) {
    let wrap = document.getElementById('mp-toast-wrap');
    if (!wrap) {
        wrap = document.createElement('div');
        wrap.id = 'mp-toast-wrap';
        document.body.appendChild(wrap);
    }
    kind = kind || 'success';
    // 兼容别名:ok/success/info/warn/warning/error/danger
    if (kind === 'ok') kind = 'success';
    if (kind === 'warning') kind = 'warn';
    if (kind === 'danger') kind = 'error';

    const ICONS = {
        success: '<path d="M3 8l3 3 7-7"/>',
        error:   '<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',
        warn:    '<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',
        info:    '<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',
        loading: '<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>',
    };

    const toast = document.createElement('div');
    toast.className = 'mp-toast ' + kind;
    toast.innerHTML = `
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${ICONS[kind] || ICONS.success}
        </svg>
        <span>${escapeHtml(msg)}</span>
    `;
    wrap.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));

    // v115 · duration 默认 2500ms · 传 0 表示不自动关 · 调用方需手动关
    const dur = (typeof duration === 'number') ? duration : 2500;
    let timer = null;
    const dismiss = () => {
        if (timer) { clearTimeout(timer); timer = null; }
        toast.classList.remove('show');
        setTimeout(() => { try { toast.remove(); } catch(e) {} }, 300);
    };
    if (dur > 0) {
        timer = setTimeout(dismiss, dur);
    }
    return dismiss;   // 返回手动关闭函数
}

async function deleteEndpoint(endpointId) {
    const ep = _erpEndpoints.find(e => e.id === endpointId);
    if (!ep) return;
    const ok = await showConfirm(t('ep-delete-confirm', { name: ep.name }), { danger: true });
    if (!ok) return;
    try {
        const resp = await fetch(`/api/erp/endpoints/${encodeURIComponent(endpointId)}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token },
        });
        if (!resp.ok) throw new Error();
        showToast(t('ep-delete-ok'));
        loadErpEndpoints();
    } catch {
        showToast(t('ep-save-fail'), 'fail');
    }
}

// 事件绑定
(function initAutomationPage() {
    // 点新增按钮
    document.getElementById('btn-add-endpoint').addEventListener('click', () => openEndpointModal(null));

    // 对话框关闭
    document.getElementById('endpoint-modal-close').addEventListener('click', closeEndpointModal);
    document.getElementById('btn-ep-cancel').addEventListener('click', closeEndpointModal);

    // 点遮罩不关闭(避免误触丢失填写的内容 · 只能通过关闭按钮/取消按钮关闭)

    // 测试连接
    document.getElementById('btn-ep-test').addEventListener('click', testEndpointConnection);

    // 保存
    document.getElementById('btn-ep-save').addEventListener('click', saveEndpoint);

    // v0.9.1 · URL 输入框失焦自动清理"Copy to clipboard"等粘贴糟粕
    document.getElementById('ep-url').addEventListener('blur', (e) => {
        const cleaned = _sanitizeUrl(e.target.value);
        if (cleaned !== e.target.value.trim()) {
            e.target.value = cleaned;
        }
    });

    // 列表里的编辑/删除按钮(事件委托)
    document.addEventListener('click', (e) => {
        const editBtn = e.target.closest('[data-ep-edit]');
        const delBtn = e.target.closest('[data-ep-del]');
        if (editBtn) openEndpointModal(editBtn.dataset.epEdit);
        if (delBtn) deleteEndpoint(delBtn.dataset.epDel);

        // v0.9.1 · 推送日志交互
        const retryBtn = e.target.closest('[data-log-retry]');
        if (retryBtn) {
            e.stopPropagation();
            retryPushLog(retryBtn.dataset.logRetry);
            return;
        }
        // v118.25.1 · 批量勾选
        const cb = e.target.closest('[data-log-cb]');
        if (cb) {
            e.stopPropagation();
            const id = cb.dataset.logCb;
            if (cb.checked) _erpSelected.add(id);
            else _erpSelected.delete(id);
            _refreshErpBatchBar();
            return;
        }
        // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 表头全选 checkbox
        const selectAllCb = e.target.closest('[data-log-select-all]');
        if (selectAllCb) {
            e.stopPropagation();
            const checkAll = selectAllCb.checked;
            const allCbs = document.querySelectorAll('[data-log-cb]');
            allCbs.forEach(function (rowCb) {
                rowCb.checked = checkAll;
                const id = rowCb.dataset.logCb;
                if (checkAll) _erpSelected.add(id);
                else _erpSelected.delete(id);
            });
            _refreshErpBatchBar();
            return;
        }
        // v118.25.1 · 批量重推按钮
        if (e.target.closest('#btn-erp-batch-retry')) {
            e.stopPropagation();
            _runErpBatchRetry();
            return;
        }
        // v118.25.1 · 取消选择
        if (e.target.closest('#btn-erp-batch-clear')) {
            e.stopPropagation();
            _erpSelected.clear();
            document.querySelectorAll('.erp-log-cb').forEach(x => { x.checked = false; });
            _refreshErpBatchBar();
            return;
        }
        const logRow = e.target.closest('[data-log-detail]');
        if (logRow) {
            // 点 checkbox 不算点 row
            if (e.target.closest('[data-log-cb]')) return;
            // 临时任务 (Zihao 2026-05-26) · 点 ERP 单号 → 复制 · 不打开详情
            const copyDocEl = e.target.closest('[data-copy-doc]');
            if (copyDocEl) {
                e.stopPropagation();
                copyErpDocNo(copyDocEl.dataset.copyDoc);
                return;
            }
            // 点「打开」链接 → 让 <a> 默认在新标签打开 · 不打开详情
            if (e.target.closest('.log-doc-open')) return;
            showLogDetail(logRow.dataset.logDetail);
            return;
        }
        const filterChip = e.target.closest('.chip-filter');
        if (filterChip) {
            document.querySelectorAll('#erp-logs-filters .chip-filter').forEach(c => c.classList.remove('active'));
            filterChip.classList.add('active');
            _logFilter = { key: filterChip.dataset.filterKey, val: filterChip.dataset.filterVal };
            loadErpLogs();
            return;
        }
        if (e.target.closest('#btn-refresh-logs')) {
            const btn = e.target.closest('#btn-refresh-logs');
            btn.classList.add('spinning');
            setTimeout(() => btn.classList.remove('spinning'), 600);
            loadErpLogs();
            return;
        }

        // v0.10 · 自动化子菜单切换(guard: 只处理有 data-auto-tab 的按钮，防止对账中心等共用 .auto-nav-item 类名的按钮触发 switchAutomationTab(undefined))
        const autoNav = e.target.closest('.auto-nav-item');
        if (autoNav && autoNav.dataset.autoTab) {
            switchAutomationTab(autoNav.dataset.autoTab);
            return;
        }
    });
})();






/* ============================================================
 * BUG-FIX-RECON-ASYNC #16 · 对账异步任务前端共用工具(三对账共用)
 * submit 秒回 job_id → 轮询 GET /api/recon/jobs/{id} 到 done/failed →
 * 用 result_id 调现有结果接口渲染。瞬时网络/网关错误容忍重试,只在超时/失败才停。
 * ⚠️ 暂塞 home.js(全局 window 工具 · 三个 recon IIFE 共用)· 迁出 deadline = REFACTOR-C1
 *    拆 home.js 时一并搬到 src/home/recon/job-poll.js(整顿期 C 阶段)。
 * ============================================================ */
(function () {
    'use strict';
    const _STAGE_LBL = {
        parse:     { zh: '解析文件中', th: 'กำลังอ่านไฟล์', en: 'Parsing files', ja: 'ファイル解析中' },
        report:    { zh: '读取报告中', th: 'กำลังอ่านรายงาน', en: 'Reading report', ja: 'レポート読込中' },
        reconcile: { zh: '对账中',     th: 'กำลังกระทบยอด', en: 'Reconciling',   ja: '照合中' },
        build:     { zh: '生成中',     th: 'กำลังสร้างไฟล์', en: 'Building',     ja: '作成中' },
        persist:   { zh: '保存中',     th: 'กำลังบันทึก',   en: 'Saving',       ja: '保存中' },
        done:      { zh: '完成',       th: 'เสร็จสิ้น',     en: 'Done',         ja: '完了' },
    };
    // 「转圈处理中」旁的实时进度文案 · parse 阶段显示「共 X/Y 个文件」(Zihao 拍板:不加进度条)
    window._reconProgressText = function (progress, lang) {
        progress = progress || {};
        // 2026-05-24 修:旧版默认 zh + 调用方传的是启动时捕获的 lang → 泰语界面进度副文案显示中文。
        //   改为实时优先读当前 UI 语言 · 默认 th(首发市场)· 非法值兜底 th。
        lang = window._currentLang || lang || localStorage.getItem('mrpilot_lang') || 'th';
        if (!_STAGE_LBL.parse[lang]) lang = 'th';
        const stage = progress.stage || 'parse';
        const lbl = (_STAGE_LBL[stage] || _STAGE_LBL.parse);
        const label = lbl[lang] || lbl.th || lbl.en;
        const total = progress.stage_total, done = progress.stage_done;
        if (stage === 'parse' && Number.isFinite(total) && total > 0) {
            const cntL = { zh: '共 {d}/{t} 个文件', th: '{d}/{t} ไฟล์', en: '{d}/{t} files', ja: '{d}/{t} ファイル' }[lang] || '{d}/{t} files';
            return label + ' · ' + cntL.replace('{d}', done || 0).replace('{t}', total);
        }
        return label;
    };
    // 轮询任务到 done/failed · 返回最终 job(或 {status:'timeout'})。onProgress(progress, job) 每轮回调。
    window._reconPollJob = async function (jobId, token, opts) {
        opts = opts || {};
        const intervalMs = opts.intervalMs || 1500;
        const maxMs = opts.maxMs || 20 * 60 * 1000; // 20 分钟硬上限
        const start = Date.now();
        let softFails = 0;
        for (;;) {
            let job = null;
            try {
                const r = await fetch('/api/recon/jobs/' + encodeURIComponent(jobId), {
                    headers: { 'Authorization': 'Bearer ' + token },
                });
                try { job = await r.json(); } catch (_) { job = null; }
                if (!r.ok || !job || !job.ok) { job = null; }
            } catch (_) { job = null; }
            if (job) {
                softFails = 0;
                if (opts.onProgress) { try { opts.onProgress(job.progress || {}, job); } catch (_) {} }
                // S8 · needs_review 也终止轮询 · 交调用方弹逐行核对面板
                // BUG-FIX-RECON-GLCSV · needs_mapping 也终止轮询 · 交调用方弹『确认列对应』面板
                if (job.status === 'done' || job.status === 'failed'
                    || job.status === 'needs_review' || job.status === 'needs_mapping') return job;
            } else {
                // 瞬时错误容忍 · 连续 10 次(~15s)拿不到才放弃
                if (++softFails >= 10) return { ok: false, status: 'failed', error_code: 'poll_unreachable' };
            }
            if (Date.now() - start > maxMs) return { ok: false, status: 'timeout', error_code: 'timeout' };
            await new Promise(res => setTimeout(res, intervalMs));
        }
    };
})();

/* ============================================================
 * v118.33.6 · Bank Reconciliation v2 (Statement vs GL)
 * Two upload zones · 3-layer matching · Excel export
 * ============================================================ */
(function () {
    'use strict';

    // ── State ─────────────────────────────────────────────────────────
    let _initialized  = false; // guard: 防 init() 重复绑事件
    let _stmtFiles   = [];   // File objects for bank statement
    let _glFiles     = [];   // File objects for GL
    let _currentTask = null; // Last run result {task_id, detail, summary, stats}
    let _currentFilter = 'all';
    let _allRows     = [];   // parsed detail rows (flat)
    let _brv2Search  = { stmt: '', gl: '' };
    let _cachedHistoryTasks = [];

    // ── DOM helpers ───────────────────────────────────────────────────
    const $ = id => document.getElementById(id);
    function fmtNum(v) {
        if (v === null || v === undefined) return '—';
        const n = Number(v);
        if (isNaN(n)) return '—';
        return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    function fmtDate(s) {
        if (!s) return '—';
        return String(s).slice(0, 10).split('-').reverse().join('/');
    }
    function esc2(s) {
        return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }
    // BUG-FIX-RECON-GLCSV · 后台整侧解析明确失败(无表格可现场修)→ 按 error_code 给 4 语友好原因 + 引导
    function _brv2FailMsg(code, lang) {
        lang = window._currentLang || lang || 'th';
        const M = {
            stmt_headers_not_found: {zh:'认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传',
                                     th:'หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่',
                                     en:'Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV',
                                     ja:'銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください'},
            gl_headers_not_found:   {zh:'认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传',
                                     th:'หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่',
                                     en:'Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV',
                                     ja:'GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください'},
            stmt_no_rows:           {zh:'文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传',
                                     th:'ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า',
                                     en:'No transaction rows found · please upload the correct statement, or try a clearer version',
                                     ja:'取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください'},
            no_rows:                {zh:'解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传',
                                     th:'ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่',
                                     en:'No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version',
                                     ja:'解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください'},
            file_unreadable:        {zh:'文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传',
                                     th:'อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel',
                                     en:'File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel',
                                     ja:'ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください'},
            file_not_supported:     {zh:'不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV',
                                     th:'ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV',
                                     en:'File type not supported · please upload PDF / image / Excel / CSV',
                                     ja:'このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください'},
            ocr_failed:             {zh:'文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传',
                                     th:'อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV',
                                     en:'Could not read the file · try a clearer version, or convert to PDF / Excel / CSV',
                                     ja:'読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください'},
        };
        const generic = {zh:'解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传',
                         th:'อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่',
                         en:'Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload',
                         ja:'解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください'};
        const m = M[code] || generic;
        return m[lang] || m.th || m.en;
    }

    // ── File rendering（vex-drop-filename + preview panel） ──────────
    function renderFileList(zone) {
        const files = zone === 'stmt' ? _stmtFiles : _glFiles;
        // 更新拖拽区内摘要文字
        const nameEl = $(`brv2-${zone}-name`);
        if (nameEl) {
            if (files.length === 0) {
                nameEl.textContent = '';
            } else {
                const lang = window._currentLang || 'zh';
                const labels = { zh: '个文件', th: ' ไฟล์', en: ' file(s)', ja: ' ファイル' };
                nameEl.textContent = files.length + (labels[lang] || ' 个文件');
            }
        }
        // 若 preview panel 已展开则刷新对应列
        const panel = $('brv2-preview-panel');
        if (panel && panel.style.display !== 'none') {
            _renderBrv2Column(zone);
        }
        _updateTogglePreviewBtn();
    }

    function _updateTogglePreviewBtn() {
        const btn   = $('brv2-toggle-preview');
        const panel = $('brv2-preview-panel');
        const hasFiles = (_stmtFiles.length + _glFiles.length) > 0;
        if (btn) btn.style.display = hasFiles ? '' : 'none';
        if (!hasFiles && panel) {
            panel.style.display = 'none';
            if (btn) btn.classList.remove('open');
        }
    }

    function _renderBrv2PreviewPanel() {
        _renderBrv2Column('stmt');
        _renderBrv2Column('gl');
    }

    function _renderBrv2Column(zone) {
        const colEl = $(zone === 'stmt' ? 'brv2-pp-stmt-col' : 'brv2-pp-gl-col');
        if (!colEl) return;
        const files = zone === 'stmt' ? _stmtFiles : _glFiles;
        const lang = window._currentLang || 'zh';
        const titleMap = {
            stmt: { zh: '① 银行账单', th: '① บัญชีธนาคาร', en: '① Bank Stmt', ja: '① 銀行明細' },
            gl:   { zh: '② 总账 GL',  th: '② GL รายงาน',  en: '② GL Report', ja: '② GL帳簿' },
        };
        const title     = (titleMap[zone] || {})[lang] || titleMap[zone].zh;
        const ph        = esc2((window.t && window.t('vex-preview-search')) || '搜索文件名...');
        const clearLbl  = esc2((window.t && window.t('vex-preview-clear-all')) || '全清');
        const searchVal = _brv2Search[zone] || '';

        colEl.innerHTML =
            '<div class="vex-pp-col-title">' +
                '<span class="vex-pp-col-name">' + esc2(title) +
                ' <span class="vex-pp-col-count">' + files.length + '</span></span>' +
            '</div>' +
            '<div class="vex-pp-search-row">' +
                '<input class="vex-pp-search" id="brv2-pp-search-' + zone + '" type="text" placeholder="' + ph + '" value="' + esc2(searchVal) + '" autocomplete="off">' +
                '<button class="vex-pp-clear-btn" id="brv2-pp-clearall-' + zone + '" type="button">' + clearLbl + '</button>' +
            '</div>' +
            '<div class="vex-pp-file-list" id="brv2-pp-' + zone + '-list"></div>' +
            '<div class="vex-pp-pagination" id="brv2-pp-' + zone + '-pg"></div>';

        const si = $('brv2-pp-search-' + zone);
        if (si) si.addEventListener('input', function (e) {
            _brv2Search[zone] = e.target.value;
            _renderBrv2FileList(zone);
        });
        const ca = $('brv2-pp-clearall-' + zone);
        if (ca) ca.addEventListener('click', function () {
            if (zone === 'stmt') _stmtFiles.length = 0;
            else _glFiles.length = 0;
            renderFileList(zone);
            updateRunBtn();
        });
        _renderBrv2FileList(zone);
    }

    function _renderBrv2FileList(zone) {
        const listEl = $('brv2-pp-' + zone + '-list');
        const pgEl   = $('brv2-pp-' + zone + '-pg');
        if (!listEl) return;
        const files   = zone === 'stmt' ? _stmtFiles : _glFiles;
        const q       = (_brv2Search[zone] || '').toLowerCase();
        const filtered = q ? files.filter(f => f.name.toLowerCase().includes(q)) : files.slice();
        const fileIco = '<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>';
        const delIco  = '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';
        listEl.innerHTML = filtered.map((f, i) =>
            '<div class="vex-pp-file-row">' +
            fileIco +
            '<span class="vex-pp-fi-name" title="' + esc2(f.name) + '">' + esc2(f.name) + '</span>' +
            '<span class="vex-pp-fi-size">' + _brv2FmtSize(f.size) + '</span>' +
            '<button class="vex-pp-fi-del" type="button" data-zone="' + zone + '" data-idx="' + files.indexOf(f) + '" aria-label="remove">' + delIco + '</button>' +
            '</div>'
        ).join('');
        listEl.querySelectorAll('.vex-pp-fi-del').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const idx = parseInt(btn.dataset.idx, 10);
                if (btn.dataset.zone === 'stmt') _stmtFiles.splice(idx, 1);
                else _glFiles.splice(idx, 1);
                renderFileList(btn.dataset.zone);
                updateRunBtn();
            });
        });
        if (pgEl) {
            const tpl = (window.t && window.t('vex-preview-count')) || '显示 {n} / 共 {m}';
            pgEl.textContent = tpl.replace('{n}', filtered.length).replace('{m}', files.length);
        }
    }

    function _brv2FmtSize(bytes) {
        if (!bytes) return '';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    // P0.1 BUG-B-T1 v118.35.0.37 · 3 anchor 预填 cache 跨会话 · localStorage 单 key 兜底
    //   不分 bank · 1 个事务所 1-2 个银行 · 简化(后续 Phase 1 P1.4 加 confidence 时再 per-bank scope)
    var _BRV2_ANCHOR_KEY = 'pearnly.brv2.lastAnchorOcr';
    function _brv2SaveLastAnchorOcr(summary) {
        try {
            var ocr = summary && summary._anchor_ocr;
            if (!ocr || typeof ocr !== 'object') return;
            var payload = {
                stmt_opening: Number.isFinite(+ocr.stmt_opening) ? +ocr.stmt_opening : null,
                gl_opening:   Number.isFinite(+ocr.gl_opening)   ? +ocr.gl_opening   : null,
                gl_closing:   Number.isFinite(+ocr.gl_closing)   ? +ocr.gl_closing   : null,
                stmt_closing: Number.isFinite(+ocr.stmt_closing) ? +ocr.stmt_closing : null,  // BUG-FIX-T3 v118.35.0.44
                ts: Date.now(),
            };
            localStorage.setItem(_BRV2_ANCHOR_KEY, JSON.stringify(payload));
        } catch (_) { /* 私模 localStorage / quota / JSON 异常 · 静默(下次跑还能再存)*/ }
    }
    function _brv2ReadLastAnchorOcr() {
        try {
            var raw = localStorage.getItem(_BRV2_ANCHOR_KEY);
            if (!raw) return null;
            var p = JSON.parse(raw);
            if (!p || typeof p !== 'object') return null;
            return p;
        } catch (_) { return null; }
    }
    function _brv2RestoreAnchorPrefill() {
        var p = _brv2ReadLastAnchorOcr();
        if (!p) return;
        var map = {
            'brv2-anchor-stmt-opening': p.stmt_opening,
            'brv2-anchor-gl-opening':   p.gl_opening,
            'brv2-anchor-gl-closing':   p.gl_closing,
            'brv2-anchor-stmt-closing': p.stmt_closing,  // BUG-FIX-T3 v118.35.0.44 · 加 4th anchor 预填
        };
        var prefilledCount = 0;
        Object.keys(map).forEach(function (id) {
            var el = document.getElementById(id);
            if (!el) return;
            // 用户已经手填了任何值 → 不覆盖
            if (el.value !== '') return;
            var v = map[id];
            if (!Number.isFinite(v)) return;
            el.value = v.toFixed(2);
            var cell = el.closest && el.closest('.brv2-anchor-cell');
            if (cell) cell.classList.add('is-prefilled');
            prefilledCount += 1;
        });
        // 触发期初差额提示行(如果 stmt + gl opening 都预填了)
        var eq = document.getElementById('brv2-anchor-eq');
        var eqVal = document.getElementById('brv2-anchor-eq-val');
        if (eq && eqVal && Number.isFinite(p.stmt_opening) && Number.isFinite(p.gl_opening)) {
            var diff = p.stmt_opening - p.gl_opening;
            eqVal.textContent = diff.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            eq.style.display = '';
        }
        // BUG-FIX-T4 v118.35.0.45 · 至少 1 个 cell 被预填 → 显示橙色 banner 提示来源
        if (prefilledCount > 0) {
            var banner = document.getElementById('brv2-anchor-prefill-banner');
            if (banner) banner.classList.add('show');
        }
    }
    // BUG-FIX-T4 v118.35.0.45 · 用户改了任意一个 anchor 后 · 如果全部 cell 都没 is-prefilled · 隐藏 banner
    function _brv2UpdatePrefillBannerVisibility() {
        var banner = document.getElementById('brv2-anchor-prefill-banner');
        if (!banner) return;
        var anyPrefilled = false;
        ['brv2-anchor-gl-closing','brv2-anchor-stmt-closing','brv2-anchor-stmt-opening','brv2-anchor-gl-opening'].forEach(function (id) {
            var el = document.getElementById(id);
            if (!el) return;
            var cell = el.closest && el.closest('.brv2-anchor-cell');
            if (cell && cell.classList.contains('is-prefilled')) anyPrefilled = true;
        });
        banner.classList.toggle('show', anyPrefilled);
    }

    // P0.3 BUG-B-T3 v118.35.0.39 · 历史详情 / 跑完结果 显示『手动录入 anchor 对照表』
    //   读 summary._anchor_overrides · 列每个被改 anchor 的 OCR 值 vs 用户值 vs 差额
    //   动态创建 DOM 插入到 brv2-summary-collapse 之后 · 不动 home.html
    var _BRV2_ANCHOR_LABEL_KEYS = [
        ['stmt_opening', 'brv2-anchor-stmt-opening'],
        ['gl_opening',   'brv2-anchor-gl-opening'],
        ['gl_closing',   'brv2-anchor-gl-closing'],
        ['stmt_closing', 'brv2-anchor-stmt-closing'],   // BUG-FIX-T3 v118.35.0.44 · 加 4th anchor
    ];
    function _brv2T(key, fallback) {
        return (window.t && window.t(key)) || fallback;
    }
    function _brv2EscHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
    function _brv2FmtNum(v) {
        if (!Number.isFinite(+v)) return '—';
        return (+v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    function _brv2RenderAnchorAudit(summary) {
        var host = document.getElementById('brv2-summary-collapse');
        if (!host || !host.parentNode) return;
        var panel = document.getElementById('brv2-anchor-audit');
        var overrides = summary && summary._anchor_overrides;
        // 没 override → 移除既有 panel(切换不同 task 时清理)
        if (!overrides || typeof overrides !== 'object' || Object.keys(overrides).length === 0) {
            if (panel && panel.parentNode) panel.parentNode.removeChild(panel);
            return;
        }
        // 没 panel → 动态创建 · 插到 summary collapse 之后
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'brv2-anchor-audit';
            panel.style.cssText = 'margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;'
                + 'border-radius:8px;padding:14px 16px;';
            host.parentNode.insertBefore(panel, host.nextSibling);
        }
        // 渲染内容
        var rows = _BRV2_ANCHOR_LABEL_KEYS
            .map(function (pair) {
                var ov = overrides[pair[0]];
                if (!ov) return '';
                var ocr = +ov.ocr || 0;
                var usr = +ov.user || 0;
                var diff = usr - ocr;
                var sign = diff > 0 ? '+' : (diff < 0 ? '' : '');
                var diffColor = Math.abs(diff) < 0.005 ? '#6b7280'
                    : (diff > 0 ? '#16a34a' : '#dc2626');
                return '<tr>'
                    + '<td style="padding:6px 10px;color:#111827;font-size:13px">'
                    +   _brv2EscHtml(_brv2T(pair[1], pair[0])) + '</td>'
                    + '<td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;'
                    +   'font-variant-numeric:tabular-nums">' + _brv2EscHtml(_brv2FmtNum(ocr)) + '</td>'
                    + '<td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;'
                    +   'font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'
                    +   _brv2EscHtml(_brv2FmtNum(usr)) + '</td>'
                    + '<td style="padding:6px 10px;color:' + diffColor + ';font-weight:500;font-size:13px;'
                    +   'text-align:right;font-variant-numeric:tabular-nums">'
                    +   _brv2EscHtml(sign + _brv2FmtNum(diff)) + '</td>'
                    + '</tr>';
            })
            .join('');
        panel.innerHTML =
            '<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'
            + _brv2EscHtml(_brv2T('brv2-anchor-audit-title',
                '⚠ This run contains manually entered anchors'))
            + '</div>'
            + '<table style="width:100%;border-collapse:collapse;font-family:inherit">'
            + '<thead><tr>'
            + '<th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;'
            +   'font-weight:500;border-bottom:1px solid #fed7aa">'
            +   _brv2EscHtml(_brv2T('brv2-anchor-audit-col-field', 'Field')) + '</th>'
            + '<th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;'
            +   'font-weight:500;border-bottom:1px solid #fed7aa">'
            +   _brv2EscHtml(_brv2T('brv2-anchor-audit-col-ocr', 'OCR')) + '</th>'
            + '<th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;'
            +   'font-weight:500;border-bottom:1px solid #fed7aa">'
            +   _brv2EscHtml(_brv2T('brv2-anchor-audit-col-user', 'User')) + '</th>'
            + '<th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;'
            +   'font-weight:500;border-bottom:1px solid #fed7aa">'
            +   _brv2EscHtml(_brv2T('brv2-anchor-audit-col-diff', 'Diff')) + '</th>'
            + '</tr></thead><tbody>' + rows + '</tbody></table>';
    }

    function _initBrv2TogglePreview() {
        const btn = $('brv2-toggle-preview');
        if (btn && !btn._reconBound) {
            btn._reconBound = true;
            btn.addEventListener('click', function () {
                const panel = $('brv2-preview-panel');
                const label = $('brv2-toggle-preview-label');
                const isOpen = panel && panel.style.display !== 'none';
                if (panel) panel.style.display = isOpen ? 'none' : '';
                btn.classList.toggle('open', !isOpen);
                if (label) label.textContent = isOpen
                    ? ((window.t && window.t('vex-toggle-preview-open')) || '查看清单')
                    : ((window.t && window.t('vex-toggle-preview-close')) || '收起清单');
                if (!isOpen) _renderBrv2PreviewPanel();
            });
        }
    }

    function updateRunBtn() {
        const btn    = $('brv2-run-btn');
        const status = $('brv2-status');
        const hasStmt = _stmtFiles.length > 0;
        const hasGl   = _glFiles.length > 0;
        if (btn) btn.disabled = !(hasStmt && hasGl);
        if (status) {
            const lang = window._currentLang || 'zh';
            if (!hasStmt && !hasGl) {
                const m = { zh: '请上传银行账单和 GL 文件', th: 'กรุณาอัปโหลดบัญชีธนาคารและ GL', en: 'Upload bank statement and GL files', ja: '銀行明細と GL を両方アップロードしてください' };
                status.textContent = m[lang] || m.zh;
            } else if (!hasStmt) {
                const m = { zh: '还缺银行账单 PDF', th: 'ยังขาดไฟล์บัญชีธนาคาร PDF', en: 'Missing bank statement PDF', ja: '銀行明細 PDF が未アップロード' };
                status.textContent = m[lang] || m.zh;
            } else if (!hasGl) {
                const m = { zh: '还缺 GL 文件', th: 'ยังขาดไฟล์ GL', en: 'Missing GL file', ja: 'GL ファイルが未アップロード' };
                status.textContent = m[lang] || m.zh;
            } else {
                const m = { zh: '两份文件已就绪', th: 'พร้อมสอบทาน', en: 'Ready to reconcile', ja: '照合を開始できます' };
                status.textContent = m[lang] || m.zh;
            }
        }
    }

    // ── Drag-and-drop（整区点击 · 无独立按钮） ────────────────────────
    function setupDrop(zoneId, inputId, zone) {
        const zoneEl  = $(zoneId);
        const inputEl = $(inputId);
        if (!zoneEl || !inputEl) return;

        // 整区点击 → 弹文件对话框
        zoneEl.addEventListener('click', () => inputEl.click());
        zoneEl.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inputEl.click(); }
        });

        zoneEl.addEventListener('dragover', e => { e.preventDefault(); zoneEl.classList.add('drag-over'); });
        zoneEl.addEventListener('dragleave', () => zoneEl.classList.remove('drag-over'));
        zoneEl.addEventListener('drop', e => {
            e.preventDefault();
            zoneEl.classList.remove('drag-over');
            const dropped = Array.from(e.dataTransfer.files || []);
            if (zone === 'stmt') _stmtFiles.push(...dropped);
            else _glFiles.push(...dropped);
            renderFileList(zone);
            updateRunBtn();
        });

        inputEl.addEventListener('change', () => {
            const chosen = Array.from(inputEl.files || []);
            if (zone === 'stmt') _stmtFiles.push(...chosen);
            else _glFiles.push(...chosen);
            inputEl.value = '';
            renderFileList(zone);
            updateRunBtn();
        });
    }

    // ── Progress helpers ──────────────────────────────────────────────
    function showProgress(show) {
        const p = $('brv2-progress'), btn = $('brv2-run-btn'), err = $('brv2-error');
        if (p)   p.style.display  = show ? '' : 'none';
        if (btn) btn.disabled     = show;
        if (err) err.style.display = 'none';
    }
    function showError(msg) {
        const err = $('brv2-error');
        if (err) { err.textContent = msg; err.style.display = ''; err.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
        showProgress(false);
        updateRunBtn();
        if (window.showToast) window.showToast(msg, 'error');
    }

    // ── Run reconciliation ────────────────────────────────────────────
    async function runRecon() {
        if (_stmtFiles.length === 0 || _glFiles.length === 0) return;
        const token = localStorage.getItem('mrpilot_token') || '';
        const lang  = (window._currentLang || 'zh');
        const acct  = ($('brv2-acct-select') || {}).value || '';

        showResultSections(false);
        showProgress(true);

        try {
            const fd = new FormData();
            _stmtFiles.forEach(f => fd.append('stmt_files', f));
            _glFiles.forEach(f => fd.append('gl_files', f));
            fd.append('gl_account', acct);
            fd.append('lang', lang);

            // BUG-B v118.35.0.36 · 3 个 anchor 余额手动录入 · 优先于 OCR 抽到的值
            // BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor stmt_closing(Statement 期末)
            const aGlClose   = parseFloat(($('brv2-anchor-gl-closing')   || {}).value);
            const aStmtClose = parseFloat(($('brv2-anchor-stmt-closing') || {}).value);
            const aStmtOpen  = parseFloat(($('brv2-anchor-stmt-opening') || {}).value);
            const aGlOpen    = parseFloat(($('brv2-anchor-gl-opening')   || {}).value);
            if (Number.isFinite(aGlClose))   fd.append('gl_closing_override',   aGlClose);
            if (Number.isFinite(aStmtClose)) fd.append('stmt_closing_override', aStmtClose);
            if (Number.isFinite(aStmtOpen))  fd.append('stmt_opening_override', aStmtOpen);
            if (Number.isFinite(aGlOpen))    fd.append('gl_opening_override',   aGlOpen);

            // BUG-FIX-RECON-ASYNC #16 · 改异步:submit 秒回 job_id → 轮询 → 用 result_id 取结果
            const submitRes = await fetch('/api/recon/bank-v2/submit', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: fd,
            });
            // v118.35.0.68 · 兜底:服务器返回非 JSON(网关 5xx/HTML 错误页 · 如磁盘满致 500)时
            //   res.json() 会抛 "Unexpected token '<'" · 不再原样弹给用户 · 改友好 4 语提示
            let sub = null;
            try { sub = await submitRes.json(); } catch (_) { sub = null; }
            // ADR-006 · 新模板 → 弹"确认列对应"面板(确认并保存后自动重跑)· 不再报"解析失败"
            if (sub && sub.needs_mapping) {
                showProgress(false);
                if (window.ReconMapping) {
                    window.ReconMapping.show(sub, {
                        token: token, lang: lang,
                        onConfirmed: function () { runRecon(); },
                    });
                } else {
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                }
                return;
            }
            if (!submitRes.ok || !sub || !sub.ok || !sub.job_id) {
                showProgress(false);
                if (sub && (sub.detail || sub.error)) {
                    showError(_humanizeBackendError(sub.detail || sub.error, 'Error ' + submitRes.status));
                } else {
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                }
                return;
            }

            // 轮询后台任务 · 转圈旁实时显示「共 X/Y 个文件」
            const _subEl = $('brv2-progress-sub');
            const job = await window._reconPollJob(sub.job_id, token, {
                onProgress: (p) => { if (_subEl) _subEl.textContent = window._reconProgressText(p, lang); },
            });
            // BUG-FIX-RECON-GLCSV · 后台解析读到表格但不认识列(整侧 needs_mapping)→ 弹『确认列对应』。
            //   正常 CSV/Excel 在 submit 同步预检就弹了 · 这里是防御纵深(预检漏网/PDF GL 等)·
            //   守铁律「整侧失败绝不进 done 完成态」。确认保存模板后 onConfirmed 重跑(预检命中模板即过)。
            if (job && job.status === 'needs_mapping' && job.mapping) {
                showProgress(false);
                if (window.ReconMapping) {
                    window.ReconMapping.show(job.mapping, {
                        token: token, lang: lang,
                        onConfirmed: function () { runRecon(); },
                    });
                } else {
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                }
                return;
            }
            // ADR-006 S8 · OCR 低信心/不完整 → 弹逐行核对纠错面板 · 用户改完用修正行重对账
            //   (不重 OCR、不重扣费;干净 OCR 不会到这里)· 守铁律「不静默出错」
            if (job && job.status === 'needs_review' && job.review) {
                showProgress(false);
                if (window.ReconReview) {
                    window.ReconReview.show(job.review, {
                        token: token, lang: lang, jobId: sub.job_id,
                        onConfirmed: async function (newJobId) {
                            showProgress(true);
                            const j2 = await window._reconPollJob(newJobId, token, {
                                onProgress: (p) => { if (_subEl) _subEl.textContent = window._reconProgressText(p, lang); },
                            });
                            await _processBankJob(j2);
                        },
                    });
                } else {
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                }
                return;
            }
            // BUG-FIX-RECON-GLCSV · 连表格结构都没读出(PDF/OCR 失败 / 空 / 损坏 / 0 行)→ 明确失败,
            //   不再静默"完成"。按 error_code 给 4 语友好原因 + 引导(换清晰文件 / 转 Excel·CSV / 重传)。
            if (job && job.status === 'failed') {
                showProgress(false);
                showError(_brv2FailMsg(job.error_code, lang));
                return;
            }
            await _processBankJob(job);

            // 轮询完成后:取结果 + 渲染(初次 + S8 确认重对账共用)
            async function _processBankJob(job) {
              try {
                if (!job || job.status !== 'done' || !job.result_id) {
                    showProgress(false);
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                    return;
                }
                // 用 result_id 调现有结果接口(GET 已补齐顶层 stats/parse_info/warnings · 与同步跑同源)
                const res = await fetch('/api/recon/bank-v2/' + encodeURIComponent(job.result_id), {
                    headers: { 'Authorization': 'Bearer ' + token },
                });
                let data = null;
                try { data = await res.json(); } catch (_) { data = null; }
                if (!res.ok || data === null || !data.ok) {
                    showProgress(false);
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                    return;
                }

                // 多账户文件:GET 不回传 gl_accounts 列表 · 单账户(绝大多数)无影响
                if ((data.gl_accounts || []).length > 1) {
                    populateAcctSelect(data.gl_accounts);
                }

                _currentTask   = data;
                _allRows       = data.detail || [];
                _currentFilter = 'all';
                document.querySelectorAll('.brv2-filter-btn').forEach(b =>
                    b.classList.toggle('active', b.dataset.filter === 'all')
                );

                // P0.1 BUG-B-T1 v118.35.0.37 · 后端总是落 summary._anchor_ocr · 存到 localStorage
                //   下次进对账 tab 自动预填 3 个 input · 不让用户从零填
                _brv2SaveLastAnchorOcr(data && data.summary);

                showProgress(false);
                renderResults(data);
                loadHistory();
                const sc = $('brv2-summary-collapse');
                if (sc) sc.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
              } catch (e) {
                showProgress(false);
                showError(e.message || 'Network error');
              }
            }

        } catch (e) {
            showError(e.message || 'Network error');
        }
    }

    function populateAcctSelect(accounts) {
        const sel = $('brv2-acct-select');
        if (!sel) return;
        const _al = window._currentLang || 'zh';
        const _allAcctLbl = { zh: '全部账户', th: 'ทุกบัญชี', en: 'All Accounts', ja: 'すべての口座' }[_al] || '全部账户';
        sel.innerHTML = `<option value="">${_allAcctLbl}</option>` +
            accounts.map(a => `<option value="${esc2(a)}">${esc2(a)}</option>`).join('');
        sel.style.display = '';
    }

    // ── 显示/隐藏结果折叠区 ──────────────────────────────────────────
    function showResultSections(show) {
        const sc = $('brv2-summary-collapse');
        const dc = $('brv2-detail-collapse');
        const eb = $('brv2-export-btn');
        const nb = $('brv2-new-btn');
        const pi = $('brv2-parse-info-wrap');
        if (sc) sc.style.display = show ? '' : 'none';
        if (dc) dc.style.display = show ? '' : 'none';
        if (eb) eb.style.display = show ? '' : 'none';
        if (nb) nb.style.display = show ? '' : 'none';
        if (!show && pi) pi.style.display = 'none';
        // v118.35.0.56 · 重置时一并清掉警告条(不匹配/跳过提示)· 防残留误导
        const wn = $('brv2-warnings');
        if (!show && wn) { wn.style.display = 'none'; wn.innerHTML = ''; }
    }

    // ── 文件解析诊断表 ────────────────────────────────────────────────
    function renderParseInfo(data) {
        const wrap = $('brv2-parse-info-wrap');
        const body = $('brv2-parse-info-body');
        if (!wrap || !body) return;
        const pi = data.parse_info;
        if (!pi) { wrap.style.display = 'none'; return; }

        const lang = window._currentLang || 'zh';
        const L = {
            title:  {zh:'文件解析状态', th:'สถานะการอ่านไฟล์', en:'File Parse Status', ja:'ファイル解析状態'},
            type:   {zh:'类型', th:'ประเภท', en:'Type', ja:'種別'},
            file:   {zh:'文件名', th:'ชื่อไฟล์', en:'File', ja:'ファイル'},
            rows:   {zh:'解析行数', th:'แถวที่พบ', en:'Rows Found', ja:'解析行数'},
            bank:   {zh:'银行/科目', th:'ธนาคาร/บัญชี', en:'Bank/Account', ja:'銀行/科目'},
            status: {zh:'状态', th:'สถานะ', en:'Status', ja:'状態'},
            stmt:   {zh:'账单', th:'บัญชีธนาคาร', en:'Stmt', ja:'明細'},
            gl:     {zh:'总账GL', th:'GL', en:'GL', ja:'GL'},
            ok:     {zh:'✓ 成功', th:'✓ สำเร็จ', en:'✓ OK', ja:'✓ 成功'},
            warn:   {zh:'⚠ 0行', th:'⚠ 0 แถว', en:'⚠ 0 rows', ja:'⚠ 0行'},
            fail:   {zh:'✗ 失败', th:'✗ ล้มเหลว', en:'✗ Failed', ja:'✗ 失敗'},
        };
        const t = k => (L[k] || {})[lang] || (L[k] || {}).zh || k;

        const rows = [
            ...(pi.stmt_files || []).map(f => ({...f, _type:'stmt', _extra: f.bank_code||''})),
            ...(pi.gl_files   || []).map(f => ({...f, _type:'gl',   _extra: (f.accounts||[]).join(', ')})),
        ];

        // v118.35.0.19 · 错误提示词翻译层:把后端 raw 技术错误翻译成用户能懂的话(4 语)
        const _ERR_MAP = {
            stmt_headers_not_found: {zh:'认不出表头列 · 请确认文件含日期/金额/余额列',
                                     th:'หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ',
                                     en:'Cannot detect column headers · ensure file has date/amount/balance columns',
                                     ja:'列ヘッダーが認識できません · 日付/金額/残高列を確認してください'},
            stmt_no_rows: {zh:'文件里没有交易数据 · 请确认上传了正确的银行流水',
                           th:'ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง',
                           en:'No transaction rows found · please check the file',
                           ja:'取引データが見つかりません · ファイルを確認してください'},
            file_not_supported: {zh:'不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV',
                                 th:'ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV',
                                 en:'File type not supported · please upload PDF / image / Excel / CSV',
                                 ja:'このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード'},
            file_unreadable: {zh:'文件无法读取 · 可能已损坏或被加密',
                              th:'อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส',
                              en:'File cannot be read · may be corrupted or encrypted',
                              ja:'ファイルを読み取れません · 破損または暗号化の可能性'},
            ocr_failed: {zh:'文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传',
                         th:'อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF',
                         en:'Could not read file · try a clearer version or upload as PDF',
                         ja:'読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行'},
            gl_headers_not_found: {zh:'认不出总账表头 · 请确认文件含科目/借方/贷方列',
                                   th:'หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต',
                                   en:'Cannot detect GL column headers · ensure account/debit/credit columns exist',
                                   ja:'GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください'},
        };
        // raw error → error_code 正则映射(后端老路径未带 code 时兜底)
        const _rawToCode = raw => {
            const r = String(raw || '');
            if (/Cannot detect bank statement column headers/i.test(r)) return 'stmt_headers_not_found';
            if (/Cannot detect GL column headers/i.test(r)) return 'gl_headers_not_found';
            if (/No transaction rows found|no pages parsed/i.test(r)) return 'stmt_no_rows';
            if (/unsupported format/i.test(r)) return 'file_not_supported';
            if (/Cannot read Excel|file_unreadable/i.test(r)) return 'file_unreadable';
            if (/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(r)) return 'ocr_failed';
            return null;
        };
        const _humanizeReconError = (row) => {
            const code = row.error_code || _rawToCode(row.error);
            if (code && _ERR_MAP[code]) {
                const lng = window._currentLang || 'zh';
                return _ERR_MAP[code][lng] || _ERR_MAP[code].zh;
            }
            // 无法翻译 → 用通用 + 截断 raw(供技术支持参考)
            return String(row.error || '').slice(0, 80);
        };

        const statusCell = row => {
            if (!row.ok && row.error)
                return `<span style="color:#dc2626">${t('fail')} — ${esc2(_humanizeReconError(row))}</span>`;
            if (!row.rows)
                return `<span style="color:#d97706">${t('warn')}</span>`;
            return `<span style="color:#059669">${t('ok')} (${row.rows})</span>`;
        };

        body.innerHTML = `
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${t('title')}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('type')}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${t('file')}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${t('rows')}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('bank')}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('status')}</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(row => `<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${row._type==='stmt'?t('stmt'):t('gl')}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc2(row.file||'')}">${esc2(row.file||'')}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${row.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${esc2(row._extra||'')}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${statusCell(row)}</td>
                    </tr>`).join('')}
                </tbody>
            </table>`;
        wrap.style.display = '';
    }

    // ── Export helper (fetch+blob so Auth header is sent) ─────────────
    async function _brv2Export(taskId) {
        const token = localStorage.getItem('mrpilot_token') || '';
        const l = window._currentLang || 'zh';
        try {
            const resp = await fetch('/api/recon/bank-v2/' + taskId + '/export?lang=' + l, {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                if (window.showToast) window.showToast(err.detail || 'Export failed', 'error');
                return;
            }
            const blob = await resp.blob();
            const cd = resp.headers.get('content-disposition') || '';
            const m  = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            const filename = m ? m[1].replace(/['"]/g, '') : 'reconciliation.xlsx';
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = filename;
            document.body.appendChild(a); a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (e) {
            if (window.showToast) window.showToast('Export error: ' + e.message, 'error');
        }
    }

    // ── Render results ────────────────────────────────────────────────
    // v118.35.0.54 · 输入不匹配 / 跳过文件 警告条(期间/规模对不上 · 不让用户看不懂差额)
    function _brv2RenderWarnings(warnings, skipped) {
        const host = $('brv2-summary-collapse');
        let box = $('brv2-warnings');
        const _l = window._currentLang || 'zh';
        const skipLbl = { zh: '⏭ 已跳过无法识别的文件:', th: '⏭ ข้ามไฟล์ที่อ่านไม่ได้:',
                          en: '⏭ Skipped unreadable file:', ja: '⏭ 読み取れないファイルをスキップ:' }[_l] || '⏭ ';
        const msgs = [];
        (skipped || []).forEach(fn => msgs.push(skipLbl + ' ' + fn));
        (warnings || []).forEach(w => msgs.push(w));
        if (!msgs.length) { if (box) box.style.display = 'none'; return; }
        if (!box) {
            box = document.createElement('div');
            box.id = 'brv2-warnings';
            if (host && host.parentNode) host.parentNode.insertBefore(box, host);
            else return;
        }
        box.style.cssText = 'display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;' +
            'border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6';
        box.innerHTML = msgs.map(m => '<div>' + esc2(m) + '</div>').join('');
    }

    function renderResults(data) {
        // Always render parse diagnostics (shown on both success and failure)
        renderParseInfo(data);
        // v118.35.0.54 · 输入不匹配 / 跳过文件 警告条
        _brv2RenderWarnings(data.warnings || [], data.skipped_files || []);

        // If parse failed, show error toast but still display the diagnostics panel
        if (!data.ok && data.error) {
            if (window.showToast) window.showToast(data.error, 'error');
        }

        const stats   = data.stats   || {};
        const summary = data.summary || {};

        const matched  = stats.matched || 0;
        const glOnly   = (stats.gl_debit_only || 0) + (stats.gl_credit_only || 0);
        const stmtOnly = (stats.stmt_withdrawal_only || 0) + (stats.stmt_deposit_only || 0);
        const fdiff    = Number(summary.formula_diff || 0);
        const diffOk   = Math.abs(fdiff) < 0.05;

        // KPI strip (3 cards)
        if ($('brv2-kpi-matched'))   $('brv2-kpi-matched').textContent   = matched;
        if ($('brv2-kpi-diff'))      $('brv2-kpi-diff').textContent      = fmtNum(fdiff);
        if ($('brv2-kpi-unmatched')) $('brv2-kpi-unmatched').textContent = glOnly + stmtOnly;
        // 差额图标颜色
        const diffIcon = $('brv2-kpi-diff-icon');
        if (diffIcon) {
            diffIcon.style.background = diffOk ? '#d1fae5' : '#fee2e2';
            diffIcon.style.color      = diffOk ? '#065f46' : '#b91c1c';
        }

        // Formula collapse 小标题
        const formulaSub = $('brv2-formula-sub');
        if (formulaSub) {
            const _fl = window._currentLang || 'zh';
            formulaSub.textContent = diffOk
                ? { zh: '✓ 平衡', th: '✓ สมดุล', en: '✓ Balanced', ja: '✓ 一致' }[_fl] || '✓ 平衡'
                : ({ zh: '差 ', th: 'ต่าง ', en: 'Diff ', ja: '差 ' }[_fl] || '差 ') + fmtNum(fdiff);
        }

        // Detail collapse 小标题
        const detailSub = $('brv2-detail-sub');
        if (detailSub) {
            const _dl = window._currentLang || 'zh';
            const _rowLbl = { zh: '共 {n} 行', th: 'ทั้งหมด {n} แถว', en: '{n} rows', ja: '計 {n} 行' }[_dl] || '共 {n} 行';
            detailSub.textContent = _rowLbl.replace('{n}', _allRows.length);
        }

        // 公式表
        function setFrm(id, val, neg) {
            const el = $(id);
            if (!el) return;
            el.textContent = (neg && val > 0 ? '(' : '') + fmtNum(neg ? -val : val) + (neg && val > 0 ? ')' : '');
        }
        setFrm('brf-gl-close',      summary.gl_closing             || 0);
        setFrm('brf-open-diff',     summary.opening_diff           || 0);
        setFrm('brf-gl-debit-only', summary.gl_debit_only_amount   || 0, true);
        setFrm('brf-gl-credit-only',summary.gl_credit_only_amount  || 0);
        setFrm('brf-stmt-wd-only',  summary.stmt_withdrawal_only_amount || 0, true);
        setFrm('brf-stmt-dep-only', summary.stmt_deposit_only_amount    || 0);
        setFrm('brf-calc-close',    summary.formula_stmt_closing   || 0);
        setFrm('brf-stmt-close',    summary.stmt_closing           || 0);
        if ($('brf-diff')) {
            $('brf-diff').textContent = fmtNum(fdiff);
        }

        // 差额卡片颜色 (v118.33.12.0 · 横向公式卡片)
        const diffCell = $('brv2-fcell-diff');
        if (diffCell) {
            diffCell.classList.toggle('brv2-fcell-diff-ok', diffOk);
        }

        // 导出按钮事件
        const exportBtn = $('brv2-export-btn');
        if (exportBtn) {
            exportBtn.onclick = () => {
                if (!_currentTask) return;
                _brv2Export(_currentTask.task_id);
            };
        }

        // P0.3 BUG-B-T3 v118.35.0.39 · 渲染 anchor 手动录入对照(只在 summary._anchor_overrides 非空时显示)
        _brv2RenderAnchorAudit(summary);

        showResultSections(true);
        renderTable();
    }

    function renderTable() {
        const tbody = $('brv2-tbody');
        if (!tbody) return;

        const rows = _allRows.filter(r => {
            if (_currentFilter === 'all')     return true;
            if (_currentFilter === 'matched') return r.match_status === 'matched';
            if (_currentFilter === 'gl_only') return r.match_status.startsWith('gl_');
            if (_currentFilter === 'stmt_only') return r.match_status.startsWith('stmt_');
            return true;
        });

        if (rows.length === 0) {
            const noRows = { zh: '无记录', th: 'ไม่มีรายการ', en: 'No rows', ja: '行なし' }[window._currentLang || 'zh'] || '无记录';
            tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${noRows}</td></tr>`;
            return;
        }

        const _lang2 = window._currentLang || 'zh';
        const T_OCR_WARN_BAL = { zh: 'OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF',
                                 th: 'การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ',
                                 en: 'Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF',
                                 ja: '残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください' }[_lang2];
        const T_OCR_LOW_CONF = { zh: 'OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF',
                                 th: 'OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ',
                                 en: 'OCR low confidence · digit was blurry or hard to read — verify against the original PDF',
                                 ja: 'OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください' }[_lang2];

        tbody.innerHTML = rows.map(r => {
            const st = r.match_status;
            const layer = r.match_layer;

            let rowClass = '';
            let badge = '';
            if (st === 'matched') {
                if (layer === 1) { rowClass = 'matched';    badge = '<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'; }
                if (layer === 2) { rowClass = 'matched-l2'; badge = '<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'; }
                if (layer === 3) { rowClass = 'matched-l3'; badge = '<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>'; }
            } else if (st === 'gl_debit_only' || st === 'gl_credit_only') {
                rowClass = 'gl-only';
                badge = '<span class="brv2-status-badge brv2-badge-gl-only">GL</span>';
            } else {
                rowClass = 'stmt-only';
                const stmtLbl = { zh: '账单', th: 'บัญชี', en: 'Stmt', ja: '明細' }[_lang2] || '账单';
                badge = `<span class="brv2-status-badge brv2-badge-stmt-only">${stmtLbl}</span>`;
            }

            // v118.33.13.0 · OCR accuracy warning icons (balance check, confidence)
            let warnIcons = '';
            if (r.stmt_balance_ok === false) {
                warnIcons += `<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${esc2(T_OCR_WARN_BAL)}">⚠</span>`;
                rowClass += ' brv2-row-warn';
            }
            if (r.stmt_confidence === 'low') {
                warnIcons += `<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${esc2(T_OCR_LOW_CONF)}">◌</span>`;
                if (!rowClass.includes('brv2-row-warn')) rowClass += ' brv2-row-warn-soft';
            }

            return `<tr class="${rowClass.trim()}">
              <td>${badge}${warnIcons}</td>
              <td>${esc2(fmtDate(r.stmt_date))}</td>
              <td title="${esc2(r.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc2(r.stmt_desc)}</td>
              <td class="num">${r.stmt_withdrawal ? fmtNum(r.stmt_withdrawal) : ''}</td>
              <td class="num">${r.stmt_deposit    ? fmtNum(r.stmt_deposit)    : ''}</td>
              <td>${esc2(fmtDate(r.gl_date))}</td>
              <td title="${esc2(r.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc2(r.gl_doc_no)}</td>
              <td class="num">${r.gl_debit  ? fmtNum(r.gl_debit)  : ''}</td>
              <td class="num">${r.gl_credit ? fmtNum(r.gl_credit) : ''}</td>
              <td>${layer ? 'L' + layer : '—'}</td>
            </tr>`;
        }).join('');
    }

    // ── History ───────────────────────────────────────────────────────
    async function loadHistory() {
        const token = localStorage.getItem('mrpilot_token') || '';
        try {
            const res  = await fetch('/api/recon/bank-v2/tasks', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const data = await res.json();
            renderHistory(data.tasks || []);
        } catch (e) {
            const emptyEl = $('brv2-history-empty');
            const lang = window._currentLang || 'zh';
            const errMsg = { zh: '加载失败', th: 'โหลดประวัติไม่ได้', en: 'Load failed', ja: '読み込み失敗' }[lang] || '加载失败';
            if (emptyEl) { emptyEl.textContent = errMsg; emptyEl.style.display = ''; }
            const wrap = $('brv2-history-table-wrap');
            if (wrap) wrap.style.display = 'none';
        }
    }

    const BRV2_PAGE_SIZE = 10;
    let _brv2Page = 1;

    function _brv2RenderPager() {
        const pager = $('brv2-history-pager');
        const info  = $('brv2-history-pager-info');
        const prev  = $('brv2-history-prev');
        const next  = $('brv2-history-next');
        if (!pager) return;
        if (_cachedHistoryTasks.length <= BRV2_PAGE_SIZE) { pager.style.display = 'none'; return; }
        pager.style.display = '';
        const totalPages = Math.ceil(_cachedHistoryTasks.length / BRV2_PAGE_SIZE);
        if (info) info.textContent = _brv2Page + ' / ' + totalPages;
        if (prev) prev.disabled = _brv2Page <= 1;
        if (next) next.disabled = _brv2Page >= totalPages;
    }

    function _brv2InitPager() {
        const prev = $('brv2-history-prev');
        const next = $('brv2-history-next');
        if (prev && !prev._brv2Bound) {
            prev._brv2Bound = true;
            prev.addEventListener('click', () => { if (_brv2Page > 1) { _brv2Page--; renderHistory(_cachedHistoryTasks); } });
        }
        if (next && !next._brv2Bound) {
            next._brv2Bound = true;
            next.addEventListener('click', () => {
                const totalPages = Math.ceil(_cachedHistoryTasks.length / BRV2_PAGE_SIZE);
                if (_brv2Page < totalPages) { _brv2Page++; renderHistory(_cachedHistoryTasks); }
            });
        }
    }

    function renderHistory(tasks) {
        if (tasks !== undefined) { _cachedHistoryTasks = tasks || []; _brv2Page = 1; }
        const all     = _cachedHistoryTasks;
        const emptyEl = $('brv2-history-empty');
        const wrap    = $('brv2-history-table-wrap');
        const tbody   = $('brv2-history-tbody');
        if (!tbody) return;

        const lang = window._currentLang || 'zh';
        if (!all.length) {
            const emptyTxt = { zh: '暂无对账记录', th: 'ยังไม่มีประวัติ', en: 'No records yet', ja: '記録なし' }[lang] || '暂无对账记录';
            if (emptyEl) { emptyEl.textContent = emptyTxt; emptyEl.style.display = ''; }
            if (wrap) wrap.style.display = 'none';
            _brv2RenderPager();
            return;
        }
        if (emptyEl) emptyEl.style.display = 'none';
        if (wrap) wrap.style.display = '';
        const totalPages = Math.ceil(all.length / BRV2_PAGE_SIZE);
        if (_brv2Page > totalPages) _brv2Page = totalPages;
        const start = (_brv2Page - 1) * BRV2_PAGE_SIZE;
        const tasks_page = all.slice(start, start + BRV2_PAGE_SIZE);

        const token = localStorage.getItem('mrpilot_token') || '';
        const SVG_LOAD = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>';
        const SVG_DL   = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>';
        const SVG_DEL  = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';

        tbody.innerHTML = '';
        tasks_page.forEach(t => {
            const diff   = Number(t.formula_diff || 0);
            const diffOk = Math.abs(diff) < 0.05;
            const stmtF  = (t.stmt_files || '').split(';').map(s => s.trim().split(/[/\\]/).pop()).filter(Boolean).join(', ');
            const glF    = (t.gl_files   || '').split(';').map(s => s.trim().split(/[/\\]/).pop()).filter(Boolean).join(', ');
            const dt     = t.created_at ? String(t.created_at).slice(0, 16).replace('T', ' ') : '';

            const tr = document.createElement('tr');
            tr.dataset.taskId = t.id;

            const tdTime = document.createElement('td');
            tdTime.textContent = dt;

            const tdFiles = document.createElement('td');
            tdFiles.className = 'glv-history-file';
            tdFiles.title = stmtF + ' + ' + glF;
            tdFiles.textContent = stmtF + ' + ' + glF;

            const tdRows = document.createElement('td');
            tdRows.className = 'glv-num';
            tdRows.textContent = (t.stmt_row_count || 0) + ' / ' + (t.gl_row_count || 0);

            const tdMatched = document.createElement('td');
            tdMatched.className = 'glv-num';
            tdMatched.textContent = t.matched_count || 0;

            const tdGlOnly = document.createElement('td');
            tdGlOnly.className = 'glv-num';
            tdGlOnly.textContent = (t.unmatched_gl || 0);

            const tdStmtOnly = document.createElement('td');
            tdStmtOnly.className = 'glv-num';
            tdStmtOnly.textContent = (t.unmatched_stmt || 0);

            const tdDiff = document.createElement('td');
            tdDiff.className = 'glv-num';
            tdDiff.style.color = diffOk ? '#059669' : '#dc2626';
            tdDiff.textContent = diffOk ? '✓' : fmtNum(diff);

            const tdAct = document.createElement('td');
            tdAct.className = 'glv-history-actions';
            const mkBtn = (svg, title, cls, onClick) => {
                const b = document.createElement('button');
                b.type = 'button'; b.title = title; b.setAttribute('aria-label', title);
                if (cls) b.className = cls;
                b.innerHTML = svg;
                b.onclick = e => { e.stopPropagation(); onClick(); };
                return b;
            };
            const delConfirm = { zh: '删除这条记录?', th: 'ลบรายการนี้?', en: 'Delete this record?', ja: 'この記録を削除しますか?' }[lang] || '删除?';
            const lblLoad = { zh: '加载', th: 'โหลด', en: 'Load', ja: '読込' }[lang] || '加载';
            const lblExp  = { zh: '导出', th: 'ส่งออก', en: 'Export', ja: 'エクスポート' }[lang] || '导出';
            const lblDel  = { zh: '删除', th: 'ลบ', en: 'Delete', ja: '削除' }[lang] || '删除';
            tdAct.appendChild(mkBtn(SVG_LOAD, lblLoad, '', () => loadTask(t.id, token)));
            tdAct.appendChild(mkBtn(SVG_DL,   lblExp,  '', () => _brv2Export(t.id)));
            tdAct.appendChild(mkBtn(SVG_DEL,  lblDel,  'glv-del', async () => {
                if (!(await showConfirm(delConfirm, { danger: true }))) return;
                await fetch('/api/recon/bank-v2/' + t.id, { method: 'DELETE', headers: { 'Authorization': 'Bearer ' + token } });
                loadHistory();
            }));

            [tdTime, tdFiles, tdRows, tdMatched, tdGlOnly, tdStmtOnly, tdDiff, tdAct].forEach(c => tr.appendChild(c));
            tr.style.cursor = 'pointer';
            tr.addEventListener('click', async (e) => {
                if (e.target.closest('.glv-del') || e.target.closest('button')) return;
                await loadTask(t.id, token);
            });
            tbody.appendChild(tr);
        });
        _brv2RenderPager();
        _applyBrv2Search();
    }

    function _applyBrv2Search() {
        const q = (($('brv2-hist-search') || {}).value || '').trim().toLowerCase();
        const tbody = $('brv2-history-tbody');
        if (!tbody) return;
        tbody.querySelectorAll('tr').forEach(tr => {
            if (!tr.dataset.taskId) return;
            tr.style.display = (!q || tr.textContent.toLowerCase().includes(q)) ? '' : 'none';
        });
    }

    async function loadTask(taskId, token) {
        try {
            const res  = await fetch('/api/recon/bank-v2/' + taskId, {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const data = await res.json();
            if (!data.ok) return;
            _currentTask   = { task_id: data.task_id, ...data };
            _allRows       = data.detail || [];
            _currentFilter = 'all';
            // 重置 filter tab 到 "all"
            document.querySelectorAll('.brv2-filter-btn').forEach(b =>
                b.classList.toggle('active', b.dataset.filter === 'all')
            );
            renderResults(_currentTask);
        } catch (e) { /* silent */ }
    }

    // ── Init ──────────────────────────────────────────────────────────
    function init() {
        if (_initialized) {
            // 二次进入只刷历史
            loadHistory();
            return;
        }
        _initialized = true;

        setupDrop('brv2-stmt-zone', 'brv2-stmt-input', 'stmt');
        setupDrop('brv2-gl-zone',   'brv2-gl-input',   'gl');

        // BUG-B v118.35.0.36 · 3 个 anchor 余额手动录入 · 实时算期初差额
        const anchorIds = ['brv2-anchor-gl-closing', 'brv2-anchor-stmt-closing', 'brv2-anchor-stmt-opening', 'brv2-anchor-gl-opening'];
        function _brv2UpdateAnchorEq() {
            const stmtOpen = parseFloat(($('brv2-anchor-stmt-opening') || {}).value);
            const glOpen   = parseFloat(($('brv2-anchor-gl-opening')   || {}).value);
            const eq       = $('brv2-anchor-eq');
            const eqVal    = $('brv2-anchor-eq-val');
            if (!eq || !eqVal) return;
            if (Number.isFinite(stmtOpen) && Number.isFinite(glOpen)) {
                const diff = stmtOpen - glOpen;
                eqVal.textContent = diff.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                eq.style.display = '';
            } else {
                eq.style.display = 'none';
            }
        }
        anchorIds.forEach(id => {
            const el = $(id);
            if (!el) return;
            el.addEventListener('input', _brv2UpdateAnchorEq);
            // P0.1 BUG-B-T1 v118.35.0.37 · 用户敲一个字 = 真用户输入 · 移除 prefilled 灰字态
            // BUG-FIX-T4 v118.35.0.45 · 同时检查 banner 是否还要显示(全 cell 都被用户改 → 隐藏 banner)
            el.addEventListener('input', () => {
                const cell = el.closest('.brv2-anchor-cell');
                if (cell) cell.classList.remove('is-prefilled');
                _brv2UpdatePrefillBannerVisibility();
            });
        });

        // P0.1 BUG-B-T1 v118.35.0.37 · 进 tab 时用上次 OCR 抽到的 3 anchor 值预填 input
        _brv2RestoreAnchorPrefill();

        const runBtn = $('brv2-run-btn');
        if (runBtn) runBtn.addEventListener('click', runRecon);

        // 清空按钮
        const resetBtn = $('brv2-reset-btn');
        if (resetBtn) resetBtn.addEventListener('click', () => {
            _currentTask   = null;
            _allRows       = [];
            _stmtFiles     = [];
            _glFiles       = [];
            renderFileList('stmt');
            renderFileList('gl');
            updateRunBtn();
            showResultSections(false);
            // 重置 acct select
            const sel = $('brv2-acct-select');
            if (sel) sel.style.display = 'none';
            // BUG-B v118.35.0.36 · 重置 anchor 录入框 + 隐藏 eq 行
            // BUG-FIX-T4 v118.35.0.45 · 清空时也移除 .is-prefilled + 隐藏 banner
            anchorIds.forEach(id => {
                const el = $(id);
                if (el) {
                    el.value = '';
                    const cell = el.closest && el.closest('.brv2-anchor-cell');
                    if (cell) cell.classList.remove('is-prefilled');
                }
            });
            const eq = $('brv2-anchor-eq');
            if (eq) eq.style.display = 'none';
            const banner = $('brv2-anchor-prefill-banner');
            if (banner) banner.classList.remove('show');
        });

        // 新建按钮（在折叠头里）
        const newBtn = $('brv2-new-btn');
        if (newBtn) newBtn.addEventListener('click', () => {
            _currentTask   = null;
            _allRows       = [];
            _stmtFiles     = [];
            _glFiles       = [];
            renderFileList('stmt');
            renderFileList('gl');
            updateRunBtn();
            showResultSections(false);
        });

        // 过滤 tab（事件冒泡拦截，不触发折叠）
        const filterTabs = $('brv2-filter-tabs');
        if (filterTabs) {
            filterTabs.addEventListener('click', e => {
                e.stopPropagation(); // 防止触发 recon-collapse-head 折叠
                const btn = e.target.closest('.brv2-filter-btn');
                if (!btn) return;
                _currentFilter = btn.dataset.filter;
                filterTabs.querySelectorAll('.brv2-filter-btn').forEach(b =>
                    b.classList.toggle('active', b === btn)
                );
                renderTable();
            });
        }

        _initBrv2TogglePreview();
        _brv2InitPager();
        const hs = $('brv2-hist-search');
        if (hs) hs.addEventListener('input', _applyBrv2Search);

        loadHistory();
        updateRunBtn();
        window._brv2LoadHistory = loadHistory;

        // Subscribe to global language changes so dynamic content re-renders
        if (!Array.isArray(window.__i18nSubs)) window.__i18nSubs = [];
        window.__i18nSubs = window.__i18nSubs.filter(s => s.name !== 'brv2');
        window.__i18nSubs.push({ name: 'brv2', fn: function() {
            updateRunBtn();
            renderFileList('stmt');
            renderFileList('gl');
            if (_currentTask) renderResults(_currentTask);
            renderHistory();
        }});
    }

    // Expose load function for panel system
    window._loadBankReconV2Panel = function(containerId) {
        // Re-mount into given container if different (used by int-drawer)
        const container = containerId ? document.getElementById(containerId) : null;
        if (container && container.id !== 'recon-pane-bank') {
            container.innerHTML = `<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`;
        }
        init();
    };

    // Auto-init when pane becomes visible
    document.addEventListener('DOMContentLoaded', () => {
        // Init immediately if pane is active
        if ($('brv2-run-btn')) init();
    });

    // Also init when reconcile page is navigated to
    window._bankReconV2Init = init;

})();

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
// v109.4 · 老的管理后台模块(/admin)已删除 · 改用新的 admin-users(数据更全 · 字段对齐多租户)
// 但右上角顶栏「管理」下拉的点击事件需要单独保留
// ============================================================
(function () {
    'use strict';
    document.addEventListener('click', (e) => {
        // 1. 顶栏「管理」按钮 → 打开下拉
        const adminToggle = e.target.closest && e.target.closest('#admin-toggle');
        if (adminToggle) {
            const dd = document.getElementById('admin-dropdown');
            if (dd) dd.classList.toggle('open');
            e.stopPropagation();
            return;
        }
        // 2. 下拉里的子菜单
        const adminItem = e.target.closest && e.target.closest('[data-admin-route]');
        if (adminItem && !adminItem.disabled) {
            const sub = adminItem.dataset.adminRoute;
            const dd = document.getElementById('admin-dropdown');
            if (dd) dd.classList.remove('open');
            if (sub === 'users') {
                // v109.4 · 跳新的 admin-users 页(不再用老的 admin · 数据更全 · 字段对齐多租户)
                if (typeof routeTo === 'function') routeTo('admin-users');
            } else if (sub === 'logs') {
                // v109.4 · 操作日志暂未实现 · 提示即将推出
                if (typeof showToast === 'function' && typeof t === 'function') {
                    showToast(t('feature-coming-soon'), 'info');
                }
            }
            return;
        }
        // 3. 点其他地方关下拉
        if (!e.target.closest('#admin-dropdown')) {
            const dd = document.getElementById('admin-dropdown');
            if (dd) dd.classList.remove('open');
        }
    });
})();


// ============================================================
// v106 · 管理员成本追踪面板
// ============================================================
(function () {
    function fmt(n, decimals) {
        if (n === null || n === undefined || isNaN(n)) return '—';
        const d = decimals === undefined ? 2 : decimals;
        return Number(n).toFixed(d).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    function fmtCost(thb) {
        if (!thb || thb === 0) return '<span class="cost-money cost-money-zero">฿ 0</span>';
        return `<span class="cost-money">฿ ${fmt(thb, 4)}</span>`;
    }

    let _lastEngines = [];

    function _renderEngines(engines) {
        const engEl = document.getElementById('kpi-engines');
        if (!engEl) return;
        if (!engines || !engines.length) {
            engEl.innerHTML = '<span style="font-size:13px; color:#9ca3af;">' + t('cost-no-engines') + '</span>';
            return;
        }
        const _engNames = {
            'gemini':       t('adm-engine-ocr'),
            'google_vision':t('adm-engine-ocr-backup'),
            'text_path':    t('adm-engine-epdf'),
            'gemini-vex':   t('adm-engine-vex'),
        };
        const sorted = [...engines].sort(function(a, b) { return (b.cost_thb || 0) - (a.cost_thb || 0); });
        engEl.innerHTML = sorted.map(function(e) {
            const name = _engNames[e.engine] || e.engine;
            const cost = e.cost_thb || 0;
            const cnt  = e.count || 0;
            const avg  = cnt ? cost / cnt : 0;
            return '<div class="engine-row">'
                + '<span class="engine-name">' + name + '</span>'
                + '<span class="engine-stats">'
                + '<span class="engine-cost">฿' + fmt(cost, 4) + '</span>'
                + '<span class="engine-cnt">' + cnt + ' · avg ฿' + fmt(avg, 4) + '</span>'
                + '</span></div>';
        }).join('');
    }
    function fmtTime(iso) {
        if (!iso) return t('cost-never-used');
        const d = new Date(iso);
        const now = new Date();
        const diffMs = now - d;
        const diffMin = Math.floor(diffMs / 60000);
        if (diffMin < 1) return 'just now';
        if (diffMin < 60) return diffMin + 'min ago';
        const diffH = Math.floor(diffMin / 60);
        if (diffH < 24) return diffH + 'h ago';
        const diffD = Math.floor(diffH / 24);
        if (diffD < 7) return diffD + 'd ago';
        return d.toISOString().slice(0, 10);
    }

    async function fetchJson(path) {
        const tok = localStorage.getItem('mrpilot_token');
        const r = await fetch(path, {
            headers: { 'Authorization': 'Bearer ' + tok },
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
    }

    async function loadOverview() {
        try {
            const data = await fetchJson('/api/admin/cost/overview');
            // 今日
            document.getElementById('kpi-today-cost').textContent = '฿ ' + fmt(data.today.cost_thb || 0, 2);
            document.getElementById('kpi-today-sub').textContent =
                (data.today.invoices || 0) + ' ' + t('cost-invoices-suffix') + ' · ' +
                (data.today.pages || 0) + ' ' + t('cost-pages-suffix');
            // 本月
            document.getElementById('kpi-month-cost').textContent = '฿ ' + fmt(data.month.cost_thb || 0, 2);
            document.getElementById('kpi-month-sub').textContent =
                (data.month.invoices || 0) + ' ' + t('cost-invoices-suffix') + ' · ' +
                (data.month.pages || 0) + ' ' + t('cost-pages-suffix');
            // 累计
            document.getElementById('kpi-total-cost').textContent = '฿ ' + fmt(data.total.cost_thb || 0, 2);
            document.getElementById('kpi-total-sub').textContent =
                (data.total.invoices || 0) + ' ' + t('cost-invoices-suffix') + ' · ' +
                (data.total.pages || 0) + ' ' + t('cost-pages-suffix');
            // 引擎明细 · 缓存供切语言时重渲
            _lastEngines = data.engines || [];
            _renderEngines(_lastEngines);
        } catch (e) {
            console.error('cost overview fail', e);
            showToast(t('cost-load-fail'), 'fail');
        }
    }

    async function loadByUser() {
        const tbody = document.getElementById('cost-by-user-tbody');
        tbody.innerHTML = `<tr><td colspan="9" class="cost-table-empty">${t('cost-loading')}</td></tr>`;
        try {
            const data = await fetchJson('/api/admin/cost/by_user');
            const users = data.users || [];
            if (!users.length) {
                tbody.innerHTML = `<tr><td colspan="9" class="cost-table-empty">${t('cost-empty')}</td></tr>`;
                return;
            }
            tbody.innerHTML = users.map(u => {
                const avg = u.total_invoices ? (u.total_cost_thb / u.total_invoices) : 0;
                return `<tr>
                    <td><strong>${escapeHtml(u.username || '—')}</strong></td>
                    <td>${u.plan ? `<span class="cost-plan-badge">${escapeHtml(u.plan)}</span>` : '—'}</td>
                    <td>${fmtCost(u.today_cost_thb)}</td>
                    <td>${fmtCost(u.month_cost_thb)}</td>
                    <td>${fmtCost(u.total_cost_thb)}</td>
                    <td>${u.total_pages}</td>
                    <td>${u.total_invoices}</td>
                    <td>${avg ? '฿ ' + fmt(avg, 4) : '—'}</td>
                    <td>${fmtTime(u.last_used_at)}</td>
                </tr>`;
            }).join('');
        } catch (e) {
            console.error('cost by_user fail', e);
            tbody.innerHTML = `<tr><td colspan="9" class="cost-table-empty">${t('cost-load-fail')}</td></tr>`;
        }
    }

    async function loadTrend() {
        const wrap = document.getElementById('cost-trend-chart');
        wrap.innerHTML = `<div class="cost-trend-empty">${t('cost-loading')}</div>`;
        try {
            const data = await fetchJson('/api/admin/cost/daily_trend?days=30');
            const days = data.days || [];
            if (!days.length) {
                wrap.innerHTML = `<div class="cost-trend-empty">${t('cost-empty')}</div>`;
                return;
            }
            // 补齐 30 天(没数据的日期填 0)· 让趋势更直观
            const today = new Date();
            const map = {};
            for (const d of days) map[d.day] = d;
            const filled = [];
            for (let i = 29; i >= 0; i--) {
                const dt = new Date(today);
                dt.setDate(dt.getDate() - i);
                const key = dt.toISOString().slice(0, 10);
                filled.push({
                    day: key,
                    cost_thb: map[key] ? map[key].cost_thb : 0,
                    invoices: map[key] ? map[key].invoices : 0,
                    pages: map[key] ? map[key].pages : 0,
                });
            }
            // 渲染纯 SVG 柱状图
            const W = 800, H = 200, PAD = 30;
            const innerW = W - PAD * 2;
            const innerH = H - PAD;
            const maxCost = Math.max(...filled.map(d => d.cost_thb), 0.01);
            const barW = innerW / filled.length * 0.7;
            const gap = innerW / filled.length * 0.3;
            const bars = filled.map((d, i) => {
                const x = PAD + (innerW / filled.length) * i + gap / 2;
                const h = (d.cost_thb / maxCost) * innerH;
                const y = H - h - PAD / 2;
                return `<rect class="trend-bar" x="${x.toFixed(1)}" y="${y.toFixed(1)}" 
                              width="${barW.toFixed(1)}" height="${h.toFixed(1)}" rx="2">
                    <title>${d.day}: ฿${d.cost_thb.toFixed(4)} · ${d.invoices} ${t('cost-invoices-suffix')}</title>
                </rect>`;
            }).join('');
            // x 轴 5 个标签
            const tickIdx = [0, 7, 14, 21, 29];
            const xLabels = tickIdx.map(i => {
                const x = PAD + (innerW / filled.length) * i + barW / 2 + gap / 2;
                const day = filled[i].day.slice(5); // MM-DD
                return `<text class="trend-label" x="${x.toFixed(1)}" y="${H - 4}" text-anchor="middle">${day}</text>`;
            }).join('');
            // y 轴 max 标签
            const yMaxLabel = `<text class="trend-label" x="${PAD - 4}" y="${PAD / 2 + 4}" text-anchor="end">฿ ${maxCost.toFixed(2)}</text>`;
            const yMidLabel = `<text class="trend-label" x="${PAD - 4}" y="${PAD / 2 + innerH / 2 + 4}" text-anchor="end">฿ ${(maxCost / 2).toFixed(2)}</text>`;
            // 底线
            const baseline = `<line class="trend-axis" x1="${PAD}" y1="${H - PAD / 2}" x2="${W - PAD}" y2="${H - PAD / 2}"/>`;
            wrap.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
                ${baseline}${bars}${xLabels}${yMaxLabel}${yMidLabel}
            </svg>`;
        } catch (e) {
            console.error('cost trend fail', e);
            wrap.innerHTML = `<div class="cost-trend-empty">${t('cost-load-fail')}</div>`;
        }
    }

    async function exportCsv() {
        try {
            const tok = localStorage.getItem('mrpilot_token');
            const resp = await fetch('/api/admin/cost/export?days=30', {
                headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mrpilot_cost_${new Date().toISOString().slice(0,10)}.csv`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error('export fail', e);
            showToast(t('cost-export-fail'), 'fail');
        }
    }

    window.loadAdminCostPage = function () {
        loadOverview();
        loadByUser();
        loadTrend();
    };

    // 切语言时重渲引擎明细(无需重新 fetch)
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('admin-cost-engines', function () {
            _renderEngines(_lastEngines);
        });
    }

    // 绑定按钮
    document.addEventListener('DOMContentLoaded', () => {
        const refreshBtn = document.getElementById('btn-cost-refresh');
        if (refreshBtn) refreshBtn.addEventListener('click', () => window.loadAdminCostPage());
        const exportBtn = document.getElementById('btn-cost-export');
        if (exportBtn) exportBtn.addEventListener('click', exportCsv);
    });
})();





// ============================================================
// v109.1 END
// ============================================================

// ============================================================
// v109.3 · 商业模式 · 套餐 + 防薅 + 升级弹窗 + LINE 绑定
// ============================================================
(function() {
    'use strict';

    let _planState = null;

    // ===== i18n 注入 =====
    const V109_3_I18N = {
        zh: {
            'plan-trial': '试用', 'plan-free': '免费版', 'plan-pro': 'Pro', 'plan-firm': 'Firm', 'plan-enterprise': '企业版',
            'banner-trial-left': '试用还剩 {n} 天 · {used}/{limit} 张',
            'banner-trial-last': '试用今天到期 · 立即升级保留数据',
            'banner-trial-expiring': '试用还剩 {n} 天 · 立即升级保留数据',
            'banner-trial-needs-line': '试用 · 绑定 LINE 解锁完整 50 张',
            'banner-free': '免费版 · 本月 {used}/{limit} 张',
            'banner-free-needs-line': '免费版 · 绑定 LINE 解锁 10 张/月',
            'banner-pro': 'Pro · 还剩 {n} 天 · {used}/{limit} 张',
            'banner-firm': 'Firm · 还剩 {n} 天',
            'banner-monthly': '月付 · 还剩 {n} 天 · {used}/{limit} 张',
            'banner-yearly':  '年付 · 还剩 {n} 天 · {used}/{limit} 张',
            'btn-renew': '续费',
            'banner-locked': '账号已封停: {reason}',
            'btn-upgrade': '升级',
            'btn-link-line': '绑定 LINE',
            // 升级弹窗
            'upg-title': '升级套餐',
            'upg-sub': '选择适合您的套餐 · 立即解锁全部功能',
            'upg-pro-tagline': '个人会计 / 小事务所',
            'upg-firm-tagline': '专业事务所 · 多用户协作',
            'upg-recommended': '推荐',
            'upg-monthly': '/月',
            'upg-feat-ocr': 'OCR · {n} 张/月',
            'upg-feat-ocr-unlim': 'OCR · 无限',
            'upg-feat-clients': '客户 · {n} 个',
            'upg-feat-clients-unlim': '客户 · 无限',
            'upg-feat-seats': '用户席位 · {n}',
            'upg-feat-automation': '自动化(邮件/文件夹/ERP)',
            'upg-feat-templates': '高级模板(ภ.พ.30 等)',
            'upg-feat-batch': '批量导出',
            'upg-feat-line': 'LINE Bot 集成',
            'upg-pick-pro': '选择 Pro',
            'upg-pick-firm': '选择 Firm',
            // 付款
            'pay-title': '付款 · {plan}',
            'pay-amount': '请转账 ฿{n}',
            'pay-step1': '步骤 1 · 转账',
            'pay-bank-row': 'Kasikorn Bank · 011-1-83212-9',
            'pay-promptpay-row': 'PromptPay · +66 85-064-2609',
            'pay-step2': '步骤 2 · 上传截图',
            'pay-pick-file': '选择截图',
            'pay-payer-name': '您的姓名(可选)',
            'pay-payer-note': '备注(可选)',
            'pay-submit': '提交审核',
            'pay-submitting': '提交中...',
            'pay-back': '返回',
            'pay-line-contact': '或联系 LINE: @Pearnly',
            'pay-success': '已提交 · 5-10 分钟内审核完毕 · 我们会通过 LINE 通知您',
            'pay-fail': '提交失败',
            'pay-need-screenshot': '请上传付款截图',
            // v111.2 · 新 3 档套餐 + 终身 Gemini key
            'upg-plan-trial':     '试用',
            'upg-plan-trial-desc':    '100 张/月 · 7 天 · 3 客户 · ฿0',
            'upg-plan-monthly-desc':  '500 张/月 · 30 天 · 10 客户 · ฿299',
            'upg-plan-yearly-desc':   '1500 张/月 · 365 天 · 30 客户 · ฿2,990',
            'upg-plan-lifetime-desc': '无限 · 永久 · 自带 Gemini Key · ฿9,900',
            'upg-plan-monthly':   '月付',
            'upg-plan-yearly':    '年付',
            'upg-plan-lifetime':  '终身买断',
            'upg-monthly-tag':    '入门 · 个人会计',
            'upg-yearly-tag':     '省 {pct}% · 中小事务所',
            'upg-lifetime-tag':   '一次买断 · 自带 Gemini Key · 无限',
            'upg-lifetime-badge': '永久',
            'upg-per-month':      '/月',
            'upg-per-year':       '/年',
            'upg-once':           '一次',
            'upg-pick':           '选择',
            'upg-feat-files':     '一次最多 {n} 文件',
            'upg-feat-own-key':   '自带 Gemini API Key',
            'pay-acct-no':        '账号',
            'pay-copied':         '已复制',
            'pay-step3-key':      '步骤 3 · 填写 Gemini API Key',
            'pay-key-hint':       '终身用户需自带 Gemini Key · 在这里申请(免费):',
            'pay-need-gemini-key': '请填写有效的 Gemini API Key(以 AIza 开头)',
            'plan-changed-toast': '套餐已更新 · 配额已同步',
            'adm-slip-not-found': '截图不存在或已被删除',
            'adm-drawer-sec-actions': '快速操作',
            'adm-drawer-btn-upgrade': '修改套餐',
            'adm-drawer-btn-ban': '封禁账号',
            'adm-drawer-btn-unban': '解除封禁',
            'adm-confirm-ban': '确认封禁 {e}?该用户将无法登录',
            'adm-banned': '已封禁',
            'adm-unbanned': '已解封',
            'scanner-editor-title':   '编辑',
            'scanner-editor-confirm': '完成',
            'scanner-filter-original':'原图',
            'scanner-filter-enhance': '增强',
            'scanner-filter-bw':      '黑白',
            'scanner-filter-gray':    '灰度',
            'scanner-brightness':     '亮度',
            'scanner-contrast':       '对比',
            'scanner-readjust':       '调整边框',
            'scanner-quad-title':     '调整四角',
            'scanner-quad-cancel':    '取消',
            'scanner-quad-confirm':   '确定',
            'scanner-quad-hint':      '拖动 4 个角点 · 框选纸张范围',
            'scanner-filter-smart':   '智能高清',
            'scanner-retake':         '重拍这张',
            'scanner-rotate-left':    '左转',
            'scanner-rotate-right':   '右转',
            'scanner-crop':           '裁剪',
            'scanner-flash':          '闪光灯',
            'scanner-flash-unavailable':'此摄像头不支持闪光灯',
            'scanner-album':          '从相册选',
            // LINE 绑定
            'line-modal-title': '绑定 LINE 解锁完整功能',
            'line-modal-sub': '绑定后立即解锁:',
            'line-benefit-1': '完整 50 张 OCR(试用)/ 10 张/月(免费版)',
            'line-benefit-2': '3 个客户(试用)',
            'line-benefit-3': '每周 LINE 接收使用周报',
            'line-benefit-4': '到期前自动 LINE 提醒',
            'line-link-btn': '点击绑定 LINE',
            'line-link-success': '绑定成功 · 配额已解锁',
            // v109.4 · LINE OAuth 即将上线
            'line-coming-title': 'LINE 绑定功能即将上线',
            'line-coming-desc': '我们正在接入 LINE 官方授权 · 不久即可一键安全绑定 · 急需开通可联系我们',
            'line-coming-close': '我知道了',
            'line-link-fail': '绑定失败 · 请重试',
            'line-already-linked': '此 LINE 已绑定其他账号',
            // toast
            'toast-rate-limit': '操作过于频繁 · 请稍后再试',
            'toast-quota-exceeded': '本期配额已用完',
            'toast-needs-line': '请先绑定 LINE 解锁配额',
            'modal-close': '关闭',
        },
        en: {
            'plan-trial': 'Trial', 'plan-free': 'Free', 'plan-pro': 'Pro', 'plan-firm': 'Firm', 'plan-enterprise': 'Enterprise',
            'banner-trial-left': '{n} days left · {used}/{limit} used',
            'banner-trial-last': 'Trial expires today · upgrade to keep data',
            'banner-trial-expiring': '{n} days left · upgrade to keep your data',
            'banner-trial-needs-line': 'Trial · link LINE to unlock 50 OCRs',
            'banner-free': 'Free · {used}/{limit} used this month',
            'banner-free-needs-line': 'Free · link LINE to unlock 10 OCRs/month',
            'banner-pro': 'Pro · {n} days left · {used}/{limit}',
            'banner-firm': 'Firm · {n} days left',
            'banner-monthly': 'Monthly · {n} days left · {used}/{limit}',
            'banner-yearly':  'Yearly · {n} days left · {used}/{limit}',
            'btn-renew': 'Renew',
            'banner-locked': 'Account banned: {reason}',
            'btn-upgrade': 'Upgrade', 'btn-link-line': 'Link LINE',
            'upg-title': 'Upgrade Plan',
            'upg-sub': 'Pick the right plan · unlock all features instantly',
            'upg-pro-tagline': 'Solo accountants / small firms',
            'upg-firm-tagline': 'Pro firms · multi-user',
            'upg-recommended': 'Recommended',
            'upg-monthly': '/mo',
            'upg-feat-ocr': 'OCR · {n}/month',
            'upg-feat-ocr-unlim': 'OCR · Unlimited',
            'upg-feat-clients': '{n} clients',
            'upg-feat-clients-unlim': 'Unlimited clients',
            'upg-feat-seats': '{n} user seat(s)',
            'upg-feat-automation': 'Automation (Email/Folder/ERP)',
            'upg-feat-templates': 'Advanced templates (P.P.30 etc.)',
            'upg-feat-batch': 'Batch export',
            'upg-feat-line': 'LINE Bot integration',
            'upg-pick-pro': 'Choose Pro',
            'upg-pick-firm': 'Choose Firm',
            'pay-title': 'Payment · {plan}',
            'pay-amount': 'Transfer ฿{n}',
            'pay-step1': 'Step 1 · Transfer',
            'pay-bank-row': 'Kasikorn Bank · 011-1-83212-9',
            'pay-promptpay-row': 'PromptPay · +66 85-064-2609',
            'pay-step2': 'Step 2 · Upload screenshot',
            'pay-pick-file': 'Pick file',
            'pay-payer-name': 'Your name (optional)',
            'pay-payer-note': 'Note (optional)',
            'pay-submit': 'Submit for review',
            'pay-submitting': 'Submitting...',
            'pay-back': 'Back',
            'pay-line-contact': 'Or contact LINE: @Pearnly',
            'pay-success': 'Submitted · review in 5-10 min · we will notify via LINE',
            'pay-fail': 'Submit failed',
            'pay-need-screenshot': 'Please upload screenshot',
            // v111.2 · new 3-tier
            'upg-plan-trial':     'Trial',
            'upg-plan-trial-desc':    '100/mo · 7 days · 3 clients · ฿0',
            'upg-plan-monthly-desc':  '500/mo · 30 days · 10 clients · ฿299',
            'upg-plan-yearly-desc':   '1500/mo · 365 days · 30 clients · ฿2,990',
            'upg-plan-lifetime-desc': 'Unlimited · Forever · Own Gemini Key · ฿9,900',
            'upg-plan-monthly':   'Monthly',
            'upg-plan-yearly':    'Yearly',
            'upg-plan-lifetime':  'Lifetime',
            'upg-monthly-tag':    'Starter · Solo accountants',
            'upg-yearly-tag':     'Save {pct}% · SME firms',
            'upg-lifetime-tag':   'Pay once · Bring your own Gemini Key · Unlimited',
            'upg-lifetime-badge': 'Forever',
            'upg-per-month':      '/mo',
            'upg-per-year':       '/yr',
            'upg-once':           'one-time',
            'upg-pick':           'Choose',
            'upg-feat-files':     'Up to {n} files per upload',
            'upg-feat-own-key':   'Bring your own Gemini API Key',
            'pay-acct-no':        'Account #',
            'pay-copied':         'Copied',
            'pay-step3-key':      'Step 3 · Enter Gemini API Key',
            'pay-key-hint':       'Lifetime users bring their own Gemini key · Get one free at:',
            'pay-need-gemini-key': 'Please enter a valid Gemini API Key (starts with AIza)',
            'plan-changed-toast': 'Plan updated · quota synced',
            'adm-slip-not-found': 'Screenshot not found',
            'adm-drawer-sec-actions': 'Quick Actions',
            'adm-drawer-btn-upgrade': 'Change Plan',
            'adm-drawer-btn-ban': 'Ban Account',
            'adm-drawer-btn-unban': 'Unban',
            'adm-confirm-ban': 'Ban {e}? This user can no longer log in.',
            'adm-banned': 'Account banned',
            'adm-unbanned': 'Account unbanned',
            'scanner-editor-title':   'Edit',
            'scanner-editor-confirm': 'Done',
            'scanner-filter-original':'Original',
            'scanner-filter-enhance': 'Enhance',
            'scanner-filter-bw':      'B & W',
            'scanner-filter-gray':    'Gray',
            'scanner-brightness':     'Brightness',
            'scanner-contrast':       'Contrast',
            'scanner-readjust':       'Adjust corners',
            'scanner-quad-title':     'Adjust 4 corners',
            'scanner-quad-cancel':    'Cancel',
            'scanner-quad-confirm':   'OK',
            'scanner-quad-hint':      'Drag 4 corners · select paper area',
            'scanner-filter-smart':   'Smart HD',
            'scanner-retake':         'Retake',
            'scanner-rotate-left':    'Rotate L',
            'scanner-rotate-right':   'Rotate R',
            'scanner-crop':           'Crop',
            'scanner-flash':          'Flash',
            'scanner-flash-unavailable':'Flash not supported on this camera',
            'scanner-album':          'From album',
            'line-modal-title': 'Link LINE to unlock full features',
            'line-modal-sub': 'After linking you will get:',
            'line-benefit-1': 'Full 50 OCRs (trial) / 10 OCRs/mo (free)',
            'line-benefit-2': '3 clients (trial)',
            'line-benefit-3': 'Weekly usage report via LINE',
            'line-benefit-4': 'Auto reminder before plan expires',
            'line-link-btn': 'Click to link LINE',
            'line-link-success': 'Linked · quota unlocked',
            // v109.4 · LINE OAuth coming soon
            'line-coming-title': 'LINE Binding · Coming Soon',
            'line-coming-desc': 'We\'re integrating LINE official login · secure one-tap binding will be available shortly · Contact us for early access',
            'line-coming-close': 'Got it',
            'line-link-fail': 'Link failed · please retry',
            'line-already-linked': 'This LINE is linked to another account',
            'toast-rate-limit': 'Too many requests · try later',
            'toast-quota-exceeded': 'Quota exceeded',
            'toast-needs-line': 'Please link LINE first',
            'modal-close': 'Close',
        },
        th: {
            'plan-trial': 'ทดลอง', 'plan-free': 'ฟรี', 'plan-pro': 'Pro', 'plan-firm': 'Firm', 'plan-enterprise': 'Enterprise',
            'banner-trial-left': 'ทดลองเหลือ {n} วัน · ใช้ {used}/{limit}',
            'banner-trial-last': 'ทดลองหมดวันนี้ · อัปเกรดเพื่อเก็บข้อมูล',
            'banner-trial-expiring': 'เหลือ {n} วัน · อัปเกรดเพื่อเก็บข้อมูล',
            'banner-trial-needs-line': 'ทดลอง · ผูก LINE เพื่อปลดล็อก 50 ใบ',
            'banner-free': 'ฟรี · ใช้ {used}/{limit} เดือนนี้',
            'banner-free-needs-line': 'ฟรี · ผูก LINE เพื่อปลดล็อก 10 ใบ/เดือน',
            'banner-pro': 'Pro · เหลือ {n} วัน · {used}/{limit}',
            'banner-firm': 'Firm · เหลือ {n} วัน',
            'banner-monthly': 'รายเดือน · เหลือ {n} วัน · {used}/{limit}',
            'banner-yearly':  'รายปี · เหลือ {n} วัน · {used}/{limit}',
            'btn-renew': 'ต่ออายุ',
            'banner-locked': 'บัญชีถูกระงับ: {reason}',
            'btn-upgrade': 'อัปเกรด', 'btn-link-line': 'ผูก LINE',
            'upg-title': 'อัปเกรดแพ็กเกจ',
            'upg-sub': 'เลือกแพ็กเกจที่เหมาะ · ปลดล็อกฟีเจอร์ทันที',
            'upg-pro-tagline': 'นักบัญชี / สำนักงานเล็ก',
            'upg-firm-tagline': 'สำนักงานบัญชีมืออาชีพ',
            'upg-recommended': 'แนะนำ',
            'upg-monthly': '/เดือน',
            'upg-feat-ocr': 'OCR · {n} ใบ/เดือน',
            'upg-feat-ocr-unlim': 'OCR · ไม่จำกัด',
            'upg-feat-clients': 'ลูกค้า · {n}',
            'upg-feat-clients-unlim': 'ลูกค้า · ไม่จำกัด',
            'upg-feat-seats': 'ผู้ใช้ · {n} คน',
            'upg-feat-automation': 'อัตโนมัติ (อีเมล/โฟลเดอร์/ERP)',
            'upg-feat-templates': 'แม่แบบขั้นสูง (ภ.พ.30 ฯลฯ)',
            'upg-feat-batch': 'ส่งออกหลายรายการ',
            'upg-feat-line': 'เชื่อมต่อ LINE Bot',
            'upg-pick-pro': 'เลือก Pro',
            'upg-pick-firm': 'เลือก Firm',
            'pay-title': 'ชำระเงิน · {plan}',
            'pay-amount': 'โอน ฿{n}',
            'pay-step1': 'ขั้นที่ 1 · โอนเงิน',
            'pay-bank-row': 'ธนาคารกสิกรไทย · 011-1-83212-9',
            'pay-promptpay-row': 'PromptPay · +66 85-064-2609',
            'pay-step2': 'ขั้นที่ 2 · อัปโหลดสลิป',
            'pay-pick-file': 'เลือกไฟล์',
            'pay-payer-name': 'ชื่อผู้โอน (ไม่บังคับ)',
            'pay-payer-note': 'หมายเหตุ (ไม่บังคับ)',
            'pay-submit': 'ส่งตรวจสอบ',
            'pay-submitting': 'กำลังส่ง...',
            'pay-back': 'ย้อนกลับ',
            'pay-line-contact': 'หรือติดต่อ LINE: @Pearnly',
            'pay-success': 'ส่งแล้ว · ตรวจสอบ 5-10 นาที · จะแจ้งทาง LINE',
            'pay-fail': 'ส่งไม่สำเร็จ',
            'pay-need-screenshot': 'กรุณาอัปโหลดสลิป',
            // v111.2 · 3 แพ็คเกจ
            'upg-plan-trial':     'ทดลอง',
            'upg-plan-trial-desc':    '100/เดือน · 7 วัน · 3 ลูกค้า · ฿0',
            'upg-plan-monthly-desc':  '500/เดือน · 30 วัน · 10 ลูกค้า · ฿299',
            'upg-plan-yearly-desc':   '1500/เดือน · 365 วัน · 30 ลูกค้า · ฿2,990',
            'upg-plan-lifetime-desc': 'ไม่จำกัด · ตลอดชีพ · Gemini Key ของตนเอง · ฿9,900',
            'upg-plan-monthly':   'รายเดือน',
            'upg-plan-yearly':    'รายปี',
            'upg-plan-lifetime':  'ตลอดชีพ',
            'upg-monthly-tag':    'เริ่มต้น · นักบัญชีอิสระ',
            'upg-yearly-tag':     'ประหยัด {pct}% · สำนักงานบัญชีขนาดกลาง',
            'upg-lifetime-tag':   'จ่ายครั้งเดียว · ใช้ Gemini Key ของคุณเอง · ไม่จำกัด',
            'upg-lifetime-badge': 'ตลอดไป',
            'upg-per-month':      '/เดือน',
            'upg-per-year':       '/ปี',
            'upg-once':           'จ่ายครั้งเดียว',
            'upg-pick':           'เลือก',
            'upg-feat-files':     'อัปโหลดสูงสุด {n} ไฟล์ต่อครั้ง',
            'upg-feat-own-key':   'ใช้ Gemini API Key ของคุณเอง',
            'pay-acct-no':        'เลขที่บัญชี',
            'pay-copied':         'คัดลอกแล้ว',
            'pay-step3-key':      'ขั้นที่ 3 · กรอก Gemini API Key',
            'pay-key-hint':       'ผู้ใช้ตลอดชีพต้องใช้ Gemini Key ของตัวเอง · ขอฟรีได้ที่:',
            'pay-need-gemini-key': 'กรุณากรอก Gemini API Key (ขึ้นต้นด้วย AIza)',
            'plan-changed-toast': 'อัปเดตแพ็คเกจแล้ว · โควต้าซิงค์แล้ว',
            'adm-slip-not-found': 'ไม่พบสลิป',
            'adm-drawer-sec-actions': 'การดำเนินการด่วน',
            'adm-drawer-btn-upgrade': 'เปลี่ยนแพ็คเกจ',
            'adm-drawer-btn-ban': 'แบนบัญชี',
            'adm-drawer-btn-unban': 'ปลดแบน',
            'adm-confirm-ban': 'ยืนยันแบน {e}?',
            'adm-banned': 'แบนแล้ว',
            'adm-unbanned': 'ปลดแบนแล้ว',
            'scanner-editor-title':   'แก้ไข',
            'scanner-editor-confirm': 'เสร็จ',
            'scanner-filter-original':'ต้นฉบับ',
            'scanner-filter-enhance': 'ปรับแต่ง',
            'scanner-filter-bw':      'ขาว-ดำ',
            'scanner-filter-gray':    'เทา',
            'scanner-brightness':     'ความสว่าง',
            'scanner-contrast':       'ความคมชัด',
            'scanner-readjust':       'ปรับขอบ',
            'scanner-quad-title':     'ปรับ 4 มุม',
            'scanner-quad-cancel':    'ยกเลิก',
            'scanner-quad-confirm':   'ตกลง',
            'scanner-quad-hint':      'ลาก 4 มุม · เลือกพื้นที่กระดาษ',
            'scanner-filter-smart':   'HD อัจฉริยะ',
            'scanner-retake':         'ถ่ายใหม่',
            'scanner-rotate-left':    'หมุนซ้าย',
            'scanner-rotate-right':   'หมุนขวา',
            'scanner-crop':           'ตัด',
            'scanner-flash':          'แฟลช',
            'scanner-flash-unavailable':'กล้องนี้ไม่รองรับแฟลช',
            'scanner-album':          'จากอัลบั้ม',
            'line-modal-title': 'ผูก LINE เพื่อปลดล็อกฟีเจอร์เต็ม',
            'line-modal-sub': 'หลังจากผูกคุณจะได้รับ:',
            'line-benefit-1': 'OCR เต็ม 50 ใบ (ทดลอง) / 10 ใบ/เดือน (ฟรี)',
            'line-benefit-2': 'ลูกค้า 3 ราย (ทดลอง)',
            'line-benefit-3': 'รายงานสัปดาห์ทาง LINE',
            'line-benefit-4': 'แจ้งเตือนก่อนหมดอายุ',
            'line-link-btn': 'คลิกผูก LINE',
            'line-link-success': 'ผูกสำเร็จ · ปลดล็อกแล้ว',
            // v109.4 · LINE OAuth เร็วๆ นี้
            'line-coming-title': 'การเชื่อม LINE · เร็วๆ นี้',
            'line-coming-desc': 'เรากำลังเชื่อมต่อ LINE Official Login · จะสามารถผูกบัญชีได้อย่างปลอดภัยในไม่ช้า · ต้องการเปิดด่วนติดต่อเราได้',
            'line-coming-close': 'เข้าใจแล้ว',
            'line-link-fail': 'ผูกไม่สำเร็จ · ลองใหม่',
            'line-already-linked': 'LINE นี้ถูกผูกกับบัญชีอื่นแล้ว',
            'toast-rate-limit': 'คำขอบ่อยเกินไป · ลองใหม่ทีหลัง',
            'toast-quota-exceeded': 'โควตาหมดแล้ว',
            'toast-needs-line': 'กรุณาผูก LINE ก่อน',
            'modal-close': 'ปิด',
        },
        ja: {
            'plan-trial': '試用', 'plan-free': 'Free', 'plan-pro': 'Pro', 'plan-firm': 'Firm', 'plan-enterprise': 'Enterprise',
            'banner-trial-left': '試用残り {n} 日 · {used}/{limit}',
            'banner-trial-last': '本日試用終了 · データ保持のためアップグレード',
            'banner-trial-expiring': '残り {n} 日 · データ保持のためアップグレード',
            'banner-trial-needs-line': '試用 · LINE 連携で 50 枚解放',
            'banner-free': 'Free · 今月 {used}/{limit}',
            'banner-free-needs-line': 'Free · LINE 連携で 10 枚/月解放',
            'banner-pro': 'Pro · 残り {n} 日 · {used}/{limit}',
            'banner-firm': 'Firm · 残り {n} 日',
            'banner-monthly': '月払い · あと {n} 日 · {used}/{limit}',
            'banner-yearly':  '年払い · あと {n} 日 · {used}/{limit}',
            'btn-renew': '更新',
            'banner-locked': 'アカウント停止: {reason}',
            'btn-upgrade': 'アップグレード', 'btn-link-line': 'LINE 連携',
            'upg-title': 'プランアップグレード',
            'upg-sub': '最適なプランを選択 · 全機能を即解放',
            'upg-pro-tagline': '個人会計 / 小規模事務所',
            'upg-firm-tagline': 'プロ事務所 · マルチユーザー',
            'upg-recommended': '推奨',
            'upg-monthly': '/月',
            'upg-feat-ocr': 'OCR · {n} 枚/月',
            'upg-feat-ocr-unlim': 'OCR · 無制限',
            'upg-feat-clients': '顧客 · {n}',
            'upg-feat-clients-unlim': '顧客 · 無制限',
            'upg-feat-seats': 'ユーザー席 · {n}',
            'upg-feat-automation': '自動化(メール/フォルダ/ERP)',
            'upg-feat-templates': '高度テンプレート(ภ.พ.30 等)',
            'upg-feat-batch': '一括エクスポート',
            'upg-feat-line': 'LINE Bot 連携',
            'upg-pick-pro': 'Pro を選択',
            'upg-pick-firm': 'Firm を選択',
            'pay-title': '支払い · {plan}',
            'pay-amount': '฿{n} を振込',
            'pay-step1': 'ステップ 1 · 振込',
            'pay-bank-row': 'カシコン銀行 · 011-1-83212-9',
            'pay-promptpay-row': 'PromptPay · +66 85-064-2609',
            'pay-step2': 'ステップ 2 · スクショアップロード',
            'pay-pick-file': 'ファイル選択',
            'pay-payer-name': 'お名前(任意)',
            'pay-payer-note': '備考(任意)',
            'pay-submit': '審査依頼',
            'pay-submitting': '送信中...',
            'pay-back': '戻る',
            'pay-line-contact': 'または LINE: @Pearnly',
            'pay-success': '送信完了 · 5-10 分で審査 · LINE で通知',
            'pay-fail': '送信失敗',
            'pay-need-screenshot': 'スクショをアップロードしてください',
            // v111.2 · 新 3 プラン
            'upg-plan-trial':     '試用',
            'upg-plan-trial-desc':    '100 枚/月 · 7 日 · 3 顧客 · ฿0',
            'upg-plan-monthly-desc':  '500 枚/月 · 30 日 · 10 顧客 · ฿299',
            'upg-plan-yearly-desc':   '1500 枚/月 · 365 日 · 30 顧客 · ฿2,990',
            'upg-plan-lifetime-desc': '無制限 · 永久 · Gemini Key 持参 · ฿9,900',
            'upg-plan-monthly':   '月払い',
            'upg-plan-yearly':    '年払い',
            'upg-plan-lifetime':  '買い切り',
            'upg-monthly-tag':    'スターター · 個人会計士',
            'upg-yearly-tag':     '{pct}% お得 · 中小事務所',
            'upg-lifetime-tag':   '一度払い · 自分の Gemini Key 使用 · 無制限',
            'upg-lifetime-badge': '永久',
            'upg-per-month':      '/月',
            'upg-per-year':       '/年',
            'upg-once':           '一度',
            'upg-pick':           '選択',
            'upg-feat-files':     '一度に最大 {n} ファイル',
            'upg-feat-own-key':   '自分の Gemini API Key を使用',
            'pay-acct-no':        '口座番号',
            'pay-copied':         'コピー完了',
            'pay-step3-key':      'ステップ 3 · Gemini API Key を入力',
            'pay-key-hint':       '買い切り利用者は自分の Gemini Key を使用 · 無料申請:',
            'pay-need-gemini-key': '有効な Gemini API Key を入力してください(AIza で始まる)',
            'plan-changed-toast': 'プランを更新しました · クォータ同期完了',
            'adm-slip-not-found': 'スクショが見つかりません',
            'adm-drawer-sec-actions': 'クイックアクション',
            'adm-drawer-btn-upgrade': 'プラン変更',
            'adm-drawer-btn-ban': 'アカウント停止',
            'adm-drawer-btn-unban': '停止解除',
            'adm-confirm-ban': '{e} を停止?',
            'adm-banned': '停止しました',
            'adm-unbanned': '解除しました',
            'scanner-editor-title':   '編集',
            'scanner-editor-confirm': '完了',
            'scanner-filter-original':'オリジナル',
            'scanner-filter-enhance': '強調',
            'scanner-filter-bw':      '白黒',
            'scanner-filter-gray':    'グレー',
            'scanner-brightness':     '明るさ',
            'scanner-contrast':       'コントラスト',
            'scanner-readjust':       '枠調整',
            'scanner-quad-title':     '4 角を調整',
            'scanner-quad-cancel':    'キャンセル',
            'scanner-quad-confirm':   'OK',
            'scanner-quad-hint':      '4 角をドラッグ · 紙の範囲を選択',
            'scanner-filter-smart':   'スマート HD',
            'scanner-retake':         '撮り直す',
            'scanner-rotate-left':    '左回転',
            'scanner-rotate-right':   '右回転',
            'scanner-crop':           'トリミング',
            'scanner-flash':          'フラッシュ',
            'scanner-flash-unavailable':'このカメラはフラッシュ非対応',
            'scanner-album':          'アルバムから',
            'line-modal-title': 'LINE 連携で全機能解放',
            'line-modal-sub': '連携後すぐに:',
            'line-benefit-1': 'OCR 完全 50 枚(試用)/ 10 枚/月(Free)',
            'line-benefit-2': '顧客 3 件(試用)',
            'line-benefit-3': '週次レポートを LINE で受信',
            'line-benefit-4': '期限前に自動 LINE 通知',
            'line-link-btn': 'クリックして LINE 連携',
            'line-link-success': '連携成功 · クォータ解放',
            // v109.4 · LINE OAuth 近日公開
            'line-coming-title': 'LINE 連携機能 · 近日公開',
            'line-coming-desc': 'LINE 公式ログインを統合中 · まもなく安全なワンタップ連携が利用可能 · 至急ご利用の場合はお問い合わせください',
            'line-coming-close': '了解',
            'line-link-fail': '連携失敗 · 再試行',
            'line-already-linked': 'この LINE は他アカウントに連携済',
            'toast-rate-limit': 'リクエスト過多 · しばらくしてから再試行',
            'toast-quota-exceeded': 'クォータ超過',
            'toast-needs-line': 'まず LINE を連携してください',
            'modal-close': '閉じる',
        },
    };
    Object.keys(V109_3_I18N).forEach(lang => {
        if (!I18N[lang]) I18N[lang] = {};
        Object.assign(I18N[lang], V109_3_I18N[lang]);
    });

    function tt(key, params) {
        let s = (I18N[currentLang] && I18N[currentLang][key]) || key;
        if (params) Object.keys(params).forEach(p => {
            s = s.replace(new RegExp('\\{' + p + '\\}', 'g'), params[p]);
        });
        return s;
    }
    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
    }

    // ============================================================
    // 拉当前套餐
    // ============================================================
    async function loadPlan() {
        try {
            const tok = localStorage.getItem('mrpilot_token');
            if (!tok) return null;
            const r = await fetch('/api/me/plan', { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!r.ok) return null;
            const newState = await r.json();
            // v111.3 · 如果 plan 档变了(管理员后台改套餐) · 全 UI 刷新
            const oldPlan = _planState && _planState.plan;
            const oldLimit = _planState && _planState.usage && _planState.usage.ocr_limit;
            _planState = newState;
            window._planState = _planState;
            renderTrialBanner();
            const newPlan = newState.plan;
            const newLimit = newState.usage && newState.usage.ocr_limit;
            if (oldPlan && (oldPlan !== newPlan || oldLimit !== newLimit)) {
                console.log('[v111.3] plan changed:', oldPlan, '→', newPlan);
                // 同步刷新顶部 / 上传提示 / 侧栏可见性
                try {
                    const u = await apiGet('/api/me');
                    const q = await apiGet('/api/ocr/quota');
                    if (u) { _userInfo = u; try { window._userInfo = u; } catch (_) { /* silent */ } }
                    if (q) _quota = q;
                    renderInfoBar();
                    renderQuotaBanner();
                    applySidebarVisibility();
                    updateUploadHint();
                    updateStartButton();
                    showToast(tt('plan-changed-toast'), 'info');
                } catch (e) { console.error('plan sync refresh failed', e); }
            }
            return _planState;
        } catch (e) { console.error('loadPlan', e); return null; }
    }
    window.reloadPlan = loadPlan;
    // v111.3 · 让 setLang 能调到这个闭包内的函数
    window.renderTrialBanner = function() { renderTrialBanner(); };

    // ============================================================
    // Trial Banner
    // ============================================================
    function ensureBanner() {
        if (document.getElementById('plan-banner')) return;
        const el = document.createElement('div');
        el.id = 'plan-banner';
        el.className = 'plan-banner';
        el.style.display = 'none';
        // v109.4 · 改成 appendChild · banner 是 fixed 不影响布局位置 · 但避免插入 body.firstChild 抢占 topbar
        document.body.appendChild(el);
    }

    function renderTrialBanner() {
        ensureBanner();
        const banner = document.getElementById('plan-banner');
        const hideBanner = () => {
            banner.style.display = 'none';
            document.body.classList.remove('has-plan-banner');
        };
        const showBanner = () => {
            banner.style.display = '';
            document.body.classList.add('has-plan-banner');
        };
        if (!_planState) { hideBanner(); return; }
        // v111.3 · super_admin 不显示 banner
        if (_userInfo && _userInfo.is_super_admin) { hideBanner(); return; }
        // v118.12 · 员工不显示任何套餐 banner(钱相关)
        if (typeof shouldHideMoney === 'function' && shouldHideMoney(_userInfo)) { hideBanner(); return; }

        const { plan, usage, trial_days_left, plan_days_left } = _planState;
        let html = '', level = 'info';

        if (plan === 'admin') {
            hideBanner(); return;
        } else if (plan === 'trial') {
            const days = (trial_days_left === null || trial_days_left === undefined) ? null : Math.max(0, Math.floor(trial_days_left));
            if (days === null) {
                hideBanner(); return;
            } else if (days <= 0) {
                html = `<span>${esc(tt('banner-trial-last'))}</span>`;
                html += '';  // v118.35.0.9 · upgrade button retired
                level = 'danger';
            } else if (days <= 2) {
                html = `<span>${esc(tt('banner-trial-expiring', {n: days}))}</span>`;
                html += '';  // v118.35.0.9 · upgrade button retired
                level = 'warn';
            } else {
                html = `<span>${esc(tt('banner-trial-left', {n: days, used: usage.ocr_used, limit: usage.ocr_limit}))}</span>`;
                html += '';  // v118.35.0.9 · upgrade button retired
                level = 'info';
            }
        } else if (plan === 'monthly') {
            const d = Math.max(0, plan_days_left || 0);
            html = `<span>${esc(tt('banner-monthly', {n: d, used: usage.ocr_used, limit: usage.ocr_limit}))}</span>`;
            // 7 天内到期 · 黄色提醒
            if (d <= 7 && d > 0) {
                html += '';  // v118.35.0.9 · upgrade button retired
                level = 'warn';
            } else {
                level = 'success';
            }
        } else if (plan === 'yearly') {
            const d = Math.max(0, plan_days_left || 0);
            html = `<span>${esc(tt('banner-yearly', {n: d, used: usage.ocr_used, limit: usage.ocr_limit}))}</span>`;
            if (d <= 30 && d > 0) {
                html += '';  // v118.35.0.9 · upgrade button retired
                level = 'warn';
            } else {
                level = 'success';
            }
        } else if (plan === 'lifetime') {
            // 永久 · 不显示 banner
            hideBanner(); return;
        } else {
            hideBanner(); return;
        }
        banner.className = 'plan-banner plan-banner-' + level;
        banner.innerHTML = html;
        showBanner();
    }

    // v118.35.0.10 · 升级 modal 整套已永久下线 · 死代码 226 行物理删除


    // ============================================================
    // LINE 绑定弹窗(开发期 · 用 dev 端点 · 真 OAuth 后续接)
    // ============================================================
    function ensureLineModal() {
        if (document.getElementById('line-modal')) return;
        const html = `
        <div class="upg-overlay" id="line-modal" style="display:none;">
            <div class="upg-modal" style="max-width:440px">
                <div class="upg-head">
                    <div>
                        <div class="upg-title">${esc(tt('line-modal-title'))}</div>
                        <div class="upg-sub">${esc(tt('line-modal-sub'))}</div>
                    </div>
                    <button class="upg-close" id="line-close-x"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l8 8M14 6l-8 8" stroke-linecap="round"/></svg></button>
                </div>
                <div class="upg-body">
                    <ul class="line-benefits">
                        <li>${esc(tt('line-benefit-1'))}</li>
                        <li>${esc(tt('line-benefit-2'))}</li>
                        <li>${esc(tt('line-benefit-3'))}</li>
                        <li>${esc(tt('line-benefit-4'))}</li>
                    </ul>
                    <button class="btn btn-line" id="line-link-btn">
                        <svg viewBox="0 0 20 20" fill="currentColor" style="width:18px;height:18px"><circle cx="10" cy="10" r="9"/></svg>
                        <span>${esc(tt('line-link-btn'))}</span>
                    </button>
                </div>
            </div>
        </div>`;
        const w = document.createElement('div'); w.innerHTML = html.trim();
        document.body.appendChild(w.firstElementChild);
        document.getElementById('line-close-x').addEventListener('click', closeLineModal);
        document.getElementById('line-modal').addEventListener('click', (e) => {
            if (e.target.id === 'line-modal') closeLineModal();
        });
        document.getElementById('line-link-btn').addEventListener('click', linkLineDev);
    }
    function closeLineModal() {
        const m = document.getElementById('line-modal');
        if (m) m.style.display = 'none';
    }
    window.openLineLinkModal = function() {
        ensureLineModal();
        document.getElementById('line-modal').style.display = '';
    };

    async function linkLineDev() {
        // v109.4 · 关掉 dev 后门(任何人点击都能假绑定)
        // 改成显示「即将上线」提示 · 真 LINE OAuth 接入后这个函数恢复正常调用 /api/me/link_line
        const btn = document.getElementById('line-link-btn');
        if (btn) btn.disabled = true;
        // 显示提示卡片(替换 modal 内容)
        const modal = document.getElementById('line-modal');
        if (modal) {
            const inner = modal.querySelector('.line-modal-inner') || modal.firstElementChild;
            if (inner) {
                inner.innerHTML = `
                    <div class="line-coming-wrap">
                        <div class="line-coming-icon">
                            <svg viewBox="0 0 48 48" fill="none" stroke="#06C755" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="24" cy="24" r="20"/>
                                <path d="M24 14v10l6 4"/>
                            </svg>
                        </div>
                        <div class="line-coming-title">${esc(tt('line-coming-title'))}</div>
                        <div class="line-coming-desc">${esc(tt('line-coming-desc'))}</div>
                        <div class="line-coming-contact">
                            <svg viewBox="0 0 24 24" fill="#06C755">
                                <path d="M12 2C6.48 2 2 5.97 2 10.86c0 3.14 2.03 5.91 5.07 7.5l-.5 3.51c-.07.45.42.78.79.55l4.04-2.4c.2.02.4.03.6.03 5.52 0 10-3.97 10-8.86C22 5.97 17.52 2 12 2z"/>
                            </svg>
                            LINE: @Pearnly
                        </div>
                        <button class="btn btn-primary line-coming-close" id="line-coming-close">${esc(tt('line-coming-close'))}</button>
                    </div>
                `;
                const closeBtn = inner.querySelector('#line-coming-close');
                if (closeBtn) closeBtn.addEventListener('click', closeLineModal);
            }
        }
    }

    // ============================================================
    // OCR 配额超额拦截(全局拦截 fetch · 看 v109. 开头的 detail)
    // ============================================================
    const _origFetch = window.fetch;
    window.fetch = async function(input, init) {
        const resp = await _origFetch.apply(this, arguments);
        // 拦截配额错误 · 自动弹弹窗
        if (resp.status === 429) {
            try {
                const cl = resp.clone();
                const data = await cl.json();
                const detail = data.detail;
                if (typeof detail === 'object' && detail && typeof detail.code === 'string' && detail.code.startsWith('v109.')) {
                    if (detail.needs_line_verify) {
                        setTimeout(() => { showToast(tt('toast-needs-line'), 'info'); openLineLinkModal(); }, 100);
                    } else {
                        setTimeout(() => { showToast(tt('toast-quota-exceeded'), 'info'); /* v118.35.0.9 · upgrade modal retired */ }, 100);
                    }
                }
            } catch (_) {}
        }
        return resp;
    };

    // ============================================================
    // 后台 · 用户管理页(仅 super_admin · 由路由切换触发渲染)
    // ============================================================
    // v118.3 · 全页数据缓存 · 切语言时立即重渲(不等 fetch)
    const _admPageState = {
        funnel: null,
        pay: null,
        users: [],
        risk: null,
    };

    function loadAdminUsersPage() {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        const _h = { headers: { 'Authorization': 'Bearer ' + tok } };
        const _errHtml = (id) => `<div class="adm-empty" style="color:#ef4444">
            加载失败 · <a href="#" style="color:#ef4444;text-decoration:underline" onclick="loadAdminUsersPage();return false">重试</a>
        </div>`;

        // v4.10.16 · 4 路同时发出 · 各自独立渲染 · 互不阻塞(原串行 ~8s → 并行 ~2-3s)
        const funnelP = fetch('/api/admin/users/funnel', _h);
        const payP    = fetch('/api/admin/payments/pending', _h);
        const usersP  = fetch('/api/admin/users?plan=all&search=&limit=100', _h);
        const riskP   = fetch('/api/admin/risk/suspicious', _h);

        funnelP
            .then(async r => { if (r.status === 403) return null; return r.json(); })
            .then(d => {
                if (!d) return;
                _admPageState.funnel = d;
                renderAdmKpi(d);
                renderAdmExpiring(d.trial_expiring_soon || []);
            })
            .catch(() => {
                const w = document.getElementById('adm-kpi-grid');
                if (w) w.innerHTML = _errHtml();
            });

        payP.then(r => r.json())
            .then(d => { _admPageState.pay = d; renderAdmPending(d.payments || []); })
            .catch(() => {
                const w = document.getElementById('adm-pending-list');
                if (w) w.innerHTML = _errHtml();
            });

        usersP.then(r => r.json())
            .then(d => { _admPageState.users = d.users || []; renderAdmUserList(d.users || []); })
            .catch(() => {
                const w = document.getElementById('adm-users-table');
                if (w) w.innerHTML = _errHtml();
            });

        riskP.then(r => r.json())
            .then(d => { _admPageState.risk = d; renderAdmRisk(d); })
            .catch(() => {
                const w = document.getElementById('adm-risk-content');
                if (w) w.innerHTML = _errHtml();
            });
    }

    // v118.3 · 立即用缓存数据 + 当前 i18n 重渲整页(切语言用 · 不等 fetch · 视觉零延迟)
    window.__rerenderAdmPage = function() {
        if (_admPageState.funnel) {
            renderAdmKpi(_admPageState.funnel);
            renderAdmExpiring(_admPageState.funnel.trial_expiring_soon || []);
        }
        if (_admPageState.pay) renderAdmPending(_admPageState.pay.payments || []);
        if (_admPageState.users && _admPageState.users.length) renderAdmUserList(_admPageState.users);
        if (_admPageState.risk) renderAdmRisk(_admPageState.risk);
        // v118.29.0 · 日志切语言重渲
        if (_admLogsState && _admLogsState.rows && _admLogsState.rows.length) {
            renderAdmLogs();
            renderAdmLogsPager();
        }
    };

    function renderAdmKpi(f) {
        const wrap = document.getElementById('adm-kpi-grid');
        if (!wrap) return;
        const bp = f.by_plan || {};
        const cards = [
            { lbl: tt('adm-kpi-today'), val: f.new_today || 0, color: '#111111' },
            { lbl: tt('adm-kpi-week'), val: f.new_week || 0, color: '#111111' },
            { lbl: tt('adm-kpi-month'), val: f.new_month || 0, color: '#111111' },
            { lbl: tt('plan-trial'), val: bp.trial || 0, color: '#f59e0b' },
            { lbl: tt('plan-free'), val: bp.free || 0, color: '#64748b' },
            { lbl: tt('plan-pro'), val: bp.pro || 0, color: '#10b981' },
            { lbl: tt('plan-firm'), val: bp.firm || 0, color: '#8b5cf6' },
            { lbl: tt('adm-kpi-conv'), val: (f.conversion_pct || 0) + '%', color: '#dc2626' },
        ];
        wrap.innerHTML = cards.map(c => `
            <div class="adm-kpi-card" style="border-top: 3px solid ${c.color}">
                <div class="adm-kpi-val" style="color: ${c.color}">${esc(c.val)}</div>
                <div class="adm-kpi-lbl">${esc(c.lbl)}</div>
            </div>
        `).join('');
    }

    function renderAdmPending(rows) {
        const wrap = document.getElementById('adm-pending-list');
        if (!wrap) return;
        if (!rows.length) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-pending-empty'))}</div>`;
            return;
        }
        wrap.innerHTML = rows.filter(r => r.status === 'pending').map(r => `
            <div class="adm-pending-item">
                <div class="adm-pending-info">
                    <div class="adm-pending-line1">
                        <strong>${esc(r.user_email || '?')}</strong> · ${esc(r.company_name || '')}
                        <span class="adm-tag">${esc(r.target_plan.toUpperCase())}</span>
                    </div>
                    <div class="adm-pending-line2">฿${esc(r.amount_thb)} · ${esc(r.payer_name || '—')} · ${esc(r.payer_note || '')}</div>
                    <div class="adm-pending-line3">${esc(new Date(r.created_at).toLocaleString())} · LINE: ${esc(r.line_id || '—')}</div>
                </div>
                <div class="adm-pending-actions">
                    ${r.screenshot_path ? `<button class="btn btn-ghost btn-sm" onclick="window.__adm_view_slip(${r.id})">${esc(tt('adm-view-slip'))}</button>` : ''}
                    <button class="btn btn-primary btn-sm" onclick="window.__adm_approve(${r.id})">${esc(tt('adm-approve'))}</button>
                    <button class="btn btn-danger btn-sm" onclick="window.__adm_reject(${r.id})">${esc(tt('adm-reject'))}</button>
                </div>
            </div>
        `).join('') || `<div class="adm-empty">${esc(tt('adm-pending-empty'))}</div>`;
    }

    // v111.3 · 看付款截图 · 带 token 鉴权 · 用 blob URL 打开
    window.__adm_view_slip = async function(payment_id) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/payments/${payment_id}/screenshot`, {
                headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (!r.ok) { showToast(tt('adm-slip-not-found'), 'error'); return; }
            const blob = await r.blob();
            const url = URL.createObjectURL(blob);
            // 弹个简单 lightbox
            const overlay = document.createElement('div');
            overlay.className = 'slip-overlay';
            overlay.innerHTML = `
                <div class="slip-modal">
                    <button class="slip-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                    <img src="${url}" alt="payment slip">
                </div>`;
            const close = () => { URL.revokeObjectURL(url); overlay.remove(); };
            overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
            overlay.querySelector('.slip-close').addEventListener('click', close);
            document.body.appendChild(overlay);
        } catch (e) {
            console.error(e);
            showToast(tt('adm-slip-not-found'), 'error');
        }
    };

    window.__adm_approve = async function(id) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/payments/${id}/review?action=approve`, {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) { showToast(tt('adm-approved'), 'success'); loadAdminUsersPage(); }
            else showToast(tt('adm-action-fail'), 'error');
        } catch (e) { showToast(tt('adm-action-fail'), 'error'); }
    };
    window.__adm_reject = async function(id) {
        const ok = await showConfirm(tt('adm-confirm-reject'), { danger: true });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/payments/${id}/review?action=reject`, {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) { showToast(tt('adm-rejected'), 'success'); loadAdminUsersPage(); }
            else showToast(tt('adm-action-fail'), 'error');
        } catch (e) { showToast(tt('adm-action-fail'), 'error'); }
    };

    function renderAdmExpiring(rows) {
        const wrap = document.getElementById('adm-expiring-list');
        if (!wrap) return;
        if (!rows.length) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-expiring-empty'))}</div>`;
            return;
        }
        wrap.innerHTML = rows.map(r => `
            <div class="adm-expiring-item">
                <div>
                    <strong>${esc(r.email)}</strong> · ${esc(r.company_name || '')}
                    <span class="adm-tag adm-tag-warn">${r.hours_left}h</span>
                </div>
                <div class="adm-expiring-actions">
                    ${r.line_id ? `<span class="adm-line-id">LINE: ${esc(r.line_id)}</span>` : ''}
                    <button class="btn btn-primary btn-sm" onclick="window.__adm_quick_upgrade('${esc(r.id)}', '${esc(r.email)}')">${esc(tt('adm-quick-upgrade'))}</button>
                </div>
            </div>
        `).join('');
    }

    window.__adm_quick_upgrade = async function(uid, email) {
        // v109.4 · 用 modal 代替原生 prompt · 跟产品 UI 一致
        // 套餐对齐新方案:trial/solo/team/firm/enterprise
        let overlay = document.getElementById('adm-upgrade-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.className = 'cpw-forgot-overlay';
        overlay.id = 'adm-upgrade-overlay';
        const plans = [
            { id: 'trial',    label: tt('upg-plan-trial'),    desc: tt('upg-plan-trial-desc') },
            { id: 'monthly',  label: tt('upg-plan-monthly'),  desc: tt('upg-plan-monthly-desc') },
            { id: 'yearly',   label: tt('upg-plan-yearly'),   desc: tt('upg-plan-yearly-desc') },
            { id: 'lifetime', label: tt('upg-plan-lifetime'), desc: tt('upg-plan-lifetime-desc') },
        ];
        overlay.innerHTML = `
            <div class="cpw-forgot-modal" style="max-width:480px;">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${esc(tt('adm-upgrade-title'))}</div>
                    <button class="cpw-forgot-close" id="adm-upg-close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${esc(email)}</p>
                    <div class="adm-plan-options">
                        ${plans.map(p => `
                            <label class="adm-plan-option">
                                <input type="radio" name="adm-target-plan" value="${p.id}">
                                <div class="adm-plan-option-body">
                                    <div class="adm-plan-option-label">${esc(p.label)}</div>
                                    <div class="adm-plan-option-desc">${esc(p.desc)}</div>
                                </div>
                            </label>
                        `).join('')}
                    </div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="adm-upg-cancel">${esc(tt('cpw-forgot-cancel'))}</button>
                    <button class="btn btn-primary" id="adm-upg-confirm">${esc(tt('adm-upg-confirm'))}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        const close = () => overlay.remove();
        overlay.querySelector('#adm-upg-close').addEventListener('click', close);
        overlay.querySelector('#adm-upg-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
        overlay.querySelector('#adm-upg-confirm').addEventListener('click', async () => {
            const sel = overlay.querySelector('input[name="adm-target-plan"]:checked');
            if (!sel) { showToast(tt('adm-pick-plan'), 'warn'); return; }
            const targetPlan = sel.value;
            const tok = localStorage.getItem('mrpilot_token');
            try {
                const r = await fetch('/api/admin/users/upgrade', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: uid, target_plan: targetPlan, note: 'manual_admin' }),
                });
                if (r.ok) { showToast(tt('adm-upgrade-ok'), 'success'); close(); loadAdminUsersPage(); }
                else { const data = await r.json().catch(() => ({})); showToast(data.detail || tt('adm-upgrade-fail'), 'error'); }
            } catch (e) { showToast(tt('adm-upgrade-fail'), 'error'); }
        });
    };

    async function loadAdmUserList() {
        const tok = localStorage.getItem('mrpilot_token');
        const planF = document.getElementById('adm-plan-filter').value;
        const search = document.getElementById('adm-user-search').value;
        try {
            const qs = `?plan=${encodeURIComponent(planF)}&search=${encodeURIComponent(search)}&limit=100`;
            const r = await fetch('/api/admin/users' + qs, { headers: { 'Authorization': 'Bearer ' + tok } });
            const data = await r.json();
            _admPageState.users = data.users || [];  // v118.3 · 缓存
            renderAdmUserList(data.users || []);
        } catch (e) { console.error(e); }
    }

    function renderAdmUserList(users) {
        const wrap = document.getElementById('adm-users-table');
        if (!wrap) return;
        if (!users.length) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-users-empty'))}</div>`;
            return;
        }
        // v109.4 · 当前登录的 super_admin 自己 · 不能对自己操作
        const meId = (window._userInfo && window._userInfo.id) ? String(window._userInfo.id) : null;
        const planLabelMap = {
            'trial': 'Trial',
            'free': 'Trial',
            'solo': 'Pearnly Solo',
            'team': 'Pearnly Team',
            'firm': 'Pearnly Firm',
            'enterprise': 'Enterprise',
            'pro': 'Pearnly Solo',  // v109.4 · 老 pro 视为 solo · 兼容老数据
            'plus': 'Pearnly Solo', // v109.4 · 老 plus 也视为 solo
            'monthly': 'Monthly',
            'lifetime': 'Lifetime',
        };
        wrap.innerHTML = `
            <div class="adm-table-head">
                <div>${esc(tt('adm-col-email'))}</div>
                <div>${esc(tt('adm-col-company'))}</div>
                <div>${esc(tt('adm-col-plan'))}</div>
                <div>${esc(tt('adm-col-usage'))}</div>
                <div>${esc(tt('adm-col-country'))}</div>
                <div>${esc(tt('adm-col-actions'))}</div>
            </div>
            ${users.map(u => {
                const isSelf = meId && String(u.id) === meId;
                const isAdmin = u.is_super_admin || u.tenant_type === 'admin';
                const planLabel = planLabelMap[u.plan] || (u.plan ? u.plan.charAt(0).toUpperCase() + u.plan.slice(1) : '—');
                const adminBadge = isAdmin ? `<span class="adm-admin-tag">${esc(tt('admin-type-super'))}</span>` : '';
                const lineBadge = u.line_id ? '· LINE' : '';
                // 自己那行 / 其他超管 · 操作按钮 disabled + 加 tooltip
                const actions = (isSelf || isAdmin)
                    ? `<div class="adm-row-actions" title="${esc(tt('admin-self-disabled-tip'))}">
                            <button class="btn btn-ghost btn-sm" disabled>${esc(tt('adm-upgrade'))}</button>
                            <button class="btn btn-ghost btn-sm" disabled>${esc(tt('adm-ban'))}</button>
                       </div>`
                    : `<div class="adm-row-actions">
                            <button class="btn btn-ghost btn-sm" onclick="window.__adm_quick_upgrade('${esc(u.id)}', '${esc(u.email)}')">${esc(tt('adm-upgrade'))}</button>
                            <button class="btn btn-ghost btn-sm" onclick="window.__adm_ban_user('${esc(u.id)}', '${esc(u.email)}')">${esc(tt('adm-ban'))}</button>
                            <button class="btn btn-ghost btn-sm adm-emp-btn-danger" onclick="window.__adm_cascade_delete('${esc(u.id)}', '${esc(u.username || u.email || '')}')" title="${esc(tt('adm-cascade-del-tip'))}">${esc(tt('adm-cascade-del'))}</button>
                       </div>`;
                return `
                    <div class="adm-table-row${isSelf ? ' adm-self-row' : ''}">
                        <div>
                            <div class="adm-cell-strong adm-cell-clickable" onclick="window.__adm_open_user_drawer('${esc(u.id)}')">${esc(u.email || u.username)}</div>
                            <div class="adm-cell-mute">${esc(new Date(u.created_at).toLocaleDateString())} ${adminBadge}</div>
                        </div>
                        <div>${esc(u.company_name || '—')}</div>
                        <div>
                            <span class="adm-plan-badge adm-plan-${esc(u.plan)}">${esc(planLabel)}</span>
                            ${u.days_left !== null && u.days_left !== undefined ? `<div class="adm-cell-mute">${u.days_left}d</div>` : ''}
                        </div>
                        <div>${u.ocr_used_month || 0}</div>
                        <div>${esc(u.country || '—')} ${lineBadge}</div>
                        ${actions}
                    </div>
                `;
            }).join('')}
        `;
    }

    window.__adm_ban_user = async function(uid, email) {
        // v109.4 · 用 modal 代替原生 prompt
        let overlay = document.getElementById('adm-ban-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.className = 'cpw-forgot-overlay';
        overlay.id = 'adm-ban-overlay';
        overlay.innerHTML = `
            <div class="cpw-forgot-modal" style="max-width:420px;">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${esc(tt('adm-ban-title'))}</div>
                    <button class="cpw-forgot-close" id="adm-ban-close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${esc(email)}</p>
                    <p class="cpw-forgot-tip">${esc(tt('adm-ban-warn'))}</p>
                    <div style="margin-top:12px;">
                        <label style="display:block;font-size:13px;color:#475569;margin-bottom:6px;">${esc(tt('adm-ban-reason'))}</label>
                        <input type="text" id="adm-ban-reason-input" class="cpw-input" autocomplete="off" placeholder="${esc(tt('adm-ban-reason-ph'))}" value="abuse">
                    </div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="adm-ban-cancel">${esc(tt('cpw-forgot-cancel'))}</button>
                    <button class="btn btn-danger" id="adm-ban-confirm">${esc(tt('adm-ban-confirm'))}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        const close = () => overlay.remove();
        overlay.querySelector('#adm-ban-close').addEventListener('click', close);
        overlay.querySelector('#adm-ban-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
        overlay.querySelector('#adm-ban-confirm').addEventListener('click', async () => {
            const reason = (overlay.querySelector('#adm-ban-reason-input').value || '').trim() || 'abuse';
            const tok = localStorage.getItem('mrpilot_token');
            try {
                const r = await fetch(`/api/admin/users/${uid}/ban?reason=${encodeURIComponent(reason)}`, {
                    method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
                });
                if (r.ok) { showToast(tt('adm-ban-ok'), 'success'); close(); loadAdmUserList(); }
                else { const data = await r.json().catch(() => ({})); showToast(data.detail || tt('adm-ban-fail'), 'error'); }
            } catch (e) { showToast(tt('adm-ban-fail'), 'error'); }
        });
    };

    // v118.16 · 级联删除老板账号(高风险 · 双重确认)
    window.__adm_cascade_delete = async function(uid, username) {
        const tok = localStorage.getItem('mrpilot_token');
        // 1) 先取影响范围
        let preview;
        try {
            const r = await fetch(`/api/admin/users/${encodeURIComponent(uid)}/cascade-preview`, {
                headers: { 'Authorization': 'Bearer ' + tok }
            });
            if (!r.ok) {
                const data = await r.json().catch(() => ({}));
                showToast(data.detail || tt('adm-cd-preview-fail'), 'error');
                return;
            }
            preview = await r.json();
        } catch (e) {
            showToast(tt('adm-cd-preview-fail'), 'error');
            return;
        }

        // 2) 渲染 modal
        let overlay = document.getElementById('adm-cd-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.className = 'cpw-forgot-overlay';
        overlay.id = 'adm-cd-overlay';
        const c = preview.counts || {};
        const t_owner = preview.owner || {};
        const t_tenant = preview.tenant || {};
        overlay.innerHTML = `
            <div class="cpw-forgot-modal" style="max-width:520px;">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title" style="color:#dc2626;">⚠ ${esc(tt('adm-cd-title'))}</div>
                    <button class="cpw-forgot-close" id="adm-cd-close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-tip" style="background:#fef2f2;border-color:#fecaca;color:#991b1b;">${esc(tt('adm-cd-warn'))}</p>
                    <div style="background:#f4f4f0;border-radius:8px;padding:12px 14px;margin:12px 0;font-size:13px;">
                        <div style="font-weight:600;margin-bottom:8px;color:#0f172a;">${esc(t_owner.username || t_owner.email || username)}</div>
                        <div style="color:#64748b;margin-bottom:10px;">${esc(t_tenant.name || '—')}${t_tenant.tenant_type ? ' · ' + esc(t_tenant.tenant_type) : ''}</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;color:#475569;">
                            <div>${esc(tt('adm-cd-c-employees'))}: <b>${c.employees||0}</b></div>
                            <div>${esc(tt('adm-cd-c-ocr'))}: <b>${c.ocr_records||0}</b></div>
                            <div>${esc(tt('adm-cd-c-clients'))}: <b>${c.clients||0}</b></div>
                            <div>${esc(tt('adm-cd-c-erp'))}: <b>${c.erp_endpoints||0}</b></div>
                            <div>${esc(tt('adm-cd-c-pushlog'))}: <b>${c.erp_push_logs||0}</b></div>
                            <div>${esc(tt('adm-cd-c-email'))}: <b>${c.email_accounts||0}</b></div>
                            <div>${esc(tt('adm-cd-c-bank'))}: <b>${c.bank_recon_sessions||0}</b></div>
                        </div>
                    </div>
                    <label style="display:block;margin:12px 0 4px;font-size:13px;color:#475569;">${esc(tt('adm-cd-type-username').replace('{n}', t_owner.username || username))}</label>
                    <input type="text" id="adm-cd-username" autocomplete="off" placeholder="${esc(t_owner.username || username)}"
                        style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
                    <label style="display:block;margin:12px 0 4px;font-size:13px;color:#475569;">${esc(tt('adm-cd-type-password'))}</label>
                    <input type="password" id="adm-cd-password" autocomplete="current-password"
                        style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
                </div>
                <div class="cpw-forgot-footer">
                    <button class="btn btn-ghost" id="adm-cd-cancel">${esc(tt('confirm-cancel') || '取消')}</button>
                    <button class="btn btn-danger" id="adm-cd-submit">${esc(tt('adm-cd-submit'))}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        const close = () => overlay.remove();
        document.getElementById('adm-cd-close').addEventListener('click', close);
        document.getElementById('adm-cd-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        document.getElementById('adm-cd-submit').addEventListener('click', async () => {
            const u = (document.getElementById('adm-cd-username').value || '').trim();
            const p = document.getElementById('adm-cd-password').value || '';
            const expected = (t_owner.username || username || '').trim();
            if (u !== expected) {
                showToast(tt('adm-cd-username-mismatch'), 'error');
                return;
            }
            if (!p) {
                showToast(tt('adm-cd-password-required'), 'error');
                return;
            }
            try {
                const r = await fetch(`/api/admin/users/${encodeURIComponent(uid)}/cascade-delete`, {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ confirm_username: u, confirm_password: p }),
                });
                const data = await r.json().catch(() => ({}));
                if (r.ok) {
                    showToast(tt('adm-cd-ok'), 'success');
                    close();
                    loadAdmUserList();
                } else {
                    // 把后端 detail 转成友好文案
                    const code = data.detail;
                    const map = {
                        'admin.password_invalid': tt('adm-cd-password-invalid'),
                        'admin.username_mismatch': tt('adm-cd-username-mismatch'),
                        'admin.cannot_delete_self': tt('adm-cd-cannot-self'),
                        'admin.not_an_owner': tt('adm-cd-not-owner'),
                        'admin.cascade_delete_failed': tt('adm-cd-fail'),
                    };
                    showToast(map[code] || (typeof code === 'string' ? code : tt('adm-cd-fail')), 'error');
                }
            } catch (e) {
                showToast(tt('adm-cd-fail'), 'error');
            }
        });
    };

    // v109.4 · 用户详情抽屉(右侧滑出)· 展示完整字段
    window.__adm_open_user_drawer = async function(uid) {
        const tok = localStorage.getItem('mrpilot_token');
        let overlay = document.getElementById('adm-drawer-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.className = 'adm-drawer-overlay';
        overlay.id = 'adm-drawer-overlay';
        overlay.dataset.uid = uid;   // v111.3 · setLang 重渲用
        overlay.innerHTML = `
            <div class="adm-drawer">
                <div class="adm-drawer-head">
                    <div class="adm-drawer-title">${esc(tt('adm-drawer-title'))}</div>
                    <button class="adm-drawer-close" id="adm-drawer-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="adm-drawer-body" id="adm-drawer-body">
                    <div class="adm-drawer-loading">${esc(tt('adm-drawer-loading'))}</div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // 等下一帧再加 .show class · 让 transition 生效
        requestAnimationFrame(() => overlay.classList.add('show'));

        const close = () => {
            overlay.classList.remove('show');
            setTimeout(() => overlay.remove(), 250);
        };
        overlay.querySelector('#adm-drawer-close').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        // 拉详情
        try {
            const r = await fetch(`/api/admin/users/${uid}`, { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!r.ok) {
                document.getElementById('adm-drawer-body').innerHTML =
                    `<div class="adm-drawer-error">${esc(tt('adm-drawer-error'))}</div>`;
                return;
            }
            const u = await r.json();
            renderAdmUserDrawer(u);
        } catch (e) {
            document.getElementById('adm-drawer-body').innerHTML =
                `<div class="adm-drawer-error">${esc(tt('adm-drawer-error'))}</div>`;
        }
    };

    // 抽屉内部渲染
    function renderAdmUserDrawer(u) {
        const body = document.getElementById('adm-drawer-body');
        if (!body) return;

        const fmtTime = (s) => {
            if (!s) return '—';
            try {
                const d = new Date(s);
                const now = new Date();
                const diff = Math.floor((now - d) / 1000);
                let rel;
                if (diff < 60) rel = tt('time-just-now');
                else if (diff < 3600) rel = tt('time-mins-ago', { n: Math.floor(diff/60) });
                else if (diff < 86400) rel = tt('time-hours-ago', { n: Math.floor(diff/3600) });
                else if (diff < 86400 * 30) rel = tt('time-days-ago', { n: Math.floor(diff/86400) });
                else rel = '';
                return d.toLocaleString() + (rel ? ' · ' + rel : '');
            } catch (e) { return s; }
        };

        const planLabelMap = {
            'trial': 'Trial', 'free': 'Trial',
            'solo': 'Pearnly Solo', 'pro': 'Pearnly Solo', 'plus': 'Pearnly Solo',
            'team': 'Pearnly Team',
            'firm': 'Pearnly Firm',
            'enterprise': 'Enterprise',
            'monthly': 'Monthly', 'lifetime': 'Lifetime',
        };
        const planLabel = planLabelMap[u.plan] || (u.plan || '—');

        const lineStatus = u.line_user_id
            ? `<span class="adm-drawer-pill adm-pill-success">✓ ${esc(tt('adm-drawer-line-linked'))}</span>`
            : `<span class="adm-drawer-pill adm-pill-warn">○ ${esc(tt('adm-drawer-line-not-linked'))}</span>`;

        const riskBadge = u.has_risk_signal
            ? `<span class="adm-drawer-pill adm-pill-danger">⚠ ${esc(tt('adm-drawer-risky'))}</span>`
            : '';

        body.innerHTML = `
            <div class="adm-drawer-header-row">
                <div class="adm-drawer-avatar">${esc((u.email || u.username || '?').charAt(0).toUpperCase())}</div>
                <div class="adm-drawer-header-text">
                    <div class="adm-drawer-name">${esc(u.email || u.username || '')}</div>
                    <div class="adm-drawer-sub">${esc(u.company_name || tt('adm-drawer-no-company'))}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-account'))}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-plan'))}</div>
                    <div class="adm-drawer-value">
                        <span class="adm-plan-badge adm-plan-${esc(u.plan)}">${esc(planLabel)}</span>
                        ${u.days_left != null ? ` · ${u.days_left}d` : ''}
                    </div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-status'))}</div>
                    <div class="adm-drawer-value">${u.is_active === false ? esc(tt('adm-drawer-banned')) : esc(tt('adm-drawer-active'))}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-line'))}</div>
                    <div class="adm-drawer-value">${lineStatus}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-role'))}</div>
                    <div class="adm-drawer-value">${u.is_super_admin ? '⭐ Super Admin' : esc(u.role || 'owner')}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-contact'))}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-email'))}</div>
                    <div class="adm-drawer-value">${esc(u.email || '—')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-phone'))}</div>
                    <div class="adm-drawer-value">${esc(u.phone || '—')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-line-id'))}</div>
                    <div class="adm-drawer-value">${esc(u.line_id || '—')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-country'))}</div>
                    <div class="adm-drawer-value">${esc(u.country || '—')}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-signup'))} ${riskBadge}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-signed-up'))}</div>
                    <div class="adm-drawer-value">${esc(fmtTime(u.created_at))}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-source'))}</div>
                    <div class="adm-drawer-value">${esc(u.signup_source || tt('adm-drawer-source-direct'))}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-ip'))}</div>
                    <div class="adm-drawer-value adm-drawer-mono">${esc(u.signup_ip || '—')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-fingerprint'))}</div>
                    <div class="adm-drawer-value adm-drawer-mono">${esc((u.signup_fingerprint || '—').slice(0, 16))}${u.signup_fingerprint ? '...' : ''}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-usage'))}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-month-ocr'))}</div>
                    <div class="adm-drawer-value">${u.ocr_used_month || 0} / ${u.ocr_quota || tt('adm-drawer-unlimited')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-total-ocr'))}</div>
                    <div class="adm-drawer-value">${u.ocr_total || 0}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-last-ocr'))}</div>
                    <div class="adm-drawer-value">${esc(fmtTime(u.last_ocr_at))}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-last-login'))}</div>
                    <div class="adm-drawer-value">${esc(fmtTime(u.last_login_at))}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-payment'))}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-payments'))}</div>
                    <div class="adm-drawer-value">${u.payment_count || 0}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-last-payment'))}</div>
                    <div class="adm-drawer-value">${esc(fmtTime(u.last_payment_at))}</div>
                </div>
            </div>

            ${!u.is_super_admin ? `
            <div class="adm-drawer-section adm-drawer-actions-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-actions'))}</div>
                <div class="adm-drawer-actions-grid">
                    <button class="btn btn-primary" onclick="window.__adm_upgrade_from_drawer('${esc(u.id)}', '${esc(u.email || '')}')">
                        ${esc(tt('adm-drawer-btn-upgrade'))}
                    </button>
                    ${u.is_active === false ?
                        `<button class="btn btn-ghost" onclick="window.__adm_unban_user('${esc(u.id)}')">${esc(tt('adm-drawer-btn-unban'))}</button>` :
                        `<button class="btn btn-danger" onclick="window.__adm_ban_user('${esc(u.id)}', '${esc(u.email || '')}')">${esc(tt('adm-drawer-btn-ban'))}</button>`
                    }
                </div>
            </div>
            ` : ''}
        `;
    }

    // v111.3 · 抽屉里点升级 → 复用现有快速升级对话框
    window.__adm_upgrade_from_drawer = function(uid, email) {
        if (typeof window.__adm_quick_upgrade === 'function') {
            window.__adm_quick_upgrade(uid, email);
        } else {
            showToast('upgrade dialog not loaded', 'error');
        }
    };
    // v111.3 · 封禁/解封用户(用现有 admin/users/ban API)
    window.__adm_ban_user = async function(uid, email) {
        const ok = await showConfirm(tt('adm-confirm-ban', { e: email }), { danger: true });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/users/${uid}/ban`, {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'admin_action' }),
            });
            if (r.ok) { showToast(tt('adm-banned'), 'success'); loadAdminUsersPage(); }
            else showToast(tt('adm-action-fail'), 'error');
        } catch (e) { showToast(tt('adm-action-fail'), 'error'); }
    };
    window.__adm_unban_user = async function(uid) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/users/${uid}/unban`, {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) { showToast(tt('adm-unbanned'), 'success'); loadAdminUsersPage(); }
            else showToast(tt('adm-action-fail'), 'error');
        } catch (e) { showToast(tt('adm-action-fail'), 'error'); }
    };

    // v116 · 风控状态(模块内闭包)
    const _admRiskState = {
        collapsed: true,                    // 默认收起
        page: { ip: 1, fp: 1, heavy: 1 },   // 各分类当前页
        pageSize: 5,
        data: null,                          // 缓存上一次接口数据
    };

    function renderAdmRisk(r) {
        const wrap = document.getElementById('adm-risk-content');
        if (!wrap) return;
        if (r) _admRiskState.data = r;
        const data = _admRiskState.data || {};
        const sip = data.same_ip_signups || [];
        const sfp = data.same_fingerprint_signups || [];
        const heavy = data.heavy_ocr_users || [];
        const ev = data.risk_events_24h || [];
        const totalSignals = sip.length + sfp.length + heavy.length;
        const totalEvents = ev.reduce((a, e) => a + (e.count || 0), 0);

        // 全部干净:简单一行
        if (!totalSignals && !totalEvents) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-risk-clean'))}</div>`;
            return;
        }

        // 顶部 summary + 展开/收起
        const collapsed = _admRiskState.collapsed;
        const summary = `
            <div class="adm-risk-summary">
                <div class="adm-risk-summary-stats">
                    ${totalSignals > 0 ? `<span class="adm-risk-stat-pill warn">${totalSignals} ${esc(tt('adm-risk-stat-groups'))}</span>` : ''}
                    ${totalEvents > 0 ? `<span class="adm-risk-stat-pill info">${totalEvents} ${esc(tt('adm-risk-stat-events'))}</span>` : ''}
                </div>
                <button class="adm-risk-toggle-btn" onclick="window.__adm_risk_toggle()">
                    ${esc(collapsed ? tt('adm-risk-expand') : tt('adm-risk-collapse'))}
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transform: rotate(${collapsed ? '0' : '180'}deg); transition: transform 0.2s">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
            </div>`;

        if (collapsed) {
            wrap.innerHTML = summary;
            return;
        }

        // 展开 · 渲染 4 分组
        const renderGroup = (title, items, kind, renderRow) => {
            if (!items.length) return '';
            const ps = _admRiskState.pageSize;
            const cur = _admRiskState.page[kind] || 1;
            const totalPages = Math.max(1, Math.ceil(items.length / ps));
            const safeCur = Math.min(cur, totalPages);
            const slice = items.slice((safeCur - 1) * ps, safeCur * ps);
            const pager = totalPages > 1 ? `
                <div class="adm-risk-pager">
                    <button class="adm-risk-pager-btn" ${safeCur <= 1 ? 'disabled' : ''} onclick="window.__adm_risk_page('${kind}', ${safeCur - 1})">‹</button>
                    <span class="adm-risk-pager-info">${safeCur} / ${totalPages}</span>
                    <button class="adm-risk-pager-btn" ${safeCur >= totalPages ? 'disabled' : ''} onclick="window.__adm_risk_page('${kind}', ${safeCur + 1})">›</button>
                </div>` : '';
            return `
                <div class="adm-risk-block">
                    <div class="adm-risk-title">${esc(title)} <span class="adm-risk-count">(${items.length})</span></div>
                    <div class="adm-risk-rows">${slice.map(renderRow).join('')}</div>
                    ${pager}
                </div>`;
        };

        const ipRows = renderGroup(tt('adm-risk-same-ip'), sip, 'ip', x => `
            <div class="adm-risk-row">
                <div class="adm-risk-row-main">
                    <div><strong>IP</strong> <code>${esc(x.ip)}</code> · ${x.count} ${esc(tt('adm-risk-accounts'))}</div>
                    <div class="adm-risk-row-sub">${(x.accounts || []).slice(0, 3).map(a => esc(a.email)).join(' · ')}${(x.accounts || []).length > 3 ? ` …` : ''}</div>
                </div>
                <button class="adm-risk-detail-btn" onclick='window.__adm_risk_detail("ip", ${JSON.stringify(JSON.stringify(x))})'>${esc(tt('adm-risk-view-detail'))}</button>
            </div>`);

        const fpRows = renderGroup(tt('adm-risk-same-fp'), sfp, 'fp', x => `
            <div class="adm-risk-row">
                <div class="adm-risk-row-main">
                    <div><strong>FP</strong> <code>${esc(x.fingerprint_short || '')}</code> · ${x.count} ${esc(tt('adm-risk-accounts'))}</div>
                    <div class="adm-risk-row-sub">${(x.accounts || []).slice(0, 3).map(a => esc(a.email)).join(' · ')}${(x.accounts || []).length > 3 ? ` …` : ''}</div>
                </div>
                <button class="adm-risk-detail-btn" onclick='window.__adm_risk_detail("fp", ${JSON.stringify(JSON.stringify(x))})'>${esc(tt('adm-risk-view-detail'))}</button>
            </div>`);

        const heavyRows = renderGroup(tt('adm-risk-heavy-ocr'), heavy, 'heavy', x => `
            <div class="adm-risk-row">
                <div class="adm-risk-row-main">
                    <div><strong>${esc(x.email)}</strong> ${x.is_banned ? `<span class="adm-pill-banned">${esc(tt('adm-risk-banned-tag'))}</span>` : ''}</div>
                    <div class="adm-risk-row-sub">${esc(x.plan || '')} · ${x.ocr_today} ${esc(tt('adm-risk-ocr-24h'))}</div>
                </div>
                ${x.is_banned
                    ? `<button class="adm-risk-detail-btn" onclick="window.__adm_unban_user('${x.user_id}')">${esc(tt('adm-drawer-btn-unban'))}</button>`
                    : `<button class="adm-risk-detail-btn danger" onclick="window.__adm_ban_user('${x.user_id}', '${esc(x.email)}')">${esc(tt('adm-drawer-btn-ban'))}</button>`}
            </div>`);

        const evBlock = ev.length ? `
            <div class="adm-risk-block">
                <div class="adm-risk-title">${esc(tt('adm-risk-events-24h'))}</div>
                <div class="adm-risk-tags">
                    ${ev.map(e => `<span class="adm-tag ${e.event === 'disposable_email' || e.event === 'rate_limited_try_later' ? 'adm-tag-warn' : ''}">${esc(e.event)}: ${e.count}</span>`).join('')}
                </div>
            </div>` : '';

        wrap.innerHTML = summary + ipRows + fpRows + heavyRows + evBlock;
    }

    // v118 · export 给 applyLang · 切语言时立即用缓存数据重渲(不等 fetch)
    window.__rerenderAdmRisk = function() { renderAdmRisk(); };

    // v116 · 折叠/展开
    window.__adm_risk_toggle = function() {
        _admRiskState.collapsed = !_admRiskState.collapsed;
        renderAdmRisk();
    };
    // v116 · 分页
    window.__adm_risk_page = function(kind, page) {
        _admRiskState.page[kind] = page;
        renderAdmRisk();
    };

    // v116 · 查看详情 modal · 显示 group 内所有 accounts + 操作按钮
    window.__adm_risk_detail = function(kind, groupJson) {
        let group;
        try { group = JSON.parse(groupJson); } catch(e) { return; }
        const accounts = group.accounts || [];
        const headerKey = kind === 'ip' ? `IP: ${group.ip}` : `Fingerprint: ${group.fingerprint_short || ''}`;

        // 关掉旧的(如果有)
        const old = document.getElementById('adm-risk-detail-modal');
        if (old) old.remove();

        const modal = document.createElement('div');
        modal.id = 'adm-risk-detail-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal modal-md">
                <div class="modal-head">
                    <div class="modal-title">${esc(tt('adm-risk-detail-title'))}</div>
                    <button class="modal-close" onclick="document.getElementById('adm-risk-detail-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="adm-risk-detail-meta">${esc(headerKey)} · ${accounts.length} ${esc(tt('adm-risk-accounts'))}</div>
                    <div class="adm-risk-detail-list" id="adm-risk-detail-list">
                        ${accounts.map(a => `
                            <div class="adm-risk-detail-row" data-uid="${esc(a.user_id)}">
                                <div class="adm-risk-detail-main">
                                    <div><strong>${esc(a.email)}</strong>
                                        ${a.is_banned ? `<span class="adm-pill-banned">${esc(tt('adm-risk-banned-tag'))}</span>` : ''}
                                    </div>
                                    <div class="adm-risk-detail-sub">${esc(a.plan || '')} · ${esc((a.created_at || '').slice(0, 10))}</div>
                                </div>
                                <div class="adm-risk-detail-actions">
                                    ${a.is_banned
                                        ? `<button class="adm-risk-detail-btn" onclick="window.__adm_risk_modal_unban('${esc(a.user_id)}')">${esc(tt('adm-drawer-btn-unban'))}</button>`
                                        : `<button class="adm-risk-detail-btn danger" onclick="window.__adm_risk_modal_ban('${esc(a.user_id)}', '${esc(a.email)}')">${esc(tt('adm-drawer-btn-ban'))}</button>`}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-foot">
                    <button class="btn-ghost" onclick="document.getElementById('adm-risk-detail-modal').remove()">${esc(tt('common-close'))}</button>
                    <button class="btn-danger" onclick='window.__adm_risk_batch_ban(${JSON.stringify(JSON.stringify(accounts))})'>
                        ${esc(tt('adm-risk-batch-ban'))} (${accounts.filter(a => !a.is_banned).length})
                    </button>
                </div>
            </div>`;
        document.body.appendChild(modal);
    };

    // v116 · modal 内单个 ban/unban(操作完后刷新整个风控)
    window.__adm_risk_modal_ban = async function(uid, email) {
        const ok = await showConfirm(tt('adm-confirm-ban', { e: email }), { danger: true });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/users/${uid}/ban`, {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'risk_review' }),
            });
            if (r.ok) {
                showToast(tt('adm-banned'), 'success');
                document.getElementById('adm-risk-detail-modal')?.remove();
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) { showToast(tt('adm-action-fail'), 'error'); }
    };
    window.__adm_risk_modal_unban = async function(uid) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/users/${uid}/unban`, {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) {
                showToast(tt('adm-unbanned'), 'success');
                document.getElementById('adm-risk-detail-modal')?.remove();
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) { showToast(tt('adm-action-fail'), 'error'); }
    };

    // v116 · 批量封禁(modal 底部按钮)
    window.__adm_risk_batch_ban = async function(accountsJson) {
        let accounts;
        try { accounts = JSON.parse(accountsJson); } catch(e) { return; }
        const targets = accounts.filter(a => !a.is_banned).map(a => a.user_id);
        if (!targets.length) { showToast(tt('adm-risk-no-targets'), 'info'); return; }
        const ok = await showConfirm(tt('adm-risk-confirm-batch', { n: targets.length }), { danger: true });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/risk/batch-ban', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_ids: targets, reason: 'risk_batch_ban' }),
            });
            const j = await r.json().catch(() => ({}));
            if (r.ok && j.ok) {
                showToast(tt('adm-risk-batch-done', { n: j.banned || 0 }), 'success');
                document.getElementById('adm-risk-detail-modal')?.remove();
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) { showToast(tt('adm-action-fail'), 'error'); }
    };

    // 路由切换触发(hash 变化时)
    function bindAdminUsersRoute() {
        const fire = () => {
            if (location.hash === '#admin-users') {
                loadAdminUsersPage();
            }
        };
        window.addEventListener('hashchange', fire);
        fire();
    }

    // 把额外 i18n 加进来
    Object.assign(I18N.zh, {
        'nav-admin-users': '用户管理',
        'admin-users-title': '用户管理',
        'admin-users-sub': '注册用户 · 套餐分布 · 待审核付款 · 风控',
        'adm-kpi-today': '今日新增', 'adm-kpi-week': '本周新增', 'adm-kpi-month': '本月新增',
        'adm-kpi-conv': '付费转化',
        'adm-pending-title': '待审核付款',
        'adm-pending-empty': '没有待审核的付款',
        'adm-refresh': '刷新',
        'adm-view-slip': '查看截图',
        'adm-approve': '批准',
        'adm-reject': '拒绝',
        'adm-approved': '已批准 · 用户已升级',
        'adm-rejected': '已拒绝',
        'adm-confirm-reject': '确认拒绝此付款?',
        'adm-action-fail': '操作失败',
        'adm-expiring-title': 'Trial 即将到期(≤ 3 天)',
        'adm-expiring-empty': '无',
        'adm-quick-upgrade': '一键升级',
        'adm-users-title': '所有用户',
        'adm-users-empty': '没有用户',
        // v118.12 · 客户/员工分 tab
        'adm-tab-customers': '客户',
        'adm-cascade-del': '删除账号',
        'adm-cascade-del-tip': '永久删除该账号 + 整个事务所数据 · 不可恢复',
        'adm-cd-title': '永久删除客户账号',
        'adm-cd-warn': '此操作将永久删除该老板 + 旗下所有员工 + 全部识别记录 / 客户档案 / ERP 配置 / 邮箱配置 / 对账数据。删除后不可恢复 · 请确认无误。',
        'adm-cd-c-employees': '员工',
        'adm-cd-c-ocr': '发票识别',
        'adm-cd-c-clients': '客户档案',
        'adm-cd-c-erp': 'ERP 端点',
        'adm-cd-c-pushlog': '推送日志',
        'adm-cd-c-email': '邮箱配置',
        'adm-cd-c-bank': '对账会话',
        'adm-cd-type-username': '请输入要删除的账号「{n}」以确认:',
        'adm-cd-type-password': '输入您(超管)自己的登录密码:',
        'adm-cd-submit': '永久删除',
        'adm-cd-username-mismatch': '账号名不匹配 · 已取消',
        'adm-cd-password-required': '请输入您的密码',
        'adm-cd-password-invalid': '密码错误',
        'adm-cd-cannot-self': '不能删除自己',
        'adm-cd-not-owner': '该用户不是老板账号',
        'adm-cd-ok': '已永久删除',
        'adm-cd-fail': '删除失败',
        'adm-cd-preview-fail': '获取影响范围失败',

        'adm-tab-employees': '员工',
        'adm-employees-empty': '暂无员工',
        'adm-employee-search-ph': '员工名 / 邮箱 / 老板 / 公司',
        'adm-emp-col-name': '员工',
        'adm-emp-col-owner': '所属老板',
        'adm-emp-col-tenant': '事务所',
        // v118.28.6 · 超管员工 tab 只读提示
        'adm-emp-readonly-tip': '本视图为只读 · 员工管理(启用/禁用/重置密码/移除)由所属老板自行操作 · 如需协助请打开老板抽屉',
            'adm-emp-col-actions': '操作',
            'adm-emp-enable': '启用',
            'adm-emp-disable': '禁用',
            'adm-emp-reset-pw': '重置密码',
            'adm-emp-remove': '移除',
            'adm-emp-confirm-enable': '启用',
            'adm-emp-confirm-disable': '禁用',
            'adm-emp-confirm-reset-pw': '为 {n} 重置密码?',
            'adm-emp-confirm-remove': '⚠ 永久移除员工 {n}?\n该员工的账号将被删除 · 此操作不可恢复。',
            'adm-emp-confirm-type-name': '请输入员工名 "{n}" 以确认删除:',
            'adm-emp-name-mismatch': '员工名不匹配 · 已取消',
            'adm-emp-toggle-ok': '操作成功',
            'adm-emp-toggle-fail': '操作失败',
            'adm-emp-new-pw': '新临时密码(请复制并告诉员工):\n\n{n}\n\n下次登录会强制员工改密。',
            'adm-emp-reset-fail': '重置失败',
            'adm-emp-remove-ok': '已移除',
            'adm-emp-copy-and-close': '我已复制',
            'adm-emp-remove-fail': '移除失败',
        'adm-emp-col-status': '状态',
        'adm-emp-col-last-login': '最后登录',
        'adm-emp-col-created': '创建时间',
        'adm-plan-solo': 'Solo',
        'adm-plan-team': 'Team',
        'adm-filter-all': '全部套餐',
        'adm-col-email': '邮箱', 'adm-col-company': '公司', 'adm-col-plan': '套餐', 'adm-search-ph': '邮箱 / 公司名',
        'adm-col-usage': '本月用量', 'adm-col-country': '国家', 'adm-col-actions': '操作',
        'adm-upgrade': '升级', 'adm-ban': '封停',
        // v109.4 · admin modal
        'adm-upgrade-title': '修改套餐',
        'adm-upg-confirm': '确认升级',
        'adm-pick-plan': '请选择套餐',
        'adm-upgrade-ok': '套餐已修改',
        'adm-upgrade-fail': '修改失败',
        'adm-ban-title': '封停账号',
        'adm-ban-warn': '⚠ 封停后该账号将无法登录 · 操作可撤销',
        'adm-ban-reason': '原因',
        'adm-ban-reason-ph': '如:abuse / 欠费 / 测试',
        'adm-ban-confirm': '确认封停',
        'adm-ban-ok': '已封停',
        'adm-ban-fail': '操作失败',
        // v109.4 · 用户详情抽屉
        'adm-drawer-title': '用户详情',
        'adm-drawer-loading': '加载中...',
        'adm-drawer-error': '加载失败 · 请稍后重试',
        'adm-drawer-no-company': '未填写公司',
        'adm-drawer-sec-account': '账户',
        'adm-drawer-sec-contact': '联系方式',
        'adm-drawer-sec-signup': '注册信息',
        'adm-drawer-sec-usage': '使用情况',
        'adm-drawer-sec-payment': '付款记录',
        'adm-drawer-plan': '套餐',
        'adm-drawer-status': '状态',
        'adm-drawer-line': 'LINE',
        'adm-drawer-role': '角色',
        'adm-drawer-email': '邮箱',
        'adm-drawer-phone': '手机',
        'adm-drawer-line-id': 'LINE ID',
        'adm-drawer-country': '国家',
        'adm-drawer-signed-up': '注册时间',
        'adm-drawer-source': '注册来源',
        'adm-drawer-source-direct': '直接访问',
        'adm-drawer-ip': '注册 IP',
        'adm-drawer-fingerprint': '设备指纹',
        'adm-drawer-month-ocr': '本月用量',
        'adm-drawer-total-ocr': '累计 OCR',
        'adm-drawer-last-ocr': '最近识别',
        'adm-drawer-last-login': '最后登录',
        'adm-drawer-payments': '付款次数',
        'adm-drawer-last-payment': '最近付款',
        'adm-drawer-banned': '🚫 已封停',
        'adm-drawer-active': '✓ 正常',
        'adm-drawer-line-linked': '已绑定',
        'adm-drawer-line-not-linked': '未绑定',
        'adm-drawer-risky': '风险用户',
        'adm-drawer-unlimited': '无限',
        'time-just-now': '刚刚',
        'time-mins-ago': '{n} 分钟前',
        'time-hours-ago': '{n} 小时前',
        'time-days-ago': '{n} 天前',
        'adm-risk-title': '⚠ 风控 · 可疑活动',
        'adm-risk-events-24h': '24h 风控事件',
        'adm-risk-same-ip': '同 IP 注册多个账号',
        'adm-risk-same-fp': '同设备指纹注册多个',
        'adm-risk-heavy-ocr': 'OCR 异常用量(24h > 30 张)',
        'adm-risk-stat-groups': '可疑分组',
        'adm-risk-stat-events': '风控事件',
        'adm-risk-expand': '展开查看',
        'adm-risk-collapse': '收起',
        'adm-risk-accounts': '个账号',
        'adm-risk-view-detail': '查看详情',
        'adm-risk-detail-title': '可疑分组详情',
        'adm-risk-batch-ban': '批量封禁',
        'adm-risk-confirm-batch': '确认封禁这 {n} 个账号?此操作可在用户管理中解除',
        'adm-risk-batch-done': '已封禁 {n} 个账号',
        'adm-risk-no-targets': '没有可封禁的账号(均已封禁或为超管)',
        'adm-risk-banned-tag': '已封禁',
        'adm-risk-ocr-24h': '张 / 24h',
        'common-close': '关闭',
        'adm-risk-clean': '✓ 当前无异常',
        'adm-engine-ocr': '单据识别',
        'adm-engine-ocr-backup': '单据识别(备用)',
        'adm-engine-epdf': '电子PDF',
        'adm-engine-vex': '销项税对账',
    });
    Object.assign(I18N.en, {
        'nav-admin-users': 'Users',
        'admin-users-title': 'User Management',
        'admin-users-sub': 'Signups · plan distribution · pending payments · risk control',
        'adm-kpi-today': 'Today', 'adm-kpi-week': 'Week', 'adm-kpi-month': 'Month',
        'adm-kpi-conv': 'Conversion',
        'adm-pending-title': 'Pending Payments',
        'adm-pending-empty': 'No pending payments',
        'adm-refresh': 'Refresh',
        'adm-view-slip': 'View slip',
        'adm-approve': 'Approve', 'adm-reject': 'Reject',
        'adm-approved': 'Approved · user upgraded',
        'adm-rejected': 'Rejected',
        'adm-confirm-reject': 'Confirm reject?',
        'adm-action-fail': 'Action failed',
        'adm-expiring-title': 'Trial expiring soon (≤ 3 days)',
        'adm-expiring-empty': 'None',
        'adm-quick-upgrade': 'Quick upgrade',
        'adm-users-title': 'All Users', 'adm-users-empty': 'No users',
        // v118.12 · customers / employees tabs
        'adm-tab-customers': 'Customers',
        'adm-cascade-del': 'Delete account',
        'adm-cascade-del-tip': 'Permanently delete this account + entire firm data · cannot undo',
        'adm-cd-title': 'Permanently delete customer',
        'adm-cd-warn': 'This will permanently delete the owner + all employees + all OCR records / clients / ERP configs / email configs / reconciliation data. Cannot be undone — please confirm.',
        'adm-cd-c-employees': 'Employees',
        'adm-cd-c-ocr': 'OCR records',
        'adm-cd-c-clients': 'Clients',
        'adm-cd-c-erp': 'ERP endpoints',
        'adm-cd-c-pushlog': 'Push logs',
        'adm-cd-c-email': 'Email accounts',
        'adm-cd-c-bank': 'Bank recon',
        'adm-cd-type-username': 'Type username "{n}" to confirm:',
        'adm-cd-type-password': 'Enter YOUR (super-admin) login password:',
        'adm-cd-submit': 'Permanently delete',
        'adm-cd-username-mismatch': 'Username mismatch · cancelled',
        'adm-cd-password-required': 'Enter your password',
        'adm-cd-password-invalid': 'Wrong password',
        'adm-cd-cannot-self': 'Cannot delete yourself',
        'adm-cd-not-owner': 'Not an owner account',
        'adm-cd-ok': 'Deleted',
        'adm-cd-fail': 'Delete failed',
        'adm-cd-preview-fail': 'Failed to fetch impact',

        'adm-tab-employees': 'Employees',
        'adm-employees-empty': 'No employees yet',
        'adm-employee-search-ph': 'Username / email / owner / firm',
        'adm-emp-col-name': 'Employee',
        'adm-emp-col-owner': 'Owner',
        'adm-emp-col-tenant': 'Firm',
        // v118.28.6
        'adm-emp-readonly-tip': 'Read-only view · Employee management (enable/disable/reset password/remove) is the firm owner\'s responsibility · Open the owner drawer if assistance is needed',
            'adm-emp-col-actions': 'Actions',
            'adm-emp-enable': 'Enable',
            'adm-emp-disable': 'Disable',
            'adm-emp-reset-pw': 'Reset password',
            'adm-emp-remove': 'Remove',
            'adm-emp-confirm-enable': 'Enable',
            'adm-emp-confirm-disable': 'Disable',
            'adm-emp-confirm-reset-pw': 'Reset password for {n}?',
            'adm-emp-confirm-remove': '⚠ Permanently remove employee {n}?\nAccount will be deleted · this action cannot be undone.',
            'adm-emp-confirm-type-name': 'Type employee name "{n}" to confirm:',
            'adm-emp-name-mismatch': 'Name mismatch · cancelled',
            'adm-emp-toggle-ok': 'OK',
            'adm-emp-toggle-fail': 'Failed',
            'adm-emp-new-pw': 'New temp password (copy and tell employee):\n\n{n}\n\nEmployee will be forced to change on next login.',
            'adm-emp-reset-fail': 'Reset failed',
            'adm-emp-remove-ok': 'Removed',
            'adm-emp-copy-and-close': 'Copied',
            'adm-emp-remove-fail': 'Remove failed',
        'adm-emp-col-status': 'Status',
        'adm-emp-col-last-login': 'Last login',
        'adm-emp-col-created': 'Created',
        'adm-plan-solo': 'Solo',
        'adm-plan-team': 'Team',
        'adm-filter-all': 'All plans',
        'adm-col-email': 'Email', 'adm-col-company': 'Company', 'adm-col-plan': 'Plan', 'adm-search-ph': 'Email / Company',
        'adm-col-usage': 'Usage', 'adm-col-country': 'Country', 'adm-col-actions': 'Actions',
        'adm-upgrade': 'Upgrade', 'adm-ban': 'Ban',
        // v109.4 · admin modal
        'adm-upgrade-title': 'Change Plan',
        'adm-upg-confirm': 'Confirm Upgrade',
        'adm-pick-plan': 'Please select a plan',
        'adm-upgrade-ok': 'Plan updated',
        'adm-upgrade-fail': 'Update failed',
        'adm-ban-title': 'Ban Account',
        'adm-ban-warn': '⚠ Banned account cannot login · action is reversible',
        'adm-ban-reason': 'Reason',
        'adm-ban-reason-ph': 'e.g. abuse / unpaid / test',
        'adm-ban-confirm': 'Confirm Ban',
        'adm-ban-ok': 'Banned',
        'adm-ban-fail': 'Failed',
        // v109.4 · user detail drawer
        'adm-drawer-title': 'User Details',
        'adm-drawer-loading': 'Loading...',
        'adm-drawer-error': 'Failed to load · please retry',
        'adm-drawer-no-company': 'No company',
        'adm-drawer-sec-account': 'Account',
        'adm-drawer-sec-contact': 'Contact',
        'adm-drawer-sec-signup': 'Sign-up Info',
        'adm-drawer-sec-usage': 'Usage',
        'adm-drawer-sec-payment': 'Payments',
        'adm-drawer-plan': 'Plan',
        'adm-drawer-status': 'Status',
        'adm-drawer-line': 'LINE',
        'adm-drawer-role': 'Role',
        'adm-drawer-email': 'Email',
        'adm-drawer-phone': 'Phone',
        'adm-drawer-line-id': 'LINE ID',
        'adm-drawer-country': 'Country',
        'adm-drawer-signed-up': 'Signed up',
        'adm-drawer-source': 'Source',
        'adm-drawer-source-direct': 'Direct',
        'adm-drawer-ip': 'Sign-up IP',
        'adm-drawer-fingerprint': 'Device fingerprint',
        'adm-drawer-month-ocr': 'OCR this month',
        'adm-drawer-total-ocr': 'OCR total',
        'adm-drawer-last-ocr': 'Last OCR',
        'adm-drawer-last-login': 'Last login',
        'adm-drawer-payments': 'Payment count',
        'adm-drawer-last-payment': 'Last payment',
        'adm-drawer-banned': '🚫 Banned',
        'adm-drawer-active': '✓ Active',
        'adm-drawer-line-linked': 'Linked',
        'adm-drawer-line-not-linked': 'Not linked',
        'adm-drawer-risky': 'Risk user',
        'adm-drawer-unlimited': 'Unlimited',
        'time-just-now': 'just now',
        'time-mins-ago': '{n} min ago',
        'time-hours-ago': '{n} hr ago',
        'time-days-ago': '{n} days ago',
        'adm-risk-title': '⚠ Risk · Suspicious Activity',
        'adm-risk-events-24h': '24h risk events',
        'adm-risk-same-ip': 'Same IP multi-signups',
        'adm-risk-same-fp': 'Same fingerprint multi-signups',
        'adm-risk-heavy-ocr': 'Heavy OCR (>30 in 24h)',
        'adm-risk-stat-groups': 'suspicious groups',
        'adm-risk-stat-events': 'risk events',
        'adm-risk-expand': 'Expand',
        'adm-risk-collapse': 'Collapse',
        'adm-risk-accounts': 'accounts',
        'adm-risk-view-detail': 'View detail',
        'adm-risk-detail-title': 'Suspicious group detail',
        'adm-risk-batch-ban': 'Batch ban',
        'adm-risk-confirm-batch': 'Ban these {n} accounts? You can unban them later in user management.',
        'adm-risk-batch-done': '{n} accounts banned',
        'adm-risk-no-targets': 'No accounts to ban (all banned or super-admin)',
        'adm-risk-banned-tag': 'Banned',
        'adm-risk-ocr-24h': 'OCRs / 24h',
        'common-close': 'Close',
        'adm-risk-clean': '✓ All clear',
        'adm-engine-ocr': 'Invoice OCR',
        'adm-engine-ocr-backup': 'Invoice OCR (backup)',
        'adm-engine-epdf': 'Electronic PDF',
        'adm-engine-vex': 'Output VAT Reconciliation',
    });
    Object.assign(I18N.th, {
        'nav-admin-users': 'จัดการผู้ใช้',
        'admin-users-title': 'จัดการผู้ใช้',
        'admin-users-sub': 'ผู้สมัคร · แพ็กเกจ · รอตรวจสอบ · ควบคุมความเสี่ยง',
        'adm-kpi-today': 'วันนี้', 'adm-kpi-week': 'สัปดาห์นี้', 'adm-kpi-month': 'เดือนนี้',
        'adm-kpi-conv': 'อัตราชำระ',
        'adm-pending-title': 'รอตรวจสอบการชำระ',
        'adm-pending-empty': 'ไม่มี',
        'adm-refresh': 'รีเฟรช',
        'adm-view-slip': 'ดูสลิป',
        'adm-approve': 'อนุมัติ', 'adm-reject': 'ปฏิเสธ',
        'adm-approved': 'อนุมัติแล้ว · ผู้ใช้ได้รับการอัปเกรด',
        'adm-rejected': 'ปฏิเสธแล้ว',
        'adm-confirm-reject': 'ยืนยันปฏิเสธ?',
        'adm-action-fail': 'ไม่สำเร็จ',
        'adm-expiring-title': 'ทดลองใกล้หมดอายุ (≤ 3 วัน)',
        'adm-expiring-empty': 'ไม่มี',
        'adm-quick-upgrade': 'อัปเกรดทันที',
        'adm-users-title': 'ผู้ใช้ทั้งหมด', 'adm-users-empty': 'ไม่มี',
        // v118.12 · ลูกค้า / พนักงาน
        'adm-tab-customers': 'ลูกค้า',
        'adm-cascade-del': 'ลบบัญชี',
        'adm-cascade-del-tip': 'ลบบัญชีและข้อมูลสำนักงานทั้งหมดอย่างถาวร · ไม่สามารถกู้คืนได้',
        'adm-cd-title': 'ลบลูกค้าอย่างถาวร',
        'adm-cd-warn': 'การดำเนินการนี้จะลบเจ้าของ + พนักงานทั้งหมด + ประวัติ OCR / ลูกค้า / ERP / อีเมล / กระทบยอดทั้งหมดอย่างถาวร · ไม่สามารถกู้คืนได้',
        'adm-cd-c-employees': 'พนักงาน',
        'adm-cd-c-ocr': 'OCR',
        'adm-cd-c-clients': 'ลูกค้า',
        'adm-cd-c-erp': 'ERP',
        'adm-cd-c-pushlog': 'Push logs',
        'adm-cd-c-email': 'อีเมล',
        'adm-cd-c-bank': 'กระทบยอด',
        'adm-cd-type-username': 'พิมพ์ชื่อผู้ใช้ "{n}" เพื่อยืนยัน:',
        'adm-cd-type-password': 'พิมพ์รหัสผ่าน(ผู้ดูแลระบบ)ของคุณ:',
        'adm-cd-submit': 'ลบถาวร',
        'adm-cd-username-mismatch': 'ชื่อไม่ตรงกัน · ยกเลิก',
        'adm-cd-password-required': 'กรอกรหัสผ่าน',
        'adm-cd-password-invalid': 'รหัสผ่านไม่ถูกต้อง',
        'adm-cd-cannot-self': 'ลบตัวเองไม่ได้',
        'adm-cd-not-owner': 'ไม่ใช่บัญชีเจ้าของ',
        'adm-cd-ok': 'ลบแล้ว',
        'adm-cd-fail': 'ลบล้มเหลว',
        'adm-cd-preview-fail': 'ดึงข้อมูลผลกระทบล้มเหลว',

        'adm-tab-employees': 'พนักงาน',
        'adm-employees-empty': 'ยังไม่มีพนักงาน',
        'adm-employee-search-ph': 'ชื่อผู้ใช้ / อีเมล / เจ้าของ / สำนักงาน',
        'adm-emp-col-name': 'พนักงาน',
        'adm-emp-col-owner': 'เจ้าของ',
        'adm-emp-col-tenant': 'สำนักงาน',
        // v118.28.6
        'adm-emp-readonly-tip': 'มุมมองแบบอ่านอย่างเดียว · การจัดการพนักงาน (เปิด/ปิด/รีเซ็ตรหัสผ่าน/ลบ) เป็นหน้าที่ของเจ้าของสำนักงาน · เปิดลิ้นชักเจ้าของหากต้องการช่วยเหลือ',
            'adm-emp-col-actions': 'การดำเนินการ',
            'adm-emp-enable': 'เปิดใช้',
            'adm-emp-disable': 'ปิดใช้',
            'adm-emp-reset-pw': 'รีเซ็ตรหัสผ่าน',
            'adm-emp-remove': 'ลบ',
            'adm-emp-confirm-enable': 'เปิดใช้',
            'adm-emp-confirm-disable': 'ปิดใช้',
            'adm-emp-confirm-reset-pw': 'รีเซ็ตรหัสผ่านให้ {n}?',
            'adm-emp-confirm-remove': '⚠ ลบพนักงาน {n} อย่างถาวร?\nบัญชีจะถูกลบ · ไม่สามารถกู้คืนได้',
            'adm-emp-confirm-type-name': 'พิมพ์ชื่อพนักงาน "{n}" เพื่อยืนยัน:',
            'adm-emp-name-mismatch': 'ชื่อไม่ตรงกัน · ยกเลิก',
            'adm-emp-toggle-ok': 'สำเร็จ',
            'adm-emp-toggle-fail': 'ล้มเหลว',
            'adm-emp-new-pw': 'รหัสผ่านชั่วคราวใหม่(คัดลอกและบอกพนักงาน):\n\n{n}\n\nพนักงานจะถูกบังคับให้เปลี่ยนรหัสในการเข้าสู่ระบบครั้งถัดไป',
            'adm-emp-reset-fail': 'รีเซ็ตล้มเหลว',
            'adm-emp-remove-ok': 'ลบแล้ว',
            'adm-emp-copy-and-close': 'คัดลอกแล้ว',
            'adm-emp-remove-fail': 'ลบล้มเหลว',
        'adm-emp-col-status': 'สถานะ',
        'adm-emp-col-last-login': 'เข้าใช้ล่าสุด',
        'adm-emp-col-created': 'สร้างเมื่อ',
        'adm-plan-solo': 'Solo',
        'adm-plan-team': 'Team',
        'adm-filter-all': 'แพ็กเกจทั้งหมด',
        'adm-col-email': 'อีเมล', 'adm-col-company': 'บริษัท', 'adm-col-plan': 'แพ็กเกจ', 'adm-search-ph': 'อีเมล / บริษัท',
        'adm-col-usage': 'ใช้แล้ว', 'adm-col-country': 'ประเทศ', 'adm-col-actions': 'จัดการ',
        'adm-upgrade': 'อัปเกรด', 'adm-ban': 'ระงับ',
        // v109.4 · admin modal
        'adm-upgrade-title': 'เปลี่ยนแพ็กเกจ',
        'adm-upg-confirm': 'ยืนยันอัปเกรด',
        'adm-pick-plan': 'กรุณาเลือกแพ็กเกจ',
        'adm-upgrade-ok': 'อัปเดตแพ็กเกจแล้ว',
        'adm-upgrade-fail': 'อัปเดตไม่สำเร็จ',
        'adm-ban-title': 'ระงับบัญชี',
        'adm-ban-warn': '⚠ บัญชีที่ถูกระงับจะเข้าสู่ระบบไม่ได้ · สามารถยกเลิกได้',
        'adm-ban-reason': 'เหตุผล',
        'adm-ban-reason-ph': 'เช่น abuse / ค้างชำระ / ทดสอบ',
        'adm-ban-confirm': 'ยืนยันระงับ',
        'adm-ban-ok': 'ระงับแล้ว',
        'adm-ban-fail': 'ล้มเหลว',
        // v109.4 · ลิ้นชักรายละเอียดผู้ใช้
        'adm-drawer-title': 'รายละเอียดผู้ใช้',
        'adm-drawer-loading': 'กำลังโหลด...',
        'adm-drawer-error': 'โหลดไม่สำเร็จ · ลองใหม่',
        'adm-drawer-no-company': 'ไม่ได้กรอกบริษัท',
        'adm-drawer-sec-account': 'บัญชี',
        'adm-drawer-sec-contact': 'การติดต่อ',
        'adm-drawer-sec-signup': 'ข้อมูลสมัคร',
        'adm-drawer-sec-usage': 'การใช้งาน',
        'adm-drawer-sec-payment': 'การชำระ',
        'adm-drawer-plan': 'แพ็กเกจ',
        'adm-drawer-status': 'สถานะ',
        'adm-drawer-line': 'LINE',
        'adm-drawer-role': 'บทบาท',
        'adm-drawer-email': 'อีเมล',
        'adm-drawer-phone': 'โทรศัพท์',
        'adm-drawer-line-id': 'LINE ID',
        'adm-drawer-country': 'ประเทศ',
        'adm-drawer-signed-up': 'สมัครเมื่อ',
        'adm-drawer-source': 'ช่องทาง',
        'adm-drawer-source-direct': 'เข้าตรง',
        'adm-drawer-ip': 'IP ที่สมัคร',
        'adm-drawer-fingerprint': 'ลายนิ้วมืออุปกรณ์',
        'adm-drawer-month-ocr': 'OCR เดือนนี้',
        'adm-drawer-total-ocr': 'OCR รวม',
        'adm-drawer-last-ocr': 'OCR ล่าสุด',
        'adm-drawer-last-login': 'เข้าสู่ระบบล่าสุด',
        'adm-drawer-payments': 'จำนวนชำระ',
        'adm-drawer-last-payment': 'ชำระล่าสุด',
        'adm-drawer-banned': '🚫 ระงับแล้ว',
        'adm-drawer-active': '✓ ปกติ',
        'adm-drawer-line-linked': 'เชื่อมแล้ว',
        'adm-drawer-line-not-linked': 'ยังไม่เชื่อม',
        'adm-drawer-risky': 'ผู้ใช้เสี่ยง',
        'adm-drawer-unlimited': 'ไม่จำกัด',
        'time-just-now': 'เพิ่งจะ',
        'time-mins-ago': '{n} นาทีที่แล้ว',
        'time-hours-ago': '{n} ชั่วโมงที่แล้ว',
        'time-days-ago': '{n} วันที่แล้ว',
        'adm-risk-title': '⚠ ควบคุมความเสี่ยง',
        'adm-risk-events-24h': 'เหตุการณ์ 24h',
        'adm-risk-same-ip': 'IP เดียวกันสมัครหลายบัญชี',
        'adm-risk-same-fp': 'อุปกรณ์เดียวกันสมัครหลายบัญชี',
        'adm-risk-heavy-ocr': 'OCR ผิดปกติ (>30 ใน 24h)',
        'adm-risk-stat-groups': 'กลุ่มน่าสงสัย',
        'adm-risk-stat-events': 'เหตุการณ์ความเสี่ยง',
        'adm-risk-expand': 'ขยาย',
        'adm-risk-collapse': 'ย่อ',
        'adm-risk-accounts': 'บัญชี',
        'adm-risk-view-detail': 'ดูรายละเอียด',
        'adm-risk-detail-title': 'รายละเอียดกลุ่มน่าสงสัย',
        'adm-risk-batch-ban': 'แบนหลายบัญชี',
        'adm-risk-confirm-batch': 'แบน {n} บัญชีนี้? สามารถปลดแบนภายหลังได้',
        'adm-risk-batch-done': 'แบน {n} บัญชีเรียบร้อย',
        'adm-risk-no-targets': 'ไม่มีบัญชีให้แบน (แบนหมดแล้วหรือเป็นแอดมิน)',
        'adm-risk-banned-tag': 'ถูกแบน',
        'adm-risk-ocr-24h': 'OCR / 24 ชม.',
        'common-close': 'ปิด',
        'adm-risk-clean': '✓ ไม่มีความผิดปกติ',
        'adm-engine-ocr': 'OCR หลัก',
        'adm-engine-ocr-backup': 'OCR สำรอง',
        'adm-engine-epdf': 'PDF อิเล็กทรอนิกส์',
        'adm-engine-vex': 'กระทบยอดภาษีขาย',
    });
    Object.assign(I18N.ja, {
        'nav-admin-users': 'ユーザー管理',
        'admin-users-title': 'ユーザー管理',
        'admin-users-sub': '登録 · プラン分布 · 審査待ち · リスク管理',
        'adm-kpi-today': '今日', 'adm-kpi-week': '今週', 'adm-kpi-month': '今月',
        'adm-kpi-conv': '有料転換',
        'adm-pending-title': '審査待ちの支払',
        'adm-pending-empty': 'なし',
        'adm-refresh': '更新',
        'adm-view-slip': 'スリップ',
        'adm-approve': '承認', 'adm-reject': '拒否',
        'adm-approved': '承認 · ユーザー昇格',
        'adm-rejected': '拒否済',
        'adm-confirm-reject': '拒否しますか?',
        'adm-action-fail': '失敗',
        'adm-expiring-title': '試用期限間近(≤ 3 日)',
        'adm-expiring-empty': 'なし',
        'adm-quick-upgrade': '即昇格',
        'adm-users-title': '全ユーザー', 'adm-users-empty': 'なし',
        // v118.12 · 顧客 / 社員
        'adm-tab-customers': '顧客',
        'adm-cascade-del': 'アカウント削除',
        'adm-cascade-del-tip': 'アカウントと事務所データを完全削除 · 復元不可',
        'adm-cd-title': '顧客を完全削除',
        'adm-cd-warn': 'オーナー + 全社員 + OCR履歴 / 顧客 / ERP / メール / 銀行照合データを完全削除します · 復元不可 · 確認してください',
        'adm-cd-c-employees': '社員',
        'adm-cd-c-ocr': 'OCR',
        'adm-cd-c-clients': '顧客',
        'adm-cd-c-erp': 'ERP',
        'adm-cd-c-pushlog': 'プッシュログ',
        'adm-cd-c-email': 'メール',
        'adm-cd-c-bank': '銀行照合',
        'adm-cd-type-username': 'ユーザー名 "{n}" を入力して確認:',
        'adm-cd-type-password': 'あなた(管理者)のログインパスワードを入力:',
        'adm-cd-submit': '完全削除',
        'adm-cd-username-mismatch': '名前が一致しません · キャンセル',
        'adm-cd-password-required': 'パスワードを入力',
        'adm-cd-password-invalid': 'パスワード違い',
        'adm-cd-cannot-self': '自分を削除できません',
        'adm-cd-not-owner': 'オーナーアカウントではない',
        'adm-cd-ok': '削除済み',
        'adm-cd-fail': '削除失敗',
        'adm-cd-preview-fail': '影響範囲取得失敗',

        'adm-tab-employees': '社員',
        'adm-employees-empty': '社員なし',
        'adm-employee-search-ph': 'ユーザー名 / メール / オーナー / 事務所',
        'adm-emp-col-name': '社員',
        'adm-emp-col-owner': 'オーナー',
        'adm-emp-col-tenant': '事務所',
        // v118.28.6
        'adm-emp-readonly-tip': '読み取り専用ビュー · 社員管理(有効化/無効化/パスワードリセット/削除)は事務所オーナーの担当 · サポートが必要な場合はオーナードロワーを開いてください',
            'adm-emp-col-actions': '操作',
            'adm-emp-enable': '有効化',
            'adm-emp-disable': '無効化',
            'adm-emp-reset-pw': 'パスワードリセット',
            'adm-emp-remove': '削除',
            'adm-emp-confirm-enable': '有効化',
            'adm-emp-confirm-disable': '無効化',
            'adm-emp-confirm-reset-pw': '{n} のパスワードをリセットしますか?',
            'adm-emp-confirm-remove': '⚠ 社員 {n} を完全に削除しますか?\nアカウントは削除されます · この操作は元に戻せません',
            'adm-emp-confirm-type-name': '社員名 "{n}" を入力して確認:',
            'adm-emp-name-mismatch': '名前が一致しません · キャンセル',
            'adm-emp-toggle-ok': '成功',
            'adm-emp-toggle-fail': '失敗',
            'adm-emp-new-pw': '新しい一時パスワード(コピーして社員に伝える):\n\n{n}\n\n次回ログイン時に強制的にパスワード変更されます',
            'adm-emp-reset-fail': 'リセット失敗',
            'adm-emp-remove-ok': '削除済み',
            'adm-emp-copy-and-close': 'コピー済み',
            'adm-emp-remove-fail': '削除失敗',
        'adm-emp-col-status': '状態',
        'adm-emp-col-last-login': '最終ログイン',
        'adm-emp-col-created': '作成日',
        'adm-plan-solo': 'Solo',
        'adm-plan-team': 'Team',
        'adm-filter-all': '全プラン',
        'adm-col-email': 'メール', 'adm-col-company': '会社', 'adm-col-plan': 'プラン', 'adm-search-ph': 'メール / 会社',
        'adm-col-usage': '使用量', 'adm-col-country': '国', 'adm-col-actions': '操作',
        'adm-upgrade': '昇格', 'adm-ban': '停止',
        // v109.4 · admin modal
        'adm-upgrade-title': 'プラン変更',
        'adm-upg-confirm': 'アップグレード確認',
        'adm-pick-plan': 'プランを選択してください',
        'adm-upgrade-ok': 'プランを変更しました',
        'adm-upgrade-fail': '変更に失敗しました',
        'adm-ban-title': 'アカウント停止',
        'adm-ban-warn': '⚠ 停止されたアカウントはログインできません · 操作は取り消し可能',
        'adm-ban-reason': '理由',
        'adm-ban-reason-ph': '例:abuse / 未払い / テスト',
        'adm-ban-confirm': '停止確認',
        'adm-ban-ok': '停止しました',
        'adm-ban-fail': '失敗',
        // v109.4 · ユーザー詳細ドロワー
        'adm-drawer-title': 'ユーザー詳細',
        'adm-drawer-loading': '読み込み中...',
        'adm-drawer-error': '読み込み失敗 · 再試行してください',
        'adm-drawer-no-company': '会社未入力',
        'adm-drawer-sec-account': 'アカウント',
        'adm-drawer-sec-contact': '連絡先',
        'adm-drawer-sec-signup': '登録情報',
        'adm-drawer-sec-usage': '利用状況',
        'adm-drawer-sec-payment': '支払い',
        'adm-drawer-plan': 'プラン',
        'adm-drawer-status': '状態',
        'adm-drawer-line': 'LINE',
        'adm-drawer-role': '役割',
        'adm-drawer-email': 'メール',
        'adm-drawer-phone': '電話',
        'adm-drawer-line-id': 'LINE ID',
        'adm-drawer-country': '国',
        'adm-drawer-signed-up': '登録日時',
        'adm-drawer-source': '登録元',
        'adm-drawer-source-direct': '直接アクセス',
        'adm-drawer-ip': '登録 IP',
        'adm-drawer-fingerprint': 'デバイス指紋',
        'adm-drawer-month-ocr': '今月の OCR',
        'adm-drawer-total-ocr': '累計 OCR',
        'adm-drawer-last-ocr': '最終 OCR',
        'adm-drawer-last-login': '最終ログイン',
        'adm-drawer-payments': '支払い回数',
        'adm-drawer-last-payment': '最終支払い',
        'adm-drawer-banned': '🚫 停止中',
        'adm-drawer-active': '✓ 正常',
        'adm-drawer-line-linked': '連携済',
        'adm-drawer-line-not-linked': '未連携',
        'adm-drawer-risky': 'リスクユーザー',
        'adm-drawer-unlimited': '無制限',
        'time-just-now': 'たった今',
        'time-mins-ago': '{n} 分前',
        'time-hours-ago': '{n} 時間前',
        'time-days-ago': '{n} 日前',
        'adm-risk-title': '⚠ リスク · 不審な活動',
        'adm-risk-events-24h': '24h リスクイベント',
        'adm-risk-same-ip': '同 IP 複数登録',
        'adm-risk-same-fp': '同指紋複数登録',
        'adm-risk-heavy-ocr': '異常 OCR(24h で 30 超)',
        'adm-risk-stat-groups': '不審グループ',
        'adm-risk-stat-events': 'リスクイベント',
        'adm-risk-expand': '展開',
        'adm-risk-collapse': '折りたたむ',
        'adm-risk-accounts': 'アカウント',
        'adm-risk-view-detail': '詳細を見る',
        'adm-risk-detail-title': '不審グループ詳細',
        'adm-risk-batch-ban': '一括停止',
        'adm-risk-confirm-batch': '{n} アカウントを停止しますか?後で解除可能。',
        'adm-risk-batch-done': '{n} アカウント停止完了',
        'adm-risk-no-targets': '停止できるアカウントがありません',
        'adm-risk-banned-tag': '停止中',
        'adm-risk-ocr-24h': 'OCR / 24h',
        'common-close': '閉じる',
        'adm-risk-clean': '✓ 異常なし',
        'adm-engine-ocr': '請求書認識',
        'adm-engine-ocr-backup': '請求書認識（予備）',
        'adm-engine-epdf': '電子PDF',
        'adm-engine-vex': '売上税報告チェック',
    });

    document.addEventListener('DOMContentLoaded', () => {
        // 显示 admin 侧栏项(super_admin 才能看见)· 复用现有 nav-admin-only 类
        // home.js 里已经有逻辑根据 user.is_super_admin 显示这些
        loadPlan();
        bindAdminUsersRoute();
        // 绑定后台筛选事件
        const planFilter = document.getElementById('adm-plan-filter');
        if (planFilter) planFilter.addEventListener('change', loadAdmUserList);
        const search = document.getElementById('adm-user-search');
        if (search) {
            let timer;
            search.addEventListener('input', () => {
                clearTimeout(timer);
                timer = setTimeout(loadAdmUserList, 300);
            });
        }
        const refr = document.getElementById('adm-refresh-pending');
        if (refr) refr.addEventListener('click', loadAdminUsersPage);

        setInterval(loadPlan, 60000); // 1 分钟
    });
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        loadPlan();
        bindAdminUsersRoute();
        setInterval(loadPlan, 60000);
    }

    // v109.4 · 暴露给 routeTo 调用 · 让侧栏点击能直接触发表格加载
    window.loadAdminUsersPage = loadAdminUsersPage;

    // ============================================================
    // v118.12 · 员工 tab(新)· 仅超管查看 · 显示所有 role=member 用户
    // ============================================================
    let _admEmployeesCache = [];

    async function loadAdmEmployees() {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        try {
            const r = await fetch('/api/admin/employees', { headers: { 'Authorization': 'Bearer ' + tok } });
            if (r.status === 403) return;
            const data = await r.json();
            _admEmployeesCache = data.employees || [];
            renderAdmEmployees(_admEmployeesCache);
        } catch (e) {
            console.error('loadAdmEmployees', e);
        }
    }

    function renderAdmEmployees(employees) {
        const wrap = document.getElementById('adm-employees-table');
        if (!wrap) return;
        // 应用搜索过滤
        const q = (document.getElementById('adm-employee-search')?.value || '').toLowerCase().trim();
        const filtered = q
            ? employees.filter(e =>
                (e.username || '').toLowerCase().includes(q) ||
                (e.email || '').toLowerCase().includes(q) ||
                (e.tenant_name || '').toLowerCase().includes(q) ||
                (e.owner_username || '').toLowerCase().includes(q))
            : employees;
        if (!filtered.length) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-employees-empty'))}</div>`;
            return;
        }
        // v118.28.6 · 只读化 · 砍「禁用/启用 / 重置密码 / 移除」3 个写按钮
        // 行业惯例:Xero/QuickBooks/Stripe 超管对客户内部员工 = 只读 + 跳老板抽屉
        wrap.innerHTML = `
            <div class="adm-emp-readonly-tip">${esc(tt('adm-emp-readonly-tip'))}</div>
            <div class="adm-emp-row adm-emp-row-head">
                <div>${esc(tt('adm-emp-col-name'))}</div>
                <div>${esc(tt('adm-emp-col-owner'))}</div>
                <div>${esc(tt('adm-emp-col-tenant'))}</div>
                <div>${esc(tt('adm-emp-col-status'))}</div>
                <div>${esc(tt('adm-emp-col-last-login'))}</div>
            </div>
            ${filtered.map(e => {
                const statusCls = (e.is_active === false) ? 'adm-emp-status-disabled' : 'adm-emp-status-active';
                const statusTxt = (e.is_active === false) ? tt('team-status-disabled') : tt('team-status-active');
                const lastLogin = e.last_login_at
                    ? new Date(e.last_login_at).toLocaleDateString()
                    : tt('team-never-login');
                return `
                    <div class="adm-emp-row">
                        <div>
                            <div class="adm-emp-cell-strong">${esc(e.username || '?')}</div>
                            <div class="adm-emp-cell-mute">${esc(e.email || '—')}</div>
                        </div>
                        <div>
                            ${e.owner_id ? `<a class="adm-emp-owner-link" onclick="window.__adm_open_user_drawer('${esc(e.owner_id)}')">${esc(e.owner_username || e.owner_email || '—')}</a>` : '—'}
                        </div>
                        <div class="adm-emp-cell-mute">${esc(e.tenant_name || '—')}</div>
                        <div class="${statusCls}">${esc(statusTxt)}</div>
                        <div class="adm-emp-cell-mute">${esc(lastLogin)}</div>
                    </div>
                `;
            }).join('')}
        `;
    }

    // v118.13 · 员工 tab 操作处理 · v118.14 改用统一 modal
    window.__adm_emp_toggle = async function(employeeId, username, makeActive) {
        if (!employeeId) return;
        const verb = makeActive ? (tt('adm-emp-confirm-enable') || '启用') : (tt('adm-emp-confirm-disable') || '禁用');
        const ok = await showConfirm(`${verb} ${username}?`, {
            title: tt('adm-emp-col-actions') || '操作',
            danger: !makeActive,
        });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/employees/${encodeURIComponent(employeeId)}/active`, {
                method: 'PATCH',
                headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !!makeActive }),
            });
            if (r.ok) {
                showToast(tt('adm-emp-toggle-ok') || '操作成功', 'success');
                loadAdmEmployees();
            } else {
                showToast(tt('adm-emp-toggle-fail') || '操作失败', 'error');
            }
        } catch (e) { showToast(tt('adm-emp-toggle-fail') || '操作失败', 'error'); }
    };

    window.__adm_emp_reset_pw = async function(employeeId, username) {
        if (!employeeId) return;
        const ok = await showConfirm(
            (tt('adm-emp-confirm-reset-pw') || '为 {n} 重置密码?').replace('{n}', username),
            { title: tt('adm-emp-reset-pw') || '重置密码' }
        );
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/employees/${encodeURIComponent(employeeId)}/reset-password`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
            });
            const data = await r.json();
            if (r.ok && data.new_password) {
                // 用统一 modal · 单按钮信息提示(替代 alert)
                await showConfirm(
                    (tt('adm-emp-new-pw') || '新临时密码(请复制并告诉员工):\n\n{n}\n\n下次登录会强制员工改密。').replace('{n}', data.new_password),
                    {
                        title: tt('adm-emp-reset-pw') || '重置密码',
                        okText: tt('adm-emp-copy-and-close') || '我已复制',
                        hideCancel: true,
                    }
                );
            } else {
                showToast(tt('adm-emp-reset-fail') || '重置失败', 'error');
            }
        } catch (e) { showToast(tt('adm-emp-reset-fail') || '重置失败', 'error'); }
    };

    window.__adm_emp_remove = async function(employeeId, username) {
        if (!employeeId) return;
        // 第 1 步:danger confirm
        const ok1 = await showConfirm(
            (tt('adm-emp-confirm-remove') || '⚠ 永久移除员工 {n}?\n该员工的账号将被删除 · 此操作不可恢复。').replace('{n}', username),
            { title: tt('adm-emp-remove') || '移除', danger: true }
        );
        if (!ok1) return;
        // 第 2 步:输入员工名再次确认 · 用 promptInput 模式
        const typed = await showConfirm(
            (tt('adm-emp-confirm-type-name') || '请输入员工名 "{n}" 以确认删除:').replace('{n}', username),
            {
                title: tt('adm-emp-remove') || '移除',
                danger: true,
                promptInput: true,
                placeholder: username,
                okText: tt('adm-emp-remove') || '移除',
            }
        );
        if (typed === null) return; // 取消
        if (typed !== username) {
            showToast(tt('adm-emp-name-mismatch') || '员工名不匹配 · 已取消', 'info');
            return;
        }
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/employees/${encodeURIComponent(employeeId)}`, {
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) {
                showToast(tt('adm-emp-remove-ok') || '已移除', 'success');
                loadAdmEmployees();
            } else {
                showToast(tt('adm-emp-remove-fail') || '移除失败', 'error');
            }
        } catch (e) { showToast(tt('adm-emp-remove-fail') || '移除失败', 'error'); }
    };

    // tab 切换
    document.addEventListener('click', (ev) => {
        const tabBtn = ev.target.closest('.adm-tab[data-adm-tab]');
        if (!tabBtn) return;
        const targetTab = tabBtn.dataset.admTab;
        document.querySelectorAll('.adm-tab[data-adm-tab]').forEach(b =>
            b.classList.toggle('active', b.dataset.admTab === targetTab));
        document.querySelectorAll('[data-adm-tab-pane]').forEach(p => {
            p.style.display = (p.dataset.admTabPane === targetTab) ? '' : 'none';
        });
        document.querySelectorAll('[data-adm-tab-filter]').forEach(f => {
            f.style.display = (f.dataset.admTabFilter === targetTab) ? '' : 'none';
        });
        if (targetTab === 'employees') loadAdmEmployees();
        if (targetTab === 'logs') loadAdmLogs(1);
    });

    // 员工搜索 · 实时过滤
    document.addEventListener('input', (ev) => {
        if (ev.target && ev.target.id === 'adm-employee-search') {
            renderAdmEmployees(_admEmployeesCache);
        }
        if (ev.target && ev.target.id === 'adm-logs-search') {
            clearTimeout(window.__admLogsSearchTimer);
            window.__admLogsSearchTimer = setTimeout(function() {
                _admLogsState.q = (ev.target.value || '').trim();
                loadAdmLogs(1);
            }, 350);
        }
    });

    // v118.29.0 · CSV 导出 · 用 fetch 拿 token + blob 下载(避免 GET URL 暴露 token)
    async function _csvDownload(url, filename) {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        try {
            const resp = await fetch(url, { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!resp.ok) {
                showToast(tt('adm-csv-failed') || 'Export failed', 'error');
                return;
            }
            const blob = await resp.blob();
            const a = document.createElement('a');
            const objUrl = URL.createObjectURL(blob);
            a.href = objUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            setTimeout(function() {
                URL.revokeObjectURL(objUrl);
                a.remove();
            }, 100);
            showToast(tt('adm-csv-ok') || 'Exported', 'success');
        } catch (e) {
            showToast(tt('adm-csv-failed') || 'Export failed', 'error');
        }
    }

    document.addEventListener('click', function(ev) {
        const btnUsers = ev.target.closest('#adm-users-csv-btn');
        if (btnUsers) {
            ev.preventDefault();
            _csvDownload('/api/admin/users.csv', 'pearnly_users.csv');
            return;
        }
        const btnLogs = ev.target.closest('#adm-logs-csv-btn');
        if (btnLogs) {
            ev.preventDefault();
            const q = encodeURIComponent(_admLogsState.q || '');
            _csvDownload('/api/admin/logs.csv?q=' + q, 'pearnly_logs.csv');
            return;
        }
        // 分页器按钮
        const pgBtn = ev.target.closest('.adm-pager-btn[data-adm-page]');
        if (pgBtn && !pgBtn.disabled) {
            const targetPage = parseInt(pgBtn.dataset.admPage, 10);
            const scope = pgBtn.dataset.admPagerScope;
            if (scope === 'logs') loadAdmLogs(targetPage);
        }
    });

    // ============================================================
    // v118.29.0 · 操作日志加载 + 渲染 + 分页
    // ============================================================
    const _admLogsState = { page: 1, per_page: 50, q: '', total: 0, rows: [] };

    async function loadAdmLogs(page) {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        const tbl = document.getElementById('adm-logs-table');
        if (tbl) tbl.innerHTML = '<div class="adm-log-empty">' + esc(tt('adm-logs-loading') || 'Loading...') + '</div>';
        _admLogsState.page = page || 1;
        try {
            const url = '/api/admin/logs?page=' + _admLogsState.page +
                '&per_page=' + _admLogsState.per_page +
                '&q=' + encodeURIComponent(_admLogsState.q || '');
            const r = await fetch(url, { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!r.ok) throw new Error('http_' + r.status);
            const data = await r.json();
            _admLogsState.rows = data.logs || [];
            _admLogsState.total = data.total || 0;
            renderAdmLogs();
            renderAdmLogsPager();
        } catch (e) {
            if (tbl) tbl.innerHTML = '<div class="adm-log-empty">' + esc(tt('adm-logs-fail') || 'Failed to load') + '</div>';
        }
    }

    function renderAdmLogs() {
        const tbl = document.getElementById('adm-logs-table');
        if (!tbl) return;
        const rows = _admLogsState.rows || [];
        if (!rows.length) {
            tbl.innerHTML = '<div class="adm-log-empty">' + esc(tt('adm-logs-empty') || 'No logs') + '</div>';
            return;
        }
        const head = `
            <div class="adm-log-row adm-log-head">
                <div>${esc(tt('adm-log-time') || 'Time')}</div>
                <div>${esc(tt('adm-log-actor') || 'Actor')}</div>
                <div>${esc(tt('adm-log-action') || 'Action')}</div>
                <div>${esc(tt('adm-log-target') || 'Target')}</div>
                <div>${esc(tt('adm-log-ip') || 'IP')}</div>
            </div>`;
        const body = rows.map(function(l) {
            let timeStr = '';
            if (l.created_at) {
                try {
                    const d = new Date(l.created_at);
                    timeStr = d.toLocaleString();
                } catch (e) { timeStr = l.created_at; }
            }
            const actor = (l.actor_username || '-') + (l.actor_is_super ? ' ⭐' : '');
            return `
                <div class="adm-log-row">
                    <div class="adm-log-time" data-label="${esc(tt('adm-log-time') || 'Time')}">${esc(timeStr)}</div>
                    <div class="adm-log-actor" data-label="${esc(tt('adm-log-actor') || 'Actor')}">${esc(actor)}</div>
                    <div data-label="${esc(tt('adm-log-action') || 'Action')}"><span class="adm-log-action">${esc(l.action || '-')}</span></div>
                    <div class="adm-log-target" data-label="${esc(tt('adm-log-target') || 'Target')}">${esc(l.target_name || l.target_type || '-')}</div>
                    <div class="adm-log-ip" data-label="${esc(tt('adm-log-ip') || 'IP')}">${esc(l.ip || '-')}</div>
                </div>`;
        }).join('');
        tbl.innerHTML = head + body;
    }

    function renderAdmLogsPager() {
        const wrap = document.getElementById('adm-pager-logs');
        if (!wrap) return;
        const total = _admLogsState.total || 0;
        const page = _admLogsState.page || 1;
        const per = _admLogsState.per_page || 50;
        const totalPages = Math.max(1, Math.ceil(total / per));
        const info = (tt('adm-pager-total') || 'Total {n}').replace('{n}', total);
        const pageStr = (tt('adm-pager-page') || 'Page {p} / {t}').replace('{p}', page).replace('{t}', totalPages);
        wrap.style.display = '';
        wrap.innerHTML = `
            <div class="adm-pager-info">${esc(info)}</div>
            <div class="adm-pager-ctrl">
                <button class="adm-pager-btn" type="button" data-adm-page="${page - 1}" data-adm-pager-scope="logs" ${page <= 1 ? 'disabled' : ''}>← ${esc(tt('adm-pager-prev') || 'Prev')}</button>
                <span class="adm-pager-page">${esc(pageStr)}</span>
                <button class="adm-pager-btn" type="button" data-adm-page="${page + 1}" data-adm-pager-scope="logs" ${page >= totalPages ? 'disabled' : ''}>${esc(tt('adm-pager-next') || 'Next')} →</button>
            </div>`;
    }

    window.loadAdmEmployees = loadAdmEmployees;
})();
// ============================================================
// v109.3 END
// ============================================================

// ============================================================
// v109.4 · 修改密码模块 · 独立 IIFE
// ============================================================
(function () {
    'use strict';

    // 密码强度评估(0-3)
    function strength(pw) {
        let s = 0;
        if (pw.length >= 8) s++;
        if (pw.length >= 12) s++;
        if (/[a-zA-Z]/.test(pw) && /\d/.test(pw)) s++;
        if (/[^a-zA-Z0-9]/.test(pw)) s++;
        return Math.min(3, s);
    }

    // 显示消息(成功 / 失败)
    function showMsg(text, type) {
        const el = document.getElementById('cpw-msg');
        if (!el) return;
        el.textContent = text;
        el.className = 'cpw-msg ' + (type || '');
    }

    // 翻译 · 走全局 t()
    function tt(key) {
        return (typeof t === 'function') ? t(key) : key;
    }

    function bindEvents() {
        // v109.4 · 防 Chrome/Edge autofill 关键技巧:页面加载时字段是 readonly · 用户点击/聚焦时才移除 readonly
        // 这样浏览器不会触发 autofill(autofill 只对非 readonly 字段生效)
        const cpwInputs = ['cpw-old', 'cpw-new', 'cpw-confirm'];
        cpwInputs.forEach(id => {
            const inp = document.getElementById(id);
            if (!inp) return;
            // 页面加载强制清空 + 设 readonly 避免 autofill
            inp.value = '';
            inp.setAttribute('readonly', 'readonly');
            // focus 时移除 readonly · 让用户能输入
            inp.addEventListener('focus', function () {
                this.removeAttribute('readonly');
            });
            // blur 时清空(防键盘 manager 残留)— 不做这个 · 用户可能想编辑后再回来确认 newpw
        });

        // 设置页打开时再次清空(用户可能已经填了之后切走又回来)
        // 通过监听 settings tab 切换实现
        document.querySelectorAll('.settings-nav-item[data-settings-tab="account"]').forEach(tab => {
            tab.addEventListener('click', () => {
                setTimeout(() => {
                    cpwInputs.forEach(id => {
                        const inp = document.getElementById(id);
                        if (inp) {
                            inp.value = '';
                            inp.setAttribute('readonly', 'readonly');
                        }
                    });
                    const bar = document.getElementById('cpw-strength-bar');
                    if (bar) { bar.style.width = '0%'; bar.className = 'cpw-strength-bar'; }
                    showMsg('', '');
                }, 100);
            });
        });

        // 眼睛图标 · 切换密码可见
        document.querySelectorAll('.cpw-eye').forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.target;
                const inp = document.getElementById(target);
                if (!inp) return;
                inp.type = inp.type === 'password' ? 'text' : 'password';
            });
        });

        // 新密码强度条
        const newInp = document.getElementById('cpw-new');
        const bar = document.getElementById('cpw-strength-bar');
        if (newInp && bar) {
            newInp.addEventListener('input', () => {
                const s = strength(newInp.value);
                const widths = ['0%', '33%', '66%', '100%'];
                const cls = ['', 'weak', 'medium', 'strong'];
                bar.style.width = widths[s];
                bar.className = 'cpw-strength-bar ' + cls[s];
            });
        }

        // v109.4 · 「忘记当前密码?」链接 → 弹窗确认发送重置邮件
        const forgotLink = document.getElementById('cpw-forgot-link');
        if (forgotLink) {
            forgotLink.addEventListener('click', () => openForgotCurrentPwModal());
        }

        // 提交
        const btn = document.getElementById('btn-change-pw');
        if (!btn) return;
        btn.addEventListener('click', async () => {
            const oldEl = document.getElementById('cpw-old');
            const newEl = document.getElementById('cpw-new');
            const cfmEl = document.getElementById('cpw-confirm');
            if (!oldEl || !newEl || !cfmEl) return;

            const oldPw = oldEl.value;
            const newPw = newEl.value;
            const cfm   = cfmEl.value;

            // 前端校验
            if (!oldPw || !newPw || !cfm) {
                showMsg(tt('settings-change-pw-empty'), 'error');
                return;
            }
            if (newPw.length < 8) {
                showMsg(tt('settings-change-pw-too-short'), 'error');
                return;
            }
            if (!(/[a-zA-Z]/.test(newPw) && /\d/.test(newPw))) {
                showMsg(tt('settings-change-pw-too-weak'), 'error');
                return;
            }
            if (newPw !== cfm) {
                showMsg(tt('settings-change-pw-mismatch'), 'error');
                return;
            }

            // 提交
            btn.disabled = true;
            const oldText = btn.textContent;
            btn.textContent = tt('settings-change-pw-submitting');
            showMsg('', '');

            try {
                const tok = localStorage.getItem('mrpilot_token');
                const r = await fetch('/api/me/change_password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + tok,
                    },
                    body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
                });
                const data = await r.json().catch(() => ({}));
                if (r.ok && data.ok) {
                    showMsg(tt('settings-change-pw-success'), 'success');
                    if (typeof showToast === 'function') showToast(tt('settings-change-pw-success'), 'success');
                    oldEl.value = ''; newEl.value = ''; cfmEl.value = '';
                    if (bar) { bar.style.width = '0%'; bar.className = 'cpw-strength-bar'; }
                } else {
                    const detail = data.detail || '';
                    let msg = tt('settings-change-pw-success'); // 占位
                    if (detail === 'wrong_old_password') msg = tt('settings-change-pw-wrong-old');
                    else if (detail === 'password_too_short') msg = tt('settings-change-pw-too-short');
                    else if (detail === 'password_too_weak') msg = tt('settings-change-pw-too-weak');
                    else msg = detail || 'Error';
                    showMsg(msg, 'error');
                }
            } catch (e) {
                console.error('change_password', e);
                showMsg('Network error', 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = oldText;
            }
        });
    }

    // v109.4 · 「忘记当前密码?」弹窗
    function openForgotCurrentPwModal() {
        const u = window._userInfo || (typeof _userInfo !== 'undefined' ? _userInfo : null);
        const email = u && u.username ? u.username : '';
        const maskedEmail = maskEmail(email);

        // 创建 overlay
        let overlay = document.getElementById('cpw-forgot-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.id = 'cpw-forgot-overlay';
        overlay.className = 'cpw-forgot-overlay';
        overlay.innerHTML = `
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${esc(tt('cpw-forgot-title'))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${esc(tt('cpw-forgot-desc'))}</p>
                    <div class="cpw-forgot-email">${esc(maskedEmail)}</div>
                    <p class="cpw-forgot-tip">${esc(tt('cpw-forgot-tip'))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${esc(tt('cpw-forgot-cancel'))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${esc(tt('cpw-forgot-send'))}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // 关闭
        const close = () => overlay.remove();
        overlay.querySelector('#cpw-forgot-close').addEventListener('click', close);
        overlay.querySelector('#cpw-forgot-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

        // 发送
        overlay.querySelector('#cpw-forgot-send').addEventListener('click', async () => {
            const sendBtn = overlay.querySelector('#cpw-forgot-send');
            const msgEl = overlay.querySelector('#cpw-forgot-msg');
            sendBtn.disabled = true;
            const oldText = sendBtn.textContent;
            sendBtn.textContent = tt('cpw-forgot-sending');
            try {
                const r = await fetch('/api/auth/forgot_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email }),
                });
                const data = await r.json().catch(() => ({}));
                if (r.ok) {
                    msgEl.textContent = tt('cpw-forgot-success');
                    msgEl.className = 'cpw-forgot-msg success';
                    sendBtn.style.display = 'none';
                    overlay.querySelector('#cpw-forgot-cancel').textContent = tt('cpw-forgot-close-btn');
                } else {
                    msgEl.textContent = data.detail || tt('cpw-forgot-fail');
                    msgEl.className = 'cpw-forgot-msg error';
                    sendBtn.disabled = false;
                    sendBtn.textContent = oldText;
                }
            } catch (e) {
                msgEl.textContent = tt('cpw-forgot-fail');
                msgEl.className = 'cpw-forgot-msg error';
                sendBtn.disabled = false;
                sendBtn.textContent = oldText;
            }
        });
    }

    // 邮箱半遮罩 · ab****@gmail.com
    function maskEmail(email) {
        if (!email || !email.includes('@')) return email || '';
        const [local, domain] = email.split('@');
        if (local.length <= 2) return local + '****@' + domain;
        return local.slice(0, 2) + '****@' + domain;
    }

    // 安全转义
    function esc(s) {
        if (s == null) return '';
        return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        bindEvents();
    } else {
        document.addEventListener('DOMContentLoaded', bindEvents);
    }
})();



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
// v118.28.4.1 · LINE 用户补邮箱强制 modal
// LINE 一键登录的临时账号(line_xxx@line.local)首次进 /home 必须填真邮箱
// 填了:已存在 → 合并到老账号;不存在 → 更新临时账号 username/email
// ============================================================
(function() {
    'use strict';

    let _modalEl = null;
    let _shown = false;

    function _buildModal() {
        if (_modalEl) return _modalEl;
        const el = document.createElement('div');
        el.id = 'line-email-modal';
        el.style.cssText = 'position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;';
        el.innerHTML = `
            <div style="background:#fff;border-radius:16px;padding:28px 24px;max-width:420px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#06C755" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="4" width="20" height="16" rx="2"/>
                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                    </svg>
                    <h3 id="line-email-title-h" style="font-size:18px;font-weight:600;color:#0f172a;margin:0;"></h3>
                </div>
                <p id="line-email-sub-p" style="font-size:14px;color:#64748b;line-height:1.55;margin:0 0 18px;"></p>
                <input id="line-email-input" type="email" autocomplete="email" style="width:100%;padding:12px 14px;border:1px solid #e5e7eb;border-radius:10px;font-size:15px;outline:none;font-family:inherit;" />
                <div id="line-email-err" style="color:#dc2626;font-size:13px;margin-top:8px;min-height:18px;"></div>
                <button id="line-email-submit-btn" type="button" style="width:100%;margin-top:14px;padding:13px 16px;background:#111111;color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;"></button>
            </div>
        `;
        document.body.appendChild(el);
        _modalEl = el;

        const inp = el.querySelector('#line-email-input');
        const btn = el.querySelector('#line-email-submit-btn');
        const err = el.querySelector('#line-email-err');

        async function _submit() {
            err.textContent = '';
            const v = (inp.value || '').trim().toLowerCase();
            if (!v || v.indexOf('@') < 0 || v.split('@')[1].indexOf('.') < 0) {
                err.textContent = t('line-email-err-invalid');
                return;
            }
            btn.disabled = true;
            btn.style.opacity = '0.6';
            try {
                const resp = await fetch('/api/me/line_complete_email', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + (localStorage.getItem('mrpilot_token') || '')
                    },
                    body: JSON.stringify({ email: v })
                });
                if (!resp.ok) throw new Error('http_' + resp.status);
                const data = await resp.json();
                if (data.token) {
                    localStorage.setItem('mrpilot_token', data.token);
                }
                // 弹完 toast 后刷新页面 · 让 _userInfo 重拉
                if (typeof showToast === 'function') {
                    showToast(data.merged ? t('line-email-merged-toast') : t('line-email-saved-toast'), 'success');
                }
                setTimeout(function() { window.location.reload(); }, 600);
            } catch (e) {
                err.textContent = t('line-email-err-failed');
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        }
        btn.addEventListener('click', _submit);
        inp.addEventListener('keydown', function(e) { if (e.key === 'Enter') _submit(); });
        return el;
    }

    function _renderTexts() {
        if (!_modalEl) return;
        const titleEl = _modalEl.querySelector('#line-email-title-h');
        const subEl = _modalEl.querySelector('#line-email-sub-p');
        const inpEl = _modalEl.querySelector('#line-email-input');
        const btnEl = _modalEl.querySelector('#line-email-submit-btn');
        if (titleEl) titleEl.textContent = t('line-email-title');
        if (subEl) subEl.textContent = t('line-email-sub');
        if (inpEl) inpEl.placeholder = t('line-email-placeholder');
        if (btnEl) btnEl.textContent = t('line-email-submit');
    }

    function _show() {
        _buildModal();
        _renderTexts();
        _modalEl.style.display = 'flex';
        _shown = true;
        const inp = _modalEl.querySelector('#line-email-input');
        if (inp) setTimeout(function() { inp.focus(); }, 100);
    }

    async function _check() {
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        try {
            const resp = await fetch('/api/me/needs_email', {
                headers: { 'Authorization': 'Bearer ' + tk }
            });
            if (!resp.ok) return;
            const data = await resp.json();
            if (data && data.needs_email) _show();
        } catch (e) {}
    }

    // 等 i18n + DOM 就绪
    function _init() {
        // 延迟 800ms 让 _userInfo / I18N 都就绪
        setTimeout(_check, 800);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }

    // i18n 订阅 · 切语言时重渲 modal 文案(若正在显示)
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('line-email-modal', function() {
            if (_shown) _renderTexts();
        });
    }
})();



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











// ============================================================
// v118.32.5.5.13 · Session 心跳 · 实时踢被挤掉的设备
// 15 秒 ping + 切回 tab 立即 check · 利用现有 apiGet 401 处理
// ============================================================
(function () {
    'use strict';
    let _hbTimer = null;
    let _hbRunning = false;
    async function _sessionCheck() {
        if (_hbRunning) return;
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        _hbRunning = true;
        try {
            const r = await fetch('/api/me', {
                headers: { 'Authorization': 'Bearer ' + tk },
                cache: 'no-store',
            });
            if (r.status === 401) {
                const body = await r.json().catch(() => ({}));
                const detail = body && body.detail;
                let code = '';
                if (typeof detail === 'string') code = detail;
                else if (detail && typeof detail === 'object') code = detail.code || '';
                console.warn('[heartbeat] session revoked', code);
                localStorage.removeItem('mrpilot_token');
                if (_hbTimer) { clearInterval(_hbTimer); _hbTimer = null; }
                if (code === 'auth.session_revoked') {
                    try { _showSessionRevokedModal(); } catch (_) { window.location.href = '/'; }
                } else {
                    const _msgKey = (code === 'auth.password_changed_relogin') ? 'alert-password-changed-relogin' : 'alert-session';
                    try {
                        if (typeof showToast === 'function' && typeof t === 'function') {
                            showToast(t(_msgKey), 'error');
                        } else {
                            alert('Session expired');
                        }
                    } catch (_) {}
                    setTimeout(() => { window.location.href = '/'; }, 1500);
                }
            }
        } catch (e) {
            // 网络错忽略 · 下个 tick 再试
        } finally {
            _hbRunning = false;
        }
    }
    function _startHeartbeat() {
        if (_hbTimer) clearInterval(_hbTimer);
        _hbTimer = setInterval(_sessionCheck, 15000);  // 15 秒
    }
    // 启动
    if (localStorage.getItem('mrpilot_token')) {
        _startHeartbeat();
    }
    // 切回 tab 立即 check(关键 · 用户离开后回来第 1 秒就被踢)
    window.addEventListener('focus', _sessionCheck);
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) _sessionCheck();
    });
    // 暴露调试
    window._sessionCheck = _sessionCheck;
})();


