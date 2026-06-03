# -*- coding: utf-8 -*-
"""
Mr.Pilot · 报表引擎专用 i18n 字典(后端独立 · 不依赖前端)
v109.0 · 2026-05-03

覆盖:模板名 / 模板描述 / 模板分类 / 列头 / 标题模板 / 合计行 / 汇总文案
4 语言:zh / th / en / ja
"""

REPORTS_I18N = {
    # ===== 模板名(4 个) =====
    "tpl-input-vat": {
        "zh": "进项税明细 (ภ.พ.30)",
        "th": "ภาษีซื้อ (ภ.พ.30)",
        "en": "Input VAT (P.P.30)",
        "ja": "仕入VAT明細 (ภ.พ.30)",
    },
    "tpl-standard": {
        "zh": "标准明细",
        "th": "รายการมาตรฐาน",
        "en": "Standard Detail",
        "ja": "標準明細",
    },
    "tpl-erp": {
        "zh": "ERP 录入格式",
        "th": "รูปแบบนำเข้า ERP",
        "en": "ERP Import Format",
        "ja": "ERPインポート形式",
    },
    "tpl-print": {
        "zh": "凭证装订清单",
        "th": "ใบรายการสำหรับเย็บเล่ม",
        "en": "Voucher Binding List",
        "ja": "証憑綴じ込み一覧",
    },
    # ===== 模板描述 =====
    "tpl-input-vat-desc": {
        "zh": "法定报税格式 · 直接交给 RD 税务局",
        "th": "รูปแบบยื่นภาษีตามกฎหมาย · ส่งกรมสรรพากรได้ทันที",
        "en": "Legal tax filing format · Submit directly to RD",
        "ja": "法定申告様式 · RDへ直接提出可",
    },
    "tpl-standard-desc": {
        "zh": "全字段明细 · 给老板汇报 / 内部审核",
        "th": "รายละเอียดครบ · รายงานเจ้านาย / ตรวจสอบภายใน",
        "en": "Full detail · Report to manager / Internal audit",
        "ja": "全項目明細 · 経営報告・内部監査向け",
    },
    "tpl-erp-desc": {
        "zh": "ASCII 列名 + ISO 日期 · 复制到 Mr.ERP / Express",
        "th": "ชื่อคอลัมน์ ASCII + วันที่ ISO · นำเข้า Mr.ERP / Express",
        "en": "ASCII columns + ISO dates · Paste into Mr.ERP / Express",
        "ja": "ASCII列名+ISO日付 · Mr.ERP/Express貼付",
    },
    "tpl-print-desc": {
        "zh": "A4 横版 · 行高大 · 适合打印装订",
        "th": "A4 แนวนอน · บรรทัดสูง · เหมาะสำหรับพิมพ์เย็บเล่ม",
        "en": "A4 landscape · Tall rows · Print-binding optimized",
        "ja": "A4横 · 行高大 · 印刷綴じ最適化",
    },
    # ===== 模板分类 =====
    "tpl-cat-tax": {"zh": "税务申报", "th": "ยื่นภาษี", "en": "Tax Filing", "ja": "税務申告"},
    "tpl-cat-internal": {
        "zh": "内部使用",
        "th": "ใช้ภายใน",
        "en": "Internal Use",
        "ja": "内部利用",
    },
    "tpl-cat-erp": {
        "zh": "ERP 集成",
        "th": "เชื่อมต่อ ERP",
        "en": "ERP Integration",
        "ja": "ERP連携",
    },
    "tpl-cat-print": {
        "zh": "打印输出",
        "th": "พิมพ์เอกสาร",
        "en": "Print Output",
        "ja": "印刷出力",
    },
    # ===== 通用列头 =====
    "col-no": {"zh": "序号", "th": "ลำดับ", "en": "No.", "ja": "番号"},
    "col-invoice-date": {"zh": "日期", "th": "วันที่", "en": "Date", "ja": "日付"},
    "col-invoice-no": {
        "zh": "发票号",
        "th": "เลขที่ใบกำกับ",
        "en": "Invoice No.",
        "ja": "請求書番号",
    },
    "col-seller-name": {
        "zh": "卖方名称",
        "th": "ชื่อผู้ขาย",
        "en": "Seller Name",
        "ja": "売主名称",
    },
    "col-seller-tax-id": {
        "zh": "卖方税号",
        "th": "เลขประจำตัวผู้เสียภาษี",
        "en": "Seller Tax ID",
        "ja": "売主税番号",
    },
    "col-seller-branch": {
        "zh": "卖方分公司",
        "th": "สาขาผู้ขาย",
        "en": "Seller Branch",
        "ja": "売主支店",
    },
    "col-seller-addr": {
        "zh": "卖方地址",
        "th": "ที่อยู่ผู้ขาย",
        "en": "Seller Address",
        "ja": "売主住所",
    },
    "col-buyer-name": {"zh": "买方名称", "th": "ชื่อผู้ซื้อ", "en": "Buyer Name", "ja": "買主名称"},
    "col-buyer-tax-id": {
        "zh": "买方税号",
        "th": "เลขผู้เสียภาษีผู้ซื้อ",
        "en": "Buyer Tax ID",
        "ja": "買主税番号",
    },
    "col-buyer-addr": {
        "zh": "买方地址",
        "th": "ที่อยู่ผู้ซื้อ",
        "en": "Buyer Address",
        "ja": "買主住所",
    },
    "col-amount-before-vat": {
        "zh": "未税金额",
        "th": "ยอดก่อน VAT",
        "en": "Subtotal",
        "ja": "税抜金額",
    },
    "col-vat-amount": {"zh": "VAT 7%", "th": "ภาษี 7%", "en": "VAT 7%", "ja": "VAT 7%"},
    "col-wht-rate": {"zh": "预扣税率", "th": "อัตราหัก ณ ที่จ่าย", "en": "WHT %", "ja": "源泉%"},
    "col-wht-amount": {
        "zh": "预扣税额",
        "th": "ภาษีหัก ณ ที่จ่าย",
        "en": "WHT Amount",
        "ja": "源泉額",
    },
    "col-total-amount": {"zh": "总金额", "th": "ยอดรวม", "en": "Total", "ja": "合計"},
    "col-filename": {"zh": "文件名", "th": "ชื่อไฟล์", "en": "Filename", "ja": "ファイル名"},
    "col-category": {"zh": "类目", "th": "หมวดหมู่", "en": "Category", "ja": "カテゴリ"},
    "col-source": {"zh": "来源", "th": "แหล่งที่มา", "en": "Source", "ja": "ソース"},
    "col-notes": {"zh": "备注", "th": "หมายเหตุ", "en": "Notes", "ja": "備考"},
    "col-signature": {"zh": "签名", "th": "ลายเซ็น", "en": "Signature", "ja": "署名"},
    "col-items": {"zh": "商品明细", "th": "รายการสินค้า", "en": "Line Items", "ja": "明細"},
    "col-item-count": {"zh": "明细数", "th": "จำนวนรายการ", "en": "Items", "ja": "明細数"},
    "col-doc-no": {"zh": "DocNo", "th": "DocNo", "en": "DocNo", "ja": "DocNo"},
    "col-vendor-name": {
        "zh": "VendorName",
        "th": "VendorName",
        "en": "VendorName",
        "ja": "VendorName",
    },
    "col-vendor-tax": {
        "zh": "VendorTaxID",
        "th": "VendorTaxID",
        "en": "VendorTaxID",
        "ja": "VendorTaxID",
    },
    "col-net-amount": {"zh": "NetAmount", "th": "NetAmount", "en": "NetAmount", "ja": "NetAmount"},
    # ===== 标题模板(占位符 {client} {month} {count}) =====
    "tpl-input-vat-title": {
        "zh": "{client} · 进项税明细 (ภ.พ.30) · {month}",
        "th": "{client} · ภาษีซื้อ (ภ.พ.30) · {month}",
        "en": "{client} · Input VAT Detail (P.P.30) · {month}",
        "ja": "{client} · 仕入VAT明細 (ภ.พ.30) · {month}",
    },
    "tpl-standard-title": {
        "zh": "{client} · 发票明细 · {month}",
        "th": "{client} · รายการใบกำกับ · {month}",
        "en": "{client} · Invoice Detail · {month}",
        "ja": "{client} · 請求書明細 · {month}",
    },
    "tpl-erp-title": {
        "zh": "ERP_IMPORT · {client} · {month}",
        "th": "ERP_IMPORT · {client} · {month}",
        "en": "ERP_IMPORT · {client} · {month}",
        "ja": "ERP_IMPORT · {client} · {month}",
    },
    "tpl-print-title": {
        "zh": "{client} · 凭证装订清单 · {month}",
        "th": "{client} · ใบรายการเย็บเล่ม · {month}",
        "en": "{client} · Voucher Binding · {month}",
        "ja": "{client} · 証憑綴じ込み · {month}",
    },
    # ===== 信息块(顶部) =====
    "info-tax-id": {"zh": "税号", "th": "เลขประจำตัวผู้เสียภาษี", "en": "Tax ID", "ja": "税番号"},
    "info-branch": {"zh": "分公司", "th": "สาขา", "en": "Branch", "ja": "支店"},
    "info-period": {"zh": "期间", "th": "ช่วงเวลา", "en": "Period", "ja": "期間"},
    "info-doc-count": {
        "zh": "共 {n} 张",
        "th": "รวม {n} ฉบับ",
        "en": "Total: {n} docs",
        "ja": "計 {n} 件",
    },
    "info-generated-at": {
        "zh": "生成时间",
        "th": "สร้างเมื่อ",
        "en": "Generated at",
        "ja": "作成日時",
    },
    "info-generated-by": {
        "zh": "由 Mr.Pilot 生成",
        "th": "สร้างโดย Mr.Pilot",
        "en": "Generated by Mr.Pilot",
        "ja": "Mr.Pilotで作成",
    },
    "info-head-office": {"zh": "总公司", "th": "สำนักงานใหญ่", "en": "Head Office", "ja": "本社"},
    "info-branch-office": {"zh": "分公司", "th": "สาขา", "en": "Branch Office", "ja": "支店"},
    # ===== 合计行 =====
    "report-total": {"zh": "合计", "th": "รวม", "en": "Total", "ja": "合計"},
    "report-grand-total": {
        "zh": "总合计",
        "th": "ยอดรวมทั้งสิ้น",
        "en": "Grand Total",
        "ja": "総合計",
    },
    "report-subtotal": {"zh": "小计", "th": "ยอดย่อย", "en": "Subtotal", "ja": "小計"},
    # ===== 第二 Sheet · 汇总分析 =====
    "summary-sheet-name": {"zh": "汇总分析", "th": "สรุป", "en": "Summary", "ja": "集計分析"},
    "summary-by-seller": {
        "zh": "按卖方汇总 (TOP 10)",
        "th": "สรุปตามผู้ขาย (TOP 10)",
        "en": "By Seller (TOP 10)",
        "ja": "売主別 (TOP 10)",
    },
    "summary-by-category": {
        "zh": "按类目汇总",
        "th": "สรุปตามหมวดหมู่",
        "en": "By Category",
        "ja": "カテゴリ別",
    },
    "summary-by-source": {
        "zh": "按来源汇总",
        "th": "สรุปตามแหล่งที่มา",
        "en": "By Source",
        "ja": "ソース別",
    },
    "summary-rank": {"zh": "排名", "th": "อันดับ", "en": "Rank", "ja": "順位"},
    "summary-count": {"zh": "张数", "th": "จำนวน", "en": "Count", "ja": "件数"},
    "summary-amount": {"zh": "金额", "th": "จำนวนเงิน", "en": "Amount", "ja": "金額"},
    "summary-percent": {"zh": "占比", "th": "ร้อยละ", "en": "Share", "ja": "占有率"},
    # ===== 来源标记 =====
    "source-email": {"zh": "邮件", "th": "อีเมล", "en": "Email", "ja": "メール"},
    "source-folder": {"zh": "文件夹", "th": "โฟลเดอร์", "en": "Folder", "ja": "フォルダ"},
    "source-scan": {"zh": "扫描", "th": "สแกน", "en": "Scan", "ja": "スキャン"},
    "source-upload": {"zh": "上传", "th": "อัปโหลด", "en": "Upload", "ja": "アップロード"},
    "source-manual": {"zh": "手动", "th": "ป้อนเอง", "en": "Manual", "ja": "手動"},
    "source-api": {"zh": "API", "th": "API", "en": "API", "ja": "API"},
    "source-line": {"zh": "LINE", "th": "LINE", "en": "LINE", "ja": "LINE"},
    # ===== 签名栏 =====
    "sig-prepared-by": {"zh": "制表人", "th": "ผู้จัดทำ", "en": "Prepared by", "ja": "作成者"},
    "sig-reviewed-by": {"zh": "审核人", "th": "ผู้ตรวจสอบ", "en": "Reviewed by", "ja": "確認者"},
    "sig-approved-by": {"zh": "负责人", "th": "ผู้อนุมัติ", "en": "Approved by", "ja": "承認者"},
    "sig-date": {"zh": "日期", "th": "วันที่", "en": "Date", "ja": "日付"},
    # ===== 默认占位 =====
    "client-default": {
        "zh": "全部客户",
        "th": "ลูกค้าทั้งหมด",
        "en": "All Clients",
        "ja": "全顧客",
    },
    "month-all": {"zh": "全部期间", "th": "ทุกช่วงเวลา", "en": "All Periods", "ja": "全期間"},
}


def i18n_get(lang: str, key: str, default: str = "") -> str:
    """
    后端 i18n 取键 · 找不到返回 default 或 key 本身
    lang: zh / th / en / ja(其他自动 fallback 到 en)
    """
    if lang not in ("zh", "th", "en", "ja"):
        lang = "en"
    entry = REPORTS_I18N.get(key)
    if not entry:
        return default or key
    return entry.get(lang) or entry.get("en") or default or key


def i18n_format(lang: str, key: str, **kwargs) -> str:
    """带占位符的版本 · 例如 i18n_format('zh', 'tpl-input-vat-title', client='X', month='2026-05')"""
    template = i18n_get(lang, key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


# 自检:启动时校验 4 语言是否都齐
def _self_check():
    missing = []
    for key, entry in REPORTS_I18N.items():
        for lang in ("zh", "th", "en", "ja"):
            if lang not in entry or not entry[lang]:
                missing.append(f"{key}.{lang}")
    if missing:
        import sys

        print(
            f"[i18n_reports] MISSING TRANSLATIONS: {missing[:5]}... total={len(missing)}",
            file=sys.stderr,
        )
    return len(missing) == 0


_I18N_OK = _self_check()
