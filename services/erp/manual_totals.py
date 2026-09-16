"""Amounts for the manual entry fields; no payment or external ERP operations."""

from decimal import Decimal
from fastapi import HTTPException


def apply(fields, items, decimal):
    gross = sum((Decimal(item["subtotal"]) for item in items), Decimal("0"))
    discount = decimal(fields.get("discount") or "0")
    deposit = decimal(fields.get("deposit_deduction") or "0")
    deduction = discount + deposit
    if deduction > gross:
        raise HTTPException(422, detail="erp.invalid_amount")
    rate = decimal(fields.get("vat_rate") or "0")
    if rate > 100:
        raise HTTPException(422, detail="erp.invalid_amount")
    remaining = deduction
    for index, item in enumerate(items):
        share = (
            (deduction * Decimal(item["subtotal"]) / gross).quantize(Decimal("0.01"))
            if gross
            else Decimal("0")
        )
        share = remaining if index == len(items) - 1 else min(remaining, share)
        item["manual_discount"] = str(share)
        remaining -= share
    base = gross - deduction
    vat = (base * rate / 100).quantize(Decimal("0.01"))
    fields.update(
        gross_amount=str(gross),
        discount=str(discount),
        deposit_deduction=str(deposit),
        subtotal=str(base),
        vat=str(vat),
        total_amount=str(base + vat),
    )
    return base, vat
