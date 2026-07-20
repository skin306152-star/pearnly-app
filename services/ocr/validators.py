# -*- coding: utf-8 -*-
"""
services/ocr/validators.py · 2026-05-21 multi-schema refactor

Doc-type-aware semantic validators. THIS is the file that prevents
'6091' (a description row in a GL) from being parsed as an amount.

The validators run AFTER Layer 2 / Layer 3 produce structured output.
They check that:
    1. Amount fields source from the correct column (not description /
       voucher_no / account_code).
    2. Numeric fields actually appear in the L1 OCR text (containment).
    3. GL direction is consistent with debit/credit split.
    4. Bank statement amounts come from deposit/withdrawal/balance.
    5. Invoice amounts come from total/subtotal/vat areas.

Each validator returns a list of warning strings. Empty list = clean.
The pipeline records the warnings on PipelinePageResult.validation_warnings
and uses them to drive confidence routing / needs_review.
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import List, Optional, Set

from .schemas import (
    BankStatementDocument,
    BankStatementEntry,
    GeneralLedgerDocument,
    GLEntry,
    Page,
    ThaiInvoice,
)

logger = logging.getLogger(__name__)


# ============================================================
# Forbidden source-column patterns for amount fields
# ============================================================
# These header keywords (lowercased, no whitespace) MUST NOT be the source
# column for an amount/debit/credit/balance field. Multi-language to cover
# real-world Thai / English / Chinese GL templates.
_DESCRIPTION_COLUMN_KEYWORDS: Set[str] = {
    "description",
    "remark",
    "remarks",
    "note",
    "notes",
    "detail",
    "details",
    "particulars",
    "narrative",
    "รายการ",
    "คําอธิบาย",
    "คำอธิบาย",
    "หมายเหตุ",
    "摘要",
    "说明",
    "备注",
    "tekijä",
    "memo",
}
_VOUCHER_COLUMN_KEYWORDS: Set[str] = {
    "voucher",
    "voucher no",
    "voucher no.",
    "voucherno",
    "vch",
    "vch no",
    "doc no",
    "doc no.",
    "document no",
    "journal no",
    "jv",
    "jv no",
    "reference",
    "ref",
    "ref no",
    "ref no.",
    "เลขที่เอกสาร",
    "เลขที่ใบสำคัญ",
    "เลขที่อ้างอิง",
    "เลขที่",
    "凭证号",
    "凭证编号",
}
_ACCOUNT_CODE_COLUMN_KEYWORDS: Set[str] = {
    "account code",
    "acc code",
    "a/c code",
    "account no",
    "a/c no",
    "รหัสบัญชี",
    "เลขที่บัญชี",
    "科目代码",
    "科目编号",
}

# Allowed source columns for GL amount/debit/credit
_GL_DEBIT_COLUMNS: Set[str] = {"debit", "dr", "เดบิต", "借方", "借"}
_GL_CREDIT_COLUMNS: Set[str] = {"credit", "cr", "เครดิต", "贷方", "贷"}
_GL_BALANCE_COLUMNS: Set[str] = {
    "balance",
    "running balance",
    "ending balance",
    "ยอดคงเหลือ",
    "คงเหลือ",
    "余额",
}

# Allowed source columns for Bank Statement amount/deposit/withdrawal
_BANK_DEPOSIT_COLUMNS: Set[str] = {
    "deposit",
    "credit",
    "in",
    "money in",
    "amount in",
    "received",
    "เงินเข้า",
    "ฝาก",
    "รับ",
    "存入",
    "存款",
    "收入",
}
_BANK_WITHDRAWAL_COLUMNS: Set[str] = {
    "withdrawal",
    "debit",
    "out",
    "money out",
    "amount out",
    "paid",
    "เงินออก",
    "ถอน",
    "จ่าย",
    "支出",
    "取款",
    "提款",
}
_BANK_BALANCE_COLUMNS: Set[str] = _GL_BALANCE_COLUMNS

# Regex for tokens that look like amounts (numbers possibly with commas/decimals)
_AMOUNT_TOKEN_RE = re.compile(r"^-?\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^-?\d+(?:\.\d+)?$")


def _norm_col(col: str) -> str:
    """Lowercase, strip, drop trailing punctuation — for column header match."""
    if not col:
        return ""
    s = col.strip().lower()
    s = s.rstrip(":.•·").strip()
    return s


def _is_forbidden_amount_source(source_column: str) -> Optional[str]:
    """Return the rejection reason if source_column is a description /
    voucher / account-code column. None = OK."""
    c = _norm_col(source_column)
    if not c:
        return None
    if c in _DESCRIPTION_COLUMN_KEYWORDS:
        return f"sourced from description column ({source_column!r})"
    if c in _VOUCHER_COLUMN_KEYWORDS:
        return f"sourced from voucher-number column ({source_column!r})"
    if c in _ACCOUNT_CODE_COLUMN_KEYWORDS:
        return f"sourced from account-code column ({source_column!r})"
    return None


def _is_allowed_gl_amount_source(source_column: str, kind: str) -> bool:
    """Returns True if source_column is the right column for the named kind
    ('debit' / 'credit' / 'balance'). When source_column is empty, we can't
    verify — return True (don't flag false positives)."""
    c = _norm_col(source_column)
    if not c:
        return True
    if kind == "debit":
        return c in _GL_DEBIT_COLUMNS
    if kind == "credit":
        return c in _GL_CREDIT_COLUMNS
    if kind == "balance":
        return c in _GL_BALANCE_COLUMNS
    return True


def _is_allowed_bank_amount_source(source_column: str, kind: str) -> bool:
    c = _norm_col(source_column)
    if not c:
        return True
    if kind == "deposit":
        return c in _BANK_DEPOSIT_COLUMNS
    if kind == "withdrawal":
        return c in _BANK_WITHDRAWAL_COLUMNS
    if kind == "balance":
        return c in _BANK_BALANCE_COLUMNS
    return True


def _value_appears_in_description(value: str, description: str) -> bool:
    """True if the value token literally appears in the description text.
    Used to detect '6091 is also somewhere in description' — the only safe
    signal that the LLM grabbed it from the wrong column.

    Matches the value as a standalone token (no surrounding digits). Also
    tries the value with trailing '.0' / '.00' stripped so '6091.00' in
    debit catches 'Description: 6091'."""
    if not value or not description:
        return False
    v = value.replace(",", "").strip()
    if not v:
        return False
    if re.search(r"(?<!\d)" + re.escape(v) + r"(?!\d)", description):
        return True
    # Strip trailing .0 / .00 zeros and try integer form
    if "." in v:
        v_int = v.rstrip("0").rstrip(".")
        if (
            v_int
            and v_int != v
            and re.search(r"(?<!\d)" + re.escape(v_int) + r"(?!\d)", description)
        ):
            return True
    return False


# ============================================================
# General Ledger validator (the 6091 case)
# ============================================================
def validate_gl_document(doc: GeneralLedgerDocument, page: Page) -> List[str]:
    """Run all GL rules on every entry. Returns warning list (empty = clean).

    Critical rules:
    R1. For each entry: debit_ref/credit_ref/balance_ref.source_column MUST be
        one of the allowed GL columns (debit/เดบิต OR credit/เครดิต OR balance).
    R2. The numeric value of debit/credit/amount MUST NOT also appear as a
        bare token in the description field (signals possible mis-pickup).
    R3. amount must equal debit (if debit>0) OR credit (if credit>0). Both
        non-zero is invalid.
    R4. direction must match debit/credit split.
    R5. The numeric token (e.g. '6091') from description MUST NOT appear in
        amount/debit/credit/balance.
    """
    warnings: List[str] = []
    for idx, entry in enumerate(doc.entries):
        row_id = entry.voucher_no or f"row#{idx + 1}"

        # R1: source-column check (when refs are present)
        for ref_name, ref, expected_kind in (
            ("debit_ref", entry.debit_ref, "debit"),
            ("credit_ref", entry.credit_ref, "credit"),
            ("balance_ref", entry.balance_ref, "balance"),
        ):
            if ref is None:
                continue
            # Reject when sourced from description/voucher/account
            reason = _is_forbidden_amount_source(ref.source_column)
            if reason:
                warnings.append(f"GL {row_id}: {ref_name}={ref.value!r} {reason} — rejected")
                _clear_amount_field(entry, ref_name)
                continue
            # Verify it's the right amount column
            if not _is_allowed_gl_amount_source(ref.source_column, expected_kind):
                warnings.append(
                    f"GL {row_id}: {ref_name} source column "
                    f"{ref.source_column!r} is not a {expected_kind} column"
                )

        # R2 + R5: 6091-style description-leak check
        for amount_field in ("debit", "credit", "amount", "balance"):
            value = getattr(entry, amount_field, "") or ""
            if not value:
                continue
            if _value_appears_in_description(value, entry.description):
                # Only warn if the value also appears as a STANDALONE token in
                # description (not part of e.g. "Invoice 6091/2024"). The
                # _value_appears_in_description function already does that.
                # Additional sanity: skip if it appears in voucher_no /
                # account_code too (those are legitimately numeric).
                if _value_appears_in_description(
                    value, entry.voucher_no
                ) or _value_appears_in_description(value, entry.account_code):
                    pass  # ambiguous — skip
                else:
                    warnings.append(
                        f"GL {row_id}: {amount_field}={value!r} also appears "
                        f"in description={entry.description!r} — possibly "
                        f"mis-sourced from description column"
                    )

        # R3: debit & credit mutually exclusive
        try:
            d = float(entry.debit) if entry.debit else 0.0
            c = float(entry.credit) if entry.credit else 0.0
        except ValueError:
            d = c = 0.0
            warnings.append(
                f"GL {row_id}: debit/credit not numeric "
                f"(debit={entry.debit!r}, credit={entry.credit!r})"
            )
        else:
            if d > 0 and c > 0:
                warnings.append(
                    f"GL {row_id}: both debit ({d}) AND credit ({c}) non-zero "
                    f"— GL rows must have exactly one"
                )

        # R4: direction consistency
        if entry.direction == "deposit" and d <= 0:
            warnings.append(
                f"GL {row_id}: direction=deposit but debit={d} (deposit requires debit>0)"
            )
        elif entry.direction == "withdrawal" and c <= 0:
            warnings.append(
                f"GL {row_id}: direction=withdrawal but credit={c} (withdrawal requires credit>0)"
            )

        # R5b: amount derivation check
        if entry.amount:
            try:
                a = float(entry.amount)
                expected = d if d > 0 else c
                if abs(a - expected) > 0.01 and (d > 0 or c > 0):
                    warnings.append(
                        f"GL {row_id}: amount={a} doesn't match " f"debit-or-credit={expected}"
                    )
            except ValueError:
                warnings.append(f"GL {row_id}: amount={entry.amount!r} not numeric")

    return warnings


def _clear_amount_field(entry: GLEntry, ref_name: str) -> None:
    """When validators reject a ref, clear the underlying amount string so
    downstream consumers don't accidentally use the wrong value."""
    if ref_name == "debit_ref":
        entry.debit = ""
        entry.debit_ref = None
        if entry.direction == "deposit":
            entry.direction = ""
            entry.amount = ""
    elif ref_name == "credit_ref":
        entry.credit = ""
        entry.credit_ref = None
        if entry.direction == "withdrawal":
            entry.direction = ""
            entry.amount = ""
    elif ref_name == "balance_ref":
        entry.balance = ""
        entry.balance_ref = None


# ============================================================
# Bank Statement validator
# ============================================================
def validate_bank_document(doc: BankStatementDocument, page: Page) -> List[str]:
    """Same idea as GL but for bank statements: deposit/withdrawal/balance
    amounts must come from the correct columns. Reference/description
    numbers MUST NOT be assigned to amounts."""
    warnings: List[str] = []
    for idx, entry in enumerate(doc.entries):
        row_id = entry.reference or f"tx#{idx + 1}"

        for ref_name, ref, expected_kind in (
            ("deposit_ref", entry.deposit_ref, "deposit"),
            ("withdrawal_ref", entry.withdrawal_ref, "withdrawal"),
            ("balance_ref", entry.balance_ref, "balance"),
        ):
            if ref is None:
                continue
            reason = _is_forbidden_amount_source(ref.source_column)
            if reason:
                warnings.append(f"Bank {row_id}: {ref_name}={ref.value!r} {reason} — rejected")
                _clear_bank_amount_field(entry, ref_name)
                continue
            if not _is_allowed_bank_amount_source(ref.source_column, expected_kind):
                warnings.append(
                    f"Bank {row_id}: {ref_name} source column "
                    f"{ref.source_column!r} is not a {expected_kind} column"
                )

        # 6091-style description leak check
        for amount_field in ("deposit", "withdrawal", "balance"):
            value = getattr(entry, amount_field, "") or ""
            if not value:
                continue
            if _value_appears_in_description(value, entry.description):
                if not _value_appears_in_description(value, entry.reference):
                    warnings.append(
                        f"Bank {row_id}: {amount_field}={value!r} also appears "
                        f"in description={entry.description!r} — possibly mis-sourced"
                    )

        # Deposit & withdrawal mutually exclusive
        try:
            d = float(entry.deposit) if entry.deposit else 0.0
            w = float(entry.withdrawal) if entry.withdrawal else 0.0
        except ValueError:
            d = w = 0.0
        else:
            if d > 0 and w > 0:
                warnings.append(f"Bank {row_id}: both deposit ({d}) AND withdrawal ({w}) non-zero")

    return warnings


def _clear_bank_amount_field(entry: BankStatementEntry, ref_name: str) -> None:
    if ref_name == "deposit_ref":
        entry.deposit = ""
        entry.deposit_ref = None
        if entry.direction == "deposit":
            entry.direction = ""
            entry.amount = ""
    elif ref_name == "withdrawal_ref":
        entry.withdrawal = ""
        entry.withdrawal_ref = None
        if entry.direction == "withdrawal":
            entry.direction = ""
            entry.amount = ""
    elif ref_name == "balance_ref":
        entry.balance = ""
        entry.balance_ref = None


# ============================================================
# Invoice validator (lighter — existing trigger logic in pipeline.py covers most)
# ============================================================
# 票面日期的合理区间。泰国税法凭证保存期 5 年 —— 比这更旧的进项/销项票不该还在
# 走识别入库,多半是年份读错一位(2026-07-20:佛历 2569 被读成 2559,归一出 2016,
# 全链零告警一路推进 Express,连税期都落到 2559-05)。未来票同理不合法。
_MAX_BACKDATE_YEARS = 5
_MAX_FUTURE_DAYS = 1
_ISO_DATE_RE = re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*$")


def validate_invoice_date(inv: ThaiInvoice, today: Optional[date] = None) -> List[str]:
    """票面日期离今天太远 → 标注复核。软闸:回落 Vision 路救不了日期(那条路读
    日期更差),所以只标注不阻断,由人来判是补录旧账还是读错了年份。

    两条识别链共用(Vision 路经 validate_invoice · 直读经 _invoice_soft_flags),
    单一实现防手抄漂移。
    """
    m = _ISO_DATE_RE.match(str(getattr(inv, "date", "") or ""))
    if not m:
        return []  # 缺日期/非 ISO 由别的闸管,这里不重复报
    try:
        parsed = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return []
    anchor = today or date.today()
    if parsed > anchor + timedelta(days=_MAX_FUTURE_DAYS):
        return [f"invoice date {parsed.isoformat()} is in the future — check the year"]
    if parsed < anchor - timedelta(days=365 * _MAX_BACKDATE_YEARS):
        return [
            f"invoice date {parsed.isoformat()} is over {_MAX_BACKDATE_YEARS} years old "
            "— check the year (Buddhist-era digit misread reads 10 years early)"
        ]
    return []


def validate_invoice(inv: ThaiInvoice, page: Page) -> List[str]:
    """Field-source check for invoices: any source_refs present must NOT
    have description as their source_column for amount fields."""
    warnings: List[str] = validate_invoice_date(inv)
    if not inv.source_refs:
        return warnings
    for fname, ref in inv.source_refs.items():
        if fname not in ("total_amount", "subtotal", "vat", "wht_amount"):
            continue
        reason = _is_forbidden_amount_source(ref.source_column)
        if reason:
            warnings.append(f"Invoice {fname}={ref.value!r} {reason} — likely mis-sourced")
    return warnings
