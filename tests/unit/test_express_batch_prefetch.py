# -*- coding: utf-8 -*-
"""Express 批量推送批级预取(preflight.build_batch_prefetch)单测(mock db · 无网络)。

钉死:批量路径与逐票路径判定等价(同一组票两条路径跑出相同 account_source/doctype_src)、
批量 N 票只发 1 次供应商档案查询 + 1 次银行流水查询(去 N+1)、预取失败时逐票回退自查不炸。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import push_dispatch  # noqa: E402
from services.erp.express_push import preflight as preflight_mod  # noqa: E402
from services.erp.express_push.preflight import (  # noqa: E402
    build_batch_prefetch,
    preflight_express,
)

OWN_TAX = "0994000333444"
VENDOR_TAX = "0107561000013"

_CONFIG = {
    "account_set": "DATAT",
    "fallback_acc": "11-04-02-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
}


def _endpoint(**over):
    cfg = dict(_CONFIG)
    cfg.update(over.pop("config", {}))
    ep = {"id": "ep-1", "adapter": "express", "user_id": "u1", "enabled": True, "config": cfg}
    ep.update(over)
    return ep


def _history(hid="hist-1", **fover):
    fields = {
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "seller_tax": VENDOR_TAX,
        "buyer_tax": OWN_TAX,
        "subtotal": "375347.20",
        "vat": "26274.30",
        "invoice_number": hid,
        "document_type": "tax_invoice",
    }
    fields.update(fover)
    return {
        "id": hid,
        "invoice_date": "2015-12-31",
        "invoice_no": hid,
        "total_amount": "401621.50",
        "confidence": "high",
        "workspace_client_id": 7,
        "pages": [{"fields": fields}],
    }


class _FakeCursorCM:
    """db.get_cursor() 假上下文管理器 · get_profiles 本身另 mock,cur 内容不重要。"""

    def __enter__(self):
        return mock.MagicMock()

    def __exit__(self, *a):
        return False


class BatchPrefetchBase(unittest.TestCase):
    def setUp(self):
        self._env = mock.patch.dict("os.environ", {"ERP_PUSH_ENABLED": "true"})
        self._env.start()
        self._tid = mock.patch("core.db.get_user_tenant_id", return_value="tenant-1")
        self._tid.start()
        self._wc = mock.patch("core.db.get_workspace_client", return_value={"tax_id": OWN_TAX})
        self._wc.start()
        self._bundle = mock.patch("core.db.get_mrerp_mappings_bundle", return_value={})
        self._bundle.start()
        self._cursor = mock.patch("core.db.get_cursor", side_effect=lambda: _FakeCursorCM())
        self._cursor.start()

    def tearDown(self):
        self._cursor.stop()
        self._bundle.stop()
        self._wc.stop()
        self._tid.stop()
        self._env.stop()


class EquivalenceTests(BatchPrefetchBase):
    """批量路径(prefetch 给了)与逐票路径(prefetch=None 自查)判定结果必须等价。"""

    def test_batch_and_per_ticket_paths_agree(self):
        histories = [_history("h1"), _history("h2")]
        profile = {"default_payment": "paid", "source": "correction"}
        bank_rows = [{"direction": "OUT", "amount": "401621.50", "tx_date": "2015-12-31"}]

        with (
            mock.patch(
                "services.purchase.supplier_posting.get_profiles",
                return_value={VENDOR_TAX: profile},
            ),
            mock.patch(
                "services.erp.express_push.bank_evidence.load_bank_index_for_histories",
                return_value=bank_rows,
            ),
        ):
            prefetch = build_batch_prefetch(_endpoint(), histories)
            batch_results = [
                preflight_express(_endpoint(), h, prefetch=prefetch) for h in histories
            ]
            solo_results = [preflight_express(_endpoint(), h) for h in histories]

        for batch_pf, solo_pf in zip(batch_results, solo_results):
            self.assertTrue(batch_pf.ready)
            self.assertTrue(solo_pf.ready)
            self.assertEqual(batch_pf.payload["doctype_src"], solo_pf.payload["doctype_src"])
            self.assertEqual(batch_pf.payload["doctype"], solo_pf.payload["doctype"])
            self.assertEqual(batch_pf.payload["account_source"], solo_pf.payload["account_source"])


class QueryCountTests(BatchPrefetchBase):
    """N 张票的批量路径:档案 1 次 IN 查询 + 银行 1 次窗口查询(而非 N 次各自查询)。"""

    def test_batch_of_three_issues_single_profile_and_bank_query(self):
        histories = [_history("h1"), _history("h2"), _history("h3")]
        profiles_mock = mock.MagicMock(return_value={VENDOR_TAX: {"default_payment": "paid"}})
        bank_mock = mock.MagicMock(return_value=[])

        with (
            mock.patch("services.purchase.supplier_posting.get_profiles", profiles_mock),
            mock.patch(
                "services.erp.express_push.bank_evidence.load_bank_index_for_histories", bank_mock
            ),
        ):
            out = push_dispatch.dispatch_endpoint_batch(_endpoint(), histories)

        self.assertEqual(len(out), 3)
        self.assertTrue(all(r["error_msg"] == "EXPRESS_QUEUED" for r in out), out)
        self.assertEqual(profiles_mock.call_count, 1, "整批同账套须只发 1 次档案 IN 查询")
        self.assertEqual(bank_mock.call_count, 1, "整批须只发 1 次银行窗口查询")


class PrefetchFallbackTests(BatchPrefetchBase):
    """预取整体失败(如 db 层意外异常)→ 逐票回退各自查询,批量结果不炸、不漏张。"""

    def test_build_batch_prefetch_failure_falls_back_per_ticket(self):
        histories = [_history("h1"), _history("h2")]
        profiles_mock = mock.MagicMock(return_value={VENDOR_TAX: {"default_payment": "paid"}})

        with (
            mock.patch.object(
                preflight_mod, "build_batch_prefetch", side_effect=RuntimeError("boom")
            ),
            mock.patch("services.purchase.supplier_posting.get_profiles", profiles_mock),
            mock.patch(
                "services.erp.express_push.bank_evidence.load_bank_index_for_history",
                return_value=[],
            ),
        ):
            out = push_dispatch.dispatch_endpoint_batch(_endpoint(), histories)

        self.assertEqual(len(out), 2)
        self.assertTrue(all(r["error_msg"] == "EXPRESS_QUEUED" for r in out), out)
        # 回退路径:preflight 逐票各自查一次档案 → N 张 N 次(证明真回退,不是静默丢档案)。
        self.assertEqual(profiles_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
