# -*- coding: utf-8 -*-
"""
P0.3 BUG-B-T3 v118.35.0.39 · 守门测试 · 前端 _brv2RenderAnchorAudit 静态契约

home.js 是 1.3MB IIFE 巨石 · 没法跑 jsdom 单测 · 用静态文本契约锁:
  1. _brv2RenderAnchorAudit 函数定义存在 + renderResults 调用了它
  2. 5 个新 i18n key 在 4 语字典里都存在(zh/en/th/ja)
  3. /bank-v2/{task_id} 路由响应保持返回完整 summary(_anchor_overrides 字段不被过滤)
"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Brv2AnchorAuditStaticContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "home.js"), "r", encoding="utf-8") as f:
            cls.home_js = f.read()
        with open(os.path.join(ROOT, "recon_routes.py"), "r", encoding="utf-8") as f:
            cls.recon_py = f.read()

    def test_brv2_render_anchor_audit_defined_and_called(self):
        """P0.3 契约 · _brv2RenderAnchorAudit 必须定义 + renderResults 必须调用"""
        # 定义存在
        self.assertIn(
            "function _brv2RenderAnchorAudit",
            self.home_js,
            "_brv2RenderAnchorAudit function missing in home.js",
        )
        # _brv2RenderAnchorAudit(summary) 至少出现 2 次:
        #   1 次是 'function _brv2RenderAnchorAudit(summary) {' 定义
        #   1 次(或更多)是 renderResults 内调用
        occurrences = self.home_js.count("_brv2RenderAnchorAudit(summary)")
        self.assertGreaterEqual(
            occurrences,
            2,
            f"_brv2RenderAnchorAudit(summary) should appear ≥2 times (1 def + ≥1 call), got {occurrences}",
        )
        # 找非 function-def 的调用 · 邻近必须有 showResultSections(确认在 renderResults 内)
        for m in re.finditer(r"_brv2RenderAnchorAudit\(summary\)", self.home_js):
            idx = m.start()
            # 前 30 字符不是 'function ' 前缀 · 才是真调用
            prefix = self.home_js[max(0, idx - 30) : idx]
            if "function " in prefix:
                continue
            nearby = self.home_js[max(0, idx - 800) : idx + 200]
            self.assertIn(
                "showResultSections",
                nearby,
                "_brv2RenderAnchorAudit call should be near showResultSections (inside renderResults)",
            )
            return
        self.fail("No non-definition call site found for _brv2RenderAnchorAudit(summary)")

    def test_anchor_audit_i18n_keys_4_lang_complete(self):
        """P0.3 契约 · 5 个新 i18n key 在 4 语字典里都存在"""
        keys = [
            "brv2-anchor-audit-title",
            "brv2-anchor-audit-col-field",
            "brv2-anchor-audit-col-ocr",
            "brv2-anchor-audit-col-user",
            "brv2-anchor-audit-col-diff",
        ]
        for k in keys:
            occurrences = self.home_js.count("'" + k + "'")
            # 至少 4 次(每语言字典各 1 次)· P0.3 helper 引用是 'brv2-anchor-audit-title' 字符串 not key def · 也算
            self.assertGreaterEqual(
                occurrences,
                4,
                f"i18n key '{k}' should appear ≥4 times (one per lang dict), got {occurrences}",
            )

    def test_get_task_route_returns_full_summary_with_underscore_fields(self):
        """P0.3 契约 · /bank-v2/{task_id} 必须返回完整 summary(含 _anchor_overrides 等 _-prefix 字段)
        防接力 agent 不小心改成 pydantic schema 把 _anchor_overrides 过滤掉
        """
        # 找 bank_v2_get_task 函数体
        m = re.search(
            r"async def bank_v2_get_task\(.*?\n(?=\s*@router|\Z)",
            self.recon_py,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "bank_v2_get_task function not found in recon_routes.py")
        body = m.group(0)
        # 必须 return 含 summary 字段(_safe_json + 完整 task summary_json)
        self.assertIn(
            '"summary": _safe_json(task.get("summary_json"))',
            body,
            "bank_v2_get_task must return full summary_json (not filtered through pydantic) — "
            "P0.3 anchor audit panel depends on summary._anchor_overrides",
        )

    def test_get_export_route_forwards_anchor_overrides(self):
        """P0.3+P0.2 契约 · /export 必须从 summary_raw 拿 _anchor_overrides 传给 export_bank_recon_excel"""
        m = re.search(
            r"async def bank_v2_export\(.*?\n(?=\s*@router|\Z)",
            self.recon_py,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "bank_v2_export function not found")
        body = m.group(0)
        self.assertIn(
            'summary_raw.get("_anchor_overrides")',
            body,
            "bank_v2_export must extract _anchor_overrides from summary_raw",
        )
        self.assertIn(
            "anchor_overrides=",
            body,
            "bank_v2_export must pass anchor_overrides= to export_bank_recon_excel",
        )


if __name__ == "__main__":
    unittest.main()
