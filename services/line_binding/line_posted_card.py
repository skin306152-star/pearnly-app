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
from decimal import Decimal, InvalidOperation

from services.line_binding import line_card

_WEB = "https://pearnly.com/home"


def _s(v) -> str:
    return str(v).strip() if v not in (None, "") else ""


def _dec(v) -> Decimal:
    try:
        return Decimal(str(v).replace(",", "").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _breakdown(doc: dict) -> tuple[str, str, str]:
    """税前 / VAT / 舍入 —— 与识别卡 _card_amounts 同口径,确认前后一致(P1G·不把 VAT 置零)。

    费用单按行落库时 VAT 不可抵 → DB 存 subtotal=总额、vat=0;若直接显 DB 值会出「ก่อนภาษี 140 ·
    VAT 0」(与确认前卡矛盾)。故:DB 已拆且自洽的 VAT(真进项)→ 采信;税票(has_vat·有税号)但费用单
    未拆 → 按泰国 7% 票面拆解(140 → 130.84/9.16);非税票 → 不显拆解(不强凑 VAT)。
    """
    total = _dec(doc.get("grand_total"))
    sub = _dec(doc.get("subtotal"))
    vat = _dec(doc.get("vat_amount"))
    rnd = _dec(doc.get("rounding"))
    if vat > 0 and total > 0 and abs(sub + vat - total) <= Decimal("1.5"):
        rnd_str = f"{rnd:,.2f}" if abs(rnd) >= Decimal("0.005") else ""
        return f"{sub:,.2f}", f"{vat:,.2f}", rnd_str
    if doc.get("has_vat") and total > 0:
        v = (total * Decimal("7") / Decimal("107")).quantize(Decimal("0.01"))
        return f"{(total - v):,.2f}", f"{v:,.2f}", ""
    return "", "", ""


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
    subtotal, vat, rounding = _breakdown(doc)
    return {
        "date": _s(doc.get("doc_date")),
        "vendor": _s(sup.get("name")),
        "seller_tax": _s(sup.get("tax_id")),
        "seller_addr": _s(sup.get("address")),
        "invoice_number": _s(doc.get("doc_no")),
        "payment_method": _s(doc.get("payment_method")),
        "subtotal": subtotal,
        "vat": vat,
        "wht": _s(doc.get("wht_amount")),
        "rounding": rounding,
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
