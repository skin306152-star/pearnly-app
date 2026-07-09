/* Pearnly AI · 4 语词典装配层 · window.AII18N + window.at() · 复用 mrpilot_lang。
 * 同 console-i18n.js 先例:纯数据,浏览器独立 <script> 加载,不并入 JS bundle。
 * 词典本体拆到 ai-i18n-{zh,th,en,ja}.js(单文件<500 行铁律·词条随 W1-W5 各任务累加,
 * 4 语合一文件迟早破线)——本文件只装配 + 挂 at()/atSetLang(),4 个分片必须先加载。
 */
(function () {
    'use strict';
    var D = {
        zh: window.__AI_I18N_ZH__,
        th: window.__AI_I18N_TH__,
        en: window.__AI_I18N_EN__,
        ja: window.__AI_I18N_JA__,
    };
    var SUPPORTED = ['zh', 'th', 'en', 'ja'];
    function detectLang() {
        var saved = '';
        try {
            saved = localStorage.getItem('mrpilot_lang') || '';
        } catch (e) {
            saved = '';
        }
        if (SUPPORTED.indexOf(saved) >= 0) return saved;
        return 'zh';
    }
    window.AII18N = { lang: detectLang(), dict: D, supported: SUPPORTED };
    window.at = function (key, vars) {
        var d = D[window.AII18N.lang] || D.zh;
        var s = d[key] != null ? d[key] : D.zh[key] != null ? D.zh[key] : key;
        if (vars) {
            Object.keys(vars).forEach(function (k) {
                s = s.replace('{' + k + '}', vars[k]);
            });
        }
        return s;
    };
    window.atSetLang = function (lang) {
        if (SUPPORTED.indexOf(lang) < 0) return;
        window.AII18N.lang = lang;
        try {
            localStorage.setItem('mrpilot_lang', lang);
        } catch (e) {
            /* localStorage 不可用（隐私模式等）不阻断切语言 */
        }
    };
})();
