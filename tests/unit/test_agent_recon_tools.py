# -*- coding: utf-8 -*-
"""对账只读工具层(services/agent/recon_tools)· 方案一(bank 明细钻取)契约。

铁三条:① 数字全来自 store 结果,明细截 _DETAIL_CAP 并如实报 omitted;
② keyword 没中/没给 → 最新一条,零任务诚实 hint;③ income/tax 未通电 → not_available_yet。
"""

import unittest
from unittest.mock import patch

from services.agent import recon_tools as rt
from services.agent.contracts import AgentContext

_CTX = AgentContext(user={"id": "u-1", "plan": "credits"}, tenant_id="t-1")

_TASK = {
    "id": 7,
    "bank_code": "BAY",
    "gl_account": "1010",
    "matched_count": 12,
    "unmatched_gl": 1,
    "unmatched_stmt": 2,
    "stmt_opening": "1000.00",
    "stmt_closing": "900.00",
    "gl_opening": "1000.00",
    "gl_closing": "880.00",
    "formula_diff": "-20.00",
    "status": "done",
    "created_at": "2026-07-01 10:00:00",
    "stmt_files": ["bay_jun.pdf"],
    "gl_files": ["gl_jun.xlsx"],
}


def _row(status, **kw):
    base = {
        "match_status": status,
        "stmt_date": "2026-06-05",
        "gl_date": "2026-06-05",
        "stmt_desc": "โอนเข้า",
        "gl_desc": "รับชำระ",
        "stmt_withdrawal": None,
        "stmt_deposit": "500.00",
        "gl_debit": "500.00",
        "gl_credit": None,
    }
    base.update(kw)
    return base


class TestDetail(unittest.TestCase):
    def _run(self, rows, *, tasks=None, kind=None, keyword=None):
        with (
            patch(
                "services.recon.bank_recon_v2_store.list_bank_recon_v2_tasks",
                return_value=_TASK if tasks is None else tasks,
            ) as ls,
            patch(
                "services.recon.bank_recon_v2_store.get_bank_recon_v2_task",
                return_value={**_TASK, "detail_json": rows},
            ),
        ):
            if tasks is None:
                ls.return_value = [_TASK]
            return rt.detail(_CTX, kind=kind, keyword=keyword)

    def test_unmatched_only_and_capped(self):
        rows = [_row("matched")] * 3 + [_row("stmt_deposit_only")] * 10 + [_row("gl_debit_only")]
        r = self._run(rows)
        self.assertTrue(r.ok)
        self.assertEqual(len(r.data["unmatched"]), rt._DETAIL_CAP)
        self.assertEqual(r.data["omitted"], 11 - rt._DETAIL_CAP)  # 如实报截断
        self.assertEqual(r.data["task"]["formula_diff"], "-20.00")
        sides = {u["side"] for u in r.data["unmatched"]}
        self.assertEqual(sides, {"BANK", "GL"} & sides)

    def test_side_and_amount_mapping(self):
        r = self._run([_row("stmt_deposit_only"), _row("gl_debit_only")])
        bank = next(u for u in r.data["unmatched"] if u["side"] == "BANK")
        gl = next(u for u in r.data["unmatched"] if u["side"] == "GL")
        self.assertEqual(bank["amount"], "500.00")  # 对账单侧取 deposit/withdrawal
        self.assertEqual(gl["amount"], "500.00")  # GL 侧取 debit/credit
        self.assertIn("agent.ok.recon_detail", r.receipt)

    def test_keyword_picks_matching_task(self):
        other = {**_TASK, "id": 8, "bank_code": "KTB", "stmt_files": ["ktb.pdf"]}
        r = self._run([_row("gl_debit_only")], tasks=[other, _TASK], keyword="BAY")
        self.assertEqual(r.data["task"]["bank"], "BAY")
        # 没中 → 最新一条(不猜不反问,任务按时间倒序)
        r2 = self._run([_row("gl_debit_only")], tasks=[other, _TASK], keyword="SCB")
        self.assertEqual(r2.data["task"]["bank"], "KTB")

    def test_no_tasks_is_honest(self):
        r = self._run([], tasks=[])
        self.assertTrue(r.ok)
        self.assertIn("hint", r.data)

    def test_income_tax_not_available_yet(self):
        for k in ("income", "tax", "vat", "gl_vat"):
            r = rt.detail(_CTX, kind=k)
            self.assertFalse(r.ok, k)
            self.assertEqual(r.error_code, "not_available_yet")

    def test_kind_default_and_aliases(self):
        self.assertEqual(rt.normalize_kind(None), "bank")
        self.assertEqual(rt.normalize_kind("BANK "), "bank")
        self.assertEqual(rt.normalize_kind("อะไรก็ไม่รู้"), "bank")
        self.assertEqual(rt.normalize_kind("sales_vat"), "tax")

    def test_detail_json_string_is_parsed(self):
        import json

        r = self._run(json.dumps([_row("gl_debit_only")]))
        self.assertEqual(len(r.data["unmatched"]), 1)


class TestOverviewDelegation(unittest.TestCase):
    def test_executor_delegates(self):
        from services.agent.executor import AgentToolset

        with patch(
            "services.recon.bank_recon_v2_store.list_bank_recon_v2_tasks", return_value=[_TASK]
        ):
            r = AgentToolset().get_recon_overview(_CTX)
        self.assertTrue(r.ok)
        self.assertEqual(r.data["recent"][0]["bank"], "BAY")
        self.assertIn("agent.ok.recon", r.receipt)


class TestObservationAndFallback(unittest.TestCase):
    """真机雷(2026-07-02):observe 漏 recon 分支 → 模型观测只剩 {"ok":True} 零数字
    只能空话/crash。锁:观测直通执行器产出;成文兜底给诚实计数。"""

    def test_observe_passes_recon_data_through(self):
        from services.agent import observe
        from services.agent.contracts import ToolResult

        detail = ToolResult(ok=True, data={"task": {"matched": 9}, "unmatched": [{"side": "GL"}]})
        out = observe.payload("recon_detail", detail)
        self.assertEqual(out["task"]["matched"], 9)
        self.assertEqual(len(out["unmatched"]), 1)
        ov = ToolResult(ok=True, data={"count": 1, "recent": [{"matched": 5}]})
        self.assertEqual(observe.payload("recon_overview", ov)["recent"][0]["matched"], 5)

    def test_grounded_fallback_covers_recon(self):
        from services.agent import fallbacks

        obs = [
            {
                "tool": "recon_detail",
                "ok": True,
                "task": {"matched": 9, "unmatched_gl": 5, "unmatched_stmt": 2},
            }
        ]
        self.assertIn("7", fallbacks.grounded_fallback(obs, "zh"))
        obs2 = [{"tool": "recon_overview", "ok": True, "recent": []}]
        self.assertIn("银行对账", fallbacks.grounded_fallback(obs2, "zh"))  # 空数据诚实指路


if __name__ == "__main__":
    unittest.main()
