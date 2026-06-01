#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_adapter_mixin_contract.py · REFACTOR-WB-modularize M0-M4

锁定 MRERPAdapter 巨类(1909→主 415)mixin 真重构 0 逻辑改:
  M0 dataclasses → mrerp_adapter_models(leaf)
  M1 登录/选公司 → MRERPLoginMixin
  M2 上传/列表分类/查删 → MRERPUploadMixin
  M3 主数据同步/校验 → MRERPMasterDataMixin
  M4 取/解析 report → MRERPReportMixin

钉死:
  1. MRO 顺序固定(组合顺序变 = 方法决议可能漂移)。
  2. 每个搬走的方法仍可达(MRO 解析)· 且确实落在预期 mixin(不是悄悄留在主类)。
  3. 各 mixin / models 是 leaf —— 不 back-import mrerp_adapter(无循环)。
  4. 主类核心(__init__/lifecycle/staticmethod helpers)仍定义在主体。
  5. dataclasses re-export 同一对象。

纯 import/类型内省 · 无 DB/Playwright/网络。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_adapter import MRERPAdapter  # noqa: E402
from services.erp import mrerp_adapter_models as _models  # noqa: E402
from services.erp import mrerp_adapter_login as _login  # noqa: E402
from services.erp import mrerp_adapter_upload as _upload  # noqa: E402
from services.erp import mrerp_adapter_report as _report  # noqa: E402
from services.erp import mrerp_adapter_masterdata as _master  # noqa: E402


class MrerpAdapterMixinContractTest(unittest.TestCase):
    def test_mro_order_fixed(self) -> None:
        self.assertEqual(
            [c.__name__ for c in MRERPAdapter.__mro__],
            [
                "MRERPAdapter",
                "MRERPLoginMixin",
                "MRERPUploadMixin",
                "MRERPReportMixin",
                "MRERPMasterDataMixin",
                "object",
            ],
        )

    def test_methods_resolve_to_expected_mixin(self) -> None:
        owner = {
            # main class body (核心 lifecycle + staticmethod helpers)
            "__init__": MRERPAdapter,
            "from_encrypted": MRERPAdapter,
            "_retry_technical": MRERPAdapter,
            "_extract_items": MRERPAdapter,
            "_extract_buyer": MRERPAdapter,
            "dialog_log": MRERPAdapter,
            # login mixin
            "login": _login.MRERPLoginMixin,
            "select_company": _login.MRERPLoginMixin,
            "_is_login_bounced": _login.MRERPLoginMixin,
            # upload mixin
            "upload_invoice_batch": _upload.MRERPUploadMixin,
            "search_invoice": _upload.MRERPUploadMixin,
            "delete_invoice": _upload.MRERPUploadMixin,
            # report mixin
            "_upload_and_fetch_report": _report.MRERPReportMixin,
            # masterdata mixin
            "_sync_master_data": _master.MRERPMasterDataMixin,
            "_verify_resolved_master_data": _master.MRERPMasterDataMixin,
        }
        for name, cls in owner.items():
            self.assertIn(name, vars(cls), f"{name} 不在 {cls.__name__} 本体")
            self.assertTrue(callable(getattr(MRERPAdapter, name, None)), f"{name} MRO 不可达")

    def test_no_method_name_collision_across_mixins(self) -> None:
        # mixin 之间方法名不得重叠(否则 MRO 静默覆盖)
        groups = [
            _login.MRERPLoginMixin,
            _upload.MRERPUploadMixin,
            _report.MRERPReportMixin,
            _master.MRERPMasterDataMixin,
        ]
        seen: dict = {}
        for g in groups:
            for name in vars(g):
                if name.startswith("__"):
                    continue
                if callable(getattr(g, name, None)):
                    self.assertNotIn(
                        name, seen, f"{name} 同名落在 {seen.get(name)} 与 {g.__name__}"
                    )
                    seen[name] = g.__name__

    def test_submodules_are_leaf(self) -> None:
        for m in (_models, _login, _upload, _report, _master):
            self.assertIsNone(
                getattr(m, "mrerp_adapter", None), f"{m.__name__} 不应 back-import 主类"
            )

    def test_dataclasses_reexport_single_source(self) -> None:
        from services.erp.mrerp_adapter import FailedRow, ImportResult, InvoiceRecord, SuccessRow

        self.assertIs(InvoiceRecord, _models.InvoiceRecord)
        self.assertIs(ImportResult, _models.ImportResult)
        self.assertIs(FailedRow, _models.FailedRow)
        self.assertIs(SuccessRow, _models.SuccessRow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
