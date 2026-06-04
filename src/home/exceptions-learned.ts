// ============================================================
// REFACTOR-WB (2026-06-02) · 异常栏 · 学习规则列表 loadLearnedRules · 从 exceptions.js 抽出 · verbatim 0 改逻辑。
// ============================================================
/* global escapeHtml, showConfirm, currentLang, humanizeError */
import { _shortDateTime } from './exceptions-helpers.js';

async function loadLearnedRules() {
    const wrap = document.getElementById('learned-list');
    if (!wrap) return;
    wrap.innerHTML = `<div class="learned-empty">${escapeHtml(t('set-learned-loading'))}</div>`;
    try {
        const resp = await fetch('/api/exception-whitelist', {
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        const data = await resp.json();
        const items = data.items || [];
        if (items.length === 0) {
            wrap.innerHTML = `<div class="learned-empty">${escapeHtml(t('set-learned-empty'))}</div>`;
            return;
        }
        const trashSvg = `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
        </svg>`;
        wrap.innerHTML = items
            .map(
                (it: {
                    id: unknown;
                    rule_code: string;
                    seller_name: unknown;
                    created_at?: string | null;
                }) => {
                    const ruleLabel = t('exc-rule-' + it.rule_code) || it.rule_code;
                    return `
                <div class="learned-row" data-wl-id="${escapeHtml(String(it.id))}">
                    <div class="learned-seller" title="${escapeHtml(it.seller_name)}">${escapeHtml(it.seller_name)}</div>
                    <div class="learned-rule">${escapeHtml(ruleLabel)}</div>
                    <div class="learned-date">${escapeHtml(_shortDateTime(it.created_at))}</div>
                    <button class="learned-del-btn" data-del-wl="${escapeHtml(String(it.id))}" title="${escapeHtml(t('set-learned-del'))}" type="button">${trashSvg}</button>
                </div>
            `;
                }
            )
            .join('');
    } catch (e) {
        console.warn('loadLearnedRules fail', e);
        wrap.innerHTML = `<div class="learned-empty">${escapeHtml(t('exc-toast-load-fail'))}</div>`;
    }
}

export { loadLearnedRules };
