"""True PostgreSQL smoke for the ERP team membership table."""

from __future__ import annotations

import importlib.util
import unittest
import uuid
from pathlib import Path
from unittest import mock

from core.rls import apply_tenant_rls
from tests.unit._pg_smoke import connect_or_skip, require_disposable_db

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "0116_erp_team_members.py"


def _migration():
    spec = importlib.util.spec_from_file_location("migration_0116_pg", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ErpTeamPgSmokeTests(unittest.TestCase):
    _schema_prefix = "smoke_erp_team_"

    def setUp(self):
        self.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.schema = self._schema_prefix + uuid.uuid4().hex[:12]
        self.cur.execute(f'CREATE SCHEMA "{self.schema}"')
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        self.cur.execute("CREATE TABLE tenants (id UUID PRIMARY KEY)")
        self.cur.execute(
            "CREATE TABLE users (id UUID PRIMARY KEY, tenant_id UUID REFERENCES tenants(id))"
        )
        self.cur.execute(
            "CREATE TABLE workspace_clients (id BIGINT PRIMARY KEY, tenant_id UUID REFERENCES tenants(id))"
        )
        self.cur.execute("CREATE TABLE erp_endpoints (id UUID PRIMARY KEY, user_id UUID)")
        self.conn.commit()

    def tearDown(self):
        try:
            self.conn.rollback()
            self.cur.execute(f'SET search_path TO "{self.schema}", public')
            require_disposable_db(self.cur, self.schema, self._schema_prefix)
            self.cur.execute(f'DROP SCHEMA IF EXISTS "{self.schema}" CASCADE')
            self.conn.commit()
        finally:
            self.cur.close()
            self.conn.close()

    def _apply(self):
        migration = _migration()
        with mock.patch.object(migration.op, "execute", side_effect=self.cur.execute):
            migration.upgrade()
            migration.upgrade()
        apply_tenant_rls(self.cur, "erp_team_members")

    def _seed_parents(self):
        tenant = str(uuid.uuid4())
        owner = str(uuid.uuid4())
        member = str(uuid.uuid4())
        endpoint = str(uuid.uuid4())
        self.cur.execute("INSERT INTO tenants VALUES (%s)", (tenant,))
        self.cur.execute(
            "INSERT INTO users VALUES (%s,%s),(%s,%s)",
            (owner, tenant, member, tenant),
        )
        self.cur.execute("INSERT INTO workspace_clients VALUES (11,%s)", (tenant,))
        self.cur.execute("INSERT INTO erp_endpoints VALUES (%s,%s)", (endpoint, owner))
        return tenant, owner, member, endpoint

    def test_schema_constraints_index_and_rls_policy(self):
        import psycopg2

        self._apply()
        tenant, owner, member, endpoint = self._seed_parents()
        self.cur.execute(
            "INSERT INTO erp_team_members "
            "(tenant_id,workspace_client_id,user_id,modules,erp_system,erp_endpoint_id,invited_by) "
            "VALUES (%s,11,%s,'[\"purchase\"]','mrerp',%s,%s)",
            (tenant, member, endpoint, owner),
        )
        self.cur.execute("SAVEPOINT invalid_team_system")
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.cur.execute(
                "INSERT INTO erp_team_members "
                "(tenant_id,workspace_client_id,user_id,modules,erp_system,invited_by) "
                "VALUES (%s,11,%s,'[]','unknown',%s)",
                (tenant, owner, owner),
            )
        self.cur.execute("ROLLBACK TO SAVEPOINT invalid_team_system")

        self.cur.execute(
            "SELECT indexname FROM pg_indexes WHERE schemaname=%s AND tablename='erp_team_members'",
            (self.schema,),
        )
        indexes = {row["indexname"] for row in self.cur.fetchall()}
        self.assertIn("ix_erp_team_members_tenant_workspace", indexes)
        self.cur.execute(
            "SELECT policyname,qual,with_check FROM pg_policies "
            "WHERE schemaname=%s AND tablename='erp_team_members'",
            (self.schema,),
        )
        policy = self.cur.fetchone()
        self.assertEqual(policy["policyname"], "tenant_isolation")
        self.assertIn("app.current_tenant_id", policy["qual"])
        self.assertIn("app.current_tenant_id", policy["with_check"])


if __name__ == "__main__":
    unittest.main()
