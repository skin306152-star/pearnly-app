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
import { localizedName, fmtQty } from './inventory-common.js';
import { showScanSuccessVisual } from './scan-success-visual.js';
import {
    ackFails,
    blockedText,
    dropFail,
    duplicateHtml,
    failLineHtml,
    hasFail,
    notFoundHtml,
    paintNote,
    pushFail,
    replaceFail,
    resetFeedback,
    resolveFail,
    scanPart,
    typedHtml,
} from './inventory-scan-ui.js';
import {
    cameraBlockedReason,
    cameraRunning,
    openCamera,
    rejectCameraCode,
    releaseCamera,
    retryCamera,
    stopCamera,
    type CamHost,
} from './inventory-scan-camera.js';

// ── 共享地基的类型面(window 上的全局,故在此就地声明;引擎本身是 plain script)──
//
// 「这一串是枪打的还是人打的」不在这一层判:行内那三个框(数量/批号/效期)都声明了
// data-enable-barcode="gun",楔子按同一把尺子判完、把框还原成扫之前的样子,才发过来。
// 这里再判一遍就是第二把尺子,而两把尺子必然漂 —— 三轮里批号框被打成 L20274901234567894、
// 第二箱整箱从收货单消失且零提示,就是这么来的。故这里只 register,判据一个字都不抄。
// onTyped 不是判据的第二个出口:它只说「刚才那一串我按人在打字处理了」,给屏上留句话。
interface WedgeBurst {
    gap: number;
    repeat: boolean;
    field: boolean;
    /** 那个框在这一串开始之前的内容 · 楔子没动过它,要当条码用得由这边还原 */
    before: string | null;
}
interface WedgeApi {
    register: (
        cb: (code: string, target: EventTarget | null) => void,
        opts?: {
            exclusive?: boolean;
            onTyped?: (code: string, target: EventTarget | null, info: WedgeBurst) => void;
        }
    ) => () => void;
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
    image_url?: string | null;
    default_cost?: number | null;
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
    syncRow: (row: HTMLElement, tracksBatch: boolean, referenceCost?: number | null) => void;
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
    // 取整交给 fmtQty(整数不带小数 · 非整数 3 位去尾零)—— 库存那边的数量都按这条规矩印,
    // 自己再写一份「乘一千取整」等于同一条规矩两处维护,漂了就是两屏显示不一样。
    return fmtQty((Number.isFinite(n) ? n : 0) + 1);
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
// 最近一串被当成「人在打字」的输入 —— 店员点「当条码用」时要把那个框还原回去(见 useTyped)。
// 只留最新一条:这句话本身就是瞬时行,下一发进来时上一条已经不在屏上了。
interface TypedBurst {
    code: string;
    el: HTMLInputElement | null;
    before: string | null;
}
let typed: TypedBurst | null = null;

function wedgeApi(): WedgeApi | null {
    const w = window as unknown as { PearnlyScanWedge?: WedgeApi };
    return w.PearnlyScanWedge || null;
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
        onDup: onCameraDup,
    };
}

// 引擎把这一次当成「同一件还在画面里」挡下了 —— 被挡下的可能正是第二箱,那一箱的唯一线索
// 就是这一行,所以它得进【累积清单】(pushFail),不能占瞬时行:瞬时行只有一格,下一次扫的
// 第一句 setMsg('busy') 就把它整格盖掉(实测数字见 inventory-scan-ui.ts 的 duplicateHtml)。
// 这里不再判一遍「到底是不是第二件」:判据在引擎里只有一份(两把尺子 AND),这一层照它的
// 结论说话。真第二箱与一次长反光在地板以下同形,分得开的只有站在货前面的那个人。
// 这个码已经欠着一笔就什么都不做:一是举着不动会反复触发,重记只让它一直往清单顶上跳,把
// 真正新失败的那件挤下去;二是那一笔要是「这个码没建档」,换成 dup 行之后「去建品」那条
// 线索没有第二个地方还记得,而那颗「加 1」按下去只会再吃一次 404。
function onCameraDup(code: string): void {
    if (!active || hasFail(code)) return;
    pushFail(part('msg'), code, duplicateHtml(code), { dup: true });
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

/** 扫码框里有字 = 有人(或一把还没打完的枪)正在往里输 —— 这时候谁都别抢焦点。 */
function scanBoxBusy(): boolean {
    const input = part('code') as HTMLInputElement | null;
    return !!input && input.value.length > 0;
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
        rejectCameraCode(code);
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
            active.host.syncRow(row, hit.tracksBatch, product.default_cost);
        }
    }
    const qty = row.querySelector<HTMLInputElement>('[data-k="qty"]');
    if (qty) {
        qty.value = bumpQty(qty.value);
        // 光标落数量框:扫完就能改数(整箱 24 支)。枪的下一发照旧收得到 —— 那个框声明了
        // data-enable-barcode="gun",楔子在框里也认枪(判据见 static/scan/scan-wedge.js)。
        // 但扫码框里还有字就别抢:那是「枪比网络快」—— 这一件的查码还在路上,下一发已经在
        // 往扫码框里打了,此刻抢焦点等于把后半串塞进数量格。真浏览器实测(查码 220ms):
        // 数量变成 167894 且照样提交得出去,而第二箱那个码一次都没查过 —— 整箱悄悄没了。
        // 楔子救不了这一档:扫码框没声明接枪,它在那里一个键都不收,拿不到前半串就无从还原。
        if (!scanBoxBusy()) qty.focus();
    }
    row.scrollIntoView({ block: 'nearest' });
    setMsg('ok', hitMsg(plan.kind, before, hit, name));
    showScanSuccessVisual({ label: name, imageUrl: product.image_url, target: row });
    // 这个码这次真进单了(多半是建完品回来重扫)→ 它那条待办到此为止
    resolveFail(part('msg'), code);
}

