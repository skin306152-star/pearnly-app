# -*- coding: utf-8 -*-
"""前门大脑解析桩(services/front_desk/interpret.py · FD-0a)。

桩契约:恒返 degraded=True(前端出降级卡),intent/client/period 全空,不调网关不写业务表。
FD-0b 实装后替换产出即可,本测试锁「桩不假装懂、降级形状齐」——真实降级路径的隔离验收在
FD-0b(mock 超时 → degraded)。
"""

import unittest

from services.front_desk import interpret


class InterpretStubTests(unittest.TestCase):
    def test_always_degraded(self):
        out = interpret.interpret("ช่วยทำ vat เดือนนี้ให้ sister makeup หน่อย")
        self.assertTrue(out["degraded"])
        self.assertEqual(out["reason"], interpret.DEGRADED_STUB)

    def test_no_intent_or_client_guessed(self):
        out = interpret.interpret("random", tenant_id="t-1", contract_id="c-1")
        self.assertIsNone(out["intent"])
        self.assertIsNone(out["client_suggestion"])
        self.assertIsNone(out["period"])

    def test_shape_is_stable_for_empty_utterance(self):
        out = interpret.interpret("")
        self.assertEqual(set(out), {"degraded", "intent", "client_suggestion", "period", "reason"})


if __name__ == "__main__":
    unittest.main()
