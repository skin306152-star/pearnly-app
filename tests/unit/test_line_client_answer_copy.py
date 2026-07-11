# -*- coding: utf-8 -*-
"""客户回答回执文案选取器契约(services/line_binding/line_client_answer_copy)。

钉死:①already_handled 压过一切 ②applied→已更新词表 ③其余→人审词表
④四语齐全且 th 恒在(回执兜底语言)。"""

import unittest

from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_answer_copy as copy


class AckCopyTests(unittest.TestCase):
    def test_already_handled_wins_over_status(self):
        picked = copy.ack_copy(vocab.APPLIED, already_handled=True)
        self.assertIs(picked, copy._ALREADY_HANDLED)

    def test_applied_status_maps_to_applied_copy(self):
        self.assertIs(copy.ack_copy(vocab.APPLIED, already_handled=False), copy._APPLIED)

    def test_other_statuses_map_to_manual_copy(self):
        self.assertIs(copy.ack_copy(vocab.MANUAL_REVIEW, already_handled=False), copy._MANUAL)

    def test_every_table_has_all_four_langs_with_th(self):
        for table in (copy._APPLIED, copy._MANUAL, copy._ALREADY_HANDLED):
            self.assertEqual(set(table), {"th", "en", "zh", "ja"})
            self.assertTrue(table["th"])


if __name__ == "__main__":
    unittest.main()
