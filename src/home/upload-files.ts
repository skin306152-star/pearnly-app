// ============================================================
// REFACTOR-C1-home-batch5 (2026-05-31) · 上传【拖拽区/文件列表/开始按钮】从 home.js 抽出为独立 ES module
//
// 来源:home.js verbatim 0 改逻辑 · dropZone/fileInput 监听 / _isImageFile/_isPdfFile/
//   _isSupportedUpload / handleFiles / renderFileList / updateStartButton / btn-clear 监听。
// 桥回:window.renderFileList / window.updateStartButton(home.js bootstrap applyLang/用户初始化 +
//   upload-camera.js + ocr-recognize.js 调)。
// 调出:handleCameraImages(upload-camera.js 经 window)· _selectedFiles/getMaxFiles 等 home.js 全局。
// ============================================================
/* global _selectedFiles:writable, _results:writable, getMaxFiles, hideAlerts, showAlert, escapeHtml, renderResults, handleCameraImages, svgIcon */

const dropZone = document.getElementById('drop-zone') as HTMLElement;
const fileInput = document.getElementById('file-input') as HTMLInputElement;

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e: Event) =>
    handleFiles((e.target as HTMLInputElement).files)
);
['dragover', 'dragenter'].forEach((evt) => {
    dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
});
['dragleave', 'drop'].forEach((evt) => {
    dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });
});
dropZone.addEventListener('drop', (e: DragEvent) => {
    e.preventDefault();
    handleFiles(e.dataTransfer!.files);
});

// v118.35.0.3 · 主上传区接收 PDF / 图片 / Excel / CSV / Word — 跟 #file-input
// accept 属性 + drop-hint 文案对齐 · 之前只接 PDF 是个老遗留过滤(底层 OCR
// pipeline 已经多 schema 支持所有格式 / 后端 /api/ocr/recognize 也接全格式)
const _SUPPORTED_UPLOAD_EXT = /\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;
function _isImageFile(f: File) {
    return (
        (f.type && f.type.startsWith('image/')) || /\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(f.name)
    );
}
function _isPdfFile(f: File) {
    return f.type === 'application/pdf' || /\.pdf$/i.test(f.name);
}
function _isSupportedUpload(f: File) {
    return _isPdfFile(f) || _isImageFile(f) || _SUPPORTED_UPLOAD_EXT.test(f.name);
}

function handleFiles(fileList: FileList | null) {
    hideAlerts();
    const all = Array.from(fileList!);
    const supported = all.filter(_isSupportedUpload);
    if (supported.length !== all.length) {
        showAlert('warn', t('alert-unsupported-format'));
    }

    // 图片走 imagesToPdf 通道(保留拍照单张缓冲条 UX),其他(PDF / Excel / CSV /
    // Word / TXT)直接入 _selectedFiles · 后端走 multi-format pipeline
    const directFiles = supported.filter((f) => !_isImageFile(f));
    const imageFiles = supported.filter(_isImageFile);

    const existing = new Set(_selectedFiles.map((f) => f.name + '_' + f.size));
    for (const f of directFiles) {
        const key = f.name + '_' + f.size;
        if (!existing.has(key)) {
            _selectedFiles.push({
                file: f,
                name: f.name,
                size: f.size,
                status: 'waiting',
                errorKey: null,
                errorParams: null,
            });
            existing.add(key);
        }
    }

    if (imageFiles.length > 0) {
        // 复用相册多选路径 · 默认每张图独立成 1 个 PDF · 用户可在浮条里改"合并"
        try {
            handleCameraImages(imageFiles, 'gallery');
        } catch (err) {
            console.error('[upload] image route failed', err);
        }
    }

    const maxFiles = getMaxFiles();
    if (_selectedFiles.length > maxFiles) {
        showAlert('warn', t('alert-file-count', { n: maxFiles }));
        _selectedFiles = _selectedFiles.slice(0, maxFiles);
    }

    renderFileList();
    updateStartButton();
    fileInput.value = '';
}

// 文件列表展开状态(false = 紧凑滚动框)
let _fileListExpanded = false;

