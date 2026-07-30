// POS 项目 · PO-A4 库存后台 · 入库弹窗「扫码加行」
//
// 真实动作是一箱一箱往架上搬,手上没空在几百个商品的下拉框里翻 —— 所以入库的主输入是扫,
// 不是选:枪扫或摄像头扫到码 → 查商品 → 直接落成一行;同一个码再扫一次 = 这一行数量 +1
// (不生成第二行重复商品,店员点进来看到的就是「这货扫了 12 件」)。下拉框留着不动,
// 没条码的散装货还得靠它。合并有两个例外,都在 planRow 上写清楚了:批次品、以及不同单位的码。
//
// 摄像头引擎(window.PearnlyScanCamera)与条码枪楔子(window.PearnlyScanWedge)是共享地基
// (static/scan/*),本文件只做「码 → 入库行」这一段;画面归 inventory-scan-camera、四态文案
// 归 inventory-scan-ui;行的 DOM 与批次显隐仍归 inventory-modals.ts,靠 ScanHost 两个回调借
// 过来,不在这里另写一套。
/* global t, escapeHtml */
import { salesFetch, salesErrMsg } from './sales-common.js';
import { isPlausibleDate, localizedName } from './inventory-common.js';
import {
    ackFails,
    blockedText,
    failLineHtml,
    notFoundHtml,
    paintNote,
    pushFail,
    replaceFail,
    resetFeedback,
    resolveFail,
    scanPart,
} from './inventory-scan-ui.js';
import {
    cameraBlockedReason,
    cameraRunning,
    openCamera,
    releaseCamera,
    retryCamera,
    stopCamera,
    type CamHost,
} from './inventory-scan-camera.js';

// 光标在数量框里时人正在打数量,三四位数字打得快也会被楔子当成一串码。零售条码最短是
// EAN-8/UPC-E 的 8 位,店里不存在 8 位数的数量 —— 用长度把「打字」和「扫码」分开。
const MIN_LEN_IN_FIELD = 8;
// 长度在批号/效期这两个框里不够用:批号「L2026-08」是 8 位,日期打成「07312026」也是 8 位。
// 行内的框里人一直在打字,把「枪」和「人」分开只剩速度这一个可靠信号(楔子自己也是这么判
// 该不该吃回车的)。两个阈值都向楔子要,拿不到才用这份兜底 —— 别在这里另立一个会漂的数。
const GUN_GAP_FALLBACK_MS = 50;
const BURST_GAP_FALLBACK_MS = 150;

// ── 共享地基的类型面(window 上的全局,故在此就地声明;引擎本身是 plain script)──
interface WedgeApi {
    register: (
        cb: (code: string, target: EventTarget | null) => void,
        opts?: { exclusive?: boolean }
    ) => () => void;
    GUN_MAX_GAP_MS?: number;
    MAX_GAP_MS?: number;
}

// 契约(跨页带码桥):建品侧挂到 window,返回 true = 表单真的打开了。
interface ProductFormBridge {
    openProductFormWithBarcode?: (code: string, opts?: { overlay?: boolean }) => boolean | void;
}

interface LookupProduct {
    id: string;
    name_th?: string | null;
    name_en?: string | null;
    name_zh?: string | null;
    track_batch?: boolean;
}
// GET /api/sales/products/lookup 的信封(routes/products_routes.py::api_lookup_product)。
// 字段名照后端那三个写,跟建品侧(sales-products-scan.ts)读的是同一份,别自创第二套。
interface LookupBody {
    product?: LookupProduct;
    matched_by?: string;
    matched_unit?: string | null;
    detail?: string;
}

/**
 * 行的 DOM 归 inventory-modals.ts:加行与批次显隐都借它的原件,扫码不另写一套。
 * syncRow 必须收下 tracksBatch —— 这个事实只有查码应答说得准:刚建完的商品还不在列表缓存里,
 * 让那边照旧去缓存里查就是「查不到 → 当非批次品 → 批号格永不出现 → 批次货静默落进散装桶」。
 */
export interface ScanHost {
    maskId: string;
    addRow: () => HTMLElement | null;
    syncRow: (row: HTMLElement, tracksBatch: boolean) => void;
}

