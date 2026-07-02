# -*- coding: utf-8 -*-
"""灰度前门路由收口(批一·止血):故障走安全兜底不掉旧路;主动 defer/无余额交旧路(能力不丢)。"""

import unittest
from unittest.mock import patch

from services.agent.loop import TurnResult
from services.line_binding import line_agent_route as route


def _call(res=None, *, balance_ok=True):
    said, charged = [], []
    kw = dict(
        balance_ok=balance_ok,
        say=lambda body: said.append(body),
        charge=lambda: charged.append(1),
        book=lambda *a, **k: True,
    )
    with patch("services.line_binding.line_agent_bridge.try_agent_turn", return_value=res):
        handled = route.route_gated({"id": "u1"}, "rt", "U1", "hi", "th", "t1", 1, "qt", [], **kw)
    return handled, said, charged


class TestRouteGated(unittest.TestCase):
    def test_reply_handled_charged_said(self):
        handled, said, charged = _call(TurnResult("reply", "สวัสดีค่ะ"))
        self.assertEqual(handled, "consumed")
        self.assertEqual(said, ["สวัสดีค่ะ"])  # 发大脑人话
        self.assertEqual(len(charged), 1)  # 计费一次

    def test_card_sent_handled_charged_no_say(self):
        handled, said, charged = _call(TurnResult("card_sent"))
        self.assertEqual(handled, "consumed")
        self.assertEqual(said, [])  # 卡已发,不再发文字
        self.assertEqual(len(charged), 1)

    def test_crash_safe_fallback_no_charge(self):
        # ★止血:故障 → 安全兜底一句(四语),不计费,消费本轮(绝不掉旧路)。
        handled, said, charged = _call(TurnResult("crash"))
        self.assertEqual(handled, "consumed")
        self.assertEqual(said, [route._SAFE_FALLBACK["th"]])
        self.assertEqual(charged, [])  # 故障不计费

    def test_defer_record_falls_to_legacy(self):
        handled, said, _ = _call(TurnResult("defer_record"))
        self.assertEqual(handled, "defer_record")  # 交旧路确定性直录
        self.assertEqual(said, [])

    def test_defer_edit_falls_to_legacy(self):
        handled, _, _ = _call(TurnResult("defer_edit"))
        self.assertEqual(handled, "defer_edit")  # 交旧路(改错/撤销·能力不丢)

    def test_no_balance_skips_agent_to_legacy(self):
        handled, said, charged = _call(balance_ok=False)
        self.assertEqual(handled, "skip")  # 无余额不跑大脑 → 旧路
        self.assertEqual((said, charged), ([], []))


if __name__ == "__main__":
    unittest.main()
