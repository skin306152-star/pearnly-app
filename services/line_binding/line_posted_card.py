# -*- coding: utf-8 -*-
"""LINE 入账成功 / 当前状态数据卡(P1G 入账后闭环)。

确认入账后(卡片 postback 确认 / 重复点击),回的不再是单行文字,而是与高置信自动入账同款的
posted 数据卡:状态徽章「已保存」+ 金额 + 日期 + 卖家 + 记录号 +「ดูรายการ/查看详情」+
「ยกเลิก/撤销」(验收 1)。重复点击 → 按单据真实状态重发当前卡(posted 重发 posted 卡 /
已作废回终态卡),不重复入账、不出不可执行动作、不跳登录(验收 2/6)。

纯构建(无 IO):把 purchase_doc 详情(get_doc)映射成与识别卡同一套字段键,复用 line_card.result_card。
"""

from __future__ import annotations

import os

from services.line_binding import line_card

_WEB = "https://pearnly.com/home"


def _s(v) -> str:
    return str(v).strip() if v not in (None, "") else ""


def fields_from_detail(detail: dict) -> dict:
    """purchase_doc 详情 → 卡片字段(只取真实落库值·与识别卡同一套键·空字段不上卡)。"""
    doc = (detail or {}).get("doc") or {}
    sup = (detail or {}).get("supplier") or {}
    lines = (detail or {}).get("lines") or []
    items = [
        {"name": _s(ln.get("description")), "amount": _s(ln.get("line_total"))}
        for ln in lines
        if _s(ln.get("description"))
    ]
    return {
        "date": _s(doc.get("doc_date")),
        "vendor": _s(sup.get("name")),
        "seller_tax": _s(sup.get("tax_id")),
        "seller_addr": _s(sup.get("address")),
        "invoice_number": _s(doc.get("doc_no")),
        "payment_method": _s(doc.get("payment_method")),
        "subtotal": _s(doc.get("subtotal")),
        "vat": _s(doc.get("vat_amount")),
        "wht": _s(doc.get("wht_amount")),
        "rounding": _s(doc.get("rounding")),
        "discount": _s(doc.get("discount_total")),
        "items": items,
    }


def build(detail: dict, *, doc_id, lang, workspace_client_id="", source="doc", token="") -> dict:
    """已入账(posted)数据卡。撤销按钮走 token(空=无 token 兼容链路·void_doc 幂等防双撤)。"""
    doc = (detail or {}).get("doc") or {}
    return line_card.result_card(
        state="posted",
        amount=doc.get("grand_total"),
        fields=fields_from_detail(detail),
        doc_id=str(doc_id or ""),
        lang=lang,
        web_url=_WEB,
        source=source,
        token=token,
        liff_id=os.getenv("LINE_LIFF_ID", "").strip(),
        workspace_client_id=str(workspace_client_id or ""),
    )
