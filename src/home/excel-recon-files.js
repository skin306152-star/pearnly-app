// ============================================================
// REFACTOR-WB-modularize · Excel 公式对账 文件入队 + 预览面板 从 IIFE 拆出
// ============================================================
import { S, $, _esc, _fmtSize, ALLOWED_EXT, MAX_INV, MAX_REP } from './excel-recon-store.js';
// P1-1:不支持格式的明确提示(4 语)· 取代此前静默丢弃
function _vexToastRejected(n) {
    const lang = window._currentLang || 'th';
    const M = {
        zh: `已忽略 ${n} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,
        th: `ข้ามไฟล์ที่ไม่รองรับ ${n} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,
        en: `Ignored ${n} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,
        ja: `非対応ファイル ${n} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`,
    };
    showToast(M[lang] || M.th, 'warn');
}

// ── 文件入队(去重 + 上限) ──
function _addInvoices(files) {
    const seen = new Set(S.invoiceFiles.map((f) => f.name + '|' + f.size));
    let _rejected = 0; // P1-1:不支持格式不再静默丢弃 · 计数后给明确 toast
    for (const f of files) {
        if (!ALLOWED_EXT.test(f.name)) {
            _rejected++;
            continue;
        }
        const k = f.name + '|' + f.size;
        if (seen.has(k)) continue;
        seen.add(k);
        S.invoiceFiles.push(f);
        if (S.invoiceFiles.length >= MAX_INV) break;
    }
    if (_rejected > 0) _vexToastRejected(_rejected);
    if (S.invoiceFiles.length > MAX_INV) {
        S.invoiceFiles = S.invoiceFiles.slice(0, MAX_INV);
        showToast(t('vex-toast-cap-inv'), 'warn');
    }
    _renderFiles();
}

function _addReports(files) {
    const seen = new Set(S.reportFiles.map((f) => f.name + '|' + f.size));
    let _rejected = 0; // P1-1:不支持格式不再静默丢弃
    for (const f of files) {
        if (!ALLOWED_EXT.test(f.name)) {
            _rejected++;
            continue;
        }
        const k = f.name + '|' + f.size;
        if (seen.has(k)) continue;
        seen.add(k);
        S.reportFiles.push(f);
        if (S.reportFiles.length >= MAX_REP) break;
    }
    if (_rejected > 0) _vexToastRejected(_rejected);
    if (S.reportFiles.length > MAX_REP) {
        S.reportFiles = S.reportFiles.slice(0, MAX_REP);
        showToast(t('vex-toast-cap-rep'), 'warn');
    }
    _renderFiles();
}

function _removeInvoice(idx) {
    S.invoiceFiles.splice(idx, 1);
    _renderFiles();
}
function _removeReport(idx) {
    S.reportFiles.splice(idx, 1);
    _renderFiles();
}

function _renderFiles() {
    const il = $('vex-list-invoice');
    const rl = $('vex-list-report');
    const _cntInv = $('vex-count-invoice'),
        _cntRep = $('vex-count-report');
    if (_cntInv) _cntInv.textContent = S.invoiceFiles.length;
    if (_cntRep) _cntRep.textContent = S.reportFiles.length;

    const _row = (f, idx, kind) => `<div class="vex-fi">
        <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
        <span class="vex-fi-n" title="${_esc(f.name)}">${_esc(f.name)}</span>
        <span class="vex-fi-s">${_fmtSize(f.size)}</span>
        <button class="vex-fi-x" type="button" data-vex-kind="${kind}" data-vex-idx="${idx}" aria-label="remove">×</button>
    </div>`;
    if (il)
        il.innerHTML =
            S.invoiceFiles.map((f, i) => _row(f, i, 'inv')).join('') ||
            `<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>`;
    if (rl)
        rl.innerHTML =
            S.reportFiles.map((f, i) => _row(f, i, 'rep')).join('') ||
            `<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>`;

    // 删除按钮事件
    document.querySelectorAll('.vex-fi-x').forEach((b) => {
        b.addEventListener('click', (e) => {
            const k = b.dataset.vexKind;
            const i = parseInt(b.dataset.vexIdx, 10);
            if (k === 'inv') _removeInvoice(i);
            else _removeReport(i);
        });
    });

    // 启用 / 禁用「生成 Excel」按钮
    const ok = S.invoiceFiles.length > 0 && S.reportFiles.length > 0;
    $('vex-build').disabled = !ok || S.running;
    const info = $('vex-action-info');
    if (info) {
        if (!S.invoiceFiles.length || !S.reportFiles.length) {
            info.textContent = t('vex-need-both') || '需要至少 1 张发票 + 1 份 VAT 报告';
            info.className = 'vex-action-info muted';
        } else {
            info.textContent = (t('vex-ready') || '已就绪 · {a} 张发票 · {b} 份报告')
                .replace('{a}', S.invoiceFiles.length)
                .replace('{b}', S.reportFiles.length);
            info.className = 'vex-action-info ok';
        }
    }
    _renderPreviewPanel();
}

// ── 预览面板 ──
const _ppInvIcon = `<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>`;
const _ppRepIcon = `<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`;
const _ppDelIcon = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;

function _renderPreviewPanel() {
    const panel = $('vex-preview-panel');
    if (!panel || panel.style.display === 'none') return;
    _renderPreviewColFull('inv');
    _renderPreviewColFull('rep');
    const guide = $('vex-pp-guide');
    if (guide) guide.style.display = S.invoiceFiles.length > 100 ? 'flex' : 'none';
}

function _renderPreviewColFull(kind) {
    const colEl = $(kind === 'inv' ? 'vex-pp-invoice-col' : 'vex-pp-report-col');
    if (!colEl) return;
    const files = kind === 'inv' ? S.invoiceFiles : S.reportFiles;
    const searchVal = kind === 'inv' ? S.previewSearchInv : S.previewSearchRep;
    const title =
        t(kind === 'inv' ? 'vex-preview-invoice' : 'vex-preview-report') ||
        (kind === 'inv' ? '销售发票' : 'VAT 报告');
    const ph = _esc(t('vex-preview-search') || '搜索文件名...');
    const clearLbl = _esc(t('vex-preview-clear-all') || '全清');

    colEl.innerHTML = `
        <div class="vex-pp-col-title">
            <span class="vex-pp-col-name">${_esc(title)} <span class="vex-pp-col-count">${files.length}</span></span>
        </div>
        <div class="vex-pp-search-row">
            <input class="vex-pp-search" id="vex-pp-search-${kind}" type="text"
                   placeholder="${ph}" value="${_esc(searchVal)}" autocomplete="off">
            <button class="vex-pp-clear-btn" id="vex-pp-clearall-${kind}" type="button">${clearLbl}</button>
        </div>
        <div class="vex-pp-file-list" id="vex-pp-${kind}-list"></div>
        <div class="vex-pp-pagination" id="vex-pp-${kind}-pg"></div>`;

    const si = $('vex-pp-search-' + kind);
    if (si)
        si.addEventListener('input', (e) => {
            if (kind === 'inv') {
                S.previewSearchInv = e.target.value;
                S.previewLimitInv = 50;
            } else {
                S.previewSearchRep = e.target.value;
                S.previewLimitRep = 50;
            }
            _renderFileListOnly(kind);
        });

    const ca = $('vex-pp-clearall-' + kind);
    if (ca)
        ca.addEventListener('click', () => {
            if (kind === 'inv') {
                S.invoiceFiles = [];
                S.previewSearchInv = '';
                S.previewLimitInv = 50;
            } else {
                S.reportFiles = [];
                S.previewSearchRep = '';
                S.previewLimitRep = 50;
            }
            _renderFiles();
        });

    _renderFileListOnly(kind);
}

function _renderFileListOnly(kind) {
    const listEl = $('vex-pp-' + kind + '-list');
    const pgEl = $('vex-pp-' + kind + '-pg');
    if (!listEl) return;
    const files = kind === 'inv' ? S.invoiceFiles : S.reportFiles;
    const searchVal = kind === 'inv' ? S.previewSearchInv : S.previewSearchRep;
    const limit = kind === 'inv' ? S.previewLimitInv : S.previewLimitRep;
    const icon = kind === 'inv' ? _ppInvIcon : _ppRepIcon;

    const indexed = files.map((f, i) => ({ f, i }));
    const filtered = searchVal
        ? indexed.filter(({ f }) => f.name.toLowerCase().includes(searchVal.toLowerCase()))
        : indexed;
    const shown = filtered.slice(0, limit);

    listEl.innerHTML =
        shown
            .map(
                ({ f, i }) => `
        <div class="vex-pp-file-row">
            ${icon}
            <span class="vex-pp-fi-name" title="${_esc(f.name)}">${_esc(f.name)}</span>
            <span class="vex-pp-fi-size">${_fmtSize(f.size)}</span>
            <button class="vex-pp-fi-del" type="button" data-kind="${kind}" data-ridx="${i}" aria-label="remove">${_ppDelIcon}</button>
        </div>`
            )
            .join('') + `<div id="vex-pp-sentinel-${kind}" style="height:1px;flex-shrink:0"></div>`;

    listEl.querySelectorAll('.vex-pp-fi-del').forEach((btn) => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.ridx, 10);
            if (btn.dataset.kind === 'inv') _removeInvoice(idx);
            else _removeReport(idx);
        });
    });

    if (pgEl) {
        const tpl = t('vex-preview-count') || '显示前 {n} / 共 {m}';
        pgEl.textContent = tpl.replace('{n}', shown.length).replace('{m}', filtered.length);
    }
    _bindPreviewObserver(kind, filtered.length);
}

function _bindPreviewObserver(kind, totalFiltered) {
    const limit = kind === 'inv' ? S.previewLimitInv : S.previewLimitRep;
    if (limit >= totalFiltered) return;
    const sentinel = $('vex-pp-sentinel-' + kind);
    const listEl = $('vex-pp-' + kind + '-list');
    if (!sentinel || !listEl) return;
    const obs = new IntersectionObserver(
        (entries) => {
            if (!entries[0].isIntersecting) return;
            obs.disconnect();
            if (kind === 'inv') S.previewLimitInv += 50;
            else S.previewLimitRep += 50;
            _renderFileListOnly(kind);
        },
        { root: listEl, threshold: 0.8 }
    );
    obs.observe(sentinel);
}

// ── 拖拽事件 ──
function _bindDropzone(zoneId, inputId, onFiles, wrongKindHint) {
    const zone = $(zoneId);
    const input = $(inputId);
    if (!zone || !input) return;
    zone.addEventListener('click', () => input.click());
    zone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            input.click();
        }
    });
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const arr = Array.from(e.dataTransfer.files);
        const ok = arr.filter((f) => ALLOWED_EXT.test(f.name));
        if (!ok.length) {
            showToast(t('vex-toast-bad-ext'), 'error');
            return;
        }
        onFiles(ok);
    });
    input.addEventListener('change', () => {
        const arr = Array.from(input.files);
        onFiles(arr);
        input.value = '';
    });
}

export { _addInvoices, _addReports, _renderFiles, _renderPreviewPanel, _bindDropzone };
