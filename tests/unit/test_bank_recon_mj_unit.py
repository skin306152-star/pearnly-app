# -*- coding: utf-8 -*-
"""银行对账 + 手工凭证 逻辑闸(无 DB · FakeCursor 脚本化):导入方向规范化 / 三余额数学 /
组合差额拦截 / 收割阈值 / 模板校验 / choice 校验 / scope_key 确定性。

真库链路(导入→匹配→学习→撤销→隔离)在 tests/e2e/_bank_recon_mj_e2e.py。
"""

import unittest
from decimal import Decimal

from core.pos_api import PosError
from services.accounting import bank_candidates, bank_match, bank_recon
from services.accounting import templates as jv_templates
from services.accounting import review as acct_review


class FakeCursor:
    """脚本化游标:fetchone/fetchall 按入队顺序返回;记录 executed 供断言。"""

    def __init__(self, fetchone=None, fetchall=None):
        self._one = list(fetchone or [])
        self._all = list(fetchall or [])
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._one.pop(0) if self._one else None

    def fetchall(self):
        return self._all.pop(0) if self._all else []


class ScopeKeyTests(unittest.TestCase):
    def test_deterministic_and_shaped(self):
        a = bank_candidates.bank_scope_key("  TRANSFER FROM Acme  ")
        b = bank_candidates.bank_scope_key("transfer from acme")
        self.assertEqual(a, b)  # trim + lower 归一
        self.assertTrue(a.startswith("bank_desc:"))
        self.assertEqual(len(a.split(":")[1]), 16)

    def test_empty_description_stable(self):
        self.assertTrue(bank_candidates.bank_scope_key(None).startswith("bank_desc:"))


class InsertLinesTests(unittest.TestCase):
    def test_direction_normalized_and_skips(self):
        cur = FakeCursor(fetchone=[{"id": "a"}, {"id": "b"}])  # 两行插入成功
        txs = [
            {"tx_date": "2026-06-01", "amount": 100.0, "direction": "IN", "description": "x"},
            {"tx_date": "2026-06-02", "amount": -50.0, "direction": "OUT", "description": "y"},
            {
                "tx_date": "2026-06-03",
                "amount": 10.0,
                "direction": "",
                "description": "z",
            },  # 无方向
        ]
        res = bank_recon.insert_lines(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            bank_account_id="ba",
            batch_id="b",
            sha256="s",
            transactions=txs,
        )
        self.assertEqual(res, {"inserted": 2, "skipped": 1})
        inserts = [e for e in cur.executed if "INSERT INTO acct_bank_lines" in e[0]]
        self.assertEqual(len(inserts), 2)  # 第三行无方向 → 不发 SQL
        self.assertEqual(inserts[0][1][5], "in")  # IN→in
        self.assertEqual(inserts[1][1][5], "out")  # OUT→out
        self.assertEqual(inserts[1][1][4], Decimal("50.00"))  # 金额取绝对值

    def test_conflict_counts_as_skipped(self):
        cur = FakeCursor(fetchone=[None])  # ON CONFLICT DO NOTHING → 无返回
        res = bank_recon.insert_lines(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            bank_account_id="ba",
            batch_id="b",
            sha256="s",
            transactions=[{"tx_date": "2026-06-01", "amount": 1, "direction": "IN"}],
        )
        self.assertEqual(res, {"inserted": 0, "skipped": 1})


class SummaryTests(unittest.TestCase):
    def test_three_balances_and_progress(self):
        cur = FakeCursor(
            fetchone=[
                {"bank_balance": Decimal("1000")},  # 银行 closing
                {"book_balance": Decimal("700")},  # 账面
                {  # 计数 + 未对净额
                    "unmatched_net": Decimal("300"),
                    "total_count": 4,
                    "matched_count": 3,
                    "unmatched_count": 1,
                },
            ],
            fetchall=[[{"coa_account_id": "c1"}]],  # _bank_coa_account_ids
        )
        s = bank_recon.summary(cur, tenant_id="t", workspace_client_id=1)
        self.assertEqual(s["bank_balance"], Decimal("1000"))
        self.assertEqual(s["book_balance"], Decimal("700"))
        self.assertEqual(s["difference"], Decimal("300"))
        self.assertEqual(s["unmatched_net"], Decimal("300"))
        self.assertEqual(s["progress"], 0.75)
        self.assertFalse(s["done"])

    def test_done_when_all_matched(self):
        cur = FakeCursor(
            fetchone=[
                {"bank_balance": Decimal("0")},
                {  # 无 coa → book 查询跳过,直接计数
                    "unmatched_net": Decimal("0"),
                    "total_count": 2,
                    "matched_count": 2,
                    "unmatched_count": 0,
                },
            ],
            fetchall=[[]],  # 无银行 COA
        )
        s = bank_recon.summary(cur, tenant_id="t", workspace_client_id=1)
        self.assertTrue(s["done"])
        self.assertEqual(s["progress"], 1.0)


