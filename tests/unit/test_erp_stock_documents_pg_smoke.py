"""Four document sources roll into one stockcard, without double counting."""

import unittest
import uuid
from datetime import date
from decimal import Decimal
from fastapi import HTTPException
from tests.unit.test_erp_internal_records_pg_smoke import InternalRecordsPgSmoke as Fixture
from services.erp import stock_documents as stock
from services.stockcard import report


class StockDocumentsPgSmoke(unittest.TestCase):
    setUpClass = classmethod(Fixture.setUpClass.__func__)
    tearDownClass = classmethod(Fixture.tearDownClass.__func__)
    _fixture_setup = Fixture.setUp

    def setUp(self):
        self._fixture_setup()
        self.cur.execute(
            "INSERT INTO tenant_modules(tenant_id,module_key,enabled) VALUES(%s,'accounting',TRUE)",
            (self.tid,),
        )

    tearDown = Fixture.tearDown
    draft = Fixture.draft
    confirm = Fixture.confirm

    def save(self, direction, qty, price="10", document_id=None):
        return stock.save(
            self.user,
            workspace_id=self.wid,
            direction=direction,
            document_id=document_id or uuid.uuid4(),
            fields={
                "date": "15/09/2569",
                "items": [{"name": "Smoke item", "qty": qty, "price": price, "unit": "件"}],
            },
        )

    def test_history_upgrade_preserves_amounts_and_is_idempotent(self):
        from services.erp.history_upgrade import upgrade

        hid, _ = self.draft(items=[{"name": "Smoke item", "qty": "2", "price": "10", "unit": "件"}])
        self.confirm(hid)
        self.cur.execute(
            "UPDATE purchase_docs SET doc_no='OLD-BILL' WHERE tenant_id=%s", (self.tid,)
        )
        self.cur.execute("SELECT grand_total FROM purchase_docs WHERE tenant_id=%s", (self.tid,))
        amount = self.cur.fetchone()["grand_total"]
        upgrade(self.cur, self.tid)
        self.cur.execute(
            "SELECT doc_no,grand_total FROM purchase_docs WHERE tenant_id=%s", (self.tid,)
        )
        first = self.cur.fetchone()
        self.assertTrue(first["doc_no"].startswith("PE-"))
        self.assertEqual(first["grand_total"], amount)
        upgrade(self.cur, self.tid)
        self.cur.execute(
            "SELECT doc_no,grand_total FROM purchase_docs WHERE tenant_id=%s", (self.tid,)
        )
        self.assertEqual(self.cur.fetchone(), first)
        self.cur.execute(
            "SELECT payload->>'doc_no' AS original FROM erp_history_upgrade_backups WHERE tenant_id=%s AND kind='purchase_docs'",
            (self.tid,),
        )
        self.assertEqual(self.cur.fetchone()["original"], "OLD-BILL")

    def test_product_search_is_scoped_and_literal(self):
        from services.erp.item_identity import search

        self.save("in", "2")
        result = search(self.user, self.wid, "moke")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name_th"], "Smoke item")
        self.assertEqual(search(self.user, self.wid, "%"), [])
        self.assertEqual(search(self.user, self.wid, ""), [])
        with self.assertRaises(HTTPException):
            search(self.user, self.wid + 999999, "Smoke")

    def test_four_sources_and_retry(self):
        hid, _ = self.draft(
            items=[{"name": "Smoke item", "qty": "10", "price": "10", "unit": "件"}]
        )
        self.confirm(hid)
        self.cur.execute(
            "UPDATE purchase_docs SET created_at='2026-09-15 01:00:00+00' WHERE tenant_id=%s",
            (self.tid,),
        )
        ir = self.save("in", "10", "20")
        self.cur.execute(
            "UPDATE erp_stock_documents SET created_at='2026-09-15 02:00:00+00' WHERE tenant_id=%s",
            (self.tid,),
        )
        hid, _ = self.draft(
            "sales", items=[{"name": "Smoke item", "qty": "4", "price": "99", "unit": "件"}]
        )
        self.confirm(hid, "sales")
        self.cur.execute(
            "UPDATE sales_documents SET created_at='2026-09-15 03:00:00+00' WHERE tenant_id=%s",
            (self.tid,),
        )
        key = uuid.uuid4()
        out = self.save("out", "6", document_id=key)
        self.assertEqual(self.save("out", "6", document_id=key), out)
        self.assertEqual(ir["doc_no"], "IR-25690915-0001")
        self.assertEqual(out["doc_no"], "IS-25690915-0001")
        self.assertEqual(out["fields"]["total_amount"], "90.00")
        groups = report.groups(
            self.cur,
            tenant_id=self.tid,
            workspace_client_id=self.wid,
            date_from=date(2026, 9, 1),
            date_to=date(2026, 9, 30),
            erp_costs=True,
        )
        self.assertEqual(len(groups), 1)
        rows = groups[0]["rows"][1:]
        self.assertEqual([r["doc_no"].split("-")[0] for r in rows], ["PE", "IR", "SI", "IS"])
        self.assertEqual(Decimal(groups[0]["totals"]["bal_qty"]), 10)
        self.assertEqual(Decimal(groups[0]["totals"]["bal_value"]), 150)
        self.cur.execute("SELECT count(*) AS n FROM purchase_docs WHERE tenant_id=%s", (self.tid,))
        self.assertEqual(self.cur.fetchone()["n"], 1)
        self.cur.execute(
            "SELECT count(*) AS n FROM sales_documents WHERE tenant_id=%s", (self.tid,)
        )
        self.assertEqual(self.cur.fetchone()["n"], 1)
        with self.assertRaises(HTTPException):
            self.save("out", "7", document_id=key)

    def test_bad_rows_and_foreign_workspace(self):
        with self.assertRaises(HTTPException):
            self.save("in", "-1")
        with self.assertRaises(HTTPException):
            stock.save(
                self.user,
                workspace_id=self.wid + 999,
                direction="in",
                document_id=uuid.uuid4(),
                fields={"date": "15/09/2569", "items": [{"name": "A", "qty": "1", "price": "1"}]},
            )
        self.cur.execute(
            "SELECT count(*) AS n FROM erp_stock_documents WHERE tenant_id=%s", (self.tid,)
        )
        self.assertEqual(self.cur.fetchone()["n"], 0)

    def test_unknown_cost_stays_unknown(self):
        doc = self.save("out", "2")
        self.assertIsNone(doc["fields"]["total_amount"])
        self.assertIsNone(doc["fields"]["items"][0]["price"])

    def test_identity_exact_name_unit_and_scope(self):
        from services.erp.item_identity import resolve_items

        items = [
            {"name": "Identity", "unit": "box"},
            {"name": "Identity", "unit": "box"},
            {"name": "Identity", "unit": "piece"},
        ]
        resolve_items(self.cur, tenant_id=self.tid, workspace_id=self.wid, items=items)
        self.assertEqual(items[0]["product_id"], items[1]["product_id"])
        self.assertNotEqual(items[0]["product_id"], items[2]["product_id"])
        self.assertRegex(items[0]["code"], r"^P-[0-9]{6}$")
        with self.assertRaises(HTTPException):
            resolve_items(
                self.cur,
                tenant_id=self.tid,
                workspace_id=self.wid,
                items=[{"name": "Identity", "code": items[0]["code"], "unit": "piece"}],
            )

    def test_backdated_receipt_replays_issue_detail_like_report(self):
        original = self.save("in", "10", "10")
        self.cur.execute(
            "UPDATE erp_stock_documents SET created_at='2026-09-15 01:00:00+00' WHERE id=%s",
            (original["id"],),
        )
        out = self.save("out", "2")
        self.assertEqual(out["fields"]["total_amount"], "20.00")
        stock.save(
            self.user,
            workspace_id=self.wid,
            direction="in",
            document_id=uuid.uuid4(),
            fields={
                "date": "14/09/2569",
                "items": [{"name": "Smoke item", "qty": "10", "price": "30", "unit": "件"}],
            },
        )
        docs = stock.list_documents(self.user, None, workspace_id=self.wid, direction="out")
        self.assertEqual(docs[0]["fields"]["total_amount"], "40.00")

    def test_cowork_rejected(self):
        user = {**self.user, "entry": "cowork"}
        with self.assertRaises(HTTPException):
            stock.save(
                user,
                workspace_id=self.wid,
                direction="in",
                document_id=uuid.uuid4(),
                fields={"date": "15/09/2569", "items": [{"name": "A", "qty": "1", "price": "1"}]},
            )


# Do not collect the imported fixture as a second test class.
del Fixture
