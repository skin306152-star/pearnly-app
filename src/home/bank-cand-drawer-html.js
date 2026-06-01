// ============================================================
// REFACTOR-WB-C3 (2026-06-01) · 银行对账「候选匹配抽屉」inner 从 home.html 抽出 · 运行期注入
//
// home.html 留空壳 <div id="bank-cand-drawer">(fixed drawer · display:none)· 本模块 eval 时注入 inner。
// bank-recon.js(main.js 内 import 在本模块之后)load()→bindEvents() 按需(automation bank tab 点击)才绑
// [data-bank-cand-close]/btn-bank-cand-ignore · eval 期注入恒早于首次 load · 故确定性在场(非竞态)。
// home.js 已 0 行(全拆完)· 0 处 parse/init 引用 bank-cand-* 元素(已核)。
// i18n:注入后子树补译(镜像 applyLang)· 切语言由 applyLang 全文扫描覆盖。verbatim inner · 0 改结构。
// ============================================================
(function () {
    'use strict';
    const m = document.getElementById('bank-cand-drawer');
    if (!m || m.dataset.wbInjected === '1') return;
    m.innerHTML = `
    <div class="bank-cand-backdrop" data-bank-cand-close></div>
    <div class="bank-cand-panel">
        <div class="bank-cand-head">
            <div>
                <div class="bank-cand-title" data-i18n="bank-cand-title">匹配候选</div>
                <div class="bank-cand-sub" id="bank-cand-tx-info"></div>
            </div>
            <button class="modal-close" data-bank-cand-close aria-label="close">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
            </button>
        </div>
        <div class="bank-cand-body" id="bank-cand-body">
            <div class="bank-empty" data-i18n="bank-cand-loading">加载中…</div>
        </div>
        <div class="bank-cand-foot">
            <button class="btn btn-ghost btn-small" id="btn-bank-cand-ignore">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10"/></svg>
                <span data-i18n="bank-cand-ignore">忽略此条流水</span>
            </button>
        </div>
    </div>
`;
    m.dataset.wbInjected = '1';
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            m.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n');
                if (I[lang][k]) el.textContent = I[lang][k];
            });
            m.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
                const k = el.getAttribute('data-i18n-placeholder');
                if (I[lang][k]) el.placeholder = I[lang][k];
            });
        }
    } catch (e) {
        /* silent · 初译失败不致命 · 切语言会补 */
    }
})();
