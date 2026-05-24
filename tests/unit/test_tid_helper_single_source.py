# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · _tid 从 app.py 搬到 route_helpers.py。

锁定(防搬迁回归):
  1. _tid 单一来源在 route_helpers · app.py 用的就是同一个对象(防两份定义漂移)
  2. _tid 行为契约不变(取 tenant_id 字符串 / None fallback)
"""

import unittest

import app
import route_helpers
from route_helpers import _tid


class TidHelperSingleSourceTests(unittest.TestCase):
    def test_single_source(self):
        """app._tid 就是 route_helpers._tid(单一来源)"""
        self.assertIs(app._tid, route_helpers._tid)

    def test_behavior_contract(self):
        """取 tenant_id 字符串 · 空/NULL fallback None"""
        self.assertIsNone(_tid(None))
        self.assertIsNone(_tid({}))
        self.assertIsNone(_tid({"tenant_id": None}))
        self.assertEqual(_tid({"tenant_id": 123}), "123")
        self.assertEqual(_tid({"tenant_id": "abc-uuid"}), "abc-uuid")


if __name__ == "__main__":
    unittest.main()
