// POS 项目 · PO-A4 入库弹窗扫码 · 「把四态说清楚」这一层:扫码条骨架 + 状态消息 + 未命中/出错卡
// + 没落地的码那条待办队列(见下面 fails)。
//
// 与 inventory-scan.ts 分家只因行数(单文件 <500)。消息元素由调用方传进来,「哪个弹窗开着」
// 在 inventory-scan 里只有一份;取景框几何也只算不画,画在那边。队列状态放这一层是因为
// 摄像头面板(inventory-scan-camera)也往同一格里写字 —— 两处各存一份就会互相盖掉。
/* global t, escapeHtml */

/** 摄像头引擎(static/scan/scan-camera.js)回调出来的错误对象。 */
export interface ScanError {
    code: string;
    messageKey: string;
    retryable: boolean;
    detail: string;
    message?: string;
}

const IC_CAM =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>';

// 取景框比引擎真正解码的区域小一档:预览是 object-fit:cover(只会裁掉画面边缘,不会补),
// 框画得比解码区小 → 框里对准的东西一定在解码区内,不会出现「框里对上了却读不出」。
const FRAME_INSET = { width: 0.9, height: 0.7 };

// 非 HTTPS / 没有摄像头 API 各是一句不同的话。Odoo 在这两种情况下让扫码按钮静默消失,
// 店员只觉得「功能没了」;这里按钮留着但说清为什么点不动。
const BLOCKED_KEY: Record<string, string> = {
    insecure_context: 'bscan.err.insecure',
    no_camera_api: 'bscan.err.unsupported',
};

/**
 * 屏上取景框的位置(百分比),由引擎真正解码的 cropRatio 现算 —— 两处各写一份比例必然漂,
 * 漂了就是「框里对准了却读不出」。取 FRAME_INSET 一档余量后仍居中。
 */
export function frameBox(crop: { width: number; height: number }): {
    width: number;
    height: number;
    left: number;
    top: number;
} {
    const width = crop.width * FRAME_INSET.width * 100;
    const height = crop.height * FRAME_INSET.height * 100;
    return { width, height, left: (100 - width) / 2, top: (100 - height) / 2 };
}

export function scanBarHtml(maskId: string): string {
    return `<div class="inv-scan">
        <div class="inv-scan-bar">
            <input class="inv-field" id="${maskId}-scan-code" autocomplete="off" placeholder="${escapeHtml(t('inv-scan-ph'))}">
            <button type="button" class="inv-mbtn" id="${maskId}-scan-cam">${IC_CAM}<span id="${maskId}-scan-camlabel">${escapeHtml(t('inv-scan-cam'))}</span></button>
        </div>
        <div class="inv-scan-hint">${escapeHtml(t('inv-scan-hint'))}</div>
        <div class="inv-scan-stage" id="${maskId}-scan-stage" hidden></div>
        <div class="inv-scan-msg" id="${maskId}-scan-msg" role="status" aria-live="polite"></div>
    </div>`;
}

/** 扫码条各件的 id 只在这里拼一次:骨架是上面那段 HTML 生成的,取件的两边都从这里取。 */
export function scanPart(maskId: string, name: string): HTMLElement | null {
    return maskId ? document.getElementById(maskId + '-scan-' + name) : null;
}

// ── 扫码反馈:失败留、成功不盖 ────────────────────────────────────────
// 这一格消息位原先只装得下一句话:后一件的「已加入」把前一件的「这个码没建档」盖掉,店员按
// 屏上反馈收货,被盖掉的那件就是「扫了、没进单、也没人告诉他」的货 —— 一整箱凭空从收货单上
// 消失。所以没落地的码进一份失败清单,成功/进行中只占最后那一行瞬时位,永远不覆盖清单。
// 清单只由五件事变动:同一个码后来真加进去了(resolveFail)、那条的出路被走过了(replaceFail)、
// 店员点掉那一行自己的出路(dropFail)、店员点「知道了」(ackFails)、这轮扫码结束(resetFeedback)。
// 收银台那一侧(static/pos/pos-scan.js 的 fails)是同一套:累积 + 计数 + 只有店员点得掉。
// 这边多一条按码去重 —— 收货时同一箱货常被反复扫,同一个码叠出一摞一模一样的卡没有意义。
interface ScanFail {
    code: string;
    html: string;
    /** 「刚才那一下被当成同一件挡下了」那一行 —— 销账规矩跟别的不一样,见 resolveFail。 */
    dup?: boolean;
}
const FAILS_MAX = 20; // 只防无限长撑破弹窗;真实一轮收货不会有 20 个码进不来
let fails: ScanFail[] = [];
let note = { tone: '', html: '' };

