// ============================================================
// 客户知识库 · 统一 API 封装(KNOWLEDGE feature · flag-gated)
//
// 所有知识库前端模块(文档库 / 问答 / 来源 / 悬浮件)共用这一份 fetch:
// Bearer token、JSON 归一、错误归一,并自动附带当前账套主体(workspace_client_id)。
// 后端在 KNOWLEDGE_ENABLED=1 时才挂路由 → kbProbe() 探一次决定是否暴露入口。
// 账套上下文复用既有 window.getActiveWorkspaceClientId / _workspaceClientsCache,不另起一套。
// ============================================================

const KB_BASE = '/api/knowledge';

// 品牌猫素材 · 带版本号破 Cloudflare 缓存(换猫时 bump);全知识库模块共用,保猫一致。
export const KB_CAT = '/static/brand/kb-cat.png?v=2';

function kbToken(): string {
    return localStorage.getItem('mrpilot_token') || '';
}

/** 当前账套主体 id;未选返回 null(此时禁止客户私有操作)。 */
export function kbWorkspaceId(): number | null {
    const fn = window.getActiveWorkspaceClientId;
    if (typeof fn !== 'function') return null;
    const v = fn();
    const n = Number(v);
    return Number.isFinite(n) && n > 0 ? n : null;
}

/** 当前账套主体显示名,从既有缓存按 id 反查;查不到给占位。 */
export function kbWorkspaceName(): string {
    const id = kbWorkspaceId();
    if (!id) return '';
    const cache = (window._workspaceClientsCache || []) as Array<{ id?: unknown; name?: unknown }>;
    const hit = cache.find((c) => Number(c.id) === id);
    return hit && hit.name ? String(hit.name) : '#' + id;
}

export interface KbResult<T> {
    ok: boolean;
    status: number;
    data: T | null;
    /** 后端归一错误码(detail.error_code / message_key),供前端映射人话。 */
    error?: string;
}

interface KbOpts {
    /** 自动把当前账套主体并入 query(GET)或 body(POST/PATCH)。默认 true。 */
    withWorkspace?: boolean;
    /** 覆盖默认 JSON body(上传文档走 FormData 时传 raw)。 */
    raw?: BodyInit;
    query?: Record<string, string | number | boolean | null | undefined>;
}

/** 知识库 JSON 请求。失败不抛,统一返回 KbResult,让调用方走四态 UI。 */
export async function kbRequest<T = unknown>(
    method: string,
    path: string,
    body?: Record<string, unknown>,
    opts: KbOpts = {}
): Promise<KbResult<T>> {
    const url = new URL(KB_BASE + path, location.origin);
    const wsId = kbWorkspaceId();
    if (opts.query) {
        for (const [k, v] of Object.entries(opts.query)) {
            if (v !== null && v !== undefined) url.searchParams.set(k, String(v));
        }
    }
    const sendWs = opts.withWorkspace !== false && wsId != null;
    if (sendWs && (method === 'GET' || method === 'DELETE')) {
        url.searchParams.set('workspace_client_id', String(wsId));
    }

    const headers: Record<string, string> = { Authorization: 'Bearer ' + kbToken() };
    let payload: BodyInit | undefined = opts.raw;
    if (!opts.raw && body !== undefined) {
        const merged = sendWs ? { workspace_client_id: wsId, ...body } : body;
        headers['Content-Type'] = 'application/json';
        payload = JSON.stringify(merged);
    }

    try {
        const resp = await fetch(url.toString(), { method, headers, body: payload });
        let data: T | null = null;
        let error: string | undefined;
        const text = await resp.text();
        if (text) {
            try {
                const parsed = JSON.parse(text);
                if (resp.ok) {
                    data = parsed as T;
                } else {
                    error =
                        parsed?.detail?.error_code ||
                        parsed?.message_key ||
                        parsed?.detail ||
                        undefined;
                }
            } catch {
                /* 非 JSON 响应(多半是 5xx HTML)· 当通用错误处理 */
            }
        }
        return { ok: resp.ok, status: resp.status, data, error };
    } catch {
        return { ok: false, status: 0, data: null, error: 'network' };
    }
}

/** 文档上传走 multipart。 */
export async function kbUpload<T = unknown>(file: File, baseId?: number): Promise<KbResult<T>> {
    const fd = new FormData();
    fd.append('file', file);
    const wsId = kbWorkspaceId();
    if (wsId != null) fd.append('workspace_client_id', String(wsId));
    if (baseId != null) fd.append('knowledge_base_id', String(baseId));
    return kbRequest<T>('POST', '/documents', undefined, { raw: fd, withWorkspace: false });
}

let _probed: boolean | null = null;

/** 探一次后端是否开启知识库(flag)。结果缓存,全程只付一次探针。 */
export async function kbProbe(): Promise<boolean> {
    if (_probed !== null) return _probed;
    const r = await kbRequest('GET', '/bases', undefined, { withWorkspace: false });
    // 200 = flag 开;404/网络 = 关。401/403 也算"开但需鉴权",仍暴露入口。
    _probed = r.status === 200 || r.status === 401 || r.status === 403;
    return _probed;
}
