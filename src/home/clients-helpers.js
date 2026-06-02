// ============================================================
// REFACTOR-WB (2026-06-02) · 客户管理 · 纯工具:鉴权/apiClient/颜色/learned 徽章 · 从 clients.js 抽出 · verbatim 0 改逻辑。
// ============================================================

// ---------- 工具 ----------
function authH() {
    return { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
}
async function apiClient(path, opts = {}) {
    const r = await fetch(path, {
        ...opts,
        headers: { 'Content-Type': 'application/json', ...authH(), ...(opts.headers || {}) },
    });
    if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || 'HTTP ' + r.status);
    }
    return r.json();
}

function getActiveColor() {
    const sel = document.querySelector('#client-color-picker .color-swatch.active');
    return sel ? sel.dataset.color : '#111111';
}

function _updateLearnedBadge(n) {
    const tag = document.getElementById('drawer-cat-learned-tag');
    if (!tag) return;
    // 如果有学过的供应商映射 · badge 显示「已学 N」 · 否则保持「自动建议」默认
    if (n > 0) {
        tag.textContent = (t('drawer-suggest-learned-with-count') || '已学 {n}').replace('{n}', n);
    }
}

export { authH, apiClient, getActiveColor, _updateLearnedBadge };
