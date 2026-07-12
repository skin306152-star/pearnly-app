import os
import unittest
import uuid

from tests.integration._helpers import require_db


class PosClientUuidScopeRealDbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        try:
            import psycopg2
        except ImportError as exc:
            raise unittest.SkipTest(str(exc)) from exc
        cls.psycopg2 = psycopg2
        cls.schema = "pos_uuid_scope_" + uuid.uuid4().hex
        cls.conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cls.conn.autocommit = True
        with cls.conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA "{cls.schema}"')
            cur.execute(f'SET search_path TO "{cls.schema}"')
            cur.execute(
                "CREATE TABLE pos_sales (tenant_id uuid NOT NULL, workspace_client_id bigint NOT NULL, "
                "client_uuid uuid UNIQUE)"
            )

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "conn", None):
            with cls.conn.cursor() as cur:
                cur.execute(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE')
            cls.conn.close()

    def test_same_uuid_is_unique_only_inside_workspace_scope(self):
        tenant = str(uuid.uuid4())
        client_uuid = str(uuid.uuid4())
        with self.conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}"')
            cur.execute("ALTER TABLE pos_sales DROP CONSTRAINT IF EXISTS pos_sales_client_uuid_key")
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_sales_client_uuid_scope "
                "ON pos_sales (tenant_id, workspace_client_id, client_uuid)"
            )
            cur.execute("INSERT INTO pos_sales VALUES (%s, 1, %s)", (tenant, client_uuid))
            cur.execute("INSERT INTO pos_sales VALUES (%s, 2, %s)", (tenant, client_uuid))
            with self.assertRaises(self.psycopg2.errors.UniqueViolation):
                cur.execute("INSERT INTO pos_sales VALUES (%s, 1, %s)", (tenant, client_uuid))


if __name__ == "__main__":
    unittest.main()
