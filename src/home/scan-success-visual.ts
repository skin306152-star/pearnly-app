import { loadAuthedImg } from './sales-common.js';

interface ScanSuccessVisualOptions {
    label: string;
    imageUrl?: string | null;
    target?: Element | string | Array<Element | string | null> | null;
    increment?: boolean;
    loadImage?: (img: HTMLImageElement, url: string) => Promise<void> | void;
}

interface ScanSuccessVisualApi {
    show(options: ScanSuccessVisualOptions): boolean;
}

export function showScanSuccessVisual(
    options: Omit<ScanSuccessVisualOptions, 'loadImage'>
): boolean {
    const api = (window as unknown as { PearnlyScanSuccessVisual?: ScanSuccessVisualApi })
        .PearnlyScanSuccessVisual;
    if (!api || typeof api.show !== 'function') return false;
    return api.show({ ...options, loadImage: loadAuthedImg });
}
