// 销项 PO-10 · 建品表单条码位:扫码填码 + 撞码当场拦(拆自 sales-products.ts · 控行数)
//
// 扫一个条形码只能得到那串数字,带不出商品名和价格(Odoo 社区版空态写了 "Scan a barcode
// to create automatically",实际也没实现)。所以这一层的价值只有两条,文案上照实说:
//   1. 免手抄 13 位数字 —— 手打错一位当场没有任何报错,要等到收银台扫不出这件货才发现;
//   2. 撞码当场拦 —— 同一个码落在两个商品上,POS 扫出来永远是先建的那个,收银员在台前
//      没有任何办法分辨,只能回后台改。故查重命中一律拦住保存,并给「去编辑那个商品」的出路。
//
// 摄像头与条码枪都用共享地基(static/scan/*):首屏只有能力探针,真开相机才懒加载解码器。
// 相机弹窗那一段在 sales-products-scan-cam.ts。
/* global t, escapeHtml */
import { salesFetch, htmlVal } from './sales-common.js';
import {
    NO_CAMERA_KEY,
    closeScanModal,
    openScanModal,
    scanUnsupportedReason,
} from './sales-products-scan-cam.js';
import type { Product } from './sales-products.js';

interface ScanWedge {
    register(
        cb: (code: string, target: EventTarget | null) => void,
        opts?: { exclusive?: boolean }
    ): () => void;
    // 速度尺子:枪 ≤GUN_MAX_GAP_MS/字符,超过 MAX_GAP_MS 就算另起一串(见 static/scan/scan-wedge.js)
    GUN_MAX_GAP_MS?: number;
    MAX_GAP_MS?: number;
}

function wedge(): ScanWedge | null {
    return (window as unknown as { PearnlyScanWedge?: ScanWedge }).PearnlyScanWedge || null;
}

// 楔子在没挂上时(首屏 JS 还没到)也得有个尺子;数值以楔子那份为准,这里只是回落。
function gapMs(name: 'GUN_MAX_GAP_MS' | 'MAX_GAP_MS', fallback: number): number {
    const v = wedge()?.[name];
    return typeof v === 'number' && v > 0 ? v : fallback;
}

const INPUT_ID = 'sx-pf-barcode'; // 沿用既有 id:readForm() 仍按它取值
const STATE_ID = 'sx-pf-bc-state';
const SCAN_BTN_ID = 'sx-pf-bc-scan';

// 零售条码最短是 EAN-8/UPC-E 的 8 位。跟 inventory-scan.ts 同一个尺子,别一处 8 一处没有。
const MIN_LEN_IN_FIELD = 8;

const IC_SCAN =
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/><path d="M7 8v8M10 8v8M13.5 8v8M17 8v8"/></svg>';

const STYLE = `
.sx-bc-row{display:flex;gap:8px;align-items:center;}
.sx-bc-row input{flex:1;}
.sx-bc-btn{flex:none;width:42px;height:38px;display:flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink-2);cursor:pointer;}
.sx-bc-btn:hover{border-color:var(--accent);color:var(--accent);}
.sx-bc-state{margin-top:6px;font-size:11.5px;}
.sx-bc-wait{color:var(--ink-3);}
.sx-bc-ok{color:var(--green);}
.sx-bc-warn{display:flex;flex-wrap:wrap;align-items:center;gap:8px;background:var(--amber-weak);color:var(--amber);border-radius:8px;padding:8px 10px;font-size:12px;}
.sx-bc-warn.dup{background:var(--red-weak);color:var(--red);}
.sx-bc-link{border:0;padding:0;background:transparent;color:inherit;font-size:12px;font-weight:700;text-decoration:underline;cursor:pointer;}
`;

function ensureStyle(): void {
    if (document.getElementById('sx-bc-style')) return;
    const st = document.createElement('style');
    st.id = 'sx-bc-style';
    st.textContent = STYLE;
    document.head.appendChild(st);
}

