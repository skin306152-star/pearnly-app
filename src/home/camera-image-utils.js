// ============================================================
// REFACTOR-WB-modularize · 图片处理纯工具(质量分析 + 图→PDF)从 upload-camera.js 拆出为独立 ES module
//
// analyzeImageQuality(亮度/分辨率采样) / imagesToPdf(jsPDF 合成) / _readImage。
// 无业务状态 · 无 home.js 全局依赖(仅浏览器 API + window.jspdf)· upload-camera.js 经 ESM import 调用。
// ============================================================
// v0.17 · 图片质量快速检查:返回 {warnings:[], width, height, brightness}
// 采样:缩到 64×64 算平均亮度(太小误差大 / 太大耗时),用 canvas
async function analyzeImageQuality(imgFile) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onerror = () => resolve({ warnings: [], width: 0, height: 0, brightness: 128 });
        reader.onload = () => {
            const img = new Image();
            img.onerror = () => resolve({ warnings: [], width: 0, height: 0, brightness: 128 });
            img.onload = () => {
                const warnings = [];
                const w = img.naturalWidth,
                    h = img.naturalHeight;
                if (w < 1000 || h < 1000) warnings.push('low_res');
                try {
                    const cv = document.createElement('canvas');
                    cv.width = 64;
                    cv.height = 64;
                    const ctx = cv.getContext('2d');
                    ctx.drawImage(img, 0, 0, 64, 64);
                    const data = ctx.getImageData(0, 0, 64, 64).data;
                    let sum = 0,
                        n = 0;
                    for (let i = 0; i < data.length; i += 4) {
                        // 感知亮度加权(Rec.601 近似)
                        sum += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
                        n++;
                    }
                    const brightness = n ? sum / n : 128;
                    if (brightness < 70) warnings.push('too_dark');
                    else if (brightness > 235) warnings.push('too_bright');
                    resolve({ warnings, width: w, height: h, brightness });
                } catch (e) {
                    resolve({ warnings, width: w, height: h, brightness: 128 });
                }
            };
            img.src = reader.result;
        };
        reader.readAsDataURL(imgFile);
    });
}

// v0.17 · 单张图片 → PDF(自动按图片比例设置页面)
// v0.17 · M3 · 多张图片合并成一个 PDF(每张图独占一页)
// 单张也走这个函数 · 保持向后兼容
async function imagesToPdf(imgFiles) {
    if (!imgFiles || imgFiles.length === 0) return null;
    const { jsPDF } = window.jspdf;
    // A4 尺寸(mm)
    const pageW = 210,
        pageH = 297;
    const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'p' });

    for (let i = 0; i < imgFiles.length; i++) {
        const imgFile = imgFiles[i];
        const { dataUrl, naturalW, naturalH } = await _readImage(imgFile);
        if (i > 0) pdf.addPage('a4', 'p');
        const ratio = naturalW / naturalH;
        let drawW = pageW - 10;
        let drawH = drawW / ratio;
        if (drawH > pageH - 10) {
            drawH = pageH - 10;
            drawW = drawH * ratio;
        }
        const x = (pageW - drawW) / 2;
        const y = (pageH - drawH) / 2;
        const fmt = imgFile.type === 'image/png' ? 'PNG' : 'JPEG';
        pdf.addImage(dataUrl, fmt, x, y, drawW, drawH, undefined, 'FAST');
    }
    const blob = pdf.output('blob');
    const now = new Date();
    const ts =
        now.getFullYear().toString() +
        String(now.getMonth() + 1).padStart(2, '0') +
        String(now.getDate()).padStart(2, '0') +
        String(now.getHours()).padStart(2, '0') +
        String(now.getMinutes()).padStart(2, '0') +
        String(now.getSeconds()).padStart(2, '0');
    const suffix = imgFiles.length > 1 ? `_${imgFiles.length}p` : '';
    return new File([blob], `photo_${ts}${suffix}.pdf`, { type: 'application/pdf' });
}

function _readImage(imgFile) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = reject;
        reader.onload = () => {
            const img = new Image();
            img.onerror = reject;
            img.onload = () =>
                resolve({
                    dataUrl: reader.result,
                    naturalW: img.naturalWidth,
                    naturalH: img.naturalHeight,
                });
            img.src = reader.result;
        };
        reader.readAsDataURL(imgFile);
    });
}
export { analyzeImageQuality, imagesToPdf };
