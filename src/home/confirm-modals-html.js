// ============================================================
// REFACTOR-WB-C3 (2026-06-01) · 两个全局确认弹窗 inner 从 home.html 抽出 · 运行期注入
//
// home.html 留两空壳 <div id="pearnly-confirm-modal"> / <div id="confirm-modal">(modal-overlay·display:none)·
// 本模块 eval 时注入 inner。pearnly-confirm.js(window.pearnlyConfirm)/ confirm-modal.js(window.showConfirm·
// ~18 模块裸调)均在【调用时】(用户动作 handler · await)才读 inner 元素 · 且带 DOM 缺失守卫(退原生
// confirm / resolve(false))· 纯 on-demand 无 eval 绑定 · import 置二者(main.js line 18/26)前确定性更稳。
// i18n:注入后子树补译 · verbatim inner · 0 改结构。
// ============================================================
(function () {
    'use strict';
    function inject(id, html) {
        const m = document.getElementById(id);
        if (!m || m.dataset.wbInjected === '1') return;
        m.innerHTML = html;
        m.dataset.wbInjected = '1';
        try {
            const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
            const I = window.I18N;
            if (I && I[lang]) {
                m.querySelectorAll('[data-i18n]').forEach((el) => {
                    const k = el.getAttribute('data-i18n');
                    if (I[lang][k]) el.textContent = I[lang][k];
                });
            }
        } catch (e) {
            /* silent · 初译失败不致命 · 切语言会补 */
        }
    }
    inject(
        'pearnly-confirm-modal',
        `
        <div class="modal" style="max-width:420px;">
            <div class="modal-head">
                <div class="modal-title" id="pearnly-confirm-title" data-i18n="confirm-default-title">请确认</div>
                <button class="modal-close" id="pearnly-confirm-close" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body">
                <div id="pearnly-confirm-msg" class="pearnly-confirm-msg"></div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="pearnly-confirm-cancel" data-i18n="confirm-cancel">取消</button>
                <button class="btn btn-primary" id="pearnly-confirm-ok" data-i18n="confirm-ok">确定</button>
            </div>
        </div>
    `
    );
    inject(
        'confirm-modal',
        `
    <div class="modal" style="max-width:420px;">
        <div class="modal-head">
            <div class="modal-title" id="confirm-modal-title" data-i18n="confirm-default-title">请确认</div>
            <button class="modal-close" id="confirm-modal-close" aria-label="close">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
            </button>
        </div>
        <div class="modal-body" id="confirm-modal-body" style="white-space:pre-wrap;line-height:1.55;"></div>
        <div class="modal-foot">
            <button class="btn btn-ghost" id="confirm-modal-cancel" data-i18n="confirm-cancel">取消</button>
            <button class="btn btn-primary" id="confirm-modal-ok" data-i18n="confirm-ok">确定</button>
        </div>
    </div>
`
    );
})();
