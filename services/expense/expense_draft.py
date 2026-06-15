# -*- coding: utf-8 -*-
"""ExpenseDraft 模型(LINE 一句话记账捕获层 · docs/smart-intake/14 §3)。

文本路解析(line_quick_entry / line_l2)产出 ExpenseDraft,统一智能通道下直接落采购进项
草稿单(不再有独立 expense_draft 表 / 确认卡)。钱一律 Decimal(不用 float)。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


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
