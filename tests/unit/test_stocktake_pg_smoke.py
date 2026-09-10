"""Real PostgreSQL snapshot, RLS, count races and HTTP transaction coverage."""

from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from io import BytesIO
from threading import Barrier
from unittest import TestCase, mock
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from psycopg2.extras import RealDictCursor

from core import db
from core.workspace_context import WorkspaceScope
from routes.stocktake_routes import router
from services.stocktake import store, schema, access, entry_schema, photo_schema
from tests.unit._pg_smoke import connect_or_skip, connect, require_disposable_db
from tests.unit.test_stocktake import ROW, xlsx


class StocktakePgSmoke(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = "stocktake_test_" + uuid4().hex[:12]
        cls.role = cls.schema + "_rls"
        conn = connect_or_skip()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA {cls.schema}")
            cur.execute(f"SET search_path TO {cls.schema}")
            cur.execute(
                "CREATE TABLE tenants (id UUID PRIMARY KEY); CREATE TABLE users (id UUID PRIMARY KEY, username TEXT, full_name TEXT); CREATE TABLE workspace_clients (id BIGINT PRIMARY KEY, tenant_id UUID)"
            )
            cur.execute(schema.DDL)
            entry_schema.apply(cur)
            photo_schema.apply(cur)
            from core.rls import apply_tenant_workspace_rls

            apply_tenant_workspace_rls(
                cur, "cowork_stocktakes", "cowork_stocktake_items", "cowork_stocktake_counts"
            )
            cur.execute(f"CREATE ROLE {cls.role} NOLOGIN NOBYPASSRLS")
            cur.execute(f"GRANT USAGE ON SCHEMA {cls.schema} TO {cls.role}")
            cur.execute(
                f"GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA {cls.schema} TO {cls.role}"
            )
            cur.execute(f"GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA {cls.schema} TO {cls.role}")
        conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = connect()
        conn.autocommit = True
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SET search_path TO {cls.schema}")
            require_disposable_db(cur, cls.schema, "stocktake_test_")
            cur.execute(f"DROP SCHEMA {cls.schema} CASCADE")
            cur.execute(f"DROP ROLE {cls.role}")
        conn.close()

    @contextmanager
    def cursor(
        self, tenant_id=None, workspace_client_id=None, user_id=None, commit=False, **kwargs
    ):
        conn = connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SET search_path TO {self.schema}")
                cur.execute(
                    "SELECT set_config('app.current_tenant_id', %s, true), set_config('app.current_workspace_id', %s, true)",
                    (tenant_id or "", str(workspace_client_id or "")),
                )
                if tenant_id:
                    cur.execute(f"SET LOCAL ROLE {self.role}")
                yield cur
            if commit:
                conn.commit()
            else:
                conn.rollback()
        finally:
            conn.close()

    def setUp(self):
        self.tenant, self.other_tenant, self.user, self.other_user = [
            str(uuid4()) for _ in range(4)
        ]
        # Shared test schema, unique tenant/workspace data for every case.
        self.ws = int(uuid4().int % 1000000000)
        with self.cursor(commit=True) as cur:
            cur.execute("INSERT INTO tenants VALUES (%s),(%s)", (self.tenant, self.other_tenant))
            cur.execute("INSERT INTO users (id) VALUES (%s),(%s)", (self.user, self.other_user))
            cur.execute(
                "INSERT INTO workspace_clients VALUES (%s,%s),(%s,%s),(%s,%s)",
                (self.ws, self.tenant, self.ws + 1, self.tenant, self.ws + 2, self.other_tenant),
            )
        self.scope = WorkspaceScope(self.tenant, self.ws, self.user)
        self.patch = mock.patch.object(db, "get_cursor_rls", self.cursor)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.task_id = self.create()
        self.item = store.detail(self.scope, self.task_id)["items"][0]

    def create(self, request_id=None, digest="original"):
        from services.stocktake.excel import FIELDS

        items = [dict(zip(FIELDS, row)) for row in [ROW, [*ROW[:4], "02", *ROW[5:]]]]
        for item in items:
            item["book_qty"] = Decimal(item["book_qty"])
        result = store.create(
            self.scope,
            "Warehouse count",
            items,
            request_id or uuid4(),
            digest,
        )["id"]
        with self.cursor(commit=True) as cur:
            cur.execute("UPDATE cowork_stocktakes SET count_mode='legacy' WHERE id=%s", (result,))
        return result

    def test_counts_preserve_zero_and_null_with_exact_difference(self):
        store.count(self.scope, self.task_id, self.item["id"], Decimal(0), 0)
        task = store.detail(self.scope, self.task_id)
        self.assertEqual(task["items"][0]["difference"], Decimal("-2.500001"))
        self.assertIsNone(task["items"][1]["actual_qty"])
        listing = store.listing(self.scope)["tasks"][0]
        self.assertEqual((listing["total"], listing["counted"], listing["differences"]), (2, 1, 1))

    def test_tenant_and_company_isolation_for_every_operation(self):
        for scope in (
            WorkspaceScope(self.tenant, self.ws + 1, self.user),
            WorkspaceScope(self.other_tenant, self.ws + 2, self.other_user),
        ):
            self.assertEqual(store.listing(scope)["tasks"], [])
            for action in (
                lambda: store.detail(scope, self.task_id),
                lambda: store.close(scope, self.task_id),
                lambda: store.count(scope, self.task_id, self.item["id"], Decimal(1), 0),
            ):
                with self.assertRaises(HTTPException) as caught:
                    action()
                self.assertEqual(caught.exception.status_code, 404)
        # Direct queries with the app role are also isolated by RLS, even without WHERE.
        with self.cursor(tenant_id=self.other_tenant, workspace_client_id=self.ws + 2) as cur:
            cur.execute("SELECT * FROM cowork_stocktake_items")
            self.assertEqual(cur.fetchall(), [])

    def test_import_retry_is_idempotent_and_cannot_replace_snapshot(self):
        self.assertEqual(self.create(self.task_id), self.task_id)
        self.assertEqual(len(store.detail(self.scope, self.task_id)["items"]), 2)
        with self.assertRaisesRegex(HTTPException, "import_conflict"):
            self.create(self.task_id, digest="replacement")
        self.assertEqual(
            store.detail(self.scope, self.task_id)["items"][0]["book_qty"], Decimal("2.500001")
        )

    def test_retry_and_recount_conflict(self):
        store.count(self.scope, self.task_id, self.item["id"], Decimal("1"), 0)
        store.count(self.scope, self.task_id, self.item["id"], Decimal("1"), 0)
        with self.assertRaisesRegex(HTTPException, "conflict"):
            store.count(self.scope, self.task_id, self.item["id"], Decimal("2"), 0)
        store.count(self.scope, self.task_id, self.item["id"], Decimal("2"), 1)
        with self.cursor() as cur:
            cur.execute(
                "SELECT previous_qty, actual_qty FROM cowork_stocktake_counts WHERE item_id=%s ORDER BY version",
                (self.item["id"],),
            )
            history = cur.fetchall()
        self.assertEqual(len(history), 2)
        self.assertIsNone(history[0]["previous_qty"])
        self.assertEqual(history[1]["previous_qty"], Decimal(1))

    def test_close_locks_all_records_and_retains_uncounted(self):
        store.close(self.scope, self.task_id)
        store.close(self.scope, self.task_id)
        with self.assertRaisesRegex(HTTPException, "closed"):
            store.count(self.scope, self.task_id, self.item["id"], Decimal(1), 0)
        task = store.detail(self.scope, self.task_id)
        self.assertEqual(task["status"], "closed")
        self.assertTrue(all(r["actual_qty"] is None for r in task["items"]))

    def test_concurrent_counts_have_one_winner(self):
        barrier = Barrier(2)

        def run(qty):
            barrier.wait()
            try:
                store.count(self.scope, self.task_id, self.item["id"], Decimal(qty), 0)
                return 200
            except HTTPException as exc:
                return exc.status_code

        with ThreadPoolExecutor(2) as executor:
            results = list(executor.map(run, ["1", "2"]))
        self.assertEqual(sorted(results), [200, 409])

    def test_concurrent_close_and_count_leave_locked_consistent_task(self):
        barrier = Barrier(2)

        def run(close):
            barrier.wait()
            try:
                if close:
                    store.close(self.scope, self.task_id)
                else:
                    store.count(self.scope, self.task_id, self.item["id"], Decimal(1), 0)
                return 200
            except HTTPException as exc:
                return exc.status_code

        with ThreadPoolExecutor(2) as executor:
            results = list(executor.map(run, [True, False]))
        self.assertEqual(results[0], 200)
        self.assertIn(results[1], (200, 409))
        self.assertEqual(store.detail(self.scope, self.task_id)["status"], "closed")
        with self.assertRaises(HTTPException):
            store.count(self.scope, self.task_id, self.item["id"], Decimal(2), 1)

    def test_http_upload_count_export_and_finish(self):
        app = FastAPI()
        app.include_router(router)
        with (
            TestClient(app) as client,
            mock.patch.object(access, "scope_for", return_value=self.scope),
        ):
            response = client.post(
                "/api/cowork/stocktakes",
                data={"name": "HTTP import", "request_id": str(uuid4())},
                files={"file": ("test.xlsx", xlsx([ROW]))},
            )
            self.assertEqual(response.status_code, 200, response.text)
            path = "/api/cowork/stocktakes/" + response.json()["id"]
            with self.cursor(commit=True) as cur:
                cur.execute(
                    "UPDATE cowork_stocktakes SET count_mode='legacy' WHERE id=%s",
                    (response.json()["id"],),
                )
            item = client.get(path).json()["items"][0]
            self.assertEqual(item["book_qty"], "2.500001")
            response = client.put(
                path + "/items/" + item["id"], json={"quantity": "0", "version": 0}
            )
            self.assertEqual(response.status_code, 200, response.text)
            response = client.get(path + "/export")
            from openpyxl import load_workbook

            wb = load_workbook(BytesIO(response.content))
            self.assertEqual(wb.active["H2"].value, 0)
            wb.close()
            self.assertEqual(client.post(path + "/close").status_code, 200)
            self.assertEqual(
                client.put(
                    path + "/items/" + item["id"], json={"quantity": "1", "version": 1}
                ).status_code,
                409,
            )
