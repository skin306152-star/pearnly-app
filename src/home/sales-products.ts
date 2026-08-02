// 销项 PO-10 · 商品管理(主数据 · 共享 · 以后 POS/库存复用)
// 接真接口 GET/POST/PATCH/DELETE /api/sales/products + /import。四态 + .modal(非抽屉)。
/* global t, escapeHtml, apiGet, apiPost, showToast */
import {
    salesFetch,
    fmtMoney,
    htmlVal,
    imageFieldHtml,
    bindImageField,
    loadAuthedImg,
    salesErrMsg,
    IC_X,
} from './sales-common.js';
import {
    barcodeConflictText,
    barcodeFieldHtml,
    bindBarcodeField,
    productLabel,
    registerProductFormOpener,
    releaseBarcodeField,
    settleBarcodeCheck,
    takePendingBarcode,
} from './sales-products-scan.js';

export interface Product {
    id: string;
    code?: string;
    barcode?: string;
    name_th?: string;
    name_en?: string;
    name_zh?: string;
    unit?: string;
    // null = 没设过价(≠ 免费)· 收银台靠这个区分「忘了填」和「真的 ฿ 0」,见 pos-cashier.priced
    unit_price: number | null;
    vat_applicable: boolean;
    track_batch?: boolean;
    image_url?: string;
}

const IC_BOX =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 8 12 3 3 8l9 5 9-5ZM3 8v8l9 5 9-5V8"/></svg>';
const IC_EDIT =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M11 4H4v16h16v-7M18.5 2.5a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>';
const IC_TRASH =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>';

let products: Product[] = [];
let keyword = '';
let searchTimer: number | undefined;

function ensureMask(id: string): HTMLElement {
    let m = document.getElementById(id);
    if (!m) {
        m = document.createElement('div');
        m.id = id;
        m.className = 'modal-mask sx-modal-mask';
        m.style.display = 'none';
        document.body.appendChild(m);
    }
    return m;
}
function closeMask(id: string) {
    const m = document.getElementById(id);
    if (m) {
        m.style.display = 'none';
        m.innerHTML = '';
    }
}

function rowsHtml(): string {
    const list = products;
    if (!list.length)
        return `<tr><td colspan="7"><div class="sx-state">${escapeHtml(t('sx-products-empty'))}</div></td></tr>`;
    return list
        .map((p) => {
            const name = productLabel(p);
            const img = p.image_url
                ? `<img data-aimg="${escapeHtml(p.image_url)}" alt="" style="width:34px;height:34px;border-radius:7px;object-fit:cover">`
                : `<div class="sx-thumb">${IC_BOX}</div>`;
            return `<tr>
                <td>${img}</td>
                <td style="color:var(--ink-3)">${escapeHtml(p.code || '—')}</td>
                <td><b>${escapeHtml(name)}</b></td>
                <td>${escapeHtml(p.unit || '—')}</td>
                <td class="r">${p.unit_price == null ? escapeHtml(t('sx-p-noprice')) : fmtMoney(p.unit_price)}</td>
                <td>${p.vat_applicable ? '<span class="sx-badge issued">7%</span>' : '<span class="sx-badge draft">—</span>'}</td>
                <td class="r"><button class="sx-chev" data-edit="${escapeHtml(p.id)}">${IC_EDIT}</button><button class="sx-chev" data-del="${escapeHtml(p.id)}">${IC_TRASH}</button></td>
            </tr>`;
        })
        .join('');
}

