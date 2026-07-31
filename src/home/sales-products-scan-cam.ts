// 销项 PO-10 · 建品表单条码位的摄像头弹窗(拆自 sales-products-scan.ts · 控行数)
//
// 只管「开一张扫码窗 → 把引擎的四态画成人话 → 扫到就回调」。撞码查重、条码框怎么填,
// 全在 sales-products-scan.ts,这里一概不碰 —— 两边混在一个文件里时,改弹窗文案要顺带
// 读一遍查重状态机。
//
// 引擎(window.PearnlyScanCamera)是共享地基 static/scan/*:首屏只有能力探针,
// 真开相机才 ensureLoaded 懒加载解码器。
/* global t, escapeHtml */
import { IC_X } from './sales-common.js';

export interface ScanError {
    code: string;
    messageKey: string;
    retryable: boolean;
    message?: string;
}
export interface CropRatio {
    width: number;
    height: number;
}
interface CameraHandle {
    start(): Promise<boolean>;
    retry(): Promise<boolean>;
    destroy(): void;
    cropRatio(): CropRatio;
}
interface CameraApi {
    create(opts: Record<string, unknown>): CameraHandle;
}
interface ScanCameraShell {
    unsupportedReason(): string | null;
    ensureLoaded(): Promise<CameraApi>;
}

const MASK_ID = 'sx-bcm';
const FRAME_ID = 'sx-bcm-frame';

// 探针给出的两种「这台设备扫不了」→ 对应两句不同的话。Odoo 在非 HTTPS 下让扫码按钮
// 静默消失,用户只觉得「功能没了」;这里按钮不显示但原因必须写在旁边。
export const NO_CAMERA_KEY: Record<string, string> = {
    insecure_context: 'bscan.err.insecure',
    no_camera_api: 'bscan.err.unsupported',
};

const STYLE = `
/* 扫码弹窗盖在建品弹窗(.modal-mask z-index:10000)之上 */
.sx-bcm{position:fixed;inset:0;z-index:10010;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,.62);}
/* 宽度写法跟 POS 侧扫码卡(.bscan-card-in)对齐:420px 定宽 + 视口相对上限,窄屏靠
   92vw 收边而不是靠父级 padding —— 两处同一个扫码弹窗,别一处写死 px 一处写百分比。 */
.sx-bcm-box{width:420px;max-width:92vw;overflow:hidden;border-radius:14px;background:var(--card);box-shadow:var(--sh2);}
.sx-bcm-head{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--line);}
.sx-bcm-title{font-size:15px;font-weight:700;color:var(--ink);}
/* 预览高度由画面自己定(video height:auto)· 容器 == 画面,取景框才跟引擎真正解码的那块
   像素严丝合缝;写死容器高比例一旦跟 cropRatio 不一致,就是「框里对准了却读不出」。 */
/* overflow:hidden 是必须的:取景框用一圈巨大的半透明 box-shadow 压暗框外,不裁就把整个
   弹窗(标题栏/按钮)一起压暗,看着像整个界面被禁用了。 */
.sx-bcm-view{position:relative;overflow:hidden;line-height:0;background:var(--ink);}
.sx-bcm-view .bscan-video{display:block;width:100%;height:auto;}
/* 位置与大小由 paintFrame 按引擎的 cropRatio 现算后写进 style:比例在两处各写一份必然漂,
   漂了就是「框里对准了却读不出」。边框走 --accent —— 它两套主题压在摄像头画面上都立得住;
   曾用的 --accent-ink 暗夜近黑,等于没画框。对比度由 test_sales_products_scan 量真令牌值把关。 */
.sx-bcm-frame{position:absolute;z-index:1;pointer-events:none;border:2px solid var(--accent);border-radius:8px;box-shadow:0 0 0 100vmax rgba(0,0,0,.3);}
.sx-bcm-msg{padding:10px 16px;text-align:center;font-size:12.5px;color:var(--ink-2);}
.sx-bcm-foot{display:flex;gap:8px;padding:0 16px 14px;}
.sx-bcm-foot .btn{flex:1;justify-content:center;}
@media(max-width:520px){.sx-bcm{padding:0;}.sx-bcm-box{width:100%;max-width:none;border-radius:0;}}
`;

// 同 sales-products-scan.ts:与 acct-common.ts 的 injectStyle 同形,收成一处要连 node
// harness 一起改(它 stub 掉 acct-common)—— 见交接单。
function ensureStyle(): void {
    if (document.getElementById('sx-bcm-style')) return;
    const st = document.createElement('style');
    st.id = 'sx-bcm-style';
    st.textContent = STYLE;
    document.head.appendChild(st);
}

function shell(): ScanCameraShell | null {
    return (window as unknown as { PearnlyScanCamera?: ScanCameraShell }).PearnlyScanCamera || null;
}

/** null = 这台设备能扫。地基常驻层缺席(理论上不会:它在 dist/pre.js 里)也算扫不了。 */
export function scanUnsupportedReason(): string | null {
    const cam = shell();
    return cam ? cam.unsupportedReason() : 'no_camera_api';
}

/**
 * 屏上取景框的位置(百分比),由引擎真正解码的 cropRatio 现算。预览是 width:100%/height:auto,
 * 容器就是画面本身,不像 object-fit:cover 那样会裁边 → 框可以跟解码区严丝合缝,不留余量。
 */
