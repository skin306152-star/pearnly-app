// ============================================================
// REFACTOR-WB (2026-06-02) · GL-VAT 对账 · 上传卡 + 文件态 · 从 gl-vat-recon.js 抽出 · verbatim 0 改逻辑。
// ============================================================
import { STATE } from './glv-store.js';
import { $, _t } from './glv-helpers.js';

// ── 文件选择 + 拖拽 ─────────────────────────────────────────────
// v118.35.0.3 · 销项税报告核查改多文件 · STATE.vatFile / STATE.glFile 现在是 File[]
function _bindUpload(cardId, inputId, nameId, target) {
    const card = $(cardId);
    const input = $(inputId);
    const name = $(nameId);
    if (!card || !input || !name) return;

    const addFiles = (files) => {
        if (!files || !files.length) return;
        const arr = Array.isArray(STATE[target]) ? STATE[target].slice() : [];
        const seen = new Set(arr.map((f) => f.name + '|' + f.size));
        for (const f of files) {
            if (!f) continue;
            const k = f.name + '|' + f.size;
            if (!seen.has(k)) {
                arr.push(f);
                seen.add(k);
            }
        }
        STATE[target] = arr;
        _renderCardSummary(name, arr);
        _updateRunButton();
        _updateStatus();
        // 同步 panel(若已展开)
        if (window._reconCollapse && window._reconCollapse.renderGlvPreview) {
            window._reconCollapse.renderGlvPreview();
        }
    };

    card.addEventListener('click', () => input.click());
    card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            input.click();
        }
    });
    input.addEventListener('change', () => {
        addFiles(Array.from(input.files || []));
        // 清空原生 input,允许重复选同名文件 · 同时避免 panel 仍从 input.files 取
        input.value = '';
    });

    // 拖拽
    card.addEventListener('dragover', (e) => {
        e.preventDefault();
        card.classList.add('drag-over');
    });
    card.addEventListener('dragleave', () => card.classList.remove('drag-over'));
    card.addEventListener('drop', (e) => {
        e.preventDefault();
        card.classList.remove('drag-over');
        const files =
            e.dataTransfer && e.dataTransfer.files ? Array.from(e.dataTransfer.files) : [];
        addFiles(files);
    });
}

function _renderCardSummary(nameEl, arr) {
    if (!nameEl) return;
    if (!arr || arr.length === 0) {
        nameEl.textContent = '';
        return;
    }
    const totalKB = arr.reduce((s, f) => s + Math.round(f.size / 1024), 0);
    if (arr.length === 1) {
        nameEl.textContent = arr[0].name + '  (' + totalKB + ' KB)';
    } else {
        const tpl = (window.t && window.t('glv-files-count')) || '{n} 个文件';
        nameEl.textContent = tpl.replace('{n}', arr.length) + '  (' + totalKB + ' KB)';
    }
}

function _glvFiles(target) {
    const v = STATE[target];
    return Array.isArray(v) ? v : v ? [v] : [];
}

function _updateRunButton() {
    const btn = $('btn-glv-run');
    if (!btn) return;
    const has = _glvFiles('glFile').length > 0 && _glvFiles('vatFile').length > 0;
    btn.disabled = !has || STATE.running;
}

function _updateStatus() {
    const status = $('glv-status');
    if (!status) return;
    if (STATE.running) return; // 跑中不覆盖
    const vN = _glvFiles('vatFile').length;
    const gN = _glvFiles('glFile').length;
    if (vN === 0 && gN === 0) {
        status.className = 'vex-action-info muted';
        status.innerHTML = '<span>' + _t('hint_need_both') + '</span>';
    } else if (vN > 0 && gN > 0) {
        status.className = 'vex-action-info ok';
        status.innerHTML = '<span>' + _t('hint_ready') + '</span>';
    } else {
        status.className = 'vex-action-info muted';
        status.innerHTML = '<span>' + _t('hint_need_one_more') + '</span>';
    }
}

// v118.32.5.5.25 · 删文件(X 按钮 / 全清按钮)· 真清 STATE + UI + 刷 panel
// v118.35.0.3 · 支持多文件 · idx=null 时整列清空 · idx=N 时只删第 N 个
function _removeFile(kind, idx) {
    const target = kind === 'vat' ? 'vatFile' : 'glFile';
    const inputId = kind === 'vat' ? 'glv-vat-input' : 'glv-gl-input';
    const nameId = kind === 'vat' ? 'glv-vat-name' : 'glv-gl-name';
    const arr = _glvFiles(target);
    if (idx == null) {
        STATE[target] = [];
    } else {
        STATE[target] = arr.filter((_, i) => i !== idx);
    }
    const inp = $(inputId);
    if (inp) inp.value = '';
    _renderCardSummary($(nameId), _glvFiles(target));
    _updateRunButton();
    _updateStatus();
    if (window._reconCollapse && window._reconCollapse.renderGlvPreview) {
        window._reconCollapse.renderGlvPreview();
    }
}

function _reset() {
    STATE.glFile = [];
    STATE.vatFile = [];
    STATE.currentTaskId = null;
    STATE.lastDetail = [];
    STATE.lastSummary = null;
    const vi = $('glv-vat-input');
    if (vi) vi.value = '';
    const gi = $('glv-gl-input');
    if (gi) gi.value = '';
    const vn = $('glv-vat-name');
    if (vn) vn.textContent = '';
    const gn = $('glv-gl-name');
    if (gn) gn.textContent = '';
    const rs = $('glv-result');
    if (rs) rs.style.display = 'none';
    const kpi = $('glv-kpi-strip');
    if (kpi) kpi.style.display = 'none';
    _updateRunButton();
    _updateStatus();
    if (window._glvClearPreviewSearch) window._glvClearPreviewSearch();
    if (window._reconCollapse && window._reconCollapse.renderGlvPreview) {
        window._reconCollapse.renderGlvPreview();
    }
}

export {
    _glvFiles,
    _bindUpload,
    _updateStatus,
    _updateRunButton,
    _removeFile,
    _renderCardSummary,
    _reset,
};
