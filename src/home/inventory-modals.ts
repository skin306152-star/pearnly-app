// POS 项目 · PO-A4 库存后台 · 入库 / 盘点弹窗
// 概念稿屏7 只画了列表;入库/盘点为「补交互」,用 .modal(D1 闸禁新增 .drawer),沿用 home-41 同套令牌。
// 接 04 §4:POST /api/inventory/in、POST /api/inventory/count(带 workspace_client_id)。表单四态:提交转圈 + inline 错误码本地化。
/* global t, escapeHtml, showToast */
import {
    invApi,
    activeWsId,
    invErrMsg,
    fmtQty,
    isSaneCost,
    isSaneExpiry,
    isSaneQty,
    type InLine,
    type CountLine,
} from './inventory-common.js';
import { mountInvScan, unmountInvScan } from './inventory-scan.js';
import { scanBarHtml } from './inventory-scan-ui.js';

const IC_X =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>';

let rowSeq = 0;

// 效期框上不写 max:实测(Chromium)一旦声明 max,① 店员逐段敲日期再也敲不出结果(年份段
// 提前跳段,后面几段全错位),② 同一串条码打进去会被夹成 0490-12-31 这种「四位年份、看着
// 正常」的值 —— 把一眼能认出的 49012 换成认不出的假日期,比不写还坏。年份由 isSaneExpiry
// 在提交前拦,扫码那一层则靠「框里不是个像样日期 = 机器打的」把码退回去。

// 扫码命中的商品可能不在列表缓存里:刚建完品(建品保存后 load() 因为库存页的 #sx-p-body
// 不在而直接 return,缓存一点没刷)、或列表正被搜索/筛选过滤着。查码应答里的 track_batch
// 是同一行数据的权威答案,记在这里,后面店员在下拉里切走再切回来,批号格照旧露得出来。
const scannedTrackBatch = new Map<string, boolean>();

function productOptions(): string {
    return invApi
        .products()
        .map((p) => `<option value="${escapeHtml(p.product_id)}">${escapeHtml(p.name)}</option>`)
        .join('');
}

function inRowHtml(): string {
    const id = 'invr-' + rowSeq++;
    // 批号/效期默认藏起来:只有选中的商品在商品资料里勾了「批次管理」才显(applyBatchVisibility)。
    // 普通百货不碰批次 → 货进散装桶、收银台直接可卖(否则批次桶货够不着 = 看得见卖不出)。
    // 四个可编辑框都带 data-enable-barcode="gun":楔子默认让开输入框,不声明 = 枪的下一发整发被吞。
    // 单价框漏声明过一次,真浏览器实测的后果:光标停在单价格时来一发枪,฿ 8850999320014/瓶
    // 原样提交、零查码、屏上零字 —— 库存估值与移动加权成本从此按万亿算,而架上件数是对的,
    // 谁也不会去看。
    // 声明的是「只收枪打的那种串」那一档 —— 人手在这三个框里打数量/批号/效期照旧归框自己,
    // 认成枪扫时楔子把框还原成扫之前的样子(判据与还原都在 static/scan/scan-wedge.js,
    // 使用方不再各判一遍)。档位值必须写全,scripts/check_scan_optin.py 盯着。
    // 数量旁边留一格入库单位:扫到箱码时这一行是「1 箱」不是「1 瓶」,单位随行提交给后端
    // 按 factor_to_base 换算(前端不自己乘)。手选商品时它空着,后端按基本单位落账。
    return `<div class="inv-frow" data-row="${id}">
        <select class="inv-field" data-k="product_id"><option value="">—</option>${productOptions()}</select>
        <span class="inv-qtycell">
            <input class="inv-field" data-k="qty" type="number" min="0" step="0.001" placeholder="0" data-enable-barcode="gun">
            <input type="hidden" data-k="unit_name">
            <span class="inv-runit" data-runit hidden></span>
        </span>
        <input class="inv-field" data-k="unit_cost" type="number" min="0" step="0.01" placeholder="0.00" data-enable-barcode="gun">
        <span class="inv-brow">
            <span class="inv-batchcell" data-batchcell style="display:none;gap:6px;align-items:center;flex:1">
                <span class="inv-blabel">${escapeHtml(t('inv-f-batch-exp'))}</span>
                <input class="inv-field" data-k="batch_no" placeholder="${escapeHtml(t('inv-f-batch'))}" data-enable-barcode="gun">
                <input class="inv-field" data-k="expiry_date" type="date" data-enable-barcode="gun">
            </span>
            <button type="button" class="inv-rowx" data-rowx="${id}" aria-label="${escapeHtml(t('inv-row-remove'))}">×</button>
        </span>
    </div>`;
}

