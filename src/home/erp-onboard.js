// ============================================================
// REFACTOR-C1 (2026-05-27) · ERP 对接新用户引导 erp-onboard 从 home.js 抽出为 ES module
//
// 来源:home.js L12749-12855 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

// ============================================================
// v118.27.8.1.15 · ERP 对接新用户引导
//   - 首次进入「自动化 → ERP 对接」sub-tab + 没有任何 endpoint + localStorage 没标记 → 弹一次
//   - 自注入轻量 modal · 不依赖 pearnlyConfirm(它只接受单消息字符串)
//   - 用户切语言时 · 如果 modal 还开着 · 重渲全文
// ============================================================
(function () {
    'use strict';

    const STORAGE_KEY = 'pearnly_erp_onboard_shown';
    let _shownThisSession = false;

    function _hasAnyEndpoint() {
        try {
            return Array.isArray(window._erpEndpoints) && window._erpEndpoints.length > 0;
        } catch (_) {
            return false;
        }
    }

    function _injectModal() {
        if (document.getElementById('erp-onboard-mask')) return;
        const mask = document.createElement('div');
        mask.id = 'erp-onboard-mask';
        mask.className = 'erp-onboard-mask';
        mask.innerHTML =
            '<div class="erp-onboard-modal" role="dialog" aria-modal="true">' +
            '<div class="erp-onboard-icon">' +
            '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
            '<rect x="4" y="6" width="24" height="20" rx="3"/>' +
            '<path d="M9 13h14M9 18h10"/>' +
            '<path d="M22 22l3 3 5-5"/>' +
            '</svg>' +
            '</div>' +
            '<div class="erp-onboard-title" id="erp-onboard-title"></div>' +
            '<div class="erp-onboard-body" id="erp-onboard-body"></div>' +
            '<div class="erp-onboard-btns">' +
            '<button type="button" class="btn btn-secondary" id="erp-onboard-later"></button>' +
            '<button type="button" class="btn btn-primary" id="erp-onboard-ok"></button>' +
            '</div>' +
            '</div>';
        document.body.appendChild(mask);

        function _renderText() {
            const tEl = document.getElementById('erp-onboard-title');
            const bEl = document.getElementById('erp-onboard-body');
            const okEl = document.getElementById('erp-onboard-ok');
            const ltEl = document.getElementById('erp-onboard-later');
            if (tEl) tEl.textContent = t('erp-onboard-title');
            if (bEl) bEl.textContent = t('erp-onboard-body');
            if (okEl) okEl.textContent = t('erp-onboard-ok');
            if (ltEl) ltEl.textContent = t('erp-onboard-later');
        }
        _renderText();

        function _close() {
            mask.style.display = 'none';
        }

        document.getElementById('erp-onboard-ok').addEventListener('click', function () {
            try {
                localStorage.setItem(STORAGE_KEY, '1');
            } catch (_) {}
            _close();
            // 跳到「连接」sub-tab 顶部 · 鼓励用户新建
            try {
                const btnAddEp = document.querySelector(
                    '#btn-add-endpoint, [data-action="erp-add-endpoint"]'
                );
                if (btnAddEp) btnAddEp.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } catch (_) {}
        });
        document.getElementById('erp-onboard-later').addEventListener('click', function () {
            try {
                localStorage.setItem(STORAGE_KEY, '1');
            } catch (_) {}
            _close();
        });
        mask.addEventListener('click', function (ev) {
            if (ev.target === mask) _close();
        });

        // i18n 切语言时 · 如果还开着 · 重渲全文
        if (typeof window.subscribeI18n === 'function') {
            window.subscribeI18n('erp-onboard-modal', function () {
                if (mask.style.display !== 'none') _renderText();
            });
        }
    }

    function _maybeShow() {
        if (_shownThisSession) return;
        try {
            if (localStorage.getItem(STORAGE_KEY) === '1') return;
        } catch (_) {
            /* silent · localStorage 私模 / 兜底默认 */
        }
        // 已有 endpoint = 老用户 · 不打扰
        if (_hasAnyEndpoint()) return;
        _shownThisSession = true;
        _injectModal();
        // 双 rAF 确保 endpoints 真的拉完
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                if (_hasAnyEndpoint()) return; // 二次保护
                const mask = document.getElementById('erp-onboard-mask');
                if (mask) mask.style.display = 'flex';
            });
        });
    }

    // 点击进入 ERP 对接子面板时触发
    document.addEventListener('click', function (ev) {
        const erpTab = ev.target.closest('.auto-nav-item[data-auto-tab="erp"]');
        const erpSub = ev.target.closest('.erp-subtab[data-erp-subtab="connect"]');
        if (erpTab || erpSub) {
            // 等 _erpEndpoints 拉好 · 大概 300-600ms
            setTimeout(_maybeShow, 700);
        }
    });
})();
