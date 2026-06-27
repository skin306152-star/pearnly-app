# -*- coding: utf-8 -*-
"""B8 RLS · 真 client_rules + member_scopes 表端到端隔离(REFACTOR-B8)。

两表 tenant_id NOT NULL → 纯 tenant 模板(均不用 tenant_ws)。在真 postgres 验:
- client_rules:真 ensure_client_rules_rls() enroll。★回归守门:设了账套上下文,workspace_client_id
  IS NULL 的 firm-wide 默认规则仍可读(证明用 tenant 不是 tenant_ws·后者会隐藏 NULL 行破业务)。
- member_scopes:授权配置(隔离轴 tenant·非 workspace),apply_tenant_rls 后跨租户隔离。
CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_client_rules_member_scopes_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
FAKE = "00000000-0000-0000-0000-0000000000ff"

_CLIENT_RULES_DDL = (
    "id BIGSERIAL PRIMARY KEY, tenant_id uuid NOT NULL, workspace_client_id bigint, "
    "rule_type text NOT NULL DEFAULT 'x', subject_type text NOT NULL DEFAULT 'global', "
    "is_active boolean NOT NULL DEFAULT true"
)
_MEMBER_SCOPES_DDL = (
    "id BIGSERIAL PRIMARY KEY, tenant_id uuid NOT NULL, membership_id uuid NOT NULL, "
    "workspace_client_id bigint NOT NULL, assigned_by uuid NOT NULL"
)


class ClientRulesMemberScopesRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.knowledge import rules_dal

        cls.db = db
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS client_rules, member_scopes CASCADE")
            cur.execute(f"CREATE TABLE client_rules ({_CLIENT_RULES_DDL})")
            cur.execute(f"CREATE TABLE member_scopes ({_MEMBER_SCOPES_DDL})")

        rules_dal.ensure_client_rules_rls()  # 真 ensure:enroll apply_tenant_rls
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.apply_tenant_rls(cur, "member_scopes")  # 同 authz_schema 内联那行
            for t in ("client_rules", "member_scopes"):
                cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {t} TO pearnly_app")
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute("DROP TABLE IF EXISTS client_rules, member_scopes CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE client_rules, member_scopes RESTART IDENTITY")

    def test_client_rules_tenant_scoped(self):
        with self.db.get_cursor_rls(A, commit=True) as cur:
            cur.execute("INSERT INTO client_rules (tenant_id) VALUES (%s)", (A,))
        with self.db.get_cursor_rls(B, commit=True) as cur:
            cur.execute("INSERT INTO client_rules (tenant_id) VALUES (%s)", (B,))
        with self.db.get_cursor_rls(A) as cur:
            cur.execute("SELECT count(*) n FROM client_rules")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(FAKE) as cur:
            cur.execute("SELECT count(*) n FROM client_rules")
            self.assertEqual(cur.fetchone()["n"], 0)

    def test_client_rules_firmwide_null_workspace_visible(self):
        # 回归:tenant 模板下,带账套上下文仍能读到 workspace_client_id IS NULL 的全所默认规则。
        # 若误用 tenant_ws,这一行会被 _WS_MATCH 隐藏 → 此断言失败。
        with self.db.get_cursor_rls(A, commit=True) as cur:
            cur.execute(
                "INSERT INTO client_rules (tenant_id, workspace_client_id) VALUES (%s, NULL)", (A,)
            )
            cur.execute(
                "INSERT INTO client_rules (tenant_id, workspace_client_id) VALUES (%s, 7)", (A,)
            )
        with self.db.get_cursor_rls(A, workspace_client_id=7) as cur:
            cur.execute("SELECT count(*) n FROM client_rules WHERE workspace_client_id IS NULL")
            self.assertEqual(cur.fetchone()["n"], 1, "firm-wide(NULL 账套)默认规则被隐藏了")

    def test_member_scopes_tenant_scoped(self):
        for t in (A, B):
            with self.db.get_cursor_rls(t, commit=True) as cur:
                cur.execute(
                    "INSERT INTO member_scopes (tenant_id, membership_id, workspace_client_id, assigned_by) "
                    "VALUES (%s, gen_random_uuid(), 1, gen_random_uuid())",
                    (t,),
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
                cur.execute("INSERT INTO client_rules (tenant_id) VALUES (%s)", (B,))


if __name__ == "__main__":
    unittest.main()
