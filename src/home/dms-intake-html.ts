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
// E(2026-06-15):地址改逐字段比对 —— 不再整串拼,用户能看清是哪个子字段差异并各自取舍。
//   addr=true 的行属户籍地址块;select 子字段 idKey 指向写库的 *_id 字段(applyDecisionToForm 用)。
export interface DxCompareRow {
    key: string;
    label: string;
    addr?: boolean;
    idKey?: string; // select 子字段对应的写库 id 字段(house_no/moo/soi/road 无需,自身即写库键)
}
export const DX_COMPARE: DxCompareRow[] = [
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

// 步骤条标签键(按任务) · 纯数据 · 避免 html 模块反向 import core 造成循环依赖。
export const STEP_KEYS: Record<string, Array<[string, string]>> = {
    identity: [
        ['dx-st1', 'dx-st1s'],
        ['dx-st2', 'dx-st2s'],
        ['dx-st3', 'dx-st3s'],
        ['dx-st4', 'dx-st4s'],
    ],
    invoice: [
        ['dxi-st1', 'dxi-st1s'],
        ['dxi-st2', 'dxi-st2s'],
        ['dxi-st3', 'dxi-st3s'],
        ['dxi-st4', 'dxi-st4s'],
    ],
};

// 任务选择器卡(发票 / 身份证)· data-task 切换由控制器接管
function taskPickerHtml(t: (k: string) => string, task: string): string {
    const opt = (key: string, titleK: string, descK: string, icon: string) =>
        `<div class="dx-opt${task === key ? ' active' : ''}" data-task="${key}">` +
        `<div class="dx-opt-ic">${icon}</div>` +
        `<div class="dx-opt-c"><b>${dxEsc(t(titleK))}</b><span>${dxEsc(t(descK))}</span></div>` +
        '<div class="dx-opt-sel"></div></div>';
    const icInv =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="22" height="22"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4"/><path d="M9 11h6M9 15h6"/></svg>';
    const icId =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="22" height="22"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2.2"/><path d="M6 16c.8-1.6 2-2.4 3-2.4s2.2.8 3 2.4M14 10h4M14 14h4"/></svg>';
    return (
        '<div class="dx-card dx-task">' +
        '<div class="dx-task-h">' +
        `<b>${dxEsc(t('dxk-pick-h'))}</b><span>${dxEsc(t('dxk-pick-s'))}</span></div>` +
        '<div class="dx-task-grid">' +
        opt('invoice', 'dxk-inv-t', 'dxk-inv-d', icInv) +
        opt('identity', 'dxk-id-t', 'dxk-id-d', icId) +
        '</div></div>'
    );
}

export function dxShell(t: (k: string) => string, task = 'invoice'): string {
    const titleKey = task === 'invoice' ? 'dxi-title' : 'dx-title';
    const subKey = task === 'invoice' ? 'dxi-sub' : 'dx-sub';
    const steps = STEP_KEYS[task] || STEP_KEYS.identity;
    const step = (n: number, b: string, s: string) =>
        `<div class="dx-step" data-step="${n}"><div class="dx-step-no">${n}</div>` +
        `<div class="dx-step-c"><b>${dxEsc(t(b))}</b><span>${dxEsc(t(s))}</span></div></div>`;
    return (
        '<div class="dmsx"><div class="dx-wrap">' +
        taskPickerHtml(t, task) +
        // 流程卡
        '<div class="dx-card">' +
        '<div class="dx-flow-h"><div>' +
        `<b id="dx-flow-title">${dxEsc(t(titleKey))}</b>` +
        `<p id="dx-flow-sub">${dxEsc(t(subKey))}</p></div>` +
        `<button class="btn" id="dx-records">${dxEsc(t('dxk-records'))}</button></div>` +
        '<div class="dx-stepper">' +
        steps.map((s, i) => step(i + 1, s[0], s[1])).join('') +
        '</div>' +
        // state 容器(控制器注入内部)· 共享:上传/识别/成功;身份证:匹配/确认;发票:复核/导出
        '<div class="dx-state active" id="dx-s-upload"></div>' +
        '<div class="dx-state" id="dx-s-searching"></div>' +
        '<div class="dx-state" id="dx-s-match"></div>' +
        '<div class="dx-state" id="dx-s-confirm"></div>' +
        '<div class="dx-state" id="dx-s-inv-review"></div>' +
        '<div class="dx-state" id="dx-s-inv-submit"></div>' +
        '<div class="dx-state" id="dx-s-success"></div>' +
        '</div></div></div>' +
        // 确认弹窗(站内 .modal)
        '<div class="modal-overlay" id="dx-modal-mask" style="display:none;"></div>'
    );
}
