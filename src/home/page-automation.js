import { AUTO_HTML_1 } from './page-automation-panes-1.js'; // REFACTOR-WB-C1 · 自动化页壳 HTML 上半(head+nav+ERP+银行 panel)
import { AUTO_HTML_2 } from './page-automation-panes-2.js'; // REFACTOR-WB-C1 · 自动化页壳 HTML 下半(邮箱+文件夹+LINE+提醒 panel)

// ============================================================
// REFACTOR-WB-C3 (2026-05-29) · page-automation 静态骨架从 home.html 抽出 · 运行期模板注入(R6 机制)
//
// home.html <section id="page-automation"(display:none)> 现为空壳 · 本模块注入骨架 innerHTML
// (含 .auto-content + 各 .auto-panel:line/folder/email/alert/erp/bank · 这些 panel 被 home.js
// openIntegrationDrawer 运行期 DOM-move 进集成抽屉 · 关闭时 _returnPanel 移回 .auto-content)。
// **import 置 main.js 最前(早于 notifications/folder-watcher/email-ingest/bank-recon/integration-config/
// erp-integration 等 panel 模块 eval/DOMContentLoaded)** → eval 即注入 · panel 恒在场;DOM-move 是运行期
// (用户点配置 · 远晚于注入)· 安全。home.js 对 .auto-panel/.auto-content 的访问全在 openIntegrationDrawer/
// _returnPanel 函数内(运行期)· parse 期 0 绑定(已核)。i18n 注入后子树补译。verbatim 0 改结构。
// ============================================================
(function () {
    'use strict';
    const sec = document.getElementById('page-automation');
    if (!sec || sec.dataset.wbInjected === '1') return;
    sec.innerHTML = AUTO_HTML_1 + AUTO_HTML_2;
    sec.dataset.wbInjected = '1';
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            sec.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n');
                if (I[lang][k]) el.textContent = I[lang][k];
            });
            sec.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                const k = el.getAttribute('data-i18n-placeholder');
                if (I[lang][k]) el.placeholder = I[lang][k];
            });
        }
    } catch (e) {
        /* silent · 初译失败不致命 · 切语言会补 */
    }
})();
