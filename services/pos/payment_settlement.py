from __future__ import annotations

from decimal import Decimal

from core.pos_api import PosError

PAYMENT_METHODS = frozenset({"cash", "qr", "promptpay", "card", "transfer"})


def validate(payments: list, grand_total: Decimal) -> tuple[list, Decimal, Decimal]:
    if not grand_total.is_finite() or grand_total < 0:
        raise PosError("pos.payment_invalid", 422, detail="grand_total")
    if grand_total == 0:
        if payments:
            raise PosError("pos.payment_invalid", 422, detail="zero_total")
        return [], Decimal("0"), Decimal("0")

    normalized = []
    paid_total = Decimal("0")
    cash_total = Decimal("0")
    for payment in payments:
        if not isinstance(payment, dict):
            raise PosError("pos.payment_invalid", 422, detail="payment")
        method = payment.get("method", "cash")
        if method not in PAYMENT_METHODS:
            raise PosError("pos.payment_invalid", 422, detail="method")
        try:
            amount = Decimal(str(payment.get("amount")))
        except (ArithmeticError, TypeError, ValueError):
            raise PosError("pos.payment_invalid", 422, detail="amount") from None
        if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            raise PosError("pos.payment_invalid", 422, detail="amount")
        paid_total += amount
        if method == "cash":
            cash_total += amount
        normalized.append(
            {
                "method": "promptpay" if method == "qr" else method,
                "amount": amount,
                "ref": payment.get("ref"),
            }
        )

    if paid_total < grand_total:
        raise PosError("pos.payment_invalid", 422, detail="underpaid")
    change = paid_total - grand_total
    if change > cash_total:
        raise PosError("pos.payment_invalid", 422, detail="noncash_overpay")
    if paid_total - change != grand_total:
        raise PosError("pos.payment_invalid", 422, detail="settlement")
    return normalized, paid_total, change
