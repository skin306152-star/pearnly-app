// ============================================================
// 客户风险规矩设置 · 静态数据(语言字典 / 线性图标 / 注入式样式)
//
// 与 rules-settings.ts(逻辑)分文件以守 <500 行。自包含 4 语言(zh/th/en/ja)
// 镜像 _showSessionRevokedModal 范式 · 不动 i18n-data;注入式 scoped CSS(含手机端
// media query)· 不碰 CSS bundle。配色对齐异常模块(蓝 #2563eb / 选中黑)。
// ============================================================

export interface ClientRuleRow {
    id: number;
    rule_type: string;
    subject_type: string;
    subject_key: string | null;
    rule_body: Record<string, unknown>;
    severity: string | null;
    is_active: boolean;
}

export const RS_LANGS = {
    zh: {
        title: '风险检查规矩',
        btn: '规矩设置',
        lead: '基础检查(VAT 算术、税号、重复票、日期)默认开着,不用配。下面这些规矩对所有客户生效。',
        gSupplier: '供应商规矩',
        gSupplierDesc: '哪些供应商要特别留意',
        gAmount: '金额上限',
        gAmountDesc: '单张票超过多少就提醒',
        gPeriod: '会计账期',
        gPeriodDesc: '票据日期得落在记账周期内',
        gCategory: '不自动推送的类别',
        gCategoryDesc: '某类发票必须人工确认',
        add: '添加',
        done: '完成',
        empty: '还没设置',
        sevHigh: '高',
        sevMid: '中',
        sevLow: '低',
        alsoLine: '也推 LINE',
        addTitle: '添加一条规矩',
        editTitle: '修改规矩',
        rType: '规矩类型',
        tForce: '供应商必审',
        tForceDesc: '指定供应商人工复核',
        tAmount: '金额上限',
        tAmountDesc: '超过就提醒',
        tPeriod: '会计账期',
        tPeriodDesc: '日期超期提醒',
        tCategory: '不自动推送',
        tCategoryDesc: '某类人工确认',
        fSupplierTax: '供应商税号',
        fAmountLimit: '金额上限(฿)',
        fCategory: '类别名称',
        fSeverity: '严重程度',
        fAlsoLine: '同时推 LINE 给老板',
        fPeriodMode: '账期范围',
        pmCurrent: '本月',
        pmPrev: '上月',
        anyInvoice: '任意发票',
        cancel: '取消',
        save: '保存',
        saved: '已保存',
        deleted: '已删除',
        delConfirm: '确定删除这条规矩?',
        loadFail: '加载失败',
        saveFail: '保存失败',
        needSupplier: '请填供应商税号',
        needAmount: '请填一个有效金额',
        needCategory: '请填类别名称',
    },
    en: {
        title: 'Risk-check rules',
        btn: 'Rules',
        lead: 'Base checks (VAT math, tax id, duplicates, dates) are always on. The rules below apply to every client.',
        gSupplier: 'Supplier rules',
        gSupplierDesc: 'Suppliers that need a closer look',
        gAmount: 'Amount limits',
        gAmountDesc: 'Flag an invoice over this amount',
        gPeriod: 'Accounting period',
        gPeriodDesc: 'Invoice date must fall in the period',
        gCategory: 'Categories not auto-pushed',
        gCategoryDesc: 'These categories need manual sign-off',
        add: 'Add',
        done: 'Done',
        empty: 'Nothing set yet',
        sevHigh: 'High',
        sevMid: 'Medium',
        sevLow: 'Low',
        alsoLine: 'LINE too',
        addTitle: 'Add a rule',
        editTitle: 'Edit rule',
        rType: 'Rule type',
        tForce: 'Force review',
        tForceDesc: 'Manual review for a supplier',
        tAmount: 'Amount limit',
        tAmountDesc: 'Flag when over',
        tPeriod: 'Accounting period',
        tPeriodDesc: 'Flag out-of-period dates',
        tCategory: 'No auto-push',
        tCategoryDesc: 'Manual sign-off',
        fSupplierTax: 'Supplier tax id',
        fAmountLimit: 'Amount limit (฿)',
        fCategory: 'Category name',
        fSeverity: 'Severity',
        fAlsoLine: 'Also push LINE to the boss',
        fPeriodMode: 'Period range',
        pmCurrent: 'This month',
        pmPrev: 'Last month',
        anyInvoice: 'Any invoice',
        cancel: 'Cancel',
        save: 'Save',
        saved: 'Saved',
        deleted: 'Deleted',
        delConfirm: 'Delete this rule?',
        loadFail: 'Failed to load',
        saveFail: 'Failed to save',
        needSupplier: 'Enter the supplier tax id',
        needAmount: 'Enter a valid amount',
        needCategory: 'Enter a category name',
    },
    th: {
        title: 'กฎตรวจความเสี่ยง',
        btn: 'กฎ',
        lead: 'การตรวจพื้นฐาน (VAT, เลขผู้เสียภาษี, ใบซ้ำ, วันที่) เปิดอยู่เสมอ กฎด้านล่างมีผลกับทุกลูกค้า',
        gSupplier: 'กฎผู้ขาย',
        gSupplierDesc: 'ผู้ขายที่ต้องดูให้ละเอียด',
        gAmount: 'วงเงินสูงสุด',
        gAmountDesc: 'แจ้งเตือนเมื่อใบเกินจำนวนนี้',
        gPeriod: 'งวดบัญชี',
        gPeriodDesc: 'วันที่ในใบต้องอยู่ในงวด',
        gCategory: 'หมวดที่ไม่ส่งอัตโนมัติ',
        gCategoryDesc: 'หมวดเหล่านี้ต้องยืนยันด้วยมือ',
        add: 'เพิ่ม',
        done: 'เสร็จ',
        empty: 'ยังไม่ได้ตั้งค่า',
        sevHigh: 'สูง',
        sevMid: 'กลาง',
        sevLow: 'ต่ำ',
        alsoLine: 'ส่ง LINE ด้วย',
        addTitle: 'เพิ่มกฎ',
        editTitle: 'แก้ไขกฎ',
        rType: 'ประเภทกฎ',
        tForce: 'บังคับตรวจ',
        tForceDesc: 'ตรวจด้วยมือสำหรับผู้ขาย',
        tAmount: 'วงเงินสูงสุด',
        tAmountDesc: 'แจ้งเมื่อเกิน',
        tPeriod: 'งวดบัญชี',
        tPeriodDesc: 'แจ้งวันที่นอกงวด',
        tCategory: 'ไม่ส่งอัตโนมัติ',
        tCategoryDesc: 'ยืนยันด้วยมือ',
        fSupplierTax: 'เลขผู้เสียภาษีผู้ขาย',
        fAmountLimit: 'วงเงินสูงสุด (฿)',
        fCategory: 'ชื่อหมวด',
        fSeverity: 'ความรุนแรง',
        fAlsoLine: 'ส่ง LINE ถึงเจ้านายด้วย',
        fPeriodMode: 'ช่วงงวด',
        pmCurrent: 'เดือนนี้',
        pmPrev: 'เดือนที่แล้ว',
        anyInvoice: 'ใบแจ้งหนี้ใดก็ได้',
        cancel: 'ยกเลิก',
        save: 'บันทึก',
        saved: 'บันทึกแล้ว',
        deleted: 'ลบแล้ว',
        delConfirm: 'ลบกฎนี้?',
        loadFail: 'โหลดไม่สำเร็จ',
        saveFail: 'บันทึกไม่สำเร็จ',
        needSupplier: 'กรอกเลขผู้เสียภาษีผู้ขาย',
        needAmount: 'กรอกจำนวนเงินที่ถูกต้อง',
        needCategory: 'กรอกชื่อหมวด',
    },
    ja: {
        title: 'リスクチェックのルール',
        btn: 'ルール',
        lead: '基本チェック(VAT計算・税番号・重複・日付)は常に有効です。以下のルールは全クライアントに適用されます。',
        gSupplier: '取引先ルール',
        gSupplierDesc: '注意が必要な取引先',
        gAmount: '金額上限',
        gAmountDesc: 'この金額を超えたら通知',
        gPeriod: '会計期間',
        gPeriodDesc: '請求日が期間内である必要',
        gCategory: '自動送信しないカテゴリ',
        gCategoryDesc: 'これらは手動確認が必要',
        add: '追加',
        done: '完了',
        empty: '未設定',
        sevHigh: '高',
        sevMid: '中',
        sevLow: '低',
        alsoLine: 'LINEも',
        addTitle: 'ルールを追加',
        editTitle: 'ルールを編集',
        rType: 'ルールの種類',
        tForce: '要確認',
        tForceDesc: '取引先を手動確認',
        tAmount: '金額上限',
        tAmountDesc: '超過時に通知',
        tPeriod: '会計期間',
        tPeriodDesc: '期間外の日付を通知',
        tCategory: '自動送信しない',
        tCategoryDesc: '手動確認',
        fSupplierTax: '取引先の税番号',
        fAmountLimit: '金額上限 (฿)',
        fCategory: 'カテゴリ名',
        fSeverity: '重大度',
        fAlsoLine: '上司にLINEも送信',
        fPeriodMode: '期間の範囲',
        pmCurrent: '今月',
        pmPrev: '先月',
        anyInvoice: '任意の請求書',
        cancel: 'キャンセル',
        save: '保存',
        saved: '保存しました',
        deleted: '削除しました',
        delConfirm: 'このルールを削除しますか?',
        loadFail: '読み込みに失敗',
        saveFail: '保存に失敗',
        needSupplier: '取引先の税番号を入力',
        needAmount: '正しい金額を入力',
        needCategory: 'カテゴリ名を入力',
    },
} as const;