function listHtml(): string {
    return `<div class="sx-toolbar">
        <div class="sx-search"><input type="text" id="sx-p-search" value="${escapeHtml(keyword)}" placeholder="${escapeHtml(t('sx-p-search-ph'))}"></div>
        <button class="btn btn-ghost" id="sx-p-import">${escapeHtml(t('sx-p-import'))}</button>
        <button class="btn btn-primary" id="sx-p-add">${escapeHtml(t('sx-p-add'))}</button>
    </div>
    <div class="sx-panel"><table class="sx-tbl">
        <thead><tr>
            <th>${escapeHtml(t('sx-p-col-img'))}</th><th>${escapeHtml(t('sx-p-col-code'))}</th>
            <th>${escapeHtml(t('sx-p-col-name'))}</th><th>${escapeHtml(t('sx-p-col-unit'))}</th>
            <th class="r">${escapeHtml(t('sx-p-col-price'))}</th><th>${escapeHtml(t('sx-p-col-vat'))}</th><th></th>
        </tr></thead>
        <tbody id="sx-p-tbody">${rowsHtml()}</tbody>
    </table></div>`;
}

function renderBody(html: string) {
    const body = document.getElementById('sx-p-body');
    if (body) body.innerHTML = html;
}

function bindList() {
    const search = document.getElementById('sx-p-search') as HTMLInputElement | null;
    if (search)
        search.oninput = () => {
            keyword = search.value;
            clearTimeout(searchTimer);
            searchTimer = window.setTimeout(refreshRows, 250);
        };
    document.getElementById('sx-p-add')!.onclick = () => openEdit(null);
    document.getElementById('sx-p-import')!.onclick = openImport;
    bindRowActions();
}
function bindRowActions() {
    // 缩略图经鉴权取图(列表行的 <img> 不能直接 src 鉴权 URL,否则 401)。
    document.querySelectorAll<HTMLImageElement>('#sx-p-body [data-aimg]').forEach((im) => {
        void loadAuthedImg(im, im.dataset.aimg || '');
    });
    document.querySelectorAll<HTMLElement>('#sx-p-body [data-edit]').forEach((el) => {
        el.onclick = () => openEdit(products.find((p) => p.id === el.dataset.edit) || null);
    });
    document.querySelectorAll<HTMLElement>('#sx-p-body [data-del]').forEach((el) => {
        el.onclick = () => del(el.dataset.del!);
    });
}

// 关弹窗要连扫码那套一起收(相机 track / 条码枪独占订阅),漏一处 = 相机灯不灭、枪失灵。
function closeProdModal() {
    releaseBarcodeField();
    closeMask('sales-prod-mask');
}

