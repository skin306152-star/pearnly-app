// ============================================================
// REFACTOR-C1-home-batch5 (2026-05-31) · 上传【相机/相册→PDF】从 home.js 抽出为独立 ES module
//
// 来源:home.js verbatim 0 改逻辑 · initUploadEntries IIFE / handleDirectPdfFiles /
//   showCameraTips / analyzeImageQuality / _cameraBuffer / handleCameraImages /
//   flushImagesAsOnePdf / renderCameraBufferBar / flushImagesAsSeparatePdfs /
//   imagesToPdf / _readImage / imageFileToPdf。
// 桥回:window.handleCameraImages(upload-files.js 的 handleFiles 把图片路由到这里)。
// 调出:renderFileList/updateStartButton(upload-files.js 经 window)· _selectedFiles 等 home.js 全局 bare。
// ============================================================
import { analyzeImageQuality, imagesToPdf } from './camera-image-utils.js'; // REFACTOR-WB-modularize · 图片工具拆出
/* global _selectedFiles:writable, renderFileList, updateStartButton, getMaxFiles, showAlert, hideAlerts, escapeHtml */

// v113 · 上传入口:拍摄(原生相机) + 上传图片(相册/本地 PDF)
// v113 · 删除 scanner.js · 整套浏览器内 OpenCV 实时检测移除
(function initUploadEntries() {
    const altRow = document.getElementById('upload-alt-row');
    const galInput = document.getElementById('gallery-input');
    const camInput = document.getElementById('camera-input');
    if (!altRow) return;

    // 移动端 + 桌面都显示
    altRow.style.display = '';

    // v113 · 拍摄票据 · 调原生相机 · 进 _cameraBuffer 流程
    const btnScanDoc = document.getElementById('btn-scan-doc');
    if (btnScanDoc && camInput) {
        btnScanDoc.addEventListener('click', async () => {
            // 显示拍摄贴士(用户可勾"不再提示"绕过)
            const skipTips = localStorage.getItem('mrpilot_camera_tips_skip') === '1';
            if (!skipTips) {
                const ok = await showCameraTips();
                if (!ok) return;
            }
            // 触发原生相机
            camInput.click();
        });
        // 拍照 input change · 每次返回 1 张 · 进 buffer
        camInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files || []);
            e.target.value = '';
            if (files.length === 0) return;
            for (const f of files) {
                await handleCameraImages([f], 'camera');
            }
        });
    }

    // v113 · 上传图片 · 走相册 · 多选 · 直接合并入流程
    const btnUploadPic = document.getElementById('btn-upload-pic');
    if (btnUploadPic && galInput) {
        btnUploadPic.addEventListener('click', () => galInput.click());
    }

    const onPick = (source) => async (e) => {
        const files = Array.from(e.target.files || []);
        e.target.value = '';
        if (files.length === 0) return;
        // v113 · 选图可能混 PDF · 拆开走两条路
        const pdfs = files.filter((f) => f.type === 'application/pdf' || /\.pdf$/i.test(f.name));
        const imgs = files.filter((f) => !pdfs.includes(f));
        if (pdfs.length > 0) await handleDirectPdfFiles(pdfs);
        if (imgs.length > 0) await handleCameraImages(imgs, source);
    };
    galInput && galInput.addEventListener('change', onPick('gallery'));
})();

// v113 · 用户从相册选了 PDF · 直接进 _selectedFiles · 不需要转换
async function handleDirectPdfFiles(pdfFiles) {
    for (const f of pdfFiles) {
        _selectedFiles.push({
            file: f,
            name: f.name,
            size: f.size,
            status: 'waiting',
            errorKey: null,
            errorParams: null,
        });
    }
    const maxFiles = getMaxFiles();
    if (_selectedFiles.length > maxFiles) {
        showAlert('warn', t('alert-file-count', { n: maxFiles }));
        _selectedFiles = _selectedFiles.slice(0, maxFiles);
    }
    renderFileList();
    updateStartButton();
}