class ComboMismatchTests(unittest.TestCase):
    def test_sum_must_equal_line_amount(self):
        cur = FakeCursor(
            fetchall=[[{"id": "d1", "outstanding": Decimal("60"), "paid_amount": Decimal("0")}]]
        )
        line = {"id": "L", "direction": "in", "amount": Decimal("100"), "bank_account_id": "ba"}
        with self.assertRaises(PosError) as ctx:
            bank_match._match_combo(
                cur,
                tenant_id="t",
                workspace_client_id=1,
                line=line,
                doc_ids=["d1"],
                created_by=None,
            )
        self.assertEqual(ctx.exception.code, "acct.bank.combo_mismatch")

    def test_missing_doc_rejected(self):
        cur = FakeCursor(fetchall=[[]])  # 一个都没查到
        line = {"id": "L", "direction": "out", "amount": Decimal("100"), "bank_account_id": "ba"}
        with self.assertRaises(PosError) as ctx:
            bank_match._match_combo(
                cur,
                tenant_id="t",
                workspace_client_id=1,
                line=line,
                doc_ids=["d1"],
                created_by=None,
            )
        self.assertEqual(ctx.exception.code, "acct.unexpected")

    def test_partially_paid_doc_rejected(self):
        # 防撤销时毁既有部分付款:已有 paid_amount>0 的单不可组合
        cur = FakeCursor(
            fetchall=[[{"id": "d1", "outstanding": Decimal("100"), "paid_amount": Decimal("40")}]]
        )
        line = {"id": "L", "direction": "in", "amount": Decimal("100"), "bank_account_id": "ba"}
        with self.assertRaises(PosError) as ctx:
            bank_match._match_combo(
                cur,
                tenant_id="t",
                workspace_client_id=1,
                line=line,
                doc_ids=["d1"],
                created_by=None,
            )
        self.assertEqual(ctx.exception.detail, "doc_already_paid")


class HarvestTests(unittest.TestCase):
    def test_empty_returns_empty(self):
        self.assertEqual(
            bank_match.harvest(FakeCursor(), tenant_id="t", workspace_client_id=1, line_ids=[]), []
        )


class TemplateValidationTests(unittest.TestCase):
    def test_invalid_drcr_rejected(self):
        with self.assertRaises(PosError) as ctx:
            jv_templates._normalize_lines(
                FakeCursor(),
                tenant_id="t",
                workspace_client_id=1,
                lines=[{"account_id": "a", "dr_cr": "bad"}],
            )
        self.assertEqual(ctx.exception.code, "acct.unexpected")

    def test_empty_lines_rejected(self):
        with self.assertRaises(PosError):
            jv_templates._normalize_lines(
                FakeCursor(), tenant_id="t", workspace_client_id=1, lines=[]
            )

    def test_valid_line_normalized(self):
        cur = FakeCursor(fetchone=[{"id": "a", "code": "1020"}])  # get_account 命中
        out = jv_templates._normalize_lines(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            lines=[{"account_id": "a", "dr_cr": "debit"}],
        )
        self.assertEqual(out, [{"account_id": "a", "dr_cr": "debit", "memo": None}])


class ReviewChoiceTests(unittest.TestCase):
    def test_invalid_choice_rejected_before_db(self):
        # choice 校验在取凭证前 → FakeCursor 不被触达
        with self.assertRaises(PosError) as ctx:
            acct_review.review_voucher(
                FakeCursor(),
                tenant_id="t",
                workspace_client_id=1,
                voucher_id="v",
                choice="bogus",
            )
        self.assertEqual(ctx.exception.code, "acct.unexpected")
        self.assertIn(ctx.exception.detail, ("invalid_choice",))


class ManualDraftTests(unittest.TestCase):
    def test_draft_flag_threads_to_pending(self):
        # create_manual_voucher 的 draft 分支:借 settings 关闭期校验后落 pending_review
        import inspect

        src = inspect.getsource(
            __import__(
                "services.accounting.posting", fromlist=["create_manual_voucher"]
            ).create_manual_voucher
        )
        self.assertIn('"pending_review" if draft else "posted"', src)
        self.assertIn("_assert_period_open", src)


if __name__ == "__main__":
    unittest.main()
