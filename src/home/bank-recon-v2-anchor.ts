// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 v2 anchor 预填 + 手动录入审计 · 从 bank-recon-v2.js 抽出
// verbatim 0 改逻辑。无可变状态(localStorage + 传入 summary)。
// ============================================================
import { _brv2T, _brv2EscHtml, _brv2FmtNum } from './bank-recon-v2-helpers.js';

// P0.1 BUG-B-T1 v118.35.0.37 · 3 anchor 预填 cache 跨会话 · localStorage 单 key 兜底
//   不分 bank · 1 个事务所 1-2 个银行 · 简化(后续 Phase 1 P1.4 加 confidence 时再 per-bank scope)
var _BRV2_ANCHOR_KEY = 'pearnly.brv2.lastAnchorOcr';
function _brv2SaveLastAnchorOcr(summary: any) {
    try {
        var ocr = summary && summary._anchor_ocr;
        if (!ocr || typeof ocr !== 'object') return;
        var payload = {
            stmt_opening: Number.isFinite(+ocr.stmt_opening) ? +ocr.stmt_opening : null,
            gl_opening: Number.isFinite(+ocr.gl_opening) ? +ocr.gl_opening : null,
            gl_closing: Number.isFinite(+ocr.gl_closing) ? +ocr.gl_closing : null,
            stmt_closing: Number.isFinite(+ocr.stmt_closing) ? +ocr.stmt_closing : null, // BUG-FIX-T3 v118.35.0.44
            ts: Date.now(),
        };
        localStorage.setItem(_BRV2_ANCHOR_KEY, JSON.stringify(payload));
    } catch (_) {
        /* 私模 localStorage / quota / JSON 异常 · 静默(下次跑还能再存)*/
    }
}
function _brv2ReadLastAnchorOcr() {
    try {
        var raw = localStorage.getItem(_BRV2_ANCHOR_KEY);
        if (!raw) return null;
        var p = JSON.parse(raw);
        if (!p || typeof p !== 'object') return null;
        return p;
    } catch (_) {
        return null;
    }
}
function _brv2RestoreAnchorPrefill() {
    var p = _brv2ReadLastAnchorOcr();
    if (!p) return;
    var map = {
        'brv2-anchor-stmt-opening': p.stmt_opening,
        'brv2-anchor-gl-opening': p.gl_opening,
        'brv2-anchor-gl-closing': p.gl_closing,
        'brv2-anchor-stmt-closing': p.stmt_closing, // BUG-FIX-T3 v118.35.0.44 · 加 4th anchor 预填
    };
    var prefilledCount = 0;
    Object.keys(map).forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        // 用户已经手填了任何值 → 不覆盖
        if ((el as HTMLInputElement).value !== '') return;
        var v = map[id as keyof typeof map];
        if (!Number.isFinite(v)) return;
        (el as HTMLInputElement).value = v.toFixed(2);
        var cell = el.closest && el.closest('.brv2-anchor-cell');
        if (cell) cell.classList.add('is-prefilled');
        prefilledCount += 1;
    });
    // 触发期初差额提示行(如果 stmt + gl opening 都预填了)
    var eq = document.getElementById('brv2-anchor-eq');
    var eqVal = document.getElementById('brv2-anchor-eq-val');
    if (eq && eqVal && Number.isFinite(p.stmt_opening) && Number.isFinite(p.gl_opening)) {
        var diff = p.stmt_opening - p.gl_opening;
        eqVal.textContent = diff.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        eq.style.display = '';
    }
    // BUG-FIX-T4 v118.35.0.45 · 至少 1 个 cell 被预填 → 显示橙色 banner 提示来源
    if (prefilledCount > 0) {
        var banner = document.getElementById('brv2-anchor-prefill-banner');
        if (banner) banner.classList.add('show');
    }
}
// BUG-FIX-T4 v118.35.0.45 · 用户改了任意一个 anchor 后 · 如果全部 cell 都没 is-prefilled · 隐藏 banner
function _brv2UpdatePrefillBannerVisibility() {
    var banner = document.getElementById('brv2-anchor-prefill-banner');
    if (!banner) return;
    var anyPrefilled = false;
    [
        'brv2-anchor-gl-closing',
        'brv2-anchor-stmt-closing',
        'brv2-anchor-stmt-opening',
        'brv2-anchor-gl-opening',
    ].forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        var cell = el.closest && el.closest('.brv2-anchor-cell');
        if (cell && cell.classList.contains('is-prefilled')) anyPrefilled = true;
    });
    banner.classList.toggle('show', anyPrefilled);
}

