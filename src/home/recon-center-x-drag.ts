// 对账中心重设计 · 上传卡拖拽(容器级委托 · 卡片 innerHTML 重渲后仍生效)。
import type { RxSide } from './recon-center-x-store.js';

export function bindGridDrop(onFiles: (side: RxSide, files: FileList) => void) {
    const grid = document.querySelector('.rcx-upload-grid');
    if (!grid) return;
    const findCard = (t: EventTarget | null) =>
        (t as HTMLElement)?.closest?.('.rcx-upload-card') as HTMLElement | null;
    grid.addEventListener('dragover', (e) => {
        const card = findCard(e.target);
        if (!card) return;
        e.preventDefault();
        card.classList.add('drag-over');
    });
    grid.addEventListener('dragleave', (e) => {
        const card = findCard(e.target);
        if (card) card.classList.remove('drag-over');
    });
    grid.addEventListener('drop', (e) => {
        const card = findCard(e.target);
        if (!card) return;
        e.preventDefault();
        card.classList.remove('drag-over');
        const side = card.dataset.side as RxSide;
        const dt = (e as DragEvent).dataTransfer;
        if (dt && dt.files && dt.files.length) onFiles(side, dt.files);
    });
    // 整框可点:点空态卡内任意处(非按钮)→ 触发该侧文件选择(change 由 root 委托接走)
    grid.addEventListener('click', (e) => {
        const card = findCard(e.target);
        if (!card || card.classList.contains('rcx-loaded')) return;
        if ((e.target as HTMLElement).closest('button')) return;
        const input = document.querySelector(
            `[data-rcx-input="${card.dataset.side}"]`
        ) as HTMLInputElement | null;
        input?.click();
    });
}
