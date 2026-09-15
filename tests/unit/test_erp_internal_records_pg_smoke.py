"""Internal web/LINE saves against PostgreSQL; every case rolls its test data back."""

from __future__ import annotations

import copy
import json
import unittest
import uuid
from contextlib import contextmanager
from unittest.mock import patch

from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from core import db
from services.erp import internal_records
from services.erp.internal_push_guard import require_external_history, require_external_user
from tests.unit._pg_smoke import connect_or_skip


class InternalRecordsPgSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.tid, self.uid, self.rid = [str(uuid.uuid4()) for _ in range(3)]
        self.cur.execute("INSERT INTO tenants(id,name) VALUES(%s,'Internal smoke')", (self.tid,))
        self.cur.execute(
            "INSERT INTO users(id,username,password_hash,tenant_id) VALUES(%s,%s,'unused',%s)",
            (self.uid, self.uid, self.tid),
        )
        self.cur.execute(
            "INSERT INTO roles(id,name,key,permissions,tenant_id) VALUES(%s,%s,'owner','{\"all\":true}',%s)",
            (self.rid, self.rid, self.tid),
        )
        self.cur.execute(
            "INSERT INTO memberships(user_id,tenant_id,role_id) VALUES(%s,%s,%s)",
            (self.uid, self.tid, self.rid),
        )
        for key in ["purchase", "sales"]:
            self.cur.execute(
                "INSERT INTO tenant_modules(tenant_id,module_key,enabled) VALUES(%s,%s,TRUE)",
                (self.tid, key),
            )
        self.cur.execute(
            "INSERT INTO workspace_clients(user_id,tenant_id,name,tax_id) VALUES(%s,%s,'Smoke company','0105559999999') RETURNING id",
            (self.uid, self.tid),
        )
        self.wid = self.cur.fetchone()["id"]
        self.user = {
            "id": self.uid,
            "tenant_id": self.tid,
            "entry": "erp",
            "role": "owner",
            "is_active": True,
        }
        self.count = 0

        @contextmanager
        def cursor(*args, **kwargs):
            self.count += 1
            name = f"internal_smoke_{self.count}"
            self.cur.execute(f"SAVEPOINT {name}")
            try:
                yield self.cur
                self.cur.execute(f"RELEASE SAVEPOINT {name}")
            except Exception:
                self.cur.execute(f"ROLLBACK TO SAVEPOINT {name}")
                raise

        self.patches = [
            patch.object(db, "get_cursor", cursor),
            patch.object(db, "get_cursor_rls", cursor),
        ]
        for mock in self.patches:
            mock.start()

    def tearDown(self):
        for mock in reversed(self.patches):
            mock.stop()
        self.conn.rollback()
        self.cur.close()

    def draft(self, direction="purchase", source="erp_web", **fields):
        hid = str(uuid.uuid4())
        data = {
            "date": "2026-09-15",
            "seller_name": "Supplier",
            "buyer_name": "Customer",
            "items": [{"name": "Smoke item", "qty": "2", "price": "100", "posting_kind": "stock"}],
            "vat": "0",
            **fields,
        }
        result = internal_records.save_draft(
            self.user,
            history_id=hid,
            workspace_id=self.wid,
            direction=direction,
            fields=data,
            source=source,
        )
        return hid, result["fields"]

    def confirm(self, hid, direction="purchase"):
        return internal_records.confirm(
            self.user, history_ids=[hid], workspace_id=self.wid, direction=direction
        )

    def test_web_and_line_both_directions_are_internal_and_idempotent(self):
        for direction in ["purchase", "sales"]:
            for source in ["erp_web", "line_erp"]:
                hid, fields = self.draft(direction, source)
                self.assertEqual(self.confirm(hid, direction)["status"], "saved")
                self.assertEqual(
                    self.confirm(hid, direction)["skipped"][0]["reason"], "already_converted"
                )
                replay = internal_records.save_draft(
                    self.user,
                    history_id=hid,
                    workspace_id=self.wid,
                    direction=direction,
                    fields=fields,
                    source=source,
                )
                self.assertEqual(replay["status"], "saved")
                table = "purchase_docs" if direction == "purchase" else "sales_documents"
                self.cur.execute(
                    f"SELECT count(*) AS n FROM {table} WHERE ocr_history_id=%s", (hid,)
                )
                self.assertEqual(self.cur.fetchone()["n"], 1)
                self.cur.execute(
                    "SELECT count(*) AS n FROM erp_push_logs WHERE history_id=%s", (hid,)
                )
                self.assertEqual(self.cur.fetchone()["n"], 0)

    def test_retry_query_excludes_internal_sources_and_keeps_cowork(self):
        from services.erp.push_retry import list_logs_due_for_retry

        endpoint = str(uuid.uuid4())
        self.cur.execute(
            "INSERT INTO erp_endpoints(id,user_id,name,adapter,config) VALUES(%s,%s,'smoke','webhook','{}')",
            (endpoint, self.uid),
        )
        logs = {}
        for source in ("erp_web", "line_erp", "manual"):
            hid, _ = self.draft()
            self.cur.execute("UPDATE ocr_history SET source=%s WHERE id=%s", (source, hid))
            self.cur.execute(
                "INSERT INTO erp_push_logs(user_id,endpoint_id,history_id,status,retry_count,max_retries,next_retry_at) "
                "VALUES(%s,%s,%s,'failed',0,3,NOW()-INTERVAL '1 minute') RETURNING id",
                (self.uid, endpoint, hid),
            )
            logs[source] = str(self.cur.fetchone()["id"])
        due = {str(row["id"]) for row in list_logs_due_for_retry(100)}
        self.assertIn(logs["manual"], due)
        self.assertNotIn(logs["erp_web"], due)
        self.assertNotIn(logs["line_erp"], due)

    def test_partial_batch_rolls_back_and_keeps_drafts(self):
        good, _ = self.draft()
        bad, _ = self.draft(items=[])
        with self.assertRaises(HTTPException):
            internal_records.confirm(
                self.user, history_ids=[good, bad], workspace_id=self.wid, direction="purchase"
            )
        self.cur.execute("SELECT staged FROM ocr_history WHERE id=ANY(%s::uuid[])", ([good, bad],))
        self.assertTrue(all(row["staged"] for row in self.cur.fetchall()))
        self.cur.execute("SELECT count(*) AS n FROM purchase_docs WHERE ocr_history_id=%s", (good,))
        self.assertEqual(self.cur.fetchone()["n"], 0)

    def test_scope_and_direction_cannot_be_changed(self):
        hid, fields = self.draft()
        with self.assertRaises(HTTPException):
            self.confirm(hid, "sales")
        other = {**self.user, "tenant_id": str(uuid.uuid4())}
        with self.assertRaises(HTTPException):
            internal_records.save_draft(
                other, history_id=hid, workspace_id=self.wid, direction="purchase", fields=fields
            )
        self.cur.execute("SELECT pages FROM ocr_history WHERE id=%s", (hid,))
        self.assertEqual(self.cur.fetchone()["pages"][0]["fields"]["direction"], "purchase")

    def test_persisted_source_is_available_to_external_dispatch_guards(self):
        hid, _ = self.draft()
        detail = db.get_ocr_history_detail(self.uid, hid, tenant_id=self.tid)
        self.assertEqual(detail["source"], "erp_web")
        with self.assertRaises(HTTPException):
            require_external_history(detail)
        with self.assertRaises(HTTPException):
            require_external_user(self.user)
        require_external_history({"source": "manual"})
        require_external_history({"source": "cowork_line"})
        require_external_user({"entry": "cowork"})

    def test_amounts_and_foreign_company_are_rejected(self):
        for amount in ["NaN", "Infinity", "-1"]:
            with self.assertRaises(HTTPException):
                self.draft(vat=amount)
        with self.assertRaises(HTTPException):
            self.draft(buyer_tax="9999999999999")

    def test_custom_vat_and_service_rows_keep_totals(self):
        for direction in ["purchase", "sales"]:
            hid, _ = self.draft(direction, vat="10")
            result = self.confirm(hid, direction)
            table = "purchase_docs" if direction == "purchase" else "sales_documents"
            self.cur.execute(
                f"SELECT * FROM {table} WHERE id=%s", (result["converted"][0]["doc_id"],)
            )
            row = self.cur.fetchone()
            # Purchase and sales keep their native header naming.
            actual = row.get("grand_total", row.get("total_amount", row.get("total")))
            self.assertEqual(str(actual), "210.00")


if __name__ == "__main__":
    unittest.main()