// v0.17 · 拍照贴士弹窗 · 返回 Promise<bool>
function showCameraTips() {
    return new Promise((resolve) => {
        const overlay = document.getElementById('camera-tips-modal');
        const btnOk = document.getElementById('camera-tips-ok');
        const btnCancel = document.getElementById('camera-tips-cancel');
        const chkSkip = document.getElementById('camera-tips-skip');
        if (!overlay || !btnOk) {
            resolve(true);
            return;
        }
        // 默认不勾选"不再提示"
        if (chkSkip) chkSkip.checked = false;
        overlay.style.display = 'flex';
        const cleanup = (go) => {
            overlay.style.display = 'none';
            if (chkSkip && chkSkip.checked) {
                localStorage.setItem('mrpilot_camera_tips_skip', '1');
            }
            btnOk.onclick = null;
            if (btnCancel) btnCancel.onclick = null;
            overlay.onclick = null;
            document.removeEventListener('keydown', onKey);
            resolve(go);
        };
        const onKey = (e) => {
            if (e.key === 'Escape') cleanup(false);
        };
        btnOk.onclick = () => cleanup(true);
        if (btnCancel) btnCancel.onclick = () => cleanup(false);
        overlay.onclick = (e) => {
            if (e.target === overlay) cleanup(false);
        };
        document.addEventListener('keydown', onKey);
        setTimeout(() => btnOk.focus(), 50);
    });
}

// v0.17 · 把拍的图转成 PDF 后塞进现有 _selectedFiles 流程
// v0.17 · M3 · 连拍缓冲区(多张合并成 1 个 PDF)
// v118.27.8.1.14e · 缓冲区现在也接相册多选 · 让用户在浮条上自己选合并 vs 分别
let _cameraBuffer = []; // { file, quality: {warnings, ...} }
let _cameraBufferSource = null; // 'camera' | 'gallery' · 决定浮条「继续」按钮触发哪个 input

async function handleCameraImages(imageFiles, source) {
    hideAlerts();
    if (!imageFiles || imageFiles.length === 0) return;

    // MR.ERP DMS · 身份证订车模式:后端按图片 OCR · 单张身份证【不转 PDF】直发原图
    // (转 photo_*.pdf 会让 id_card OCR 读不到图 → Layer1Error · DMS-UI-003 2026-06-01)。
    var _docMode =
        typeof window.getOcrDocumentMode === 'function' ? window.getOcrDocumentMode() : 'invoice';
    if (_docMode === 'thai_id_card') {
        for (const f of imageFiles) {
            _selectedFiles.push({
                file: f,
                name: f.name,
                size: f.size,
                status: 'waiting',
                errorKey: null,
                errorParams: null,
            });
        }
        const _maxF = getMaxFiles();
        if (_selectedFiles.length > _maxF) {
            showAlert('warn', t('alert-file-count', { n: _maxF }));
            _selectedFiles = _selectedFiles.slice(0, _maxF);
        }
        renderFileList();
        updateStartButton();
        return;
    }

    // 等 jsPDF 加载
    if (typeof window.jspdf === 'undefined' || !window.jspdf.jsPDF) {
        showToast(t('camera-loading'), 'info');
        for (let i = 0; i < 30; i++) {
            await new Promise((r) => setTimeout(r, 100));
            if (window.jspdf && window.jspdf.jsPDF) break;
        }
        if (!window.jspdf || !window.jspdf.jsPDF) {
            showToast(t('camera-lib-fail'), 'error');
            return;
        }
    }

    // 拍照单张(source='camera' 且 1 张)→ 进缓冲区 · 显示浮条
    if (source === 'camera' && imageFiles.length === 1) {
        const f = imageFiles[0];
        let q = {};
        try {
            q = await analyzeImageQuality(f);
        } catch (e) {}
        _cameraBuffer.push({ file: f, quality: q });
        _cameraBufferSource = 'camera';
        renderCameraBufferBar();
        return;
    }

    // v118.27.8.1.14e · 相册多选 ≥2 张 · 或 buffer 已有图(用户点"继续选"追加)
    // → 进缓冲区 · 浮条让用户选「分别识别(默认)」或「合并为 1 个 PDF」
    // 痛点修复:之前强制合并 · 80%+ 场景用户是想批量传不同发票 · 默认合并是错的
    if (source === 'gallery' && (imageFiles.length >= 2 || _cameraBuffer.length > 0)) {
        for (const f of imageFiles) {
            let q = {};
            try {
                q = await analyzeImageQuality(f);
            } catch (e) {}
            _cameraBuffer.push({ file: f, quality: q });
        }
        _cameraBufferSource = 'gallery';
        renderCameraBufferBar();
        return;
    }

    // 相册单张(且 buffer 为空)→ 直接 1 张 = 1 个独立 PDF · 不打扰
    await flushImagesAsSeparatePdfs(imageFiles);
}