// ── 跨页带码 ────────────────────────────────────────────────────────────
// routeTo 把 hash 重写成 #/route,URL 参数放不住 → 走内存交接,同 openPurchaseDetail 的
// pendingId 范式。取一次即清,否则下次进商品页会莫名再弹一次带旧码的表单。
// 只服务同文档的调用方;POS 是另一个文档,它扫到未建档的码时给的是「去商品数据建」的指路
// 文案(posui.bscan.create_where),不带码过来。
let pendingBarcode = '';

export function takePendingBarcode(): string {
    const code = pendingBarcode;
    pendingBarcode = '';
    return code.trim();
}

// 建品表单归 sales-products.ts,它 import 本模块;反向 import 会成环,故由它开机时把开表单的
// 那只手注册进来。没注册 = 桥打不开表单,如实返回 false 让调用方回落。
type FormOpener = (code: string) => boolean;
let formOpener: FormOpener | null = null;

export function registerProductFormOpener(open: FormOpener): void {
    formOpener = open;
}

/**
 * 别处扫到一个没建档的码 → 开建品表单并把码填好。
 *
 * opts.overlay=true:叠在调用方自己的弹窗之上开(入库单扫到未建档的货就是这条路)。
 *   跳页会把半张入库单连行一起丢掉,而建品弹窗是 .modal-mask(z-index 10000)、入库弹窗是
 *   .inv-modal-mask(1200),原地叠上去就行,不必先离开当前屏。
 * 省略 / false:跳到商品数据页再开表单(调用方本来就要离开当前屏时走这条)。
 *
 * 返回 true 才表示表单真的开出来了 —— 调用方靠这个决定要不要显示诚实回落文案,
 * 所以这里绝不能不管三七二十一返回 true。
 */
function openFormWithBarcode(code: unknown, opts?: { overlay?: boolean }): boolean {
    const clean = String(code || '').trim();
    if (!clean) return false;
    if (opts && opts.overlay) return formOpener ? formOpener(clean) : false;
    if (typeof window.routeTo !== 'function') return false;
    pendingBarcode = clean;
    window.routeTo('sales-products');
    return true;
}

(
    window as unknown as {
        openProductFormWithBarcode?: (code: string, opts?: { overlay?: boolean }) => boolean;
    }
).openProductFormWithBarcode = openFormWithBarcode;

// ── 撞码检查 ────────────────────────────────────────────────────────────
type CheckState = 'idle' | 'checking' | 'free' | 'self' | 'dup' | 'error';

// GET /api/sales/products/lookup 的信封(routes/products_routes.py::api_lookup_product)。
// 字段名照后端那三个写,别自创:曾经这里读的是 d.unit.unit_name,后端从来没发过这个形状,
// 于是单位码那句话一次都没显示过 —— 而它正是「绿字说没人用、POS 却扫到别的商品」那条路。
interface LookupEnvelope {
    product?: Product;
    matched_by?: string;
    matched_unit?: string | null;
}

let checkState: CheckState = 'idle';
let hitProduct: Product | null = null;
// 命中的是「瓶/箱」这类单位码时的单位名。POS 的 by-barcode 先配 product_units.barcode 再配
// products.barcode,所以一个码可能不是主码而是别人的单位码 —— 只说「已经是某商品的了」会
// 让人以为看错了,得说清是主码还是哪个单位的码。
let hitUnit = '';
let checkTimer: number | undefined;
let checkSeq = 0;
let ownProductId: string | null = null;
let openOther: ((p: Product) => void) | null = null;
let wedgeOff: (() => void) | null = null;

export function productLabel(p: { name_th?: string; name_en?: string; name_zh?: string }): string {
    return p.name_th || p.name_en || p.name_zh || '—';
}

// 只在真查到别的商品时非空。「查不了」不算撞码 —— 凭一次网络失败拦住保存是撒谎。
export function barcodeConflict(): Product | null {
    return checkState === 'dup' ? hitProduct : null;
}

