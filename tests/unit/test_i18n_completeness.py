#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_i18n_completeness.py · v118.34.34 (Zihao 2026-05-19 拍板)

守门 · TECH_DEBT.md P0 #2 · home.js i18n 字典完整性 gate.

每个新加的 'foo-bar' i18n key 必须在 zh / en / th / ja 4 个语言块都补 ·
否则 pytest fail → CI 阻塞 PR · 防止 raw key 上线给非中文用户看见.

跑法:
  pytest tests/unit/test_i18n_completeness.py -v

跑出来失败 · 看错误信息里列出的缺失 key · 去 home.js 的对应语言块补上即可.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


from check_i18n import diff_keysets, parse_i18n_blocks  # noqa: E402

HOME_JS = PROJECT_ROOT / "home.js"


class I18nDictCompletenessTests(unittest.TestCase):
    """zh 是 source of truth · en/th/ja 不能漏 key."""

    @classmethod
    def setUpClass(cls):
        cls.text = HOME_JS.read_text(encoding="utf-8")
        cls.blocks = parse_i18n_blocks(cls.text)

    def test_four_language_blocks_present(self):
        self.assertEqual(
            set(self.blocks.keys()),
            {"zh", "en", "th", "ja"},
            "home.js I18N 必须有且仅有 zh/en/th/ja 4 个语言块",
        )

    def test_no_missing_keys_in_any_lang(self):
        """zh 里有的 key · en/th/ja 都必须有."""
        diffs = diff_keysets(self.blocks, source="zh")
        missing_summary = {lang: d["missing"] for lang, d in diffs.items() if d["missing"]}
        if missing_summary:
            lines = ["以下 i18n key 缺失 · 必须补全:"]
            for lang, keys in missing_summary.items():
                lines.append(f"  [{lang}] missing {len(keys)} keys:")
                for k in keys[:20]:
                    lines.append(f"    - {k}")
                if len(keys) > 20:
                    lines.append(f"    ... 还有 {len(keys) - 20} 个")
            self.fail("\n".join(lines))

    def test_no_extra_keys_in_non_source_lang(self):
        """en/th/ja 里有的 key · zh 也应该有 (反向防漏)."""
        diffs = diff_keysets(self.blocks, source="zh")
        extra_summary = {lang: d["extra"] for lang, d in diffs.items() if d["extra"]}
        if extra_summary:
            lines = ["以下 i18n key 在 non-zh 但 zh 缺 · 反向漏译:"]
            for lang, keys in extra_summary.items():
                lines.append(f"  [{lang}] zh 缺 {len(keys)} keys (在 {lang} 里有):")
                for k in keys[:20]:
                    lines.append(f"    - {k}")
                if len(keys) > 20:
                    lines.append(f"    ... 还有 {len(keys) - 20} 个")
            self.fail("\n".join(lines))


if __name__ == "__main__":
    unittest.main()