// 把一组图合并成 1 个 PDF · 加入 _selectedFiles
async function flushImagesAsOnePdf(imageFiles) {
    const warningSet = new Set();
    for (const f of imageFiles) {
        try {
            const q = await analyzeImageQuality(f);
            (q.warnings || []).forEach((w) => warningSet.add(w));
        } catch (e) {}
    }
    try {
        const pdfFile = await imagesToPdf(imageFiles);
        if (pdfFile) {
            _selectedFiles.push({
                file: pdfFile,
                name: pdfFile.name,
                size: pdfFile.size,
                status: 'waiting',
                errorKey: null,
                errorParams: null,
            });
        }
    } catch (err) {
        console.error('[camera] convert failed', err);
        showToast(t('camera-convert-fail'), 'error');
        return;
    }

    const maxFiles = getMaxFiles();
    if (_selectedFiles.length > maxFiles) {
        showAlert('warn', t('alert-file-count', { n: maxFiles }));
        _selectedFiles = _selectedFiles.slice(0, maxFiles);
    }

    renderFileList();
    updateStartButton();
    showToast(t('camera-added-merged', { n: imageFiles.length }), 'success');

    if (warningSet.size > 0) {
        setTimeout(() => {
            if (warningSet.has('too_dark')) showToast(t('camera-quality-dark'), 'warn');
            else if (warningSet.has('low_res')) showToast(t('camera-quality-lowres'), 'warn');
            else if (warningSet.has('too_bright'))
                showToast(t('camera-quality-overexposed'), 'warn');
        }, 1000);
    }
}

