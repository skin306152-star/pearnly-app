(function () {
    'use strict';

    var copy = {
        th: {
            title: 'ตรวจสอบเอกสาร ERP',
            purchaseTitle: 'ตรวจสอบเอกสารซื้อ',
            salesTitle: 'ตรวจสอบเอกสารขาย',
            loading: 'กำลังโหลดร่างเอกสาร…',
            failed: 'โหลดเอกสารไม่สำเร็จ',
            expired: 'รายการหมดอายุ',
            saved: 'บันทึกแล้ว',
            confirmed: 'ยืนยันแล้ว',
            discarded: 'ทิ้งแล้ว',
            kind: 'ประเภทการลงสต๊อก',
            pick: 'เลือกประเภท',
            stock: 'สินค้าในสต๊อก',
            service: 'บริการ (ไม่กระทบสต๊อก)',
            purchase: 'ซื้อ',
            sales: 'ขาย',
        },
        en: {
            title: 'Review ERP documents',
            purchaseTitle: 'Review purchase documents',
            salesTitle: 'Review sales documents',
            loading: 'Loading draft…',
            failed: 'Could not load document',
            expired: 'Draft expired',
            saved: 'Saved',
            confirmed: 'Confirmed',
            discarded: 'Discarded',
            kind: 'Posting kind',
            pick: 'Choose type',
            stock: 'Inventory',
            service: 'Service (non-stock)',
            purchase: 'Purchase',
            sales: 'Sales',
        },
        zh: {
            title: '复核 ERP 单据',
            purchaseTitle: '复核采购单据',
            salesTitle: '复核销售单据',
            loading: '正在加载草稿…',
            failed: '无法加载单据',
            expired: '草稿已过期',
            saved: '已保存',
            confirmed: '已确认',
            discarded: '已丢弃',
            kind: '过账类型',
            pick: '选择类型',
            stock: '库存',
            service: '服务（不动库存）',
            purchase: '采购',
            sales: '销售',
        },
        ja: {
            title: 'ERP 書類を確認',
            purchaseTitle: '仕入書類を確認',
            salesTitle: '売上書類を確認',
            loading: '下書きを読み込み中…',
            failed: '書類を読み込めません',
            expired: '下書きの期限切れ',
            saved: '保存しました',
            confirmed: '確認しました',
            discarded: '破棄しました',
            kind: '計上種別',
            pick: '種別を選択',
            stock: '在庫',
            service: 'サービス（在庫なし）',
            purchase: '仕入',
            sales: '売上',
        },
    };

    var labels = {
        invoice_number: ['เลขที่ใบแจ้งหนี้', 'Invoice no.', '发票号', '請求書番号'],
        date: ['วันที่', 'Date', '日期', '日付'],
        document_type: ['ประเภทเอกสาร', 'Document type', '单据类型', '書類種類'],
        seller_name: ['ผู้ขาย', 'Seller', '卖方', '売り手'],
        seller_tax: ['เลขผู้เสียภาษีผู้ขาย', 'Seller tax ID', '卖方税号', '売り手税番号'],
        seller_branch: ['สาขาผู้ขาย', 'Seller branch', '卖方分店', '売り手支店'],
        seller_addr: ['ที่อยู่ผู้ขาย', 'Seller address', '卖方地址', '売り手住所'],
        seller_address: ['ที่อยู่ผู้ขาย', 'Seller address', '卖方地址', '売り手住所'],
        buyer_name: ['ผู้ซื้อ', 'Buyer', '买方', '買い手'],
        buyer_tax: ['เลขผู้เสียภาษีผู้ซื้อ', 'Buyer tax ID', '买方税号', '買い手税番号'],
        buyer_branch: ['สาขาผู้ซื้อ', 'Buyer branch', '买方分店', '買い手支店'],
        buyer_addr: ['ที่อยู่ผู้ซื้อ', 'Buyer address', '买方地址', '買い手住所'],
        buyer_address: ['ที่อยู่ผู้ซื้อ', 'Buyer address', '买方地址', '買い手住所'],
        subtotal: ['ยอดก่อนภาษี', 'Subtotal', '小计', '小計'],
        vat: ['ภาษีมูลค่าเพิ่ม', 'VAT', 'VAT', 'VAT'],
        total_amount: ['ยอดรวม', 'Total', '总额', '合計'],
        notes: ['หมายเหตุ', 'Notes', '备注', '備考'],
        name: ['ชื่อสินค้า', 'Item name', '商品名', '商品名'],
        qty: ['จำนวน', 'Quantity', '数量', '数量'],
        unit: ['หน่วย', 'Unit', '单位', '単位'],
        price: ['ราคาต่อหน่วย', 'Unit price', '单价', '単価'],
        subtotal_item: ['จำนวนเงิน', 'Amount', '金额', '金額'],
    };
    var languageIndex = { th: 0, en: 1, zh: 2, ja: 3 };

    window.erpLineIntakeI18n = {
        text: function (lang, key, values) {
            var local = (copy[lang] || copy.th)[key] || copy.en[key];
            return local || window.lineIntakeReviewI18n.text(lang, key, values);
        },
        label: function (lang, key) {
            var row = labels[key];
            return row ? row[languageIndex[lang] || 0] : key;
        },
    };
})();
