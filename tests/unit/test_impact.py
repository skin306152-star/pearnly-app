#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/impact.py 规划逻辑的守门测试。

impact.py 决定一次 diff 该跑什么,所以它自己是纯函数(plan 吃显式 paths,不吃 git
状态),测试就能直接喂路径断言结果 —— 不必建 git 仓库。判据都是行为契约:

  - E2E 目标从 tests/e2e/e2e_ledger.json 的 covers 里选,`static/ai/**` 这种通配
    covers 是这张台账的既有写法,选不中 = 改了 ai 源码却没人提醒重跑验收脚本;
  - 没登记的 spec 必须变成 ledger_gaps —— 让「漏登记」像漏跑一样可见(见台账头部
    的 _why,漏登记 = 没人知道它保着什么);
  - 生产 .py 一律 full(依赖反推不出安全子集),只有 unit 目录内的测试文件才是
    targeted —— 这是 planner 的 fail-safe 设计,防止"觉得改动小"就少跑了。

所有用例都读真实台账(load_ledger),台账里 specs 的条数/名字变了就红。
"""

from __future__ import annotations

import unittest

from scripts import impact


class LedgerShape(unittest.TestCase):
    """测试依赖真实台账,先锁住它的形状,别让测试在台账悄悄改版后假绿。"""

    def setUp(self):
        self.ledger = impact.load_ledger()

    def test_ledger_has_spec_entries(self):
        self.assertGreaterEqual(len(self.ledger["specs"]), 5)

    def test_b2m1_steward_local_spec_is_declared(self):
        self.assertIn("_b2m1_steward_local.spec.js", self.ledger["specs"])


class SpecSelection(unittest.TestCase):
    """从 covers 选 E2E 目标:static/ai/** 通配必须命中台账里的 spec。"""

    def setUp(self):
        self.ledger = impact.load_ledger()

    def test_static_ai_change_selects_steward_local_spec(self):
        report = impact.plan(["static/ai/ai-steward.js"], self.ledger)
        self.assertIn("tests/e2e/_b2m1_steward_local.spec.js", report["specs"])
        self.assertIn(
            "tests/e2e/_b2m1_steward_local.spec.js",
            report["spec_command"],
        )
        self.assertIn("node scripts/_steward_chat_v2_verify.cjs", report["cjs_commands"])

    def test_static_ai_nested_change_selects_steward_local_spec(self):
        """static/ai/** 必须也吃子目录:ai 的新模块常落在 static/ai/ 下面更深。"""
        report = impact.plan(["static/ai/chat/render.js"], self.ledger)
        self.assertIn("tests/e2e/_b2m1_steward_local.spec.js", report["specs"])

    def test_unrelated_change_selects_no_steward_spec(self):
        report = impact.plan(["static/pos/pos.html"], self.ledger)
        self.assertNotIn("tests/e2e/_b2m1_steward_local.spec.js", report["specs"])


class LedgerGaps(unittest.TestCase):
    """没登记的 spec 必须浮出来 —— 漏登记要跟漏跑一样可见。"""

    def setUp(self):
        self.ledger = impact.load_ledger()

    def test_undeclared_new_spec_is_a_ledger_gap(self):
        report = impact.plan(["tests/e2e/new.spec.js"], self.ledger)
        self.assertEqual(report["ledger_gaps"], ["new.spec.js"])

    def test_declared_spec_change_has_no_gap(self):
        report = impact.plan(["tests/e2e/_b2m1_steward_local.spec.js"], self.ledger)
        self.assertEqual(report["ledger_gaps"], [])


class UnitPlan(unittest.TestCase):
    """unit 计划的三态:full / targeted / skip,是 planner 的 fail-safe 核心。"""

    def setUp(self):
        self.ledger = impact.load_ledger()

    def test_production_python_keeps_full_suite(self):
        report = impact.plan(["app/main.py"], self.ledger)
        unit = report["unit"]
        self.assertEqual(unit["mode"], "full")
        self.assertIn("run_unit_sharded", unit["command"])

    def test_unit_only_change_is_targeted(self):
        report = impact.plan(["tests/unit/test_impact.py"], self.ledger)
        unit = report["unit"]
        self.assertEqual(unit["mode"], "targeted")
        self.assertEqual(unit["command"], "python -m unittest tests.unit.test_impact")
        gates = {gate["name"] for gate in report["gates"]}
        self.assertNotIn("check_authz_coverage", gates)
        self.assertNotIn("check_e2e_stub_contracts", gates)

    def test_docs_and_css_change_skips_unit_tests(self):
        report = impact.plan(["docs/readme.md", "static/home.css"], self.ledger)
        self.assertEqual(report["unit"]["mode"], "skip")
        self.assertIsNone(report["unit"]["command"])

    def test_ledger_data_change_does_not_trigger_frontend_build(self):
        report = impact.plan(["tests/e2e/e2e_ledger.json"], self.ledger)
        gates = {gate["name"] for gate in report["gates"]}
        self.assertNotIn("build", gates)
        self.assertNotIn("check_ui_consistency", gates)
        self.assertNotIn("check_authz_coverage", gates)


if __name__ == "__main__":
    unittest.main()
