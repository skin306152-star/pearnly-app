# -*- coding: utf-8 -*-
"""
services/ocr/pattern_memory.py · REFACTOR-WA-OCRSPLIT P-C(纯搬家 · 0 逻辑改)

从 pipeline.py 抽出发票号 pattern 记忆(InvoicePatternMemory)+ 其阈值常量。
跨页 pattern 学习态的自洽 class · pipeline 文件头 re-export 回原命名空间(调用方 0 改动·身份不变)。
"""

from __future__ import annotations

import os
import re
import threading
from typing import Dict, Optional, Set

MIN_INSTANCES_BEFORE_FLAGGING = int(os.environ.get("OCR_PIPELINE_PATTERN_MIN_INSTANCES", "2"))


class InvoicePatternMemory:
    """Tracks invoice_number prefix patterns per seller_tax to catch anomalies.

    Pattern extraction: leading letters + up to 4 leading digits before any
    non-alphanumeric separator. Examples:
        IV69/00271  -> 'IV69'   (letters + 2 digits, stops at `/`)
        IV69100179  -> 'IV6910' (no separator; 4 digits captured)
        IV60/00304  -> 'IV60'   (different from IV69!)
        INV2026030204 -> 'INV2026'
        INV2026030002 -> 'INV2026'

    Anomaly logic: only flag if the seller_tax has been seen with >=
    MIN_INSTANCES_BEFORE_FLAGGING different invoices already (baseline
    built). Brand-new sellers don't get flagged.

    Current scope: in-memory only, per-Pipeline-process. For production
    integration with app.py, this can be initialized from
    db.get_seller_recent_invoices(seller_tax) or similar.
    """

    _PREFIX_RE = re.compile(r"^([A-Za-z]+)(\d{0,4})")

    def __init__(self):
        self._patterns: Dict[str, Set[str]] = {}
        self._instance_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    @classmethod
    def _extract_pattern(cls, invoice_number: str) -> Optional[str]:
        """Returns canonical pattern or None if no clean prefix."""
        if not invoice_number:
            return None
        m = cls._PREFIX_RE.match(invoice_number)
        if not m or not m.group(1):
            return None
        return (m.group(1) + m.group(2)).upper()

    def record(self, seller_tax: Optional[str], invoice_number: Optional[str]) -> None:
        """Record that this seller_tax issued an invoice with this pattern.

        Called after every page is processed. We deliberately record AFTER
        the (possibly-L3-corrected) final invoice, so the memory learns
        the corrected values.
        """
        if not seller_tax or not invoice_number:
            return
        pattern = self._extract_pattern(invoice_number)
        if not pattern:
            return
        with self._lock:
            self._patterns.setdefault(seller_tax, set()).add(pattern)
            self._instance_counts[seller_tax] = self._instance_counts.get(seller_tax, 0) + 1

    def check_anomaly(
        self,
        seller_tax: Optional[str],
        invoice_number: Optional[str],
    ) -> Optional[str]:
        """Return a trigger-reason string if pattern doesn't match any
        previously seen pattern for this seller_tax. None = OK or no baseline.

        Skips check if (a) inputs empty, (b) less than
        MIN_INSTANCES_BEFORE_FLAGGING invoices seen for this seller_tax.
        """
        if not seller_tax or not invoice_number:
            return None
        new_pattern = self._extract_pattern(invoice_number)
        if not new_pattern:
            return None
        with self._lock:
            known = self._patterns.get(seller_tax)
            instance_count = self._instance_counts.get(seller_tax, 0)
            if not known or instance_count < MIN_INSTANCES_BEFORE_FLAGGING:
                return None
            if new_pattern in known:
                return None
            return (
                f"invoice_number {invoice_number!r} pattern={new_pattern!r} "
                f"differs from known patterns {sorted(known)} for seller_tax "
                f"{seller_tax} ({instance_count} prior invoices)"
            )
