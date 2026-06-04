// ============================================================
// REFACTOR-WB-modularize · 设置页【联系我们 + 首选项】面板 从 archive-settings.js 拆出为独立 ES module
//
// archive-settings.js 抽 home.js 时把不相关的两块打包到了一起;二者不读归档规则状态,只是同属设置页。
// verbatim 0 改逻辑 · 加载顺序同原 IIFE(bundle defer · 裸调 home.js 暴露的全局)。
// ============================================================
/* global _contact, escapeHtml, token */
(function () {
    window.loadAboutPanel = () => loadAboutPanel();
    window.loadPrefsSettings = () => loadPrefsSettings();

    // ====== v0.14 · 联系我们 panel · v118.25.3 重构(LINE/Email/Phone/Address 4 项 · 删 Facebook) ======
    function loadAboutPanel() {
        const el = document.getElementById('settings-contact-grid');
        if (!el) return;
        const phone = _contact?.phone || '086-889-2228';
        const lineId = _contact?.line_id || '@Pearnly';
        const lineUrl = _contact?.line_url || 'https://line.me/R/ti/p/@059oupmg';
        const email = _contact?.email || 'hello@pearnly.com';
        const address = _contact?.address || 'Bangkok, Thailand';
        el.innerHTML = `
            <a class="contact-item" href="${escapeHtml(lineUrl)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t('contact-line'))}</div>
                    <div class="contact-value">${escapeHtml(lineId)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(email)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t('contact-email'))}</div>
                    <div class="contact-value">${escapeHtml(email)}</div>
                </div>
            </a>
            <a class="contact-item" href="tel:${escapeHtml(phone.replace(/[^\d+]/g, ''))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t('contact-phone'))}</div>
                    <div class="contact-value">${escapeHtml(phone)}</div>
                </div>
            </a>
            <div class="contact-item">
                <div class="contact-icon address">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s-7-7.5-7-13a7 7 0 1114 0c0 5.5-7 13-7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t('contact-address'))}</div>
                    <div class="contact-value">${escapeHtml(address)}</div>
                </div>
            </div>
        `;
    }

    // ====== v0.13 · 首选项加载 + 保存 ======
    async function loadPrefsSettings() {
        try {
            const resp = await fetch('/api/settings/dup-check', {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) return;
            const data = await resp.json();
            const cb = document.getElementById('pref-dup-check') as HTMLInputElement | null;
            if (cb) cb.checked = !!data.enabled;
        } catch (e) {
            console.warn('load prefs failed', e);
        }
    }

    // 绑定保存(只绑一次)
    const _prefDupCheckEl = document.getElementById('pref-dup-check');
    if (_prefDupCheckEl && !_prefDupCheckEl.dataset.bound) {
        _prefDupCheckEl.dataset.bound = '1';
        _prefDupCheckEl.addEventListener('change', async (e) => {
            const enabled = (e.target as HTMLInputElement).checked;
            try {
                const resp = await fetch('/api/settings/dup-check', {
                    method: 'PUT',
                    headers: {
                        Authorization: 'Bearer ' + token,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ enabled }),
                });
                if (resp.ok) {
                    showToast(
                        enabled ? t('pref-dup-check-on-toast') : t('pref-dup-check-off-toast'),
                        'success'
                    );
                } else {
                    (e.target as HTMLInputElement).checked = !enabled; // 回滚 UI
                    showToast(t('pref-save-failed'), 'error');
                }
            } catch (err) {
                (e.target as HTMLInputElement).checked = !enabled;
                showToast(t('pref-save-failed'), 'error');
            }
        });
    }
})();