// P0.3 BUG-B-T3 v118.35.0.39 · 历史详情 / 跑完结果 显示『手动录入 anchor 对照表』
//   读 summary._anchor_overrides · 列每个被改 anchor 的 OCR 值 vs 用户值 vs 差额
//   动态创建 DOM 插入到 brv2-summary-collapse 之后 · 不动 home.html
var _BRV2_ANCHOR_LABEL_KEYS = [
    ['stmt_opening', 'brv2-anchor-stmt-opening'],
    ['gl_opening', 'brv2-anchor-gl-opening'],
    ['gl_closing', 'brv2-anchor-gl-closing'],
    ['stmt_closing', 'brv2-anchor-stmt-closing'], // BUG-FIX-T3 v118.35.0.44 · 加 4th anchor
];

function _brv2RenderAnchorAudit(summary: any) {
    var host = document.getElementById('brv2-summary-collapse');
    if (!host || !host.parentNode) return;
    var panel = document.getElementById('brv2-anchor-audit');
    var overrides = summary && summary._anchor_overrides;
    // 没 override → 移除既有 panel(切换不同 task 时清理)
    if (!overrides || typeof overrides !== 'object' || Object.keys(overrides).length === 0) {
        if (panel && panel.parentNode) panel.parentNode.removeChild(panel);
        return;
    }
    // 没 panel → 动态创建 · 插到 summary collapse 之后
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'brv2-anchor-audit';
        panel.style.cssText =
            'margin-top:14px;background:var(--warn-bg);border:1px solid var(--amber-500);' +
            'border-radius:8px;padding:14px 16px;';
        host.parentNode.insertBefore(panel, host.nextSibling);
    }
    // 渲染内容
    var rows = _BRV2_ANCHOR_LABEL_KEYS
        .map(function (pair) {
            var ov = overrides[pair[0]];
            if (!ov) return '';
            var ocr = +ov.ocr || 0;
            var usr = +ov.user || 0;
            var diff = usr - ocr;
            var sign = diff > 0 ? '+' : diff < 0 ? '' : '';
            var diffColor = Math.abs(diff) < 0.005 ? '#6b7280' : diff > 0 ? '#16a34a' : '#dc2626';
            return (
                '<tr>' +
                '<td style="padding:6px 10px;color:var(--ink);font-size:13px">' +
                _brv2EscHtml(_brv2T(pair[1], pair[0])) +
                '</td>' +
                '<td style="padding:6px 10px;color:var(--ink2);font-size:13px;text-align:right;' +
                'font-variant-numeric:tabular-nums">' +
                _brv2EscHtml(_brv2FmtNum(ocr)) +
                '</td>' +
                '<td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;' +
                'font-size:13px;text-align:right;font-variant-numeric:tabular-nums">' +
                _brv2EscHtml(_brv2FmtNum(usr)) +
                '</td>' +
                '<td style="padding:6px 10px;color:' +
                diffColor +
                ';font-weight:500;font-size:13px;' +
                'text-align:right;font-variant-numeric:tabular-nums">' +
                _brv2EscHtml(sign + _brv2FmtNum(diff)) +
                '</td>' +
                '</tr>'
            );
        })
        .join('');
    panel.innerHTML =
        '<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">' +
        _brv2EscHtml(
            _brv2T('brv2-anchor-audit-title', '⚠ This run contains manually entered anchors')
        ) +
        '</div>' +
        '<table style="width:100%;border-collapse:collapse;font-family:inherit">' +
        '<thead><tr>' +
        '<th style="padding:6px 10px;text-align:left;color:var(--ink2);font-size:11px;' +
        'font-weight:500;border-bottom:1px solid #fed7aa">' +
        _brv2EscHtml(_brv2T('brv2-anchor-audit-col-field', 'Field')) +
        '</th>' +
        '<th style="padding:6px 10px;text-align:right;color:var(--ink2);font-size:11px;' +
        'font-weight:500;border-bottom:1px solid #fed7aa">' +
        _brv2EscHtml(_brv2T('brv2-anchor-audit-col-ocr', 'OCR')) +
        '</th>' +
        '<th style="padding:6px 10px;text-align:right;color:var(--ink2);font-size:11px;' +
        'font-weight:500;border-bottom:1px solid #fed7aa">' +
        _brv2EscHtml(_brv2T('brv2-anchor-audit-col-user', 'User')) +
        '</th>' +
        '<th style="padding:6px 10px;text-align:right;color:var(--ink2);font-size:11px;' +
        'font-weight:500;border-bottom:1px solid #fed7aa">' +
        _brv2EscHtml(_brv2T('brv2-anchor-audit-col-diff', 'Diff')) +
        '</th>' +
        '</tr></thead><tbody>' +
        rows +
        '</tbody></table>';
}

export {
    _brv2SaveLastAnchorOcr,
    _brv2RestoreAnchorPrefill,
    _brv2UpdatePrefillBannerVisibility,
    _brv2RenderAnchorAudit,
};
