# -*- coding: utf-8 -*-
"""
services/ocr/triggers.py · REFACTOR-WA-OCRSPLIT P-B(纯搬家 · 0 逻辑改)

从 pipeline.py 抽出 L3 触发 / 置信度纯决策逻辑(不调 L1/L2/L3·只看已抽字段+L1词级置信):
  阈值常量(CONFIDENCE_THRESHOLD/AMOUNT_TOLERANCE_THB/CRITICAL_FIELDS/CONFIDENCE_AUTO/REVIEW)+
  _aggregate_page_confidence / _bucket_confidence / _check_amount_math /
  _count_invoice_no_candidates / _evaluate_triggers。
pipeline 文件头 re-export 回原命名空间 → 调用方 0 改动 · 对象身份不变。触发口径一字未改。
"""

from __future__ import annotations

import os
import re
from typing import List, Optional

from .confidence import check_field_in_l1_text, find_field_min_word_conf
from .pattern_memory import InvoicePatternMemory
from .schemas import BusinessDocumentType, Page, ThaiInvoice

CONFIDENCE_THRESHOLD = float(os.environ.get("OCR_PIPELINE_CONF_THRESHOLD", "0.85"))


AMOUNT_TOLERANCE_THB = float(os.environ.get("OCR_PIPELINE_AMOUNT_TOL", "0.5"))


CRITICAL_FIELDS = ("invoice_number", "total_amount", "seller_tax")


CONFIDENCE_AUTO_THRESHOLD = float(os.environ.get("OCR_CONF_AUTO", "0.98"))


CONFIDENCE_REVIEW_THRESHOLD = float(os.environ.get("OCR_CONF_REVIEW", "0.90"))


def _aggregate_page_confidence(
    l1_page: Page,
    invoice: ThaiInvoice,
    document,
    triggers: List[str],
    needs_manual_review: bool,
    document_type: BusinessDocumentType,
) -> float:
    """Return a single 0..1 confidence for the page.

    - Start at L1 avg_confidence (1.0 for text/table paths).
    - Subtract penalty per trigger/validation warning.
    - Floor at 0.0, cap at 1.0.
    """
    base = float(l1_page.avg_confidence or 0.0)
    if base <= 0.0:
        base = 0.85  # neutral starting point when L1 doesn't provide one
    penalty = 0.05 * len(triggers)
    if needs_manual_review:
        penalty += 0.10
    final = max(0.0, min(1.0, base - penalty))
    return final


def _bucket_confidence(conf: float, needs_review: bool) -> str:
    if needs_review:
        return "needs_review"
    if conf >= CONFIDENCE_AUTO_THRESHOLD:
        return "auto"
    if conf >= CONFIDENCE_REVIEW_THRESHOLD:
        return "yellow_confirm"
    return "needs_review"


def _check_amount_math(invoice: ThaiInvoice) -> Optional[str]:
    """Returns a trigger reason string if subtotal + vat != total within
    AMOUNT_TOLERANCE_THB, else None. If any of the 3 fields can't be parsed
    as a number, returns None (don't fire false trigger on a missing field —
    missing fields are caught by the dedicated checks)."""
    try:
        sub = float(invoice.subtotal) if invoice.subtotal else None
        vat = float(invoice.vat) if invoice.vat else None
        total = float(invoice.total_amount) if invoice.total_amount else None
    except (ValueError, TypeError):
        return "amount field not numeric (parse failed)"
    if sub is None or vat is None or total is None:
        return None  # can't check; another rule may fire
    expected = sub + vat
    diff = abs(expected - total)
    if diff > AMOUNT_TOLERANCE_THB:
        return (
            f"amount math fail: subtotal {sub:.2f} + vat {vat:.2f} "
            f"= {expected:.2f} != total {total:.2f} "
            f"(diff {diff:.2f} > {AMOUNT_TOLERANCE_THB})"
        )
    return None


def _count_invoice_no_candidates(full_text: str, sample_invoice_no: str) -> int:
    """P0 修 (2026-05-26) · 数 OCR 文本里跟 sample 发票号"同族"的不同候选号个数。

    从已成功提取的 invoice_number 推导出结构正则(字母段照搬 · 数字段→\\d+),
    再在整页 OCR 文本里 findall · 去重计数。用于"同页多票防静默漏":候选数 >
    实际提取数 → 大概率漏了一张堆叠发票。

    例:sample='IV69/00179' → 正则 'IV\\d+/\\d+' · 页文本含 IV69/00179 + IV69/00189
        → 返回 2。
    保守:推不出正则 / 正则错 → 返回 0(不误报)。
    """
    if not full_text or not sample_invoice_no:
        return 0
    parts = re.split(r"(\d+)", str(sample_invoice_no).strip())
    segs: List[str] = []
    for seg in parts:
        if not seg:
            continue
        segs.append(r"\d+" if seg.isdigit() else re.escape(seg))
    if not segs or r"\d+" not in segs:
        # 没有数字段的发票号(纯字母)→ 正则会过度匹配 · 不数
        return 0
    pattern = "".join(segs)
    try:
        found = re.findall(pattern, full_text)
    except re.error:
        return 0
    return len({f.strip() for f in found if f.strip()})


