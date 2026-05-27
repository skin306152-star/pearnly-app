// ============================================================
// REFACTOR-C1 (2026-05-27) · 对账中心子tab切换+全站设置弹窗 recon-subtab-settings 从 home.js 抽出为 ES module
//
// 来源:home.js L12858-12982 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

/* global renderSettings */

/* ============================================================
 * v118.32.0 · 对账中心子 tab 切换 + 全站设置弹窗
 * 2026-05-25 P2 清理:旧客户期间销项税流程(屏A 建单 / 屏C 结果modal / 屏B 批量分类)
 *   已整体删除(无 UI 入口的废弃流程)· 仅保留仍在用的子 tab 切换 + 设置弹窗。
 * ============================================================ */
(function () {
    'use strict';

    // ── 对账中心子 tab 切换(bank / sale-vat / gl-vat)──
    function _setMainHeader(pane) {
        // L2 pane 各自有标题 · L1 永远保持 rc-page-title/rc-page-sub · 不随 tab 变
        return;
    }

    function _initSubTabs() {
        const tabs = document.querySelectorAll('[data-recon-tab]');
        tabs.forEach((btn) => {
            btn.addEventListener('click', () => {
                tabs.forEach((b) => b.classList.remove('active'));
                btn.classList.add('active');
                const pane = btn.dataset.reconTab;
                const paneBank = document.getElementById('recon-pane-bank');
                const paneSv = document.getElementById('recon-pane-sale-vat');
                const paneGlVat = document.getElementById('recon-pane-gl-vat');
                if (paneBank) paneBank.style.display = pane === 'bank' ? '' : 'none';
                if (paneSv) paneSv.style.display = pane === 'sale-vat' ? '' : 'none';
                if (paneGlVat) paneGlVat.style.display = pane === 'gl-vat' ? '' : 'none';
                _setMainHeader(pane);
                // 销项税(sale-vat)数据加载由新 VEX 模块自绑(_loadVexKpi/_loadVexTaskList)
                if (pane === 'gl-vat' && window.GlVatRecon) window.GlVatRecon.ensureInit();
                if (pane === 'bank' && typeof window._bankReconV2Init === 'function') {
                    window._bankReconV2Init();
                }
            });
        });
        const activeTab = document.querySelector('[data-recon-tab].active');
        if (activeTab) _setMainHeader(activeTab.dataset.reconTab);
    }

    // ── 全站设置弹窗(历史上挂在本模块 · 与销项税流程无关 · 保留原样)──
    // v118.32.3 · 系统设置改为 modal 弹窗(参考 DeepSeek/ChatGPT/Linear)
    function _wrapSettingsAsModal() {
        const page = document.getElementById('page-settings');
        if (!page) return null;
        let overlay = document.getElementById('settings-modal-overlay');
        if (overlay) return overlay;

        overlay = document.createElement('div');
        overlay.id = 'settings-modal-overlay';
        overlay.className = 'settings-modal-overlay';
        overlay.style.display = 'none';

        // 把 page-settings 移进 overlay
        page.parentElement.insertBefore(overlay, page);
        overlay.appendChild(page);

        // ✕ 关闭按钮 · v118.32.3.9 修:放进 page-settings 内部(position:absolute 相对 page-settings 定位)
        const closeBtn = document.createElement('button');
        closeBtn.id = 'settings-modal-close';
        closeBtn.className = 'settings-modal-close';
        closeBtn.setAttribute('aria-label', 'close');
        closeBtn.innerHTML =
            '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>';
        page.insertBefore(closeBtn, page.firstChild); // ← 放进 page-settings 内 · 不是 overlay 的子

        closeBtn.addEventListener('click', closeSettingsModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeSettingsModal();
        });

        return overlay;
    }

    function openSettingsModal() {
        const overlay = _wrapSettingsAsModal();
        if (!overlay) return;
        overlay.style.display = 'flex';
        document.body.classList.add('settings-modal-open');
        const page = document.getElementById('page-settings');
        if (page) page.style.display = 'block';

        // v118.32.3.8 · 主动触发 settings 初始化(renderSettings 填表单 + 模拟 click active tab 触发 access-log/team 的 hook)
        setTimeout(() => {
            try {
                if (typeof renderSettings === 'function') renderSettings();
            } catch (e) {
                console.warn('renderSettings:', e);
            }
            // 找当前 active tab · 没有就 fallback profile
            let activeTab =
                document.querySelector('.settings-tab.active') ||
                document.querySelector('.settings-tab[data-tab="profile"]');
            if (activeTab) {
                // 用 dispatchEvent 模拟点击 · 触发所有 click 绑定的 hook
                activeTab.click();
            }
        }, 50);
    }

    function closeSettingsModal() {
        const overlay = document.getElementById('settings-modal-overlay');
        if (overlay) overlay.style.display = 'none';
        document.body.classList.remove('settings-modal-open');
    }

    window.openSettingsModal = openSettingsModal;
    window.closeSettingsModal = closeSettingsModal;

    // Esc 关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const overlay = document.getElementById('settings-modal-overlay');
            if (overlay && overlay.style.display === 'flex') closeSettingsModal();
        }
    });

    // 兼容 hash 路由 · #/settings 也打开 modal
    window.addEventListener('hashchange', () => {
        if (location.hash === '#/settings') openSettingsModal();
    });
    window.addEventListener('DOMContentLoaded', () => {
        if (location.hash === '#/settings') openSettingsModal();
    });

    // ── init ──
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _initSubTabs);
    } else {
        _initSubTabs();
    }
})();
