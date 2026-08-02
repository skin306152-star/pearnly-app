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

import shutil
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tests.unit._node_harness import _run_node  # noqa: E402

from check_i18n import diff_keysets, parse_i18n_blocks, _i18n_source_file  # noqa: E402

# REFACTOR-C1(2026-05-25)· I18N 字典已从 home.js 抽到 static/i18n-data.js ·
# 跟 check_i18n 用同一个源文件解析器(优先 i18n-data.js · 回退 home.js)
I18N_SRC = _i18n_source_file()


class I18nDictCompletenessTests(unittest.TestCase):
    """zh 是 source of truth · en/th/ja 不能漏 key."""

    @classmethod
    def setUpClass(cls):
        cls.text = I18N_SRC.read_text(encoding="utf-8")
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


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过 node eval 交叉验证")
class ParserSeesEveryKeyTests(unittest.TestCase):
    """解析器认出来的键 == 浏览器真拿到的键。

    「0 missing」有两种来法:真齐了,或者解析器压根没看那几个键。原来的 `^\\s*['\"]…`
    + `.match()` 一行只认第一条,于是一行挤两条词条的地方后一条从上线起就在射程外
    (实测 14 个:contact-line-label / contact-phone-label / dxi-st1s~4s / help-modal-tip /
    set-group-{about,company,system,workflow} / set-page-sub / user-menu-{help,logout}),
    闸自报每块 4975 而真值 4989 —— 那 14 个键任意一语丢了,闸照报 0 missing。
    所以不拿正则自证,拿浏览器同款求值对拍;正则再被人动一次,这里先红。
    """

    def test_parsed_keys_match_a_real_eval(self):
        blocks = _run_node(
            "global.window = {};"
            "require('./static/i18n-data.js');"
            "const out = {};"
            "for (const l of Object.keys(window.I18N)) out[l] = Object.keys(window.I18N[l]);"
            "console.log(JSON.stringify(out));"
        )
        parsed = parse_i18n_blocks(I18N_SRC.read_text(encoding="utf-8"))
        self.assertEqual(sorted(parsed), sorted(blocks))
        for lang in sorted(blocks):
            truth = set(blocks[lang])
            with self.subTest(lang):
                self.assertEqual(sorted(parsed[lang] - truth), [], "解析器多认了这些键")
                self.assertEqual(sorted(truth - parsed[lang]), [], "解析器漏认了这些键")


if __name__ == "__main__":
    unittest.main()