// barcodePrefill:别处扫到未建档的码跳进来建品(见 sales-products-scan 的跨页带码)。
function openEdit(p: Product | null, barcodePrefill?: string) {
    const mask = ensureMask('sales-prod-mask');
    mask.innerHTML = `<div class="modal" role="dialog" style="max-width:560px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t(p ? 'sx-p-edit' : 'sx-p-new'))}</div>
            <button class="modal-close" id="sx-p-close">${IC_X}</button></div>
        <div class="modal-body">
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t('sx-p-f-code'))}</label><input type="text" id="sx-pf-code" value="${htmlVal(p?.code)}" maxlength="25"><div class="sx-field-hint">${escapeHtml(t('sx-p-f-code-hint'))}</div><div class="sx-field-err" id="sx-pf-code-err"></div></div>
                <div>${barcodeFieldHtml(p ? p.barcode : barcodePrefill)}</div>
            </div>
            <div class="form-row"><label>${escapeHtml(t('sx-p-f-name-th'))} *</label><input type="text" id="sx-pf-th" value="${htmlVal(p?.name_th)}" maxlength="100"><div class="sx-field-hint">${escapeHtml(t('sx-p-f-name-hint'))}</div></div>
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t('sx-p-f-name-en'))}</label><input type="text" id="sx-pf-en" value="${htmlVal(p?.name_en)}" maxlength="100"></div>
                <div><label>${escapeHtml(t('sx-p-f-name-zh'))}</label><input type="text" id="sx-pf-zh" value="${htmlVal(p?.name_zh)}" maxlength="100"></div>
            </div>
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t('sx-p-f-unit'))}</label><input type="text" id="sx-pf-unit" value="${htmlVal(p?.unit)}" maxlength="50"></div>
                <div><label>${escapeHtml(t('sx-p-f-price'))}</label><input type="number" id="sx-pf-price" value="${htmlVal(p?.unit_price)}" min="0" step="0.01"><div class="sx-field-hint">${escapeHtml(t('sx-p-f-price-hint'))}</div></div>
            </div>
            <div class="form-row"><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" id="sx-pf-vat" ${!p || p.vat_applicable ? 'checked' : ''} style="width:auto"> ${escapeHtml(t('sx-p-f-vat'))}</label></div>
            <div class="form-row"><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" id="sx-pf-batch" ${p && p.track_batch ? 'checked' : ''} style="width:auto"> ${escapeHtml(t('sx-p-f-batch'))}</label><div class="sx-field-hint">${escapeHtml(t('sx-p-f-batch-hint'))}</div></div>
            <div class="form-row">${imageFieldHtml('sx-pf-image', t('sx-p-f-image'), p?.image_url)}</div>
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-p-cancel">${escapeHtml(t('sx-cancel'))}</button>
            <button class="btn btn-primary" id="sx-p-save">${escapeHtml(t('sx-p-save'))}</button>
        </div></div>`;
    mask.style.display = 'flex';
    document.getElementById('sx-p-close')!.onclick = closeProdModal;
    document.getElementById('sx-p-cancel')!.onclick = closeProdModal;
    mask.onclick = (e) => {
        if (e.target === mask) closeProdModal();
    };
    document.getElementById('sx-p-save')!.onclick = () => save(p);
    bindImageField('sx-pf-image');
    // 撞码时「去编辑那个商品」= 换成那个商品的编辑态,不再多开一层弹窗。
    bindBarcodeField(p ? p.id : null, (other) => {
        closeProdModal();
        openEdit(other);
    });
}

// 价格留空发 null,不发 0:这个表单最常走的那条路就是抱着货只填个名字建档(扫到未建档的码
// → 「去建这个商品」)。发 0 的话后端存 0.00、收银台的零元闸看到「有值」就放行,整件货 ฿ 0
// 进车、฿ 0 出门,小票/日结/报表全看着正常。null 才让「没设过价」和「真的免费」分得开。
// 人自己打的 0 照样发 0 —— 那是人做的决定,小票上看得见;这里堵的是系统替人编出来的价。
function priceOrNull(raw: string): number | null {
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
}

function readForm() {
    const val = (id: string) => (document.getElementById(id) as HTMLInputElement).value.trim();
    return {
        name_th: val('sx-pf-th'),
        // 清空 = 发 null,且每次都把全部键发齐:PATCH 那侧按 exclude_unset 分「这次没改」与
        // 「改成空」(routes.products_routes._patch_fields),键不发出去就等于没改 —— 清空条码
        // 会静默变成不改还回 ok:true,回去存另一件货照旧撞码,人没有出路。
        code: val('sx-pf-code') || null,
        barcode: val('sx-pf-barcode') || null,
        name_en: val('sx-pf-en') || null,
        name_zh: val('sx-pf-zh') || null,
        unit: val('sx-pf-unit') || null,
        unit_price: priceOrNull(val('sx-pf-price')),
        vat_applicable: (document.getElementById('sx-pf-vat') as HTMLInputElement).checked,
        track_batch: (document.getElementById('sx-pf-batch') as HTMLInputElement).checked,
        image_url: val('sx-pf-image') || null,
    };
}

async function failMsg(r: Response, fallbackKey: string): Promise<string> {
    const d = await r.json().catch(() => ({}));
    return salesErrMsg(d && d.detail, fallbackKey);
}

function setCodeErr(msg: string) {
    const el = document.getElementById('sx-pf-code-err');
    if (el) el.textContent = msg;
}

