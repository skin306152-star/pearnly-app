// ============================================================
// REFACTOR-C1 (2026-05-27) · GL vs 销项税报告对账 gl-vat-recon 从 home.js 抽出为 ES module
// REFACTOR-WB (2026-06-02) · STATE 入 store + 拆 6 子模块(store/helpers/upload/results/history/run)。
// REFACTOR-C5 · 迁 TypeScript · _glvPreviewFiles 参数标注 + window 桥进 globals.d.ts(行为 verbatim)。
// ============================================================
import { STATE } from './glv-store.js';
import { $, _renderKpi } from './glv-helpers.js';
import { _bindUpload, _updateStatus, _removeFile, _glvFiles, _reset } from './glv-upload.js';
import { _renderTable, _renderSummary, _bindSectionToggle } from './glv-results.js';
import { _loadHistory, _applyGlvSearch } from './glv-history.js';
import { _run, _export } from './glv-run.js';

// ── 语言切换时重渲（不依赖离开/返回 tab） ───────────────────────
function _onLangChange() {
    // 1. 状态条
    if (!STATE.running) _updateStatus();
    // 2. 历史表（按钮 title / 空状态文案都靠 _t() 动态生成）
    _loadHistory();
    // 3. 当前明细表（表头由 data-i18n 处理，但单元格里 "未找到" 等动态文案要重渲）
    if (STATE.lastDetail && STATE.lastDetail.length) {
        _renderTable(STATE.lastDetail);
    }
    if (STATE.lastSummary) {
        _renderSummary(STATE.lastSummary);
    }
}

// ── 初始化（首次进入 tab 时调用） ────────────────────────────────
function ensureInit() {
    if (STATE.inited) {
        _loadHistory(); // 二次进入也刷新历史
        return;
    }
    STATE.inited = true;
    _bindUpload('glv-drop-gl', 'glv-gl-input', 'glv-gl-name', 'glFile');
    _bindUpload('glv-drop-vat', 'glv-vat-input', 'glv-vat-name', 'vatFile');
    const btnRun = $('btn-glv-run');
    if (btnRun) btnRun.addEventListener('click', _run);
    const btnExp = $('btn-glv-export');
    if (btnExp) btnExp.addEventListener('click', _export);
    const btnReset = $('btn-glv-reset');
    if (btnReset) btnReset.addEventListener('click', _reset);
    const glvSearchEl = $('glv-hist-search');
    if (glvSearchEl) glvSearchEl.addEventListener('input', _applyGlvSearch);
    _bindSectionToggle();
    _renderKpi(null); // 初始 KPI 显示 '—'
    _updateStatus();
    window._loadGlvHistory = _loadHistory;
    _loadHistory();
    // v118.32.5.1 · 订阅 i18n 切换总线 · 切语言实时刷新动态文案
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('gl-vat-recon', _onLangChange);
    }
}

window._glvRemoveFile = _removeFile;

window.GlVatRecon = { ensureInit };
// v118.35.0.3 · 让 preview panel(在另一个 IIFE)能拿到多文件 STATE
window._glvPreviewFiles = function (kind: string) {
    return _glvFiles(kind === 'vat' ? 'vatFile' : 'glFile');
};
