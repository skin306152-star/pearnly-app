# -*- coding: utf-8 -*-
"""ExpenseDraft 模型 + 草稿表存取(LINE 一句话记账捕获层 · docs/smart-intake/14 §3)。

图片路(09)与文本路(10)共用同一套字段 —— 两路解析后都产出 ExpenseDraft,落同一张
expense_draft 表,下游 dedup/确认/复核一致。钱一律 Decimal(不用 float),时间存 UTC,
多租户走 tenant_id + workspace_client_id 隔离 + 参数化 SQL。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

# 与 services/ocr ThaiInvoice 同口径的票据类型(图/文共用)。
DOC_TYPES = ("tax_invoice", "simplified_tax_invoice", "receipt", "credit_note", "other", "")
DRAFT_STATUSES = ("draft", "confirmed", "discarded")


class ExpenseDraft(BaseModel):
    """一笔待确认的支出草稿。金额默认含税总额(裸数字即总额 · doc 10 §3)。"""

    amount: Optional[Decimal] = Field(default=None, description="总额(含税),Decimal")
    qty: Optional[Decimal] = Field(default=None)
    unit_price: Optional[Decimal] = Field(default=None)
    currency: str = Field(default="THB")
    expense_type: str = Field(default="", description="goods | service | ''")
    category: str = Field(default="", description="大类名(展示快照)")
    subcategory: str = Field(default="", description="子类名(展示快照)")
    category_id: Optional[str] = Field(default=None, description="链到 expense_categories 大类")
    subcategory_id: Optional[str] = Field(default=None, description="链到 expense_categories 子类")
    vendor_name: str = Field(default="")
    vendor_tax_id: str = Field(default="")
    invoice_number: str = Field(default="", description="原样保留前缀,简式不强制(09 §5)")
    doc_date: Optional[str] = Field(default=None, description="YYYY-MM-DD,缺省=今天")
    vat_mode: str = Field(default="included", description="none | vat7 | included")
    vat_amount: Optional[Decimal] = Field(default=None)
    wht_amount: Optional[Decimal] = Field(default=None)
    document_type: str = Field(default="")
    note: str = Field(default="")
    source: str = Field(default="line_text")
    raw_text: str = Field(default="")
    confidence: Decimal = Field(default=Decimal("0"))

    def has_amount(self) -> bool:
        return self.amount is not None and self.amount > 0


_COLS = (
    "source",
    "status",
    "line_user_id",
    "raw_text",
    "document_type",
    "amount",
    "qty",
    "unit_price",
    "currency",
    "expense_type",
    "category",
    "subcategory",
    "category_id",
    "subcategory_id",
    "vendor_name",
    "vendor_tax_id",
    "invoice_number",
    "doc_date",
    "vat_mode",
    "vat_amount",
    "wht_amount",
    "note",
    "confidence",
    "created_by",
)


def insert_draft(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    draft: ExpenseDraft,
    line_user_id: Optional[str] = None,
    created_by: Optional[str] = None,
    status: str = "draft",
) -> str:
    """插入一条草稿,返回 id。SQL 参数化 + 显式列(无 SELECT */无字符串拼值)。"""
    vals = {
        "source": draft.source,
        "status": status,
        "line_user_id": line_user_id,
        "raw_text": draft.raw_text,
        "document_type": draft.document_type,
        "amount": draft.amount,
        "qty": draft.qty,
        "unit_price": draft.unit_price,
        "currency": draft.currency,
        "expense_type": draft.expense_type,
        "category": draft.category,
        "subcategory": draft.subcategory,
        "category_id": draft.category_id,
        "subcategory_id": draft.subcategory_id,
        "vendor_name": draft.vendor_name,
        "vendor_tax_id": draft.vendor_tax_id,
        "invoice_number": draft.invoice_number,
        "doc_date": draft.doc_date,
        "vat_mode": draft.vat_mode,
        "vat_amount": draft.vat_amount,
        "wht_amount": draft.wht_amount,
        "note": draft.note,
        "confidence": draft.confidence,
        "created_by": created_by,
    }
    cols = ["tenant_id", "workspace_client_id", *_COLS]
    placeholders = ", ".join(["%s"] * len(cols))
    params = [tenant_id, workspace_client_id, *[vals[c] for c in _COLS]]
    cur.execute(
        f"INSERT INTO expense_draft ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return str(cur.fetchone()["id"])


def get_draft(cur, *, tenant_id: str, workspace_client_id: int, draft_id: str) -> Optional[dict]:
    """按 id 取草稿(作用域内);不存在 → None。"""
    cur.execute(
        "SELECT id, status, amount, qty, unit_price, currency, expense_type, category, subcategory, "
        "vendor_name, vendor_tax_id, invoice_number, doc_date, document_type, "
        "vat_amount, wht_amount, note, raw_text "
        "FROM expense_draft "
        "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s",
        (draft_id, tenant_id, workspace_client_id),
    )
    r = cur.fetchone()
    if not r:
        return None
    return {
        "id": str(r["id"]),
        "status": r["status"],
        "amount": r["amount"],
        "qty": r["qty"],
        "unit_price": r["unit_price"],
        "currency": r["currency"],
        "expense_type": r["expense_type"],
        "category": r["category"],
        "subcategory": r["subcategory"],
        "vendor_name": r["vendor_name"],
        "vendor_tax_id": r["vendor_tax_id"],
        "invoice_number": r["invoice_number"],
        "doc_date": r["doc_date"].isoformat() if r["doc_date"] else None,
        "document_type": r["document_type"],
        "vat_amount": r["vat_amount"],
        "wht_amount": r["wht_amount"],
        "note": r["note"],
        "raw_text": r["raw_text"],
    }


def set_status(
    cur, *, tenant_id: str, workspace_client_id: int, draft_id: str, status: str
) -> bool:
    """改草稿状态(confirmed/discarded);作用域内才改,返回是否命中。"""
    if status not in DRAFT_STATUSES:
        raise ValueError(f"invalid status: {status}")
    cur.execute(
        "UPDATE expense_draft SET status = %s, updated_at = now() "
        "WHERE id = %s AND tenant_id = %s AND workspace_client_id = %s",
        (status, draft_id, tenant_id, workspace_client_id),
    )
    return cur.rowcount > 0
