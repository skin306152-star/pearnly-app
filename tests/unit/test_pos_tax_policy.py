from decimal import Decimal

from services.pos import tax_policy


class Cursor:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.row


def test_registered_store_uses_seven_percent_and_requested_price_mode():
    cur = Cursor({"vat_registered": True})
    out = tax_policy.resolve(
        cur, tenant_id="tenant-1", workspace_client_id=9, price_includes_vat=True
    )
    assert out == {
        "vat_registered": True,
        "vat_rate": Decimal("7"),
        "price_includes_vat": True,
        "doc_kind": "abbrev_tax_invoice",
    }
    assert cur.calls[0][1] == ("tenant-1", 9)


def test_unregistered_store_cannot_charge_or_claim_inclusive_vat():
    for row in ({"vat_registered": False}, None):
        cur = Cursor(row)
        out = tax_policy.resolve(
            cur, tenant_id="tenant-1", workspace_client_id=9, price_includes_vat=True
        )
        assert out["vat_rate"] == Decimal("0")
        assert out["price_includes_vat"] is False
        assert out["doc_kind"] == "receipt"
