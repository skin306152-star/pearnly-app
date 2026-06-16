// 商户采购 · 复核屏左栏(票图查看器 + 多文件相册 + 凭据卡)。从 purchase-form 抽出保 <500。
// 查看器:拖拽平移 + 滚轮缩放 + 旋转/复位 + 实时百分比(原生 transform,不自造图片编辑器)。
// 多文件 1/N:billUrls 相册(翻页 + 缩略图 + 加附件);鉴权 serving url 取 blob 显示,本地 blob 直接用。
/* global t, escapeHtml */
import { fetchAuthedBlobUrl } from './purchase-common.js';
import type { FormState } from './purchase-form-types.js';

const ICON_DOC =
    '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/></svg>';
const I_PLUS =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 5v14M5 12h14"/></svg>';
const I_MINUS =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12h14"/></svg>';
const I_ROT =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a9 9 0 11-2.6-6.4"/><path d="M21 4v4h-4"/></svg>';
const I_RESET =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 4H4v4M16 4h4v4M16 20h4v-4M8 20H4v-4"/></svg>';
const I_FULL =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>';

// 左栏 = 票据查看器(下挂相册缩略图条 · 真图小样翻页)+ 凭据卡(替代收据)。查看器 id 保持原样供 mountViewer 复用。
export function leftColHtml(st: FormState): string {
    const n = st.billUrls.length;
    const fileTag =
        n > 1
            ? `<span class="vfile">${escapeHtml(t('pur-file'))} ${st.billIdx + 1} / ${n}</span>`
            : '';
    const inner = n
        ? `<img id="pur-vimg" class="vimg" alt="${escapeHtml(t('pur-bill'))}"/>`
        : `<div class="vph">${ICON_DOC}</div>`;
    const thumbs = st.billUrls
        .map(
            (_, i) =>
                `<div class="t ${i === st.billIdx ? 'on' : ''}" data-thumb="${i}"><img class="timg" data-tidx="${i}" alt=""></div>`
        )
        .join('');
    return `<aside class="preview-pane" id="pane-doc">
        <div class="card"><div class="hd">${escapeHtml(t('pur-bill'))}</div><div class="bd">
            <div class="viewer" id="pur-viewer">${inner}
                <span class="vhint">${escapeHtml(t('pur-viewer-hint'))}</span>${fileTag}
                <div class="vtools"><span class="vzoom" id="pur-vzoom">100%</span><button data-z="in" title="+">${I_PLUS}</button><button data-z="out" title="-">${I_MINUS}</button><button data-z="rot" title="rotate">${I_ROT}</button><button data-z="reset" title="reset">${I_RESET}</button><button data-z="full" title="${escapeHtml(t('pur-viewer-full'))}">${I_FULL}</button></div>
            </div>
            <div class="thumbs">${thumbs}<div class="add" id="pur-add-file">${I_PLUS}</div></div>
        </div></div>
        <div class="card"><div class="hd">${escapeHtml(t('pur-vouchers-hd'))}</div><div class="bd">
            <div class="hint">${escapeHtml(t('pur-sub-receipt-hint'))}</div>
            <button class="btn full ghost mt" id="pur-gen-receipt">+ ${escapeHtml(t('pur-gen-receipt'))}</button>
        </div></div>
        <input type="file" id="pur-addfile-input" accept="image/*,application/pdf" multiple style="display:none">
    </aside>`;
}

let cleanup: (() => void) | null = null;

// 挂载当前相册页 + 拖拽/缩放/旋转控制 + 缩略图切换 + 加文件。refresh 用于切页/加文件后重渲左栏。
export async function mountViewer(st: FormState, refresh: () => void): Promise<void> {
    if (cleanup) {
        cleanup();
        cleanup = null;
    }
    await loadCurrent(st);
    wireZoomPan();
    document.querySelectorAll<HTMLElement>('#pane-doc [data-thumb]').forEach((el) => {
        el.onclick = () => {
            st.billIdx = Number(el.dataset.thumb);
            refresh();
        };
    });
    const addBtn = document.getElementById('pur-add-file');
    const addInput = document.getElementById('pur-addfile-input') as HTMLInputElement | null;
    if (addBtn && addInput) addBtn.onclick = () => addInput.click();
    if (addInput)
        addInput.onchange = () => {
            const files = addInput.files ? Array.from(addInput.files) : [];
            addInput.value = '';
            files.forEach((f) => st.billUrls.push(URL.createObjectURL(f)));
            if (files.length) st.billIdx = st.billUrls.length - 1;
            refresh();
        };
    loadThumbs(st);
}

