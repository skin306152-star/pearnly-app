"""Normalize payment-method text extracted from purchase documents."""

from __future__ import annotations

_PAYMENT_PATTERNS = (
    (
        "promptpay",
        ("พร้อมเพย์", "promptpay", "prompt pay", "qrpayment", "qr payment", "qr code", "qr"),
    ),
    ("transfer", ("โอนเงิน", "โอน", "transfer", "汇款", "转账")),
    ("card", ("บัตรเครดิต", "บัตร", "credit", "debit", "card", "刷卡", "信用卡")),
    ("cash", ("เงินสด", "cash", "现金", "付现")),
)


def payment_from_ocr(raw) -> str:
    """Return a canonical code when known, otherwise preserve the OCR text."""
    value = str(raw or "").strip()
    lowered = value.lower()
    for code, words in _PAYMENT_PATTERNS:
        if any(word.lower() in lowered for word in words):
            return code
    return value
