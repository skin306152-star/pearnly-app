// REFACTOR-C1-home-batch9f · 真核心叶子层 cutover(从 home.js verbatim 抽出 · 0 逻辑改)
// 工具(t/escapeHtml/svgIcon)+ Session 被踢弹窗(🔴)+ 鉴权 API(🔴铁律#26)+ plan 上限 helper。
// main.js 第 1 个 import:保证 sibling 模块 eval 期 window.t/apiGet/_showSessionRevokedModal 等已就绪。
// 共享状态(currentLang/_userInfo/token/I18N)仍是 home.js 顶层 let/const · 经全局词法环境裸名解析。
/* global I18N, token, currentLang */

// 首屏并发去重(2026-06-11):启动期多个模块各自 fetch 同一只读 GET(erp/endpoints ×3、
//   exceptions/stats ×2)在缓存填好前同时打到后端 · 跨区 DB 每条往返 ~69ms · 纯浪费。在
//   fetch 边界合并"同一时刻在飞的相同 GET":后到者复用在飞 Promise 的克隆响应 · 请求落地即
//   从表移除 → 只去并发重复 · 不做持久缓存 · 对调用方语义零变化。仅作用于 home 页 bundle。
(function coalesceConcurrentGets() {
    const native = window.fetch.bind(window);
    if ((native as { __coalesced?: boolean }).__coalesced) return;
    const inflight = new Map<string, Promise<Response>>();
    const wrapped = function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
        const req = input instanceof Request ? input : null;
        const method = (init?.method || req?.method || 'GET').toUpperCase();
        const url =
            typeof input === 'string'
                ? input
                : input instanceof URL
                  ? input.href
                  : (req as Request).url;
        // 仅合并无副作用 GET · 同源 /api · 无 AbortSignal(防一方 abort 误伤共享方)
        if (method !== 'GET' || init?.signal || req?.signal || url.indexOf('/api/') < 0) {
            return native(input as RequestInfo, init);
        }
        const headers = new Headers((init?.headers || req?.headers) ?? undefined);
        const key =
            url +
            '|' +
            (headers.get('Authorization') || '') +
            '|' +
            (headers.get('X-Workspace-Client-Id') || '');
        const pending = inflight.get(key);
        if (pending) return pending.then((r) => r.clone());
        const p = native(input as RequestInfo, init);
        const done = () => inflight.delete(key);
        p.then(done, done);
        inflight.set(key, p);
        return p.then((r) => r.clone());
    } as typeof window.fetch;
    (wrapped as { __coalesced?: boolean }).__coalesced = true;
    window.fetch = wrapped;
})();

// 单次批量上限:v118.27.8.1.15 后 trial 30 / monthly 500 / yearly 800 / lifetime 1000
function getMaxFiles() {
    // v111.2 · 优先用后端 /api/me/plan 返回的 limits.max_upload_files
    try {
        const ps = window._planState;
        if (ps && ps.limits && (ps.limits as any).max_upload_files) {
            return (ps.limits as any).max_upload_files;
        }
        // 后端 plan 字符串兜底(/api/me/plan 还没回 · 用 _userInfo.plan)
        const plan = (_userInfo && _userInfo.plan) || 'trial';
        // super_admin 直接放最高
        if (_userInfo && _userInfo.is_super_admin) return 9999;
        // v118.27.8.1.15 · 全档上调对齐后端 PLAN_CONFIG
        const mapping = {
            admin: 9999,
            lifetime: 1000,
            yearly: 800,
            monthly: 500,
            trial: 30,
            // 老 plan 名兼容(不会再用·但保险)
            enterprise: 1000,
            firm: 800,
            pro: 500,
            plus: 30,
            free: 30,
        };
        return mapping[plan as keyof typeof mapping] || 30;
    } catch (_) {
        return 30;
    }
}

function getMaxPagesPerFile() {
    try {
        const ps = window._planState;
        if (ps && ps.limits && (ps.limits as any).max_pages_per_file)
            return (ps.limits as any).max_pages_per_file;
        if (_userInfo && _userInfo.is_super_admin) return 999;
        const plan = (_userInfo && _userInfo.plan) || 'trial';
        return plan === 'lifetime' || plan === 'enterprise' ? 100 : 50;
    } catch (_) {
        return 50;
    }
}

