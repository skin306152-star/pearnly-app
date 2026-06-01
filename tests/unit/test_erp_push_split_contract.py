#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_erp_push_split_contract.py · REFACTOR-WB-modularize E1/E2/E3

锁定 erp_push.py facade 切分(1518→480)0 逻辑改:
  E1 → erp_mrerp_listing(连接测试 + 客户/产品拉取)
  E2 → erp_payload(payload 构造 + 通用 webhook + PUSH_TIMEOUT_SEC)
  E3 → erp_dms_push(MR.ERP DMS 全段 + push_mrerp_dms stub)

钉死:
  1. erp_push re-export 的名与子模块是【同一对象】(assertIs · `import erp_push as _erp`
     的 6 消费方 + dispatch/dms 单测 0 改动)。
  2. ADAPTER_REGISTRY 4 适配器映射不变 · 指向同一函数对象(防误推分发表完整)。
  3. 防误推核心仍在 erp_push:push_to_endpoint / ENCRYPTED_CRED_ADAPTERS 未被搬走。
  4. 子模块是 leaf —— 不 back-import erp_push(无循环)。

纯 import 契约 · 无 DB/网络/Playwright。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import erp_push as _erp  # noqa: E402
import erp_mrerp_listing as _listing  # noqa: E402
import erp_payload as _payload  # noqa: E402
import erp_dms_push as _dms  # noqa: E402

_E1 = ("test_mrerp_endpoint", "list_mrerp_customers", "list_mrerp_products")
_E2 = (
    "PUSH_TIMEOUT_SEC",
    "build_standard_payload",
    "build_payload_with_idempotency",
    "_iso",
    "push_webhook",
    "_apply_field_map",
    "push_flowaccount",
    "flatten_history_for_mrerp",
)
_E3 = (
    "test_mrerp_dms_endpoint",
    "push_mrerp_dms_id_card",
    "push_mrerp_dms",
    "_build_mrerp_dms_adapter",
    "_dms_friendly",
    "_dms_resolve_creds",
    "_id_card_payload_from_dict",
    "_mrerp_result_dict",
    "_DMS_FRIENDLY",
    "_DMS_DEFAULT_URL",
)


class ErpPushSplitContractTest(unittest.TestCase):
    def test_e1_reexport_single_source(self) -> None:
        for n in _E1:
            self.assertIs(getattr(_erp, n), getattr(_listing, n), f"E1 {n} re-export 漂移")

    def test_e2_reexport_single_source(self) -> None:
        for n in _E2:
            self.assertIs(getattr(_erp, n), getattr(_payload, n), f"E2 {n} re-export 漂移")

    def test_e3_reexport_single_source(self) -> None:
        for n in _E3:
            self.assertIs(getattr(_erp, n), getattr(_dms, n), f"E3 {n} re-export 漂移")

    def test_adapter_registry_intact(self) -> None:
        reg = _erp.ADAPTER_REGISTRY
        self.assertEqual(set(reg), {"webhook", "flowaccount", "mrerp", "mrerp_dms"})
        self.assertIs(reg["webhook"], _payload.push_webhook)
        self.assertIs(reg["flowaccount"], _payload.push_flowaccount)
        self.assertIs(reg["mrerp_dms"], _dms.push_mrerp_dms)

    def test_anti_mispush_core_stays_in_erp_push(self) -> None:
        # 防误推核心绝不搬走:push_to_endpoint 硬拒 mrerp_dms 发票推送 + 加密凭据集
        self.assertTrue(callable(getattr(_erp, "push_to_endpoint", None)))
        self.assertIn("push_to_endpoint", vars(_erp))  # 定义在 erp_push 本体(非 re-export)
        self.assertEqual(_erp.ENCRYPTED_CRED_ADAPTERS, {"mrerp", "mrerp_dms"})

    def test_submodules_are_leaf(self) -> None:
        for m in (_listing, _payload, _dms):
            self.assertIsNone(
                getattr(m, "erp_push", None), f"{m.__name__} 不应 back-import erp_push"
            )

    def test_dms_stub_still_refuses(self) -> None:
        # push_mrerp_dms 仍是拒绝 stub(不是发票推送目标)
        ok, status, _body = _erp.push_mrerp_dms({}, {})
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