function lineHtml(tone: string, html: string): string {
    return html ? `<div class="inv-scan-line${tone ? ' ' + tone : ''}">${html}</div>` : '';
}

// 计数行:「还有几件没进来」得一眼看得见,否则清单长了就只剩一堆看不出轻重的黄字。
// 「知道了」是这份清单唯一的出口 —— 没有出口的常驻警告等于噪音,店员会学会无视它。
function headHtml(): string {
    return lineHtml(
        'warn',
        `<span class="c">${escapeHtml(t('inv-scan-fails-n', { n: fails.length }))}</span>` +
            `<button type="button" class="inv-scan-act" data-scan-ack="1">${escapeHtml(
                t('inv-scan-fails-ack')
            )}</button>`
    );
}

// 整块的 tone 仍按最重的那一档给(清单非空 = warn),逐条再各自上色:一格里同时挂着黄色的
// 「没建档」和绿色的「已加入」时,两句话不能都被涂成同一个颜色。
function render(el: HTMLElement | null): void {
    if (!el) return;
    const tone = fails.length ? 'warn' : note.tone;
    el.className = 'inv-scan-msg' + (tone ? ' ' + tone : '');
    el.innerHTML =
        (fails.length ? headHtml() : '') +
        fails.map((f) => lineHtml('warn', f.html)).join('') +
        lineHtml(note.tone, note.html);
}

/** 瞬时行:busy=正在开相机/正在查,ok=命中,tip=取景引导,err/warn=这台机器扫不了。 */
export function paintNote(el: HTMLElement | null, tone: string, html: string): void {
    note = { tone, html };
    render(el);
}

/** 这个码没落地 —— 排进失败清单。最新的排最上面(不滚动也看得见刚扫那件),同码只刷新一条。 */
export function pushFail(
    el: HTMLElement | null,
    code: string,
    html: string,
    opts?: { dup?: boolean }
): void {
    fails = fails.filter((f) => f.code !== code);
    fails.unshift({ code, html, dup: !!(opts && opts.dup) });
    fails.length = Math.min(fails.length, FAILS_MAX);
    render(el);
}

/** 这个码已经欠着一笔了吗 —— 调用方靠它决定要不要再排一条(见 inventory-scan.ts 的 onCameraDup)。 */
export function hasFail(code: string): boolean {
    return fails.some((f) => f.code === code);
}

/** 店员点「知道了」:清单归零,瞬时行不动(那是另一件事的状态)。 */
export function ackFails(el: HTMLElement | null): void {
    fails = [];
    render(el);
}

/** 那条的出路走过了(建品桥说打不开)→ 换成诚实回落,但这个码仍然没落地,不许出队。 */
export function replaceFail(el: HTMLElement | null, code: string, html: string): void {
    const at = fails.findIndex((f) => f.code === code);
    if (at >= 0) fails[at] = { code, html };
    render(el);
}

/**
 * 这个码这次真加进行里了(建完品回来重扫)→ 它的待办到此为止。
 *
 * dup 那一行是唯一的例外:它说的是【那一箱】可能没进单,而这个码后来又真记上一件,记的是
 * 【再一箱】—— 拿后者销前者等于把没进单的那箱悄悄抹掉,屏上于是跟全都收上了一模一样。
 * 真浏览器实测(1.2s 与 2.0s 空档交替、无人触碰、14.1 秒):不加这条例外时那行被自动抹掉
 * 2 次,收货单最后 3 件而柜台上过了 6 箱。所以它只有店员销得掉 —— 点「是第二件 · 加 1」
 * (走 dropFail)或点「知道了」。收银台同一招(static/pos/pos-scan.js 的 resolveFail)。
 */
export function resolveFail(el: HTMLElement | null, code: string): void {
    const at = fails.findIndex((f) => f.code === code && !f.dup);
    if (at < 0) return;
    fails.splice(at, 1);
    render(el);
}

