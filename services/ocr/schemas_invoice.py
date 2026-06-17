# -*- coding: utf-8 -*-
"""OCR schemas · 泰国税务发票(ThaiInvoice/LineItem + 值coercion)(REFACTOR-WA · R20 拆 · 0 逻辑改)。"""

import re
from datetime import date
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from services.ocr.schemas_layer1 import FieldRef

# 泰式 2 位年(DD/MM/YY)正则:两个分隔符 + 结尾 2 位年。
_TWO_DIGIT_DATE = re.compile(r"^\s*\d{1,2}[/\-.]\d{1,2}[/\-.](\d{2})\s*$")


def _fix_two_digit_year_date(date_raw: str, model_date: Optional[str], today_year: int):
    """泰式收据 2 位年消歧(B · 24/08/25 模型常猜成 2023)。
    只在 date_raw 是 DD/MM/YY 时介入,且只重算「年」(保留模型的 -MM-DD,避免日/月歧义):
    候选 = 公历 20YY 与 2 位佛历 25YY−543,取 [2000, 今年+1] 内最接近今天的那个。
    4 位年/非日期 → 原样交还模型(不干预 4 位佛历减 543 的既有逻辑)。"""
    if not model_date or not re.match(r"^\d{4}-\d{2}-\d{2}$", model_date):
        return model_date
    m = _TWO_DIGIT_DATE.match(date_raw or "")
    if not m:
        return model_date
    yy = int(m.group(1))
    cands = [y for y in (2000 + yy, 2500 + yy - 543) if 2000 <= y <= today_year + 1]
    if not cands:
        return model_date
    year = min(cands, key=lambda y: abs(today_year - y))
    return f"{year:04d}{model_date[4:]}"


_BE_YEAR_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")


def _fix_buddhist_year_date(date_raw: str, model_date: Optional[str], today_year: int):
    """4 位佛历年确定性减 543(不信 LLM 算术 · 铁律:换算用确定性代码)。

    票面印 4 位年(date_raw 如 "17/06/2569")时,以印出的年份为准做 BE−543,覆盖模型 date 的年(保留
    -MM-DD)。治模型把 2569 误算成 2023 这类。仅当结果落 [2000, 今年+1] 才采信。无 4 位佛历年 → 原样。"""
    if not model_date or not re.match(r"^\d{4}-\d{2}-\d{2}$", model_date):
        return model_date
    for m in _BE_YEAR_RE.finditer(date_raw or ""):
        be = int(m.group(1))
        if 2400 <= be <= 2700:
            ce = be - 543
            if 2000 <= ce <= today_year + 1:
                return f"{ce:04d}{model_date[4:]}"
    return model_date


# ============================================================
# Layer 2 schemas (Flash-Lite field extraction)
# ============================================================
def _coerce_to_str(v):
    """Permissive coercion for required string fields: None -> "", numbers -> str."""
    if v is None:
        return ""
    if isinstance(v, bool):
        # JSON booleans are not expected for string fields; stringify defensively
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return v


def _coerce_to_optional_str(v):
    """Coercion for Optional[str] fields: None stays None, numbers -> str,
    empty strings -> None (treats "" same as missing for consumers that
    do truthiness checks)."""
    if v is None:
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    if isinstance(v, str) and not v:
        return None
    return v


class LineItem(BaseModel):
    """A single line item in a Thai tax invoice.

    All numeric-looking fields stay as strings (no Decimal) for compatibility
    with the existing gemini_engine output schema and downstream consumers
    (mrerp_xlsx_generator reads these as strings; converting now would
    cascade-break consumers).
    """

    name: str = Field(default="", description="item description as printed")
    qty: str = Field(default="", description="quantity, number-as-string")
    price: str = Field(default="", description="unit price, number-as-string, no commas")
    subtotal: str = Field(default="", description="line subtotal, number-as-string, no commas")

    # Gemini may return null / number for any of these; coerce defensively.
    _str_coerce = field_validator("name", "qty", "price", "subtotal", mode="before")(_coerce_to_str)


