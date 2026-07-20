# -*- coding: utf-8 -*-
"""L3 视觉复核的抗锚定契约。

L3 的定位是"看图复核前一轮的结果",但 prompt 里同时摆着 Vision 全文和上一轮 JSON。
2026-07-20 实测:佛历年 2569 被 Vision 读成 2559 时,L3 只修被 trigger 点名的金额,
日期 0/4 沿用错值(用手写的 5 行简化 OCR 文本复现不出来 —— 必须喂真实 Vision 全文,
锚定才够强)。补上独立复读段后同样输入 4/4 读对,金额不受影响。

本测试锁的是 prompt 契约:那段指示必须在、且必须排在输出指令之前。
"""

from __future__ import annotations

import unittest

from services.ocr.layer3_fallback import _INDEPENDENT_REREAD, _build_user_prompt
from services.ocr.schemas import ThaiInvoice

_L2 = ThaiInvoice(
    invoice_number="IV69/00475",
    date="2016-05-31",
    date_raw="31/5/2559",
    total_amount="13888.60",
)
_TRIGGERS = ["total_amount='13888.60' not found in L1 OCR text"]


class IndependentRereadContractTests(unittest.TestCase):
    def setUp(self):
        self.prompt = _build_user_prompt("วันที่/Date 31/5/2559", _L2, _TRIGGERS)

    def test_prompt_carries_the_reread_block(self):
        self.assertIn(_INDEPENDENT_REREAD, self.prompt)

    def test_image_wins_over_ocr_text_is_stated(self):
        self.assertIn("IMAGE WINS", _INDEPENDENT_REREAD)

    def test_names_single_stroke_digit_confusion(self):
        # 5/6 一笔之差正是 2569→2559 的成因,这条不能被后人顺手删掉
        self.assertIn("5/6", _INDEPENDENT_REREAD)

    def test_reread_precedes_the_output_instruction(self):
        """排在输出指令之前 —— 放在结尾会被"现在输出"截断语义。"""
        self.assertLess(
            self.prompt.index(_INDEPENDENT_REREAD),
            self.prompt.index("Now look at the IMAGE"),
        )

    def test_previous_json_still_supplied(self):
        """抗锚定不等于不给上一轮结果 —— L3 仍需知道哪里被怀疑。"""
        self.assertIn("PREVIOUS JSON", self.prompt)
        self.assertIn("31/5/2559", self.prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
