# -*- coding: utf-8 -*-
"""过账去向解析守门单测(services/erp/express_push/posting_kind)。

口径与设计理由见该模块 docstring。此处钉三件事:
  1. normalize 认不出的值一律 None —— 错记库存会真扣客户库存并结转 COGS,查账才发现,不可逆;
  2. 两级优先级(显式传参 > 票上声明),且脏值不吃掉下一级;
  3. 解析确实落在 enqueue_express 函数体内(见 BatchDispatchRegressionTests);
  4. 归一确实落在 run_recognition_core 入口(两条上传腿唯一漏斗 · 见 IntakeFunnelTests)。
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import push_dispatch  # noqa: E402
from services.erp.express_push.enqueue import enqueue_express  # noqa: E402
from services.erp.express_push.posting_kind import (  # noqa: E402
    VALID_POSTING_KINDS,
    normalize,
    resolve_posting_kind,
)
from services.erp.express_push.preflight import Preflight  # noqa: E402

# 端点 / 票的形状复用 Express 入队单测,别在这儿另养一份(两份会漂:少 enabled、少科目字段)。
from tests.unit.test_express_enqueue import _sales_endpoint, _sales_history  # noqa: E402

# 真实会撞上的脏值:前端空串、旧客户端拼错、手工改库、i18n 文案漏翻。
DIRTY_VALUES = ("", "   ", "stocks", "STOCK_ITEM", "inventory", "库存", "none", "null", "1", "true")


class NormalizeTests(unittest.TestCase):
    def test_canonical_values_pass_through(self):
        self.assertEqual(normalize("stock"), "stock")
        self.assertEqual(normalize("service"), "service")

    def test_case_and_whitespace_tolerated(self):
        # 载荷经 JSON / 表单来回,大小写与首尾空白不该让一次合法声明作废。
        self.assertEqual(normalize("  STOCK "), "stock")
        self.assertEqual(normalize("Service"), "service")
        self.assertEqual(normalize("\tstock\n"), "stock")

    def test_unknown_string_never_becomes_stock(self):
        for value in DIRTY_VALUES:
            with self.subTest(value=value):
                self.assertIsNone(normalize(value))

    def test_non_string_never_becomes_stock(self):
        # bool 是 int 子类、dict/list 是整包 payload 传错位,都不能被当成声明。
        for value in (None, 0, 1, True, False, 3.5, ["stock"], {"posting_kind": "stock"}, object()):
            with self.subTest(value=repr(value)):
                self.assertIsNone(normalize(value))

    def test_only_two_kinds_are_valid(self):
        # 新增去向必须同步改 mapper,别只加枚举:此断言逼后来者看一眼这个测试。
        self.assertEqual(VALID_POSTING_KINDS, ("service", "stock"))


def _history(kind=None, hid="hist-1"):
    h = _sales_history()
    h["id"] = hid
    if kind is not None:
        h["posting_kind"] = kind
    return h


class ResolvePriorityTests(unittest.TestCase):
    def test_explicit_beats_history(self):
        # 手动推的每批开关是"此刻这个人"的决定,压过票上写的旧声明。
        self.assertEqual(resolve_posting_kind("service", _history("stock")), "service")
        self.assertEqual(resolve_posting_kind("stock", _history("service")), "stock")

    def test_history_declaration_used_when_caller_silent(self):
        # 声明跟着票走:自动推/重试/批量三条腿都不传参,全靠这一级。
        self.assertEqual(resolve_posting_kind(None, _history("service")), "service")
        self.assertEqual(resolve_posting_kind(None, _history("stock")), "stock")

    def test_nothing_declared_is_none(self):
        # None = 没人声明过,语义见 posting_kind.py docstring。
        self.assertIsNone(resolve_posting_kind(None, _history()))
        self.assertIsNone(resolve_posting_kind(None, None))
        self.assertIsNone(resolve_posting_kind(None))

    def test_dirty_explicit_falls_through_to_history(self):
        # 脏的显式值不该吃掉票上的合法声明 —— 否则前端传个空串就把库存票记成服务。
        for bad in DIRTY_VALUES:
            with self.subTest(explicit=bad):
                self.assertEqual(resolve_posting_kind(bad, _history("stock")), "stock")

    def test_dirty_history_is_none_not_stock(self):
        # 手工改库写坏 posting_kind 列 → 当没声明,不是回落 stock。
        self.assertIsNone(resolve_posting_kind(None, _history("stocks")))
        self.assertIsNone(resolve_posting_kind("inventory", _history("STOCK_ITEM")))

    def test_history_without_column_is_not_an_error(self):
        # 列是后加的可空列,老票读出来没这个 key(或为 NULL)→ 当无声明。
        self.assertIsNone(resolve_posting_kind(None, {"id": "old"}))
        self.assertIsNone(resolve_posting_kind(None, _history(None)))


def _stub_preflight():
    """替身 preflight:ready + 最小 payload,让 enqueue 跑完整条 queued 路径。"""
    return mock.Mock(return_value=Preflight(payload={"doctype": "IV", "account_set": "DATAT"}))


def _capture_preflight(history, endpoint=None, **kwargs):
    """跑一次 enqueue_express,回传 preflight_express 收到的调用。

    解析在 enqueue_express 函数体内,mock 点必须下沉到 preflight_express
    (mock 掉 enqueue_express 本身会把被测逻辑一起 mock 没)。
    """
    stub = _stub_preflight()
    with mock.patch("services.erp.express_push.enqueue.preflight_express", stub):
        enqueue_express(endpoint or _sales_endpoint(), history, **kwargs)
    stub.assert_called_once()
    return stub.call_args


# 失败时逐字打给改动者看,别让人凭直觉把这层加回来(全文见 posting_kind.py docstring)。
_NO_ENDPOINT_DEFAULT_WHY = (
    "账套级默认是【故意撤销】的:配上等于把 sales_mapper 的「永续客户 + 库存路未开 → 交会计」"
    "长期关闭;要加回来先连同该 escalate 一起重新评估。"
)


class EndpointDefaultStaysRemovedTests(unittest.TestCase):
    def test_endpoint_config_default_is_never_adopted(self):
        # 端点 config 里塞了 default_posting_kind + 票上无声明 → 仍然 None(走画像 escalate)。
        endpoint = _sales_endpoint(config={"default_posting_kind": "stock"})
        call = _capture_preflight(_history(), endpoint)
        self.assertIsNone(call.kwargs["posting_kind"], _NO_ENDPOINT_DEFAULT_WHY)


class EnqueueResolutionTests(unittest.TestCase):
    def test_history_declaration_reaches_preflight(self):
        # 自动推/重试/批量三条腿的形态:调用方不传 posting_kind,票上带着声明。
        # 此条红 = enqueue_express 没过 resolve_posting_kind,三条腿的票上声明被静默丢弃。
        call = _capture_preflight(_history("stock"))
        self.assertEqual(call.kwargs["posting_kind"], "stock")


class BatchDispatchRegressionTests(unittest.TestCase):
    def test_batch_leg_resolves_history_declaration(self):
        stub = _stub_preflight()
        with (
            mock.patch("services.erp.express_push.enqueue.preflight_express", stub),
            mock.patch(
                "services.erp.express_push.preflight.build_batch_prefetch",
                return_value={"profiles": {}, "bank_index": []},
            ),
        ):
            results = push_dispatch.dispatch_endpoint_batch(
                _sales_endpoint(),
                [_history("stock", "h1"), _history("service", "h2"), _history(None, "h3")],
            )

        self.assertEqual(len(results), 3)
        kinds = [c.kwargs["posting_kind"] for c in stub.call_args_list]
        self.assertEqual(
            kinds,
            ["stock", "service", None],
            "批量分拣腿丢了票上声明:解析必须留在 enqueue_express 函数体内(push_dispatch "
            "绕过 push_to_endpoint,搁 erp_push 解析这条腿永远读不到)。",
        )


class IntakeFunnelTests(unittest.TestCase):
    """归一在收料口入口就发生(同步/异步两条上传腿都经 run_recognition_core)。

    用一个必然被拒的文件名让函数在归一之后、跑 OCR 之前抛 400 —— 归一是函数体第一句,
    这样不必搭起整条识别管线就能钉住"进门先归一 + 丢声明留痕"。
    """

    def _run(self, kind):
        from fastapi import HTTPException

        from services.ocr.recognize.core import run_recognition_core

        file = mock.Mock(filename="x.exe")
        with self.assertRaises(HTTPException):
            run_recognition_core({"plan": "free"}, b"x", file, posting_kind=kind)

    def test_unrecognized_declaration_is_logged_not_silently_dropped(self):
        with self.assertLogs("mr-pilot", level="WARNING") as cm:
            self._run("stok")
        self.assertTrue(
            any("stok" in line for line in cm.output),
            "认不出的声明被静默丢弃 —— 那是静默改数的入口,必须留痕",
        )

    def test_canonical_declaration_does_not_warn(self):
        with self.assertLogs("mr-pilot", level="WARNING") as cm:
            logging.getLogger("mr-pilot").warning("sentinel")  # assertLogs 要求至少一条
            self._run("  STOCK ")
        self.assertEqual([line for line in cm.output if "posting-kind" in line], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
