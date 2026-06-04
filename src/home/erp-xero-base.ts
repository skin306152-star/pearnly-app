// ============================================================
// REFACTOR-WB-modularize · Xero 共享核心(状态 store + 助手 + 状态拉取)从 erp-xero.js 拆出
//
// S(status/statusLoaded/bound·中心化)+ _esc/_toast/_isOwner/_getCurrentHistory/
// _isHistoryExceptional/_loadStatus。erp-xero(卡片+action)与 erp-xero-push 均 import。
// ============================================================
/* global escapeHtml, _results, _drawerIdx */

interface XeroBaseState {
    status: Record<string, unknown> | null;
    statusLoaded: boolean;
    bound: boolean;
}
export const S: XeroBaseState = {
    status: null,
    statusLoaded: false,
    bound: false,
};
function _esc(s: unknown) {
    return typeof escapeHtml === 'function'
        ? escapeHtml(s == null ? '' : String(s))
        : String(s == null ? '' : s);
}
function _toast(msg: string, kind?: string) {
    try {
        if (typeof showToast === 'function') showToast(msg, kind || 'info');
    } catch (e) {}
}

function _isOwner() {
    const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
    return !!(u && (u.role === 'owner' || u.is_super_admin));
}

function _getCurrentHistory() {
    try {
        const r = (typeof _results !== 'undefined' ? _results : [])[
            typeof _drawerIdx !== 'undefined' ? _drawerIdx : -1
        ];
        return r || null;
    } catch (e) {
        return null;
    }
}

function _isHistoryExceptional(h: Record<string, unknown> | null) {
    if (!h) return false;
    const st = String(h.status || '').toLowerCase();
    return st === 'exception' || st === 'exception_pending' || st === 'rejected';
}

async function _loadStatus(force?: boolean) {
    if (S.statusLoaded && !force) return S.status;
    const tk = localStorage.getItem('mrpilot_token');
    if (!tk) return null;
    try {
        const r = await fetch('/api/erp/xero/status', {
            headers: { Authorization: 'Bearer ' + tk },
        });
        if (!r.ok) throw new Error('http_' + r.status);
        S.status = await r.json();
        S.statusLoaded = true;
    } catch (e) {
        S.status = { configured: false, connected: false, organisations: [] };
        S.statusLoaded = false;
    }
    return S.status;
}

export { _esc, _toast, _isOwner, _getCurrentHistory, _isHistoryExceptional, _loadStatus };
