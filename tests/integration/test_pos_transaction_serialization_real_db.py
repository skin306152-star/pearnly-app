import concurrent.futures
import os
import time
import unittest
import uuid

from tests.integration._helpers import require_db


class PosTransactionSerializationRealDbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        try:
            import psycopg2
        except ImportError as exc:
            raise unittest.SkipTest(str(exc)) from exc
        cls.psycopg2 = psycopg2
        cls.schema = "pos_serial_" + uuid.uuid4().hex
        with cls._connect(autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA "{cls.schema}"')
            cur.execute(f'SET search_path TO "{cls.schema}"')
            cur.execute(
                "CREATE TABLE sales (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, workspace_id bigint NOT NULL, "
                "client_uuid uuid, status text NOT NULL, amount numeric NOT NULL)"
            )
            cur.execute(
                "CREATE UNIQUE INDEX uq_sales_client_scope "
                "ON sales (tenant_id, workspace_id, client_uuid)"
            )
            cur.execute(
                "CREATE TABLE refunds (id bigserial PRIMARY KEY, sale_id uuid NOT NULL, amount numeric NOT NULL)"
            )
            cur.execute("CREATE TABLE shifts (id uuid PRIMARY KEY, status text NOT NULL)")

    @classmethod
    def tearDownClass(cls):
        with cls._connect(autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE')

    @classmethod
    def _connect(cls, autocommit=False):
        conn = cls.psycopg2.connect(os.environ["DATABASE_URL"])
        conn.autocommit = autocommit
        return conn

    def setUp(self):
        with self._connect(autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute("TRUNCATE refunds, sales, shifts")

    def test_same_client_uuid_creates_only_one_sale(self):
        tenant, client_uuid = str(uuid.uuid4()), str(uuid.uuid4())

        def create_or_get(hold=0):
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{self.schema}"')
                scope = f"pos:{tenant}:7:{client_uuid}"
                cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (scope,))
                cur.execute(
                    "SELECT id FROM sales WHERE tenant_id=%s AND workspace_id=7 AND client_uuid=%s",
                    (tenant, client_uuid),
                )
                row = cur.fetchone()
                if row:
                    return "deduped"
                cur.execute(
                    "INSERT INTO sales VALUES (%s,%s,7,%s,'completed',100)",
                    (str(uuid.uuid4()), tenant, client_uuid),
                )
                if hold:
                    time.sleep(hold)
                return "created"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(create_or_get, 0.3)
            time.sleep(0.05)
            second = pool.submit(create_or_get)
            results = [first.result(timeout=5), second.result(timeout=5)]
        self.assertCountEqual(results, ["created", "deduped"])

    def test_two_partial_refunds_cannot_exceed_original(self):
        sale_id, tenant = str(uuid.uuid4()), str(uuid.uuid4())
        with self._connect(autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute(
                "INSERT INTO sales VALUES (%s,%s,7,NULL,'completed',100)", (sale_id, tenant)
            )

        def refund(hold=0):
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{self.schema}"')
                cur.execute("SELECT amount FROM sales WHERE id=%s FOR UPDATE", (sale_id,))
                total = cur.fetchone()[0]
                cur.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM refunds WHERE sale_id=%s", (sale_id,)
                )
                if cur.fetchone()[0] + 60 > total:
                    return "rejected"
                cur.execute("INSERT INTO refunds (sale_id,amount) VALUES (%s,60)", (sale_id,))
                if hold:
                    time.sleep(hold)
                return "created"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(refund, 0.3)
            time.sleep(0.05)
            second = pool.submit(refund)
            results = [first.result(timeout=5), second.result(timeout=5)]
        self.assertCountEqual(results, ["created", "rejected"])

    def test_double_void_compare_and_set_has_one_winner(self):
        sale_id, tenant = str(uuid.uuid4()), str(uuid.uuid4())
        with self._connect(autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute(
                "INSERT INTO sales VALUES (%s,%s,7,NULL,'completed',100)", (sale_id, tenant)
            )

        def void():
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{self.schema}"')
                cur.execute(
                    "UPDATE sales SET status='void' WHERE id=%s AND status='completed' RETURNING id",
                    (sale_id,),
                )
                return "voided" if cur.fetchone() else "stale"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                future.result(timeout=5) for future in (pool.submit(void), pool.submit(void))
            ]
        self.assertCountEqual(results, ["voided", "stale"])

    def test_sale_and_shift_close_serialize_on_shift_row(self):
        shift_id = str(uuid.uuid4())
        with self._connect(autocommit=True) as conn, conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute("INSERT INTO shifts VALUES (%s,'open')", (shift_id,))

        def sale(hold=0):
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{self.schema}"')
                cur.execute("SELECT status FROM shifts WHERE id=%s FOR UPDATE", (shift_id,))
                if cur.fetchone()[0] != "open":
                    return "closed"
                cur.execute(
                    "INSERT INTO sales VALUES (%s,%s,7,NULL,'completed',10)",
                    (str(uuid.uuid4()), str(uuid.uuid4())),
                )
                if hold:
                    time.sleep(hold)
                return "created"

        def close():
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{self.schema}"')
                cur.execute("SELECT status FROM shifts WHERE id=%s FOR UPDATE", (shift_id,))
                cur.execute("UPDATE shifts SET status='closed' WHERE id=%s", (shift_id,))
                return "closed"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(sale, 0.3)
            time.sleep(0.05)
            second = pool.submit(close)
            self.assertEqual(first.result(timeout=5), "created")
            self.assertEqual(second.result(timeout=5), "closed")
        self.assertEqual(sale(), "closed")


if __name__ == "__main__":
    unittest.main()
