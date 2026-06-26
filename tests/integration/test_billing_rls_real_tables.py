# -*- coding: utf-8 -*-
"""B8 RLS wave3 3d · 真钱表端到端隔离(REFACTOR-B8)。

在真 postgres 上验钱表的租户隔离(第二道防线):
- tenant_credits / credit_transactions(tenant 维度)→ 租户 A 的余额/流水,租户 B 读不到、
  且 WITH CHECK 拦住「往别家租户塞流水」。
- ocr_cost_log(tenant_or_user)→ 真 cost.log_ocr_cost 写入后只有本租户/本人可见;
  tenant_id 为空的孤立行回退按 user 隔离。
钱路径绝不 bypass(charge.py 等),超管聚合才显式 bypass —— 本测试不碰超管路径。
CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_billing_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"

_STUBS = (
    "CREATE TABLE tenant_credits ("
    "  tenant_id UUID PRIMARY KEY, balance_thb NUMERIC(12,2) DEFAULT 0,"
    "  updated_at TIMESTAMPTZ DEFAULT NOW())",
    "CREATE TABLE credit_transactions ("
    "  id SERIAL PRIMARY KEY, tenant_id UUID NOT NULL, user_id UUID, type TEXT,"
    "  amount_thb NUMERIC(12,2), pages INT DEFAULT 0, balance_after NUMERIC(12,2),"
    "  description TEXT, created_at TIMESTAMPTZ DEFAULT NOW())",
    "CREATE TABLE monthly_page_usage ("
    "  tenant_id UUID NOT NULL, year_month TEXT NOT NULL, pages_used INT DEFAULT 0,"
    "  updated_at TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY (tenant_id, year_month))",
    "CREATE TABLE ocr_cost_log ("
    "  id BIGSERIAL PRIMARY KEY, user_id UUID NOT NULL, tenant_id UUID, history_id TEXT,"
    "  engine TEXT NOT NULL DEFAULT 'gemini', pages INT DEFAULT 1, input_tokens INT DEFAULT 0,"
    "  output_tokens INT DEFAULT 0, cost_thb NUMERIC(10,4) DEFAULT 0, elapsed_ms INT DEFAULT 0,"
    "  created_at TIMESTAMPTZ DEFAULT NOW())",
)
_TABLES = ("tenant_credits", "credit_transactions", "monthly_page_usage", "ocr_cost_log")


class BillingRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.cost import store as cost

        cls.db, cls.rls, cls.cost = db, rls, cost
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")
            for ddl in _STUBS:
                cur.execute(ddl)
            # 单一来源模板:tenant 维度 3 表 + tenant_or_user 的 ocr_cost_log
            rls.apply_tenant_rls(cur, "tenant_credits", "credit_transactions", "monthly_page_usage")
            rls.apply_tenant_or_user_rls(cur, "ocr_cost_log")
            cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {', '.join(_TABLES)} TO pearnly_app")
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            # FORCE:本地恢复库 owner 也受 policy 约束才能真测隔离(prod 靠非 owner 角色)
            for t in _TABLES:
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(f"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "TRUNCATE tenant_credits, credit_transactions, monthly_page_usage, ocr_cost_log RESTART IDENTITY"
            )

    def _seed_money(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO tenant_credits(tenant_id, balance_thb) VALUES (%s, 100),(%s, 200)",
                (A, B),
            )
            cur.execute(
                "INSERT INTO credit_transactions(tenant_id, user_id, type, amount_thb, balance_after) "
                "VALUES (%s,%s,'usage',-5,95),(%s,%s,'usage',-7,193)",
                (A, UA, B, UB),
            )

    def test_tenant_credits_cross_tenant_blocked(self):
        self._seed_money()
        with self.db.get_cursor_rls(tenant_id=A) as cur:
            cur.execute("SELECT count(*) n, COALESCE(SUM(balance_thb),0) s FROM tenant_credits")
            r = cur.fetchone()
        self.assertEqual(r["n"], 1)
        self.assertEqual(float(r["s"]), 100.0)  # 只看到自己,不会把 B 的 200 加进来

    def test_credit_transactions_cross_tenant_blocked(self):
        self._seed_money()
        with self.db.get_cursor_rls(tenant_id=B) as cur:
            cur.execute("SELECT count(*) n FROM credit_transactions")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(tenant_id="00000000-0000-0000-0000-0000000000ff") as cur:
            cur.execute("SELECT count(*) n FROM credit_transactions")
            self.assertEqual(cur.fetchone()["n"], 0)

    def test_with_check_blocks_writing_other_tenant(self):
        # 在 A 的上下文里试图往 B 塞流水 → WITH CHECK 拒(钱不能跨租户记账)。
        import psycopg2

        with self.assertRaises(psycopg2.errors.Error):
            with self.db.get_cursor_rls(tenant_id=A, commit=True) as cur:
                cur.execute(
                    "INSERT INTO credit_transactions(tenant_id, user_id, type, amount_thb, balance_after) "
                    "VALUES (%s,%s,'usage',-1,0)",
                    (B, UA),
                )

    def test_log_ocr_cost_real_fn_isolated(self):
        # 真 DAL 在 tenant+user 上下文写自己的成本行。
        self.assertTrue(self.cost.log_ocr_cost(UA, A, "h1", "gemini", 1, 0, 0, 0.5, 10))
        self.assertTrue(self.cost.log_ocr_cost(UB, B, "h2", "gemini", 1, 0, 0, 0.7, 12))
        with self.db.get_cursor_rls(tenant_id=A, user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM ocr_cost_log")
            self.assertEqual(cur.fetchone()["n"], 1)

    def test_ocr_cost_log_null_tenant_falls_back_to_user(self):
        # 孤立行 tenant_id IS NULL → 按 user 隔离(tenant_or_user 模板兜底)。
        self.assertTrue(self.cost.log_ocr_cost(UA, None, "h3", "gemini", 1, 0, 0, 0.3, 5))
        with self.db.get_cursor_rls(user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM ocr_cost_log WHERE tenant_id IS NULL")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(user_id=UB) as cur:
            cur.execute("SELECT count(*) n FROM ocr_cost_log WHERE tenant_id IS NULL")
            self.assertEqual(cur.fetchone()["n"], 0)


if __name__ == "__main__":
    unittest.main()