def _evaluate_triggers(
    page: Page,
    invoice: ThaiInvoice,
    pattern_memory: Optional[InvoicePatternMemory] = None,
) -> List[str]:
    """Return list of trigger reason strings; empty list = layer 3 not needed.

    Exception: if invoice.is_not_invoice == True, return [] (no point sending
    a non-invoice through layer 3 visual review).

    Trigger rules (B1 fix replaces page-avg confidence with word-level
    per-critical-field confidence + L1-text containment check + pattern
    familiarity check):

    1. Critical fields missing (invoice_number, total_amount)
    2. Amount math fail (subtotal + vat != total)
    3. seller_tax format invalid (non-empty but not 13 digits)
    4. (NEW) Per-critical-field word-level confidence < threshold —
       finds matching L1 words and checks their min confidence. Catches
       things like Vision misreading `/` as `1` where the page average
       still looks high.
    5. (NEW) L1 text containment — extracted value does not appear in L1
       full_text (suggests layer 2 hallucinated the value).
    6. (NEW) Invoice pattern anomaly — extracted invoice_number prefix
       differs from previously seen patterns for this seller_tax.
    """
    if invoice.is_not_invoice:
        return []

    triggers: List[str] = []

    # Rule 1: critical fields missing
    if not invoice.invoice_number:
        triggers.append("invoice_number missing")
    if not invoice.total_amount:
        triggers.append("total_amount missing")

    # Rule 2: amount math
    math_reason = _check_amount_math(invoice)
    if math_reason:
        triggers.append(math_reason)

    # Rule 3: tax_id format
    if invoice.seller_tax:
        if not invoice.seller_tax.isdigit() or len(invoice.seller_tax) != 13:
            triggers.append(
                f"seller_tax format invalid: {invoice.seller_tax!r} " "(expected 13 digits)"
            )

    # Rule 4 (NEW): per-critical-field word-level confidence
    # For each non-empty critical field, find matching L1 words and check
    # their min confidence.
    for field_name in CRITICAL_FIELDS:
        value = getattr(invoice, field_name, None)
        if not value:
            continue  # missing was already caught by rule 1
        min_conf = find_field_min_word_conf(page, value)
        if min_conf is None:
            # No L1 word matched — handled by rule 5 below
            continue
        if min_conf < CONFIDENCE_THRESHOLD:
            triggers.append(
                f"{field_name}={value!r} word min conf {min_conf:.3f} "
                f"< threshold {CONFIDENCE_THRESHOLD}"
            )

    # Rule 4b: date — same check using date_raw (as printed) if available,
    # else the normalized date string
    date_val = invoice.date_raw or invoice.date
    if date_val:
        min_conf = find_field_min_word_conf(page, date_val)
        if min_conf is not None and min_conf < CONFIDENCE_THRESHOLD:
            triggers.append(
                f"date={date_val!r} word min conf {min_conf:.3f} "
                f"< threshold {CONFIDENCE_THRESHOLD}"
            )

    # Rule 5 (NEW): L1 containment — non-empty extracted critical fields
    # must appear in L1's full_text (after whitespace+comma normalization).
    # If absent, layer 2 likely hallucinated.
    for field_name in CRITICAL_FIELDS:
        value = getattr(invoice, field_name, None)
        if not value:
            continue
        if not check_field_in_l1_text(page, value):
            triggers.append(
                f"{field_name}={value!r} not found in L1 OCR text "
                "(possibly hallucinated by layer 2)"
            )

    # Rule 6 (NEW): template / pattern familiarity. Skipped silently if no
    # memory passed in or no baseline yet.
    if pattern_memory is not None and invoice.invoice_number:
        anomaly = pattern_memory.check_anomaly(invoice.seller_tax, invoice.invoice_number)
        if anomaly:
            triggers.append(anomaly)

    # Rule 7 (P0 2026-05-26 · 同页多票):OCR 文本里的发票号候选数 > 已提取数 →
    # 大概率漏了一张堆叠发票。把它当作 L3 视觉复读的触发条件(先加强自身 OCR ·
    # 让 Flash 看图把漏的那张补回来)· 而不是直接丢给人工。真正的人工兜底只在
    # L3 复读后仍然短缺时才在 pipeline 末尾触发。
    if invoice.invoice_number:
        extracted_n = 1 + len(invoice.additional_invoices or [])
        candidate_n = _count_invoice_no_candidates(page.full_text, invoice.invoice_number)
        if candidate_n > extracted_n:
            triggers.append(
                f"possible_missed_invoice(L2): {candidate_n} invoice-number candidates "
                f"vs {extracted_n} extracted — escalate to visual re-read"
            )

    return triggers
