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

// 新码 → message_key 的代表映射。detail.message_key 缺席时(如白名单/已学规则只带
// rule_code)用它取人话标签;有 detail 时仍以 detail.message_key 为准(更精确,
// 例如 R-DATE-01 可能是无法解析或未来日期两种)。
const RULE_CODE_TO_MSGKEY: Record<string, string> = {
    'R-VAT-01': 'risk.vat_mismatch',
    'R-VAT-02': 'risk.total_mismatch',
    'R-SUM-01': 'risk.line_sum_mismatch',
    'R-LINE-01': 'risk.line_amount_mismatch',
    'R-MULTIPAGE-01': 'risk.multipage_mismatch',
    'R-TAXID-01': 'risk.seller_tax_id_invalid',
    'R-TAXID-02': 'risk.buyer_tax_id_invalid',
    'R-TAXID-03': 'risk.tax_id_placeholder',
    'R-DUP-01': 'risk.duplicate_exact',
    'R-DUP-02': 'risk.duplicate_suspected',
    'R-DATE-01': 'risk.invoice_date_unparseable',
    'R-DATE-02': 'risk.invoice_date_out_of_period',
    'R-SUP-01': 'risk.supplier_not_allowlisted',
    'R-SUP-02': 'risk.supplier_force_review',
    'R-LIMIT-01': 'risk.amount_over_limit',
    'R-CAT-01': 'risk.category_no_auto_push',
};

// 异常行的人话标签。新引擎 finding 的 detail.message_key(risk.*)最精确;旧库存
// 行(math_mismatch 等)及 confidence_low 走 exc-rule-<code>;无 detail 的新码用
// 上面的映射;都缺则显原始码。
function _labelOr(key: string, fallback: string) {
    const v = t(key);
    return v && v !== key ? v : fallback;
}

type ExcRuleLike = { rule_code?: string; detail?: { message_key?: string } | null };

function excRuleLabel(it: ExcRuleLike) {
    const code = it.rule_code || '';
    const mk = it.detail && it.detail.message_key;
    if (mk) {
        const v = _labelOr(mk, '');
        if (v) return v;
    }
    const byCode = _labelOr('exc-rule-' + code, '');
    if (byCode) return byCode;
    const mapped = RULE_CODE_TO_MSGKEY[code];
    if (mapped) {
        const v = _labelOr(mapped, '');
        if (v) return v;
    }
    return code;
}

// 筛选 chip 的规则分组。16 个新码收成 5 组,每组同时纳入对应旧码,使部署前产生的
// 历史异常行(math_mismatch / tax_id_format_invalid / duplicate / amount_missing)仍可按组筛。
const EXC_RULE_GROUPS: { labelKey: string; codes: string[] }[] = [
    {
        labelKey: 'exc-grp-arithmetic',
        codes: ['R-VAT-01', 'R-VAT-02', 'R-SUM-01', 'R-LINE-01', 'R-MULTIPAGE-01', 'math_mismatch'],
    },
    {
        labelKey: 'exc-grp-taxid',
        codes: ['R-TAXID-01', 'R-TAXID-02', 'R-TAXID-03', 'tax_id_format_invalid'],
    },
    { labelKey: 'exc-grp-dup', codes: ['R-DUP-01', 'R-DUP-02', 'duplicate'] },
    { labelKey: 'exc-grp-date', codes: ['R-DATE-01', 'R-DATE-02'] },
    { labelKey: 'exc-grp-customer', codes: ['R-SUP-01', 'R-SUP-02', 'R-LIMIT-01', 'R-CAT-01'] },
    { labelKey: 'exc-grp-fields', codes: ['amount_missing'] },
    { labelKey: 'exc-chip-confidence_low', codes: ['confidence_low'] },
];

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

export {
    _tn,
    _sevSvg,
    _emptySvg,
    _fmtMoney,
    _shortDate,
    _v,
    _money,
    _shortDateTime,
    excRuleLabel,
    EXC_RULE_GROUPS,
};
