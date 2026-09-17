from decimal import Decimal
from unittest import TestCase

from fastapi import HTTPException
from services.erp.internal_records import normalized_fields
from services.erp.pos_form import calculate
from services.erp.internal_records import _decimal


class OriginalPosFormTests(TestCase):
    def fields(self, **updates):
        fields = dict(
            manual_layout=2,
            date="16/09/2569",
            price_mode="exclusive",
            pos_form={"paymentStatus": "unpaid"},
            items=[
                dict(
                    name="Original goods",
                    qty="2",
                    price="100",
                    discount="10",
                    vat_rate="7",
                    wht_rate="3",
                )
            ],
        )
        fields.update(updates)
        return fields

    def test_original_per_line_tax_discount_and_payment(self):
        fields = self.fields()
        result = normalized_fields(fields, "purchase", {"name": "Test"}, "test")
        self.assertEqual(Decimal(result["subtotal"]), Decimal("190"))
        self.assertEqual(Decimal(result["vat"]), Decimal("13.30"))
        self.assertEqual(Decimal(result["total_amount"]), Decimal("203.30"))
        self.assertEqual(Decimal(result["wht_amount"]), Decimal("5.70"))
        self.assertEqual(result["payment_received"], "0")
        fields["pos_form"]["paymentStatus"] = "paid"
        result = normalized_fields(fields, "purchase", {"name": "Test"}, "test")
        self.assertEqual(Decimal(result["payment_received"]), Decimal("197.60"))

    def test_inclusive_uses_original_calculator(self):
        fields = self.fields(price_mode="inclusive")
        fields["items"][0].update(price="107", discount="0", wht_rate="0")
        calc, lines, _ = calculate(fields, _decimal)
        self.assertEqual(calc["grand_total"], Decimal("214"))
        self.assertEqual(lines[0]["unit_price"], Decimal("100"))

    def test_bad_override_is_rejected(self):
        fields = self.fields(
            pos_form={
                "manualOn": True,
                "override": {"subtotal": 100, "discount": 0, "vat": 7, "grand": 999},
            }
        )
        with self.assertRaises(HTTPException):
            calculate(fields, _decimal)

    def test_sales_vat_and_wht_are_separate_and_do_not_mark_paid(self):
        fields = self.fields()
        fields["items"][0].update(qty="1", price="100", discount="0", wht_rate="5")
        result = normalized_fields(fields, "sales", {"name": "Test"}, "test")
        self.assertEqual(Decimal(result["vat"]), Decimal("7"))
        self.assertEqual(Decimal(result["wht_amount"]), Decimal("5"))
        self.assertEqual(Decimal(result["total_amount"]), Decimal("107"))
        self.assertEqual(Decimal(result["payment_received"]), Decimal("0"))
