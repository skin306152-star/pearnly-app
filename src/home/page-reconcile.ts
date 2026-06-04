import { RECON_HTML_1 } from './page-reconcile-panes-1.js'; // REFACTOR-WB-C1 · 对账中心壳 HTML 上半(head+tabs+银行对账 pane)
import { RECON_HTML_2 } from './page-reconcile-panes-2.js'; // REFACTOR-WB-C1 · 对账中心壳 HTML 下半(销项税+GL-VAT pane)

// ============================================================
// REFACTOR-WB-C3 (2026-05-29) · page-reconcile 静态骨架从 home.html 抽出 · 运行期模板注入(R6 机制)
//
// home.html <section id="page-reconcile"> 现为空壳 · 本模块注入骨架 innerHTML。
// 对账中心被 6 个模块渲染/绑定(recon-center / recon-subtab-settings / gl-vat-recon / bank-recon-v2 /
// recon-collapse / excel-formula-recon · 多含 DOMContentLoaded 绑定)→ 本 import 置于 main.js 最前(所有 home
// 模块之前)· eval 即注入 · 保证早于任何模块 eval-time getElementById 与 DOMContentLoaded · 元素恒在场。
// home.js parse 期 0 处绑定对账元素(已核 · 全走 window.loadReconcilePage 路由期 + 模块 DOMContentLoaded)。
// i18n:注入后子树补译(镜像 applyLang)· 切语言由 applyLang 全文扫描覆盖。verbatim 搬迁骨架 · 0 改结构。
// ============================================================
(function () {
    'use strict';
    const sec = document.getElementById('page-reconcile');
    if (!sec || sec.dataset.wbInjected === '1') return;
    sec.innerHTML = RECON_HTML_1 + RECON_HTML_2;
    sec.dataset.wbInjected = '1';
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            sec.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n');
                if (k && I[lang][k]) el.textContent = I[lang][k];
            });
            sec.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                const k = el.getAttribute('data-i18n-placeholder');
                if (k && I[lang][k]) (el as HTMLInputElement).placeholder = I[lang][k];
            });
        }
    } catch (e) {
        /* silent · 初译失败不致命 · 切语言会补 */
    }
})();
