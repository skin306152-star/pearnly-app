from datetime import date, datetime
from decimal import Decimal

from services.intake_bridge.convert import erp_declaration_error, validate_erp_histories
from services.intake_bridge.sales_leg import _build_lines
from services.purchase.intake import build_draft_from_invoice
from services.stockcard.movements import MovementSet, _classify_sale


def test_purchase_bridge_preserves_mixed_line_item_types():
    draft = build_draft_from_invoice(
        {
            "subtotal": "150",
            "items": [
                {"name": "stock", "qty": "1", "price": "100", "posting_kind": "stock"},
                {"name": "service", "qty": "1", "price": "50", "posting_kind": "service"},
            ],
        },
        kind="purchase_invoice",
    )
    assert [line["item_type"] for line in draft["lines"]] == ["goods", "service"]


def test_purchase_bridge_does_not_collapse_declared_lines_when_totals_differ():
    draft = build_draft_from_invoice(
        {
            "subtotal": "100",
            "total_amount": "107",
            "items": [
                {"name": "stock", "qty": "1", "price": "100", "posting_kind": "stock"},
                {"name": "service", "qty": "1", "price": "50", "posting_kind": "service"},
            ],
        },
        kind="purchase_invoice",
    )
    assert [line["item_type"] for line in draft["lines"]] == ["goods", "service"]


def test_sales_bridge_preserves_mixed_line_item_types():
    lines = _build_lines(
        {
            "items": [
                {"name": "stock", "qty": "1", "price": "100", "posting_kind": "stock"},
                {"name": "service", "qty": "1", "price": "50", "posting_kind": "service"},
            ]
        }
    )
    assert [line["item_type"] for line in lines] == ["goods", "service"]


def test_stockcard_excludes_service_sales_but_keeps_legacy_default_goods():
    out = MovementSet()
    base = {
        "line_id": "line-1",
        "issue_date": date(2026, 1, 1),
        "doc_number": "S-1",
        "doc_created_at": datetime(2026, 1, 1),
        "doc_type": "tax_invoice",
        "grand_total": Decimal("50"),
        "line_no": 1,
        "product_id": "p-1",
        "description": "service",
        "qty": Decimal("1"),
        "line_total": Decimal("50"),
    }
    _classify_sale({**base, "item_type": "service"}, out)
    assert not out.by_key
    _classify_sale({**base, "line_id": "line-2", "description": "legacy"}, out)
    assert len(out.by_key) == 1


def test_erp_declaration_requires_direction_and_explicit_complete_lines():
    valid = {
        "direction": "sales",
        "items": [{"name": "Consulting", "qty": "1", "posting_kind": "service"}],
    }
    assert erp_declaration_error(valid) is None
    assert erp_declaration_error({**valid, "direction": ""}) == "no_direction"
    assert erp_declaration_error({**valid, "items": []}) == "no_items"
    assert (
        erp_declaration_error(
            {**valid, "items": [{"name": "", "qty": "1", "posting_kind": "stock"}]}
        )
        == "item_name_required"
    )
    assert (
        erp_declaration_error(
            {**valid, "items": [{"name": "A", "qty": "", "posting_kind": "stock"}]}
        )
        == "item_qty_required"
    )
    assert (
        erp_declaration_error({**valid, "items": [{"name": "A", "qty": "1"}]})
        == "posting_kind_required"
    )


def test_validate_erp_histories_fails_closed_for_missing_and_invalid_rows():
    class Cur:
        def execute(self, _sql, _params):
            pass

        def fetchall(self):
            return [
                {
                    "id": "good",
                    "pages": [
                        {
                            "fields": {
                                "direction": "purchase",
                                "items": [{"name": "A", "qty": "1", "posting_kind": "stock"}],
                            }
                        }
                    ],
                },
                {"id": "bad", "pages": [{"fields": {"direction": "sales", "items": []}}]},
            ]

    assert validate_erp_histories(
        Cur(), tenant_id="t1", history_ids=["good", "bad", "missing"]
    ) == {"bad": "no_items", "missing": "not_found"}
