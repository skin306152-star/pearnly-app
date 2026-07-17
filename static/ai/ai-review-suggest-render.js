/*
 * Pearnly AI · ai-review-suggest-render.js · J-A 确定性读数解歧建议(改数三字段预填)HTML
 *
 * amount_math_fail 票若 order_detail.alerts 挂着 amount_read_suggested(J-13 · 后端确定性
 * 纯代码反解出的唯一自洽建议),改数(E)态从单字段(仅 VAT)升级成三字段(净额/VAT/含税),
 * 预填建议值 + 琥珀标注"AI 按票面等式推算,请核对原图"(非静默,人工仍需核对原图再提交,
 * 建议永不自动落库)。无建议票的 E 态维持现状,走 ai-review-render.js 内联的单字段表单,
 * 不进本模块。拆出独立文件同 ai-review-pool.js 先例(单文件<500 铁律)。
 */
(function (root) {
    'use strict';

    function esc(s) {
        return AI.state.esc(s);
    }

    function fieldHtml(id, labelKey, value) {
        return (
            '<div class="rv-suggest-field">' +
            '<label class="rv-edit-lb" for="' +
            id +
            '">' +
            esc(at(labelKey)) +
            '</label>' +
            '<input class="rv-vat-input num" id="' +
            id +
            '" inputmode="decimal" value="' +
            esc(value == null ? '' : value) +
            '">' +
            '</div>'
        );
    }

    // ctx: {editSuggestValues: {net, vat, grand}, editErr}(ai-review.js::startEdit 赋值,
    // 三字段均已预填建议值 · 至少是空串,不用再兜底)。
    function editFormHtml(ctx) {
        var v = ctx.editSuggestValues || {};
        return (
            '<div class="rv-edit rv-edit-suggest" id="rvEdit">' +
            '<div class="rv-suggest-note">' +
            esc(at('rv_suggest_note')) +
            '</div>' +
            '<div class="rv-suggest-fields">' +
            fieldHtml('rvNetInput', 'rv_field_net', v.net) +
            fieldHtml('rvVatInput', 'rv_field_vat_face', v.vat) +
            fieldHtml('rvGrandInput', 'rv_field_total', v.grand) +
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
