// Phase 3 · LIFF 复核屏入口。后端 /liff/purchase/{doc} → 302 /home?liff=purchase&doc=。
// 让 Phase 1 的 purchase-form 复核屏在 LINE webview(LIFF)里跑:签 id_token → 换 Pearnly token →
// 回 /home 打开该单复核屏。不重做 Flex;App 内不放 LINE 按钮(用户自行去 LINE)。
// 真验需真 LINE channel + LIFF ID(留用户配 window.__PEARNLY_LIFF_ID__ · 此环境验不了真 LIFF)。
/* global t, escapeHtml */

const LIFF_DOC_KEY = 'pearnly_liff_doc';
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

async function liffEntry(doc: string | null): Promise<void> {
    mask(t('liff-signing-in'));
    const liffId = (window as unknown as { __PEARNLY_LIFF_ID__?: string }).__PEARNLY_LIFF_ID__;
    const liff = await loadLiffSdk();
    if (!liff || !liffId) {
        mask(t('liff-open-in-line'));
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
            mask(t(liffErrKey(body)));
            return;
        }
        localStorage.setItem('mrpilot_token', body.data.token);
        if (doc) sessionStorage.setItem(LIFF_DOC_KEY, doc);
        // 带 token 重进 /home(去掉 liff 参数)· 正常引导起来后 liffResume 打开复核屏。
        location.replace('/home');
    } catch (_) {
        mask(t('liff-open-in-line'));
    }
}

// 回到带 token 的 /home 后:打开复核屏对应单(等 purchase-form 就绪)。
function liffResume(): void {
    const doc = sessionStorage.getItem(LIFF_DOC_KEY);
    if (!doc) return;
    sessionStorage.removeItem(LIFF_DOC_KEY);
    let tries = 0;
    const open = () => {
        if (typeof window.openPurchaseForm === 'function') window.openPurchaseForm(doc);
        else if (tries++ < 40) setTimeout(open, 120);
    };
    open();
}

if (qp('liff') === 'purchase') liffEntry(qp('doc'));
else liffResume();
