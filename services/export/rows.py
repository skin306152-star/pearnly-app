# -*- coding: utf-8 -*-
"""进项明细 → 一行一明细导出行(纯转换 · 不连库 · 喂 excel.py / sheets.py)。

逆向 Paypers Sheet "一行=一条明细"(非一张票):一张单的 N 行明细展成 N 行,文档级字段
(日期/卖家/付款/过账)逐行重复,行级字段(描述/数量/单价/税前/VAT/分类)取自该行。
**比 Paypers 多**借方/贷方/凭证号/入账状态(来自做账分录,见 entries.summarize_voucher)。

VAT/WHT 逐行 = 行净额 × 率(镜像 purchase.totals 逐行取整);整单折扣/凑整是文档级,
落该单首行(Σ 行可还原文档合计)。category_names: 分类 id → 名(调用方查好传入)。
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")

# (key, 表头)· rows.py 与 excel.py / sheets.py 共用此列序(单一真源)。
COLUMNS = [
    ("doc_date", "日期"),
    ("doc_id", "单据ID"),
    ("doc_no", "税票号"),
    ("doc_kind", "单据类型"),
    ("payment_status", "付款状态"),
    ("has_vat", "有进项税票"),
    ("description", "描述"),
    ("qty", "数量"),
    ("unit_price", "单价"),
    ("line_net", "税前"),
    ("line_discount", "行折扣"),
    ("doc_discount", "整单折扣"),
    ("vat_rate", "VAT率"),
    ("line_vat", "VAT"),
    ("wht_rate", "WHT率"),
    ("line_wht", "WHT"),
    ("rounding", "四舍五入"),
    ("item_type", "费用性质"),
    ("category", "大类"),
    ("subcategory", "小类"),
    ("supplier_name", "卖家"),
    ("supplier_tax_id", "卖家税号"),
    ("branch_type", "分店类型"),
    ("branch_no", "分店码"),
    ("supplier_address", "卖家地址"),
    ("requester", "经手成员"),
    ("debit", "借方科目"),
    ("credit", "贷方科目"),
    ("voucher_no", "凭证号"),
    ("posting_status", "入账状态"),
    ("evidence", "证据"),
    ("note", "备注"),
]

_DOC_KIND = {"purchase_invoice": "进货发票", "purchase_order": "采购订单", "expense": "费用"}
_PAY_STATUS = {"paid": "已付", "unpaid": "未付", "partial": "部分付"}
_ITEM_TYPE = {"goods": "商品", "service": "服务"}


def _d(v) -> Decimal:
    try:
        return Decimal(str(v if v is not None else 0))
    except (ValueError, ArithmeticError):
        return Decimal("0")


def _q(v: Decimal) -> Decimal:
    return v.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def _line_rows(item: dict, category_names: dict) -> list:
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
                "doc_kind": _DOC_KIND.get(doc.get("doc_kind"), doc.get("doc_kind") or ""),
                "payment_status": _PAY_STATUS.get(
                    doc.get("payment_status"), doc.get("payment_status") or ""
                ),
                "has_vat": "是" if doc.get("has_vat") else "否",
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
                "item_type": _ITEM_TYPE.get(ln.get("item_type"), ln.get("item_type") or ""),
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
                "posting_status": posting.get("status_label", "未记账"),
                "evidence": item.get("evidence_url") or "",
                "note": "",
            }
        )
    return rows


def build_export_rows(items: list, *, category_names: Optional[dict] = None) -> list:
    """[{doc,lines,supplier,posting,evidence_url}] → 一行一明细导出行(扁平 dict 列表)。

    items 由调用方按套账隔离查好(get_doc 形态 + entries.get_posting_for_source 摘要)。
    无明细行的单据(理论不存在,_validate_lines 拦)→ 跳过不产空行。
    """
    cats = category_names or {}
    out = []
    for item in items or []:
        out.extend(_line_rows(item, cats))
    return out
