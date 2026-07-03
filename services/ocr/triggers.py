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
    soft_flags: Optional[List[str]] = None,
) -> float:
    """Return a single 0..1 confidence for the page.

    - Start at L1 avg_confidence (1.0 for text/table paths).
    - Subtract penalty per trigger AND per soft_flag (low word-conf that didn't
      escalate to L3 still lowers confidence into yellow_confirm so the user
      eyeballs it — that's the whole point of moving Rule 4 here, doc 09 §3.1).
    - Floor at 0.0, cap at 1.0.
    """
    base = float(l1_page.avg_confidence or 0.0)
    if base <= 0.0:
        base = 0.85  # neutral starting point when L1 doesn't provide one
    penalty = 0.05 * (len(triggers) + len(soft_flags or []))
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
    """Returns a trigger reason string if the amounts don't reconcile within
    AMOUNT_TOLERANCE_THB, else None. If any of the 3 core fields can't be
    parsed as a number, returns None (don't fire false trigger on a missing
    field — missing fields are caught by the dedicated checks).

    泰国票折扣在小计后、VAT 前:总额 = 小计 − 折扣 + VAT。小计有「折前」「折后」两种
    印法,两种口径任一平即放行,别把 7-11 类折扣票误送 L3(f003 实案 2026-07-03)。"""
    try:
        sub = float(invoice.subtotal) if invoice.subtotal else None
        vat = float(invoice.vat) if invoice.vat else None
        total = float(invoice.total_amount) if invoice.total_amount else None
        disc = float(invoice.discount) if getattr(invoice, "discount", None) else 0.0
    except (ValueError, TypeError):
        return "amount field not numeric (parse failed)"
    if sub is None or vat is None or total is None:
        return None  # can't check; another rule may fire
    diff = min(abs(sub + vat - total), abs(sub - disc + vat - total))
    if diff > AMOUNT_TOLERANCE_THB:
        return (
            f"amount math fail: subtotal {sub:.2f} - discount {disc:.2f} "
            f"+ vat {vat:.2f} != total {total:.2f} "
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
    """Return list of L3-escalation reasons; empty list = layer 3 not needed.

    L3 is the slow visual re-read arm — only fire it when a visual pass can
    actually fix something. Low per-field word confidence on a value that DOES
    appear in the L1 text is NOT escalated here (thermal/small-print receipts
    read low-conf on nearly everything); that path goes to _evaluate_soft_flags
    → yellow_confirm instead (doc 09 §3.1, speed fix).

    Escalation rules:
    1. invoice_number missing — only for FULL tax invoices (a legal เลขที่ is
       mandatory only there). Simplified / receipt / non-invoice keep their
       R#/REF as-is and never escalate for a "missing" legal number (§3.2).
       total_amount missing escalates for any doc (an expense with no total is
       unusable).
    2. Amount math fail (subtotal + vat != total).
    3. seller_tax format invalid — only for FULL tax invoices (input-VAT claim
       needs a real 13-digit seller id; a card SLIP's TID is not a tax id).
    5. L1 containment — extracted value absent from L1 full_text (layer 2 likely
       hallucinated it → a visual re-read is warranted).
    6. Invoice pattern anomaly vs previously seen patterns for this seller_tax.
    7. Same-page multi-invoice candidate count > extracted.
    """
    if invoice.is_not_invoice:
        return []

    # Missing document_type → treat as full tax invoice (stricter default).
    is_full_tax_invoice = getattr(invoice, "document_type", "tax_invoice") == "tax_invoice"

    triggers: List[str] = []

    # Rule 1: critical fields missing. Legal invoice number is required only on
    # full tax invoices; simplified/receipt POS slips carry a non-legal R# only.
    if not invoice.invoice_number and is_full_tax_invoice:
        triggers.append("invoice_number missing")
    if not invoice.total_amount:
        triggers.append("total_amount missing")

    # Rule 2: amount math
    math_reason = _check_amount_math(invoice)
    if math_reason:
        triggers.append(math_reason)

    # Rule 3 (P1G-Perf · removed as an L3 trigger): a malformed/missing seller
    # tax-id alone no longer escalates to the slow L3 visual re-read. Zihao
    # 2026-06-18: an invalid 13-digit id is a tax-optional detail — the card
    # shows the amount + "โปรดตรวจสอบ" and the user fixes the id on the web,
    # which is far cheaper than a 10–45s visual pass that often can't read a
    # blurry footer id anyway. The id is still surfaced for review via the
    # soft-flag path (yellow_confirm) in _evaluate_soft_flags, not here.

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
    # 让 Flash 看图把漏的那张补回来)· 而不是直接丢给人工。
    # P1G-Perf(Zihao 2026-06-18):只在【主金额不可靠】时才升 L3 —— 主金额齐全且自洽
    # 的多行/多票票,主单据照常出卡,漏票交给 page_runner 末尾的 validation_warning
    # 标「请核对」(needs_manual_review),不再为一张可能漏的堆叠票让用户多等 10s 视觉复读。
    main_amount_reliable = bool(invoice.total_amount) and not math_reason
    if invoice.invoice_number and not main_amount_reliable:
        extracted_n = 1 + len(invoice.additional_invoices or [])
        candidate_n = _count_invoice_no_candidates(page.full_text, invoice.invoice_number)
        if candidate_n > extracted_n:
            triggers.append(
                f"possible_missed_invoice(L2): {candidate_n} invoice-number candidates "
                f"vs {extracted_n} extracted — escalate to visual re-read"
            )

    return triggers


def _evaluate_soft_flags(page: Page, invoice: ThaiInvoice) -> List[str]:
    """Low word-level confidence on a value that DOES appear in the L1 text.

    Not a hallucination (Rule 5 escalates those) and not worth a slow L3 visual
    re-read — just lower page confidence to yellow_confirm so the user eyeballs
    the field. Thermal / small-print receipts read low-conf on nearly every
    field; escalating that to L3 was the main speed killer (doc 09 §3.1).
    Returns reasons that feed the confidence penalty but never gate L3.
    """
    if invoice.is_not_invoice:
        return []

    flags: List[str] = []

    for field_name in CRITICAL_FIELDS:
        value = getattr(invoice, field_name, None)
        if not value:
            continue
        min_conf = find_field_min_word_conf(page, value)
        if min_conf is None or min_conf >= CONFIDENCE_THRESHOLD:
            continue
        # value not in L1 text → Rule 5 already escalates it; don't double-handle
        if check_field_in_l1_text(page, value):
            flags.append(
                f"{field_name}={value!r} low word conf {min_conf:.3f} "
                f"< {CONFIDENCE_THRESHOLD} (in L1 text → confirm, no L3)"
            )

    date_val = invoice.date_raw or invoice.date
    if date_val:
        min_conf = find_field_min_word_conf(page, date_val)
        if min_conf is not None and min_conf < CONFIDENCE_THRESHOLD:
            flags.append(
                f"date={date_val!r} low word conf {min_conf:.3f} "
                f"< {CONFIDENCE_THRESHOLD} (confirm, no L3)"
            )

    # Malformed seller tax-id on a full tax invoice (P1G-Perf · was Rule 3 L3
    # trigger): nudge the user to check it via yellow_confirm instead of a slow
    # visual re-read (the VAT breakdown still derives from the amount).
    is_full_tax_invoice = getattr(invoice, "document_type", "tax_invoice") == "tax_invoice"
    if is_full_tax_invoice and invoice.seller_tax:
        if not invoice.seller_tax.isdigit() or len(invoice.seller_tax) != 13:
            flags.append(
                f"seller_tax format invalid: {invoice.seller_tax!r} "
                "(expected 13 digits → confirm, no L3)"
            )

    return flags
