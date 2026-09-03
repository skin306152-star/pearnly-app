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
    mountControls(options: {
        container: HTMLElement;
        camera: ScanCameraControlsHandle;
        t: (key: string) => string;
    }): ScanCameraControls | null;
}

export interface ScanCameraControlsHandle {
    cameraControl(name: string, value?: boolean): boolean | Promise<boolean>;
}

export interface ScanCameraControls {
    refreshTorch(): boolean;
    destroy(): void;
}

function visualApi(): ScanSuccessVisualApi | null {
    const api = (window as unknown as { PearnlyScanSuccessVisual?: ScanSuccessVisualApi })
        .PearnlyScanSuccessVisual;
    return api && typeof api.show === 'function' ? api : null;
}

export function showScanSuccessVisual(
    options: Omit<ScanSuccessVisualOptions, 'loadImage'>
): boolean {
    const api = visualApi();
    if (!api) return false;
    return api.show({ ...options, loadImage: loadAuthedImg });
}

export function mountScanCameraControls(
    container: HTMLElement,
    camera: ScanCameraControlsHandle
): ScanCameraControls | null {
    const api = visualApi();
    if (!api || typeof api.mountControls !== 'function') return null;
    return api.mountControls({ container, camera, t: (key) => t(key) });
}