// ── 判成「人在打字」的那一发 ──────────────────────────────────────────
// 楔子判不出是枪打的就交还给人:不回调、不动框里的内容。屏上于是什么都没有 —— 三轮实测
// 正是这样,第二箱整箱从收货单消失,消息还停在上一件的「已加入」,店员以为枪没响再扫一次。
// 所以这一发也要落成一句状态。它不是错误(店员多半真的在打字),故走最弱的 tip 档、只占
// 瞬时行;真是慢枪扫的那一发,店员点一下就能补回来。
function onTyped(code: string, target: EventTarget | null, info: WedgeBurst): void {
    if (!active) return;
    const el = target as HTMLInputElement | null;
    typed = { code, el: el && typeof el.value === 'string' ? el : null, before: info.before };
    setMsg('tip', typedHtml(code));
}

// 店员说「这一串确实是扫的」:先把框还原成这一串开始前的样子,再当条码查。
// 不还原 = 那串码留在数量框里跟着整张收货单提交(数量 8850999320014)。
function useTyped(code: string): void {
    const pending = typed;
    typed = null;
    if (pending && pending.code === code && pending.el) pending.el.value = pending.before || '';
    clearMsg();
    enqueue(code);
}

// ── 装配 ──────────────────────────────────────────────────────────────
// 带码建品必须【叠在本弹窗之上】:跳走会把半张入库单连行一起丢掉。建完回来再扫一次即命中,
// 不做回调链。桥没接上或它自己说打不开(返回非 true)时不假装成功,由调用方给诚实回落。
function openCreateForm(code: string): boolean {
    const open = (window as unknown as ProductFormBridge).openProductFormWithBarcode;
    return typeof open === 'function' && open(code, { overlay: true }) === true;
}

function onMsgClick(ev: MouseEvent): void {
    const el = (ev.target as HTMLElement | null)?.closest<HTMLElement>(
        '[data-scan-create],[data-scan-retry],[data-scan-manual],[data-scan-ack],[data-scan-typed],[data-scan-dup]'
    );
    if (!el) return;
    if (el.dataset.scanRetry) {
        retryCamera(camHost());
        return;
    }
    if (el.dataset.scanTyped) {
        useTyped(el.dataset.scanTyped);
        return;
    }
    // 「是第二件」:走跟真扫一次完全相同的那条路(查码 → 落行),不在这里另写一套加数量 ——
    // 另写一套就会漏掉批次品另起一行、箱码带单位这些落行规矩。
    // 先销后查:这一行的账由店员这一下结掉(resolveFail 已经不再碰它),留着它等回包等于
    // 同一颗按钮可以被连点两下,收货单上凭空多一件。真落行失败的话那条路自己会挂一行。
    if (el.dataset.scanDup) {
        dropFail(part('msg'), el.dataset.scanDup);
        enqueue(el.dataset.scanDup);
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
    typed = null;
    resetFeedback();

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

    // 弹窗开着时独占楔子:枪扫的码不该漏进底下的库存页。收到什么就查什么 —— 落在行内框里
    // 的那几发,楔子已经判过是枪打的并把框还原了(见 WedgeApi 上面那段)。
    const gun = wedgeApi();
    if (gun) active.offWedge = gun.register((code) => enqueue(code), { exclusive: true, onTyped });

    const blocked = cameraBlockedReason();
    if (blocked) {
        if (btn) btn.disabled = true;
        setMsg('warn', blockedText(blocked));
    }
}

export function unmountInvScan(): void {
    if (!active) return;
    if (active.offWedge) active.offWedge();
    // 不放就是相机灯一直亮着、别的应用再也打不开相机
    releaseCamera();
    // 这轮收货结束 = 那几条「没落地的码」的事也结束了(DOM 本来就要被清掉,状态得跟着走)
    resetFeedback();
    // 那个框跟着弹窗一起没了,留着引用只会让下一轮把值写进一个已经不在页面上的元素
    typed = null;
    active = null;
}