// ── 纯判定(单测直接验)────────────────────────────────────────────────
export type RowPlanKind = 'bump' | 'fill' | 'append';
export interface RowPlan {
    kind: RowPlanKind;
    index: number;
}
/** 屏上一行的身份:同一件货按不同单位入库是两行(1 箱 ≠ 1 瓶)。unit 空 = 按基本单位。 */
export interface ScanRow {
    productId: string;
    unit: string;
}
export interface ScanHit extends ScanRow {
    tracksBatch: boolean;
}

/**
 * 已选同一商品 → 落回那一行;否则先用掉空行(弹窗默认开两行空行);都没有才追加。
 *
 * 批次品不合并:一行只带一组批号/效期,第二箱(批号 B/别的效期)合进第一箱那一行 = 两箱
 * 全落在第一箱的效期下,POS 的 FEFO 出货顺序与近效期告警从此按错日期算。宁可多一行让店员
 * 填这箱的批号,也不能悄悄把第二箱的效期换掉。
 * 单位不同也不合并:扫箱码与扫瓶码是同一件货的两种入库单位,合并会把「1 箱」当成「1 瓶」。
 */
export function planRow(rows: ScanRow[], hit: ScanHit): RowPlan {
    const same = hit.tracksBatch
        ? -1
        : rows.findIndex((r) => r.productId === hit.productId && r.unit === hit.unit);
    if (same >= 0) return { kind: 'bump', index: same };
    const blank = rows.findIndex((r) => !r.productId);
    if (blank >= 0) return { kind: 'fill', index: blank };
    return { kind: 'append', index: -1 };
}

/** 扫一次 = 一件。空/非数字当 0 起算;拆零品可能是小数,乘一千取整免得浮点尾巴。 */
export function bumpQty(current: string): string {
    const n = Number(String(current || '').trim());
    const next = (Number.isFinite(n) ? n : 0) + 1;
    return String(Math.round(next * 1000) / 1000);
}

/**
 * 枪扫进数量框时字符照旧落进了那个框(楔子只吃 Enter/Tab,不吃字符),把这串码摘回去,
 * 数量才不会变成一串条码。光标被人挪到中间时是插入,故先看尾再看中间。
 */
export function stripScanned(value: string, code: string): string {
    if (!code || !value) return value;
    if (value === code) return '';
    if (value.endsWith(code)) return value.slice(0, -code.length);
    const at = value.indexOf(code);
    return at >= 0 ? value.slice(0, at) + value.slice(at + code.length) : value;
}

/** 落在输入框里的按键串要够长才当条码,否则手打的数量会被当成扫了一件货。 */
export function acceptsCode(code: string, fromField: boolean): boolean {
    if (code.length < 3) return false;
    return !fromField || code.length >= MIN_LEN_IN_FIELD;
}

/**
 * 箱码与瓶码是两个码同一件货,命中的是哪个单位由后端答:matched_by='unit' 时 matched_unit
 * 是那个单位名。前端只把它原样带进这一行,换算成基本单位是后端 resolve_factor 的活 ——
 * 前端替它乘一遍 = 系数改一次两处漂。
 * 主码命中(matched_by='product')一律当基本单位:POS 的 by-barcode 在主码命中时会把
 * base_unit 填进 matched_unit,照单全收会给每一行都贴一个没有意义的单位。
 */
export function matchedUnit(body: LookupBody | null): string {
    if (!body || body.matched_by === 'product') return '';
    return String(body.matched_unit || '').trim();
}

// ── 运行态 ────────────────────────────────────────────────────────────
interface Active {
    host: ScanHost;
    offWedge: (() => void) | null;
}
let active: Active | null = null;
// 串行化:摄像头连扫与枪扫可能撞在一起,两个查询同时回来会把同一件货加成两行。
let chain: Promise<void> = Promise.resolve();

/**
 * 一串按键的快照。value 是按第一个字符之前框里的东西 —— 判成枪扫时原样放回去(见 onWedge);
 * maxGap 答的是「这串到底是枪打的还是人打的」,人手打不出 ≤50ms/字符,这是行内框里唯一
 * 分得开两者的信号(批号也好日期也好,长度都不够用)。
 */
