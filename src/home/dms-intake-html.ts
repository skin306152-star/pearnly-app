// ============================================================
// 录入工作台(身份证 → DMS 客户)· HTML 模板与纯构建函数
// 设计稿 pearnly_identity_from_recognition_redesign.html · 作用域 .dmsx
// 控制器在 dms-intake.ts。DMS 字段标签为领域名(泰/中双语字面量·非 i18n 键)。
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

const ADDR_FIELDS = (sfx: string): DxFormField[] => [
    { key: 'house_no' + sfx, label: 'เลขที่ / 房号', type: 'detected' },
    { key: 'building' + sfx, label: 'อาคาร / 建筑', type: '' },
    { key: 'floor' + sfx, label: 'ชั้น / 楼层', type: '' },
    { key: 'room' + sfx, label: 'ห้อง / 房间', type: '' },
    { key: 'village' + sfx, label: 'หมู่บ้าน / 村庄', type: '' },
    { key: 'moo' + sfx, label: 'หมู่ที่ / 村组', type: 'detected' },
    { key: 'soi' + sfx, label: 'ตรอก/ซอย / 巷', type: '' },
    { key: 'road' + sfx, label: 'ถนน / 路', type: '' },
    { key: 'province_id' + sfx, label: 'จังหวัด / 府', type: 'select-province' },
    { key: 'district_id' + sfx, label: 'อำเภอ/เขต / 县·区', type: 'select-district' },
    { key: 'subdistrict_id' + sfx, label: 'ตำบล/แขวง / 乡·分区', type: 'select-subdistrict' },
    { key: 'zipcode_id' + sfx, label: 'รหัสไปรษณีย์ / 邮编', type: 'select-postcode' },
];

export const DX_SECTIONS: DxFormSection[] = [
    {
        id: 'cust',
        title: 'ข้อมูลลูกค้า / 客户资料',
        note: '字段名称按 DMS 客户资料结构',
        fields: [
            { key: 'cuscode', label: 'รหัสลูกค้า / 客户代码', type: 'readonly' },
            { key: 'prefix_id', label: 'คำนำหน้านาม / 称谓', type: 'select-title' },
            { key: 'name', label: 'ชื่อ นามสกุลลูกค้า / 客户姓名', type: 'detected' },
            { key: 'tel_work', label: 'เบอร์โทรศัพท์ที่ทำงาน / 工作电话', type: '' },
            { key: 'tel_home', label: 'เบอร์โทรศัพท์ที่บ้าน / 家庭电话', type: '' },
            { key: 'phone', label: 'เบอร์โทรศัพท์ / 手机号', type: '' },
            { key: 'email', label: 'อีเมล / 邮箱', type: '' },
            { key: 'line_id', label: 'Line', type: '' },
            { key: 'facebook', label: 'Facebook', type: '' },
            { key: 'birthday_be', label: 'วัน/เดือน/ปี เกิด / 出生日期', type: 'detected' },
            { key: 'people_id', label: 'เลขประจำตัวประชาชน / 身份证号', type: 'detected' },
            { key: 'tax_id', label: 'เลขประจำตัวผู้เสียภาษี / 纳税人编号', type: 'detected' },
            { key: 'credit_day', label: 'เครดิต / 信用额度', type: '' },
            { key: 'branch_code', label: 'สาขา / 分店代码', type: 'readonly' },
        ],
    },
    {
        id: 'addr_id',
        title: 'ที่อยู่ตามบัตรประชาชน / 身份证地址',
        note: '本次身份证读取出的地址',
        addr: '',
        fields: ADDR_FIELDS(''),
    },
    {
        id: 'addr_ct',
        title: 'ที่อยู่สำหรับติดต่อ / 联系地址',
        note: 'DMS 可编辑地址字段',
        addr: '_ct',
        sameAs: true,
        fields: ADDR_FIELDS('_ct'),
    },
    {
        id: 'addr_sd',
        title: 'ที่อยู่ติดต่อเอกสาร / 文件联系地址',
        note: '用于邮寄或文件联系',
        addr: '_sd',
        sameAs: true,
        fields: ADDR_FIELDS('_sd'),
    },
];

// 比对行(领域字段·双语标签)。新值取自 OCR,DMS 值取自 current_fields。
export const DX_COMPARE: Array<{ key: string; label: string }> = [
    { key: 'prefix_name', label: 'คำนำหน้านาม / 称谓' },
    { key: 'name', label: 'ชื่อ นามสกุลลูกค้า / 姓名' },
    { key: 'people_id', label: 'เลขประจำตัวประชาชน / 身份证号' },
    { key: 'birthday_be', label: 'วัน/เดือน/ปี เกิด / 出生日期' },
    { key: 'phone', label: 'เบอร์โทรศัพท์ / 手机号' },
    { key: 'tax_id', label: 'เลขประจำตัวผู้เสียภาษี / 纳税人编号' },
    { key: 'subdistrict_name', label: 'ตำบล/แขวง / 乡·分区' },
    { key: 'address', label: 'ที่อยู่ / 完整地址' },
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
        `<p id="dx-flow-sub">${dxEsc(t('dx-sub'))}</p></div>` +
        `<span class="dx-badge blue" id="dx-flow-badge"></span></div>` +
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
