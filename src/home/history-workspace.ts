// ============================================================
// 识别记录抽屉 · 「归属套账」下拉(桥 bindDrawerWorkspace · history-drawer 打开时调)
// 税号路由再准也有例外(代付/票面税号印错)→ 给手动改归属的口子。
// 单套账租户不注入(没得挪 · 不加噪音);改归属打 POST /api/history/{id}/assign_workspace。
// ============================================================
/* global token, t, showToast, escapeHtml */

type WsClient = { id: number; name?: string };

function _wsCache(): WsClient[] {
    return (window._workspaceClientsCache as WsClient[]) || [];
}

async function _ensureWsCache(): Promise<WsClient[]> {
    let cache = _wsCache();
    if (!cache.length && typeof window.fetchWorkspaceClients === 'function') {
        try {
            await window.fetchWorkspaceClients();
        } catch {
            /* 拉不到就不注入 */
        }
        cache = _wsCache();
    }
    return cache;
}

window.bindDrawerWorkspace = async function (historyId: unknown, currentWs: unknown) {
    document.getElementById('drawer-workspace-wrap')?.remove();
    const card = document.querySelector('.drawer-client-card');
    if (!card || !historyId) return;
    const cache = await _ensureWsCache();
    if (cache.length < 2) return;

    const wrap = document.createElement('div');
    wrap.id = 'drawer-workspace-wrap';
    wrap.className = 'drawer-client-body';
    wrap.innerHTML =
        '<select class="drawer-client-select" id="drawer-workspace-select" title="' +
        escapeHtml(t('drawer-workspace-label')) +
        '"><option value="">' +
        escapeHtml(t('drawer-workspace-label')) +
        '</option>' +
        cache
            .map(
                (c) =>
                    '<option value="' + c.id + '">' + escapeHtml(c.name || '#' + c.id) + '</option>'
            )
            .join('') +
        '</select>';
    card.appendChild(wrap);

    const sel = document.getElementById('drawer-workspace-select') as HTMLSelectElement | null;
    if (!sel) return;
    const cur = currentWs ? String(currentWs) : '';
    sel.value = cur;
    sel.onchange = async () => {
        if (!sel.value) {
            sel.value = cur; // 不许清空归属(Express 方向判定要锚点)
            return;
        }
        try {
            const r = await fetch(`/api/history/${historyId}/assign_workspace`, {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ workspace_client_id: parseInt(sel.value, 10) }),
            });
            if (!r.ok) throw new Error('assign_workspace ' + r.status);
            showToast(t('ws-msg-updated'), 'success');
        } catch (e) {
            console.error(e);
            showToast(t('ws-msg-save-fail'), 'fail');
            sel.value = cur;
        }
    };
};

export {};
