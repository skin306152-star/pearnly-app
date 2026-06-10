# -*- coding: utf-8 -*-
"""authz ensure 迁移守门:种子 6 角色 / 加列 / 回填幂等 / 建表(docs/permissions/01)。

内存假游标拦 SQL · 不触真库(同 test_numbering_workspace_migration 套路)。
"""

import unittest

import services.db_migrations.authz_schema as mig


class _Cur:
    def __init__(self):
        self.sql = []
        self.params = []
        self.rowcount = 0

    def execute(self, sql, params=None):
        self.sql.append(" ".join(sql.split()))
        self.params.append(params)

    def fetchall(self):
        return []

    def fetchone(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _DB:
    def __init__(self, cur):
        self._cur = cur

    def get_cursor(self, commit=False):
        return self._cur


class AuthzMigrationTests(unittest.TestCase):
    def _run(self):
        cur = _Cur()
        orig = mig.db
        mig.db = _DB(cur)
        try:
            mig.ensure_authz_schema()
        finally:
            mig.db = orig
        return cur

    def test_seeds_all_six_system_roles(self):
        cur = self._run()
        seeded = [p[0] for p in cur.params if p and isinstance(p, tuple) and len(p) == 3]
        self.assertEqual(
            set(seeded), {"owner", "admin", "accountant", "clerk", "viewer", "cashier"}
        )

    def test_owner_seeded_with_all_shortcut(self):
        cur = self._run()
        owner_rows = [p for p in cur.params if p and p[0] == "owner"]
        self.assertEqual(owner_rows[0][2], '{"all": true}')

    def test_roles_and_memberships_columns_added(self):
        joined = " || ".join(self._run().sql)
        self.assertIn("ALTER TABLE roles ADD COLUMN IF NOT EXISTS key TEXT", joined)
        self.assertIn(
            "ALTER TABLE memberships ADD COLUMN IF NOT EXISTS scope_mode TEXT NOT NULL DEFAULT 'all'",
            joined,
        )
        self.assertIn("uq_roles_system_key", joined)

    def test_backfill_is_idempotent_and_keeps_legacy_mapping(self):
        joined = " || ".join(self._run().sql)
        self.assertIn("ON CONFLICT (user_id) DO NOTHING", joined)
        self.assertIn("u.role = 'owner' OR u.invited_by IS NULL", joined)
        self.assertIn("ELSE 'accountant'", joined)

    def test_creates_scope_and_invitation_tables(self):
        joined = " || ".join(self._run().sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS member_scopes", joined)
        self.assertIn("workspace_client_id BIGINT NOT NULL", joined)
        self.assertIn("CREATE TABLE IF NOT EXISTS invitations", joined)
        self.assertIn("uq_invitations_token_hash", joined)
