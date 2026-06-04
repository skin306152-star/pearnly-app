// REFACTOR-WB-C3 · 运行期注入公共助手
//
// C3 把 home.html 各区块的静态 markup 抽进 src/home/*-html.js,空壳留 home.html。
// 本助手统一「注入 innerHTML + 子树初译」逻辑(原先各模块各抄一份)。
// 注入幂等(dataset.wbInjected 哨兵);子树初译镜像 applyLang,读 window.I18N/_currentLang,
// boot applyLang 已跑过,切语言由 applyLang 全文扫描覆盖,故初译失败不致命。
export function wbInject(id: string, html: string) {
    const m = document.getElementById(id);
    if (!m || m.dataset.wbInjected === '1') return;
    m.innerHTML = html;
    m.dataset.wbInjected = '1';
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (!I || !I[lang]) return;
        m.querySelectorAll('[data-i18n]').forEach((el) => {
            const k = el.getAttribute('data-i18n');
            if (k && I[lang][k]) el.textContent = I[lang][k];
        });
        m.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
            const k = el.getAttribute('data-i18n-placeholder');
            if (k && I[lang][k]) (el as HTMLInputElement).placeholder = I[lang][k];
        });
    } catch {
        // 初译失败不致命,切语言会补
    }
}
