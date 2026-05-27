// ============================================================
// REFACTOR-C1 (2026-05-27 R8) · 集成页「配置」按钮→抽屉 integration-config 从 home.js 抽出为 ES module
//
// 来源:home.js L915-933 · verbatim 0 改逻辑(仅 prettier 重排)。
// 委派到 window.openIntegrationDrawer(留在 home.js · 经 window. 调用)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

// v118.32.5.5.37 NAV-IA Phase 5 收尾 · 集成页「配置」按钮 → 右侧抽屉(不再跳 automation 路由)
// anchor→drawer tab 映射(google-drive/sheets 走原 inline 展开 · 不拦截)
(function () {
    const _anchorMap = {
        line: 'line',
        folder: 'folder',
        gmail: 'email',
        erp: 'erp',
        alert: 'alert',
    };
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.int-btn-configure');
        if (!btn) return;
        const row = btn.closest('.integration-row');
        const anchor = row ? row.dataset.intAnchor : null;
        if (anchor && _anchorMap[anchor]) {
            const nameEl = row.querySelector('.int-name');
            const title = nameEl ? (nameEl.textContent || nameEl.innerText || '').trim() : '配置';
            if (typeof window.openIntegrationDrawer === 'function') {
                window.openIntegrationDrawer(_anchorMap[anchor], title);
            }
        }
        // google-drive / google-sheets 走原有 inline 展开逻辑 · 不拦截
    });
})();
