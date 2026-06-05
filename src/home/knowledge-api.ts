// ============================================================
// 客户知识库 · 统一 API 封装(KNOWLEDGE feature · flag-gated)
//
// 所有知识库前端模块(文档库 / 问答 / 来源 / 悬浮件)共用这一份 fetch:
// Bearer token、JSON 归一、错误归一,并自动附带当前账套主体(workspace_client_id)。
// 后端在 KNOWLEDGE_ENABLED=1 时才挂路由 → kbProbe() 探一次决定是否暴露入口。
// 账套上下文复用既有 window.getActiveWorkspaceClientId / _workspaceClientsCache,不另起一套。
// ============================================================
/* global escapeHtml */

const KB_BASE = '/api/knowledge';

// 品牌猫素材 · 带版本号破 Cloudflare 缓存(换猫时 bump);全知识库模块共用,保猫一致。
export const KB_CAT = '/static/brand/kb-cat.png?v=2';

function kbToken(): string {
    return localStorage.getItem('mrpilot_token') || '';
}

/** i18n 取词:命中 window.t 用译文,否则回退默认文案。知识库各模块共用。 */
export function kbT(key: string, fallback: string): string {
    if (typeof window.t === 'function') {
        const s = window.t(key);
        if (s && s !== key) return s;
    }
    return fallback;
}

/** HTML 转义(含单引号 &#39;,可安全用于单引号属性)。window.escapeHtml 缺失时直出。 */
export function kbEsc(s: unknown): string {
    return typeof escapeHtml === 'function' ? escapeHtml(String(s ?? '')) : String(s ?? '');
}

// 线性图标(lucide 风格 · currentColor 描边)。知识库统一用线性 SVG,不用 emoji 当图标。
const KB_ICON_PATHS: Record<string, string> = {
    file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>',
    'file-text':
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
    sheet: '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/>',
    image: '<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21"/>',
    upload: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="m9 15 3-3 3 3"/>',
    message: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    'shield-check':
        '<path d="M20 13c0 5-3.5 7.5-7.7 9a1 1 0 0 1-.7 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    x: '<path d="M18 6 6 18"/><path d="M6 6l12 12"/>',
};

/** 线性 SVG 图标字符串。未知名回退 file。stroke 走 currentColor,尺寸由容器 CSS 定。 */
export function kbIcon(name: keyof typeof KB_ICON_PATHS | string): string {
    const path = KB_ICON_PATHS[name] || KB_ICON_PATHS.file;
    return `<svg class="kb-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${path}</svg>`;
}

export interface KbModal {
    modal: HTMLElement;
    open(): void;
    close(): void;
}

/**
 * 知识库标准弹窗外壳:遮罩 + 居中卡,点遮罩 / `[data-kb-${prefix}-close]` / Esc 关闭。
 * 尺寸、层级等样式由各模块自行注入 `#kb-${prefix}-style`;本工厂只管 DOM 与开合行为。
 * 幂等:重复调用复用已建节点。
 */
export function kbModalShell(prefix: string): KbModal {
    const maskId = `kb-${prefix}-mask`;
    const modalId = `kb-${prefix}-modal`;
    const open = (): void => document.getElementById(maskId)?.classList.add('open');
    const close = (): void => document.getElementById(maskId)?.classList.remove('open');

    let mask = document.getElementById(maskId);
    if (!mask) {
        mask = document.createElement('div');
        mask.id = maskId;
        mask.className = `kb-${prefix}-mask`;
        mask.innerHTML = `<div class="kb-${prefix}-modal" id="${modalId}" role="dialog" aria-modal="true"></div>`;
        document.body.appendChild(mask);
        const m = mask;
        m.addEventListener('click', (e) => {
            if (e.target === m || (e.target as HTMLElement).closest(`[data-kb-${prefix}-close]`))
                close();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && m.classList.contains('open')) close();
        });
    }
    return { modal: document.getElementById(modalId) as HTMLElement, open, close };
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
