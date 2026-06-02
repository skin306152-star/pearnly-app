// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 v2 上传区 + 文件预览面板 + 运行按钮态 · 从 bank-recon-v2.js 抽出
// verbatim 0 改逻辑。读/写 S.stmtFiles / S.glFiles / S.brv2Search(就地 mutate + 重赋值都安全)。
// ============================================================
import { S } from './bank-recon-v2-store.js';
import { $, esc2, _brv2FmtSize } from './bank-recon-v2-helpers.js';

// ── File rendering（vex-drop-filename + preview panel） ──────────
function renderFileList(zone) {
    const files = zone === 'stmt' ? S.stmtFiles : S.glFiles;
    // 更新拖拽区内摘要文字
    const nameEl = $(`brv2-${zone}-name`);
    if (nameEl) {
        if (files.length === 0) {
            nameEl.textContent = '';
        } else {
            const lang = window._currentLang || 'zh';
            const labels = { zh: '个文件', th: ' ไฟล์', en: ' file(s)', ja: ' ファイル' };
            nameEl.textContent = files.length + (labels[lang] || ' 个文件');
        }
    }
    // 若 preview panel 已展开则刷新对应列
    const panel = $('brv2-preview-panel');
    if (panel && panel.style.display !== 'none') {
        _renderBrv2Column(zone);
    }
    _updateTogglePreviewBtn();
}

function _updateTogglePreviewBtn() {
    const btn = $('brv2-toggle-preview');
    const panel = $('brv2-preview-panel');
    const hasFiles = S.stmtFiles.length + S.glFiles.length > 0;
    if (btn) btn.style.display = hasFiles ? '' : 'none';
    if (!hasFiles && panel) {
        panel.style.display = 'none';
        if (btn) btn.classList.remove('open');
    }
}

function _renderBrv2PreviewPanel() {
    _renderBrv2Column('stmt');
    _renderBrv2Column('gl');
}

function _renderBrv2Column(zone) {
    const colEl = $(zone === 'stmt' ? 'brv2-pp-stmt-col' : 'brv2-pp-gl-col');
    if (!colEl) return;
    const files = zone === 'stmt' ? S.stmtFiles : S.glFiles;
    const lang = window._currentLang || 'zh';
    const titleMap = {
        stmt: { zh: '① 银行账单', th: '① บัญชีธนาคาร', en: '① Bank Stmt', ja: '① 銀行明細' },
        gl: { zh: '② 总账 GL', th: '② GL รายงาน', en: '② GL Report', ja: '② GL帳簿' },
    };
    const title = (titleMap[zone] || {})[lang] || titleMap[zone].zh;
    const ph = esc2((window.t && window.t('vex-preview-search')) || '搜索文件名...');
    const clearLbl = esc2((window.t && window.t('vex-preview-clear-all')) || '全清');
    const searchVal = S.brv2Search[zone] || '';

    colEl.innerHTML =
        '<div class="vex-pp-col-title">' +
        '<span class="vex-pp-col-name">' +
        esc2(title) +
        ' <span class="vex-pp-col-count">' +
        files.length +
        '</span></span>' +
        '</div>' +
        '<div class="vex-pp-search-row">' +
        '<input class="vex-pp-search" id="brv2-pp-search-' +
        zone +
        '" type="text" placeholder="' +
        ph +
        '" value="' +
        esc2(searchVal) +
        '" autocomplete="off">' +
        '<button class="vex-pp-clear-btn" id="brv2-pp-clearall-' +
        zone +
        '" type="button">' +
        clearLbl +
        '</button>' +
        '</div>' +
        '<div class="vex-pp-file-list" id="brv2-pp-' +
        zone +
        '-list"></div>' +
        '<div class="vex-pp-pagination" id="brv2-pp-' +
        zone +
        '-pg"></div>';

    const si = $('brv2-pp-search-' + zone);
    if (si)
        si.addEventListener('input', function (e) {
            S.brv2Search[zone] = e.target.value;
            _renderBrv2FileList(zone);
        });
    const ca = $('brv2-pp-clearall-' + zone);
    if (ca)
        ca.addEventListener('click', function () {
            if (zone === 'stmt') S.stmtFiles.length = 0;
            else S.glFiles.length = 0;
            renderFileList(zone);
            updateRunBtn();
        });
    _renderBrv2FileList(zone);
}