interface Burst {
    el: HTMLInputElement;
    value: string;
    at: number;
    maxGap: number;
}
let burst: Burst | null = null;

function wedgeApi(): WedgeApi | null {
    const w = window as unknown as { PearnlyScanWedge?: WedgeApi };
    return w.PearnlyScanWedge || null;
}

function gunGapMs(): number {
    const api = wedgeApi();
    return (api && api.GUN_MAX_GAP_MS) || GUN_GAP_FALLBACK_MS;
}

function burstGapMs(): number {
    const api = wedgeApi();
    return (api && api.MAX_GAP_MS) || BURST_GAP_FALLBACK_MS;
}

function part(name: string): HTMLElement | null {
    return scanPart(active ? active.host.maskId : '', name);
}

// 相机面板认「哪张弹窗」+「码交给谁」;alive 让它在等解码器时认得出弹窗已经换了一张。
function camHost(): CamHost {
    const opened = active;
    return {
        maskId: opened ? opened.host.maskId : '',
        alive: () => active === opened,
        onCode: enqueue,
    };
}

function rowEls(): HTMLElement[] {
    const wrap = active ? document.getElementById(active.host.maskId + '-rows') : null;
    return wrap ? Array.from(wrap.querySelectorAll<HTMLElement>('[data-row]')) : [];
}

function productSel(row: HTMLElement): HTMLSelectElement | null {
    return row.querySelector<HTMLSelectElement>('[data-k="product_id"]');
}

function unitField(row: HTMLElement): HTMLInputElement | null {
    return row.querySelector<HTMLInputElement>('[data-k="unit_name"]');
}

function setMsg(tone: string, html: string): void {
    paintNote(part('msg'), tone, html);
}

function clearMsg(): void {
    setMsg('', '');
}

// 这一件有结论了 → 撤掉「正在查」那句,再把它排进「没落地的码」待办队列。
function failCode(code: string, html: string): void {
    clearMsg();
    pushFail(part('msg'), code, html);
}

function focusCodeInput(): void {
    const input = part('code') as HTMLInputElement | null;
    if (input) input.focus();
}

// ── 查商品 → 落行 ─────────────────────────────────────────────────────
function enqueue(code: string): void {
    chain = chain.then(() => lookup(code.trim())).catch(() => undefined);
}

async function lookup(code: string): Promise<void> {
    if (!code || !active) return;
    setMsg('busy', escapeHtml(t('inv-scan-looking')));
    let resp: Response;
    try {
        resp = await salesFetch('/api/sales/products/lookup?barcode=' + encodeURIComponent(code));
    } catch (_) {
        failCode(code, failLineHtml(t('inv-scan-fail'), code));
        return;
    }
    if (resp.status === 404) {
        failCode(code, notFoundHtml(code));
        return;
    }
    const body = (await resp.json().catch(() => null)) as LookupBody | null;
    if (!resp.ok) {
        failCode(code, failLineHtml(salesErrMsg(body && body.detail, 'inv-scan-fail'), code));
        return;
    }
    const product = body && body.product;
    if (!product || !product.id) {
        failCode(code, failLineHtml(t('inv-scan-fail'), code));
        return;
    }
    applyHit(code, product, matchedUnit(body));
}

// 列表被搜索关键词过滤过时,下拉里可能没有刚扫到的商品:不补 option 就设不进 value,
// 提交时这一行会被静默丢掉(看着加上了,实际没入库)。
function ensureOption(sel: HTMLSelectElement, id: string, name: string): void {
    if (Array.from(sel.options).some((o) => o.value === id)) return;
    const opt = document.createElement('option');
    opt.value = id;
    opt.textContent = name;
    sel.appendChild(opt);
}

// 单位码命中:这一行按「箱」入库。字段是提交时发给后端换算的凭据,标签是给店员看的 ——
// 只写字段不显示,屏上还是一个没有单位的「1」,谁也看不出入的是 12 瓶。
function setRowUnit(row: HTMLElement, unit: string): void {
    const field = unitField(row);
    if (field) field.value = unit;
    const label = row.querySelector<HTMLElement>('[data-runit]');
    if (label) {
        label.textContent = unit;
        label.hidden = !unit;
    }
}

