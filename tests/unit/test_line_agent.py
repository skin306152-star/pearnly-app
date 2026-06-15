# -*- coding: utf-8 -*-
"""LINE 对话大脑护栏(docs/smart-intake/15 · Phase 2b)。

锁:写账闸 may_write —— 仅 record + 陈述/命令才写;问句/否定/假设/非记账一律不写(铁律护栏)。
understand 无 key → None(回落)。
"""

import unittest

from services.expense import line_agent


class MayWriteTests(unittest.TestCase):
    def test_record_statement_writes(self):
        self.assertTrue(line_agent.may_write("record", "statement"))
        self.assertTrue(line_agent.may_write("record", "command"))

    def test_record_question_negation_hypothetical_never_write(self):
        for sa in ("question", "negation", "hypothetical"):
            self.assertFalse(line_agent.may_write("record", sa), sa)

    def test_non_record_never_writes(self):
        for intent in ("query_summary", "query_detail", "undo", "edit", "chat", "out_of_scope"):
            self.assertFalse(line_agent.may_write(intent, "statement"), intent)


class UnderstandTests(unittest.TestCase):
    def test_no_key_returns_none(self):
        self.assertIsNone(line_agent.understand("ค่าน้ำ 50", api_key=None))

    def test_blank_text_returns_none(self):
        self.assertIsNone(line_agent.understand("  ", api_key="k"))


if __name__ == "__main__":
    unittest.main()
