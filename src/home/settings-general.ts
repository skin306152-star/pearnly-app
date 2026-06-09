// ============================================================
// REFACTOR-C1 (2026-05-27 R8) · 设置→通用面板 settings-general 从 home.js 抽出为 ES module
//
// 来源:home.js L760-770(语言 select 切换)+ L1878-1962(generalSettingsModule · tz/date/number)· verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

/* global applyLang, currentLang */

// v118.28.5.1 · 设置 → 系统 → 通用设置 · 语言 select 切换(替代旧 set-lang-row 4 按钮卡)
(function () {
    const sel = document.getElementById('general-lang') as HTMLSelectElement | null;
    if (!sel) return;
    sel.addEventListener('change', (e) => {
        const lang = (e.target as HTMLSelectElement).value;
        if (lang) applyLang(lang);
    });
    const _curLang =
        (typeof currentLang === 'string' && currentLang) ||
        localStorage.getItem('mrpilot_lang') ||
        'th';
    sel.value = _curLang;
})();

// 当前阶段:语言走 applyLang 全通路 · 其他三项前端 localStorage 占位
// 后端 schema 留给 v118.29.x 一起加(避免本版引入空 schema)
(function generalSettingsModule() {
    'use strict';

    const LS_TZ = 'pearnly_general_tz';
    const LS_DATE = 'pearnly_general_date_format';
    const LS_NUMBER = 'pearnly_general_number_format';
    const LS_CALENDAR = 'pearnly_calendar';

    const DEFAULTS = {
        tz: 'Asia/Bangkok',
        date: 'YYYY-MM-DD',
        number: 'comma_dot',
        calendar: 'buddhist',
    };

    function _loadGeneral() {
        const tz = document.getElementById('general-tz') as HTMLSelectElement | null;
        const dt = document.getElementById('general-date') as HTMLSelectElement | null;
        const nm = document.getElementById('general-number') as HTMLSelectElement | null;
        const cal = document.getElementById('general-calendar') as HTMLSelectElement | null;
        if (!tz || !dt || !nm) return;
        try {
            tz.value = localStorage.getItem(LS_TZ) || DEFAULTS.tz;
            dt.value = localStorage.getItem(LS_DATE) || DEFAULTS.date;
            nm.value = localStorage.getItem(LS_NUMBER) || DEFAULTS.number;
            if (cal) cal.value = localStorage.getItem(LS_CALENDAR) || DEFAULTS.calendar;
        } catch (e) {
            tz.value = DEFAULTS.tz;
            dt.value = DEFAULTS.date;
            nm.value = DEFAULTS.number;
            if (cal) cal.value = DEFAULTS.calendar;
        }
    }

    async function _saveGeneral() {
        const btn = document.getElementById('btn-save-general') as HTMLButtonElement | null;
        const msg = document.getElementById('general-save-msg');
        if (!btn) return;
        const orig = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span>' + (t('msg-saving') || '保存中...') + '</span>';
        if (msg) {
            msg.textContent = '';
            msg.classList.remove('error');
        }
        try {
            const tz =
                ((document.getElementById('general-tz') || {}) as { value?: string }).value ||
                DEFAULTS.tz;
            const dt =
                ((document.getElementById('general-date') || {}) as { value?: string }).value ||
                DEFAULTS.date;
            const nm =
                ((document.getElementById('general-number') || {}) as { value?: string }).value ||
                DEFAULTS.number;
            const cal =
                ((document.getElementById('general-calendar') || {}) as { value?: string }).value ||
                DEFAULTS.calendar;
            try {
                localStorage.setItem(LS_TZ, tz);
                localStorage.setItem(LS_DATE, dt);
                localStorage.setItem(LS_NUMBER, nm);
                localStorage.setItem(LS_CALENDAR, cal);
            } catch (e) {}
            window._pearnlyGeneral = { tz: tz, date_format: dt, number_format: nm };
            if (msg) msg.textContent = t('msg-saved') || '已保存';
        } catch (e) {
            if (msg) {
                msg.textContent = t('msg-save-failed') || '保存失败';
                msg.classList.add('error');
            }
        } finally {
            btn.disabled = false;
            btn.innerHTML = orig;
            setTimeout(function () {
                if (msg) msg.textContent = '';
            }, 3000);
        }
    }

    function _bind() {
        const btn = document.getElementById('btn-save-general') as
            | (HTMLButtonElement & { _pearnlyGenBound?: boolean })
            | null;
        if (!btn) {
            setTimeout(_bind, 200);
            return;
        }
        if (btn._pearnlyGenBound) return;
        btn._pearnlyGenBound = true;
        btn.addEventListener('click', _saveGeneral);
        _loadGeneral();
    }

    function _rerenderAll() {
        _loadGeneral();
        const sel = document.getElementById('general-lang') as HTMLSelectElement | null;
        if (sel) {
            const cur =
                (typeof currentLang === 'string' && currentLang) ||
                localStorage.getItem('mrpilot_lang') ||
                'th';
            sel.value = cur;
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _bind);
    } else {
        _bind();
    }

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('settings-general', _rerenderAll);
    }
})();