function rowIdentities(rows: HTMLElement[]): ScanRow[] {
    return rows.map((r) => ({
        productId: (productSel(r) || { value: '' }).value,
        unit: (unitField(r) || { value: '' }).value,
    }));
}

// 合并加一件是「一箱箱扫同一件货」的正常动作,不必解释;另起一行必须解释,否则店员只看见
// 行数变多,不知道该去填这箱的批号/效期。单位码同理:得说清这一行的 1 是 1 箱不是 1 瓶。
function hitMsg(kind: RowPlanKind, before: ScanRow[], hit: ScanHit, name: string): string {
    const split = hit.tracksBatch && before.some((r) => r.productId === hit.productId);
    const key =
        kind === 'bump' ? 'inv-scan-bumped' : split ? 'inv-scan-batch-row' : 'inv-scan-added';
    const line = escapeHtml(t(key, { name }));
    return hit.unit ? line + ' · ' + escapeHtml(t('inv-scan-unit-hit', { unit: hit.unit })) : line;
}

function applyHit(code: string, product: LookupProduct, unit: string): void {
    if (!active) return;
    const name = localizedName({
        th: product.name_th ?? null,
        en: product.name_en ?? null,
        zh: product.name_zh ?? null,
    });
    const rows = rowEls();
    const before = rowIdentities(rows);
    const hit: ScanHit = { productId: product.id, unit, tracksBatch: !!product.track_batch };
    const plan = planRow(before, hit);
    const row = plan.kind === 'append' ? active.host.addRow() : rows[plan.index];
    if (!row) {
        setMsg('err', escapeHtml(t('inv-scan-fail')));
        return;
    }
    if (plan.kind !== 'bump') {
        const sel = productSel(row);
        if (sel) {
            ensureOption(sel, product.id, name);
            sel.value = product.id;
            setRowUnit(row, unit);
            // 批次品的批号/效期格走 onProductChange 同一套显隐,不在这里另判一遍;但「管不管
            // 批次」这个事实得由查码应答带过去 —— 那边的列表缓存里可能根本没有这件刚建的货。
            active.host.syncRow(row, hit.tracksBatch);
        }
    }
    const qty = row.querySelector<HTMLInputElement>('[data-k="qty"]');
    if (qty) {
        qty.value = bumpQty(qty.value);
        // 光标落数量框:扫完就能改数(整箱 24 支);枪的下一发也照旧收得到(见 onWedge)
        qty.focus();
    }
    row.scrollIntoView({ block: 'nearest' });
    setMsg('ok', hitMsg(plan.kind, before, hit, name));
    // 这个码这次真进单了(多半是建完品回来重扫)→ 它那条待办到此为止
    resolveFail(part('msg'), code);
}

// ── 装配 ──────────────────────────────────────────────────────────────
function rowField(target: EventTarget | null): HTMLInputElement | null {
    const el = target as HTMLElement | null;
    if (!el || !(el instanceof HTMLInputElement)) return null;
    return rowEls().some((row) => row.contains(el)) ? el : null;
}

// 一串按键的起点:楔子按 150ms 间隔把「一串」切出来,这里跟着同一根节拍记下按第一个字符
// 之前框里是什么,并量这串的最大字符间隔。非打印键不动快照(Enter/Tab 不改 value)。
function onRowKeydown(ev: KeyboardEvent): void {
    if (!ev.key || ev.key.length !== 1) return;
    const el = rowField(ev.target);
    if (!el) return;
    const now = Date.now();
    const gap = burst && burst.el === el ? now - burst.at : Infinity;
    if (gap > burstGapMs()) burst = { el, value: el.value, at: now, maxGap: 0 };
    else if (burst) {
        burst.maxGap = Math.max(burst.maxGap, gap);
        burst.at = now;
    }
}

