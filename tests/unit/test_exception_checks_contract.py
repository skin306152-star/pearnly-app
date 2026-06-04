# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · OCR 异常检测 + 智能提醒链从 app.py 抽到 exception_checks.py。

锁定(防搬迁回归 + 防重复拷贝):
  1. app.py 与 exception_checks 用同一份 _async_run_exception_checks / _parse_money
     (单一来源 · OCR/LINE 上传路由 + history PUT 共用 · 不许各自拷一份漂移)
  2. confidence_low 规则码值不变(DB rule_code 契约 · 发票规则已统一进知识库引擎)
  3. _parse_money 行为契约不变
  4. line_client 防御式 import(未部署降级 None · 不在 import 期炸)
"""

import unittest

from services.exceptions import exception_checks


class ExceptionChecksContractTests(unittest.TestCase):
    def test_single_source_with_app(self):
        """消费者调的就是 exception_checks 的同一份对象 · 单一来源。
        _async_run_exception_checks:app.py OCR/LINE 上传路由仍调(app 再导出)。
        _parse_money:history PUT 用 · REFACTOR-B1 步骤 B 后随 history_routes 搬出 ·
        断言跟到新消费者 history_routes(app.py 已不再 import)。"""
        import app
        from routes import history_routes

        self.assertIs(app._async_run_exception_checks, exception_checks._async_run_exception_checks)
        self.assertIs(history_routes._parse_money, exception_checks._parse_money)
        self.assertIs(
            history_routes._async_run_exception_checks,
            exception_checks._async_run_exception_checks,
        )

    def test_rule_code_constants(self):
        """confidence_low 规则码值不变;发票规则码现由知识库引擎(R-*)统一产出"""
        self.assertEqual(exception_checks.EXC_RULE_CONFIDENCE_LOW, "confidence_low")

    def test_parse_money_behavior(self):
        """_parse_money 容错解析 · 千分位/฿/THB 剥离 · 失败返 None"""
        self.assertEqual(exception_checks._parse_money("1,234.50"), 1234.5)
        self.assertEqual(exception_checks._parse_money("฿ 100"), 100.0)
        self.assertEqual(exception_checks._parse_money("2,000 THB"), 2000.0)
        self.assertIsNone(exception_checks._parse_money(None))
        self.assertIsNone(exception_checks._parse_money(""))
        self.assertIsNone(exception_checks._parse_money("abc"))

    def test_line_client_defensive_import(self):
        """line_client 防御式 import · 未部署时 None · 不在 import 期炸(模块属性存在)"""
        self.assertTrue(hasattr(exception_checks, "line_client"))


if __name__ == "__main__":
    unittest.main()
