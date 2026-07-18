/*
 * Pearnly AI · ai-review-suggest-render.js · J-A 确定性读数解歧建议(改数三字段预填)HTML
 *
 * amount_math_fail 票若 order_detail.alerts 挂着 amount_read_suggested(J-13 · 后端确定性
 * 纯代码反解出的唯一自洽建议),改数(E)态预填建议值并用琥珀提示。没有建议时也显示票号、
 * 日期、净额、VAT、含税合计，让人按原件修正 OCR 原值；建议永不自动落库。
 */
(function (root) {
    'use strict';

    function esc(s) {
        return AI.state.esc(s);
    }

    function fieldHtml(id, labelKey, value, original, opts) {
        opts = opts || {};
        return (
            '<div class="rv-suggest-field' +
            (opts.wide ? ' wide' : '') +
            '">' +
            '<label class="rv-edit-lb" for="' +
            id +
            '">' +
            esc(at(labelKey)) +
            '</label>' +
            '<input class="rv-vat-input' +
            (opts.numeric ? ' num' : '') +
            '" id="' +
            id +
            '" type="' +
            (opts.type || 'text') +
            '"' +
            (opts.numeric ? ' inputmode="decimal"' : '') +
            ' value="' +
            esc(value == null ? '' : value) +
            '"><div class="rv-edit-original">' +
            esc(at('rv_original_value', { value: original || '—' })) +
            '</div>' +
            '</div>'
        );
    }

    // ctx: {editSuggestValues, editErr}(ai-review.js::startEdit 赋值,字段至少是空串)。
    function editFormHtml(ctx) {
        var v = ctx.editSuggestValues || {};
        var original = (ctx.entry && ctx.entry.ocr_read) || {};
        return (
            '<div class="rv-edit rv-edit-suggest" id="rvEdit">' +
            '<div class="' +
            (ctx.editSuggestion ? 'rv-suggest-note' : 'rv-edit-note') +
            '">' +
            esc(at(ctx.editSuggestion ? 'rv_suggest_note' : 'rv_edit_values_note')) +
            '</div>' +
            '<div class="rv-suggest-fields">' +
            fieldHtml(
                'rvInvoiceNoInput',
                'rv_field_invno',
                v.invoice_number,
                original.invoice_number,
                { wide: true }
            ) +
            fieldHtml(
                'rvInvoiceDateInput',
                'rv_field_date',
                v.invoice_date,
                original.invoice_date,
                { type: 'date' }
            ) +
            fieldHtml('rvNetInput', 'rv_field_net', v.net, original.subtotal, {
                numeric: true,
            }) +
            fieldHtml('rvVatInput', 'rv_field_vat_face', v.vat, original.vat, {
                numeric: true,
            }) +
            fieldHtml('rvGrandInput', 'rv_field_total', v.grand, original.total_amount, {
                numeric: true,
            }) +
            '</div>' +
            '<div class="rv-edit-hint">' +
            esc(at('rv_edit_hint')) +
            '</div>' +
            (ctx.editErr
                ? '<div class="rv-edit-err" id="rvEditErr">' +
                  esc(at('rv_edit_vat_required')) +
                  '</div>'
                : '') +
            '</div>'
        );
    }

    var api = { editFormHtml: editFormHtml };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.reviewSuggest = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
