# -*- coding: utf-8 -*-
"""进项明细 → 一行一明细导出行(纯转换 · 不连库 · 喂 excel.py / sheets.py)。

逆向 Paypers Sheet "一行=一条明细"(非一张票):一张单的 N 行明细展成 N 行,文档级字段
(日期/卖家/付款/过账)逐行重复,行级字段(描述/数量/单价/税前/VAT/分类)取自该行。
**比 Paypers 多**借方/贷方/凭证号/入账状态(来自做账分录,见 entries.summarize_voucher)。

VAT/WHT 逐行 = 行净额 × 率(镜像 purchase.totals 逐行取整);整单折扣/凑整是文档级,
落该单首行(Σ 行可还原文档合计)。category_names: 分类 id → 名(调用方查好传入)。

列头 + 枚举值随 lang 4 语(zh/en/th/ja)· 导出文件跟随用户语言,不写死中文(默认 zh 向后兼容)。
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")

# 列序(单一真源)· rows.py 与 excel.py / sheets.py 共用。表头按 lang 取(headers())。
COLUMN_KEYS = [
    "doc_date", "doc_id", "doc_no", "doc_kind", "payment_status", "has_vat",
    "description", "qty", "unit_price", "line_net", "line_discount", "doc_discount",
    "vat_rate", "line_vat", "wht_rate", "line_wht", "rounding", "item_type",
    "category", "subcategory", "supplier_name", "supplier_tax_id", "branch_type",
    "branch_no", "supplier_address", "requester", "debit", "credit", "voucher_no",
    "posting_status", "evidence", "note",
]  # fmt: skip

_HEADERS = {
    "zh": ["日期", "单据ID", "税票号", "单据类型", "付款状态", "有进项税票", "描述", "数量",
           "单价", "税前", "行折扣", "整单折扣", "VAT率", "VAT", "WHT率", "WHT", "四舍五入",
           "费用性质", "大类", "小类", "卖家", "卖家税号", "分店类型", "分店码", "卖家地址",
           "经手成员", "借方科目", "贷方科目", "凭证号", "入账状态", "证据", "备注"],
    "en": ["Date", "Doc ID", "Tax invoice no.", "Doc type", "Payment status", "Has input VAT",
           "Description", "Qty", "Unit price", "Pre-tax", "Line discount", "Doc discount",
           "VAT rate", "VAT", "WHT rate", "WHT", "Rounding", "Expense type", "Category",
           "Subcategory", "Supplier", "Supplier tax ID", "Branch type", "Branch code",
           "Supplier address", "Handled by", "Debit account", "Credit account", "Voucher no.",
           "Posting status", "Evidence", "Note"],
    "th": ["วันที่", "รหัสเอกสาร", "เลขที่ใบกำกับ", "ประเภทเอกสาร", "สถานะชำระ", "มีภาษีซื้อ",
           "รายละเอียด", "จำนวน", "ราคาต่อหน่วย", "ก่อนภาษี", "ส่วนลดรายการ", "ส่วนลดทั้งใบ",
           "อัตรา VAT", "VAT", "อัตรา WHT", "WHT", "ปัดเศษ", "ประเภทค่าใช้จ่าย", "หมวดหลัก",
           "หมวดย่อย", "ผู้ขาย", "เลขภาษีผู้ขาย", "ประเภทสาขา", "รหัสสาขา", "ที่อยู่ผู้ขาย",
           "ผู้ดำเนินการ", "บัญชีเดบิต", "บัญชีเครดิต", "เลขที่ใบสำคัญ", "สถานะบันทึกบัญชี",
           "หลักฐาน", "หมายเหตุ"],
    "ja": ["日付", "伝票ID", "税票番号", "伝票種別", "支払状況", "仕入税あり", "摘要", "数量",
           "単価", "税抜", "明細値引", "伝票値引", "VAT率", "VAT", "WHT率", "WHT", "端数処理",
           "費用種別", "大分類", "小分類", "仕入先", "仕入先税番号", "支店種別", "支店コード",
           "仕入先住所", "担当者", "借方科目", "貸方科目", "証憑番号", "記帳状況", "証拠", "備考"],
}  # fmt: skip

# 列序 + 中文表头(向后兼容:旧导入 rows.COLUMNS 仍可用 · 等价 zip(COLUMN_KEYS, _HEADERS['zh']))
COLUMNS = list(zip(COLUMN_KEYS, _HEADERS["zh"]))


def headers(lang: str = "zh") -> list:
    """表头(按 lang)· 未知语言回退 zh。"""
    return _HEADERS.get(lang, _HEADERS["zh"])


_DOC_KIND = {
    "zh": {"purchase_invoice": "进货发票", "purchase_order": "采购订单", "expense": "费用"},
    "en": {"purchase_invoice": "Purchase invoice", "purchase_order": "Purchase order", "expense": "Expense"},
    "th": {"purchase_invoice": "ใบกำกับซื้อ", "purchase_order": "ใบสั่งซื้อ", "expense": "ค่าใช้จ่าย"},
    "ja": {"purchase_invoice": "仕入請求書", "purchase_order": "発注書", "expense": "費用"},
}  # fmt: skip
_PAY_STATUS = {
    "zh": {"paid": "已付", "unpaid": "未付", "partial": "部分付"},
    "en": {"paid": "Paid", "unpaid": "Unpaid", "partial": "Partial"},
    "th": {"paid": "ชำระแล้ว", "unpaid": "ยังไม่ชำระ", "partial": "ชำระบางส่วน"},
    "ja": {"paid": "支払済", "unpaid": "未払", "partial": "一部支払"},
}  # fmt: skip
_ITEM_TYPE = {
    "zh": {"goods": "商品", "service": "服务"},
    "en": {"goods": "Goods", "service": "Service"},
    "th": {"goods": "สินค้า", "service": "บริการ"},
    "ja": {"goods": "商品", "service": "サービス"},
}  # fmt: skip
_YES = {"zh": "是", "en": "Yes", "th": "ใช่", "ja": "はい"}
_NO = {"zh": "否", "en": "No", "th": "ไม่", "ja": "いいえ"}
_NOT_BOOKED = {"zh": "未记账", "en": "Not booked", "th": "ยังไม่บันทึกบัญชี", "ja": "未記帳"}
_VIEW = {"zh": "查看", "en": "View", "th": "ดู", "ja": "表示"}
_SHEET_TITLE = {
    "zh": "进项明细",
    "en": "Purchase details",
    "th": "รายละเอียดซื้อ",
    "ja": "仕入明細",
}


def _lang(lang: str) -> str:
    return lang if lang in _HEADERS else "zh"


def view_label(lang: str = "zh") -> str:
    """证据超链显示文案(按 lang)。"""
    return _VIEW.get(_lang(lang), _VIEW["zh"])


def sheet_title(lang: str = "zh") -> str:
    """导出工作表默认标题(按 lang · 调用方有套账主体名时优先用主体名)。"""
    return _SHEET_TITLE.get(_lang(lang), _SHEET_TITLE["zh"])


def _d(v) -> Decimal:
    try:
        return Decimal(str(v if v is not None else 0))
    except (ValueError, ArithmeticError):
        return Decimal("0")


def _q(v: Decimal) -> Decimal:
    return v.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def _line_rows(item: dict, category_names: dict, lang: str) -> list:
    doc = item.get("doc") or {}
    supplier = item.get("supplier") or {}
    posting = item.get("posting") or {}
    lines = item.get("lines") or []
    rows = []
    for idx, ln in enumerate(lines):
        net = _d(ln.get("line_total"))
        vat_rate = _d(ln.get("vat_rate")) if ln.get("vat_applicable", True) else Decimal("0")
        first = idx == 0
        rows.append(
            {
                "doc_date": doc.get("doc_date"),
                "doc_id": doc.get("id"),
                "doc_no": doc.get("doc_no"),
                "doc_kind": _DOC_KIND[lang].get(doc.get("doc_kind"), doc.get("doc_kind") or ""),
                "payment_status": _PAY_STATUS[lang].get(
                    doc.get("payment_status"), doc.get("payment_status") or ""
                ),
                "has_vat": _YES[lang] if doc.get("has_vat") else _NO[lang],
                "description": ln.get("description") or "",
                "qty": _d(ln.get("qty")),
                "unit_price": _d(ln.get("unit_price")),
                "line_net": net,
                "line_discount": _d(ln.get("discount")),
                # 文档级整单折扣/凑整落首行(Σ 行 = 文档合计)
                "doc_discount": _d(doc.get("discount_total")) if first else Decimal("0"),
                "vat_rate": vat_rate,
                "line_vat": _q(net * vat_rate / _HUNDRED),
                "wht_rate": _d(ln.get("wht_rate")),
                "line_wht": _q(net * _d(ln.get("wht_rate")) / _HUNDRED),
                "rounding": _d(doc.get("rounding")) if first else Decimal("0"),
                "item_type": _ITEM_TYPE[lang].get(ln.get("item_type"), ln.get("item_type") or ""),
                "category": category_names.get(str(ln.get("category_id")), ""),
                "subcategory": category_names.get(str(ln.get("subcategory_id")), ""),
                "supplier_name": supplier.get("name") or "",
                "supplier_tax_id": supplier.get("tax_id") or "",
                "branch_type": supplier.get("branch_type") or "",
                "branch_no": supplier.get("branch_no") or "",
                "supplier_address": supplier.get("address") or "",
                "requester": doc.get("requester") or "",
                "debit": posting.get("debit_text", ""),
                "credit": posting.get("credit_text", ""),
                "voucher_no": posting.get("voucher_no", ""),
                "posting_status": posting.get("status_label", _NOT_BOOKED[lang]),
                "evidence": item.get("evidence_url") or "",
                "note": "",
            }
        )
    return rows


def build_export_rows(
    items: list, *, category_names: Optional[dict] = None, lang: str = "zh"
) -> list:
    """[{doc,lines,supplier,posting,evidence_url}] → 一行一明细导出行(扁平 dict 列表)。

    items 由调用方按套账隔离查好(get_doc 形态 + entries.get_posting_for_source 摘要)。
    枚举值(单据类型/付款状态/费用性质/有无税票/入账状态)按 lang 本地化,默认 zh。
    无明细行的单据(理论不存在,_validate_lines 拦)→ 跳过不产空行。
    """
    cats = category_names or {}
    lg = _lang(lang)
    out = []
    for item in items or []:
        out.extend(_line_rows(item, cats, lg))
    return out
