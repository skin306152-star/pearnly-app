/*
 * Pearnly AI · ai-supplier-profiles-render.js · 供应商过账档案面板(Z3-b)纯校验 + HTML 拼装
 *
 * 骨架照 ai-profile-panels-render.js 的别名面板同构(列表 + 加行表单 + 删行按钮),换字段:
 * 税号 / 供应商名(后端读侧富化,查不到给 null,这里显示「—」)/ 现-赊(default_payment)/
 * 货-费(default_item_type)/ 来源徽标(correction=学来的 · user_rule=人工规则)。
 *
 * 值域(cash/credit、goods/expense)与后端 services/ocr_history/posting_manual.py 的
 * _PAYMENT_VALUES/_ITEM_TYPE_VALUES 同源词汇,这里只是展示层复制一份字符串常量——没有校验
 * 逻辑要保持同源(前端不判值域,选框天然只出这两个值,非法值路由层 422 兜底)。
 * 双导出同 ai-profile-panels-render.js 先例:validateTaxIdRaw 零 DOM 依赖,
 * node(tests/unit/test_ai_supplier_profiles_pure.py)直接 require;HTML 拼装依赖
 * at()/AI.state,只在浏览器根挂载。编排在 ai-profile.js。
 */
(function (root) {
    'use strict';

    var PAYMENT_VALUES = ['cash', 'credit'];
    var ITEM_TYPE_VALUES = ['goods', 'expense'];
    var UNSET = '';

    var SOURCE_CHIP = { correction: 's', user_rule: 'n' };
    var SOURCE_KEY = { correction: 'sp_source_correction', user_rule: 'sp_source_user_rule' };

    // 税号入参最小前端校验(清洗后必须恰好 13 位数字)。真正的落库清洗/值域闸在后端
    // (clean_tax_id 同源口径,routes/supplier_posting_routes.py),前端只挡明显无效输入,
    // 不重抄一份泰文税号规则。
    function validateTaxIdRaw(raw) {
        var digits = String(raw == null ? '' : raw).replace(/\D/g, '');
        if (digits.length !== 13) return { ok: false, errKey: 'err_sp_tax_id_invalid' };
        return { ok: true, value: digits };
    }

    var pure = {
        PAYMENT_VALUES: PAYMENT_VALUES,
        ITEM_TYPE_VALUES: ITEM_TYPE_VALUES,
        UNSET: UNSET,
        SOURCE_CHIP: SOURCE_CHIP,
        SOURCE_KEY: SOURCE_KEY,
        validateTaxIdRaw: validateTaxIdRaw,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    function paymentLabel(v) {
        return v === UNSET ? at('sp_axis_unset') : at('sp_payment_' + v);
    }
    function itemTypeLabel(v) {
        return v === UNSET ? at('sp_axis_unset') : at('sp_item_' + v);
    }

    function sourceChipHtml(source) {
        var cls = SOURCE_CHIP[source] || 'n';
        var key = SOURCE_KEY[source];
        return '<span class="chip ' + cls + '">' + esc(key ? at(key) : source) + '</span>';
    }

    function supplierProfileRowHtml(row, deletingTaxId) {
        var busy = deletingTaxId === row.seller_tax_id;
        var name = row.supplier_name ? esc(row.supplier_name) : '—';
        var payment = row.default_payment ? paymentLabel(row.default_payment) : at('sp_axis_unset');
        var itemType = row.default_item_type
            ? itemTypeLabel(row.default_item_type)
            : at('sp_axis_unset');
        return (
            '<div class="sp-row"><div class="sp-main"><b>' +
            esc(row.seller_tax_id) +
            '</b> <span class="sp-name">' +
            name +
            '</span>' +
            sourceChipHtml(row.source) +
            '<small>' +
            esc(payment) +
            ' · ' +
            esc(itemType) +
            '</small></div>' +
            '<button type="button" class="btn sm" data-action="sp-delete" data-tax="' +
            esc(row.seller_tax_id) +
            '"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(busy ? at('sp_delete_btn_busy') : at('sp_delete_btn')) +
            '</button></div>'
        );
    }

    function supplierProfileListHtml(rows, deletingTaxId) {
        if (!rows || !rows.length) {
            return '<div class="alias-empty">' + esc(at('sp_empty_s')) + '</div>';
        }
        return (
            '<div class="sp-list">' +
            rows
                .map(function (r) {
                    return supplierProfileRowHtml(r, deletingTaxId);
                })
                .join('') +
            '</div>'
        );
    }

    function supplierProfileFormHtml(ctx) {
        var err = ctx.spErrKey ? '<div class="intake-err">' + esc(at(ctx.spErrKey)) + '</div>' : '';
        var btnLabel = ctx.spSubmitting ? at('sp_add_btn_busy') : at('sp_add_btn');
        var paymentOptions = AI.state.optionsHtml(
            [UNSET].concat(PAYMENT_VALUES),
            ctx.spPaymentValue || UNSET,
            paymentLabel
        );
        var itemTypeOptions = AI.state.optionsHtml(
            [UNSET].concat(ITEM_TYPE_VALUES),
            ctx.spItemTypeValue || UNSET,
            itemTypeLabel
        );
        return (
            '<form id="spForm" class="alias-form" novalidate>' +
            '<input class="sf-in" id="spTaxId" name="tax_id" maxlength="20" placeholder="' +
            esc(at('sp_add_ph_tax_id')) +
            '" value="' +
            esc(ctx.spTaxIdValue || '') +
            '">' +
            '<select class="sf-in" id="spPayment" name="default_payment">' +
            paymentOptions +
            '</select>' +
            '<select class="sf-in" id="spItemType" name="default_item_type">' +
            itemTypeOptions +
            '</select>' +
            '<button type="submit" class="btn pri" data-action="sp-add"' +
            (ctx.spSubmitting ? ' disabled' : '') +
            '>' +
            esc(btnLabel) +
            '</button>' +
            err +
            '</form>'
        );
    }

    function supplierProfilePanelHtml(ctx) {
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('sp_title')) +
            '</h3></div><div class="bd">' +
            supplierProfileListHtml(ctx.supplierProfiles, ctx.spDeletingTaxId) +
            supplierProfileFormHtml(ctx) +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.supplierProfilesRender = {
        PAYMENT_VALUES: PAYMENT_VALUES,
        ITEM_TYPE_VALUES: ITEM_TYPE_VALUES,
        UNSET: UNSET,
        validateTaxIdRaw: validateTaxIdRaw,
        supplierProfilePanelHtml: supplierProfilePanelHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