function productById(id: string) {
    return invApi.products().find((p) => p.product_id === id) || null;
}

// 查码应答优先于列表缓存:缓存是上一次 /api/inventory/stock 的快照,可能比这件货还老。
function tracksBatch(id: string): boolean {
    const known = scannedTrackBatch.get(id);
    if (known !== undefined) return known;
    const prod = productById(id);
    return !!(prod && prod.track_batch);
}

// 选中商品后按是否批次品调整行:收货行显隐批号/效期(非批次品清空不发批号);
// 盘点行显隐并填充批次下拉(逐批盘:选具体批次单独对账,或「合计」走整品聚合)。
// scanned:扫码加行时由查码应答带过来的 track_batch(店员自己改下拉时没有,走 tracksBatch)。
function onProductChange(row: HTMLElement, scanned?: boolean) {
    const sel = row.querySelector<HTMLSelectElement>('[data-k="product_id"]');
    const id = sel ? sel.value : '';
    if (scanned !== undefined && id) scannedTrackBatch.set(id, scanned);
    const prod = id ? productById(id) : null;
    const isBatch = !!id && tracksBatch(id);

    const cell = row.querySelector<HTMLElement>('[data-batchcell]');
    if (cell) {
        cell.style.display = isBatch ? 'flex' : 'none';
        if (!isBatch)
            cell.querySelectorAll<HTMLInputElement>('input').forEach((i) => (i.value = ''));
    }

    const bsel = row.querySelector<HTMLSelectElement>('[data-batchsel]');
    if (bsel) {
        const batches = (isBatch && prod ? prod.batches : []).filter((b) => b.batch_id);
        bsel.innerHTML = batches.length
            ? `<option value="">${escapeHtml(t('inv-count-all-batches'))}</option>` +
              batches
                  .map(
                      (b) =>
                          `<option value="${escapeHtml(b.batch_id!)}">${escapeHtml(
                              (b.batch_no || '—') + ' · ' + t('inv-count-onhand') + fmtQty(b.qty)
                          )}</option>`
                  )
                  .join('')
            : '';
        bsel.style.display = batches.length ? '' : 'none';
    }
}

function bindProductChange(maskId: string) {
    const mask = document.getElementById(maskId);
    if (!mask) return;
    mask.querySelectorAll<HTMLElement>('[data-row]').forEach((row) => {
        const sel = row.querySelector<HTMLSelectElement>('[data-k="product_id"]');
        if (sel) sel.onchange = () => onProductChange(row);
    });
}

function countRowHtml(): string {
    const id = 'invc-' + rowSeq++;
    return `<div class="inv-frow count" data-row="${id}">
        <select class="inv-field" data-k="product_id"><option value="">—</option>${productOptions()}</select>
        <span style="display:flex;gap:6px;align-items:center">
            <select class="inv-field" data-k="batch_id" data-batchsel style="display:none;flex:1"></select>
            <input class="inv-field" data-k="counted_qty" type="number" min="0" step="0.001" placeholder="0" style="width:82px">
            <button type="button" class="inv-rowx" data-rowx="${id}" aria-label="${escapeHtml(t('inv-row-remove'))}">×</button>
        </span>
    </div>`;
}

interface ModalCfg {
    maskId: string;
    titleKey: string;
    submitKey: string;
    isCount: boolean;
    labels: string;
    rowFactory: () => string;
}

function modalHtml(cfg: ModalCfg, rows: string): string {
    return `<div class="inv-modal">
        <div class="inv-modal-head">
            <div class="h">${escapeHtml(t(cfg.titleKey))}</div>
            <button type="button" class="inv-modal-x" data-inv-close="${cfg.maskId}">${IC_X}</button>
        </div>
        <div class="inv-modal-body">
            ${cfg.isCount ? '' : scanBarHtml(cfg.maskId)}
            ${cfg.labels}
            <div id="${cfg.maskId}-rows">${rows}</div>
            <button type="button" class="inv-addrow" data-inv-add="${cfg.maskId}">+ ${escapeHtml(t('inv-add-row'))}</button>
            <div class="inv-merr" id="${cfg.maskId}-err"></div>
        </div>
        <div class="inv-modal-foot">
            <button type="button" class="inv-mbtn" data-inv-close="${cfg.maskId}">${escapeHtml(t('inv-cancel'))}</button>
            <button type="button" class="inv-mbtn primary" id="${cfg.maskId}-submit">${escapeHtml(t(cfg.submitKey))}</button>
        </div>
    </div>`;
}