/** 撞码那句话(主码 / 某单位的码各一句)· 状态行与保存失败提示共用同一份措辞。 */
export function barcodeConflictText(): string {
    const dup = barcodeConflict();
    if (!dup) return '';
    const name = productLabel(dup);
    return hitUnit ? t('sx-p-bc-dup-unit', { name, unit: hitUnit }) : t('sx-p-bc-dup', { name });
}

function inputEl(): HTMLInputElement | null {
    return document.getElementById(INPUT_ID) as HTMLInputElement | null;
}

function renderState(): void {
    const el = document.getElementById(STATE_ID);
    if (!el) return;
    if (checkState === 'idle') {
        el.innerHTML = '';
        return;
    }
    if (checkState === 'checking') {
        el.innerHTML = `<span class="sx-bc-wait">${escapeHtml(t('sx-p-bc-checking'))}</span>`;
        return;
    }
    if (checkState === 'free' || checkState === 'self') {
        let line = t('sx-p-bc-free');
        if (checkState === 'self')
            line = hitUnit ? t('sx-p-bc-self-unit', { unit: hitUnit }) : t('sx-p-bc-self');
        el.innerHTML = `<span class="sx-bc-ok">${escapeHtml(line)}</span>`;
        return;
    }
    if (checkState === 'error') {
        el.innerHTML = `<div class="sx-bc-warn">${escapeHtml(t('sx-p-bc-check-fail'))}<button type="button" class="sx-bc-link" id="sx-bc-recheck">${escapeHtml(t('sx-p-bc-recheck'))}</button></div>`;
        const again = document.getElementById('sx-bc-recheck');
        if (again)
            again.onclick = () => {
                const code = inputEl()?.value.trim() || '';
                void runCheck(code);
            };
        return;
    }
    el.innerHTML = `<div class="sx-bc-warn dup">${escapeHtml(barcodeConflictText())}<button type="button" class="sx-bc-link" id="sx-bc-goedit">${escapeHtml(t('sx-p-bc-dup-open'))}</button></div>`;
    const go = document.getElementById('sx-bc-goedit');
    if (go)
        go.onclick = () => {
            const other = hitProduct;
            if (other && openOther) openOther(other);
        };
}

// 404 = 没有别的商品占这个码;网络/服务器错 ≠ 没撞码,必须说「查不了」并给重查按钮。
// 把查不了当放行,等于把撞码悄悄放过 —— 而撞码只有到收银台才暴露,那时改不了。
async function runCheck(code: string): Promise<void> {
    const seq = ++checkSeq;
    if (!code) {
        hitProduct = null;
        hitUnit = '';
        checkState = 'idle';
        renderState();
        return;
    }
    checkState = 'checking';
    hitProduct = null;
    hitUnit = '';
    renderState();
    let next: CheckState = 'error';
    let found: Product | null = null;
    let unit = '';
    try {
        const r = await salesFetch(
            '/api/sales/products/lookup?barcode=' + encodeURIComponent(code)
        );
        if (r.status === 404) next = 'free';
        else if (r.ok) {
            const d = (await r.json().catch(() => null)) as LookupEnvelope | null;
            const p = d && d.product;
            if (p && p.id) {
                found = p;
                // matched_by='unit' = 这码配在某个售卖单位上(箱码/瓶码),matched_unit 是单位名;
                // 配到商品主码时 matched_by='product' 且 matched_unit 为空。
                unit = (d.matched_by === 'unit' && d.matched_unit) || '';
                next = ownProductId !== null && p.id === ownProductId ? 'self' : 'dup';
            }
        }
    } catch (_) {
        next = 'error';
    }
    if (seq !== checkSeq) return; // 码又变了 / 弹窗已关:旧回包作废
    hitProduct = next === 'dup' ? found : null;
    hitUnit = next === 'dup' || next === 'self' ? unit : '';
    checkState = next;
    renderState();
}

/**
 * 保存前把查重推到落定,返回真撞上的那个商品(没撞 / 查不了都返回 null)。
 *
 * 查重本身是 400ms 防抖 + 异步:贴一个已被占用的码进来立刻点保存,防抖还没跑、状态还是
 * idle,只看 barcodeConflict() 就等于直接放行 —— 同一个码落两个商品,POS 扫出来永远是先建
 * 的那个(两条查询都是 LIMIT 1),收银员在台前分辨不了。所以这里一律现查一次:顺带把
 * 「表单开着的这几分钟里别人占了这个码」也盖住。查不了照旧不拦(见 barcodeConflict)。
 */
