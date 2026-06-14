// ============================================================
// 录入工作台(身份证 → DMS 客户)· HTML 模板与纯构建函数
// 设计稿 pearnly_identity_from_recognition_redesign.html · 作用域 .dmsx
// 控制器在 dms-intake.ts。DMS 字段标签为 i18n 键(dxf-*)· 渲染时 t() · 跟随语言切换。
// ============================================================
/* global escapeHtml */

function dxEsc(s: unknown): string {
    return typeof escapeHtml === 'function'
        ? escapeHtml(s == null ? '' : String(s))
        : String(s == null ? '' : s);
}

// 全字段表单分区(对齐 DMS 客户资料页结构)。type:detected=识别填充·changed=与现值不同·
// readonly=只读·select-*=下拉·空=普通。addr=该分区是地址(带「同身份证地址」开关)。
export interface DxFormField {
    key: string;
    label: string;
    type: string;
}
export interface DxFormSection {
    id: string;
    title: string;
    note: string;
    addr?: string; // 地址套件后缀:""(身份证)/"_ct"(联系)/"_sd"(寄送);非地址不设
    sameAs?: boolean; // 联系/寄送默认「与身份证相同」
    fields: DxFormField[];
}

// label 为 i18n 键(dxf-*)· 渲染时 t(label) · 跟随用户语言切换(不写死中泰字面量)。
const ADDR_FIELDS = (sfx: string): DxFormField[] => [
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

export const DX_SECTIONS: DxFormSection[] = [
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
export const DX_COMPARE: Array<{ key: string; label: string }> = [
    { key: 'prefix_name', label: 'dxf-prefix' },
    { key: 'name', label: 'dxf-name' },
    { key: 'people_id', label: 'dxf-pid' },
    { key: 'birthday_be', label: 'dxf-birthday' },
    { key: 'phone', label: 'dxf-phone' },
    { key: 'tax_id', label: 'dxf-tax' },
    { key: 'subdistrict_name', label: 'dxf-subdistrict' },
    { key: 'address', label: 'dxf-address' },
];

export function dxShell(t: (k: string) => string): string {
    const step = (n: number, b: string, s: string) =>
        `<div class="dx-step" data-step="${n}"><div class="dx-step-no">${n}</div>` +
        `<div class="dx-step-c"><b>${dxEsc(t(b))}</b><span>${dxEsc(t(s))}</span></div></div>`;
    return (
        '<div class="dmsx"><div class="dx-wrap">' +
        // 流程卡
        '<div class="dx-card">' +
        '<div class="dx-flow-h"><div>' +
        `<b id="dx-flow-title">${dxEsc(t('dx-title'))}</b>` +
        `<p id="dx-flow-sub">${dxEsc(t('dx-sub'))}</p></div></div>` +
        '<div class="dx-stepper">' +
        step(1, 'dx-st1', 'dx-st1s') +
        step(2, 'dx-st2', 'dx-st2s') +
        step(3, 'dx-st3', 'dx-st3s') +
        step(4, 'dx-st4', 'dx-st4s') +
        '</div>' +
        // state 容器(控制器注入内部)
        '<div class="dx-state active" id="dx-s-upload"></div>' +
        '<div class="dx-state" id="dx-s-searching"></div>' +
        '<div class="dx-state" id="dx-s-match"></div>' +
        '<div class="dx-state" id="dx-s-confirm"></div>' +
        '<div class="dx-state" id="dx-s-success"></div>' +
        '</div></div></div>' +
        // 确认弹窗(站内 .modal)
        '<div class="modal-overlay" id="dx-modal-mask" style="display:none;"></div>'
    );
}
