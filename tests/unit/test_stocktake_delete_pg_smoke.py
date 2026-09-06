"""Hard deletion is atomic, scoped, retry-safe and serialized with count writes."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import TestCase, mock
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from core.workspace_context import WorkspaceScope
from routes.stocktake_routes import router
from services.stocktake import access, entries, excel, store
from tests.unit import test_stocktake_pg_smoke as legacy
from tests.unit.test_stocktake import ROW, xlsx


class StocktakeDeletePgSmoke(TestCase):
    setUpClass = classmethod(legacy.StocktakePgSmoke.setUpClass.__func__)
    tearDownClass = classmethod(legacy.StocktakePgSmoke.tearDownClass.__func__)
    cursor = legacy.StocktakePgSmoke.cursor
    setUp = legacy.StocktakePgSmoke.setUp

    def create(self):
        return store.create(self.scope, "Delete fixture", excel.parse(xlsx([ROW])), uuid4(), "x")[
            "id"
        ]

    def add(self):
        return entries.write(self.scope, self.task_id, self.item["id"], uuid4(), "2", "WH", "01")

    def totals(self):
        with self.cursor() as cur:
            result = []
            for table in (
                "cowork_stocktakes",
                "cowork_stocktake_items",
                "cowork_stocktake_counts",
                "cowork_stocktake_entries",
                "cowork_stocktake_entry_events",
            ):
                cur.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE tenant_id=%s", (self.tenant,))
                result.append(cur.fetchone()["n"])
            return result

    def test_delete_scan_legacy_and_other_task_survives(self):
        self.add()
        store.close(self.scope, self.task_id)
        other = self.create()
        self.assertEqual(self.totals(), [2, 2, 0, 1, 1])
        self.assertEqual(store.delete_task(self.scope, self.task_id), {"ok": True})
        self.assertEqual(store.delete_task(self.scope, self.task_id), {"ok": True})
        self.assertEqual(self.totals(), [1, 1, 0, 0, 0])
        row = store.detail(self.scope, other)["items"][0]
        with self.cursor(commit=True) as cur:
            cur.execute("UPDATE cowork_stocktakes SET count_mode='legacy' WHERE id=%s", (other,))
        store.count(self.scope, other, row["id"], Decimal("3"), 0)
        self.assertEqual(self.totals(), [1, 1, 1, 0, 0])
        store.delete_task(self.scope, other)
        self.assertEqual(self.totals(), [0, 0, 0, 0, 0])

    def test_cross_tenant_workspace_and_http_permission(self):
        self.add()
        for scope in (
            WorkspaceScope(self.tenant, self.ws + 1, self.user),
            WorkspaceScope(self.other_tenant, self.ws + 2, self.other_user),
        ):
            # Missing and inaccessible IDs have the same idempotent response, with no write.
            self.assertEqual(store.delete_task(scope, self.task_id), {"ok": True})
        self.assertEqual(self.totals(), [1, 1, 0, 1, 1])
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        path = f"/api/cowork/stocktakes/{self.task_id}"
        with mock.patch.object(access, "scope_for", side_effect=HTTPException(403)) as permission:
            self.assertEqual(client.delete(path).status_code, 403)
            self.assertEqual(permission.call_args.args[1], "recon.create")
        self.assertEqual(self.totals(), [1, 1, 0, 1, 1])
        with mock.patch.object(access, "scope_for", return_value=self.scope):
            self.assertEqual(client.delete(path).status_code, 200)
            self.assertEqual(client.delete(path).status_code, 200)
            self.assertEqual(client.get(path).status_code, 404)
            self.assertEqual(client.get(path + "/export").status_code, 404)
            self.assertEqual(client.get("/api/cowork/stocktakes").json()["tasks"], [])
        self.assertEqual(self.totals(), [0, 0, 0, 0, 0])

    def test_failed_delete_rolls_back_all_children(self):
        self.add()
        # A real FK blocks the final parent delete after all child DELETEs have run.
        with self.cursor(commit=True) as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS delete_guard (task_id UUID REFERENCES cowork_stocktakes(id))"
            )
            cur.execute("INSERT INTO delete_guard VALUES (%s)", (self.task_id,))
        from psycopg2.errors import ForeignKeyViolation

        with self.assertRaises(ForeignKeyViolation):
            store.delete_task(self.scope, self.task_id)
        self.assertEqual(self.totals(), [1, 1, 0, 1, 1])

    def test_count_delete_race_cannot_leave_orphan_data(self):
        barrier = Barrier(2)

        def count():
            barrier.wait()
            try:
                self.add()
                return 200
            except HTTPException as exc:
                return exc.status_code

        def delete():
            barrier.wait()
            return store.delete_task(self.scope, self.task_id)

        with ThreadPoolExecutor(max_workers=2) as pool:
            counted, deleted = pool.submit(count), pool.submit(delete)
            self.assertIn(counted.result(), (200, 404))
            self.assertEqual(deleted.result(), {"ok": True})
        self.assertEqual(self.totals(), [0, 0, 0, 0, 0])