export async function settleBarcodeCheck(): Promise<Product | null> {
    clearTimeout(checkTimer);
    await runCheck(inputEl()?.value.trim() || '');
    return barcodeConflict();
}

// 框里每落进一个字符:先记速度(判枪/人手要用),再走手打的防抖查重。
function onFieldInput(): void {
    noteFieldChar();
    clearTimeout(checkTimer);
    const code = inputEl()?.value.trim() || '';
    if (!code) {
        void runCheck('');
        return;
    }
    checkTimer = window.setTimeout(() => void runCheck(code), 400);
}

// ── 落进条码框的那一发:枪打的还是人手打的 ─────────────────────────────
// 楔子的回调只给 (code, target),它内部算过的字符间隔没发出来,所以这里按同一套尺子自己量:
// 字符落进框会发 input 事件,记下相邻两次的间隔就够。只有全串跑到枪速才算枪扫。
let burstGap = 0; // 本串里最大的字符间隔
let burstChars = 0; // 本串已落进框的字符数
let burstAt = 0;

function resetBurst(): void {
    burstGap = 0;
    burstChars = 0;
}

function noteFieldChar(): void {
    const now = Date.now();
    const gap = burstChars ? now - burstAt : Infinity;
    burstAt = now;
    // 间隔超过 MAX_GAP_MS = 楔子已经把上一串收尾了,这里跟着另起一串
    if (gap > gapMs('MAX_GAP_MS', 150)) {
        burstGap = 0;
        burstChars = 1;
        return;
    }
    burstGap = Math.max(burstGap, gap);
    burstChars += 1;
}

/**
 * 这一发是枪扫吗 —— 整串都以枪速连着落进框才算。
 *
 * 人手进不到这个区间:键盘自动重复要按住 ~500ms 才起,那早被楔子按 MAX_GAP_MS 收尾了,
 * 凑不出一串全 ≤GUN_MAX_GAP_MS 的输入(与 scan-wedge 的 endKeyFromGun 同一个判据)。
 * burstChars 少于这串的位数 = 有一部分字符不是这一发打进来的(或压根没落进框),同样不算。
 *
 * 判错的方向是安全的:把真枪扫误判成人打,框里留的是枪刚敲进去的那串字符本身,只有
 * 「框里原本有旧码、要用扫码替换掉」这一种会退化成新旧相接 —— 看得见、当场能改。
 */
function burstIsGunSpeed(code: string): boolean {
    return burstChars >= code.length && burstGap <= gapMs('GUN_MAX_GAP_MS', 50);
}

/**
 * 楔子/相机送来一串码时,条码框最终该是什么值(null = 别动这个框)。
 *
 * fromField = 这串字符已经由浏览器落进条码框里了(楔子只吃 Enter/Tab,不吃字符)。这一档
 * 的整框覆盖只有一种正当用途:框里有旧码,扫一枪把它换掉。人在框里手打时楔子照样会按
 * 150ms 静默把输入切成碎片吐过来,拿碎片覆盖就把已经打好的位数吃掉了 —— 剩下的那截看着
 * 仍是个合法条码,存下去 POS 永远扫不出这件货,后台却一切正常。
 *
 * 位数、前缀都分不开这两者:手打 EAN-13 停一下,后半截 '999320014' 有 9 位、也不是框里
 * 那串的前缀。能分开的只有速度。
 * fromField=false(相机扫,或光标不在条码框里时枪扫)没有这个歧义:整框写进去。
 */
function scanFieldValue(code: string, fromField: boolean): string | null {
    if (code.length < 3) return null; // 楔子的下限;这里再挡一道,别人改了那边不至于漏进来
    if (!fromField) return code;
    if (code.length < MIN_LEN_IN_FIELD) return null;
    return burstIsGunSpeed(code) ? code : null;
}

