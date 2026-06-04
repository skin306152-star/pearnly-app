// ============================================================
// REFACTOR-WB-C3 · 归档字段编辑 modal inner 从 home.html 抽出 · 运行期注入
//
// home.html 留空壳 <div id="archive-token-modal">(overlay · display:none)· 本模块 eval 时注入 .modal inner。
// archive-settings.js 用 document 级事件委托(click)· 不在 eval 期直绑 modal 元素 → 注入早于打开即可 · 无竞态。
// archive-token-body 由 JS 在 openArchiveTokenModal 时动态填充 · 本模块仅注入静态壳。home.js 0 引用。
// i18n:注入后子树补译(镜像 applyLang)· 切语言由 applyLang 全文扫描覆盖。verbatim inner · 0 改结构。
// ============================================================
(function () {
    'use strict';
    const m = document.getElementById('archive-token-modal');
    if (!m || m.dataset.wbInjected === '1') return;
    m.innerHTML = `
        <div class="modal" style="max-width:420px;">
            <div class="modal-head">
                <div class="modal-title" data-i18n="archive-token-title">编辑字段</div>
                <button class="modal-close" id="archive-token-close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body" id="archive-token-body"></div>
            <div class="modal-foot">
                <button class="btn btn-danger btn-ghost" id="btn-archive-token-delete" data-i18n="archive-token-delete">删除此字段</button>
                <button class="btn btn-primary" id="btn-archive-token-ok" data-i18n="archive-token-ok">确定</button>
            </div>
        </div>`;
    m.dataset.wbInjected = '1';
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            m.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n');
                if (k && I[lang][k]) el.textContent = I[lang][k];
            });
        }
    } catch (e) {
        /* silent · 初译失败不致命 · 切语言会补 */
    }
})();
