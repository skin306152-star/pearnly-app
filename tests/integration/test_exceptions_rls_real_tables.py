# -*- coding: utf-8 -*-
"""B8 RLS wave3 3b · 真 exceptions + exception_whitelist 表端到端隔离(REFACTOR-B8)。

用真 ensure_exceptions_tables()(建两表 + enroll tenant_or_user)+ 真 store/whitelist 函数,
在真 postgres 上验证:租户 A 写的异常/白名单,租户 B 一概读不到、改不到、删不到(WITH CHECK 也验)。
CI 默认 skip(无真 DB),本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_exceptions_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"

# ocr_history 留作普通桩(不 enroll)· list_exceptions 的 INNER JOIN 用它,隔离全来自 exceptions policy。
_OCR_STUB = (
    "CREATE TABLE ocr_history (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), "
    "user_id UUID, tenant_id UUID, filename TEXT, invoice_date DATE, "
    "confidence TEXT, client_id BIGINT)"
)


class ExceptionsRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.exceptions import store, exceptions_whitelist as wl

        cls.db, cls.s, cls.wl = db, store, wl
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS exceptions, exception_whitelist, ocr_history CASCADE")
            cur.execute(_OCR_STUB)

        store.ensure_exceptions_tables()  # 建两表 + enroll tenant_or_user

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON exceptions,exception_whitelist,ocr_history "
                "TO pearnly_app"
            )
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            # FORCE:本地恢复库 owner 也受 policy 约束才能真测隔离(prod 靠非 owner 角色)
            for t in ("exceptions", "exception_whitelist"):
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(
                    "DROP TABLE IF EXISTS exceptions, exception_whitelist, ocr_history CASCADE"
                )

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE exceptions, exception_whitelist, ocr_history RESTART IDENTITY")

    def _seed(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO ocr_history(user_id,tenant_id,filename) VALUES (%s,%s,'a.pdf') "
                "RETURNING id",
                (UA, A),
            )
            ha = str(cur.fetchone()["id"])
            cur.execute(
                "INSERT INTO ocr_history(user_id,tenant_id,filename) VALUES (%s,%s,'b.pdf') "
                "RETURNING id",
                (UB, B),
            )
            hb = str(cur.fetchone()["id"])
        # 真 store 函数写异常(RLS 下 WITH CHECK 校验租户)
        ea = self.s.insert_exception(UA, A, ha, "DUP", seller_name="S-A")
        eb = self.s.insert_exception(UB, B, hb, "DUP", seller_name="S-B")
        self.assertIsNotNone(ea)
        self.assertIsNotNone(eb)
        return ea, eb, ha, hb

    def test_list_cross_tenant_blocked(self):
        _, _, _, _ = self._seed()
        a = self.s.list_exceptions(UA, tenant_id=A)
        self.assertEqual([e["seller_name"] for e in a], ["S-A"])
        b = self.s.list_exceptions(UB, tenant_id=B)
        self.assertEqual([e["seller_name"] for e in b], ["S-B"])

    def test_get_cross_tenant_blocked(self):
        ea, _, _, _ = self._seed()
        self.assertIsNone(self.s.get_exception(UB, ea, tenant_id=B))
        self.assertIsNotNone(self.s.get_exception(UA, ea, tenant_id=A))

    def test_resolve_cross_tenant_blocked(self):
        ea, _, _, _ = self._seed()
        self.assertFalse(self.s.resolve_exception(UB, ea, tenant_id=B))
        self.assertTrue(self.s.resolve_exception(UA, ea, tenant_id=A))

    def test_delete_pending_cross_tenant_blocked(self):
        _, _, ha, _ = self._seed()
        self.assertEqual(self.s.delete_pending_exceptions_by_history(ha, tenant_id=B), 0)
        self.assertEqual(self.s.delete_pending_exceptions_by_history(ha, tenant_id=A), 1)

    def test_whitelist_cross_tenant_blocked(self):
        self.assertTrue(self.wl.add_exception_whitelist(UA, A, "ACME", "DUP"))
        self.assertTrue(self.wl.is_exception_whitelisted(UA, A, "ACME", "DUP"))
        # B 看不到 A 的白名单 → 该规则对 B 不生效
        self.assertFalse(self.wl.is_exception_whitelisted(UB, B, "ACME", "DUP"))
        self.assertEqual(len(self.wl.list_exception_whitelist(UA, tenant_id=A)), 1)
        self.assertEqual(len(self.wl.list_exception_whitelist(UB, tenant_id=B)), 0)
        self.assertEqual(self.wl.count_whitelist_rules(UA, tenant_id=A), 1)
        self.assertEqual(self.wl.count_whitelist_rules(UB, tenant_id=B), 0)


if __name__ == "__main__":
    unittest.main()