// 扫到 / 枪打到一个码:填进框 + 立刻查(不走手打的防抖,一整串已经到齐了)。
function applyCode(raw: string, fromField = false): void {
    const code = String(raw || '').trim();
    const input = inputEl();
    if (!input) return;
    const next = scanFieldValue(code, fromField);
    if (next === null) return;
    closeScanModal();
    input.value = next;
    input.focus();
    resetBurst(); // 这一串已经被消费掉,别让它继续给下一发背书
    clearTimeout(checkTimer);
    void runCheck(next);
}

// 光标在条码框里时字符已经落进框了(这个框对枪 opt-in),这一发只能当碎片处置;光标在别处
// 时枪的按键被楔子截走,框里什么都没有,整串写进去。
function onWedge(code: string, target: EventTarget | null): void {
    applyCode(code, target === inputEl());
}

// ── 对外:条码位的 HTML + 接线 ──────────────────────────────────────────
export function barcodeFieldHtml(barcode?: string | null): string {
    const why = scanUnsupportedReason();
    const btn = why
        ? ''
        : `<button type="button" class="sx-bc-btn" id="${SCAN_BTN_ID}" title="${escapeHtml(t('sx-p-bc-scan'))}" aria-label="${escapeHtml(t('sx-p-bc-scan'))}">${IC_SCAN}</button>`;
    // 扫不了也要说清为什么,并指出条码枪/手输这两条路照旧能走。
    const why2 = why
        ? `<div class="sx-field-hint">${escapeHtml(t(NO_CAMERA_KEY[why] || 'bscan.err.unsupported'))} · ${escapeHtml(t('sx-p-bc-gun'))}</div>`
        : '';
    return `<label>${escapeHtml(t('sx-p-f-barcode'))}</label>
        <div class="sx-bc-row">
            <input type="text" id="${INPUT_ID}" value="${htmlVal(barcode)}" maxlength="100" autocomplete="off" data-enable-barcode>
            ${btn}
        </div>
        <div class="sx-field-hint">${escapeHtml(t('sx-p-bc-hint'))}</div>
        ${why2}
        <div class="sx-bc-state" id="${STATE_ID}"></div>`;
}

/**
 * @param productId 编辑态的商品 id(新建传 null)· 用它把「这码是自己的」跟撞别人区分开
 * @param onEditOther 撞码时「去编辑那个商品」的落点(由商品页提供,避免反向依赖)
 */
export function bindBarcodeField(
    productId: string | null,
    onEditOther: (p: Product) => void
): void {
    releaseBarcodeField();
    ensureStyle();
    ownProductId = productId;
    openOther = onEditOther;
    const btn = document.getElementById(SCAN_BTN_ID);
    // 相机扫到的码光标不在框里 → fromField=false,整框写进去;「手动输入」把焦点还回来。
    if (btn)
        btn.onclick = () =>
            openScanModal(
                (code) => applyCode(code),
                () => inputEl()?.focus()
            );
    resetBurst();
    const input = inputEl();
    if (input) input.oninput = onFieldInput;
    // 独占:建品弹窗开着时,枪扫到的码只该落进这个框,底下页面的订阅者不该也吃一份。
    wedgeOff = wedge()?.register(onWedge, { exclusive: true }) || null;
    // 带码进来的(别处扫到未建档)立刻查一次:它正是最该当场拦的撞码场景。
    const prefilled = input?.value.trim() || '';
    if (prefilled) void runCheck(prefilled);
}

// 关弹窗必须调:漏了 = 相机灯一直亮着(track 没停)+ 条码枪被独占订阅者永久截走。
export function releaseBarcodeField(): void {
    closeScanModal();
    clearTimeout(checkTimer);
    resetBurst();
    checkSeq++;
    if (wedgeOff) {
        wedgeOff();
        wedgeOff = null;
    }
    checkState = 'idle';
    hitProduct = null;
    hitUnit = '';
    ownProductId = null;
    openOther = null;
}
