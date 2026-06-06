# -*- coding: utf-8 -*-
"""销项单据路由的请求模型(从 sales_routes.py 抽出 · 单一职责)。

金额按 docs/04 一律字符串化传输,这里只做形状/范围校验;业务归一化在 services/sales。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LineIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    product_id: Optional[str] = Field(None, max_length=64)
    qty: float = Field(1, ge=0)
    unit_price: float = Field(0, ge=0)
    discount: float = Field(0, ge=0)
    discount_pct: Optional[float] = Field(None, ge=0, le=100)
    vat_applicable: bool = True


class BuyerIn(BaseModel):
    """买方块(docs/15)。type 决定 tax_id 语义与分店是否适用;后端再归一化+校验。"""

    type: str = Field("company", max_length=20)
    name: Optional[str] = Field(None, max_length=300)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=40)
    branch_type: Optional[str] = Field(None, max_length=10)
    branch_no: Optional[str] = Field(None, max_length=10)


class PaymentIn(BaseModel):
    """收款块(docs/16 §J2)。收据/合并单开出前必须已收款。"""

    status: str = Field("unpaid", max_length=12)
    paid_amount: float = Field(0, ge=0)
    method: Optional[str] = Field(None, max_length=20)
    date: Optional[str] = Field(None, description="YYYY-MM-DD")


class DocumentIn(BaseModel):
    doc_type: str = Field("tax_invoice", max_length=40)
    client_id: Optional[int] = None
    seller_workspace_client_id: Optional[int] = None
    currency: str = Field("THB", max_length=8)
    vat_rate: float = Field(7, ge=0, le=100)
    wht_rate: float = Field(0, ge=0, le=100)
    header_discount_amount: float = Field(0, ge=0)
    header_discount_pct: float = Field(0, ge=0, le=100)
    price_includes_vat: bool = Field(False, description="价内含税(§C·单据级·默认价外)")
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD · 账期到期日")
    payment_terms: Optional[str] = Field(None, max_length=200)
    lines: list[LineIn] = Field(..., min_length=1)
    buyer: Optional[BuyerIn] = None
    payment: Optional[PaymentIn] = None


class IssueIn(BaseModel):
    prefix: Optional[str] = Field(None, max_length=20)
    reset: str = Field("yearly")
    issue_date: Optional[str] = Field(None, description="YYYY-MM-DD · 默认今天")


class RejectIn(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class NoteIn(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)
    vat_rate: float = Field(7, ge=0, le=100)
    wht_rate: float = Field(0, ge=0, le=100)
    lines: list[LineIn] = Field(..., min_length=1)
    prefix: Optional[str] = Field(None, max_length=20)
    reset: str = Field("yearly")
    issue_date: Optional[str] = Field(None, description="YYYY-MM-DD · 默认今天")


class ConvertIn(BaseModel):
    """报价单转换(§L3):目标单据类型。"""

    target_doc_type: str = Field("tax_invoice", max_length=40)
