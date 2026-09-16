"""ERP stockcard conservation, receipt precision and unknown costs."""

from decimal import Decimal as D

from services.stockcard.report import grand_totals
from services.stockcard.rolling import Balance, Movement, ZERO_BALANCE, roll


def move(side, qty, price=None, amount=None):
    return Movement(
        1,
        "TEST",
        "",
        side,
        D(qty),
        None if price is None else D(price),
        (1,),
        None if amount is None else D(amount),
    )


def test_receipt_preserves_net_total_and_full_depletion_clears_rounding():
    final, rows = roll(
        ZERO_BALANCE,
        [move("in", "3", "0.33", "1.00"), move("out", "1"), move("out", "2")],
        erp_costs=True,
    )
    assert rows[0]["amount"] == D("1.00")
    assert rows[1]["amount"] == D("0.33")
    assert rows[2]["amount"] == D("0.67")
    assert final.qty == final.value == 0
    assert sum(r["amount"] if r["kind"] == "in" else -r["amount"] for r in rows) == final.value


def test_unknown_negative_opening_does_not_invent_negative_average():
    final, rows = roll(ZERO_BALANCE, [move("out", "10"), move("in", "5", "10")], erp_costs=True)
    assert final.qty == -5
    assert final.unit is None and final.value is None
    assert rows[-1]["amount"] == D("50.00")


def test_period_quantity_value_conserve_and_sale_uses_cost():
    initial = Balance(D("10"), D("100"), D("10"))
    final, rows = roll(initial, [move("in", "10", "20"), move("out", "4")], erp_costs=True)
    assert rows[1]["unit_price"] == D("15")
    assert final.qty == D("16") and final.value == D("240")
    assert initial.qty + D("10") - D("4") == final.qty
    assert initial.value + rows[0]["amount"] - rows[1]["amount"] == final.value


def test_grand_totals_sum_products_not_unit_prices_and_propagate_unknown():
    groups = [
        {
            "totals": {
                "in_qty": "3",
                "in_amount": "1.00",
                "out_qty": "1",
                "out_amount": "0.33",
                "bal_qty": "2",
                "bal_value": "0.67",
            }
        },
        {
            "totals": {
                "in_qty": "4",
                "in_amount": "20.00",
                "out_qty": "2",
                "out_amount": None,
                "bal_qty": "-2",
                "bal_value": None,
            }
        },
    ]
    total = grand_totals(groups)
    assert total == {
        "in_qty": "7",
        "in_amount": "21.00",
        "out_qty": "3",
        "out_amount": None,
        "bal_qty": "0",
        "bal_value": None,
    }
    assert "bal_unit_cost" not in total