function _renderBrv2FileList(zone) {
    const listEl = $('brv2-pp-' + zone + '-list');
    const pgEl = $('brv2-pp-' + zone + '-pg');
    if (!listEl) return;
    const files = zone === 'stmt' ? S.stmtFiles : S.glFiles;
    const q = (S.brv2Search[zone] || '').toLowerCase();
    const filtered = q ? files.filter((f) => f.name.toLowerCase().includes(q)) : files.slice();
    const fileIco =
        '<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>';
    const delIco =
        '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';
    listEl.innerHTML = filtered
        .map(
            (f, i) =>
                '<div class="vex-pp-file-row">' +
                fileIco +
                '<span class="vex-pp-fi-name" title="' +
                esc2(f.name) +
                '">' +
                esc2(f.name) +
                '</span>' +
                '<span class="vex-pp-fi-size">' +
                _brv2FmtSize(f.size) +
                '</span>' +
                '<button class="vex-pp-fi-del" type="button" data-zone="' +
                zone +
                '" data-idx="' +
                files.indexOf(f) +
                '" aria-label="remove">' +
                delIco +
                '</button>' +
                '</div>'
        )
        .join('');
    listEl.querySelectorAll('.vex-pp-fi-del').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const idx = parseInt(btn.dataset.idx, 10);
            if (btn.dataset.zone === 'stmt') S.stmtFiles.splice(idx, 1);
            else S.glFiles.splice(idx, 1);
            renderFileList(btn.dataset.zone);
            updateRunBtn();
        });
    });
    if (pgEl) {
        const tpl = (window.t && window.t('vex-preview-count')) || '显示 {n} / 共 {m}';
        pgEl.textContent = tpl.replace('{n}', filtered.length).replace('{m}', files.length);
    }
}

function _initBrv2TogglePreview() {
    const btn = $('brv2-toggle-preview');
    if (btn && !btn._reconBound) {
        btn._reconBound = true;
        btn.addEventListener('click', function () {
            const panel = $('brv2-preview-panel');
            const label = $('brv2-toggle-preview-label');
            const isOpen = panel && panel.style.display !== 'none';
            if (panel) panel.style.display = isOpen ? 'none' : '';
            btn.classList.toggle('open', !isOpen);
            if (label)
                label.textContent = isOpen
                    ? (window.t && window.t('vex-toggle-preview-open')) || '查看清单'
                    : (window.t && window.t('vex-toggle-preview-close')) || '收起清单';
            if (!isOpen) _renderBrv2PreviewPanel();
        });
    }
}

function updateRunBtn() {
    const btn = $('brv2-run-btn');
    const status = $('brv2-status');
    const hasStmt = S.stmtFiles.length > 0;
    const hasGl = S.glFiles.length > 0;
    if (btn) btn.disabled = !(hasStmt && hasGl);
    if (status) {
        const lang = window._currentLang || 'zh';
        if (!hasStmt && !hasGl) {
            const m = {
                zh: '请上传银行账单和 GL 文件',
                th: 'กรุณาอัปโหลดบัญชีธนาคารและ GL',
                en: 'Upload bank statement and GL files',
                ja: '銀行明細と GL を両方アップロードしてください',
            };
            status.textContent = m[lang] || m.zh;
        } else if (!hasStmt) {
            const m = {
                zh: '还缺银行账单 PDF',
                th: 'ยังขาดไฟล์บัญชีธนาคาร PDF',
                en: 'Missing bank statement PDF',
                ja: '銀行明細 PDF が未アップロード',
            };
            status.textContent = m[lang] || m.zh;
        } else if (!hasGl) {
            const m = {
                zh: '还缺 GL 文件',
                th: 'ยังขาดไฟล์ GL',
                en: 'Missing GL file',
                ja: 'GL ファイルが未アップロード',
            };
            status.textContent = m[lang] || m.zh;
        } else {
            const m = {
                zh: '两份文件已就绪',
                th: 'พร้อมสอบทาน',
                en: 'Ready to reconcile',
                ja: '照合を開始できます',
            };
            status.textContent = m[lang] || m.zh;
        }
    }
}

// ── Drag-and-drop（整区点击 · 无独立按钮） ────────────────────────
function setupDrop(zoneId, inputId, zone) {
    const zoneEl = $(zoneId);
    const inputEl = $(inputId);
    if (!zoneEl || !inputEl) return;

    // 整区点击 → 弹文件对话框
    zoneEl.addEventListener('click', () => inputEl.click());
    zoneEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            inputEl.click();
        }
    });

    zoneEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        zoneEl.classList.add('drag-over');
    });
    zoneEl.addEventListener('dragleave', () => zoneEl.classList.remove('drag-over'));
    zoneEl.addEventListener('drop', (e) => {
        e.preventDefault();
        zoneEl.classList.remove('drag-over');
        const dropped = Array.from(e.dataTransfer.files || []);
        if (zone === 'stmt') S.stmtFiles.push(...dropped);
        else S.glFiles.push(...dropped);
        renderFileList(zone);
        updateRunBtn();
    });

    inputEl.addEventListener('change', () => {
        const chosen = Array.from(inputEl.files || []);
        if (zone === 'stmt') S.stmtFiles.push(...chosen);
        else S.glFiles.push(...chosen);
        inputEl.value = '';
        renderFileList(zone);
        updateRunBtn();
    });
}

export { renderFileList, updateRunBtn, setupDrop, _initBrv2TogglePreview };
