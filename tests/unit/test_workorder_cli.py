# -*- coding: utf-8 -*-
"""工单 CLI 输出渲染测试(scripts/run_workorder.py · _format_outcome 三态)。

守的是一条曾经会说谎的路径:引擎停机时 RunOutcome.status 恒为工单库状态 'stuck',
needs 与 stuck 无从区分——渲染必须改看 out.result.status,否则缺料被打成卡点、missing
清单还打不出来。这里脱离 DB/引擎,直接对渲染纯函数断言 completed / needs / stuck 三态。
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from services.workorder import engine
from services.workorder.engine import RunOutcome, StepResult

_MOD = Path(__file__).resolve().parents[2] / "scripts" / "run_workorder.py"
_spec = importlib.util.spec_from_file_location("run_workorder", _MOD)
cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cli)


class FormatOutcomeTests(unittest.TestCase):
    def test_completed_lists_deliverables_and_exits_zero(self):
        out = RunOutcome(status=engine.TERMINAL_STATUS, completed=True)
        lines, code = cli._format_outcome(out, {"pp30_draft": "/out/pp30.xlsx"})
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], "completed · 工单落 review")
        self.assertIn("  [pp30_draft] /out/pp30.xlsx", lines)

    def test_needs_labels_needs_and_lists_missing(self):
        # 停机语义在 result.status(needs);工单库状态 out.status 是 'stuck'——不能拿它区分。
        out = RunOutcome(
            status="stuck",
            completed=False,
            stopped_at="reconcile",
            result=StepResult.needs(["sales_summary"]),
        )
        lines, code = cli._format_outcome(out, None)
        self.assertEqual(code, 2)
        self.assertEqual(lines[0], "stopped at reconcile (needs):")
        self.assertEqual(lines[1:], ["  - sales_summary"])

    def test_stuck_labels_stuck_and_lists_reasons(self):
        out = RunOutcome(
            status="stuck",
            completed=False,
            stopped_at="reconcile",
            result=StepResult.stuck(["amount_math_fail", "无人工裁决"]),
        )
        lines, code = cli._format_outcome(out, None)
        self.assertEqual(code, 2)
        self.assertEqual(lines[0], "stopped at reconcile (stuck):")
        self.assertEqual(lines[1:], ["  - amount_math_fail", "  - 无人工裁决"])


if __name__ == "__main__":
    unittest.main()