/** 店员点掉了那一行自己的出路 → 这笔账由他那一下结掉,不管它是哪一档。 */
export function dropFail(el: HTMLElement | null, code: string): void {
    const at = fails.findIndex((f) => f.code === code);
    if (at < 0) return;
    fails.splice(at, 1);
    render(el);
}

export function resetFeedback(): void {
    fails = [];
    note = { tone: '', html: '' };
}

/** 查失败那档:话是后端/网络给的,码是店员分辨「哪一件没进来」的唯一凭据,得跟着一起显。 */
export function failLineHtml(text: string, code: string): string {
    return `<span class="c">${escapeHtml(text)}</span><b class="inv-scan-code">${escapeHtml(code)}</b>`;
}

function actionHtml(attr: string, key: string): string {
    return `<button type="button" class="inv-scan-act" ${attr}>${escapeHtml(t(key))}</button>`;
}

// 未命中必须把扫到的码显出来:店员才分得清是码贴错了还是这货压根没建档。
export function notFoundHtml(code: string): string {
    const line = escapeHtml(t('bscan.notfound').replace('{code}', code));
    return `<span class="c">${line}</span>${actionHtml(
        `data-scan-create="${escapeHtml(code)}"`,
        'bscan.notfound_create'
    )}`;
}

/**
 * 楔子把这一串当成人在打字了(见 static/scan/scan-wedge.js 的 onTyped)。
 *
 * 它不是错误 —— 店员多半真的在填批号/效期,所以走最弱的那一档(tip)、只占瞬时行、不进
 * 待办队列。但必须看得见:慢枪扫的那一发也长这样,静默丢掉就是三轮实测的「整箱从收货单
 * 消失、屏上零字」。带上那串字符是唯一能让店员认出「原来是我刚才那一枪」的凭据,再给一条
 * 出路 —— 判不准时机器偏向人手,判错的那一半由店员一点补回来。
 */
export function typedHtml(code: string): string {
    return (
        `<span class="c">${escapeHtml(t('inv-scan-typed'))}</span>` +
        `<b class="inv-scan-code">${escapeHtml(code)}</b>` +
        actionHtml(`data-scan-typed="${escapeHtml(code)}"`, 'inv-scan-typed-use')
    );
}

/**
 * 摄像头把这一次当成「同一件还在画面里」挡下了(见 static/scan/scan-camera.js 的 onDuplicate)。
 *
 * 它进【待办队列】,不占瞬时行。曾经按「这只是一句可能的问话,别给队列注水」放在瞬时行,
 * 而瞬时行只有一格:下一次扫码的第一句(lookup 开头那句「正在查这个条码」)就把整格盖掉。
 * 真浏览器实测(1.2s/2.0s 空档交替、无人触碰、14.1 秒):那行出现 3 次、自己消失 2 次,
 * 柜台上过了 6 箱而收货单只有 3 件 —— 少的三箱屏上零痕迹。可能没进单的一箱跟确定没进单的
 * 一箱,对存货估值与之后每一笔 COGS 是同一种错,理该同一份账本记着。
 * 引擎那道地板以下,真第二箱与一次长反光在解码结果上分不开,只有站在货前面的店员分得开。
 */
export function duplicateHtml(code: string): string {
    return (
        `<span class="c">${escapeHtml(t('inv-scan-dup'))}</span>` +
        `<b class="inv-scan-code">${escapeHtml(code)}</b>` +
        actionHtml(`data-scan-dup="${escapeHtml(code)}"`, 'inv-scan-dup-add')
    );
}

// 可重试的档给重试;不可重试的(没相机/非 HTTPS/权限要去系统设置改)给「手动输入条码」
// 这条出路 —— 给重试按钮是耍人。
export function errorHtml(err: ScanError): string {
    const line = `<span class="c">${escapeHtml(err.message || t(err.messageKey))}</span>`;
    return (
        line +
        (err.retryable
            ? actionHtml('data-scan-retry="1"', 'inv-scan-retry')
            : actionHtml('data-scan-manual="1"', 'bscan.manual'))
    );
}

export function blockedText(reason: string): string {
    return escapeHtml(t(BLOCKED_KEY[reason] || 'bscan.err.unsupported'));
}
