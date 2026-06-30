# -*- coding: utf-8 -*-
"""agent_i18n 渲染 + 前后端 key 同源 contract(MASTER-PLAN 铁律 2:对话/按钮同源)。"""

import re
import unittest
from pathlib import Path

from services.agent import agent_i18n

_I18N_JS = Path(__file__).resolve().parents[2] / "static" / "i18n-data.js"


def _js_agent_keys() -> set:
    """从 static/i18n-data.js 抽 agent.* key 集合(line-based · 不依赖 JS 解析)。"""
    keys = set()
    kv = re.compile(r"^\s*'(agent\.[a-zA-Z_.]+)'\s*:")
    for ln in _I18N_JS.read_text(encoding="utf-8").splitlines():
        m = kv.match(ln)
        if m:
            keys.add(m.group(1))
    return keys


class TestAgentI18n(unittest.TestCase):
    def test_renders_with_slots(self):
        out = agent_i18n.render("agent.ok.balance|balance=123.45;pages=7", "zh")
        self.assertIn("123.45", out)
        self.assertIn("7", out)
        self.assertNotIn("{", out)  # 槽位全部替换,不漏花括号

    def test_missing_slot_degrades_to_blank(self):
        # 缺槽位 → 空串,绝不把 {slot} 吐给用户。
        out = agent_i18n.render("agent.ok.notifications", "th")
        self.assertNotIn("{", out)
        self.assertNotIn("top_list", out)

    def test_extra_slot_ignored(self):
        out = agent_i18n.render("agent.ok.history|count=3;ghost=zzz", "en")
        self.assertIn("3", out)
        self.assertNotIn("zzz", out)

    def test_lang_fallback_to_th(self):
        # 未知语言 → 落 th(主市场),不返回 key。
        out = agent_i18n.render("agent.chat.greeting", "fr")
        self.assertEqual(out, agent_i18n.render("agent.chat.greeting", "th"))
        self.assertNotEqual(out, "agent.chat.greeting")

    def test_unknown_key_returns_key(self):
        self.assertEqual(agent_i18n.render("agent.ghost.nope", "zh"), "agent.ghost.nope")

    def test_value_separators_do_not_break_parse(self):
        # copy_map 已消毒 ; |;此处确认值含逗号/空格仍正确落位。
        out = agent_i18n.render(
            "agent.ok.history_summary|count=4;by_status=confirmed 3, failed 1", "zh"
        )
        self.assertIn("4", out)
        self.assertIn("confirmed 3, failed 1", out)

    def test_all_four_langs_present(self):
        for key in agent_i18n.keys():
            for lang in ("zh", "en", "th", "ja"):
                self.assertTrue(agent_i18n._T[key].get(lang), f"{key}/{lang} 缺译")

    def test_key_parity_with_i18n_data_js(self):
        # 前后端同源:两侧 agent.* key 集合必须一致,防漂。
        py = agent_i18n.keys()
        js = _js_agent_keys()
        self.assertEqual(py, js, f"only-py={py - js} only-js={js - py}")


if __name__ == "__main__":
    unittest.main()
