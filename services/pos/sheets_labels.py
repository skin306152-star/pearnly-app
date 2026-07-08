# -*- coding: utf-8 -*-
"""POS Google Sheet 留档表头 + 付款方式标签字典(从 sheets_sync.py 拆出 · SRP · 控单文件 <500)。

表头随建表当下老板后台的界面语言走(th/en/zh/ja,同 static/i18n-data.js 四语),不写死中文;
语言选定后随 pos_sheets_settings.header_lang 落库固定,之后每笔追加都用同一语言,不随收银员
当下语言漂移(否则同一张表列头和内容语言前后不一致)。
"""

from __future__ import annotations

LANGS = ("th", "en", "zh", "ja")

_HEADER_LABELS = {
    "receipt_no": {
        "th": "เลขที่ใบเสร็จ",
        "en": "Receipt No.",
        "zh": "收据号",
        "ja": "レシート番号",
    },
    "date": {"th": "วันที่", "en": "Date", "zh": "日期", "ja": "日付"},
    "time": {"th": "เวลา", "en": "Time", "zh": "时间", "ja": "時刻"},
    "cashier": {"th": "แคชเชียร์", "en": "Cashier", "zh": "收银员", "ja": "レジ担当"},
    "items": {"th": "รายการสินค้า", "en": "Items", "zh": "商品明细", "ja": "商品明細"},
    "qty_total": {"th": "จำนวนรวม", "en": "Total Qty", "zh": "商品数量合计", "ja": "合計数量"},
    "subtotal": {
        "th": "ยอดก่อนภาษี",
        "en": "Subtotal (excl. VAT)",
        "zh": "小计(未税)",
        "ja": "小計(税抜)",
    },
    "discount": {"th": "ส่วนลด", "en": "Discount", "zh": "折扣", "ja": "割引"},
    "vat": {"th": "ภาษีมูลค่าเพิ่ม", "en": "VAT", "zh": "VAT 税额", "ja": "消費税"},
    "grand_total": {"th": "ยอดรวมสุทธิ", "en": "Grand Total", "zh": "总额", "ja": "合計金額"},
    "method": {"th": "วิธีชำระเงิน", "en": "Payment Method", "zh": "付款方式", "ja": "支払方法"},
    "paid": {"th": "จำนวนที่รับ", "en": "Amount Paid", "zh": "实收金额", "ja": "お預かり金額"},
    "change": {"th": "เงินทอน", "en": "Change", "zh": "找零", "ja": "お釣り"},
}

_HEADER_KEYS = (
    "receipt_no",
    "date",
    "time",
    "cashier",
    "items",
    "qty_total",
    "subtotal",
    "discount",
    "vat",
    "grand_total",
    "method",
    "paid",
    "change",
)

_PAYMENT_METHOD_LABEL = {
    "cash": {"th": "เงินสด", "en": "Cash", "zh": "现金", "ja": "現金"},
    "transfer": {"th": "โอนเงิน", "en": "Bank Transfer", "zh": "银行转账", "ja": "銀行振込"},
    "card": {"th": "บัตร", "en": "Card", "zh": "刷卡", "ja": "カード"},
    "promptpay": {"th": "พร้อมเพย์", "en": "PromptPay", "zh": "PromptPay", "ja": "PromptPay"},
}


def norm_lang(raw: str) -> str:
    return raw if raw in LANGS else "th"


def header_row(lang: str) -> list:
    lg = norm_lang(lang)
    return [_HEADER_LABELS[k][lg] for k in _HEADER_KEYS]


def method_label(method: str, lang: str) -> str:
    lg = norm_lang(lang)
    entry = _PAYMENT_METHOD_LABEL.get(method or "")
    return entry[lg] if entry else (method or "")