// 表头只管第一行那三列:批号/效期是批次品才露的第二行,标题跟着它走(inRowHtml 里的
// .inv-blabel)—— 留在表头就是一个指着空列的标题,而且批次格藏着时它还常驻在那儿。
const IN_LABELS = () =>
    `<div class="inv-flabels"><span>${escapeHtml(t('inv-col-product'))}</span><span>${escapeHtml(t('inv-f-qty'))}</span><span>${escapeHtml(t('inv-f-cost'))}</span></div>`;

const COUNT_LABELS = () =>
    `<div class="inv-flabels count"><span>${escapeHtml(t('inv-col-product'))}</span><span>${escapeHtml(t('inv-f-counted'))}</span></div>`;

function collectRows(maskId: string): Record<string, string>[] {
    const wrap = document.getElementById(maskId + '-rows');
    if (!wrap) return [];
    const out: Record<string, string>[] = [];
    wrap.querySelectorAll<HTMLElement>('[data-row]').forEach((row) => {
        const rec: Record<string, string> = {};
        row.querySelectorAll<HTMLInputElement | HTMLSelectElement>('[data-k]').forEach((f) => {
            rec[f.dataset.k!] = f.value.trim();
        });
        out.push(rec);
    });
    return out;
}

function showErr(maskId: string, msg: string) {
    const el = document.getElementById(maskId + '-err');
    if (el) el.textContent = msg;
}

// 拦下来还得指到是哪一行:十几行的收货单上只说「有一行不对」等于让店员自己一行行找。
function focusRowField(maskId: string, index: number, key: string) {
    const wrap = document.getElementById(maskId + '-rows');
    const row = wrap ? wrap.querySelectorAll<HTMLElement>('[data-row]')[index] : null;
    const field = row ? row.querySelector<HTMLInputElement>(`[data-k="${key}"]`) : null;
    if (!field) return;
    field.focus();
    field.select();
    field.scrollIntoView({ block: 'nearest' });
}

function openModal(cfg: ModalCfg) {
    const mask = document.getElementById(cfg.maskId);
    if (!mask) return;
    rowSeq = 0;
    mask.innerHTML = modalHtml(cfg, cfg.rowFactory() + cfg.rowFactory());
    mask.classList.add('show');
    mask.querySelectorAll<HTMLElement>('[data-inv-close]').forEach((b) => {
        b.onclick = () => closeModal(cfg.maskId);
    });
    const add = mask.querySelector<HTMLElement>('[data-inv-add]');
    if (add) add.onclick = () => addRow(cfg);
    bindRowX(cfg.maskId);
    bindProductChange(cfg.maskId);
    const submit = document.getElementById(cfg.maskId + '-submit') as HTMLButtonElement | null;
    if (submit) submit.onclick = () => doSubmit(cfg, submit);
    mask.onclick = (e) => {
        if (e.target === mask) closeModal(cfg.maskId);
    };
    // 盘点是「数现有的」,加行靠扫没意义;收货才是一箱一箱扫进来
    if (!cfg.isCount)
        mountInvScan({
            maskId: cfg.maskId,
            addRow: () => addRow(cfg),
            syncRow: onProductChange,
        });
}

function addRow(cfg: ModalCfg): HTMLElement | null {
    const rows = document.getElementById(cfg.maskId + '-rows');
    if (!rows) return null;
    rows.insertAdjacentHTML('beforeend', cfg.rowFactory());
    bindRowX(cfg.maskId);
    bindProductChange(cfg.maskId);
    return rows.lastElementChild as HTMLElement | null;
}

function bindRowX(maskId: string) {
    const mask = document.getElementById(maskId);
    if (!mask) return;
    mask.querySelectorAll<HTMLElement>('[data-rowx]').forEach((x) => {
        x.onclick = () => {
            const row = mask.querySelector(`[data-row="${x.dataset.rowx}"]`);
            if (row) row.remove();
        };
    });
}

function closeModal(maskId: string) {
    unmountInvScan(); // 关弹窗必须放相机 + 退订楔子(否则相机灯一直亮、枪还在往这里扫)
    const mask = document.getElementById(maskId);
    if (mask) {
        mask.classList.remove('show');
        mask.innerHTML = '';
    }
}