class ThaiInvoice(BaseModel):
    """Structured Thai tax invoice fields, produced by layer 2.

    Field naming uses `_tax` suffix (NOT `_tax_id`) per migration-plan
    decision 2; this matches the existing gemini_engine output schema and
    keeps all downstream consumers working unchanged.

    Default values are chosen so that an empty / missing field passes
    validation while remaining distinguishable from "explicitly null":
        - strings  -> ""  (empty string)
        - optional -> None (Gemini was unable to extract)
        - lists    -> []
        - bools    -> False

    All numeric fields are strings (no commas, no currency) to match the
    existing schema; pipeline.py / validators.py converts to Decimal when
    arithmetic validation is needed.
    """

    document_type: Literal[
        "tax_invoice", "simplified_tax_invoice", "receipt", "credit_note", "other"
    ] = Field(
        default="tax_invoice",
        description="document type. tax_invoice = full Thai tax invoice "
        "(ใบกำกับภาษีเต็มรูป, can claim input VAT, legal invoice no required); "
        "simplified_tax_invoice = ใบกำกับภาษีอย่างย่อ/ABB (POS slip, no legal "
        "invoice no, cannot claim VAT); receipt/credit_note/other otherwise",
    )
    is_not_invoice: bool = Field(
        default=False,
        description="true when the text is clearly NOT an invoice (letter, "
        "contract, blank page, etc.)",
    )
    is_copy_or_duplicate: bool = Field(
        default=False,
        description="true when text contains สำเนา / COPY / DUPLICATE markers",
    )

    invoice_number: Optional[str] = Field(default=None)
    date: Optional[str] = Field(
        default=None,
        description="YYYY-MM-DD Gregorian (Buddhist year converted -543 by Gemini)",
    )
    date_raw: str = Field(default="", description="date text exactly as printed")

    seller_name: str = Field(default="")
    seller_tax: str = Field(default="", description="13-digit Thai tax ID or empty")
    seller_addr: str = Field(default="")

    buyer_name: str = Field(default="")
    buyer_tax: str = Field(default="", description="13-digit Thai tax ID or empty")
    buyer_addr: str = Field(default="")

    subtotal: str = Field(default="", description="number-as-string, no commas")
    vat: str = Field(default="", description="number-as-string, no commas")
    wht_rate: str = Field(default="", description='number only, e.g. "3" not "3%"')
    wht_amount: str = Field(default="", description="number-as-string, no commas")
    total_amount: Optional[str] = Field(default=None)
    payment_method: str = Field(
        default="", description="how paid as printed: cash|transfer|qr|card, empty if not shown"
    )

    items: List[LineItem] = Field(default_factory=list)

    notes: str = Field(default="", description="remark text")
    category: str = Field(default="", description="3-5 char summary in items' language")

    # P0 修 (2026-05-26) · 同页多票:图片型 PDF 一页可能印多张独立发票
    # (各自 invoice_number + 合计)。Layer 2 把第 1 张放顶层字段,其余每张作为
    # 完整对象放这里(嵌套层的 additional_invoices 必须为空 · 不递归)。
    # legacy_adapter 会把它们拆成多个 page 条目 → invoice_grouper 产出多张发票。
    additional_invoices: List["ThaiInvoice"] = Field(
        default_factory=list,
        description="extra invoices found on the SAME page beyond the primary "
        "(multi-invoice-per-page). Each is a full ThaiInvoice; their own "
        "additional_invoices must stay empty.",
    )

    # 2026-05-21 multi-schema refactor: per-field source provenance.
    # Optional — populated by Layer 2 / Layer 3 when the model returns
    # bbox / source_text info. Used by validators to enforce "amount only
    # from total/subtotal/vat columns".
    source_refs: Dict[str, FieldRef] = Field(
        default_factory=dict,
        description="map of field_name -> FieldRef (invoice_number / "
        "total_amount / subtotal / vat / seller_tax / buyer_tax / date)",
    )

    # ---- Defensive coercion: Gemini sometimes returns null for empty fields
    # or number for a number-as-string. Without these, valid Gemini output
    # fails strict pydantic validation and triggers the layer 2 retry budget
    # for no reason.
    _str_coerce = field_validator(
        "date_raw",
        "seller_name",
        "seller_tax",
        "seller_addr",
        "buyer_name",
        "buyer_tax",
        "buyer_addr",
        "subtotal",
        "vat",
        "wht_rate",
        "wht_amount",
        "notes",
        "category",
        "payment_method",
        mode="before",
    )(_coerce_to_str)

    _opt_str_coerce = field_validator(
        "invoice_number",
        "date",
        "total_amount",
        mode="before",
    )(_coerce_to_optional_str)

    @field_validator("is_not_invoice", "is_copy_or_duplicate", mode="before")
    @classmethod
    def _coerce_bool(cls, v):
        """Gemini sometimes returns null for booleans; treat null as False."""
        return False if v is None else v

    @field_validator("items", mode="before")
    @classmethod
    def _coerce_items(cls, v):
        """Gemini may return null for empty items list."""
        return [] if v is None else v

    @field_validator("document_type", mode="before")
    @classmethod
    def _coerce_document_type(cls, v):
        """Gemini may return null or an unexpected value; fall back to tax_invoice."""
        if v is None:
            return "tax_invoice"
        allowed = {"tax_invoice", "simplified_tax_invoice", "receipt", "credit_note", "other"}
        return v if v in allowed else "other"

    @field_validator("source_refs", mode="before")
    @classmethod
    def _coerce_source_refs(cls, v):
        # Gemini 有两种 null 玩法都得防(否则整份发票 422/400):
        #   1) 整个 source_refs = null            → {}
        #   2) 个别字段 = null,如 {"vat": null}  → 丢掉该键(不是合法 FieldRef dict)
        # 真实踩坑(2026-05-26 Codex 验收 qa_3):source_refs.vat=null →
        #   "Input should be a valid dictionary" → 整份 PDF 400。根因是只防了 case 1。
        if v is None:
            return {}
        if isinstance(v, dict):
            # 只保留可构造 FieldRef 的条目:dict(Gemini JSON)或已是 FieldRef 实例(代码内构造);
            # null / 标量 / list 一律丢弃。漏掉 FieldRef 实例会静默丢溯源 → validator 拦不住误源金额。
            return {k: val for k, val in v.items() if isinstance(val, (dict, FieldRef))}
        return v

    @field_validator("additional_invoices", mode="before")
    @classmethod
    def _coerce_additional(cls, v):
        return [] if v is None else v

    @model_validator(mode="after")
    def _normalize_year(self):
        """年份确定性重算(不信 LLM 算术):2 位年消歧 + 4 位佛历减 543(治 2569 被误算成 2023)。"""
        ty = date.today().year
        self.date = _fix_two_digit_year_date(self.date_raw, self.date, ty)
        self.date = _fix_buddhist_year_date(self.date_raw, self.date, ty)
        return self


# Self-referencing field (additional_invoices: List[ThaiInvoice]) needs rebuild.
ThaiInvoice.model_rebuild()
