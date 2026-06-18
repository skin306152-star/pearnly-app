# -*- coding: utf-8 -*-
"""票据字段展示清洗(P1F · 确定性纯函数 · 卡片与详情页共用同一套规则)。

目标:把明显异常值(短数字/日期片段当税号、纯金额/字段标签当卖家)判 invalid,UI 显示为空/
待补而非假值。只清洗展示值,不改 OCR 引擎、不改金额计算。raw 仍可留存供调试。

- clean_tax_id:泰国税号 = 恰好 13 位数字(剥分隔符);否则 ''(短数字/日期/含字母噪声全弃)。
- clean_seller:剥空白;纯金额/字段标签/日期/无内容/过短 → ''。
- clean_invoice_no:允许短号(与税号不同),但纯日期 → ''。
"""

from __future__ import annotations

import re

_AMOUNT_RE = re.compile(r"^[\d,]+(?:\.\d+)?$")
# 完整日期(DD/MM/YY[YY] 或 ISO)→ 不得当卖家/票号。单段「13」「2026」由金额规则兜住。
_FULL_DATE_RE = re.compile(r"^\d{1,4}[/\-.]\d{1,2}[/\-.]\d{2,4}$|^\d{4}-\d{2}-\d{2}$")
_ALNUM_RE = re.compile(r"[0-9A-Za-z฀-๿]")  # 至少含一个数字/拉丁/泰文字符才算有内容

# 卖家不得是这些字段标签/金额词(票面常见噪声·精确匹配·不误伤「Total Tools」这类真店名)。
_SELLER_STOPWORDS = frozenset(
    {
        "vat",
        "tax",
        "tax id",
        "tax invoice",
        "total",
        "subtotal",
        "sub total",
        "grand total",
        "net",
        "amount",
        "balance",
        "cash",
        "change",
        "qty",
        "discount",
        "ภาษีมูลค่าเพิ่ม",
        "ภาษี",
        "ภาษี 7%",
        "รวม",
        "รวมเงิน",
        "ยอดรวม",
        "ยอดสุทธิ",
        "สุทธิ",
        "เงินสด",
        "เงินทอน",
        "ส่วนลด",
        "จำนวนเงิน",
        "ใบกำกับภาษี",
        "เลขประจำตัวผู้เสียภาษี",
        "สาขา",
    }
)


def clean_tax_id(raw) -> str:
    """泰国税号 = 恰好 13 位数字(剥任何分隔符/文字)。否则判 invalid → ''。

    「13」「2026」「06」→ ''(位数不足);「13/06/26」→ 数字 130626 仅 6 位 → '';
    「0107561000013」→ 保留;「0105561000013 บริษัท」→ 取 13 位数字保留。
    """
    digits = re.sub(r"\D", "", str(raw or ""))
    return digits if len(digits) == 13 else ""


def clean_seller(raw) -> str:
    """卖家清洗:剥空白;纯金额/字段标签/完整日期/无内容/过短(<2)→ ''(不展示假值)。

    「1780.00」「Total」「VAT」「13」「13/06/26」→ '';「Bangchak」「บางจาก」「7-11」→ 保留。
    """
    s = str(raw or "").strip()
    if len(s) < 2 or not _ALNUM_RE.search(s):
        return ""
    if s.lower() in _SELLER_STOPWORDS:
        return ""
    if _AMOUNT_RE.match(s) or _FULL_DATE_RE.match(s):
        return ""
    return s


def clean_invoice_no(raw) -> str:
    """票号:允许短号(与税号不同);剥空白;纯日期片段 → ''(日期不当票号)。"""
    s = str(raw or "").strip()
    if not s or _FULL_DATE_RE.match(s):
        return ""
    return s


def clean_supplier_display(supplier: dict | None) -> dict | None:
    """详情页/卡片展示用:清洗 supplier 的 name/tax_id(invalid → None,不展示假值)。

    原值留在 DB(供调试/编辑补全)·仅清洗对外展示副本。supplier 为 None 原样返回。
    """
    if not supplier:
        return supplier
    out = dict(supplier)
    out["tax_id"] = clean_tax_id(out.get("tax_id")) or None
    out["name"] = clean_seller(out.get("name")) or None
    return out


def serialize_supplier(doc: dict) -> dict | None:
    """get_doc 用:从 doc 行抽 supplier(清洗税号/卖家)+ **同步清洗 doc 的扁平字段**。

    详情页/编辑表单(purchase-common.ts)优先读扁平 doc.supplier_tax_id/supplier_name(嵌套
    supplier 是 doc 的兄弟节点·前端取 doc.supplier 取不到)→ 必须把扁平字段也清,否则编辑页仍显「13」。
    无 supplier_id → None。会就地改 doc 的两个扁平字段(同一份 cleaned 供卡片/详情/保存共用)。
    """
    if not doc.get("supplier_id"):
        return None
    tax = clean_tax_id(doc.get("supplier_tax_id")) or None
    name = clean_seller(doc.get("supplier_name")) or None
    doc["supplier_tax_id"] = tax
    doc["supplier_name"] = name
    return {
        "id": doc["supplier_id"],
        "name": name,
        "tax_id": tax,
        "branch_type": doc.get("supplier_branch_type"),
        "branch_no": doc.get("supplier_branch_no"),
        "address": doc.get("supplier_address"),
        "phone": doc.get("supplier_phone"),
    }
