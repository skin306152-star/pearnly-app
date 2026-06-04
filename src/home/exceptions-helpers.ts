// ============================================================
// REFACTOR-WB (2026-06-02) · 异常栏 · 纯工具:i18n/SVG/格式化 · 从 exceptions.js 抽出 · verbatim 0 改逻辑。
// ============================================================
/* global escapeHtml, showConfirm, currentLang, humanizeError */

// v118.20.5 · 简易 i18n 占位替换({n} 等)
function _tn(key: string, vars?: Record<string, unknown>) {
    let s = t(key) || key;
    if (vars)
        for (const k in vars) s = s.replace(new RegExp('\\{' + k + '\\}', 'g'), String(vars[k]));
    return s;
}

// SVG 小图标(规则严重度)
function _sevSvg(sev: string) {
    if (sev === 'high') {
        return `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 1.5L1 12.5h12L7 1.5z"/>
            <line x1="7" y1="6" x2="7" y2="9"/>
            <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
        </svg>`;
    }
    if (sev === 'medium') {
        return `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="7" y1="4" x2="7" y2="7.5"/>
            <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
        </svg>`;
    }
    return `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="7" cy="7" r="5.5"/>
        <line x1="4.5" y1="7" x2="9.5" y2="7"/>
    </svg>`;
}

function _emptySvg() {
    return `<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 19l5 5 13-13"/>
        <circle cx="20" cy="20" r="17"/>
    </svg>`;
}

function _fmtMoney(n: unknown) {
    if (n === null || n === undefined) return '—';
    const v = parseFloat(String(n));
    if (isNaN(v)) return '—';
    return (
        '฿ ' + v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    );
}

function _shortDate(iso?: string | null) {
    if (!iso) return '—';
    return iso.slice(0, 10);
}

function _v(s: unknown) {
    if (s === null || s === undefined || String(s).trim() === '') {
        return `<span class="empty">${escapeHtml(t('exc-empty-val'))}</span>`;
    }
    return escapeHtml(String(s));
}

function _money(n: unknown) {
    if (n === null || n === undefined) return '—';
    const v = typeof n === 'number' ? n : parseFloat(String(n).replace(/,/g, ''));
    if (isNaN(v)) return escapeHtml(String(n));
    return (
        '฿ ' + v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    );
}

// ============================================================
// v118.21.2 · 设置页 · 学习规则面板(列出 / 撤销已学的白名单)
// ============================================================
function _shortDateTime(iso?: string | null) {
    if (!iso) return '—';
    try {
        const d = new Date(iso);
        const pad = (n: number) => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch (_) {
        return iso.slice(0, 16).replace('T', ' ');
    }
}

export { _tn, _sevSvg, _emptySvg, _fmtMoney, _shortDate, _v, _money, _shortDateTime };
