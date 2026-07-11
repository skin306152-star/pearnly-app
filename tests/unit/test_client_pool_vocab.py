# -*- coding: utf-8 -*-
"""待问客户池词汇表(services/line_binding/client_pool_vocab)· 纯常量叶子契约。

钉死:三终态出边为空(不悬空)、active/terminal 互斥覆盖全集、非法跳转判假、
零依赖(不 import 本包任何模块,防循环导入回归)。
"""

import ast
import unittest
from pathlib import Path

from services.line_binding import client_pool_vocab as vocab


class VocabShapeTests(unittest.TestCase):
    def test_question_types_are_the_full_set(self):
        self.assertEqual(
            set(vocab.QUESTION_TYPES),
            {"direction", "amount", "drop", "freeform"},
        )

    def test_active_and_terminal_partition_all_statuses(self):
        self.assertEqual(vocab.ACTIVE_STATUSES | vocab.TERMINAL_STATUSES, vocab.ALL_STATUSES)
        self.assertEqual(vocab.ACTIVE_STATUSES & vocab.TERMINAL_STATUSES, frozenset())
        self.assertEqual(
            vocab.ALL_STATUSES,
            {"staged", "pending", "manual_review", "applied", "resolved_internally", "cancelled"},
        )


class LegalTransitionTests(unittest.TestCase):
    def test_terminal_states_have_no_outgoing_edges(self):
        for status in vocab.TERMINAL_STATUSES:
            self.assertEqual(vocab.LEGAL_TRANSITIONS[status], frozenset())

    def test_staged_can_only_go_pending_or_cancelled(self):
        self.assertEqual(vocab.LEGAL_TRANSITIONS[vocab.STAGED], {vocab.PENDING, vocab.CANCELLED})

    def test_pending_allows_push_failure_rollback_to_staged(self):
        self.assertIn(vocab.STAGED, vocab.LEGAL_TRANSITIONS[vocab.PENDING])

    def test_manual_review_only_reaches_terminal_states(self):
        self.assertEqual(
            vocab.LEGAL_TRANSITIONS[vocab.MANUAL_REVIEW], {vocab.APPLIED, vocab.CANCELLED}
        )

    def test_is_legal_transition_matches_table(self):
        self.assertTrue(vocab.is_legal_transition(vocab.STAGED, vocab.PENDING))
        self.assertFalse(vocab.is_legal_transition(vocab.APPLIED, vocab.PENDING))
        self.assertFalse(vocab.is_legal_transition("bogus", vocab.PENDING))


class ZeroDependencyTests(unittest.TestCase):
    def test_module_imports_nothing_from_own_package(self):
        """静态解析源码 import 语句:不许 import services.line_binding 下任何兄弟模块
        (纯常量叶子,防循环导入 · 照 decisions.py 同款保证)。"""
        src = Path(vocab.__file__).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotIn("line_binding", node.module)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("line_binding", alias.name)


if __name__ == "__main__":
    unittest.main()
