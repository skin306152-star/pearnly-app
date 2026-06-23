// ============================================================
// 共用原图查看器 · 识别记录抽屉 / 异常抽屉 复用 —— 以采购「复核单据」票图查看器为标准
//   (purchase-form-bill.ts wireZoomPan 同款:拖拽平移 + 滚轮缩放 + 触摸 pinch + 旋转/复位/
//   全屏 + 实时百分比 · 原生 transform 作用在 <img>)。CSS 见 home-52-image-viewer.css(.pv-*)。
//   图源 = /api/history/{id}/page/{n}.png(PyMuPDF 渲页)· X-Page-Count 给总页数 →
//   一份多页 PDF(装多张发票)可翻页看每页。留底 PDF 异步回填 → 首次 404 轮询重试等就绪
//   (加载中态),非 404 硬错/网络错不空等。容器高度各调用方按界面定。
//   每实例状态独立(闭包)· mount 返回 cleanup(解绑 window 监听 · 中止在飞重试)。
//   文案由调用方传入(模块不绑 i18n)· 鉴权用 token 全局。
// ============================================================
/* global token, escapeHtml */

// history_id → objectURL · 跨开关复用不重拉 · LRU 封顶,淘汰即 revoke(防 blob 无限驻留)
const ivCache = new Map<string, string>();
const IV_MAX = 20;
function ivPut(id: string, url: string): void {
    ivCache.set(id, url);
    if (ivCache.size > IV_MAX) {
        const oldest = ivCache.keys().next().value as string;
        const u = ivCache.get(oldest);
        ivCache.delete(oldest);
        if (u) URL.revokeObjectURL(u);
    }
}

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

interface ViewerText {
    hint?: string;
    noimg?: string;
    loading?: string;
}

export function imageViewerHtml(o: ViewerText = {}): string {
    const e = (s?: string) => escapeHtml(s || '');
    return (
        '<div class="pv-viewer"><img class="pv-img" alt="">' +
        (o.hint ? `<span class="pv-hint">${e(o.hint)}</span>` : '') +
        `<div class="pv-empty">${e(o.noimg)}</div>` +
        `<div class="pv-loading"><span class="pv-spin"></span>${e(o.loading)}</div>` +
        '<div class="pv-tools">' +
        '<span class="pv-pager"><button data-z="prev" type="button" title="prev">‹</button>' +
        '<span class="pv-pgnum">1/1</span>' +
        '<button data-z="next" type="button" title="next">›</button></span>' +
        '<span class="pv-zoom">100%</span>' +
        `<button data-z="in" type="button" title="+">${I_PLUS}</button>` +
        `<button data-z="out" type="button" title="-">${I_MINUS}</button>` +
        `<button data-z="rot" type="button" title="rotate">${I_ROT}</button>` +
        `<button data-z="reset" type="button" title="reset">${I_RESET}</button>` +
        `<button data-z="full" type="button" title="full">${I_FULL}</button></div></div>`
    );
}

