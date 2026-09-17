import { thaiToday, thaiDateText } from './thai-date-picker.js';
import { manualHtml, readManual, bindManual } from './manual-document.js';
import './record-form.css';
export type Fields = Record<string, unknown>;
export type Item = { name: string; qty: string; price: string };
const copy: Record<string, string[]> = {
    amountError: [
        'กรุณาตรวจสอบจำนวน ราคา และภาษี',
        'Check quantity, price and tax.',
        '请检查数量、单价和税额。',
        '数量・単価・税額を確認してください。',
    ],
    companyError: [
        'บริษัทในเอกสารไม่ตรงกับบริษัทที่เลือก',
        'The document company does not match the selected company.',
        '单据公司与当前账套不一致，请核对。',
        '書類の会社が選択した会社と一致しません。',
    ],
    duplicateError: [
        'เลขที่เอกสารนี้ถูกบันทึกแล้ว',
        'This document number is already recorded.',
        '该单据号已记录，请勿重复保存。',
        'この伝票番号は既に記録されています。',
    ],
    accessError: [
        'ไม่มีสิทธิ์ดำเนินการนี้',
        'You do not have permission for this action.',
        '当前账号没有此操作权限。',
        'この操作の権限がありません。',
    ],
    lockedError: [
        'บันทึกรายการนี้แล้ว กรุณากลับไปดูรายการ',
        'This record is saved. Open it from the records list.',
        '这笔记录已保存，请返回记录列表查看。',
        'この記録は保存済みです。一覧から確認してください。',
    ],
    purchase: ['บันทึกซื้อ', 'Record a purchase', '记一笔采购', '仕入を記録'],
    sales: ['บันทึกขาย', 'Record a sale', '记一笔销售', '売上を記録'],
    manual: ['กรอกเอง', 'Enter manually', '手动录入', '手入力'],
    upload: ['อัปโหลดเอกสาร', 'Upload attachment', '上传附件', '添付ファイルをアップロード'],
    date: ['วันที่', 'Date', '日期', '日付'],
    supplier: ['ผู้ขาย', 'Supplier', '供应商', '仕入先'],
    customer: ['ลูกค้า', 'Customer', '客户', '顧客'],
    number: [
        'เลขที่เอกสาร (ไม่บังคับ)',
        'Document number (optional)',
        '单据号（选填）',
        '伝票番号（任意）',
    ],
    name: ['สินค้า / บริการ', 'Product / service', '商品 / 服务', '商品 / サービス'],
    qty: ['จำนวน', 'Quantity', '数量', '数量'],
    price: ['ราคาต่อหน่วย', 'Unit price', '单价', '単価'],
    kind: ['ประเภท', 'Type', '类型', '種類'],
    stock: ['สินค้า', 'Goods', '商品', '商品'],
    service: ['บริการ', 'Service', '服务', 'サービス'],
    add: ['เพิ่มรายการ', 'Add a line', '添加一行', '行を追加'],
    remove: ['ลบ', 'Remove', '移除', '削除'],
    vat: ['ภาษีมูลค่าเพิ่ม', 'VAT amount', '税额', '税額'],
    notes: ['หมายเหตุ (ไม่บังคับ)', 'Notes (optional)', '备注（选填）', '備考（任意）'],
    total: ['รวม', 'Total', '合计', '合計'],
    draft: ['บันทึกฉบับร่าง', 'Save draft', '保存草稿', '下書き保存'],
    confirm: ['บันทึก', 'Save', '保存', '保存'],
    saved: ['บันทึกแล้ว', 'Saved', '已保存', '保存しました'],
    draftSaved: ['บันทึกฉบับร่างแล้ว', 'Draft saved', '草稿已保存', '下書きを保存しました'],
    records: ['ดูรายการ', 'View records', '查看记录', '記録を表示'],
    again: ['บันทึกรายการใหม่', 'Record another', '再记一笔', '続けて記録'],
    busy: ['กำลังดำเนินการ…', 'Working…', '正在处理…', '処理中…'],
    error: [
        'บันทึกไม่สำเร็จ ข้อมูลยังอยู่ กรุณาตรวจสอบแล้วลองใหม่',
        'Could not save. Your entries are retained; check and retry.',
        '保存失败，填写内容已保留，请检查后重试。',
        '保存できませんでした。入力内容は保持されています。確認して再試行してください。',
    ],
    choose: ['เลือกไฟล์', 'Choose files', '选择文件', 'ファイルを選択'],
    hint: [
        'อัปโหลดรูปภาพ PDF หรือเอกสาร แล้วตรวจสอบก่อนบันทึก',
        'Upload images, PDFs or documents, then review before saving.',
        '上传图片、PDF 或文档，核对内容后保存。',
        '画像・PDF・書類をアップロードし、確認して保存します。',
    ],
    workspace: [
        'กรุณาเลือกบริษัทก่อน',
        'Select a company first',
        '请先选择公司账套',
        '会社を選択してください',
    ],
    attachment: [
        'แนบไฟล์ (ไม่บังคับ · PDF / รูปภาพ)',
        'Attachment (optional · PDF / image)',
        '附件（选填 · PDF / 图片）',
        '添付（任意 · PDF / 画像）',
    ],
    attachmentError: [
        'แนบไฟล์ไม่สำเร็จ กรุณาลองใหม่',
        'Could not attach the file. Please retry.',
        '附件保存失败，请重试。',
        '添付を保存できませんでした。再試行してください。',
    ],
    emptyRecognition: [
        'ไม่พบรายการที่อ่านได้',
        'No records were recognized.',
        '未识别到记录。',
        '記録を読み取れませんでした。',
    ],
    drafts: ['ฉบับร่าง', 'Drafts', '已存草稿', '保存済みの下書き'],
};
export function tr(key: string, lang: string): string {
    return copy[key]?.[Math.max(0, ['th', 'en', 'zh', 'ja'].indexOf(lang))] || key;
}
export function esc(value: unknown): string {
    return String(value ?? '').replace(
        /[&<>"']/g,
        (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!
    );
}
export function emptyFields(): Fields {
    return {
        date: thaiDateText(thaiToday()),
        items: [{ name: '', qty: '1', price: '' }],
        vat: '0',
        vat_rate: '0',
        manual_layout: 1,
        branch: '00000',
        cash_payment: true,
    };
}
export function formHtml(fields: Fields, direction: string, lang: string): string {
    return manualHtml(fields, direction, lang);
}
export const readFields = readManual;
export const bindLines = bindManual;

export function describeError(error: unknown, lang: string): string {
    const detail = String(error instanceof Error ? error.message : error);
    const codes: Array<[string, string]> = [
        ['invalid_amount', 'amountError'],
        ['workspace_mismatch', 'companyError'],
        ['duplicate', 'duplicateError'],
        ['forbidden', 'accessError'],
        ['formal_document_locked', 'lockedError'],
    ];
    return tr(codes.find(([code]) => detail.includes(code))?.[1] || 'error', lang);
}