export type RsLang = keyof typeof RS_LANGS;
export type RsDict = Record<keyof (typeof RS_LANGS)['zh'], string>;

export function rsL(): RsDict {
    const raw =
        (window as { _currentLang?: string })._currentLang ||
        localStorage.getItem('mrpilot_lang') ||
        'th';
    const lang = (raw in RS_LANGS ? raw : 'th') as RsLang;
    return RS_LANGS[lang];
}

const RS_ICON = {
    settings:
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    building:
        '<rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/>',
    wallet: '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    calendar:
        '<path d="M8 2v4M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    octagon:
        '<path d="M2.586 16.726A2 2 0 0 1 2 15.312V8.688a2 2 0 0 1 .586-1.414l4.688-4.688A2 2 0 0 1 8.688 2h6.624a2 2 0 0 1 1.414.586l4.688 4.688A2 2 0 0 1 22 8.688v6.624a2 2 0 0 1-.586 1.414l-4.688 4.688a2 2 0 0 1-1.414.586H8.688a2 2 0 0 1-1.414-.586z"/><path d="M12 8v4M12 16h.01"/>',
    bell: '<path d="M10.268 21a2 2 0 0 0 3.464 0"/><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"/>',
    pencil: '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/>',
    trash: '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    plus: '<path d="M5 12h14M12 5v14"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
};

