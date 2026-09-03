// POS 项目 · PO-A4 入库弹窗扫码 · 摄像头面板(开/停/重试 + 取景框)
//
// 与 inventory-scan.ts 分家:那边是「码 → 行」,这边是「画面 → 码」,两件事各自够一屏。
// 相机句柄只在这里存一份 —— 两处各存一份就会出现「关了弹窗灯还亮着」。共享地基
// (window.PearnlyScanCamera)只回调,弹窗长什么样归调用方,故本文件只画 stage 那一块。
/* global t, escapeHtml */
import { blockedText, errorHtml, frameBox, paintNote, scanPart } from './inventory-scan-ui.js';
import {
    mountScanCameraControls,
    type ScanCameraControls,
    type ScanCameraControlsHandle,
} from './scan-success-visual.js';
import type { ScanError } from './inventory-scan-ui.js';

interface CameraHandle extends ScanCameraControlsHandle {
    start: () => Promise<boolean>;
    retry: () => Promise<boolean>;
    destroy: () => void;
    reject: (code: string) => void;
    cropRatio: () => { width: number; height: number };
}
interface CameraApi {
    unsupportedReason: () => string | null;
    ensureLoaded: () => Promise<CameraApi>;
    armFeedback?: () => boolean;
    create?: (opts: {
        container?: HTMLElement;
        t?: (key: string) => string;
        onScan?: (code: string) => void;
        onError?: (err: ScanError) => void;
        onState?: (state: string) => void;
        onDuplicate?: (code: string, info: { gapMs: number; misses: number }) => void;
    }) => CameraHandle;
}

/** 面板挂在哪张弹窗上 + 解出来的码交给谁。 */
export interface CamHost {
    maskId: string;
    /** 等解码器那几秒里弹窗可能已被关掉/重开 —— 回 false 就别再往旧那张脸上画。 */
    alive: () => boolean;
    onCode: (code: string) => void;
    /**
     * 引擎把这一次当成「同一件还在画面里」挡下了(static/scan/scan-camera.js 的 onDuplicate)。
     * 那道地板 ≈1.6s 降不下来:1.2 秒的真空档与 1.2 秒的反光在解码结果上同形。所以地板以下
     * 的第二箱只能问店员 —— 一声不吭就是「扫了没反应」,而收货单上少一箱谁也看不出来。
     */
    onDup: (code: string) => void;
}

let cam: CameraHandle | null = null;
let controls: ScanCameraControls | null = null;

function shell(): CameraApi | null {
    const w = window as unknown as { PearnlyScanCamera?: CameraApi };
    const api = w.PearnlyScanCamera;
    return api && typeof api.unsupportedReason === 'function' ? api : null;
}

// 首屏 bundle 里的 loader 缺席也算「这台机器扫不了」· 不静默当没这功能。
export function cameraBlockedReason(): string | null {
    const api = shell();
    return api ? api.unsupportedReason() : 'no_camera_api';
}

export function cameraRunning(): boolean {
    return !!cam;
}

// 相机的话都是瞬时行:它盖不掉「这几个码没落地」那条待办队列(那是别的货的事)。
function msg(host: CamHost, tone: string, html: string): void {
    paintNote(scanPart(host.maskId, 'msg'), tone, html);
}

function setLabel(host: CamHost, running: boolean): void {
    const label = scanPart(host.maskId, 'camlabel');
    if (label) label.textContent = t(running ? 'inv-scan-cam-stop' : 'inv-scan-cam');
}

function paintFrame(stage: HTMLElement, crop: { width: number; height: number }): HTMLElement {
    const box = frameBox(crop);
    const frame = document.createElement('div');
    frame.className = 'inv-scan-frame';
    frame.style.width = box.width + '%';
    frame.style.height = box.height + '%';
    frame.style.left = box.left + '%';
    frame.style.top = box.top + '%';
    stage.appendChild(frame);
    return frame;
}

function onState(host: CamHost, state: string): void {
    if (state === 'starting') msg(host, 'busy', escapeHtml(t('inv-scan-opening')));
    else if (state === 'scanning') {
        msg(host, 'tip', escapeHtml(t('inv-scan-aim')));
        controls?.refreshTorch();
    }
}

function decoderError(): ScanError {
    // 解码器没拉下来(泰国移动网络上几百 KB 可能就是拉不动)· 下一次可能就好了
    return {
        code: 'decoder_unavailable',
        messageKey: 'bscan.err.decoder',
        retryable: true,
        detail: '',
    };
}

export async function openCamera(host: CamHost): Promise<void> {
    const blocked = cameraBlockedReason();
    const api = shell();
    if (blocked || !api) {
        msg(host, 'warn', blockedText(blocked || 'no_camera_api'));
        return;
    }
    if (api.armFeedback) api.armFeedback();
    const btn = scanPart(host.maskId, 'cam') as HTMLButtonElement | null;
    msg(host, 'busy', escapeHtml(t('inv-scan-opening')));
    if (btn) btn.disabled = true;
    let loaded: CameraApi;
    try {
        loaded = await api.ensureLoaded();
    } catch (_) {
        if (btn) btn.disabled = false;
        msg(host, 'err', errorHtml(decoderError()));
        return;
    }
    if (btn) btn.disabled = false;
    const stage = scanPart(host.maskId, 'stage');
    if (!host.alive() || !stage || !loaded.create) return;
    stage.hidden = false;
    const handle = loaded.create({
        container: stage,
        t,
        onScan: host.onCode,
        onError: (err) => msg(host, 'err', errorHtml(err)),
        onState: (state) => onState(host, state),
        onDuplicate: (code) => host.onDup(code),
    });
    cam = handle;
    const frame = paintFrame(stage, handle.cropRatio());
    controls?.destroy();
    controls = mountScanCameraControls(stage, handle, frame);
    setLabel(host, true);
    void handle.start();
}

export function stopCamera(host: CamHost): void {
    releaseCamera();
    const stage = scanPart(host.maskId, 'stage');
    if (stage) {
        stage.innerHTML = '';
        stage.hidden = true;
    }
    setLabel(host, false);
    msg(host, '', '');
}

export function retryCamera(host: CamHost): void {
    if (cam) void cam.retry();
    else void openCamera(host);
}

export function rejectCameraCode(code: string): void {
    if (cam) cam.reject(code);
}

/** 只放硬件,不动 DOM:关弹窗时整块 DOM 本来就要被清掉,但相机灯必须当场灭。 */
export function releaseCamera(): void {
    if (cam) cam.destroy();
    cam = null;
    controls?.destroy();
    controls = null;
}
