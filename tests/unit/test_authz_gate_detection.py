# -*- coding: utf-8 -*-
"""authz 闸的守门识别本身可信吗(2026-07-25)。

背景:第 8 道闸(check_authz_coverage)靠正则认 handler 有没有门。它原来只看 handler
自己一层,于是门写在同文件 helper 里的路由(payroll 年报 / bank-sales)被误判"无守门",
85 条报红里 68 条是误报 —— 闸自己不准比没有闸更坏,人会开始无视真报警。

改成顺着调用往里看两层后,必须锁住反面:**真没门的照样要被抓出来**,否则闸变橡皮章。
本文件同时钉住"看几层"这个边界,免得以后有人偷偷放宽成"看到天亮"。

2026-08-11 体检又复现三种"假守门":门被整行注释掉、门埋在 `if False:` 里、门写在
`db.execute("DELETE ...")` 之后 —— 一行都不生效,认名字的正则却全判"已守门"。判门改走
AST 之后,下面每种退化写法各钉一条反证,外加两条控制组防误伤(门在写库之前照认、SQL 是
变量时照认)。
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


def _commented_gate_helper():
    # require_perm(None, "x.y")
    return 1


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


def handler_erp_draft_gate():
    _draft_token(None, "draft")  # noqa: F821
    return {"ok": True}


def handler_gate_commented_out():
    # require_perm(None, "x.y")
    return {"ok": True}


def handler_gate_in_dead_branch():
    if False:
        require_perm(None, "x.y")  # noqa: F821
    return {"ok": True}


def handler_gate_in_dead_branch_else():
    if False:
        pass
    else:
        require_perm(None, "x.y")  # noqa: F821
    return {"ok": True}


def handler_gate_after_delete():
    db.execute("DELETE FROM ocr_history WHERE id = %s", (1,))  # noqa: F821
    require_perm(None, "x.y")  # noqa: F821
    return {"ok": True}


def handler_gate_before_delete():
    require_perm(None, "x.y")  # noqa: F821
    db.execute("DELETE FROM ocr_history WHERE id = %s", (1,))  # noqa: F821
    return {"ok": True}


def handler_gate_after_dynamic_sql():
    db.execute(sql, params)  # noqa: F821
    require_perm(None, "x.y")  # noqa: F821
    return {"ok": True}


def handler_calls_helper_with_commented_gate():
    _commented_gate_helper()
    return {"ok": True}


def handler_gated_helper_after_delete():
    db.execute("DELETE FROM ocr_history WHERE id = %s", (1,))  # noqa: F821
    _gated_helper()
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

    def test_erp_draft_custom_gate_detected(self):
        self.assertEqual(self._gate(handler_erp_draft_gate), "erp_draft_gate")

    def test_truly_ungated_handler_still_flagged(self):
        """闸不许变橡皮章:调了个无关 helper 不等于有门。"""
        self.assertIsNone(self._gate(handler_no_gate_anywhere))

    def test_lookahead_depth_is_bounded(self):
        """只看两层 —— 再深不认(宁可误报让人来看,不许无边界地猜有门)。"""
        self.assertIsNone(self._gate(handler_gate_three_hops))

    def test_commented_out_gate_is_not_a_gate(self):
        """注释掉的门一行都不执行,认名字的正则却判它有门。"""
        self.assertIsNone(self._gate(handler_gate_commented_out))

    def test_gate_in_dead_branch_is_not_a_gate(self):
        """`if False:` 里的门永远跑不到。"""
        self.assertIsNone(self._gate(handler_gate_in_dead_branch))

    def test_live_else_branch_still_counts(self):
        """剪的是恒假那半边,else 是真会跑的路径 —— 别连它一起剪了。"""
        self.assertEqual(self._gate(handler_gate_in_dead_branch_else), "require_perm")

    def test_gate_after_write_is_not_a_gate(self):
        """先删数据再查权限 = 没查:数据已经没了,再 403 也救不回来。"""
        self.assertIsNone(self._gate(handler_gate_after_delete))

    def test_gate_before_write_still_counts(self):
        """控制组:同样两行,门在写库之前就是真门。"""
        self.assertEqual(self._gate(handler_gate_before_delete), "require_perm")

    def test_non_literal_sql_does_not_swallow_the_gate(self):
        """SQL 是变量时判不出读写,保守当读 —— 否则一片已守门路由被误伤成红。"""
        self.assertEqual(self._gate(handler_gate_after_dynamic_sql), "require_perm")

    def test_helper_with_commented_gate_is_not_a_gate(self):
        """往下跟的每一层都按同一套判,不是只有 handler 自己这层。"""
        self.assertIsNone(self._gate(handler_calls_helper_with_commented_gate))

    def test_gated_helper_after_write_does_not_rescue(self):
        """被剪掉的调用也不能当往下跟的入口,否则删完再调 helper 又骗过去了。"""
        self.assertIsNone(self._gate(handler_gated_helper_after_delete))


class PublicRouteWhitelistTests(unittest.TestCase):
    """锁住 cowork / erp 页面壳在公开白名单,且不存在通配 /erp/{rest:path}。"""

    def test_cowork_shell_in_public_whitelist(self):
        from scripts.check_authz_coverage import PUBLIC_ROUTES

        self.assertIn(("GET", "/cowork"), PUBLIC_ROUTES)

    def test_erp_shell_in_public_whitelist(self):
        from scripts.check_authz_coverage import PUBLIC_ROUTES

        self.assertIn(("GET", "/erp"), PUBLIC_ROUTES)

    def test_no_erp_wildcard_route_in_whitelist(self):
        """/erp/{rest:path} 不在白名单 —— 避免扩大公开面。"""
        from scripts.check_authz_coverage import PUBLIC_ROUTES

        self.assertNotIn(("GET", "/erp/{rest:path}"), PUBLIC_ROUTES)


if __name__ == "__main__":
    unittest.main()
