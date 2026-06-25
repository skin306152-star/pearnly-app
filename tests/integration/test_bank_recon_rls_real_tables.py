# -*- coding: utf-8 -*-
"""B8 RLS · bank_reconcile_* 真表端到端隔离(REFACTOR-B8)。

用真 ensure_bank_recon_rls() enroll(user-only + 经 tx_id 传递)+ 真 store 函数
(create_bank_recon_session / get_bank_recon_session / list_bank_recon_sessions),
在真 postgres 上验证:user u1 建的 session/transaction/candidate,user u2 一概读不到。
证 bank_reconcile_* 三表(无 tenant_id · user 维度)的 DB 级隔离真闭合。CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_bank_recon_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

U1 = "11111111-1111-1111-1111-111111111111"
U2 = "22222222-2222-2222-2222-222222222222"


class BankReconRealTableRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.recon import bank_recon_v1_store as store

        cls.db, cls.store = db, store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(
                "DROP TABLE IF EXISTS bank_reconcile_candidates, "
                "bank_reconcile_transactions, bank_reconcile_sessions CASCADE"
            )
            # 只建 store 函数用到的列(真表由 alembic 建 · 这里 stub 同名同形)
            cur.execute(
                "CREATE TABLE bank_reconcile_sessions ("
                "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id TEXT, bank_code TEXT, "
                "source_filename TEXT, source_pages INT, parse_status TEXT, match_status TEXT, "
                "account_last4 TEXT, statement_month TEXT, period_start DATE, period_end DATE, "
                "opening_balance NUMERIC, closing_balance NUMERIC, total_inflow NUMERIC, "
                "total_outflow NUMERIC, tx_count INT, matched_count INT, unmatched_count INT, "
                "parse_error TEXT, workspace_client_id INT, client_id INT, "
                "created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now())"
            )
            cur.execute(
                "CREATE TABLE bank_reconcile_transactions ("
                "id BIGSERIAL PRIMARY KEY, session_id UUID, user_id TEXT, row_no INT, "
                "tx_date DATE, value_date DATE, direction TEXT, amount NUMERIC, "
                "balance_after NUMERIC, description TEXT, counterparty TEXT, ref_no TEXT, "
                "channel TEXT, match_status TEXT DEFAULT 'unmatched')"
            )
            cur.execute(
                "CREATE TABLE bank_reconcile_candidates ("
                "id BIGSERIAL PRIMARY KEY, tx_id BIGINT, history_id UUID, score NUMERIC)"
            )

        store.ensure_bank_recon_rls()  # enroll user-only(sessions/tx)+ via-parent(candidates)
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON bank_reconcile_sessions,"
                "bank_reconcile_transactions,bank_reconcile_candidates TO pearnly_app"
            )
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            # FORCE:本地恢复库 owner 也受 policy 约束才能真测隔离(prod 靠非 owner 角色)
            for t in (
                "bank_reconcile_sessions",
                "bank_reconcile_transactions",
                "bank_reconcile_candidates",
            ):
                cur.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(
                    "DROP TABLE IF EXISTS bank_reconcile_candidates, "
                    "bank_reconcile_transactions, bank_reconcile_sessions CASCADE"
                )

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "TRUNCATE bank_reconcile_candidates, bank_reconcile_transactions, "
                "bank_reconcile_sessions RESTART IDENTITY"
            )

    def _seed_u1(self):
        sid = self.store.create_bank_recon_session(U1, "KBANK", "stmt.pdf", 2)
        self.assertIsNotNone(sid)
        # 直接 seed 一笔流水 + 候选(系统侧 bypass · 模拟解析/匹配落库)
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "INSERT INTO bank_reconcile_transactions(session_id,user_id,amount) "
                "VALUES (%s,%s,100) RETURNING id",
                (sid, U1),
            )
            tx_id = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO bank_reconcile_candidates(tx_id,score) VALUES (%s,0.9)", (tx_id,)
            )
        return sid, tx_id

    def _count(self, q, **ctx):
        with self.db.get_cursor_rls(**ctx) as cur:
            cur.execute(q)
            return cur.fetchone()["n"]

    def test_session_owner_sees_other_user_blocked(self):
        sid, _ = self._seed_u1()
        # u1 凭真 store 函数看得到自己的 session
        self.assertIsNotNone(self.store.get_bank_recon_session(U1, sid, tenant_id=None))
        self.assertEqual(len(self.store.list_bank_recon_sessions(U1, tenant_id=None)), 1)
        # u2 凭同样的 session_id 一概读不到
        self.assertIsNone(self.store.get_bank_recon_session(U2, sid, tenant_id=None))
        self.assertEqual(len(self.store.list_bank_recon_sessions(U2, tenant_id=None)), 0)

    def test_transactions_cross_user_blocked(self):
        sid, _ = self._seed_u1()
        q = "SELECT count(*) AS n FROM bank_reconcile_transactions"
        self.assertEqual(self._count(q, user_id=U1), 1)
        self.assertEqual(self._count(q, user_id=U2), 0)
        self.assertEqual(self._count(q, bypass=True), 1)

    def test_candidates_via_parent_cross_user_blocked(self):
        sid, tx_id = self._seed_u1()
        # candidate 无 user_id · 经 tx_id→transactions(user_id)传递隔离
        q = "SELECT count(*) AS n FROM bank_reconcile_candidates"
        self.assertEqual(self._count(q, user_id=U1), 1)
        self.assertEqual(self._count(q, user_id=U2), 0)
        # 点名 tx_id 也跨不过去
        self.assertEqual(
            self._count(
                f"SELECT count(*) AS n FROM bank_reconcile_candidates WHERE tx_id={tx_id}",
                user_id=U2,
            ),
            0,
        )

    def test_other_user_cannot_insert_candidate_for_foreign_tx(self):
        _, tx_id = self._seed_u1()
        # u2 往 u1 的 tx 下塞候选 → WITH CHECK 经父查询拒(看不到父 tx)
        with self.assertRaises(Exception):
            with self.db.get_cursor_rls(user_id=U2, commit=True) as cur:
                cur.execute(
                    "INSERT INTO bank_reconcile_candidates(tx_id,score) VALUES (%s,0.5)", (tx_id,)
                )


if __name__ == "__main__":
    unittest.main()
