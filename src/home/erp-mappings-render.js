// ============================================================
// REFACTOR-WB-modularize · ERP 字段映射「视图层」(常量 + 共享状态 + 渲染)从 erp-mappings.js 拆出
//
// 常量 + _state(从不重赋值 · export 共享)+ _esc/_toast/_isOwner/_isSkin 小助手 +
// 表头/各 select/加新行/数据行渲染。erp-mappings.js(控制层:fetch/save/delete/bind)ESM import。
// ============================================================
/* global escapeHtml */
const ERP_OPTIONS = ['flowaccount', 'peak', 'xero', 'quickbooks', 'express'];
const ERP_LABELS = {
    flowaccount: 'FlowAccount',
    peak: 'PEAK',
    xero: 'Xero',
    quickbooks: 'QuickBooks',
    express: 'Express',
};
const CATEGORY_OPTIONS = [
    'expense_office',
    'expense_travel',
    'expense_utility',
    'asset_inventory',
    'asset_fixed',
    'liability_ap',
    'revenue_sales',
    'revenue_service',
    'other',
];
const TAX_KIND_OPTIONS = ['vat_7', 'vat_0', 'vat_exempt', 'wht_1', 'wht_3', 'wht_5', 'non_vat'];
const TEST_USER_ID = '468b50c1-5593-4fd6-990d-515ce8085563'; // skin

let _state = {
    sub: 'clients', // clients / accounts / taxes / products
    loaded: { clients: false, accounts: false, taxes: false, products: false },
    items: { clients: [], accounts: [], taxes: [], products: [] },
    clientList: [], // 客户下拉数据 · 一次拿
    clientLoaded: false,
    addingNew: { clients: false, accounts: false, taxes: false, products: false },
    bound: false,
};

function _isOwner() {
    const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
    return !!(u && (u.role === 'owner' || u.is_super_admin));
}
function _isSkin() {
    const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
    return !!(u && u.id === TEST_USER_ID);
}

function _esc(s) {
    return typeof escapeHtml === 'function'
        ? escapeHtml(s == null ? '' : String(s))
        : String(s == null ? '' : s);
}
function _toast(msg, kind) {
    try {
        if (typeof showToast === 'function') showToast(msg, kind || 'info');
    } catch (e) {}
}

function _renderHead(sub) {
    if (sub === 'clients') {
        return (
            '<div class="erp-map-row erp-map-head row-clients">' +
            '<div>' +
            _esc(t('erp-map-col-client')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-erp')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-erp-code')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-notes')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-actions')) +
            '</div>' +
            '</div>'
        );
    }
    if (sub === 'accounts') {
        return (
            '<div class="erp-map-row erp-map-head row-accounts">' +
            '<div>' +
            _esc(t('erp-map-col-erp')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-category')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-erp-code')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-erp-name')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-notes')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-actions')) +
            '</div>' +
            '</div>'
        );
    }
    if (sub === 'products') {
        return (
            '<div class="erp-map-row erp-map-head row-products">' +
            '<div>' +
            _esc(t('erp-map-col-item-name')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-erp-product-code')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-erp-name')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-notes')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-actions')) +
            '</div>' +
            '</div>'
        );
    }
    // taxes
    return (
        '<div class="erp-map-row erp-map-head row-taxes">' +
        '<div>' +
        _esc(t('erp-map-col-erp')) +
        '</div>' +
        '<div>' +
        _esc(t('erp-map-col-tax')) +
        '</div>' +
        '<div>' +
        _esc(t('erp-map-col-erp-tax-code')) +
        '</div>' +
        '<div>' +
        _esc(t('erp-map-col-notes')) +
        '</div>' +
        '<div>' +
        _esc(t('erp-map-col-actions')) +
        '</div>' +
        '</div>'
    );
}

function _erpSelect(currentValue, fieldKey) {
    let s = '<select class="form-input" data-erp-field="' + fieldKey + '">';
    s += '<option value="">' + _esc(t('erp-map-pick-erp')) + '</option>';
    ERP_OPTIONS.forEach(function (k) {
        const sel = k === currentValue ? ' selected' : '';
        s += '<option value="' + k + '"' + sel + '>' + _esc(ERP_LABELS[k]) + '</option>';
    });
    s += '</select>';
    return s;
}

function _clientSelect(currentClientId) {
    let s = '<select class="form-input" data-erp-field="client_id">';
    s += '<option value="">' + _esc(t('erp-map-pick-client')) + '</option>';
    (_state.clientList || []).forEach(function (c) {
        const sel = String(c.id) === String(currentClientId) ? ' selected' : '';
        s += '<option value="' + c.id + '"' + sel + '>' + _esc(c.name || '#' + c.id) + '</option>';
    });
    s += '</select>';
    return s;
}

function _categorySelect(currentValue) {
    let s = '<select class="form-input" data-erp-field="pearnly_category">';
    s += '<option value="">' + _esc(t('erp-map-pick-cat')) + '</option>';
    CATEGORY_OPTIONS.forEach(function (k) {
        const sel = k === currentValue ? ' selected' : '';
        s += '<option value="' + k + '"' + sel + '>' + _esc(t('erp-map-cat-' + k)) + '</option>';
    });
    s += '</select>';
    return s;
}

function _taxKindSelect(currentValue) {
    let s = '<select class="form-input" data-erp-field="pearnly_tax_kind">';
    s += '<option value="">' + _esc(t('erp-map-pick-tax')) + '</option>';
    TAX_KIND_OPTIONS.forEach(function (k) {
        const sel = k === currentValue ? ' selected' : '';
        s += '<option value="' + k + '"' + sel + '>' + _esc(t('erp-map-tax-' + k)) + '</option>';
    });
    s += '</select>';
    return s;
}

