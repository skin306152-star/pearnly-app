#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_topup_contract_safety_net.py · REFACTOR-WC

充值金额契约安全网 · 纯加测试不改业务 · 给 A/B 拆 billing_topup_routes 当保险。

锁定充值请求 / 超管审批的金额边界契约(Pydantic 校验)。这是「充值金额对」的第一道
闸 —— 防负额充值、防 0 额、防越界天价(500000 上限)。重构若把 gt=0 / le=500000
约束改丢,畸形金额会直接进 DB 写入,本测试在校验层先拦下。纯模型实例化(0 DB ·
0 网络)→ CI 真跑不 skip。

覆盖维度(对应 loop「充值 · 金额对」):
  1. 用户充值请求 amount_thb:gt=0(拒 0/负)· le=500000(拒越界)· 边界精确
  2. 超管审批 actual_amount_thb:gt=0(实际到账额不可为 0/负)
  3. 缺字段:amount_thb 必填(缺 → 拒)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_topup_models():
    try:
        from pydantic import ValidationError

        from routes import billing_topup_routes as routes
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"billing_topup_routes 不可 import:{e}")
    return routes, ValidationError


class TopupRequestAmountBoundsTest(unittest.TestCase):
    """用户充值请求 _TopupRequestBody.amount_thb · gt=0 · le=500000"""

    def setUp(self) -> None:
        self.routes, self.ValidationError = _load_topup_models()
        self.Model = self.routes._TopupRequestBody

    def _accepts(self, **kw) -> bool:
        try:
            self.Model(**kw)
            return True
        except self.ValidationError:
            return False

    def test_zero_amount_rejected(self) -> None:
        # 0 元充值无意义 · gt=0 必须拦(否则建出 0 额 pending 污染审批队列)
        self.assertFalse(self._accepts(amount_thb=0))

    def test_negative_amount_rejected(self) -> None:
        # 负额充值 = 反向扣钱 · 绝不允许
        self.assertFalse(self._accepts(amount_thb=-5))

    def test_minimum_positive_accepted(self) -> None:
        self.assertTrue(self._accepts(amount_thb=1))

    def test_upper_cap_boundary_accepted(self) -> None:
        # 500000 是上限内 · 恰好接受(边界值 le 含等于)
        self.assertTrue(self._accepts(amount_thb=500000))

    def test_over_cap_rejected(self) -> None:
        # 超 500000 上限 · 拦天价误填(防一次充值打爆余额表)
        self.assertFalse(self._accepts(amount_thb=500001))

    def test_amount_field_required(self) -> None:
        # amount_thb 必填 · 缺字段直接拒(不给默认 0)
        self.assertFalse(self._accepts(note="缺金额"))


class AdminTopupApproveAmountTest(unittest.TestCase):
    """超管审批 _AdminTopupApproveBody.actual_amount_thb · gt=0(实际到账额)"""

    def setUp(self) -> None:
        self.routes, self.ValidationError = _load_topup_models()
        self.Model = self.routes._AdminTopupApproveBody

    def _accepts(self, **kw) -> bool:
        try:
            self.Model(**kw)
            return True
        except self.ValidationError:
            return False

    def test_zero_actual_amount_rejected(self) -> None:
        # 审批到账额 0 = 批了个空 · gt=0 拦(防误批 0 额却标已充值)
        self.assertFalse(self._accepts(actual_amount_thb=0))

    def test_negative_actual_amount_rejected(self) -> None:
        self.assertFalse(self._accepts(actual_amount_thb=-100))

    def test_positive_actual_amount_accepted(self) -> None:
        # 实际到账额可与申请额不同(超管按真实银行流水填)· 正数即可
        self.assertTrue(self._accepts(actual_amount_thb=250))

    def test_actual_amount_field_required(self) -> None:
        self.assertFalse(self._accepts(note="缺实际金额"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
