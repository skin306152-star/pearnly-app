# -*- coding: utf-8 -*-
"""
P0.3 BUG-B-T3 v118.35.0.39 · 守门测试 · 前端 _brv2RenderAnchorAudit 静态契约

home.js 是 1.3MB IIFE 巨石 · 没法跑 jsdom 单测 · 用静态文本契约锁:
  1. _brv2RenderAnchorAudit 函数定义存在 + renderResults 调用了它
  2. 5 个新 i18n key 在 4 语字典里都存在(zh/en/th/ja)
  3. /bank-v2/{task_id} 路由响应保持返回完整 summary(_anchor_overrides 字段不被过滤)
"""

import glob
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Brv2AnchorAuditStaticContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # REFACTOR-C1(2026-05-27 R7)· bank-recon-v2 已从 home.js 抽到 src/home/bank-recon-v2.js
        # (含 _brv2RenderAnchorAudit 定义 + 调用)· 前端静态契约改读「home.js + src/home/*.js」并集
        # (拼接 == 原巨石全文 · 拆分后仍能找到搬走的函数)。
        parts = []
        # REFACTOR-C1-home-batch9g2 · home.js 巨石已删 · 内容全在 src/home/*.js · 读取改可选
        _home = os.path.join(ROOT, "home.js")
        if os.path.exists(_home):
            with open(_home, "r", encoding="utf-8") as f:
                parts.append(f.read())
        for p in sorted(glob.glob(os.path.join(ROOT, "src", "home", "*.js"))):
            with open(p, "r", encoding="utf-8") as f:
                parts.append(f.read())
        cls.home_js = "\n".join(parts)
        # REFACTOR-WB-modularize · recon_routes.py 2000 行已拆 · bank-v2 handler 搬到
        # recon_routes_bankv2*.py · 静态契约改读这些文件的并集(拼接 == 原全文 · 仍能找到搬走的 handler)
        _recon_parts = []
        for _rp in ("recon_routes.py", "recon_routes_bankv2.py", "recon_routes_bankv2_run.py"):
            _rpath = os.path.join(ROOT, "routes", _rp)
            if os.path.exists(_rpath):
                with open(_rpath, "r", encoding="utf-8") as f:
                    _recon_parts.append(f.read())
        cls.recon_py = "\n".join(_recon_parts)
        # REFACTOR-C1(2026-05-25)· I18N 4 语字典已从 home.js 抽到 static/i18n-data.js ·
        # i18n key 完整性校验改读这里(回退 home.js 兼容老结构 / 万一回滚)
        _i18n_path = os.path.join(ROOT, "static", "i18n-data.js")
        if not os.path.exists(_i18n_path):
            _i18n_path = os.path.join(ROOT, "home.js")
        with open(_i18n_path, "r", encoding="utf-8") as f:
            cls.i18n_data = f.read()

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
            # 4 语字典定义在 static/i18n-data.js(每语言各 1 次 = 4 次)· 见 setUpClass
            occurrences = self.i18n_data.count("'" + k + "'")
            self.assertGreaterEqual(
                occurrences,
                4,
                f"i18n key '{k}' should appear ≥4 times (one per lang dict in i18n-data.js), got {occurrences}",
            )

    def test_get_task_route_returns_full_summary_with_underscore_fields(self):
        """P0.3 契约 · /bank-v2/{task_id} 必须返回完整 summary(含 _anchor_overrides 等 _-prefix 字段)
        防接力 agent 不小心改成 pydantic schema 把 _anchor_overrides 过滤掉
        """
        # 找 bank_v2_get_task 函数体
        m = re.search(
            r"async def bank_v2_get_task\(.*?\n(?=\s*@(?:router|bankv2_router|bankv2_run_router)|\Z)",
            self.recon_py,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "bank_v2_get_task function not found in recon_routes.py")
        body = m.group(0)
        # 必须 return 完整 summary(不经 pydantic 过滤掉 _anchor_overrides)。
        # BUG-FIX-RECON-ASYNC #16 起 · summary 先 _safe_json 成 var 再原样返回(并顺带从中
        # 还原顶层 stats/parse_info/warnings)· 这里校验「全量解析 + 原样返回」两点都在。
        self.assertIn(
            'summary = _safe_json(task.get("summary_json"))',
            body,
            "bank_v2_get_task must parse the full summary_json (not filtered through pydantic) — "
            "P0.3 anchor audit panel depends on summary._anchor_overrides",
        )
        self.assertIn(
            '"summary": summary',
            body,
            "bank_v2_get_task must return the full summary unchanged (not a filtered subset)",
        )

    def test_get_export_route_forwards_anchor_overrides(self):
        """P0.3+P0.2 契约 · /export 必须从 summary_raw 拿 _anchor_overrides 传给 export_bank_recon_excel"""
        m = re.search(
            r"async def bank_v2_export\(.*?\n(?=\s*@(?:router|bankv2_router|bankv2_run_router)|\Z)",
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
