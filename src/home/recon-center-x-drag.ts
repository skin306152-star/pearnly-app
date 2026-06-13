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
        card.classList.add('rcx-drag');
    });
    grid.addEventListener('dragleave', (e) => {
        const card = findCard(e.target);
        if (card) card.classList.remove('rcx-drag');
    });
    grid.addEventListener('drop', (e) => {
        const card = findCard(e.target);
        if (!card) return;
        e.preventDefault();
        card.classList.remove('rcx-drag');
        const side = card.dataset.side as RxSide;
        const dt = (e as DragEvent).dataTransfer;
        if (dt && dt.files && dt.files.length) onFiles(side, dt.files);
    });
}