async function doSubmit(cfg: ModalCfg, submit: HTMLButtonElement) {
    showErr(cfg.maskId, '');
    const wsId = activeWsId();
    if (wsId == null) {
        showErr(cfg.maskId, t('inv-need-workspace'));
        return;
    }
    const raw = collectRows(cfg.maskId);
    // 数量格里那串东西根本不是数量(一整串条码掉了进来)→ 停下来让店员看一眼。盘点这一侧
    // 一起拦:它连楔子那层保护都没有(counted_qty 不声明接枪,枪打的字符原样落进框),而
    // 盘点写的是「架上就是这么多」,一次就把这件货的库存改成天文数字。
    const qtyKey = cfg.isCount ? 'counted_qty' : 'qty';
    const badQty = raw.findIndex((r) => !isSaneQty(r[qtyKey]));
    if (badQty >= 0) {
        showErr(cfg.maskId, t('inv-err-bad-qty'));
        focusRowField(cfg.maskId, badQty, qtyKey);
        return;
    }
    if (cfg.isCount) {
        const lines: CountLine[] = raw
            .filter((r) => r.product_id && r.counted_qty !== '')
            .map((r) => {
                const ln: CountLine = { product_id: r.product_id, counted_qty: r.counted_qty };
                if (r.batch_id) ln.batch_id = r.batch_id; // 选了具体批次 → 逐批对账;空=合计
                return ln;
            });
        if (!lines.length) {
            showErr(cfg.maskId, t('inv-err-no-lines'));
            return;
        }
        try {
            await withLoading(submit, () => invApi.postCount(wsId, lines));
            showToast(t('inv-count-ok'), 'success');
            closeModal(cfg.maskId);
            window.reloadInventory?.();
        } catch (e) {
            showErr(cfg.maskId, invErrMsg(e, 'inv-submit-fail'));
        }
        return;
    }
    // 单价格同理,而且更隐蔽:数量错了架上一点就对不上,单价错了只动库存估值与移动加权
    // 成本,单子当场看不出任何异常。
    const badCost = raw.findIndex((r) => !isSaneCost(r.unit_cost));
    if (badCost >= 0) {
        showErr(cfg.maskId, t('inv-err-bad-cost'));
        focusRowField(cfg.maskId, badCost, 'unit_cost');
        return;
    }
    // 坏效期不许溜进流水:49012-03-31 这种值(一串条码被打进 type=date)后端照收,那批货
    // 从此永远不会进近效期名单。宁可在这里停下来让店员看一眼,也不能默默把日期抹掉再提交。
    const badExpiry = raw.findIndex((r) => !isSaneExpiry(r.expiry_date));
    if (badExpiry >= 0) {
        showErr(cfg.maskId, t('inv-err-bad-expiry'));
        focusRowField(cfg.maskId, badExpiry, 'expiry_date');
        return;
    }
    // 空批号/效期不发(后端 Optional · 空串会把效期当坏日期);单价缺省 0。
    // unit_name 只有扫到单位码(箱码)才有值:后端按 factor_to_base 折算成基本单位落账,
    // 不发就是按基本单位算 —— 12 瓶一箱会变成 1 瓶。
    const lines: InLine[] = raw
        .filter((r) => r.product_id && Number(r.qty) > 0)
        .map((r) => {
            const ln: InLine = { product_id: r.product_id, qty: r.qty };
            if (r.unit_name) ln.unit_name = r.unit_name;
            if (r.unit_cost) ln.unit_cost = r.unit_cost;
            if (r.batch_no) ln.batch_no = r.batch_no;
            if (r.batch_no && r.expiry_date) ln.expiry_date = r.expiry_date;
            return ln;
        });
    if (!lines.length) {
        showErr(cfg.maskId, t('inv-err-no-lines'));
        return;
    }
    submit.disabled = true;
    try {
        await invApi.postIn(wsId, lines);
        showToast(t('inv-in-ok'), 'success');
        closeModal(cfg.maskId);
        window.reloadInventory?.();
    } catch (e) {
        showErr(cfg.maskId, invErrMsg(e, 'inv-submit-fail'));
        submit.disabled = false;
    }
}

window.openInventoryIn = function () {
    openModal({
        maskId: 'inv-in-mask',
        titleKey: 'inv-in-title',
        submitKey: 'inv-in-submit',
        isCount: false,
        labels: IN_LABELS(),
        rowFactory: inRowHtml,
    });
};

window.openInventoryCount = function () {
    openModal({
        maskId: 'inv-count-mask',
        titleKey: 'inv-count-title',
        submitKey: 'inv-count-submit',
        isCount: true,
        labels: COUNT_LABELS(),
        rowFactory: countRowHtml,
    });
};
