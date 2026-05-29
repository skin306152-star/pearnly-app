# -*- coding: utf-8 -*-
"""OCR schemas · 非发票文档(GL/银行对账单/VAT报告/通用表)(REFACTOR-WA · R20 拆 · 0 逻辑改)。"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator
from services.ocr.schemas_layer1 import FieldRef

# ============================================================
# Multi-document Layer 2 schemas (2026-05-21 refactor)
# ============================================================
# Each non-invoice document type has its own row schema + document schema.
# The Layer 2 prompt is selected per document_type — see layer2_structure.py.
# Validators (validators.py) enforce that amount fields source from the
# correct columns (Debit/Credit for GL, deposit/withdrawal/balance for bank
# statement, etc.) — this is what prevents 6091-style description numbers
# from being mis-parsed as amounts.


class GLEntry(BaseModel):
    """One row of a General Ledger.

    Field-source contract (enforced by validators.validate_gl_entry):
    - debit / credit / balance MUST come from their respective columns
    - amount = debit if debit > 0 else credit (derived, signed)
    - direction = 'deposit' (debit > 0) | 'withdrawal' (credit > 0) | ''
    - description / voucher_no / account_code numbers (e.g. 6091, JV681130.1,
      QP10280137, 1112-07) MUST NOT appear in debit/credit/amount/balance
    """

    transaction_date: str = Field(default="", description="YYYY-MM-DD or empty")
    transaction_date_raw: str = Field(default="", description="date text as printed")
    voucher_no: str = Field(default="", description="voucher/document number, e.g. JV681130.1")
    account_code: str = Field(default="", description="account code, e.g. 1112-07")
    description: str = Field(
        default="",
        description="row description text — may contain numbers like '6091' "
        "that MUST NOT be treated as amounts",
    )
    debit: str = Field(
        default="", description="debit amount, number-as-string no commas; empty = no debit"
    )
    credit: str = Field(
        default="", description="credit amount, number-as-string no commas; empty = no credit"
    )
    amount: str = Field(
        default="",
        description="derived: debit if debit>0 else credit (number-as-string). "
        "Always sourced from Debit/Credit column — never description.",
    )
    direction: Literal["deposit", "withdrawal", ""] = Field(
        default="",
        description="'deposit' = bank goes up (debit>0); 'withdrawal' = bank goes down (credit>0)",
    )
    balance: str = Field(default="", description="running balance, number-as-string")

    # Provenance: where did each numeric field come from?
    debit_ref: Optional[FieldRef] = Field(default=None)
    credit_ref: Optional[FieldRef] = Field(default=None)
    balance_ref: Optional[FieldRef] = Field(default=None)

    raw_row_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="original column→cell mapping for audit / re-parse",
    )

    @field_validator(
        "transaction_date",
        "transaction_date_raw",
        "voucher_no",
        "account_code",
        "description",
        "debit",
        "credit",
        "amount",
        "balance",
        mode="before",
    )
    @classmethod
    def _coerce_gl_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("direction", mode="before")
    @classmethod
    def _coerce_direction(cls, v):
        if v is None or v == "":
            return ""
        if v in ("deposit", "withdrawal"):
            return v
        return ""

    @field_validator("raw_row_data", mode="before")
    @classmethod
    def _coerce_raw_row(cls, v):
        return {} if v is None else v


class GeneralLedgerDocument(BaseModel):
    """A GL document — many rows + summary metadata."""

    document_type: Literal["general_ledger"] = "general_ledger"
    period_start: str = Field(default="", description="YYYY-MM-DD or empty")
    period_end: str = Field(default="", description="YYYY-MM-DD or empty")
    account_name: str = Field(default="", description="bank account / GL account name")
    account_number: str = Field(default="", description="account number if printed")
    opening_balance: str = Field(default="")
    closing_balance: str = Field(default="")
    entries: List[GLEntry] = Field(default_factory=list)

    # v118.35.0.51 · 顶层 str 字段 None→"" 兜底(同 BankStatementDocument)
    @field_validator(
        "period_start",
        "period_end",
        "account_name",
        "account_number",
        "opening_balance",
        "closing_balance",
        mode="before",
    )
    @classmethod
    def _coerce_gl_doc_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("entries", mode="before")
    @classmethod
    def _coerce_entries(cls, v):
        return [] if v is None else v


class BankStatementEntry(BaseModel):
    """One row of a Bank Statement.

    Field-source contract (enforced by validators.validate_bank_entry):
    - deposit / withdrawal / balance MUST come from their respective columns
    - amount = deposit if deposit > 0 else withdrawal
    - description / reference number text MUST NOT be assigned to amount
    """

    transaction_date: str = Field(default="")
    transaction_date_raw: str = Field(default="")
    description: str = Field(default="")
    reference: str = Field(default="", description="reference / transaction code")
    deposit: str = Field(default="", description="money in / เงินเข้า / credit column")
    withdrawal: str = Field(default="", description="money out / เงินออก / debit column")
    amount: str = Field(default="", description="derived: deposit if deposit>0 else withdrawal")
    direction: Literal["deposit", "withdrawal", ""] = Field(default="")
    balance: str = Field(default="", description="running balance")

    deposit_ref: Optional[FieldRef] = Field(default=None)
    withdrawal_ref: Optional[FieldRef] = Field(default=None)
    balance_ref: Optional[FieldRef] = Field(default=None)

    # v118.35.0.11 · raw_row_data 字段从 BankStatementEntry 删除 · 80+ 行流水 ×
    # 每行 ~150 token raw_row_data dict = 输出超 8192 → JSON 截断 · 改后 token
    # 预算砍掉一半 · 跟 max_output_tokens 16384 一起把截断率压到 0

    @field_validator(
        "transaction_date",
        "transaction_date_raw",
        "description",
        "reference",
        "deposit",
        "withdrawal",
        "amount",
        "balance",
        mode="before",
    )
    @classmethod
    def _coerce_bank_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("direction", mode="before")
    @classmethod
    def _coerce_direction(cls, v):
        if v is None or v == "":
            return ""
        if v in ("deposit", "withdrawal"):
            return v
        return ""


class BankStatementDocument(BaseModel):
    document_type: Literal["bank_statement"] = "bank_statement"
    bank_name: str = Field(default="")
    bank_code: str = Field(default="", description="kbank/bbl/scb/etc. or empty")
    account_name: str = Field(default="")
    account_number: str = Field(default="")
    account_last4: str = Field(default="")
    period_start: str = Field(default="")
    period_end: str = Field(default="")
    opening_balance: str = Field(default="")
    closing_balance: str = Field(default="")
    entries: List[BankStatementEntry] = Field(default_factory=list)

    # v118.35.0.51 · 顶层 str 字段 None→"" 兜底(Gemini 对续页/无期初常返 null · 否则 schema 崩)
    @field_validator(
        "bank_name",
        "bank_code",
        "account_name",
        "account_number",
        "account_last4",
        "period_start",
        "period_end",
        "opening_balance",
        "closing_balance",
        mode="before",
    )
    @classmethod
    def _coerce_doc_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("entries", mode="before")
    @classmethod
    def _coerce_entries(cls, v):
        return [] if v is None else v


class VatReportEntry(BaseModel):
    """One row of a VAT report (销项/进项税报告)."""

    seq_no: str = Field(default="", description="row sequence number on report")
    transaction_date: str = Field(default="")
    transaction_date_raw: str = Field(default="")
    invoice_no: str = Field(default="")
    customer_name: str = Field(default="")
    customer_tax: str = Field(default="", description="13-digit Thai tax ID")
    customer_branch: str = Field(default="", description="买方分公司 / สำนักงานใหญ่ etc.")
    subtotal: str = Field(default="", description="净额, number-as-string")
    vat: str = Field(default="")
    total: str = Field(default="")

    invoice_no_ref: Optional[FieldRef] = Field(default=None)
    subtotal_ref: Optional[FieldRef] = Field(default=None)
    vat_ref: Optional[FieldRef] = Field(default=None)
    total_ref: Optional[FieldRef] = Field(default=None)

    raw_row_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "seq_no",
        "transaction_date",
        "transaction_date_raw",
        "invoice_no",
        "customer_name",
        "customer_tax",
        "customer_branch",
        "subtotal",
        "vat",
        "total",
        mode="before",
    )
    @classmethod
    def _coerce_vat_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("raw_row_data", mode="before")
    @classmethod
    def _coerce_raw_row(cls, v):
        return {} if v is None else v


class VatReportDocument(BaseModel):
    document_type: Literal["vat_report"] = "vat_report"
    seller_name: str = Field(default="", description="申报方公司名 (报告主体)")
    seller_tax: str = Field(default="")
    period_year: str = Field(default="", description="public year, e.g. '2026'")
    period_month: str = Field(default="", description="'01'..'12'")
    total_subtotal: str = Field(default="")
    total_vat: str = Field(default="")
    total_total: str = Field(default="")
    entries: List[VatReportEntry] = Field(default_factory=list)

    @field_validator("entries", mode="before")
    @classmethod
    def _coerce_entries(cls, v):
        return [] if v is None else v


class GenericTableDocument(BaseModel):
    """Fallback for unknown document types — just preserves the table grid."""

    document_type: Literal["generic_table"] = "generic_table"
    headers: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("headers", mode="before")
    @classmethod
    def _coerce_headers(cls, v):
        return [] if v is None else v

    @field_validator("rows", mode="before")
    @classmethod
    def _coerce_rows(cls, v):
        return [] if v is None else v


NonInvoiceDocument = Union[
    GeneralLedgerDocument,
    BankStatementDocument,
    VatReportDocument,
    GenericTableDocument,
]