export function rsSvg(name: keyof typeof RS_ICON, size = 16): string {
    return (
        `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
        `stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${RS_ICON[name]}</svg>`
    );
}

export const RS_STYLE = `
#rules-settings-modal,#rs-add-modal{position:fixed;inset:0;z-index:9000;display:none;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,.38);}
#rs-add-modal{z-index:9010;}
#rules-settings-modal.rs-open,#rs-add-modal.rs-open{display:flex;}
.rs-pop{width:720px;max-width:100%;max-height:86vh;background:#fff;border-radius:16px;box-shadow:0 10px 32px rgba(0,0,0,.18);display:grid;grid-template-rows:auto 1fr auto;overflow:hidden;}
.rs-head{display:flex;align-items:center;gap:10px;padding:16px 20px;border-bottom:1px solid #e8e8e3;}
.rs-head h2{font-size:16px;font-weight:650;margin:0;color:#111;}
.rs-tag{font-size:11px;font-weight:600;color:#2563eb;background:#eaf1fe;border:1px solid #cfe0fc;padding:2px 7px;border-radius:6px;}
.rs-close{margin-left:auto;width:32px;height:32px;border-radius:8px;border:1px solid #e8e8e3;background:#fff;color:#999;cursor:pointer;display:grid;place-items:center;}
.rs-close:hover{border-color:#111;color:#111;}
.rs-body{overflow-y:auto;padding:16px 20px;}
.rs-foot{padding:12px 20px;border-top:1px solid #e8e8e3;display:flex;justify-content:flex-end;}
.rs-lead{font-size:13px;color:#555;line-height:1.6;margin:0 0 16px;}
.rs-group{border:1px solid #e8e8e3;border-radius:12px;margin-bottom:14px;overflow:hidden;}
.rs-ghead{display:flex;align-items:center;gap:10px;padding:13px 16px;border-bottom:1px solid #f0f0eb;}
.rs-gico{width:30px;height:30px;border-radius:8px;background:#f4f4f0;display:grid;place-items:center;color:#555;flex:none;}
.rs-gt{font-size:14px;font-weight:600;color:#111;}
.rs-gd{font-size:12px;color:#999;margin-top:1px;}
.rs-addbtn{margin-left:auto;display:inline-flex;align-items:center;gap:4px;font-size:12.5px;font-weight:600;color:#2563eb;background:#eaf1fe;border:1px solid #cfe0fc;border-radius:8px;padding:6px 11px;cursor:pointer;}
.rs-gbody{padding:4px 16px 12px;}
.rs-rule{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f0f0eb;}
.rs-rule:last-child{border-bottom:none;}
.rs-rm{min-width:0;flex:1;}
.rs-rt{font-size:13.5px;font-weight:500;color:#111;}
.rs-rt b{font-family:"SF Mono",Menlo,Consolas,monospace;font-weight:600;}
.rs-line{font-size:11px;font-weight:600;color:#16a34a;margin-left:6px;white-space:nowrap;}
.rs-rs{font-size:12px;color:#999;margin-top:3px;}
.rs-sev{font-size:11px;font-weight:600;padding:3px 9px;border-radius:10px;white-space:nowrap;flex:none;}
.rs-sev.high{background:#fee2e2;color:#dc2626;}
.rs-sev.medium{background:#fef3c7;color:#d97706;}
.rs-sev.low{background:#f4f4f0;color:#999;}
.rs-sw{width:38px;height:22px;border-radius:999px;background:#2563eb;position:relative;cursor:pointer;flex:none;border:none;padding:0;}
.rs-sw::after{content:"";position:absolute;top:2px;left:18px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.15s;}
.rs-sw.off{background:#cbd5e0;}
.rs-sw.off::after{left:2px;}
.rs-icobtn{width:28px;height:28px;border-radius:7px;border:1px solid #e8e8e3;background:#fff;color:#999;cursor:pointer;display:grid;place-items:center;flex:none;}
.rs-icobtn:hover{border-color:#111;color:#111;}
.rs-empty{font-size:12.5px;color:#999;padding:10px 0 4px;}
.rs-types{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:4px;}
.rs-type{border:1px solid #e8e8e3;border-radius:9px;padding:10px 11px;font-size:12.5px;cursor:pointer;text-align:left;background:#fff;}
.rs-type.on{border-color:#2563eb;background:#eaf1fe;}
.rs-type .tt{font-weight:600;color:#111;}
.rs-type .td{color:#999;font-size:11px;margin-top:2px;}
.rs-mlbl{font-size:12px;font-weight:600;color:#555;margin:14px 0 7px;}
.rs-field{font-size:13.5px;width:100%;border:1px solid #e8e8e3;border-radius:8px;padding:9px 11px;background:#fff;color:#111;box-sizing:border-box;}
.rs-two{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.rs-check{display:flex;align-items:center;gap:8px;font-size:13px;color:#555;margin-top:12px;cursor:pointer;}
.rs-check input{width:16px;height:16px;accent-color:#2563eb;}
.rs-btn{height:38px;padding:0 16px;border-radius:9px;font-size:13.5px;font-weight:600;cursor:pointer;border:1px solid transparent;}
.rs-btn-ghost{background:transparent;color:#6b7280;}
.rs-btn-ghost:hover{background:#f0f1ee;}
.rs-btn-primary{background:#2563eb;color:#fff;}
.rs-btn-primary:hover{background:#1d4ed8;}
@media (max-width:560px){
.rs-pop{max-height:94vh;border-radius:14px;}
.rs-types{grid-template-columns:1fr;}
.rs-two{grid-template-columns:1fr;}
.rs-rule{flex-wrap:wrap;}
.rs-rm{flex-basis:100%;}
}
`;