// 挂到一个含 .pv-viewer 的根元素 · 载入 page.png(重试)+ 接拖拽/缩放/旋转/全屏。返回 cleanup。
export function mountImageViewer(root: HTMLElement, historyId: string | null): () => void {
    const vp = root.querySelector('.pv-viewer') as HTMLElement | null;
    const img = root.querySelector('.pv-img') as HTMLImageElement | null;
    const zl = root.querySelector('.pv-zoom') as HTMLElement | null;
    if (!vp || !img) return () => {};

    let scale = 1;
    let tx = 0;
    let ty = 0;
    let rot = 0;
    let drag = false;
    let sx = 0;
    let sy = 0;
    let alive = true; // mount 作废后置 false → 停在飞重试 / 翻页加载
    const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
    const apply = () => {
        img.style.transform = `translate(calc(-50% + ${tx}px), calc(-50% + ${ty}px)) scale(${scale}) rotate(${rot}deg)`;
        if (zl) zl.textContent = Math.round(scale * 100) + '%';
    };
    // 多页 PDF(一份装多张发票)翻页:第几页由 page.png 接口渲;总页数从 X-Page-Count 拿。
    const pgEl = root.querySelector('.pv-pgnum');
    let page = 1;
    let total = 1;
    const goPage = (p: number) => {
        page = Math.trunc(clamp(p, 1, total));
        if (pgEl) pgEl.textContent = page + '/' + total; // 立刻更新页码(不等图加载)
        scale = 1; // 翻页即复位变换(每页独立观看)
        tx = 0;
        ty = 0;
        rot = 0;
        apply();
        void loadImage(
            vp,
            img,
            historyId,
            page,
            () => alive,
            (n) => {
                total = n;
                vp.classList.toggle('multi', n > 1);
                if (pgEl) pgEl.textContent = page + '/' + n;
            }
        );
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
    // 触摸:单指平移 + 双指 pinch 缩放(原生 transform 不会自动缩放 <img>,须自处理)。
    let pinchDist = 0;
    let pinchScale = 1;
    const dist2 = (tl: TouchList) =>
        Math.hypot(tl[0].clientX - tl[1].clientX, tl[0].clientY - tl[1].clientY);
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
    const onTools = (e: Event) => {
        const b = (e.target as HTMLElement).closest('.pv-tools button') as HTMLElement | null;
        if (!b) return;
        e.stopPropagation();
        const z = b.dataset.z;
        if (z === 'prev') return goPage(page - 1);
        if (z === 'next') return goPage(page + 1);
        if (z === 'in') scale = clamp(scale * 1.2, 0.4, 6);
        else if (z === 'out') scale = clamp(scale / 1.2, 0.4, 6);
        else if (z === 'rot') rot += 90;
        else if (z === 'reset') {
            scale = 1;
            tx = 0;
            ty = 0;
            rot = 0;
        } else if (z === 'full') {
            if (document.fullscreenElement) void document.exitFullscreen?.();
            else void vp.requestFullscreen?.();
            return;
        }
        apply();
    };
    vp.addEventListener('wheel', onWheel, { passive: false });
    vp.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    vp.addEventListener('touchstart', onTStart, { passive: false });
    vp.addEventListener('touchmove', onTMove, { passive: false });
    vp.addEventListener('touchend', onTEnd);
    vp.addEventListener('click', onTools);
    img.style.transformOrigin = 'center';
    apply();
    goPage(1);

    return () => {
        alive = false;
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
    };
}

// 抽屉重渲/换单常见模式:先清同 key 的旧实例,再挂新的。pane 为空(未渲查看器)= 只清不挂。
const _mounts = new Map<string, () => void>();
export function remountImageViewer(
    key: string,
    pane: HTMLElement | null,
    historyId: string | null
): void {
    _mounts.get(key)?.();
    _mounts.delete(key);
    if (pane && pane.querySelector('.pv-viewer'))
        _mounts.set(key, mountImageViewer(pane, historyId));
}

async function loadImage(
    vp: HTMLElement,
    img: HTMLImageElement,
    historyId: string | null,
    page: number,
    alive: () => boolean,
    onTotal: (n: number) => void
) {
    if (!historyId) {
        vp.classList.add('noimg');
        return;
    }
    vp.classList.remove('noimg');
    const key = historyId + ':' + page; // 按页缓存(一份多页 PDF 翻页不重拉)
    const cached = ivCache.get(key);
    if (cached) {
        img.src = cached;
        return;
    }
    vp.classList.add('loading');
    for (let i = 0; i < 8 && alive(); i++) {
        if (!vp.isConnected) return;
        try {
            const r = await fetch(
                `/api/history/${encodeURIComponent(historyId)}/page/${page}.png`,
                { headers: { Authorization: 'Bearer ' + token } }
            );
            if (r.ok) {
                const u = URL.createObjectURL(await r.blob());
                ivPut(key, u);
                if (!alive()) return;
                vp.classList.remove('loading');
                img.src = u;
                onTotal(parseInt(r.headers.get('X-Page-Count') || '1', 10) || 1);
                return;
            }
            if (r.status !== 404) break; // 渲染失败等硬错 → 不再等
        } catch {
            break; // 网络错 → 停
        }
        await new Promise((res) => setTimeout(res, 1200));
    }
    if (alive()) {
        vp.classList.remove('loading');
        vp.classList.add('noimg');
    }
}
