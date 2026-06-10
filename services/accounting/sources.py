# -*- coding: utf-8 -*-
"""业务单 → 引擎上下文(只读 · 按套账取 · docs/accounting/02 引擎流程第一步)。

每种 source_type 一个 loader,产出 rules.build 吃的规范化 ctx(金额 Decimal 反解,不重算)。
source_tier 判定(C1 数据源分级):进项单 source 来自 OCR 入口(photo/line/email)= ocr,
手录 = first_party;销项/POS 在系统内发生 = 恒 first_party。
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal

_OCR_SOURCES = ("photo", "line", "email")


def load(
    cur, *, tenant_id: str, workspace_client_id: int, source_type: str, source_id, context=None
):
    """返回 ctx dict 或 None(单不存在/非可记账状态)。context 给 payment 等无独立行的事件。"""
    if source_type == "purchase":
        return _purchase(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=source_id
        )
    if source_type == "sale":
        return _sale(cur, tenant_id=tenant_id, doc_id=source_id)
    if source_type == "pos":
        return _pos(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=source_id
        )
    if source_type == "payment":
        return _payment(context or {})
    if source_type == "vat_closing":
        return _vat_closing(context or {})
    return None


def _today():
    return datetime.now(timezone.utc).date()


def _purchase(cur, *, tenant_id, workspace_client_id, doc_id):
    cur.execute(
        "SELECT doc_kind, doc_no, doc_date, supplier_id, source, status, "
        "subtotal, discount_total, vat_amount, wht_amount, rounding, grand_total, net_payable "
        "FROM purchase_docs WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, doc_id),
    )
    doc = cur.fetchone()
    if doc is None or doc["status"] != "posted":
        return None
    cur.execute(
        "SELECT item_type, product_id, description, line_total, category_id "
        "FROM purchase_lines WHERE tenant_id = %s AND purchase_doc_id = %s ORDER BY line_no",
        (tenant_id, doc_id),
    )
    lines = cur.fetchall()
    return {
        "source_type": "purchase",
        "source_tier": "ocr" if doc["source"] in _OCR_SOURCES else "first_party",
        "doc_kind": doc["doc_kind"],
        "amounts": {
            "grand_total": doc["grand_total"],
            "vat_amount": doc["vat_amount"],
            "wht_amount": doc["wht_amount"],
        },
        "lines": [dict(ln) for ln in lines],
        "ref": f"进项单 {doc['doc_no'] or str(doc_id)[:8]}",
        "voucher_date": doc["doc_date"] or _today(),
        "scope_keys": _purchase_scope_keys(doc, lines),
    }


def _purchase_scope_keys(doc, lines) -> list:
    """学习记忆查找键(优先级序):供应商 → 描述指纹。"""
    keys = []
    if doc.get("supplier_id"):
        keys.append(f"supplier:{doc['supplier_id']}")
    desc = next((ln["description"] for ln in lines if ln.get("description")), None)
    if desc:
        h = hashlib.sha256(desc.strip().lower().encode("utf-8")).hexdigest()[:16]
        keys.append(f"desc_hash:{h}")
    return keys


def _sale(cur, *, tenant_id, doc_id):
    cur.execute(
        "SELECT doc_type, doc_number, status, issue_date, grand_total, vat_amount, wht_amount, "
        "payment_status, paid_amount, payment_method "
        "FROM sales_documents WHERE tenant_id = %s AND id = %s",
        (tenant_id, doc_id),
    )
    doc = cur.fetchone()
    if doc is None or doc["status"] != "issued":
        return None
    return {
        "source_type": "sale",
        "source_tier": "first_party",
        "doc_kind": doc["doc_type"],
        "amounts": {
            "grand_total": doc["grand_total"],
            "vat_amount": doc["vat_amount"],
            "wht_amount": doc["wht_amount"],
            "paid_amount": doc["paid_amount"],
        },
        "paid_at_issue": doc["payment_status"] in ("paid", "partial"),
        "payment_method": doc["payment_method"],
        "ref": f"销售单 {doc['doc_number'] or str(doc_id)[:8]}",
        "voucher_date": doc["issue_date"] or _today(),
        "scope_keys": [],
    }


def _pos(cur, *, tenant_id, workspace_client_id, sale_id):
    cur.execute(
        "SELECT receipt_no, sale_type, status, sold_at, "
        "grand_total, vat_amount, paid_total, change_amount "
        "FROM pos_sales WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, sale_id),
    )
    sale = cur.fetchone()
    if sale is None or sale["status"] != "completed":
        return None
    cur.execute(
        "SELECT method, amount FROM pos_payments WHERE tenant_id = %s AND sale_id = %s",
        (tenant_id, sale_id),
    )
    cash = Decimal("0")
    bank = Decimal("0")
    for p in cur.fetchall():
        amt = Decimal(str(p["amount"] or 0))
        if p["method"] == "cash":
            cash += amt
        else:
            bank += amt
    cash -= Decimal(str(sale["change_amount"] or 0))
    payments = []
    if cash > 0:
        payments.append({"role": "cash", "amount": cash})
    if bank > 0:
        payments.append({"role": "bank", "amount": bank})
    return {
        "source_type": "pos",
        "source_tier": "first_party",
        "amounts": {"grand_total": sale["grand_total"], "vat_amount": sale["vat_amount"]},
        "payments": payments,
        "is_refund": sale["sale_type"] == "refund",
        "ref": f"POS 小票 {sale['receipt_no'] or str(sale_id)[:8]}",
        "voucher_date": (sale["sold_at"].date() if sale["sold_at"] else _today()),
        "scope_keys": [],
    }


def _payment(context: dict):
    """付款/收款事件没有独立行(进项付款只更新累计)→ 事件参数由挂点经 context 传入。"""
    if not context.get("amount"):
        return None
    return {
        "source_type": "payment",
        "source_tier": "first_party",
        "amounts": {"amount": context["amount"]},
        "direction": context.get("direction") or "out",
        "payment_method": context.get("payment_method"),
        "ref": context.get("ref") or "付款",
        "voucher_date": context.get("voucher_date") or _today(),
        "scope_keys": [],
    }


def _vat_closing(context: dict):
    if "output_vat_total" not in context:
        return None
    return {
        "source_type": "vat_closing",
        "source_tier": "first_party",
        "amounts": {
            "output_vat_total": context["output_vat_total"],
            "input_vat_total": context["input_vat_total"],
        },
        "ref": context.get("period") or "",
        "voucher_date": context.get("voucher_date") or _today(),
        "scope_keys": [],
    }