export function frameBox(crop: CropRatio): {
    width: number;
    height: number;
    left: number;
    top: number;
} {
    const width = crop.width * 100;
    const height = crop.height * 100;
    return { width, height, left: (100 - width) / 2, top: (100 - height) / 2 };
}

function paintFrame(view: HTMLElement, crop: CropRatio): void {
    document.getElementById(FRAME_ID)?.remove(); // 重试会再 create 一次,别叠出两个框
    const box = frameBox(crop);
    const frame = document.createElement('div');
    frame.id = FRAME_ID;
    frame.className = 'sx-bcm-frame';
    frame.style.width = box.width + '%';
    frame.style.height = box.height + '%';
    frame.style.left = box.left + '%';
    frame.style.top = box.top + '%';
    view.appendChild(frame);
}

let handle: CameraHandle | null = null;
let onManual: (() => void) | null = null;

function setScanMsg(html: string): void {
    const el = document.getElementById('sx-bcm-msg');
    if (el) el.innerHTML = html;
}

function manualBtnHtml(): string {
    return `<button type="button" class="btn btn-ghost" id="sx-bcm-manual">${escapeHtml(t('bscan.manual'))}</button>`;
}

function setScanFoot(html: string): void {
    const el = document.getElementById('sx-bcm-foot');
    if (!el) return;
    el.innerHTML = html;
    const manual = document.getElementById('sx-bcm-manual');
    if (manual)
        manual.onclick = () => {
            const back = onManual;
            closeScanModal();
            if (back) back();
        };
}

export function closeScanModal(): void {
    if (handle) {
        handle.destroy();
        handle = null;
    }
    onManual = null;
    document.getElementById(MASK_ID)?.remove();
}

// retryable=false 的档(没相机 / 非 HTTPS / 权限被拒)不给重试按钮 —— 重试一万次也一样,
// 出路是手动输入。
function renderScanError(err: ScanError, retry: (() => void) | null): void {
    setScanMsg(`<div class="sx-bc-warn">${escapeHtml(err.message || t(err.messageKey))}</div>`);
    const acts = [manualBtnHtml()];
    if (retry)
        acts.push(
            `<button type="button" class="btn btn-primary" id="sx-bcm-retry">${escapeHtml(t('sx-retry'))}</button>`
        );
    setScanFoot(acts.join(''));
    const again = document.getElementById('sx-bcm-retry');
    if (again && retry) again.onclick = retry;
}

async function startCamera(onCode: (code: string) => void): Promise<void> {
    const cam = shell();
    const view = document.getElementById('sx-bcm-view');
    if (!cam || !view) return;
    setScanMsg(escapeHtml(t('sx-p-bc-opening')));
    setScanFoot(manualBtnHtml());
    let api: CameraApi;
    try {
        api = await cam.ensureLoaded();
    } catch (_) {
        renderScanError(
            { code: 'decoder_unavailable', messageKey: 'bscan.err.decoder', retryable: true },
            () => void startCamera(onCode)
        );
        return;
    }
    if (!document.getElementById(MASK_ID)) return; // 拉解码器期间用户已关掉弹窗
    if (handle) handle.destroy();
    const h = api.create({
        container: view,
        t,
        onScan: onCode,
        onError: (e: ScanError) => renderScanError(e, e.retryable ? () => void h.retry() : null),
        onState: (s: string) => {
            if (s === 'starting') setScanMsg(escapeHtml(t('sx-p-bc-opening')));
            else if (s === 'scanning') {
                setScanMsg(escapeHtml(t('sx-p-bc-aim')));
                setScanFoot(manualBtnHtml());
            }
        },
    });
    handle = h;
    paintFrame(view, h.cropRatio());
    void h.start();
}

/**
 * @param onCode 解出一个码(弹窗由调用方在 applyCode 里关)
 * @param onBackToField 用户选「手动输入条码」后的落点(把焦点还给条码框)
 */
export function openScanModal(onCode: (code: string) => void, onBackToField: () => void): void {
    if (document.getElementById(MASK_ID)) return; // 开着就不再开:两张同 id 的窗会互相抢元素
    if (scanUnsupportedReason()) return; // 按钮本就不该在 · 双保险
    ensureStyle();
    onManual = onBackToField;
    const mask = document.createElement('div');
    mask.id = MASK_ID;
    mask.className = 'sx-bcm';
    mask.innerHTML = `<div class="sx-bcm-box" role="dialog" aria-modal="true">
        <div class="sx-bcm-head"><div class="sx-bcm-title">${escapeHtml(t('sx-p-bc-title'))}</div>
            <button type="button" class="modal-close" id="sx-bcm-x" aria-label="${escapeHtml(t('sx-cancel'))}">${IC_X}</button></div>
        <div class="sx-bcm-view" id="sx-bcm-view"></div>
        <div class="sx-bcm-msg" id="sx-bcm-msg"></div>
        <div class="sx-bcm-foot" id="sx-bcm-foot"></div>
    </div>`;
    document.body.appendChild(mask);
    const x = document.getElementById('sx-bcm-x');
    if (x) x.onclick = closeScanModal;
    mask.onclick = (e) => {
        if (e.target === mask) closeScanModal();
    };
    void startCamera(onCode);
}
