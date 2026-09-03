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
import { showScanSuccessVisual } from './scan-success-visual.js';
import { productDisplayName } from './product-names.js';
import {
    NO_CAMERA_KEY,
    closeScanModal,
    openScanModal,
    scanUnsupportedReason,
} from './sales-products-scan-cam.js';
import type { Product } from './sales-products.js';

// 「这一发是枪打的还是人打的」不在这里判 —— 判据只有一份,在楔子里(见 static/scan/
// scan-wedge.js 文件头)。这一层拿到回调就是拿到结论。判成「人在打字」的那一发楔子也说一声
// (onTyped),那一路不是第二个判据,只负责让屏上有字。
interface ScanWedge {
    register(
        cb: (code: string, target: EventTarget | null) => void,
        opts?: {
            exclusive?: boolean;
            onTyped?: (code: string, target: EventTarget | null) => void;
        }
    ): () => void;
}

function wedge(): ScanWedge | null {
    return (window as unknown as { PearnlyScanWedge?: ScanWedge }).PearnlyScanWedge || null;
}

const INPUT_ID = 'sx-pf-barcode'; // 沿用既有 id:readForm() 仍按它取值
const STATE_ID = 'sx-pf-bc-state';
const SCAN_BTN_ID = 'sx-pf-bc-scan';

// 楔子的下限,这里再挡一道:相机那条路不经过楔子,别人改了那边不至于漏进来。
const MIN_CODE_LEN = 3;

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

// 与 acct-common.ts 的 injectStyle 同形。收成一处要连 tests/unit 的 node harness 一起改
// (它 stub 掉 acct-common,现在直接 import 会 TypeError),不是纯替换 —— 见交接单。
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
// typed = 楔子把这一发交还给人了(慢枪与人手在 50~100ms 这一段是叠着的,引擎宁可判人)。
// 它必须自成一档:那串字符已经落在框里跟旧码接成了一条新串,而查重照旧会去问那条串,
// 回一句绿色的「没人用这个码」—— 店员照着那句话点保存,落库的条码 POS 永远扫不出来。
type CheckState = 'idle' | 'checking' | 'free' | 'self' | 'dup' | 'error' | 'typed';

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
// 被判成打字的那一串 + 它落进来之前框里是什么(点「当条码用」时按它还原)
let typedBurst: { code: string; before: string } | null = null;

