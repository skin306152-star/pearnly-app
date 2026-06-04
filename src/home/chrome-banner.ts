// ============================================================
// REFACTOR-WB-modularize · 非 Chromium 浏览器一次性提示 banner 从 folder-watcher.js 拆出
//
// 与文件夹监听无业务耦合 · 仅检测内核 + 顶部 banner + 跟随语言重渲。
// 主页加载后(及切语言经 window._refreshChromeBanner)触发。
// ============================================================
// v118.24 · Chromium 浏览器检测 + 顶部 banner(非 Chromium 系一次性提示)
function _isChromium() {
    try {
        if (navigator.userAgentData && Array.isArray(navigator.userAgentData.brands)) {
            return navigator.userAgentData.brands.some((b) =>
                /chromium|google chrome|microsoft edge/i.test(b.brand || '')
            );
        }
    } catch {}
    const ua = navigator.userAgent || '';
    if (/Edg\//.test(ua)) return true; // Edge (Chromium)
    if (/Chrome\//.test(ua) && !/OPR\/|YaBrowser|Opera/.test(ua)) return true; // Chrome
    return false;
}
function _showChromeBanner() {
    try {
        if (_isChromium()) return;
        if (localStorage.getItem('pearnly_chrome_banner_dismissed') === '1') return;
        const el = document.getElementById('chrome-only-banner');
        if (!el) return;
        const msgEl = el.querySelector('[data-i18n="chrome-banner-msg"]');
        const btnEl = el.querySelector('[data-i18n="chrome-banner-dismiss"]');
        if (msgEl && typeof t === 'function') msgEl.textContent = t('chrome-banner-msg');
        if (btnEl && typeof t === 'function') btnEl.textContent = t('chrome-banner-dismiss');
        el.style.display = '';
        const closeBtn = document.getElementById('chrome-only-banner-close');
        if (closeBtn && !closeBtn.dataset.bound) {
            closeBtn.dataset.bound = '1';
            closeBtn.addEventListener('click', () => {
                el.style.display = 'none';
                try {
                    localStorage.setItem('pearnly_chrome_banner_dismissed', '1');
                } catch {}
            });
        }
    } catch (e) {
        /* 静默 */
    }
}
// 主页面加载后 + 切语言后都触发(让文案跟随当前语言)
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _showChromeBanner);
    } else {
        setTimeout(_showChromeBanner, 0);
    }
}
window._refreshChromeBanner = _showChromeBanner;