function getMaxMbPerFile() {
    try {
        const ps = window._planState;
        if (ps && ps.limits && (ps.limits as any).max_mb_per_file)
            return (ps.limits as any).max_mb_per_file;
        if (_userInfo && _userInfo.is_super_admin) return 500;
        const plan = (_userInfo && _userInfo.plan) || 'trial';
        if (plan === 'lifetime' || plan === 'enterprise') return 200;
        return 100;
    } catch (_) {
        return 100;
    }
}

// ============================================================
// 工具
// ============================================================
function t(key: string, params?: Record<string, string>) {
    let s = (I18N[currentLang] && I18N[currentLang][key]) || key;
    if (params) for (const k in params) s = s.replace('{' + k + '}', params[k]);
    return s;
}
function escapeHtml(s: unknown) {
    return String(s ?? '').replace(
        /[&<>"']/g,
        (ch: string) =>
            ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;',
            })[ch] as string
    );
}

// v93 · SVG 线性图标 helper · lucide 风格 · 替代 emoji 保持专业感
function svgIcon(name: string, size?: number) {
    size = size || 14;
    const paths = {
        refresh:
            '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',
        cache: '<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
        wifiOff:
            '<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',
        wifiOn: '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
        check: '<path d="M20 6 9 17l-5-5"/>',
        alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
        mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
        folder: '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
        api: '<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',
        copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
        minus: '<line x1="5" y1="12" x2="19" y2="12"/>',
        sparkle:
            '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>',
    };
    const inner = paths[name as keyof typeof paths] || '';
    return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${inner}</svg>`;
}

// ============================================================
// Session 被踢弹窗 (v118.32.5.5.34 · 替换原 toast+redirect)
// ============================================================
function _showSessionRevokedModal() {
    if (document.getElementById('pn-session-revoked-modal')) return;
    var l =
        (typeof currentLang === 'string' && currentLang) ||
        localStorage.getItem('mrpilot_lang') ||
        'th';
    var titles = {
        zh: '账号已在其他设备登录',
        en: 'Signed in on another device',
        th: 'บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น',
        ja: '他のデバイスでサインインされました',
    };
    var bodies = {
        zh: '你的账号刚刚在另一台设备上登录\n当前设备已自动退出，请重新登录继续使用。',
        en: 'Your account was just signed in on another device.\nThis device has been logged out automatically.',
        th: 'บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น\nระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่',
        ja: 'お使いのアカウントが別のデバイスでサインインされました。\nこのデバイスは自動的にログアウトされました。',
    };
    var okLabels = {
        zh: '确定，去登录',
        en: 'OK, Sign in',
        th: 'ตกลง เข้าสู่ระบบ',
        ja: 'OK、ログイン',
    };
    var lang = titles[l as keyof typeof titles] ? l : 'th';
    var overlay = document.createElement('div');
    overlay.id = 'pn-session-revoked-modal';
    overlay.style.cssText =
        'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;';
    overlay.innerHTML =
        '<div style="background:var(--card);border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;">' +
        '<div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;">' +
        '<svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg>' +
        '</div>' +
        '<div style="font-size:16px;font-weight:700;color:var(--ink);margin-bottom:10px;line-height:1.4;">' +
        titles[lang as keyof typeof titles] +
        '</div>' +
        '<div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">' +
        bodies[lang as keyof typeof bodies] +
        '</div>' +
        '<button id="pn-srm-ok" style="width:100%;padding:11px 0;background:var(--btn-blue);color:var(--accent-ink);border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">' +
        okLabels[lang as keyof typeof okLabels] +
        '</button>' +
        '</div>';
    document.body.appendChild(overlay);
    document.getElementById('pn-srm-ok')!.addEventListener('click', function () {
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
    } catch (_) {
        /* 切换器未就绪 · 静默 */
    }
    return {};
}
async function apiGet(url: string) {
    const resp = await fetch(url, {
        headers: { Authorization: 'Bearer ' + token, ..._wsHeader() } as HeadersInit,
    });
    if (resp.status === 401 || resp.status === 403) {
        // v118.11 · 修 BUG B 员工登录跳着陆页:兼容 string/object detail
        // 原代码只看 detail.code · 但后端经常用 detail="auth.xxx" 字符串 · 导致任何 401/403 都跳
        // 新规则:401 一定跳 · 403 必须 detail 包含 "auth." 才跳 · 否则当业务错误抛出
        const data = await resp.json().catch(() => ({}));
        const detail = data && data.detail;
        let code = '';
        if (typeof detail === 'string') code = detail;
        else if (detail && typeof detail === 'object') code = detail.code || '';
        const isAuthFail =
            resp.status === 401 || (typeof code === 'string' && code.indexOf('auth.') >= 0);
        if (isAuthFail) {
            console.warn('[auth-fail-redirect]', url, resp.status, detail); // 诊断 · 用户截屏给我看
            localStorage.removeItem('mrpilot_token');
            if (code === 'auth.session_revoked') {
                _showSessionRevokedModal();
            } else {
                const _msgKey =
                    code === 'auth.password_changed_relogin'
                        ? 'alert-password-changed-relogin'
                        : 'alert-session';
                showToast(t(_msgKey), 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            }
            return null;
        }
        // 业务类 403(如 quota.need_api_key)交由调用方处理
        const err = new Error('biz_403') as Error & { detail?: unknown };
        err.detail = detail;
        throw err;
    }
    if (!resp.ok) throw new Error('fetch failed');
    return await resp.json();
}
async function apiPost(url: string, data: unknown) {
    const resp = await fetch(url, {
        method: 'POST',
        headers: {
            Authorization: 'Bearer ' + token,
            'Content-Type': 'application/json',
            ..._wsHeader(),
        } as HeadersInit,
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
        const isAuthFail =
            resp.status === 401 || (typeof code === 'string' && code.indexOf('auth.') >= 0);
        if (isAuthFail) {
            console.warn('[auth-fail-redirect]', url, resp.status, detail);
            localStorage.removeItem('mrpilot_token');
            if (code === 'auth.session_revoked') {
                _showSessionRevokedModal();
            } else {
                const _msgKey =
                    code === 'auth.password_changed_relogin'
                        ? 'alert-password-changed-relogin'
                        : 'alert-session';
                showToast(t(_msgKey), 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            }
            return null;
        }
        // 业务类 403 · 返回原 resp 让调用方处理
        return resp;
    }
    return resp;
}

// v118.10 · PUT helper(/api/me/profile 等)· 返回 {ok: true/false, ...} 而不是 Response
async function apiPut(url: string, data: unknown) {
    try {
        const resp = await fetch(url, {
            method: 'PUT',
            headers: {
                Authorization: 'Bearer ' + token,
                'Content-Type': 'application/json',
                ..._wsHeader(),
            } as HeadersInit,
            body: JSON.stringify(data),
        });
        if (resp.status === 401 || resp.status === 403) {
            // v118.11 · 同 apiGet · 兼容 string/object detail
            const body = await resp.json().catch(() => ({}));
            const detail = body && body.detail;
            let code = '';
            if (typeof detail === 'string') code = detail;
            else if (detail && typeof detail === 'object') code = detail.code || '';
            const isAuthFail =
                resp.status === 401 || (typeof code === 'string' && code.indexOf('auth.') >= 0);
            if (isAuthFail) {
                console.warn('[auth-fail-redirect]', url, resp.status, detail);
                localStorage.removeItem('mrpilot_token');
                if (code === 'auth.session_revoked') {
                    _showSessionRevokedModal();
                } else {
                    const _msgKey =
                        code === 'auth.password_changed_relogin'
                            ? 'alert-password-changed-relogin'
                            : 'alert-session';
                    showToast(t(_msgKey), 'error');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1500);
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

// REFACTOR-C1-home-batch9f · window 挂出(~70 模块 eval 期裸读依赖 · apiGet/apiPost 已在上方 D 块挂出)
window.t = t;
window.escapeHtml = escapeHtml;
window.svgIcon = svgIcon;
window._showSessionRevokedModal = _showSessionRevokedModal;
window._wsHeader = _wsHeader;
window.apiPut = apiPut;
window.getMaxFiles = getMaxFiles;
window.getMaxPagesPerFile = getMaxPagesPerFile;
window.getMaxMbPerFile = getMaxMbPerFile;
