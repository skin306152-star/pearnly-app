// ============================================================
// 共用原图查看器 · 录入工作台复核 / 识别记录抽屉 / 异常抽屉 三处复用
//   原图从 /api/history/{id}/page/1.png(PyMuPDF 渲页)取 · 留底 PDF 是识别后异步
//   回填,首次 404 → 轮询重试等就绪(加载中态),非 404 硬错/网络错不空等。
//   交互:拖拽平移 / 滚轮缩放 / 放大缩小 / 旋转 / 重置 / 双击放大。
//   每个实例状态独立(闭包)· mount 返回 cleanup(解绑 window 监听 · 中止在飞重试)。
//   文案由调用方传入(模块不绑 i18n)· 鉴权用 token 全局。
// ============================================================
/* global token, escapeHtml */

const ivCache = new Map<string, string>(); // history_id → objectURL · 跨开关复用不重拉
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

interface ViewerText {
    title?: string;
    help?: string;
    noimg?: string;
    loading?: string;
}

export function imageViewerHtml(o: ViewerText = {}): string {
    const e = (s?: string) => escapeHtml(s || '');
    return (
        '<div class="iv-card"><div class="iv-toolbar">' +
        `<div class="iv-title">${e(o.title)}</div><div class="iv-ctrls">` +
        '<button class="iv-btn" data-iv="out" type="button" title="−">−</button>' +
        '<span class="iv-zoom">100%</span>' +
        '<button class="iv-btn" data-iv="in" type="button" title="+">＋</button>' +
        '<button class="iv-btn" data-iv="rot" type="button" title="↻">↻</button>' +
        '<button class="iv-btn" data-iv="reset" type="button" title="⟲">⟲</button>' +
        '</div></div><div class="iv-viewport">' +
        '<div class="iv-canvas"><img class="iv-img" draggable="false" alt=""></div>' +
        `<div class="iv-empty">${e(o.noimg)}</div>` +
        `<div class="iv-loading"><span class="iv-spin"></span>${e(o.loading)}</div>` +
        (o.help ? `<div class="iv-help">${e(o.help)}</div>` : '') +
        '</div></div>'
    );
}

export function mountImageViewer(card: HTMLElement, historyId: string | null): () => void {
    const vp = card.querySelector('.iv-viewport') as HTMLElement | null;
    const canvas = card.querySelector('.iv-canvas') as HTMLElement | null;
    const img = card.querySelector('.iv-img') as HTMLImageElement | null;
    const label = card.querySelector('.iv-zoom') as HTMLElement | null;
    if (!vp || !canvas || !img) return () => {};

    const st = { x: 0, y: 0, scale: 1, rot: 0 };
    const apply = () => {
        canvas.style.transform = `translate(calc(-50% + ${st.x}px), calc(-50% + ${st.y}px)) scale(${st.scale}) rotate(${st.rot}deg)`;
        if (label) label.textContent = Math.round(st.scale * 100) + '%';
    };
    apply();

    const onClick = (e: Event) => {
        const b = (e.target as HTMLElement).closest('[data-iv]') as HTMLElement | null;
        if (!b) return;
        const a = b.dataset.iv;
        if (a === 'in') st.scale = clamp(st.scale + 0.15, 0.4, 3.4);
        else if (a === 'out') st.scale = clamp(st.scale - 0.15, 0.4, 3.4);
        else if (a === 'rot') st.rot = (st.rot + 90) % 360;
        else if (a === 'reset') Object.assign(st, { x: 0, y: 0, scale: 1, rot: 0 });
        apply();
    };
    card.addEventListener('click', onClick);

    let drag = false;
    let sx = 0;
    let sy = 0;
    let ox = 0;
    let oy = 0;
    const down = (e: MouseEvent) => {
        drag = true;
        sx = e.clientX;
        sy = e.clientY;
        ox = st.x;
        oy = st.y;
        vp.classList.add('dragging');
    };
    const move = (e: MouseEvent) => {
        if (!drag) return;
        st.x = ox + (e.clientX - sx);
        st.y = oy + (e.clientY - sy);
        apply();
    };
    const up = () => {
        drag = false;
        vp.classList.remove('dragging');
    };
    const wheel = (e: WheelEvent) => {
        e.preventDefault();
        st.scale = clamp(st.scale + (e.deltaY < 0 ? 0.1 : -0.1), 0.4, 3.4);
        apply();
    };
    const dbl = () => {
        Object.assign(st, { x: 0, y: 0, scale: 1.6, rot: 0 });
        apply();
    };
    vp.addEventListener('mousedown', down);
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
    vp.addEventListener('wheel', wheel, { passive: false });
    vp.addEventListener('dblclick', dbl);

    let alive = true;
    void loadImage(card, img, historyId, () => alive);

    return () => {
        alive = false;
        card.removeEventListener('click', onClick);
        vp.removeEventListener('mousedown', down);
        window.removeEventListener('mousemove', move);
        window.removeEventListener('mouseup', up);
        vp.removeEventListener('wheel', wheel);
        vp.removeEventListener('dblclick', dbl);
    };
}

async function loadImage(
    card: HTMLElement,
    img: HTMLImageElement,
    historyId: string | null,
    alive: () => boolean
) {
    if (!historyId) {
        card.classList.add('noimg');
        return;
    }
    const cached = ivCache.get(historyId);
    if (cached) {
        img.src = cached;
        return;
    }
    card.classList.add('loading');
    for (let i = 0; i < 8 && alive(); i++) {
        if (!card.isConnected) return;
        try {
            const r = await fetch(`/api/history/${encodeURIComponent(historyId)}/page/1.png`, {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (r.ok) {
                const u = URL.createObjectURL(await r.blob());
                ivCache.set(historyId, u);
                if (!alive()) return;
                card.classList.remove('loading');
                img.src = u;
                return;
            }
            if (r.status !== 404) break; // 渲染失败等硬错 → 不再等
        } catch {
            break; // 网络错 → 停
        }
        await new Promise((res) => setTimeout(res, 1200));
    }
    if (alive()) {
        card.classList.remove('loading');
        card.classList.add('noimg');
    }
}