// 查重要几百毫秒:这段时间保存键必须说清自己在等什么,并且点不动(不然连点两下就是两条商品)。
async function withSaveBusy<T>(job: () => Promise<T>): Promise<T> {
    const btn = document.getElementById('sx-p-save') as HTMLButtonElement | null;
    if (btn) {
        btn.disabled = true;
        btn.textContent = t('sx-p-bc-checking');
    }
    try {
        return await job();
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = t('sx-p-save');
        }
    }
}

async function save(p: Product | null) {
    const payload = readForm();
    setCodeErr('');
    if (!payload.name_th) return showToast(t('sx-p-name-required'), 'error');
    // 撞码不许存:同一个码落两个商品,POS 扫出来永远是先建的那个,收银员在台前分辨不了。
    // 查重是异步的,不等它落定就等于「贴上码立刻点保存」能绕过去 —— settleBarcodeCheck 会把
    // 在飞的推完/没查过的现查。只有真查到别的商品才拦(查不了 ≠ 撞码,不凭一次网络失败拦人)。
    const dup = await withSaveBusy(settleBarcodeCheck);
    if (dup) {
        // 状态行同时画出「去编辑那个商品」那条出路,焦点挪回条码框让它进视野
        showToast(barcodeConflictText(), 'error');
        document.getElementById('sx-pf-barcode')?.focus();
        return;
    }
    const url = p ? `/api/sales/products/${p.id}` : '/api/sales/products';
    try {
        const r = await salesFetch(url, {
            method: p ? 'PATCH' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!r.ok) {
            const d = await r.json().catch(() => ({}));
            const detail = d && d.detail ? String(d.detail) : 'HTTP ' + r.status;
            // 编码重复 → 标在「编码」框旁(红字),不弹系统错误
            if (detail === 'sales.product_code_exists') {
                setCodeErr(t('sales.product_code_exists'));
                (document.getElementById('sx-pf-code') as HTMLInputElement)?.focus();
                return;
            }
            showToast(salesErrMsg(detail, 'sx-p-save-fail'), 'error');
            return;
        }
        closeProdModal();
        showToast(t('sx-p-saved'), 'success');
        await load();
    } catch (_) {
        showToast(t('sx-p-save-fail'), 'error');
    }
}

async function del(id: string) {
    if (window.pearnlyConfirm) {
        const ok = await window.pearnlyConfirm(t('sx-p-del-confirm'));
        if (!ok) return;
    } else if (!confirm(t('sx-p-del-confirm'))) return;
    try {
        const r = await salesFetch(`/api/sales/products/${id}`, { method: 'DELETE' });
        if (!r.ok) {
            showToast(await failMsg(r, 'sx-p-del-fail'), 'error');
            return;
        }
        showToast(t('sx-p-deleted'), 'success');
        await load();
    } catch (_) {
        showToast(t('sx-p-del-fail'), 'error');
    }
}

function openImport() {
    // 两个弹窗共用一张 mask:导入把建品表单的 DOM 覆盖掉,但条码枪的独占订阅不会自己退,
    // 不在这里收掉就会永久截走全站的枪输入。
    releaseBarcodeField();
    const mask = ensureMask('sales-prod-mask');
    mask.innerHTML = `<div class="modal" role="dialog" style="max-width:480px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t('sx-p-import-title'))}</div>
            <button class="modal-close" id="sx-imp-close">${IC_X}</button></div>
        <div class="modal-body">
            <input type="file" id="sx-imp-file" accept=".xlsx,.xls" style="width:100%">
            <div class="sx-banner" style="margin-top:10px">${escapeHtml(t('sx-p-import-hint'))}</div>
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-imp-cancel">${escapeHtml(t('sx-cancel'))}</button>
            <button class="btn btn-primary" id="sx-imp-go">${escapeHtml(t('sx-p-import-go'))}</button>
        </div></div>`;
    mask.style.display = 'flex';
    document.getElementById('sx-imp-close')!.onclick = () => closeMask('sales-prod-mask');
    document.getElementById('sx-imp-cancel')!.onclick = () => closeMask('sales-prod-mask');
    document.getElementById('sx-imp-go')!.onclick = doImport;
}
async function doImport() {
    const f = (document.getElementById('sx-imp-file') as HTMLInputElement).files?.[0];
    if (!f) return showToast(t('sx-p-import-pick'), 'error');
    const fd = new FormData();
    fd.append('file', f);
    try {
        const r = await salesFetch('/api/sales/products/import', { method: 'POST', body: fd });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error();
        closeMask('sales-prod-mask');
        showToast(
            t('sx-p-import-done').replace('{n}', String(data.created ?? data.imported ?? 0)),
            'success'
        );
        await load();
    } catch (_) {
        showToast(t('sx-p-import-fail'), 'error');
    }
}

// 服务端搜索:GET /api/sales/products?q=(后端按 code/barcode/名称匹配)。空关键词取全量。
async function fetchProducts(): Promise<Product[]> {
    const kw = keyword.trim();
    const url = '/api/sales/products' + (kw ? '?q=' + encodeURIComponent(kw) : '');
    const data = await apiGet(url);
    return (data && (data.products as Product[])) || [];
}

// 搜索输入触发:只换 tbody(不重渲整个列表 → 不丢输入框焦点/光标)。
async function refreshRows() {
    try {
        products = await fetchProducts();
    } catch (_) {
        return;
    }
    const tb = document.getElementById('sx-p-tbody');
    if (tb) tb.innerHTML = rowsHtml();
    bindRowActions();
}

async function load() {
    // 建品表单可能是叠在别的屏上开的(入库单扫到未建档的码),那时商品页根本没挂载:再去重画
    // 列表会在 bindList 里撞上不存在的按钮抛错,把一次成功的保存显示成「保存失败」。
    if (!document.getElementById('sx-p-body')) return;
    renderBody(`<div class="sx-state">${escapeHtml(t('sx-loading'))}</div>`);
    try {
        products = await fetchProducts();
        renderBody(listHtml());
        bindList();
    } catch (_) {
        renderBody(
            `<div class="sx-state error">${escapeHtml(t('sx-error'))}<br><button class="btn btn-ghost" id="sx-p-retry">${escapeHtml(t('sx-retry'))}</button></div>`
        );
        const retry = document.getElementById('sx-p-retry');
        if (retry) retry.onclick = () => load();
    }
}

// 别处扫到未建档的码 → window.openProductFormWithBarcode(code, {overlay:true}) 把建品表单叠在
// 调用方自己的弹窗之上(入库单跳页就会连半张单一起丢)。桥挂在扫码模块上,开表单的手在这里;
// 反向 import 会成环,所以开机把手注册过去。
registerProductFormOpener((code) => {
    openEdit(null, code);
    // 真开出来了才回 true:调用方靠它决定要不要显示「先去商品数据页建品」的诚实回落文案
    const mask = document.getElementById('sales-prod-mask');
    return !!mask && mask.style.display === 'flex';
});

window.loadSalesProducts = function () {
    const sec = document.getElementById('page-sales-products');
    if (!sec) return;
    if (sec.dataset.sxInit !== '1') {
        sec.innerHTML = `<div class="sx-page"><div class="sx-head"><h2>${escapeHtml(t('nav-sales-products'))}</h2></div><div id="sx-p-body"></div></div>`;
        sec.dataset.sxInit = '1';
    }
    // 别处扫到未建档的码跳进来 → 列表就绪后直接开新建表单,码已填好(等 load 是为了让
    // 「去编辑那个商品」拿得到最新列表,不是表单本身要等)。
    void load().then(() => {
        const code = takePendingBarcode();
        if (code) openEdit(null, code);
    });
};

// 切账套重载已统一收口到 core-boot 全局 pearnly:workspace-changed → reloadCurrentRoute。
