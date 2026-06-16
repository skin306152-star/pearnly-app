// Phase 3 · LIFF 复核屏入口。后端 /liff/purchase/{doc} → 302 /home?liff=purchase&doc=。
// 让 Phase 1 的 purchase-form 复核屏在 LINE webview(LIFF)里跑:签 id_token → 换 Pearnly token →
// 回 /home 打开该单复核屏。不重做 Flex;App 内不放 LINE 按钮(用户自行去 LINE)。
// 真验需真 LINE channel + LIFF ID(留用户配 window.__PEARNLY_LIFF_ID__ · 此环境验不了真 LIFF)。
/* global t, escapeHtml */

const LIFF_DOC_KEY = 'pearnly_liff_doc';
const LIFF_INBOX_KEY = 'pearnly_liff_inbox';
const LIFF_VIEW_KEY = 'pearnly_liff_view';
const LIFF_WS_KEY = 'pearnly_liff_ws';
const LIFF_SDK_SRC = 'https://static.line-scdn.net/liff/edge/2/sdk.js';

interface LiffSdk {
    init(cfg: { liffId: string }): Promise<void>;
    isLoggedIn(): boolean;
    login(): void;
    getIDToken(): string | null;
}

function qp(name: string): string | null {
    return new URLSearchParams(location.search).get(name);
}

function mask(msg: string): void {
    // 套账门 preboot 把 #workspace-gate-root 以外的元素 visibility:hidden → 会藏掉本 mask。
    // LIFF 入口不需要选套账(直达指定单)· 摘掉 preboot 让 mask 可见 · z-index 盖过门(900)。
    document.body.classList.remove('workspace-gate-preboot');
    let el = document.getElementById('liff-mask');
    if (!el) {
        el = document.createElement('div');
        el.id = 'liff-mask';
        el.style.cssText =
            'position:fixed;inset:0;z-index:4000;background:var(--bg);' +
            'display:flex;align-items:center;justify-content:center;text-align:center;' +
            'padding:24px;color:var(--ink2);font-size:14px;line-height:1.6;';
        document.body.appendChild(el);
    }
    el.innerHTML = escapeHtml(msg);
}

// i18n 早期可能未就绪(本模块在引导链前 eval)→ t 缺失时用兜底文案,不致空白。
function tx(key: string, fallback: string): string {
    try {
        const s = typeof t === 'function' ? t(key) : '';
        return s && s !== key ? s : fallback;
    } catch (_) {
        return fallback;
    }
}

function loadLiffSdk(): Promise<LiffSdk | null> {
    return new Promise((resolve) => {
        const existing = (window as unknown as { liff?: LiffSdk }).liff;
        if (existing) return resolve(existing);
        const s = document.createElement('script');
        s.src = LIFF_SDK_SRC;
        s.onload = () => resolve((window as unknown as { liff?: LiffSdk }).liff || null);
        s.onerror = () => resolve(null);
        document.head.appendChild(s);
    });
}

function liffErrKey(body: unknown): string {
    const detail = (body as { error?: { detail?: string } })?.error?.detail || '';
    if (detail === 'line_not_bound') return 'liff-not-bound';
    if (detail === 'liff_verify_failed') return 'liff-verify-failed';
    return 'liff-open-in-line';
}

async function fetchLiffId(): Promise<string> {
    // LIFF ID 服务端配置(env LINE_LIFF_ID)· 公开端点;取不到返空 → 提示在 LINE 打开。
    try {
        const r = await fetch('/api/line/liff/config');
        const b = await r.json();
        return (b && b.data && b.data.liff_id) || '';
    } catch (_) {
        return '';
    }
}

async function liffEntry(
    doc: string | null,
    inbox: string | null,
    view: string | null,
    ws: string | null
): Promise<void> {
    mask(tx('liff-signing-in', '正在登录 LINE…'));
    const liffId =
        (window as unknown as { __PEARNLY_LIFF_ID__?: string }).__PEARNLY_LIFF_ID__ ||
        (await fetchLiffId());
    const liff = await loadLiffSdk();
    if (!liff || !liffId) {
        mask(tx('liff-open-in-line', '请在 LINE 中打开此页面'));
        return;
    }
    try {
        await liff.init({ liffId });
        if (!liff.isLoggedIn()) {
            liff.login();
            return;
        }
        const idToken = liff.getIDToken() || '';
        const r = await fetch('/api/line/liff/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: idToken }),
        });
        const body = await r.json().catch(() => null);
        if (!body || !body.ok || !body.data || !body.data.token) {
            mask(tx(liffErrKey(body), '登录失败,请重试'));
            return;
        }
        localStorage.setItem('mrpilot_token', body.data.token);
        if (doc) sessionStorage.setItem(LIFF_DOC_KEY, doc);
        if (inbox) sessionStorage.setItem(LIFF_INBOX_KEY, inbox);
        if (view) sessionStorage.setItem(LIFF_VIEW_KEY, view);
        if (ws) sessionStorage.setItem(LIFF_WS_KEY, ws);
        // 带 token 重进 /home(去掉 liff 参数)· 正常引导起来后 liffResume 打开复核屏/待归类。
        location.replace('/home');
    } catch (_) {
        mask(tx('liff-open-in-line', '请在 LINE 中打开此页面'));
    }
}

// 回到带 token 的 /home 后:深链落点 —— doc 开复核屏对应单,inbox 开待归类页(等路由就绪)。
function liffResume(): void {
    const doc = sessionStorage.getItem(LIFF_DOC_KEY);
    const inbox = sessionStorage.getItem(LIFF_INBOX_KEY);
    const view = sessionStorage.getItem(LIFF_VIEW_KEY);
    const ws = sessionStorage.getItem(LIFF_WS_KEY);
    if (!doc && !inbox) return;
    sessionStorage.removeItem(LIFF_DOC_KEY);
    sessionStorage.removeItem(LIFF_INBOX_KEY);
    sessionStorage.removeItem(LIFF_VIEW_KEY);
    sessionStorage.removeItem(LIFF_WS_KEY);
    // 该单只在自己的套账可见 → 自动切到它、放行套账门(否则硬门挡在编辑页前/按错套账存)。
    if (ws && typeof window.satisfyWorkspaceGate === 'function')
        window.satisfyWorkspaceGate(Number(ws));
    let tries = 0;
    const open = () => {
        if (inbox) {
            if (typeof window.routeTo === 'function') window.routeTo('purchase-inbox');
            else if (tries++ < 40) setTimeout(open, 120);
            return;
        }
        // view=receipt(PO-7)→ 只读详情页(看/出替代收据);否则编辑复核屏。
        if (view === 'receipt') {
            if (typeof window.openPurchaseDetail === 'function') window.openPurchaseDetail(doc!);
            else if (tries++ < 40) setTimeout(open, 120);
            return;
        }
        if (typeof window.openPurchaseForm === 'function') window.openPurchaseForm(doc);
        else if (tries++ < 40) setTimeout(open, 120);
    };
    open();
}

if (qp('liff') === 'purchase') liffEntry(qp('doc'), qp('inbox'), qp('view'), qp('ws'));
else liffResume();
