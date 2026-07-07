// 采购导出页 · Google 连接卡组件(状态查询 / 渲染 / 连接 / 断开)。
// 从 purchase-export.ts 抽出以守单一职责。卡片骨架(#pex-gcard 等)与样式由该页 shell()/PAGE_CSS 注入。
// 原集成中心 Google 卡迁来并收敛为唯一实现(元素 id 用 pex-g 前缀)· 端点 /api/integrations/google/*。
/* global t, escapeHtml, showToast */
import { papi, activeWsId, purchaseErrMsg } from './purchase-common.js';

interface GoogleStatus {
    configured: boolean;
    connected: boolean;
    email: string;
}

function render(st: GoogleStatus): void {
    const badge = document.getElementById('pex-gbadge');
    const desc = document.getElementById('pex-gdesc');
    const act = document.getElementById('pex-gact');
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
        act.innerHTML = `<button class="ig-btn" id="pex-gdisconnect">${escapeHtml(t('int-google-disconnect'))}</button>`;
        const b = document.getElementById('pex-gdisconnect');
        if (b) b.onclick = gDisconnect;
        return;
    }
    badge.className = 'int-gst off';
    badge.textContent = t('int-google-st-off');
    desc.textContent = t('int-google-desc');
    act.innerHTML = `<button class="ig-btn pri" id="pex-gconnect">${escapeHtml(t('int-google-connect'))}</button>`;
    const b = document.getElementById('pex-gconnect');
    if (b) b.onclick = gConnect;
}

// 连接走整页导航换一次性票据(与集成中心同一后端端点)· 按当前套账隔离。
async function gConnect(): Promise<void> {
    const ws = activeWsId();
    if (ws == null) {
        showToast(t('workspace.required'), 'error');
        return;
    }
    try {
        const res = (await papi(
            'POST',
            `/api/integrations/google/connect/start?workspace_client_id=${ws}`
        )) as { url?: string };
        if (!res.url) throw new Error('missing_google_connect_url');
        window.location.href = res.url;
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

async function gDisconnect(): Promise<void> {
    if (typeof window.showConfirm === 'function') {
        const ok = await window.showConfirm(t('int-google-disconnect-confirm'));
        if (!ok) return;
    }
    const ws = activeWsId();
    const q = ws != null ? `?workspace_client_id=${ws}` : '';
    try {
        await papi('POST', `/api/integrations/google/disconnect${q}`);
        showToast(t('int-google-disconnected'), 'success');
        loadPexGoogleCard();
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

export async function loadPexGoogleCard(): Promise<void> {
    const ws = activeWsId();
    if (ws == null) {
        render({ configured: true, connected: false, email: '' });
        return;
    }
    try {
        const st = (await papi(
            'GET',
            `/api/integrations/google/status?workspace_client_id=${ws}`
        )) as GoogleStatus;
        render(st);
    } catch (_) {
        render({ configured: true, connected: false, email: '' });
    }
}
