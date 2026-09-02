(function () {
    'use strict';

    var copy = {
        th: {
            additionalField: 'ข้อมูลเพิ่มเติม',
            unknownValue: 'ค่าระบบที่ไม่รู้จัก',
            notSpecified: 'ไม่ได้ระบุ',
            true: 'ใช่',
            false: 'ไม่ใช่',
            searchPlaceholder: 'ค้นหาเลขที่เอกสาร คู่ค้า หรือวันที่',
            filterAll: 'ทั้งหมด',
            filterReview: 'ต้องตรวจสอบ',
            filterReady: 'พร้อมลงบัญชี',
            statusReview: 'ต้องตรวจสอบ',
            statusReady: 'พร้อม',
            invoices: 'เอกสาร',
            pages: 'หน้า',
            itemCount: 'รายการ',
            viewDetails: 'ดูและแก้ไขรายละเอียด',
            backToList: 'กลับไปรายการเอกสาร',
            resolveBeforeConfirm: 'แก้ไขเอกสารที่มีปัญหา {count} ฉบับก่อนลงบัญชี',
            noMatches: 'ไม่พบเอกสารที่ตรงกับเงื่อนไข',
            loadMore: 'โหลดเพิ่ม',
            batchSummary: '{total} เอกสาร · พร้อม {ready} · ต้องตรวจสอบ {review}',
            confirmBatch: 'ยืนยันลงบัญชีทั้งหมด',
            save: 'บันทึกการแก้ไข',
            discard: 'ทิ้งเอกสาร',
            confirmDiscard: 'ทิ้งเอกสารฉบับร่างทั้งหมดหรือไม่',
            cancel: 'ยกเลิก',
            original: 'เอกสารต้นฉบับ',
            pdfDocument: 'เอกสาร PDF',
            openOriginal: 'แตะเพื่อเปิด',
            closeOriginal: 'ปิดเอกสารต้นฉบับ',
            fields: 'ข้อมูล OCR',
            items: 'รายการสินค้าและบริการ',
            loadingPreview: 'กำลังโหลดตัวอย่าง…',
            previewFailed: 'เปิดภาพต้นฉบับไม่สำเร็จ',
        },
        en: {
            additionalField: 'Additional information',
            unknownValue: 'Unrecognized system value',
            notSpecified: 'Not specified',
            true: 'Yes',
            false: 'No',
            searchPlaceholder: 'Search document number, party, or date',
            filterAll: 'All',
            filterReview: 'Needs review',
            filterReady: 'Ready',
            statusReview: 'Needs review',
            statusReady: 'Ready',
            invoices: 'Documents',
            pages: 'Pages',
            itemCount: 'Items',
            viewDetails: 'View and edit details',
            backToList: 'Back to documents',
            resolveBeforeConfirm: 'Resolve issues in {count} document(s) before posting',
            noMatches: 'No documents match these filters',
            loadMore: 'Load more',
            batchSummary: '{total} documents · {ready} ready · {review} need review',
            confirmBatch: 'Confirm and post all',
            save: 'Save changes',
            discard: 'Discard documents',
            confirmDiscard: 'Discard this entire draft?',
            cancel: 'Cancel',
            original: 'Original document',
            pdfDocument: 'PDF document',
            openOriginal: 'Tap to view',
            closeOriginal: 'Close original',
            fields: 'OCR fields',
            items: 'Items',
            loadingPreview: 'Loading preview…',
            previewFailed: 'Could not open the original',
        },
        zh: {
            additionalField: '附加信息',
            unknownValue: '未识别的系统值',
            notSpecified: '未填写',
            true: '是',
            false: '否',
            searchPlaceholder: '搜索单据号、交易方或日期',
            filterAll: '全部',
            filterReview: '待处理异常',
            filterReady: '可入账',
            statusReview: '待处理',
            statusReady: '已就绪',
            invoices: '单据',
            pages: '页',
            itemCount: '条明细',
            viewDetails: '查看并编辑明细',
            backToList: '返回单据列表',
            resolveBeforeConfirm: '请先处理 {count} 张异常单据，再批量确认入账',
            noMatches: '没有符合条件的单据',
            loadMore: '加载更多',
            batchSummary: '共 {total} 张 · 可入账 {ready} · 待处理 {review}',
            confirmBatch: '批量确认入账',
            save: '保存修改',
            discard: '丢弃单据',
            confirmDiscard: '确定丢弃这批草稿？',
            cancel: '取消',
            original: '原始单据',
            pdfDocument: 'PDF 文件',
            openOriginal: '点击查看',
            closeOriginal: '关闭原件',
            fields: 'OCR 字段',
            items: '商品与服务明细',
            loadingPreview: '正在加载缩略图…',
            previewFailed: '无法打开原始单据',
        },
        ja: {
            additionalField: '追加情報',
            unknownValue: '未認識のシステム値',
            notSpecified: '未指定',
            true: 'はい',
            false: 'いいえ',
            searchPlaceholder: '書類番号、取引先、日付を検索',
            filterAll: 'すべて',
            filterReview: '要確認',
            filterReady: '計上可能',
            statusReview: '要確認',
            statusReady: '準備完了',
            invoices: '書類',
            pages: 'ページ',
            itemCount: '明細',
            viewDetails: '明細を表示・編集',
            backToList: '書類一覧に戻る',
            resolveBeforeConfirm: '{count} 件の問題を解消してから一括計上してください',
            noMatches: '条件に一致する書類がありません',
            loadMore: 'さらに読み込む',
            batchSummary: '全 {total} 件 · 準備完了 {ready} · 要確認 {review}',
            confirmBatch: '一括確認して計上',
            save: '変更を保存',
            discard: '書類を破棄',
            confirmDiscard: 'この下書きをすべて破棄しますか？',
            cancel: 'キャンセル',
            original: '原本',
            pdfDocument: 'PDF 書類',
            openOriginal: 'タップして表示',
            closeOriginal: '原本を閉じる',
            fields: 'OCR 項目',
            items: '商品・サービス明細',
            loadingPreview: 'プレビューを読み込み中…',
            previewFailed: '原本を開けませんでした',
        },
    };

    var EMPTY_CATALOG = { label_aliases: {}, labels: {}, enum_aliases: {}, enums: {} };
    var catalog = null;
    var catalogPromise = null;

    function format(value, values) {
        return String(value || '').replace(/\{(\w+)\}/g, function (_, key) {
            return values && values[key] != null ? String(values[key]) : '';
        });
    }

    function language(lang) {
        return ['th', 'en', 'zh', 'ja'].indexOf(lang) >= 0 ? lang : 'th';
    }

    function localized(row, lang) {
        if (!row || typeof row !== 'object') return '';
        return row[language(lang)] || row.en || row.th || '';
    }

    function normalize(value) {
        return String(value == null ? '' : value)
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '_')
            .replace(/^_+|_+$/g, '');
    }

    function canonicalField(key) {
        var aliases = (catalog || EMPTY_CATALOG).label_aliases || {};
        return aliases[key] || key;
    }

    function enumTable(key) {
        var fields = (catalog || EMPTY_CATALOG).enums || {};
        return fields[canonicalField(key)] || null;
    }

    function canonicalValue(key, value) {
        var normalized = normalize(value);
        var aliases = ((catalog || EMPTY_CATALOG).enum_aliases || {})[canonicalField(key)] || {};
        return aliases[normalized] || normalized;
    }

    function load() {
        if (catalog) return Promise.resolve(catalog);
        if (!catalogPromise) {
            catalogPromise = fetch('/static/line-intake-review/system-fields.json?v=1')
                .then(function (response) {
                    if (!response.ok) throw new Error('system i18n unavailable');
                    return response.json();
                })
                .catch(function () {
                    return EMPTY_CATALOG;
                })
                .then(function (value) {
                    catalog = value && typeof value === 'object' ? value : EMPTY_CATALOG;
                    return catalog;
                });
        }
        return catalogPromise;
    }

    function label(lang, key) {
        var fields = (catalog || EMPTY_CATALOG).labels || {};
        return localized(fields[canonicalField(key)], lang) || text(lang, 'additionalField');
    }

    function options(lang, key, currentValue) {
        var table = enumTable(key);
        if (!table) return null;
        var raw = String(currentValue == null ? '' : currentValue);
        var current = canonicalValue(key, raw);
        var rows = Object.keys(table).map(function (value) {
            return {
                value: value === current && raw ? raw : value,
                label: localized(table[value], lang),
                selected: value === current,
            };
        });
        if (raw && !Object.prototype.hasOwnProperty.call(table, current)) {
            rows.unshift({ value: raw, label: text(lang, 'unknownValue'), selected: true });
        }
        return rows;
    }

    function enumText(lang, key, value) {
        var table = enumTable(key);
        if (!table || value == null || value === '') return value;
        var row = table[canonicalValue(key, value)];
        return localized(row, lang) || text(lang, 'unknownValue');
    }

    function text(lang, key, values) {
        var table = copy[language(lang)];
        return format(table[key] || copy.en[key] || key, values);
    }

    window.lineIntakeReviewI18n = {
        enumText: enumText,
        label: label,
        load: load,
        options: options,
        text: text,
    };
})();
