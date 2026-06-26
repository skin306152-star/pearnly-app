# -*- coding: utf-8 -*-
"""B8 RLS wave3 3b · 真 notification_rules + notification_logs 表端到端隔离(REFACTOR-B8)。

真 ensure_notification_tables()(建两表 + enroll tenant_or_user)+ 真 store 函数,在真 postgres 上验:
租户 A 的规则/日志,租户 B 读不到、改不到、删不到;★ 后台 hook 路径 list_active_*_by_template
经 bypass 仍能跨租户读全表(否则通知漏推)。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_notification_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"


class NotificationRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.notification import store

        cls.db, cls.s = db, store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS notification_rules, notification_logs CASCADE")

        store.ensure_notification_tables()  # 建两表 + enroll tenant_or_user

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON notification_rules,notification_logs "
                "TO pearnly_app"
            )
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            for t in ("notification_rules", "notification_logs"):
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute("DROP TABLE IF EXISTS notification_rules, notification_logs CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE notification_rules, notification_logs RESTART IDENTITY")

    def _seed(self):
        ra = self.s.create_notification_rule(UA, A, "rA", "TPL")
        rb = self.s.create_notification_rule(UB, B, "rB", "TPL")
        self.assertIsNotNone(ra)
        self.assertIsNotNone(rb)
        return ra, rb

    def test_list_rules_cross_tenant_blocked(self):
        self._seed()
        self.assertEqual(
            [r["name"] for r in self.s.list_notification_rules(UA, tenant_id=A)], ["rA"]
        )
        self.assertEqual(
            [r["name"] for r in self.s.list_notification_rules(UB, tenant_id=B)], ["rB"]
        )

    def test_get_update_delete_cross_tenant_blocked(self):
        ra, _ = self._seed()
        self.assertIsNone(self.s.get_notification_rule(ra, UB, tenant_id=B))
        self.assertIsNotNone(self.s.get_notification_rule(ra, UA, tenant_id=A))
        self.assertFalse(self.s.update_notification_rule(ra, UB, B, enabled=False))
        self.assertTrue(self.s.update_notification_rule(ra, UA, A, enabled=False))
        self.assertFalse(self.s.delete_notification_rule(ra, UB, B))
        self.assertTrue(self.s.delete_notification_rule(ra, UA, A))

    def test_logs_cross_tenant_blocked(self):
        self.s.log_notification(UA, A, None, "TPL", "ev", "ref", "luid", "sent")
        self.assertEqual(len(self.s.list_notification_logs(UA, tenant_id=A)), 1)
        self.assertEqual(len(self.s.list_notification_logs(UB, tenant_id=B)), 0)

    def test_hook_bypass_reads_cross_tenant(self):
        # ★ 硬点验证:后台 hook 经 bypass 取全表两租户规则(单租户上下文会漏 → 通知漏推)。
        self._seed()
        rows = self.s.list_active_notification_rules_by_template("TPL")
        self.assertEqual(len(rows), 2)
        self.assertEqual({str(r["tenant_id"]) for r in rows}, {A, B})


if __name__ == "__main__":
    unittest.main()
