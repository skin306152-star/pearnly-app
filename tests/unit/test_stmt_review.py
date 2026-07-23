# -*- coding: utf-8 -*-
"""ADR-006 S8 · stmt_review 基础层守门测试(纯函数 · 不依赖部署/网络)。"""

import unittest
from types import SimpleNamespace

from services.importer import stmt_review as sr


def _row(date=None, desc="x", wd=0.0, dep=0.0, bal=0.0, conf="high"):
    return SimpleNamespace(
        date=date,
        description=desc,
        withdrawal=wd,
        deposit=dep,
        balance=bal,
        confidence=conf,
        balance_ok=None,
        direction_autocorrected=False,
        amount_autocorrected=False,
        account_no="",
    )


class NeedsReviewTests(unittest.TestCase):
    def test_clean_ocr_no_review(self):
        pr = {"ok": True, "rows": [_row()], "low_conf_count": 0, "completeness": {"ok": True}}
        self.assertFalse(sr.needs_review(pr))

    def test_low_conf_triggers(self):
        pr = {"ok": True, "rows": [_row()], "low_conf_count": 1, "completeness": {"ok": True}}
        self.assertTrue(sr.needs_review(pr))

    def test_incomplete_triggers(self):
        pr = {
            "ok": True,
            "rows": [_row()],
            "low_conf_count": 0,
            "completeness": {"ok": False, "issues": [{"type": "credit_count_mismatch"}]},
        }
        self.assertTrue(sr.needs_review(pr))

    def test_failed_or_empty_no_review(self):
        self.assertFalse(sr.needs_review({"ok": False, "rows": [_row()]}))
        self.assertFalse(sr.needs_review({"ok": True, "rows": [], "low_conf_count": 5}))

    def test_machine_rewritten_amount_triggers(self):
        """A-4:金额被余额链反推改写过 → 必须弹核对关。

        改写把 balance_ok 翻 True、该行退出 balance_warn 口径,此前整份账单因此判「不用人看」——
        可这笔数正是销项倒推与逐笔对账的基数。信心高、完整性也过,唯一异常就是机器改过钱。
        """
        pr = {
            "ok": True,
            "rows": [_row()],
            "low_conf_count": 0,
            "amount_fixed_count": 1,
            "completeness": {"ok": True},
        }
        self.assertTrue(sr.needs_review(pr))

    def test_zero_rewrites_stays_frictionless(self):
        # 没改过就不该多一道关(零摩擦不能被这条新判据破坏)。
        pr = {
            "ok": True,
            "rows": [_row()],
            "low_conf_count": 0,
            "amount_fixed_count": 0,
            "completeness": {"ok": True},
        }
        self.assertFalse(sr.needs_review(pr))


class SerializeTests(unittest.TestCase):
    def test_rows_to_review_shape_and_idx(self):
        import datetime as dt

        rows = [
            _row(date=dt.date(2026, 5, 1), desc="ฝากเงิน", dep=100.0, bal=1100.0),
            _row(date=dt.date(2026, 5, 2), desc="ถอน", wd=50.0, bal=1050.0, conf="low"),
        ]
        rv = sr.statement_rows_to_review(rows)
        self.assertEqual([r["idx"] for r in rv], [0, 1])
        self.assertEqual(rv[0]["date"], "2026-05-01")
        self.assertEqual(rv[0]["deposit"], 100.0)
        self.assertEqual(rv[1]["confidence"], "low")

    def test_roundtrip_to_statement_rows(self):
        rv = [
            {
                "idx": 0,
                "date": "2026-05-01",
                "description": "ฝาก",
                "withdrawal": 0,
                "deposit": 100.0,
                "balance": 1100.0,
                "confidence": "high",
                "account_no": "",
            }
        ]
        srows = sr.review_rows_to_statement_rows(rv, source_file="f.pdf")
        self.assertEqual(len(srows), 1)
        self.assertEqual(srows[0].deposit, 100.0)
        self.assertEqual(srows[0].balance, 1100.0)
        self.assertEqual(srows[0].date.isoformat(), "2026-05-01")
        self.assertTrue(srows[0].balance_ok)  # 用户核对后标已确认


