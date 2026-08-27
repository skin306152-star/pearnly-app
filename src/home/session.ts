// 入口级会话隔离 · 单一事实源(src/home/session.ts)
//
// 同一 Chrome 里 /cowork 与 /erp 要用不同账号同时在线、互不覆盖,像两个独立产品:
// 每个入口一个 token 槽,绝不共写一个 key。
//   · cowork → mrpilot_token_cowork
//   · erp   → mrpilot_token_erp
//   · legacy main/pos(以及 dms/ai/daily 等独立壳)→ mrpilot_token
//
// 入口判定(冷启动优先 pathname/canonical,免得被另一标签共享的 pearnly_entry 误导):
//   1. pathname(/cowork|/erp|/pos|/dms|/ai|/daily)最优先;
//   2. ?canonical=cowork|erp(preboot 归一 pathname 前/失败时的兜底);
//   3. pearnly_entry 只作为 veteran /home 内部页面的回归提示,绝不用于 cowork/erp 槽判定。
//
// 安全迁移:仅当 legacy token 的 JWT entry 精确匹配时才把 legacy 收养进槽
//   (cowork 可收养 main/cowork · erp 只收养 erp · pos/main/dms/ai/daily 一律不收养)。
//
// 写/清统一经这里,保持 window.token 与当前槽同步;401/logout 只清当前槽,不扫别的槽。
// import 即 boot(migrate + 同步 window.token),必须是最早 import,先于任何消费 window.token 的 sibling。

export type SessionEntry = 'cowork' | 'erp' | 'main' | 'pos' | 'dms' | 'ai' | 'daily' | '';

const LEGACY_TOKEN_KEY = 'mrpilot_token';
const COWORK_TOKEN_KEY = 'mrpilot_token_cowork';
const ERP_TOKEN_KEY = 'mrpilot_token_erp';

const LEGACY_WS_KEY = 'pearnly_active_workspace_client_id';

/** 解析 token 的 JWT payload 里的 entry(只认字符串,解失败返回 '')。 */
export function decodeJwtEntry(token: string): SessionEntry {
    const part = (token || '').split('.')[1];
    if (!part) return '';
    try {
        const payload = JSON.parse(atob(part.replace(/-/g, '+').replace(/_/g, '/')));
        const e = payload && payload.entry ? payload.entry : '';
        return typeof e === 'string' ? (e as SessionEntry) : '';
    } catch (_) {
        return '';
    }
}

function pathnameEntry(): SessionEntry {
    if (typeof location === 'undefined') return '';
    const p = location.pathname;
    if (p === '/cowork') return 'cowork';
    if (p === '/erp') return 'erp';
    if (p === '/pos') return 'pos';
    if (p === '/dms') return 'dms';
    if (p === '/ai') return 'ai';
    if (p === '/daily') return 'daily';
    return '';
}

function canonicalFromQuery(): 'cowork' | 'erp' | '' {
    if (typeof location === 'undefined') return '';
    try {
        const m = decodeURIComponent(location.search).match(/[?&]canonical=(cowork|erp)/);
        return m ? (m[1] as 'cowork' | 'erp') : '';
    } catch (_) {
        return '';
    }
}

/** 当前页会话入口。只认 pathname / canonical query,绝不认共享的 pearnly_entry:
 *  同一 Chrome 里另一标签(/cowork 或 /erp)先写了 pearnly_entry,不能让这个标签被误导去认错槽。
 *  冷启动 pathname(/cowork|/erp)最优先;?canonical=cowork|erp 兜底(preboot 归一 pathname 前的 /home 内部页)。
 */
export function entry(): SessionEntry {
    const p = pathnameEntry();
    if (p) return p;
    return canonicalFromQuery();
}

/** 当前入口的 token 槽 key。cowork/erp 各自独立,其余(含 legacy main/pos)共用 legacy。 */
export function tokenKey(): string {
    const e = entry();
    if (e === 'cowork') return COWORK_TOKEN_KEY;
    if (e === 'erp') return ERP_TOKEN_KEY;
    return LEGACY_TOKEN_KEY;
}

/** 当前入口的 active workspace key。cowork/erp 分槽,避免标签页互改 X-Workspace-Client-Id。 */
export function workspaceKey(): string {
    const e = entry();
    if (e === 'cowork') return LEGACY_WS_KEY + '_cowork';
    if (e === 'erp') return LEGACY_WS_KEY + '_erp';
    return LEGACY_WS_KEY;
}

/** 迁移收养:仅当 legacy token 的 JWT entry 精确匹配才把 legacy 复制进当前槽(cowork 接 main/cowork,erp 只接 erp)。 */
export function migrateLegacyToken(): boolean {
    const e = entry();
    if (e !== 'cowork' && e !== 'erp') return false;
    try {
        const key = tokenKey();
        if (localStorage.getItem(key)) return false; // 槽已有自己的 token,不覆盖
        const legacy = localStorage.getItem(LEGACY_TOKEN_KEY);
        if (!legacy) return false;
        const jwtEntry = decodeJwtEntry(legacy);
        const accepted =
            e === 'cowork' ? jwtEntry === 'cowork' || jwtEntry === 'main' : jwtEntry === 'erp';
        if (!accepted) return false;
        localStorage.setItem(key, legacy);
        return true;
    } catch (_) {
        return false;
    }
}

/** 当前槽 token(空串表示未登录)。 */
export function getToken(): string {
    try {
        return localStorage.getItem(tokenKey()) || '';
    } catch (_) {
        return '';
    }
}

export function hasToken(): boolean {
    return !!getToken();
}

/** 写入当前槽并同步 window.token。 */
export function setToken(value: string): void {
    try {
        localStorage.setItem(tokenKey(), value);
    } catch (_) {
        /* silent */
    }
    window.token = value;
}

/** 只清当前槽并同步 window.token,绝不扫别的槽(cowork/erp 互不清)。 */
export function clearToken(): void {
    try {
        localStorage.removeItem(tokenKey());
    } catch (_) {
        /* silent */
    }
    window.token = '';
}

/** 当前入口的 active workspace client id(cowork/erp 分槽)。 */
export function getWorkspaceClientId(): number | null {
    try {
        const v = localStorage.getItem(workspaceKey());
        if (!v || v === 'null' || v === '0' || v === '') return null;
        const n = parseInt(v, 10);
        return isNaN(n) ? null : n;
    } catch (_) {
        return null;
    }
}

/** 写当前入口的 active workspace client id(cowork/erp 分槽)。 */
export function setWorkspaceClientId(id: number | null): void {
    const k = workspaceKey();
    try {
        if (id == null || id === 0) localStorage.removeItem(k);
        else localStorage.setItem(k, String(id));
    } catch (_) {
        /* silent · 私模/配额 */
    }
}

// boot:迁移 + 同步 window.token + 挂 window.session。import 即跑,必须最早 import。
migrateLegacyToken();
window.token = getToken();
window.session = {
    entry,
    tokenKey,
    workspaceKey,
    decodeJwtEntry,
    migrateLegacyToken,
    getToken,
    hasToken,
    setToken,
    clearToken,
    getWorkspaceClientId,
    setWorkspaceClientId,
};