/**
 * 落在行内框里的一串是枪打的才算条码:批号「L2026-08」够 8 位,长度分不开人和枪,只有速度
 * 分得开(人手打不出 ≤50ms/字符)。效期框还有第二个与速度无关的判据 —— 人填完一个日期,框里
 * 剩下的一定是个 4 位年份的像样日期;一串条码打进去剩下的是 49012-03-31,只有机器打得出来,
 * 所以慢枪打进效期框也照样按枪算。
 * 剩下那档(慢枪打进批号框)那串码照旧留在框里看得见,店员改得掉,不会静默进流水。
 *
 * 判成枪就把框还原成这一串开始之前的样子:数量框还能靠 stripScanned 把码摘回去,type=date
 * 摘不了 —— 一串数字打进去 value 已经变成 49012-03-31,那串码在 value 里根本找不到。
 */
function onWedge(code: string, target: EventTarget | null): void {
    const field = rowField(target);
    if (!acceptsCode(code, !!field)) return;
    if (!field) {
        enqueue(code);
        return;
    }
    const snap = burst && burst.el === field ? burst : null;
    burst = null;
    const machine = field.type === 'date' && !isPlausibleDate(field.value);
    if (snap && snap.maxGap > gunGapMs() && !machine) return;
    field.value = snap ? snap.value : stripScanned(field.value, code);
    enqueue(code);
}

// 带码建品必须【叠在本弹窗之上】:跳走会把半张入库单连行一起丢掉。建完回来再扫一次即命中,
// 不做回调链。桥没接上或它自己说打不开(返回非 true)时不假装成功,由调用方给诚实回落。
function openCreateForm(code: string): boolean {
    const open = (window as unknown as ProductFormBridge).openProductFormWithBarcode;
    return typeof open === 'function' && open(code, { overlay: true }) === true;
}

function onMsgClick(ev: MouseEvent): void {
    const el = (ev.target as HTMLElement | null)?.closest<HTMLElement>(
        '[data-scan-create],[data-scan-retry],[data-scan-manual],[data-scan-ack]'
    );
    if (!el) return;
    if (el.dataset.scanRetry) {
        retryCamera(camHost());
        return;
    }
    if (el.dataset.scanAck) {
        ackFails(part('msg'));
        return;
    }
    if (el.dataset.scanManual) {
        clearMsg();
        focusCodeInput();
        return;
    }
    const code = el.dataset.scanCreate || '';
    if (openCreateForm(code)) return;
    // 桥打不开 → 换掉这一条的说法,但这个码仍然没落地,不许让它悄悄出队
    replaceFail(
        part('msg'),
        code,
        `<span class="c">${escapeHtml(t('inv-scan-create-manual').replace('{code}', code))}</span>`
    );
}

export function mountInvScan(host: ScanHost): void {
    unmountInvScan();
    active = { host, offWedge: null };
    resetFeedback();
    document.addEventListener('keydown', onRowKeydown, true);

    const btn = part('cam') as HTMLButtonElement | null;
    if (btn)
        btn.onclick = () => (cameraRunning() ? stopCamera(camHost()) : void openCamera(camHost()));
    const input = part('code') as HTMLInputElement | null;
    if (input)
        input.onkeydown = (ev: KeyboardEvent) => {
            if (ev.key !== 'Enter') return;
            ev.preventDefault(); // 枪的回车不该顺手把整张入库单提交了
            const code = input.value.trim();
            input.value = '';
            enqueue(code);
        };
    const msg = part('msg');
    if (msg) msg.onclick = onMsgClick;

    // 弹窗开着时独占楔子:枪扫的码不该漏进底下的库存页
    const gun = wedgeApi();
    if (gun) active.offWedge = gun.register(onWedge, { exclusive: true });

    const blocked = cameraBlockedReason();
    if (blocked) {
        if (btn) btn.disabled = true;
        setMsg('warn', blockedText(blocked));
    }
}

export function unmountInvScan(): void {
    if (!active) return;
    if (active.offWedge) active.offWedge();
    document.removeEventListener('keydown', onRowKeydown, true);
    // 不放就是相机灯一直亮着、别的应用再也打不开相机
    releaseCamera();
    // 这轮收货结束 = 那几条「没落地的码」的事也结束了(DOM 本来就要被清掉,状态得跟着走)
    resetFeedback();
    burst = null;
    active = null;
}