function _renderAddRow(sub) {
    const saveBtn =
        '<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">' +
        _esc(t('erp-map-save')) +
        '</button>';
    if (sub === 'clients') {
        return (
            '<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new">' +
            '<div data-label="' +
            _esc(t('erp-map-col-client')) +
            '">' +
            _clientSelect('') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp')) +
            '">' +
            _erpSelect('', 'erp_type') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-code')) +
            '"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="' +
            _esc(t('erp-map-ph-erp-code')) +
            '"></div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-notes')) +
            '"><input type="text" class="form-input" data-erp-field="notes" placeholder="' +
            _esc(t('erp-map-ph-notes')) +
            '"></div>' +
            '<div>' +
            saveBtn +
            '</div>' +
            '</div>'
        );
    }
    if (sub === 'accounts') {
        return (
            '<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new">' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp')) +
            '">' +
            _erpSelect('', 'erp_type') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-category')) +
            '">' +
            _categorySelect('') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-code')) +
            '"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="' +
            _esc(t('erp-map-ph-acc-code')) +
            '"></div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-name')) +
            '"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="' +
            _esc(t('erp-map-ph-acc-name')) +
            '"></div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-notes')) +
            '"><input type="text" class="form-input" data-erp-field="notes" placeholder="' +
            _esc(t('erp-map-ph-notes')) +
            '"></div>' +
            '<div>' +
            saveBtn +
            '</div>' +
            '</div>'
        );
    }
    // taxes
    return (
        '<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new">' +
        '<div data-label="' +
        _esc(t('erp-map-col-erp')) +
        '">' +
        _erpSelect('', 'erp_type') +
        '</div>' +
        '<div data-label="' +
        _esc(t('erp-map-col-tax')) +
        '">' +
        _taxKindSelect('') +
        '</div>' +
        '<div data-label="' +
        _esc(t('erp-map-col-erp-tax-code')) +
        '"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="' +
        _esc(t('erp-map-ph-tax-code')) +
        '"></div>' +
        '<div data-label="' +
        _esc(t('erp-map-col-notes')) +
        '"><input type="text" class="form-input" data-erp-field="notes" placeholder="' +
        _esc(t('erp-map-ph-notes')) +
        '"></div>' +
        '<div>' +
        saveBtn +
        '</div>' +
        '</div>'
    );
}

function _renderItemRow(sub, it, readonly) {
    const delBtn = readonly
        ? ''
        : '<button class="erp-map-del-btn" type="button" data-erp-del="' +
          _esc(it.id) +
          '" title="' +
          _esc(t('erp-map-delete')) +
          '">' +
          '<svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg>' +
          '</button>';
    const erpBadge =
        '<span class="erp-map-erp-badge">' +
        _esc(ERP_LABELS[it.erp_type] || it.erp_type) +
        '</span>';
    if (sub === 'clients') {
        return (
            '<div class="erp-map-row row-clients">' +
            '<div data-label="' +
            _esc(t('erp-map-col-client')) +
            '" class="erp-map-cell-name">' +
            _esc(it.client_name || '#' + it.client_id) +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp')) +
            '">' +
            erpBadge +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-code')) +
            '" class="erp-map-code">' +
            _esc(it.erp_code || '') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-notes')) +
            '">' +
            _esc(it.notes || '') +
            '</div>' +
            '<div>' +
            delBtn +
            '</div>' +
            '</div>'
        );
    }
    if (sub === 'accounts') {
        const catLabel =
            t('erp-map-cat-' + (it.pearnly_category || 'other')) || it.pearnly_category;
        return (
            '<div class="erp-map-row row-accounts">' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp')) +
            '">' +
            erpBadge +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-category')) +
            '" class="erp-map-cell-name">' +
            _esc(catLabel) +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-code')) +
            '" class="erp-map-code">' +
            _esc(it.erp_code || '') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-name')) +
            '">' +
            _esc(it.erp_name || '') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-notes')) +
            '">' +
            _esc(it.notes || '') +
            '</div>' +
            '<div>' +
            delBtn +
            '</div>' +
            '</div>'
        );
    }
    if (sub === 'products') {
        return (
            '<div class="erp-map-row row-products">' +
            '<div data-label="' +
            _esc(t('erp-map-col-item-name')) +
            '" class="erp-map-cell-name">' +
            _esc(it.item_name || '') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-product-code')) +
            '" class="erp-map-code">' +
            _esc(it.erp_code || '') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-name')) +
            '">' +
            _esc(it.erp_name || '') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-notes')) +
            '">' +
            _esc(it.notes || '') +
            '</div>' +
            '<div>' +
            delBtn +
            '</div>' +
            '</div>'
        );
    }
    // taxes
    const taxLabel = t('erp-map-tax-' + (it.pearnly_tax_kind || '')) || it.pearnly_tax_kind;
    return (
        '<div class="erp-map-row row-taxes">' +
        '<div data-label="' +
        _esc(t('erp-map-col-erp')) +
        '">' +
        erpBadge +
        '</div>' +
        '<div data-label="' +
        _esc(t('erp-map-col-tax')) +
        '" class="erp-map-cell-name">' +
        '<span class="erp-map-tax-badge">' +
        _esc(taxLabel) +
        '</span></div>' +
        '<div data-label="' +
        _esc(t('erp-map-col-erp-tax-code')) +
        '" class="erp-map-code">' +
        _esc(it.erp_code || '') +
        '</div>' +
        '<div data-label="' +
        _esc(t('erp-map-col-notes')) +
        '">' +
        _esc(it.notes || '') +
        '</div>' +
        '<div>' +
        delBtn +
        '</div>' +
        '</div>'
    );
}

export { _state, _esc, _toast, _isOwner, _isSkin, _renderHead, _renderAddRow, _renderItemRow };
