# -*- coding: utf-8 -*-
"""
2026-05-23 · 守门测试 · release_notes 覆盖式规则(CLAUDE.md §6 升级铁律)

锁定 4 个契约:
  1. release_notes 4 语全到(zh / th / en / ja)· 每个 ≥50 字符 ≤2000 字符
  2. 不留历史 prepend:不含老版本号 v118.35.0.4x (x < 当前)· 不含 prepend 标记『以下面向用户』/『features for end users』/『ด้านล่างคือ』/『以下はエンドユーザー』
  3. 用标准官方语言:不含口语化标记(🚨 / 客户反馈 / 我们修了 / 大白话)
  4. 不含开发术语:不含 "根因" / "修法" / 直接代码引用(如 datetime · openpyxl · split · regex)
"""

import asyncio
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ReleaseNotesContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import sys

        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        # REFACTOR-B1(2026-05-28)· get_frontend_version 已迁到 meta_aliases_routes
        from routes import meta_aliases_routes

        result = asyncio.run(meta_aliases_routes.get_frontend_version())
        cls.release_notes = result.get("release_notes") or {}

    def test_4_lang_all_present_with_reasonable_length(self):
        """契约 1 · 4 语全到 · 每个 50-2000 字符(防漏译 / 防仍是 prepend 链超长)"""
        for lang in ("zh", "th", "en", "ja"):
            self.assertIn(lang, self.release_notes, f"release_notes 缺 {lang} 字段")
            text = self.release_notes[lang]
            self.assertGreaterEqual(len(text), 50, f"{lang} 太短({len(text)} chars)· 至少 50 字符")
            self.assertLessEqual(
                len(text),
                2000,
                f"{lang} 太长({len(text)} chars)· 上限 2000 · 可能 prepend 老历史没清",
            )

    def test_no_history_prepend_chain(self):
        """契约 2 · 无 prepend 老历史(CLAUDE.md §6 新规则)"""
        prepend_markers = [
            "以下面向用户",  # zh prepend 老标记
            "features for end users",  # en
            "ด้านล่างคือฟีเจอร์สำหรับผู้ใช้",  # th
            "以下はエンドユーザー",  # ja
            "(不变)",
            "(unchanged)",
            "(ไม่เปลี่ยนแปลง)",
            "(変更なし)",
        ]
        for lang in ("zh", "th", "en", "ja"):
            text = self.release_notes[lang]
            for marker in prepend_markers:
                self.assertNotIn(
                    marker,
                    text,
                    f"{lang} 残留 prepend 标记『{marker}』· 违反 CLAUDE.md §6 覆盖式规则",
                )
        # 不含多个旧版本号(覆盖式 · 至多含 1 个版本号自指)
        for lang in ("zh", "th", "en", "ja"):
            text = self.release_notes[lang]
            version_count = len(re.findall(r"v118\.\d+\.\d+\.\d+", text))
            self.assertLessEqual(
                version_count, 1, f"{lang} 含 {version_count} 个版本号 · 覆盖式应至多 1 个"
            )

    def test_uses_official_language_no_emoji_no_kouyu(self):
        """契约 3 · 官方语言 · 不含 🚨 / emoji / 口语化卖萌词"""
        kouyu_markers = [
            "🚨",
            "🔥",
            "💥",
            "🎉",  # emoji 表情
            "客户反馈",
            "客户说",
            "用户反馈我们",  # 内部叙事
            "我们修了",
            "我们发现",
            "我们决定",
            "大白话",
            "口语",
            "通俗",
            "hotfix",  # 开发术语
            "BUG-FIX",
            "P0",
            "P1",
            "P2",  # commit/task 编号
        ]
        for lang in ("zh", "th", "en", "ja"):
            text = self.release_notes[lang]
            for marker in kouyu_markers:
                self.assertNotIn(
                    marker,
                    text,
                    f"{lang} 含口语/内部叙事标记『{marker}』· 违反 CLAUDE.md §6 标准官方语言规则",
                )

    def test_no_developer_jargon(self):
        """契约 4 · 不含开发术语 / 代码引用"""
        dev_terms = [
            "根因",
            "修法",
            "回归测试",  # zh 开发术语
            "Root cause",
            "Fix:",
            "regression",
            "ต้นเหตุ",
            "วิธีแก้",  # th 开发术语
            "根本原因",
            "修正:",  # ja
            # 直接代码引用
            "datetime",
            "openpyxl",
            "split(",
            "regex",
            "JSONB",
            "Alembic",
            "schema",
            "function",
            "callback",
            "handler",
        ]
        for lang in ("zh", "th", "en", "ja"):
            text = self.release_notes[lang]
            for term in dev_terms:
                self.assertNotIn(
                    term, text, f"{lang} 含开发术语『{term}』· 违反 CLAUDE.md §6 用户能懂规则"
                )


if __name__ == "__main__":
    unittest.main()
