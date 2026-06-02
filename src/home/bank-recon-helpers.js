// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 M10 · 纯工具:进度/错误/格式化/评分徽章 · 从 bank-recon.js 抽出
// verbatim 0 改逻辑。
// ============================================================

function _scoreBadge(score) {
    const n = Number(score || 0);
    let cls = 'score-low';
    if (n >= 85) cls = 'score-high';
    else if (n >= 60) cls = 'score-mid';
    return (
        '<span class="bank-cand-score ' +
        cls +
        '">' +
        n.toFixed(0) +
        ' ' +
        t('bank-cand-score-unit') +
        '</span>'
    );
}

// ---------- 工具 ----------
function showBankProgress(show) {
    const el = document.getElementById('bank-upload-progress');
    if (el) el.style.display = show ? '' : 'none';
}

function showBankError(msg) {
    const el = document.getElementById('bank-upload-error');
    if (el) {
        el.textContent = msg;
        el.style.display = '';
    }
}

function hideBankError() {
    const el = document.getElementById('bank-upload-error');
    if (el) el.style.display = 'none';
}

function formatUploadError(detail) {
    const map = {
        'bank_recon.only_pdf': t('bank-err-only-pdf'),
        'bank_recon.empty_file': t('bank-err-empty'),
        'bank_recon.file_too_large': t('bank-err-too-large'),
        'bank_recon.save_failed': t('bank-err-server'),
        // v118.26.1 · 批量上传扩展错误码
        'bank_recon.scanned': t('bank-err-scanned'),
        'bank_recon.no_tx': t('bank-err-no-tx'),
        network: t('bank-err-network'),
    };
    return map[detail] || t('bank-err-unknown') + ' (' + detail + ')';
}

function fmtAmt(v) {
    if (v === null || v === undefined) return '-';
    const n = Number(v);
    if (isNaN(n)) return '-';
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(s) {
    if (!s) return '-';
    const str = String(s);
    return str.length >= 10 ? str.slice(0, 10) : str;
}

function formatPeriod(a, b) {
    if (!a && !b) return '';
    return (formatDate(a) || '?') + ' ~ ' + (formatDate(b) || '?');
}

function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

export {
    _scoreBadge,
    showBankProgress,
    showBankError,
    hideBankError,
    formatUploadError,
    fmtAmt,
    formatDate,
    formatPeriod,
    esc,
};
