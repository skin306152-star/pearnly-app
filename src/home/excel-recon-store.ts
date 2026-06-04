// ============================================================
// REFACTOR-WB-modularize · Excel 公式对账(skin-only)共享 store + 常量 + 工具 从 IIFE 中心化
// ============================================================
const MAX_INV = 1000;
const MAX_REP = 30;
// P1-1 修(2026-05-25 销项税回归):此前只允许 pdf/jpg/png/webp · 但 UI 文案 + accept 宣传
//   支持 Excel/CSV/Word → 用户选了被静默丢弃(开始按钮还禁用)。放开到与 accept 一致 ·
//   后端发票侧/报告侧都已能解析这些格式(报告 parse_vat_report 全格式 · 发票走 pipeline)。
const ALLOWED_EXT = /\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i;

const $ = (id: string) => document.getElementById(id);
function _authHeader() {
    return { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
}
function _esc(s: unknown) {
    const map: Record<string, string> = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    };
    return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => map[c]);
}
function _fmtSize(b: number) {
    if (b < 1024) return b + ' B';
    if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
    return (b / 1024 / 1024).toFixed(1) + ' MB';
}

export const S = {
    invoiceFiles: [],
    reportFiles: [],
    running: false,
    vexAllRows: [],
    previewLimitInv: 50,
    previewLimitRep: 50,
    previewSearchInv: '',
    previewSearchRep: '',
    vexPage: 1,
};

export { MAX_INV, MAX_REP, ALLOWED_EXT, $, _authHeader, _esc, _fmtSize };