// 鉴权 serving url → blob object URL · 按 url 缓存(查看器与缩略图共用同一张图 · 去重取图 · 切页不重拉)。
const blobCache = new Map<string, string>();
async function resolveSrc(url: string): Promise<string | null> {
    if (url.startsWith('blob:') || url.startsWith('data:')) return url;
    const cached = blobCache.get(url);
    if (cached) return cached;
    try {
        const src = await fetchAuthedBlobUrl(url);
        blobCache.set(url, src);
        return src;
    } catch (_) {
        return null;
    }
}

async function loadCurrent(st: FormState): Promise<void> {
    const img = document.getElementById('pur-vimg') as HTMLImageElement | null;
    const url = st.billUrls[st.billIdx];
    if (!img || !url) return;
    const src = await resolveSrc(url);
    if (src) img.src = src;
}

// 缩略图条逐张换真图小样(占位 <img> 取回鉴权 blob · 失败留 .t 底色)。
async function loadThumbs(st: FormState): Promise<void> {
    const imgs = document.querySelectorAll<HTMLImageElement>('#pane-doc .thumbs .t img[data-tidx]');
    await Promise.all(
        Array.from(imgs).map(async (img) => {
            const url = st.billUrls[Number(img.dataset.tidx)];
            if (!url) return;
            const src = await resolveSrc(url);
            if (src) img.src = src;
        })
    );
}

function wireZoomPan(): void {
    const vp = document.getElementById('pur-viewer');
    const img = document.getElementById('pur-vimg') as HTMLImageElement | null;
    const zl = document.getElementById('pur-vzoom');
    if (!vp || !img) return;
    let scale = 1,
        tx = 0,
        ty = 0,
        rot = 0,
        drag = false,
        sx = 0,
        sy = 0;
    const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
    const apply = () => {
        img.style.transform = `translate(calc(-50% + ${tx}px), calc(-50% + ${ty}px)) scale(${scale}) rotate(${rot}deg)`;
        if (zl) zl.textContent = Math.round(scale * 100) + '%';
    };
    const onWheel = (e: WheelEvent) => {
        e.preventDefault();
        scale = clamp(scale * (e.deltaY < 0 ? 1.12 : 0.89), 0.4, 6);
        apply();
    };
    const onDown = (e: MouseEvent) => {
        drag = true;
        sx = e.clientX - tx;
        sy = e.clientY - ty;
        vp.classList.add('grabbing');
    };
    const onMove = (e: MouseEvent) => {
        if (!drag) return;
        tx = e.clientX - sx;
        ty = e.clientY - sy;
        apply();
    };
    const onUp = () => {
        drag = false;
        vp.classList.remove('grabbing');
    };
    // 触摸:单指平移 + 双指 pinch 缩放(手机真机·原生 transform 不会自动缩放 <img>,须自处理)。
    let pinchDist = 0;
    let pinchScale = 1;
    const dist2 = (t: TouchList) =>
        Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
    const onTStart = (e: TouchEvent) => {
        if (e.touches.length === 2) {
            pinchDist = dist2(e.touches);
            pinchScale = scale;
        } else if (e.touches.length === 1) {
            drag = true;
            sx = e.touches[0].clientX - tx;
            sy = e.touches[0].clientY - ty;
        }
    };
    const onTMove = (e: TouchEvent) => {
        if (e.touches.length === 2) {
            e.preventDefault();
            scale = clamp(pinchScale * (dist2(e.touches) / (pinchDist || 1)), 0.4, 6);
            apply();
        } else if (drag && e.touches.length === 1) {
            e.preventDefault();
            tx = e.touches[0].clientX - sx;
            ty = e.touches[0].clientY - sy;
            apply();
        }
    };
    const onTEnd = () => {
        drag = false;
        pinchDist = 0;
    };
    vp.addEventListener('wheel', onWheel, { passive: false });
    vp.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    vp.addEventListener('touchstart', onTStart, { passive: false });
    vp.addEventListener('touchmove', onTMove, { passive: false });
    vp.addEventListener('touchend', onTEnd);
    vp.querySelectorAll<HTMLElement>('.vtools button').forEach((b) => {
        b.onclick = (e) => {
            e.stopPropagation();
            const z = b.dataset.z;
            if (z === 'in') scale = clamp(scale * 1.2, 0.4, 6);
            if (z === 'out') scale = clamp(scale / 1.2, 0.4, 6);
            if (z === 'rot') rot += 90;
            if (z === 'reset') {
                scale = 1;
                tx = 0;
                ty = 0;
                rot = 0;
            }
            if (z === 'full') {
                if (document.fullscreenElement) document.exitFullscreen?.();
                else vp.requestFullscreen?.();
                return;
            }
            apply();
        };
    });
    img.style.transformOrigin = 'center';
    apply();
    cleanup = () => {
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
    };
}
