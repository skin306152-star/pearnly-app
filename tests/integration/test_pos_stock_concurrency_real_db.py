import concurrent.futures
import os
import time
import unittest
import uuid

from tests.integration._helpers import require_db


class PosStockConcurrencyRealDbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError as exc:
            raise unittest.SkipTest(str(exc)) from exc
        cls.psycopg2 = psycopg2
        cls.cursor_factory = RealDictCursor
        cls.schema = "pos_stock_test_" + uuid.uuid4().hex
        with cls._connect(autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA "{cls.schema}"')
            cur.execute(f'SET search_path TO "{cls.schema}"')
            cur.execute(
                "CREATE TABLE inventory_batches (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, "
                "workspace_client_id bigint, product_id uuid NOT NULL, batch_no text NOT NULL, "
                "expiry_date date, received_at date NOT NULL, unit_cost numeric)"
            )
            cur.execute(
                "CREATE TABLE inventory_stock (id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, "
                "workspace_client_id bigint NOT NULL, product_id uuid NOT NULL, warehouse_id bigint NOT NULL, "
                "batch_id uuid, qty_on_hand numeric NOT NULL, updated_at timestamptz DEFAULT now())"
            )
            cur.execute(
                "CREATE TABLE inventory_transactions (id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, "
                "workspace_client_id bigint NOT NULL, product_id uuid NOT NULL, warehouse_id bigint NOT NULL, "
                "batch_id uuid, txn_type text, qty_delta numeric, unit_cost numeric, ref_type text, ref_id text, "
                "client_uuid uuid, reason text, created_by uuid, created_at timestamptz DEFAULT now())"
            )

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "schema", None):
            with cls._connect(autocommit=True) as conn, conn.cursor() as cur:
                cur.execute(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE')

    @classmethod
    def _connect(cls, autocommit=False):
        conn = cls.psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=cls.cursor_factory)
        conn.autocommit = autocommit
        return conn

    def setUp(self):
        self.tenant = str(uuid.uuid4())
        self.product = str(uuid.uuid4())
        self.batch = str(uuid.uuid4())
        with self._connect(autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute("TRUNCATE inventory_transactions, inventory_stock, inventory_batches")
            cur.execute(
                "INSERT INTO inventory_batches VALUES (%s,%s,7,%s,'B1',CURRENT_DATE,CURRENT_DATE,10)",
                (self.batch, self.tenant, self.product),
            )
            cur.execute(
                "INSERT INTO inventory_stock (tenant_id,workspace_client_id,product_id,warehouse_id,batch_id,qty_on_hand) "
                "VALUES (%s,7,%s,1,%s,5)",
                (self.tenant, self.product, self.batch),
            )

    def _sell(self, sale_id, hold=0):
        from core.pos_api import PosError
        from services.pos.stock import deduct_for_sale

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{self.schema}"')
                deduct_for_sale(
                    cur,
                    tenant_id=self.tenant,
                    workspace_client_id=7,
                    warehouse_id=1,
                    product_id=self.product,
                    qty_base=4,
                    track_batch=True,
                    explicit_batch_id=None,
                    sale_id=sale_id,
                )
                if hold:
                    time.sleep(hold)
            conn.commit()
            return "ok"
        except PosError as exc:
            conn.rollback()
            return exc.code
        finally:
            conn.close()

    def test_two_connections_only_one_sale_wins(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self._sell, "sale-1", 0.4)
            time.sleep(0.1)
            second = pool.submit(self._sell, "sale-2")
            results = [first.result(timeout=5), second.result(timeout=5)]
        self.assertCountEqual(results, ["ok", "pos.out_of_stock"])
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute("SELECT qty_on_hand FROM inventory_stock")
            self.assertEqual(cur.fetchone()["qty_on_hand"], 1)
            cur.execute("SELECT count(*) AS n FROM inventory_transactions")
            self.assertEqual(cur.fetchone()["n"], 1)

    def test_second_line_failure_rolls_back_first_line(self):
        from core.pos_api import PosError
        from services.pos.stock import deduct_for_sale

        other_product = str(uuid.uuid4())
        conn = self._connect()
        with self.assertRaises(PosError):
            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{self.schema}"')
                deduct_for_sale(
                    cur,
                    tenant_id=self.tenant,
                    workspace_client_id=7,
                    warehouse_id=1,
                    product_id=self.product,
                    qty_base=4,
                    track_batch=True,
                    explicit_batch_id=None,
                    sale_id="whole-sale",
                )
                deduct_for_sale(
                    cur,
                    tenant_id=self.tenant,
                    workspace_client_id=7,
                    warehouse_id=1,
                    product_id=other_product,
                    qty_base=1,
                    track_batch=True,
                    explicit_batch_id=None,
                    sale_id="whole-sale",
                )
        conn.rollback()
        conn.close()
        with self._connect() as check, check.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute("SELECT qty_on_hand FROM inventory_stock")
            self.assertEqual(cur.fetchone()["qty_on_hand"], 5)
            cur.execute("SELECT count(*) AS n FROM inventory_transactions")
            self.assertEqual(cur.fetchone()["n"], 0)


if __name__ == "__main__":
    unittest.main()
