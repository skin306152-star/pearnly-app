# -*- coding: utf-8 -*-
"""
services/recon/gl_vat_types.py · Pearnly

Dataclasses for GL-vs-VAT reconciliation (gl_vat_reconciler). Leaf module —
breaks import cycles between the parser / reconcile / export layers.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


# ─────────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────────
@dataclass
class GlRow:
    doc_no: str  # 原始凭证号 (ใบสำคัญ)
    norm_doc_no: str  # 归一化后
    date: str
    account_code: str  # 4110-01 等
    description: str
    debit: float
    credit: float


@dataclass
class ReconRow:
    doc_no: str  # 来自 VAT 报表的参考单号
    date: str
    customer_name: str
    vat_amount: float  # 税前金额 from VAT report
    gl_amount: Optional[float]
    diff: Optional[float]
    account_codes: str  # 去重逗号拼接


@dataclass
class GlVatSummary:
    gl_total: float
    gl_only_credit: float  # 不在 VAT 中的 GL 行贷方汇总（正数）
    gl_only_debit: float  # 不在 VAT 中的 GL 行借方汇总（正数）
    vat_only_positive: float  # 不在 GL 中的 VAT 正数汇总
    vat_only_negative: float  # 不在 GL 中的 VAT 负数汇总（已为负）
    vat_total: float
    # v118.32.5.5.11 · 调整项明细(Korn 反馈:汇总不只显示金额 · 要展开单据明细)
    gl_only_credit_items: List[Dict[str, Any]] = None  # [{doc_no, date, desc, amount}]
    gl_only_debit_items: List[Dict[str, Any]] = None
    vat_only_positive_items: List[Dict[str, Any]] = None  # [{doc_no, date, customer_name, amount}]
    vat_only_negative_items: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.gl_only_credit_items is None:
            self.gl_only_credit_items = []
        if self.gl_only_debit_items is None:
            self.gl_only_debit_items = []
        if self.vat_only_positive_items is None:
            self.vat_only_positive_items = []
        if self.vat_only_negative_items is None:
            self.vat_only_negative_items = []
