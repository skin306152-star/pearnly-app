"""ERP-only OCR additions; Cowork retains its existing extraction instructions."""

from contextlib import contextmanager
from contextvars import ContextVar

_enabled = ContextVar("erp_ocr_fields", default=False)
INSTRUCTIONS = """
ERP receipt review:
Read the issue date's digits directly from the document, not today's year, expiry dates,
loyalty dates or previous guesses. Preserve the exact printed date in date_raw. Convert
Buddhist years to Gregorian once for date. If a digit is unreadable, leave date null.
Extract payment_received as the explicit NET amount actually paid (card/VISA/Mastercard,
transfer, QR or cash less printed change). This is NOT the invoice total or amount due.
A payment method alone is not evidence of payment: leave payment_received empty unless
an amount is explicitly printed next to the payment. Never infer payment from total_amount.
For cash, also keep cash_amount and change_amount as printed; do not count payment twice.
"""


@contextmanager
def context(enabled):
    token = _enabled.set(enabled)
    try:
        yield
    finally:
        _enabled.reset(token)


def extend(prompt):
    if not _enabled.get():
        return prompt
    # Include the field in the actual output example, not only prose below it.
    prompt = prompt.replace(
        '"cash_amount":',
        '"payment_received": "explicit net paid amount as printed, empty if absent",\n  "cash_amount":',
    )
    return prompt + INSTRUCTIONS


def enabled():
    return _enabled.get()


def printed_date(raw):
    from fastapi import HTTPException
    from services.erp.business_dates import standard

    try:
        return standard(raw)
    except HTTPException:
        return None
