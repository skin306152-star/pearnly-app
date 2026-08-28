/* Pearnly DMS · 身份证 → DMS 客户向导 · HTML 模板与纯构建数据(作用域 .dmsx)。
 * 移植自主站 src/home/dms-intake-html.ts 的 identity 分支——独立壳只此一个任务,
 * 去掉发票/汇总任务选择器与其步骤/状态容器。字段标签为 i18n 键(dxf-*)· 渲染时 t()。
 * 控制器在 dms-intake.js;取值模型在 dms-intake-core.js。 */
(function (root) {
    'use strict';

    function dxEsc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }

    // 全字段表单分区(对齐 DMS 客户资料页结构)。type:detected=识别填充·changed=与现值不同·
    // readonly=只读·select-*=下拉·空=普通。addr=该分区是地址(带「同身份证地址」开关)。
    var ADDR_FIELDS = function (sfx) {
        return [
            { key: 'house_no' + sfx, label: 'dxf-house', type: 'detected' },
            { key: 'building' + sfx, label: 'dxf-building', type: '' },
            { key: 'floor' + sfx, label: 'dxf-floor', type: '' },
            { key: 'room' + sfx, label: 'dxf-room', type: '' },
            { key: 'village' + sfx, label: 'dxf-village', type: '' },
            { key: 'moo' + sfx, label: 'dxf-moo', type: 'detected' },
            { key: 'soi' + sfx, label: 'dxf-soi', type: '' },
            { key: 'road' + sfx, label: 'dxf-road', type: '' },
            { key: 'province_id' + sfx, label: 'dxf-province', type: 'select-province' },
            { key: 'district_id' + sfx, label: 'dxf-district', type: 'select-district' },
            { key: 'subdistrict_id' + sfx, label: 'dxf-subdistrict', type: 'select-subdistrict' },
            { key: 'zipcode_id' + sfx, label: 'dxf-zipcode', type: 'select-postcode' },
        ];
    };

    var DX_SECTIONS = [
        {
            id: 'cust',
            title: 'dxs-cust',
            note: 'dxsn-cust',
            fields: [
                { key: 'cuscode', label: 'dxf-cuscode', type: 'readonly' },
                { key: 'prefix_id', label: 'dxf-prefix', type: 'select-title' },
                { key: 'name', label: 'dxf-name', type: 'detected' },
                { key: 'tel_work', label: 'dxf-telwork', type: '' },
                { key: 'tel_home', label: 'dxf-telhome', type: '' },
                { key: 'phone', label: 'dxf-phone', type: '' },
                { key: 'email', label: 'dxf-email', type: '' },
                { key: 'line_id', label: 'dxf-line', type: '' },
                { key: 'facebook', label: 'dxf-facebook', type: '' },
                { key: 'birthday_be', label: 'dxf-birthday', type: 'detected' },
                { key: 'people_id', label: 'dxf-pid', type: 'detected' },
                { key: 'tax_id', label: 'dxf-tax', type: 'detected' },
                { key: 'credit_day', label: 'dxf-credit', type: '' },
                { key: 'branch_code', label: 'dxf-branch', type: 'readonly' },
            ],
        },
        {
            id: 'addr_id',
            title: 'dxs-addr-id',
            note: 'dxsn-addr-id',
            addr: '',
            fields: ADDR_FIELDS(''),
        },
        {
            id: 'addr_ct',
            title: 'dxs-addr-ct',
            note: 'dxsn-addr-ct',
            addr: '_ct',
            sameAs: true,
            fields: ADDR_FIELDS('_ct'),
        },
        {
            id: 'addr_sd',
            title: 'dxs-addr-sd',
            note: 'dxsn-addr-sd',
            addr: '_sd',
            sameAs: true,
            fields: ADDR_FIELDS('_sd'),
        },
    ];

    // 比对行 · label 为 i18n 键(复用 dxf-*)。新值取自 OCR,DMS 值取自 current_fields。
    // 地址逐子字段比对;select 子字段 idKey 指向写库 *_id 字段(applyDecisionToForm 用)。
    var DX_COMPARE = [
        { key: 'prefix_name', label: 'dxf-prefix' },
        { key: 'name', label: 'dxf-name' },
        { key: 'people_id', label: 'dxf-pid' },
        { key: 'birthday_be', label: 'dxf-birthday' },
        { key: 'phone', label: 'dxf-phone' },
        { key: 'tax_id', label: 'dxf-tax' },
        { key: 'house_no', label: 'dxf-house', addr: true },
        { key: 'moo', label: 'dxf-moo', addr: true },
        { key: 'soi', label: 'dxf-soi', addr: true },
        { key: 'road', label: 'dxf-road', addr: true },
        { key: 'subdistrict_name', label: 'dxf-subdistrict', addr: true, idKey: 'subdistrict_id' },
        { key: 'district_name', label: 'dxf-district', addr: true, idKey: 'district_id' },
        { key: 'province_name', label: 'dxf-province', addr: true, idKey: 'province_id' },
        { key: 'zipcode_name', label: 'dxf-zipcode', addr: true, idKey: 'zipcode_id' },
    ];

    var STEPS = [
        ['dx-st1', 'dx-st1s'],
        ['dx-st2', 'dx-st2s'],
        ['dx-st3', 'dx-st3s'],
        ['dx-st4', 'dx-st4s'],
    ];

    // 向导外壳(identity 单任务)· state 容器由控制器注入内部。
    function dxShell(t) {
        var step = function (n, b, s) {
            return (
                '<div class="dx-step" data-step="' +
                n +
                '"><div class="dx-step-no">' +
                n +
                '</div><div class="dx-step-c"><b>' +
                dxEsc(t(b)) +
                '</b><span>' +
                dxEsc(t(s)) +
                '</span></div></div>'
            );
        };
        return (
            '<div class="dmsx"><div class="dx-wrap"><div class="dx-card">' +
            '<div class="dx-flow-h"><div><b id="dx-flow-title">' +
            dxEsc(t('dx-title')) +
            '</b><p id="dx-flow-sub">' +
            dxEsc(t('dx-sub')) +
            '</p></div>' +
            '<button class="btn" id="dx-records">' +
            dxEsc(t('dxk-records')) +
            '</button></div>' +
            '<div class="dx-stepper">' +
            STEPS.map(function (s, i) {
                return step(i + 1, s[0], s[1]);
            }).join('') +
            '</div>' +
            '<div class="dx-state active" id="dx-s-upload"></div>' +
            '<div class="dx-state" id="dx-s-searching"></div>' +
            '<div class="dx-state" id="dx-s-match"></div>' +
            '<div class="dx-state" id="dx-s-confirm"></div>' +
            '<div class="dx-state" id="dx-s-success"></div>' +
            '</div>' +
            '<div id="dx-erp-cards" class="dx-erp-cards-zone"></div>' +
            '</div></div>' +
            '<div class="modal-overlay" id="dx-modal-mask" style="display:none;"></div>'
        );
    }

    root.DXHTML = { dxShell: dxShell, DX_SECTIONS: DX_SECTIONS, DX_COMPARE: DX_COMPARE };
    if (typeof module !== 'undefined' && module.exports) root.DXHTML.__test = true;
})(typeof self !== 'undefined' ? self : this);
