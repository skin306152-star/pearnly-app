/* Pearnly DMS · 4 语词典装配层 · window.DXI18N + window.dt()。
 * 同 ai-i18n.js 先例:纯数据分片(dms-i18n-{zh,th,en,ja}.js)独立 <script> 先加载,
 * 本文件只装配 + 挂 dt()/dtSetLang()。复用 mrpilot_lang(与主站/其它壳共享语言选择)。 */
(function () {
    'use strict';
    var D = {
        zh: window.__DMS_I18N_ZH__,
        th: window.__DMS_I18N_TH__,
        en: window.__DMS_I18N_EN__,
        ja: window.__DMS_I18N_JA__,
    };
    var SUPPORTED = ['zh', 'th', 'en', 'ja'];
    function detectLang() {
        var saved = '';
        try {
            saved = localStorage.getItem('mrpilot_lang') || '';
        } catch (e) {
            saved = '';
        }
        return SUPPORTED.indexOf(saved) >= 0 ? saved : 'zh';
    }
    window.DXI18N = { lang: detectLang(), dict: D, supported: SUPPORTED };
    window.dt = function (key, vars) {
        var d = D[window.DXI18N.lang] || D.zh;
        var s = d[key] != null ? d[key] : D.zh[key] != null ? D.zh[key] : key;
        if (vars) {
            Object.keys(vars).forEach(function (k) {
                s = s.replace('{' + k + '}', vars[k]);
            });
        }
        return s;
    };
    window.dtSetLang = function (lang) {
        if (SUPPORTED.indexOf(lang) < 0) return;
        window.DXI18N.lang = lang;
        try {
            localStorage.setItem('mrpilot_lang', lang);
        } catch (e) {
            /* localStorage 不可用(隐私模式)不阻断切语言 */
        }
    };
})();
