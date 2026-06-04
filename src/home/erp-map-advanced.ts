// ============================================================
// REFACTOR-C1 (2026-05-27) · ERP 字段映射高级 sub-tab toggle erp-map-advanced 从 home.js 抽出为 ES module
//
// 来源:home.js L12693-12740 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

// ============================================================
// v27.8.1.13a · 字段映射 · 显示/折叠高级 sub-tab toggle + 凭据 modal 调试入口
// 独立 IIFE · 不动 erp-mappings 现有逻辑
// ============================================================
(function () {
    'use strict';

    function _setToggleLabel() {
        const btn = document.getElementById('erp-map-show-advanced-btn');
        if (!btn) return;
        const subtabs = document.getElementById('erp-map-subtabs');
        if (!subtabs) return;
        const expanded = subtabs.classList.contains('show-advanced');
        const label = btn.querySelector('.erp-map-adv-btn-label');
        if (label && typeof t === 'function') {
            const k = expanded ? 'erp-map-hide-advanced' : 'erp-map-show-advanced';
            const v = t(k);
            if (v && v !== k) label.textContent = v;
        }
        btn.setAttribute('aria-pressed', expanded ? 'true' : 'false');
    }

    document.addEventListener('click', function (ev) {
        const btn = (ev.target as HTMLElement).closest('#erp-map-show-advanced-btn');
        if (!btn) return;
        ev.preventDefault();
        const subtabs = document.getElementById('erp-map-subtabs');
        if (!subtabs) return;
        subtabs.classList.toggle('show-advanced');
        _setToggleLabel();
        // 折叠时若当前 active 是高级 sub-tab · 切回客户映射
        if (!subtabs.classList.contains('show-advanced')) {
            const activeBtn = subtabs.querySelector(
                '.erp-map-subtab.active.erp-map-subtab-advanced'
            );
            if (activeBtn) {
                const clientBtn = subtabs.querySelector<HTMLElement>(
                    '.erp-map-subtab[data-erp-subtab="clients"]'
                );
                if (clientBtn) clientBtn.click();
            }
        }
    });

    function _rerenderAll() {
        _setToggleLabel();
    }

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('erp-map-advanced-toggle', _rerenderAll);
    }
})();
