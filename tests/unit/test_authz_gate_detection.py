# -*- coding: utf-8 -*-
"""authz 闸的守门识别本身可信吗(2026-07-25)。

背景:第 8 道闸(check_authz_coverage)靠正则认 handler 有没有门。它原来只看 handler
自己一层,于是门写在同文件 helper 里的路由(payroll 年报 / bank-sales)被误判"无守门",
85 条报红里 68 条是误报 —— 闸自己不准比没有闸更坏,人会开始无视真报警。

改成顺着调用往里看两层后,必须锁住反面:**真没门的照样要被抓出来**,否则闸变橡皮章。
本文件同时钉住"看几层"这个边界,免得以后有人偷偷放宽成"看到天亮"。
"""

from __future__ import annotations

import sys
import unittest

from scripts.authz_route_inventory import _gate_of

_MODULE = sys.modules[__name__]


def _gated_helper():
    require_perm(None, "x.y")  # noqa: F821 — 只取源码文本给正则看,不执行


def _ai_gated_helper():
    authorize_pearnly_ai(None, "x.y", not_found="nope")  # noqa: F821


def _outer_helper():
    _ai_gated_helper()


def _deep_helper():
    _outer_helper()


def _harmless_helper():
    return 1 + 1


def handler_direct_gate():
    require_perm(None, "x.y")  # noqa: F821
    return {"ok": True}


def handler_gate_one_hop():
    _gated_helper()
    return {"ok": True}


def handler_gate_two_hops():
    _outer_helper()
    return {"ok": True}


def handler_no_gate_anywhere():
    _harmless_helper()
    return {"ok": True}


def handler_gate_three_hops():
    _deep_helper()
    return {"ok": True}


class GateDetectionTests(unittest.TestCase):
    def _gate(self, fn):
        import inspect

        return _gate_of(inspect.getsource(fn), _MODULE)

    def test_direct_gate_detected(self):
        self.assertEqual(self._gate(handler_direct_gate), "require_perm")

    def test_gate_in_same_file_helper_detected(self):
        self.assertEqual(self._gate(handler_gate_one_hop), "require_perm→_gated_helper")

    def test_gate_two_hops_detected(self):
        gate = self._gate(handler_gate_two_hops)
        self.assertIsNotNone(gate)
        self.assertTrue(gate.startswith("pearnly_ai_gate"), gate)

    def test_truly_ungated_handler_still_flagged(self):
        """闸不许变橡皮章:调了个无关 helper 不等于有门。"""
        self.assertIsNone(self._gate(handler_no_gate_anywhere))

    def test_lookahead_depth_is_bounded(self):
        """只看两层 —— 再深不认(宁可误报让人来看,不许无边界地猜有门)。"""
        self.assertIsNone(self._gate(handler_gate_three_hops))


if __name__ == "__main__":
    unittest.main()
