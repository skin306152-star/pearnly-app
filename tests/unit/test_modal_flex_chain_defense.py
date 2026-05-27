# -*- coding: utf-8 -*-
"""
P0.4 BUG-A-T1 v118.35.0.40 · 守门测试 · modal flex-chain 防御性 min-height:0 静态契约

锁定 3 个契约:
  1. home.css .modal-body 必须含 min-height: 0(防 flex chain 不传递 · settings 同款病预防)
  2. home.css .drawer-body 必须含 min-height: 0(同上)
  3. audit doc docs/audits/2026-05-23-modal-flex-chain-audit.md 存在 · 锁住接力 agent 看
"""

import glob
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ModalFlexChainDefenseTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # REFACTOR-C2: home.css 已拆到 static/home-*.css · 读 home.css + 所有切片的并集
        # (按 link 顺序拼接 == 原始 home.css 字节级一致 · 见 BATCH_STRATEGY §13)·
        # 规则搬进切片后在并集里仍找得到 · 测试不随拆分误报。
        parts = []
        with open(os.path.join(ROOT, "home.css"), "r", encoding="utf-8") as f:
            parts.append(f.read())
        for p in sorted(glob.glob(os.path.join(ROOT, "static", "home-*.css"))):
            with open(p, "r", encoding="utf-8") as f:
                parts.append(f.read())
        cls.home_css = "\n".join(parts)

    def test_modal_body_has_min_height_zero(self):
        """P0.4 契约 · 至少 1 个 .modal-body block 含 min-height: 0
        home.css 有 2 个 .modal-body 定义(2 套 modal pattern)· 含 flex chain 的那个需要 min-height:0
        若被未来 agent 删除 · 此 test 立即 fail · 防回退
        """
        # 找所有 .modal-body { ... } block · 至少 1 个含 min-height: 0
        blocks = re.findall(r"^\.modal-body\s*\{([^}]*)\}", self.home_css, re.MULTILINE)
        self.assertGreater(len(blocks), 0, ".modal-body rule(s) not found in home.css")
        ok = any(re.search(r"min-height\s*:\s*0\s*[;}\s]", b) for b in blocks)
        self.assertTrue(
            ok,
            f".modal-body needs `min-height: 0` in ≥1 block (found {len(blocks)} blocks · "
            f"settings flex-chain bug防御 · 详见 docs/audits/2026-05-23-modal-flex-chain-audit.md)",
        )

    def test_drawer_body_has_min_height_zero(self):
        """P0.4 契约 · .drawer-body 必须含 min-height: 0(防 zoom 偏移时滚动条不触发)"""
        # .drawer-body 是单行 css · 含 inline 注释 · 用 substring match
        # 找包含 .drawer-body 的行
        for line in self.home_css.splitlines():
            stripped = line.lstrip()
            if stripped.startswith(".drawer-body"):
                self.assertRegex(
                    line,
                    r"min-height\s*:\s*0\s*[;}\s]",
                    ".drawer-body must include `min-height: 0`",
                )
                return
        self.fail(".drawer-body rule not found in home.css")

    def test_audit_doc_exists_with_required_sections(self):
        """P0.4 契约 · audit doc 存在 + 含必要段落(锁接力 agent 看)"""
        audit_path = os.path.join(ROOT, "docs", "audits", "2026-05-23-modal-flex-chain-audit.md")
        self.assertTrue(
            os.path.exists(audit_path),
            "Audit doc missing: docs/audits/2026-05-23-modal-flex-chain-audit.md",
        )
        with open(audit_path, "r", encoding="utf-8") as f:
            doc = f.read()
        # 必要段:6 个 modal 类 + 修法预案 + 接力 agent 必读
        for required in [
            ".modal",
            ".drawer",
            ".rd-modal",
            ".log-detail-box",
            ".admin-modal",
            ".add-emp-modal",
        ]:
            self.assertIn(
                required, doc, f"Audit doc must mention modal class `{required}` in the audit table"
            )
        self.assertIn("修法预案", doc, "Audit doc must include 修法预案 section for future bug")
        self.assertIn("接力 agent 必读", doc, "Audit doc must include 接力 agent 必读 section")


if __name__ == "__main__":
    unittest.main()
