// 集成中心 · Google Drive/Sheets 授权卡(外流归档 OAuth)。
// 骨架由 page-integrations.ts 注入(#int-google-card);本模块按 status 填连接态 + 绑连接/断开。
// 连接走整页浏览器导航(connect 302 跳 Google · 鉴权头带不上 → ?t= 传同一 Bearer · 后端 B 方案网关)。
// 凭据按套账隔离(workspace_client_id)· 个人模式/未选账套 → 提示先选公司。
/* global t, token, showToast */
import { papi, purchaseErrMsg, activeWsId, injectStyle } from './purchase-common.js';

interface GoogleStatus {
    configured: boolean;
    connected: boolean;
    email: string;
    scope: string;
}

const CSS = `
.int-gst{font-size:11px;font-weight:700;border-radius:6px;padding:2px 8px;}
.int-gst.on{background:var(--green-weak);color:var(--green);}
.int-gst.off{background:var(--line2);color:var(--ink3);}
.int-gst.na{background:var(--line2);color:var(--ink3);}
#int-google-act .ig-btn{padding:6px 12px;border:1px solid var(--line);background:var(--card);color:var(--ink2);border-radius:6px;font-family:inherit;font-size:12px;font-weight:500;cursor:pointer;}
#int-google-act .ig-btn:hover{background:var(--bg);border-color:var(--ink-4);color:var(--ink);}
#int-google-act .ig-btn.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700;}
#int-google-act .ig-btn.pri:hover{background:var(--accent-deep);}
#int-google-act .ig-btn:disabled{opacity:.55;cursor:not-allowed;}
#int-google-card.hl{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-weak);}
`;

function connectUrl(ws: number): string {
    const tk = typeof token === 'string' ? token : '';
    return `/api/integrations/google/connect?workspace_client_id=${ws}&t=${encodeURIComponent(tk)}`;
}

function render(st: GoogleStatus): void {
    const badge = document.getElementById('int-google-st');
    const desc = document.getElementById('int-google-desc');
    const act = document.getElementById('int-google-act');
    if (!badge || !desc || !act) return;

    if (!st.configured) {
        badge.className = 'int-gst na';
        badge.textContent = t('int-google-st-na');
        desc.textContent = t('int-google-na-desc');
        act.innerHTML = '';
        return;
    }
    if (st.connected) {
        badge.className = 'int-gst on';
        badge.textContent = t('int-google-st-on');
        desc.textContent = st.email
            ? t('int-google-connected-as', { email: st.email })
            : t('int-google-desc');
        act.innerHTML = `<button class="ig-btn" id="int-google-disconnect">${t('int-google-disconnect')}</button>`;
        const btn = document.getElementById('int-google-disconnect');
        if (btn) btn.onclick = disconnect;
        return;
    }
    badge.className = 'int-gst off';
    badge.textContent = t('int-google-st-off');
    desc.textContent = t('int-google-desc');
    act.innerHTML = `<button class="ig-btn pri" id="int-google-connect">${t('int-google-connect')}</button>`;
    const btn = document.getElementById('int-google-connect');
    if (btn) btn.onclick = connect;
}

function connect(): void {
    const ws = activeWsId();
    if (ws == null) {
        showToast(t('workspace.required'), 'error');
        return;
    }
    // 整页导航:鉴权 fetch 拿不到 302 跳转 → location.href 让浏览器直接走授权流。
    window.location.href = connectUrl(ws);
}

async function disconnect(): Promise<void> {
    if (typeof window.showConfirm === 'function') {
        const okc = await window.showConfirm(t('int-google-disconnect-confirm'));
        if (!okc) return;
    }
    const ws = activeWsId();
    const q = ws != null ? `?workspace_client_id=${ws}` : '';
    try {
        await papi('POST', `/api/integrations/google/disconnect${q}`);
        showToast(t('int-google-disconnected'), 'success');
        loadIntegrationGoogle();
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

// 进集成页 / 切账套时刷新;失败保守显「未连接 + 连接」(不阻断页面)。
function loadIntegrationGoogle(): void {
    injectStyle('int-google-css', CSS);
    const card = document.getElementById('int-google-card');
    if (!card) return;
    const ws = activeWsId();
    const q = ws != null ? `?workspace_client_id=${ws}` : '';
    papi('GET', `/api/integrations/google/status${q}`)
        .then((d) => render(d as GoogleStatus))
        .catch(() => render({ configured: true, connected: false, email: '', scope: '' }));
}

// 外流面板 412(未连)→ 跳集成中心后高亮 Google 卡引导授权。
function highlightGoogleCard(): void {
    const card = document.getElementById('int-google-card');
    if (!card) return;
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    card.classList.add('hl');
    setTimeout(() => card.classList.remove('hl'), 1600);
}

window.loadIntegrationGoogle = loadIntegrationGoogle;
window.highlightGoogleCard = highlightGoogleCard;
