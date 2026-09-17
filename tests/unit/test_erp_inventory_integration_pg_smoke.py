"""ERP inventory reuses the document journal, including stocktake variances."""

from decimal import Decimal
from fastapi import HTTPException
from tests.unit.test_erp_stock_documents_pg_smoke import StockDocumentsPgSmoke
from services.erp import inventory, product_numbers, item_identity
from services.sales import products


class InventoryIntegrationPgSmoke(StockDocumentsPgSmoke):
    def overview(self, **kwargs):
        return inventory.overview(self.cur, tenant_id=self.tid, workspace_id=self.wid, **kwargs)

    def test_product_number_shared_with_document_identity(self):
        p = products.create_product(
            self.cur,
            tenant_id=self.tid,
            workspace_client_id=self.wid,
            fields=product_numbers.prepare(
                self.cur, self.tid, {"name_th": "Smoke item", "unit": "件"}
            ),
        )
        doc = self.save("in", "10", "20")
        self.assertEqual(doc["fields"]["items"][0]["product_id"], str(p["id"]))
        self.assertEqual(doc["fields"]["items"][0]["code"], p["code"])
        self.assertEqual(p["base_unit"], "件")
        self.assertEqual(len(self.overview()["items"]), 1)

    def test_count_and_report_same_balance_retry_and_unknown(self):
        self.save("in", "10", "20")
        self.save("out", "3")
        before = self.overview()["items"][0]
        pid = before["product_id"]
        self.assertEqual(Decimal(before["qty_on_hand"]), 7)
        req = [{"product_id": pid, "counted_qty": "5"}]
        changed = inventory.count(self.cur, self.user, self.wid, req)
        self.assertEqual(len(changed["documents"]), 1)
        self.assertEqual(inventory.count(self.cur, self.user, self.wid, req)["documents"], [])
        after = self.overview()
        self.assertEqual(Decimal(after["items"][0]["qty_on_hand"]), 5)
        self.assertEqual(Decimal(after["summary"]["stock_value"]), 100)
        inventory.count(self.cur, self.user, self.wid, [{"product_id": pid, "counted_qty": "8"}])
        self.assertEqual(Decimal(self.overview()["summary"]["stock_value"]), 160)
        self.assertIsNone(self.overview(mask_cost=True)["summary"]["stock_value"])
        self.assertEqual(len(self.overview(query=before["code"])["items"]), 1)
        self.assertEqual(self.overview(query="%")["items"], [])
        with self.assertRaises(HTTPException):
            inventory.count(self.cur, self.user, self.wid + 999999, req)

    def test_overview_four_sources(self):
        hid, _ = self.draft(
            items=[{"name": "Smoke item", "qty": "10", "price": "20", "unit": "件"}]
        )
        self.confirm(hid)
        self.save("in", "5", "20")
        hid, _ = self.draft(
            direction="sales",
            items=[{"name": "Smoke item", "qty": "2", "price": "50", "unit": "件"}],
        )
        self.confirm(hid, direction="sales")
        self.save("out", "3")
        data = self.overview()
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(Decimal(data["items"][0]["qty_on_hand"]), 10)
        self.assertEqual(Decimal(data["summary"]["stock_value"]), 200)

    def test_count_request_retry_after_intervening_movement(self):
        import uuid

        self.save("in", "10", "20")
        pid = self.overview()["items"][0]["product_id"]
        rid = str(uuid.uuid4())
        args = [{"product_id": pid, "counted_qty": "8"}]
        first = inventory.count(self.cur, self.user, self.wid, args, request_id=rid)
        self.save("out", "1")
        second = inventory.count(self.cur, self.user, self.wid, args, request_id=rid)
        self.assertEqual(first, second)
        self.assertEqual(Decimal(self.overview()["items"][0]["qty_on_hand"]), 7)

    def test_product_stock_and_unit_guard(self):
        self.save("in", "2", "20")
        pid = self.overview()["items"][0]["product_id"]
        for fields in ({"is_active": False}, {"unit": "箱"}):
            with self.assertRaises(HTTPException):
                product_numbers.guard_change(self.cur, self.tid, self.wid, pid, fields)
        product_numbers.guard_change(self.cur, self.tid, self.wid, pid, {"unit": "件"})
        self.save("out", "2")
        product_numbers.guard_change(self.cur, self.tid, self.wid, pid, {"is_active": False})
