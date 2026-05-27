// ============================================================
// REFACTOR-C1 (2026-05-27 R8) · Help modal 关闭绑定 help-modal 从 home.js 抽出为 ES module
//
// 来源:home.js L880-913 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

// v118.33.7.8 · 修 X 关闭 BUG · Phase 2 删 sidebar-user 时把 help-modal close 逻辑误删 · 这里独立绑回
(function () {
    function _bindHelpModal() {
        const helpModal = document.getElementById('help-modal');
        const helpClose = document.getElementById('help-modal-close');
        if (!helpModal) return;
        if (helpClose && !helpClose.dataset.bound) {
            helpClose.addEventListener('click', function () {
                helpModal.style.display = 'none';
            });
            helpClose.dataset.bound = '1';
        }
        if (!helpModal.dataset.maskBound) {
            helpModal.addEventListener('click', function (e) {
                if (e.target === helpModal) helpModal.style.display = 'none';
            });
            helpModal.dataset.maskBound = '1';
        }
        // ESC 关闭
        if (!window._helpModalEscBound) {
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && helpModal.style.display === 'flex') {
                    helpModal.style.display = 'none';
                }
            });
            window._helpModalEscBound = true;
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _bindHelpModal);
    } else {
        _bindHelpModal();
    }
})();
