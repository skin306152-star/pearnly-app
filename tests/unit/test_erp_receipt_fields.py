from decimal import Decimal

import pytest
from fastapi import HTTPException

from services.erp.internal_payment import payment
from services.erp.business_dates import business_fields, standard
from services.erp.ocr_fields import context, extend
from services.ocr.schemas_invoice import ThaiInvoice


def test_erp_dates_use_printed_year_not_current_year_or_model_guess():
    with context(True):
        assert ThaiInvoice(date="2026-06-30", date_raw="30-06-2025").date == "2025-06-30"
        assert ThaiInvoice(date="2025-06-30", date_raw="30-06-2026").date == "2026-06-30"
        assert ThaiInvoice(date="2569-05-24", date_raw="24/05/2569").date == "2026-05-24"
        assert ThaiInvoice(date="2026-05-24", date_raw="24/05/69").date is None
        assert ThaiInvoice(date="2026-05-24", date_raw="").date is None
    f = business_fields({"date": "2026-05-24", "date_raw": "24-05-2569"})
    assert f["date"] == "24/05/2569"
    assert f["date_raw"] == "24-05-2569"
    assert business_fields(f) == f
    assert standard(f["date"]) == "2026-05-24"


def test_erp_prompt_context_does_not_change_cowork():
    assert extend("existing") == "existing"
    with context(True):
        assert "payment_received" in extend("existing")
        output = extend('{"cash_amount": "cash", "change_amount": "change"}')
        assert '"payment_received":' in output.split("ERP receipt review:")[0]
        with context(False):
            assert extend("existing") == "existing"
    assert extend("existing") == "existing"


@pytest.mark.parametrize("direction", ["purchase", "sales"])
def test_explicit_receipt_payments(direction):
    assert (
        payment(
            {"total_amount": "3806", "payment_method": "card", "payment_received": "3806"},
            direction,
        )["status"]
        == "paid"
    )
    assert (
        payment({"total_amount": "3806", "payment_method": "card"}, direction)["status"] == "unpaid"
    )
    f = {
        "total_amount": "1125",
        "cash_amount": "2000",
        "change_amount": "875",
        "payment_method": "cash",
    }
    assert payment(f, direction)["paid_amount"] == Decimal("1125.00")
    f["payment_received"] = "1125"
    assert payment(f, direction)["paid_amount"] == Decimal("1125.00")
    assert (
        payment({"total_amount": "100", "payment_received": "40"}, direction)["status"] == "partial"
    )
    with pytest.raises(HTTPException):
        payment({"total_amount": "100", "payment_received": "101"}, direction)