function renderFileList() {
    const list = document.getElementById('file-list');
    // v118.44.0.2 · admin layout 没有 #file-list DOM · 加防御避免 applyLang 抛错 / lang-switching class 残留
    if (!list) return;
    if (_selectedFiles.length === 0) {
        list.classList.remove('has-files');
        list.innerHTML = '';
        return;
    }
    list.classList.add('has-files');

    const total = _selectedFiles.length;
    const processing = _selectedFiles.filter(
        (f) => f.status === 'processing' || f.status === 'retrying'
    ).length;
    const success = _selectedFiles.filter((f) => f.status === 'success').length;
    const error = _selectedFiles.filter((f) => f.status === 'error').length;

    let progressText = `<span class="count">${escapeHtml(t('file-list-total', { n: total }))}</span>`;
    const parts = [];
    if (processing)
        parts.push(
            `<span style="color: var(--accent, #111111);">${processing} ${escapeHtml(t('status-processing'))}</span>`
        );
    if (success)
        parts.push(
            `<span style="color: var(--success, #059669);">${success} ${escapeHtml(t('status-success'))}</span>`
        );
    if (error)
        parts.push(
            `<span style="color: var(--danger, #dc2626);">${error} ${escapeHtml(t('status-error'))}</span>`
        );
    if (parts.length) progressText += ' · ' + parts.join(' · ');

    const toggleLabel = _fileListExpanded ? t('file-list-collapse') : t('file-list-expand');

    const itemsHtml = _selectedFiles
        .map((f, idx) => {
            let statusText = t('status-' + f.status);
            if (f.status === 'retrying') statusText = t('status-retrying');
            if (f.status === 'error' && f.errorKey) {
                statusText = t(f.errorKey as string, f.errorParams || {});
            }
            const spinner =
                f.status === 'processing' || f.status === 'retrying'
                    ? '<span class="spinner"></span>'
                    : '';
            // v92 · Bug 7 · 失败文件显示重试按钮
            const retryBtn =
                f.status === 'error' && f.canRetry
                    ? `<button class="file-retry-btn" data-retry-idx="${idx}" title="${escapeHtml(t('upload-retry-btn'))}">${svgIcon('refresh', 12)}<span>${escapeHtml(t('upload-retry-btn'))}</span></button>`
                    : '';
            // v92 · Bug 8 · 缓存命中标签
            const cacheBadge =
                f.status === 'success' && f.fromCache
                    ? `<span class="file-cache-badge">${svgIcon('cache', 11)}<span>${escapeHtml(t('cache-hit-badge'))}</span></span>`
                    : '';
            return `
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</span>
                ${cacheBadge}
                <span class="file-status ${f.status}">${spinner}${statusText}</span>
                ${retryBtn}
            </li>
        `;
        })
        .join('');

    list.innerHTML = `
        <div class="file-list-head">
            <div>${progressText}</div>
            ${total > 5 ? `<button class="toggle" id="file-list-toggle">${escapeHtml(toggleLabel)}</button>` : ''}
        </div>
        <ul class="file-list-body${_fileListExpanded ? ' expanded' : ''}" id="file-list-body">
            ${itemsHtml}
        </ul>
    `;

    const toggleBtn = document.getElementById('file-list-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            _fileListExpanded = !_fileListExpanded;
            renderFileList();
        });
    }

    // v92 · Bug 7 · 重试按钮事件委托
    const body = document.getElementById('file-list-body');
    if (body && !body.dataset.retryBound) {
        body.dataset.retryBound = '1';
        body.addEventListener('click', async (e) => {
            const btn = (e.target as HTMLElement).closest('.file-retry-btn') as HTMLElement;
            if (!btn) return;
            const idx = parseInt(btn.dataset.retryIdx || '-1', 10);
            if (idx < 0 || idx >= _selectedFiles.length) return;
            const f = _selectedFiles[idx];
            if (!f || f.status !== 'error') return;
            // 手动重试 · 不走自动重试逻辑(传 isAutoRetry = true 阻止二次自动重试)
            if (typeof window._reprocessFile === 'function') {
                await window._reprocessFile(f, true);
            }
        });
    }
}

function updateStartButton() {
    const btnStart = document.getElementById('btn-start') as HTMLButtonElement;
    const btnClear = document.getElementById('btn-clear') as HTMLButtonElement;
    const btnExport = document.getElementById('btn-export') as HTMLButtonElement;
    const hasWaiting = _selectedFiles.some((f) => f.status === 'waiting');
    btnStart.disabled = _selectedFiles.length === 0 || !hasWaiting;
    btnClear.disabled = _selectedFiles.length === 0 && _results.length === 0;
    btnExport.disabled = _results.length === 0;
}

// 清空
document.getElementById('btn-clear')!.addEventListener('click', () => {
    _selectedFiles = [];
    _results = [];
    renderFileList();
    renderResults();
    updateStartButton();
    hideAlerts();
});

// 桥回 home.js + 兄弟模块
window.renderFileList = renderFileList;
window.updateStartButton = updateStartButton;
