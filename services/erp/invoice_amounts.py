"""Validate reviewed OCR amounts without rewriting the receipt's values."""

from decimal import Decimal, InvalidOperation
from fastapi import HTTPException

CENT = Decimal("0.01")


def number(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result < 0:
            raise ValueError
        return result
    except (ValueError, InvalidOperation, TypeError):
        raise HTTPException(422, detail="erp.amount_mismatch") from None


def line_amount(item):
    value = item.get("subtotal")
    return (
        number(value)
        if value not in (None, "")
        else number(item.get("qty")) * number(item.get("price"))
    )


def resolve(fields):
    total = number(fields.get("total_amount"))
    vat = number(fields.get("vat") or 0)
    discount = number(fields.get("discount") or 0)
    net = total - vat
    if net < 0:
        raise HTTPException(422, detail="erp.amount_mismatch")
    subtotal = number(fields.get("subtotal", net))
    if (
        min(
            abs(subtotal - net),
            abs(subtotal - discount - net),
            abs(subtotal - total),
            abs(subtotal - discount - total),
        )
        > CENT
    ):
        raise HTTPException(422, detail="erp.amount_mismatch")
    gross = sum((line_amount(item) for item in fields["items"]), Decimal(0))
    inclusive = abs(gross - discount - total) <= CENT
    if not inclusive and abs(gross - discount - net) > CENT:
        raise HTTPException(422, detail="erp.amount_mismatch")
    return dict(
        total=total,
        vat=vat,
        discount=discount,
        net=net,
        gross=gross,
        inclusive=inclusive,
        rate=vat * 100 / net if net else Decimal(0),
    )


def purchase_lines(fields):
    """Allocate the reviewed net acquisition cost; receipt prices remain in OCR history."""
    amounts = resolve(fields)
    remaining = amounts["net"]
    lines = []
    for i, item in enumerate(fields["items"]):
        share = (
            (amounts["net"] * line_amount(item) / amounts["gross"]).quantize(CENT)
            if amounts["gross"]
            else Decimal(0)
        )
        share = remaining if i == len(fields["items"]) - 1 else min(remaining, share)
        remaining -= share
        qty = number(item["qty"])
        lines.append(
            dict(
                item_type="goods",
                product_id=item.get("product_id"),
                description=item["name"],
                qty=str(qty),
                unit=item.get("unit"),
                unit_price=str(share / qty),
                vat_rate=str(amounts["rate"]),
                vat_applicable=True,
            )
        )
    return lines, amounts
