"""Carry explicit manual payment amounts into the existing document ledgers."""

from decimal import Decimal, InvalidOperation

from fastapi import HTTPException


def payment(fields, direction):
    def amount(key):
        try:
            value = Decimal(str(fields.get(key) or 0))
        except InvalidOperation:
            raise HTTPException(422, detail="erp.invalid_amount") from None
        if not value.is_finite() or value < 0:
            raise HTTPException(422, detail="erp.invalid_amount")
        return value

    paid = (
        amount("payment_received")
        if direction == "sales"
        else (
            amount("cash_amount")
            + amount("cheque_payment")
            + amount("bank_interest")
            - amount("received_discount")
            - amount("withholding_outstanding")
        )
    )
    total = amount("total_amount")
    if paid < 0 or paid > total:
        raise HTTPException(422, detail="erp.invalid_amount")
    return {
        "paid_amount": paid.quantize(Decimal("0.01")),
        "status": "paid" if paid > 0 and paid == total else "partial" if paid else "unpaid",
        "date": fields.get("date") if paid else None,
        "method": "cash" if fields.get("cash_payment") else fields.get("payment_method"),
    }
