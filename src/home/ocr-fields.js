/* REFACTOR-C1-home-batch9b · OCR 多页字段合并 + 抽屉字段编辑
 * 从 home.js verbatim 抽出(0 逻辑改):mergeFields / onFieldEdit / updateDrawerEditCount。
 *
 * 桥接说明:
 * - 3 个函数 window.X=X 挂出 —— mergeFields 被 ocr-recognize/ocr-results/ocr-duplicate
 *   裸调(OCR 流程内);onFieldEdit/updateDrawerEditCount 被 ocr-results(抽屉渲染绑 input
 *   事件)+ recon-drawer(window 桥)裸调。
 * - mergeFields 是纯函数(仅 args)。onFieldEdit/updateDrawerEditCount 读 _results/_drawerIdx
 *   (home.js 顶层 · 全局解析 · 仅属性 mutation)· 调 renderResults(window 桥)。
 * - 全部调用点都在事件 / 异步 handler 内 → 无引导期裸调风险。
 */
/* global _results, _drawerIdx, renderResults */

function mergeFields(pages) {
    const result = {
        invoice_number: null,
        date: null,
        total_amount: null,
        tax_ids: [],
        seller_name: '',
        seller_tax: '',
        seller_addr: '',
        buyer_name: '',
        buyer_tax: '',
        buyer_addr: '',
        subtotal: '',
        vat: '',
        notes: '',
        items: [],
    };
    // 只取主页(非副本/重复页)
    const primaryPages = pages.filter((p) => !p.is_duplicate && !p.is_copy);
    const sourcePages = primaryPages.length > 0 ? primaryPages : pages;
    for (const p of sourcePages) {
        const f = p.fields || {};
        // 标量字段:取第一个非空值
        if (!result.invoice_number && f.invoice_number) result.invoice_number = f.invoice_number;
        if (!result.date && f.date) result.date = f.date;
        if (!result.total_amount && f.total_amount) result.total_amount = f.total_amount;
        if (!result.subtotal && f.subtotal) result.subtotal = f.subtotal;
        if (!result.vat && f.vat) result.vat = f.vat;
        if (!result.seller_name && f.seller_name) result.seller_name = f.seller_name;
        if (!result.seller_tax && f.seller_tax) result.seller_tax = f.seller_tax;
        if (!result.seller_addr && f.seller_addr) result.seller_addr = f.seller_addr;
        if (!result.buyer_name && f.buyer_name) result.buyer_name = f.buyer_name;
        if (!result.buyer_tax && f.buyer_tax) result.buyer_tax = f.buyer_tax;
        if (!result.buyer_addr && f.buyer_addr) result.buyer_addr = f.buyer_addr;
        if (!result.notes && f.notes) result.notes = f.notes;
        // 数组字段:合并所有页
        if (Array.isArray(f.items) && f.items.length) result.items.push(...f.items);
        if (Array.isArray(f.tax_ids)) result.tax_ids.push(...f.tax_ids);
    }
    // 兜底:若 seller_tax / buyer_tax 仍空,从 tax_ids 取
    result.tax_ids = [...new Set(result.tax_ids)];
    if (!result.seller_tax && result.tax_ids[0]) result.seller_tax = result.tax_ids[0];
    if (!result.buyer_tax && result.tax_ids[1]) result.buyer_tax = result.tax_ids[1];
    return result;
}

function onFieldEdit(e) {
    const key = e.target.dataset.field;
    const val = e.target.value;
    const r = _results[_drawerIdx];
    const original = r.merged_fields[key];
    if (val === (original ?? '')) delete r.edits[key];
    else {
        r.edits[key] = val;
        r.merged_fields[key] = val;
    }
    const wrap = document.querySelector(`[data-field-wrap="${key}"]`);
    if (wrap) wrap.classList.toggle('edited', r.edits[key] !== undefined);
    updateDrawerEditCount();
    renderResults();
}

function updateDrawerEditCount() {
    const r = _results[_drawerIdx];
    const n = r ? Object.keys(r.edits).length : 0;
    const el = document.getElementById('drawer-edit-count-sub');
    if (el) el.textContent = n > 0 ? t('drawer-edit-count', { n }) : '';
}

// ── window 桥(ocr-recognize/ocr-results/ocr-duplicate/recon-drawer 裸调)──
window.mergeFields = mergeFields;
window.onFieldEdit = onFieldEdit;
window.updateDrawerEditCount = updateDrawerEditCount;