// 浮条(拍照单张后 · 或相册多选后显示 · 让用户选合并/分别识别/继续添加)
// v118.27.8.1.14e · 按 _cameraBufferSource 决定:
//   camera 来源(拍照)→ 默认合并(常见场景:正反面/多页税单) · 「继续拍」触发 camera-input
//   gallery 来源(相册)→ 默认分别(常见场景:批量传不同发票) · 「继续选」触发 gallery-input
function renderCameraBufferBar() {
    let bar = document.getElementById('camera-buffer-bar');
    if (_cameraBuffer.length === 0) {
        if (bar) bar.remove();
        _cameraBufferSource = null;
        return;
    }
    if (!bar) {
        bar = document.createElement('div');
        bar.id = 'camera-buffer-bar';
        bar.className = 'camera-buffer-bar';
        document.body.appendChild(bar);
    }
    const n = _cameraBuffer.length;
    const showSep = n >= 2;
    const isGallery = _cameraBufferSource === 'gallery';
    const moreLabel = isGallery ? t('camera-buffer-more-gallery') : t('camera-buffer-more');

    // 主/副按钮分配:
    //   单张:仅一个「完成」按钮(合并 = 分别 = 1 个 PDF · 行为一致)
    //   多张相册:主 = 分别识别(默认) · 副 = 合并
    //   多张拍照:主 = 合并完成(默认) · 副 = 分别识别
    let actionsHtml;
    if (!showSep) {
        actionsHtml = `<button type="button" class="btn btn-primary btn-sm" data-cbb-action="merge">${escapeHtml(t('camera-buffer-done'))}</button>`;
    } else if (isGallery) {
        // 相册多选 · 默认分别
        actionsHtml = `
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="merge">${escapeHtml(t('camera-buffer-done-merge'))}</button>
            <button type="button" class="btn btn-primary btn-sm" data-cbb-action="separate">${escapeHtml(t('camera-buffer-done-separate', { n }))}</button>
        `;
    } else {
        // 拍照多张 · 默认合并(保留原行为)
        actionsHtml = `
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="separate">${escapeHtml(t('camera-buffer-done-separate', { n }))}</button>
            <button type="button" class="btn btn-primary btn-sm" data-cbb-action="merge">${escapeHtml(t('camera-buffer-done-merge'))}</button>
        `;
    }

    bar.innerHTML = `
        <div class="cbb-count">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7h4l2-2h6l2 2h4a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V8a1 1 0 011-1z"/>
                <circle cx="12" cy="13" r="4"/>
            </svg>
            <span>${escapeHtml(t('camera-buffer-count', { n }))}</span>
        </div>
        <div class="cbb-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="discard">${escapeHtml(t('camera-buffer-discard'))}</button>
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="more">${escapeHtml(moreLabel)}</button>
            ${actionsHtml}
        </div>
    `;

    bar.querySelector('[data-cbb-action="discard"]').onclick = () => {
        _cameraBuffer = [];
        _cameraBufferSource = null;
        renderCameraBufferBar();
    };
    bar.querySelector('[data-cbb-action="more"]').onclick = () => {
        // 按来源触发对应 input · 桌面端 camera-input 退化成文件选择器一样能用
        const inputId = isGallery ? 'gallery-input' : 'camera-input';
        const input = document.getElementById(inputId);
        if (input) input.click();
    };
    const mergeBtn = bar.querySelector('[data-cbb-action="merge"]');
    if (mergeBtn) {
        mergeBtn.onclick = async () => {
            const files = _cameraBuffer.map((x) => x.file);
            _cameraBuffer = [];
            _cameraBufferSource = null;
            renderCameraBufferBar();
            await flushImagesAsOnePdf(files);
        };
    }
    const sepBtn = bar.querySelector('[data-cbb-action="separate"]');
    if (sepBtn) {
        sepBtn.onclick = async () => {
            const files = _cameraBuffer.map((x) => x.file);
            _cameraBuffer = [];
            _cameraBufferSource = null;
            renderCameraBufferBar();
            await flushImagesAsSeparatePdfs(files);
        };
    }
}

// v118.27.8.1.14e · 注册 i18n 订阅 · 切语言时浮条立刻重渲
if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('camera-buffer-bar', () => {
        if (_cameraBuffer.length > 0) renderCameraBufferBar();
    });
}

// v113 · 把每张图分别转成独立 PDF · 加进 _selectedFiles
async function flushImagesAsSeparatePdfs(imageFiles) {
    const warningSet = new Set();
    let okCount = 0;
    for (const f of imageFiles) {
        try {
            const q = await analyzeImageQuality(f);
            (q.warnings || []).forEach((w) => warningSet.add(w));
            const pdfFile = await imagesToPdf([f]);
            if (pdfFile) {
                _selectedFiles.push({
                    file: pdfFile,
                    name: pdfFile.name,
                    size: pdfFile.size,
                    status: 'waiting',
                    errorKey: null,
                    errorParams: null,
                });
                okCount++;
            }
        } catch (err) {
            console.error('[camera] separate convert failed', err);
        }
    }
    if (okCount === 0) {
        showToast(t('camera-convert-fail'), 'error');
        return;
    }
    const maxFiles = getMaxFiles();
    if (_selectedFiles.length > maxFiles) {
        showAlert('warn', t('alert-file-count', { n: maxFiles }));
        _selectedFiles = _selectedFiles.slice(0, maxFiles);
    }
    renderFileList();
    updateStartButton();
    showToast(t('camera-added-separate', { n: okCount }), 'success');

    if (warningSet.size > 0) {
        setTimeout(() => {
            if (warningSet.has('too_dark')) showToast(t('camera-quality-dark'), 'warn');
            else if (warningSet.has('low_res')) showToast(t('camera-quality-lowres'), 'warn');
            else if (warningSet.has('too_bright'))
                showToast(t('camera-quality-overexposed'), 'warn');
        }, 1000);
    }
}

// 桥回:upload-files.js 的 handleFiles 调
window.handleCameraImages = handleCameraImages;