export function productLabel(p: { name_th?: string; name_en?: string; name_zh?: string }): string {
    return productDisplayName(p);
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

function formValue(id: string): string {
    return (document.getElementById(id) as HTMLInputElement | null)?.value.trim() || '';
}

function showCodeAccepted(code: string): void {
    const label = formValue('sx-pf-th') || formValue('sx-pf-en') || formValue('sx-pf-zh') || code;
    showScanSuccessVisual({
        label,
        imageUrl: formValue('sx-pf-image'),
        target: inputEl(),
        increment: false,
    });
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
    if (checkState === 'typed') {
        const code = typedBurst ? typedBurst.code : '';
        // 文案与入库侧共用一份(同一件事,两个屏上不能有两种说法)
        el.innerHTML =
            `<div class="sx-bc-warn">${escapeHtml(t('inv-scan-typed'))}` +
            `<b class="tnum">${escapeHtml(code)}</b>` +
            `<button type="button" class="sx-bc-link" data-scan-typed="${escapeHtml(code)}" id="sx-bc-usetyped">${escapeHtml(t('inv-scan-typed-use'))}</button></div>`;
        const use = document.getElementById('sx-bc-usetyped');
        if (use) use.onclick = () => useTypedBurst();
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
async function runCheck(code: string, scanned = false): Promise<void> {
    const seq = ++checkSeq;
    if (!code) {
        hitProduct = null;
        hitUnit = '';
        checkState = 'idle';
        renderState();
        return;
    }
    checkState = typedBurst ? 'typed' : 'checking';
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
    // 只压住绿字那一档:框里是「旧码 + 刚判成打字的那一串」时,说它「没人用」等于替一串
    // 不是码的东西背书。撞码与查不了照旧显示 —— 那两档压下去就是把硬拦路藏起来了。
    checkState = typedBurst && next === 'free' ? 'typed' : next;
    renderState();
    if (scanned && (checkState === 'free' || checkState === 'self')) showCodeAccepted(code);
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

// 框里每落进一个字符走一次手打的防抖查重。枪扫也会一个个落进来,但楔子最迟 150ms 收尾,
// 早于这里的 400ms —— 半截码的查重发不出去,整串到齐后由 applyCode 直接查。
function onFieldInput(): void {
    clearTimeout(checkTimer);
    typedBurst = null; // 店员自己动过框了 —— 那条回路指的已经不是框里这串东西
    const code = inputEl()?.value.trim() || '';
    if (!code) {
        void runCheck('');
        return;
    }
    checkTimer = window.setTimeout(() => void runCheck(code), 400);
}

/**
 * 扫到 / 枪打到一个码:整框写进去 + 立刻查(不走手打的防抖,一整串已经到齐了)。
 *
 * 这里不再判「这一发是枪还是人」。光标在条码框里时字符确实先落进了框,但那个框声明的是
 * data-enable-barcode="gun":人手打的楔子根本不发过来,发过来的它已经先把框还原成扫之前的
 * 样子。三轮里「新码接在旧码后面凑成 26 位、绿字还说没人用这个码」那条路死在这一步 ——
 * 覆盖时框里是旧值本身,不是「旧值 + 刚落进来的一串」。
 */
function applyCode(raw: string): void {
    const code = String(raw || '').trim();
    const input = inputEl();
    if (!input || code.length < MIN_CODE_LEN) return;
    closeScanModal();
    typedBurst = null;
    input.value = code;
    input.focus();
    clearTimeout(checkTimer);
    void runCheck(code, true);
}

/**
 * 楔子把这一发交还给人了(见 static/scan/scan-wedge.js 的 onTyped)。
 *
 * 只在【框里本来就有东西】时出声。落进空框的那一串,框里的值就等于那个码本身,没有歧义,
 * 再弹一句提示只是噪音;而接在旧码后面的那一串是另一回事:框里成了一条 26 位的东西,
 * 400ms 的防抖照旧拿它去查重,回一句绿色的「没人用这个码」—— 屏上每一处都在说「可以存」,
 * 落库之后 POS 永远扫不出这件货。所以这一档要摆出来 + 给一条一点就补回来的路。
 */
function onTyped(code: string, target: EventTarget | null): void {
    const input = inputEl();
    const el = target as HTMLInputElement | null;
    if (!input || el !== input || code.length < MIN_CODE_LEN) return;
    // before 由这一层自己算:楔子交还的那一串原封不动挂在框尾
    const now = input.value;
    const before = now.endsWith(code) ? now.slice(0, -code.length) : now;
    if (!before) return;
    typedBurst = { code, before };
    checkState = 'typed';
    renderState();
}

/** 店员说「这一串确实是扫的」:框先还原成这一发之前的样子,再整框按条码走。 */
function useTypedBurst(): void {
    const pending = typedBurst;
    const input = inputEl();
    if (!pending || !input) return;
    input.value = pending.before;
    applyCode(pending.code);
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
            <input type="text" id="${INPUT_ID}" value="${htmlVal(barcode)}" maxlength="100" autocomplete="off" data-enable-barcode="gun">
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
    // 相机扫到的码整框写进去;「手动输入」把焦点还回来。
    if (btn)
        btn.onclick = () =>
            openScanModal(
                (code) => applyCode(code),
                () => inputEl()?.focus()
            );
    const input = inputEl();
    if (input) input.oninput = onFieldInput;
    // 独占:建品弹窗开着时,枪扫到的码只该落进这个框,底下页面的订阅者不该也吃一份。
    wedgeOff = wedge()?.register((code) => applyCode(code), { exclusive: true, onTyped }) || null;
    // 带码进来的(别处扫到未建档)立刻查一次:它正是最该当场拦的撞码场景。
    const prefilled = input?.value.trim() || '';
    if (prefilled) void runCheck(prefilled);
}

// 关弹窗必须调:漏了 = 相机灯一直亮着(track 没停)+ 条码枪被独占订阅者永久截走。
export function releaseBarcodeField(): void {
    closeScanModal();
    clearTimeout(checkTimer);
    checkSeq++;
    typedBurst = null;
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
