"""Adapter for the existing POS form; use its existing authoritative calculator."""

from fastapi import HTTPException

from services.purchase.totals import compute_purchase_totals, override_totals


def calculate(fields, decimal):
    form = fields.get("pos_form") or {}
    lines = []
    for item in fields.get("items") or []:
        rate = decimal(item.get("vat_rate") or 0)
        wht = decimal(item.get("wht_rate") or 0)
        if rate > 100 or wht > 100:
            raise HTTPException(422, detail="erp.invalid_amount")
        price = decimal(item.get("price") or 0)
        discount = decimal(item.get("discount") or 0)
        if fields.get("price_mode") == "inclusive":
            divisor = 1 + rate / 100
            price, discount = price / divisor, discount / divisor
        lines.append(
            dict(
                item_type="service" if item.get("posting_kind") == "service" else "goods",
                product_id=item.get("product_id"),
                description=item["name"],
                qty=decimal(item["qty"], positive=True),
                unit=item.get("unit"),
                unit_price=price,
                discount=discount,
                vat_rate=rate,
                wht_rate=wht,
                category_id=item.get("category_id"),
                subcategory_id=item.get("subcategory_id"),
            )
        )
    calc = compute_purchase_totals(lines)
    override = None
    if form.get("manualOn"):
        values = form.get("override") or {}
        override = dict(
            override_on=True,
            subtotal=decimal(values.get("subtotal")),
            discount_total=decimal(values.get("discount")),
            vat_amount=decimal(values.get("vat")),
            grand_total=decimal(values.get("grand")),
        )
        calc, valid = override_totals(lines, override=override)
        if not valid:
            raise HTTPException(422, detail="erp.invalid_amount")
    if calc["net_payable"] < 0:
        raise HTTPException(422, detail="erp.invalid_amount")
    return calc, lines, override


def normalize(fields, decimal):
    calc, _, _ = calculate(fields, decimal)
    fields.update(
        subtotal=str(calc["subtotal"]),
        discount=str(calc["discount_total"]),
        vat=str(calc["vat_amount"]),
        wht_amount=str(calc["wht_amount"]),
        total_amount=str(calc["grand_total"]),
        net_payable=str(calc["net_payable"]),
    )
    # Payment comes from the user's explicit selection, never from a payment method.
    fields["payment_received"] = (
        str(calc["net_payable"])
        if (fields.get("pos_form", {}).get("paymentStatus") == "paid")
        else "0"
    )
    return calc["subtotal"], calc["vat_amount"]
