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
    if (route === 'settings') renderSettings();
    if (route === 'history') loadHistoryPage();
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
    // REFACTOR-C1 · 老套餐 v109.3 IIFE 已删(计费迁移收尾 step2)· renderTrialBanner 不复存在 ·
    //   原 window.renderTrialBanner 兜底赋值随之移除(否则引用已删函数会 ReferenceError)。
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

    // v118.33.2 NAV-IA Phase 2 · sidebar 底部「成本追踪 / 用户管理 / 测试 / adm-lang-bar」整体已删 · 显隐逻辑搬到头像菜单 applyRoleVisibility
    // REFACTOR-C1 · 顶栏超管下拉(#admin-dropdown)+ 老 home.html admin 布局已下线 · 超管走独立 /admin SPA

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
        try { return JSON.stringify(detail).slice(0, 160); } catch (_) { /* silent: detail 含循环引用时 stringify 抛错 · 下方 fallback/String(detail) 兜底 */ }
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













