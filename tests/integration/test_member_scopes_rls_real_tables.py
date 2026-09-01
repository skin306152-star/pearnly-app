# -*- coding: utf-8 -*-
"""member_scopes 真表租户隔离测试。"""

import os
import unittest

from tests.integration._helpers import require_disposable_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
FAKE = "00000000-0000-0000-0000-0000000000ff"

_DDL = (
    "id BIGSERIAL PRIMARY KEY, tenant_id uuid NOT NULL, membership_id uuid NOT NULL, "
    "workspace_client_id bigint NOT NULL, assigned_by uuid NOT NULL"
)


class MemberScopesRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_disposable_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls

        cls.db = db
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS member_scopes CASCADE")
            cur.execute(f"CREATE TABLE member_scopes ({_DDL})")
            rls.apply_tenant_rls(cur, "member_scopes")
            cur.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON member_scopes TO pearnly_app")
            cur.execute("ALTER TABLE member_scopes FORCE ROW LEVEL SECURITY")
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute("DROP TABLE IF EXISTS member_scopes CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE member_scopes RESTART IDENTITY")

    def test_tenant_scoped(self):
        for tenant_id in (A, B):
            with self.db.get_cursor_rls(tenant_id, commit=True) as cur:
                cur.execute(
                    "INSERT INTO member_scopes "
                    "(tenant_id, membership_id, workspace_client_id, assigned_by) "
                    "VALUES (%s, gen_random_uuid(), 1, gen_random_uuid())",
                    (tenant_id,),
                )
        with self.db.get_cursor_rls(A) as cur:
            cur.execute("SELECT count(*) n FROM member_scopes")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(FAKE) as cur:
            cur.execute("SELECT count(*) n FROM member_scopes")
            self.assertEqual(cur.fetchone()["n"], 0)

    def test_with_check_blocks_cross_tenant(self):
        import psycopg2

        with self.db.get_cursor_rls(A, commit=True) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    "INSERT INTO member_scopes "
                    "(tenant_id, membership_id, workspace_client_id, assigned_by) "
                    "VALUES (%s, gen_random_uuid(), 1, gen_random_uuid())",
                    (B,),
                )


if __name__ == "__main__":
    unittest.main()
