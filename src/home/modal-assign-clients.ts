// ============================================================
// REFACTOR-WB-C3 · 客户分配 modal inner 从 home.html 抽出 · 运行期注入
//
// home.html 留空壳 <div id="assign-clients-modal">(overlay · display:none)· 本模块 eval 时注入 .modal inner。
// binder = assign-clients.js · _bindOnce() 仅在 window.openAssignClientsModal(用户开弹窗)时调用 → 非 eval 期直绑 →
// 注入(eval 期)必早于任何用户打开 → getElementById('assign-modal-*') 必命中。home.js 0 引用。
// i18n:注入后子树补译(镜像 applyLang)· 切语言由 applyLang + subscribeI18n('assign-clients-modal') 覆盖。verbatim inner。
// ============================================================
(function () {
    'use strict';
    const m = document.getElementById('assign-clients-modal');
    if (!m || m.dataset.wbInjected === '1') return;
    m.innerHTML = `
    <div class="modal" style="max-width:480px">
        <div class="modal-head">
            <div class="modal-title">
                <span data-i18n="assign-modal-title">分配客户</span>
                <span class="modal-title-sub" id="assign-modal-target"></span>
            </div>
            <button type="button" class="modal-close" id="assign-modal-close" aria-label="Close">
                <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l8 8M14 6l-8 8" stroke-linecap="round"/></svg>
            </button>
        </div>
        <div class="modal-body">
            <div class="assign-modal-toolbar">
                <label class="assign-toolbar-checkbox">
                    <input type="checkbox" id="assign-select-all">
                    <span data-i18n="assign-select-all">全选</span>
                </label>
                <span class="assign-toolbar-count" id="assign-selected-count"></span>
            </div>
            <div class="assign-clients-list" id="assign-clients-list">
                <div class="assign-empty" data-i18n="assign-loading">加载中...</div>
            </div>
        </div>
        <div class="modal-foot">
            <button type="button" class="btn btn-ghost" id="assign-modal-cancel" data-i18n="assign-cancel">取消</button>
            <button type="button" class="btn btn-primary" id="assign-modal-save" data-i18n="assign-save">保存</button>
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