class BalanceChainTests(unittest.TestCase):
    def test_correct_chain_all_ok(self):
        rv = [
            {"idx": 0, "deposit": 100.0, "withdrawal": 0, "balance": 1100.0},
            {"idx": 1, "deposit": 0, "withdrawal": 50.0, "balance": 1050.0},
        ]
        chain = sr.recompute_balance_chain(rv, opening=1000.0)
        self.assertTrue(all(c["ok"] for c in chain))
        self.assertTrue(sr.balance_chain_ok(rv, 1000.0))

    def test_wrong_balance_flagged_no_cascade(self):
        # 第 1 行余额读错(应 1100 写成 1200)· 只该这行标错 · 第 2 行用印刷余额承前不连累
        rv = [
            {"idx": 0, "deposit": 100.0, "withdrawal": 0, "balance": 1200.0},  # 错
            {"idx": 1, "deposit": 0, "withdrawal": 50.0, "balance": 1150.0},  # 1200-50 自洽
        ]
        chain = sr.recompute_balance_chain(rv, opening=1000.0)
        self.assertFalse(chain[0]["ok"])
        self.assertEqual(chain[0]["diff"], 100.0)
        self.assertTrue(chain[1]["ok"])  # 承前用 actual=1200 · 不级联全红
        self.assertFalse(sr.balance_chain_ok(rv, 1000.0))


class ReviewPayloadTests(unittest.TestCase):
    def _pdf_res(self, low=1, comp_ok=True, opening=1000.0):
        return {
            "ok": True,
            "opening": opening,
            "closing": 1050.0,
            "low_conf_count": low,
            "completeness": {
                "ok": comp_ok,
                "issues": (
                    [] if comp_ok else [{"type": "credit_count_mismatch", "count": 4, "printed": 5}]
                ),
            },
            "rows": [_row(desc="ฝาก", dep=100.0, bal=1100.0, conf="low" if low else "high")],
        }

    def test_pdf_low_conf_builds_payload(self):
        p = sr.build_bank_review_payload([self._pdf_res(low=1)], ["scan.pdf"])
        self.assertIsNotNone(p)
        self.assertEqual(p["kind"], "bank_stmt_rows")
        self.assertEqual(p["files"], ["scan.pdf"])
        self.assertEqual(p["opening"], 1000.0)
        self.assertEqual(p["row_count"], 1)

    def test_excel_never_reviewed_here(self):
        # 干净/低信心都一样:Excel 不归 S8 核对(走 S1–S7)
        self.assertIsNone(sr.build_bank_review_payload([self._pdf_res(low=5)], ["book.xlsx"]))

    def test_clean_pdf_no_payload(self):
        self.assertIsNone(
            sr.build_bank_review_payload([self._pdf_res(low=0, comp_ok=True)], ["clean.pdf"])
        )

    def test_rewritten_amount_alone_builds_payload_and_counts(self):
        """A-4:整份账单信心高、完整性过,唯一异常是机器改过一行金额 → 也要进核对面板。"""
        res = self._pdf_res(low=0, comp_ok=True)
        res["amount_fixed_count"] = 1
        res["rows"][0].amount_autocorrected = True
        p = sr.build_bank_review_payload([res], ["scan.pdf"])
        self.assertIsNotNone(p)
        self.assertEqual(p["amount_fixed_count"], 1)
        # 改写标记必须逐行透出,面板才指得到是哪一行被改的。
        self.assertTrue(p["rows"][0]["amount_autocorrected"])

    def test_incomplete_pdf_carries_issues(self):
        p = sr.build_bank_review_payload([self._pdf_res(low=0, comp_ok=False)], ["scan.pdf"])
        self.assertIsNotNone(p)
        self.assertEqual(p["completeness_issues"][0]["type"], "credit_count_mismatch")
        self.assertEqual(p["completeness_issues"][0]["file"], "scan.pdf")

    def test_multifile_global_idx(self):
        p = sr.build_bank_review_payload(
            [self._pdf_res(low=1), self._pdf_res(low=1)], ["a.pdf", "b.pdf"]
        )
        self.assertEqual([r["idx"] for r in p["rows"]], [0, 1])
        self.assertEqual([r["source_file"] for r in p["rows"]], ["a.pdf", "b.pdf"])


if __name__ == "__main__":
    unittest.main()
