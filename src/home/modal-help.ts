// REFACTOR-WB-C3 · 帮助弹窗 inner 抽出 home.html → 运行期注入
// home.html 留空壳 <div id="help-modal">,本模块注入 .modal inner。
// help-modal.js 是 eval 期 IIFE + early-return guard(!helpClose return)→ main.js 本模块 import 必置 help-modal.js 前。
// i18n:注入后对自身子树补译(读 window._currentLang/window.I18N · 镜像 applyLang)。
const HELP_MODAL_HTML = `
    <div class="modal" style="max-width:440px">
        <div class="modal-head">
            <div class="modal-title" data-i18n="help-modal-title">帮助反馈</div>
            <button type="button" class="modal-close" id="help-modal-close" aria-label="Close">
                <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l8 8M14 6l-8 8" stroke-linecap="round"/></svg>
            </button>
        </div>
        <div class="modal-body">
            <p class="help-modal-tip" data-i18n="help-modal-tip">遇到问题或有产品建议?以下方式联系我们 · 通常 24 小时内回复</p>
            <div class="help-contact-list">
                <a class="help-contact-card" href="mailto:hello@pearnly.com">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="5" width="18" height="14" rx="2"/>
                        <path d="M3 7l9 6 9-6"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-email-label">邮箱</div>
                        <div class="help-contact-value">hello@pearnly.com</div>
                    </div>
                </a>
                <a class="help-contact-card" href="tel:+66868892228">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-phone-label">电话</div>
                        <div class="help-contact-value">+66 86-889-2228</div>
                    </div>
                </a>
                <a class="help-contact-card" href="https://line.me/R/ti/p/@059oupmg" target="_blank" rel="noopener">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-line-label">LINE 客服</div>
                        <div class="help-contact-value">@059oupmg</div>
                    </div>
                </a>
            </div>
        </div>
    </div>`;

function _injectHelpModal() {
    const host = document.getElementById('help-modal');
    if (!host || host.children.length) return;
    host.innerHTML = HELP_MODAL_HTML;
    const lang = window._currentLang || 'th';
    const dict: Record<string, string> = (window.I18N && window.I18N[lang]) || {};
    host.querySelectorAll('[data-i18n]').forEach((el) => {
        const k = el.getAttribute('data-i18n');
        if (k && dict[k]) el.textContent = dict[k];
    });
}

// 必须在 help-modal.js(eval 期 IIFE)之前注入,否则其 getElementById('help-modal-close') 为 null → early-return 静默失效。
// 本模块 import 置于 help-modal.js 前 → eval 期此处先注入。
if (document.readyState === 'loading') {
    _injectHelpModal();
} else {
    _injectHelpModal();
}
