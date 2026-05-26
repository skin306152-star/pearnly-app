# -*- coding: utf-8 -*-
"""P1d 路由单测 · app._auto_push_smart_routed / _auto_push_batch_for_endpoint
   + ERP_SELLER_ROUTING 回滚开关。

锁定(Zihao 2026-05-26 蓝图):
  - 单端点 = 现行为(一组批量到该端点)
  - 多端点 = 各推各的(按卖方账套绑定的 endpoint 分组)
  - 未匹配/未绑端点/端点停用 = 兼容兜底(推现有 auto_push 端点 · 不阻断)
  - per-invoice 隔离(一张落库异常不影响其余)
  - dedup:已成功过写 skipped_dup,不进 dispatch
  - 失败入重试队列;用户数据错不入队
  - 回滚开关默认关
"""

import os
import unittest
from unittest import mock

import app
import db


class FlagTests(unittest.TestCase):
    def test_default_off(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ERP_SELLER_ROUTING", None)
            self.assertFalse(app._erp_seller_routing_enabled())

    def test_truthy_values(self):
        for v in ("1", "true", "TRUE", "yes", "on"):
            with mock.patch.dict(os.environ, {"ERP_SELLER_ROUTING": v}):
                self.assertTrue(app._erp_seller_routing_enabled(), v)

    def test_falsy_values(self):
        for v in ("0", "false", "off", "", "nope"):
            with mock.patch.dict(os.environ, {"ERP_SELLER_ROUTING": v}):
                self.assertFalse(app._erp_seller_routing_enabled(), v)

    def test_per_user_allowlist(self):
        # 全局关 · 但名单内 user 灰度开;名单外(含 mrerp)仍关。
        env = {"ERP_SELLER_ROUTING": "0", "ERP_SELLER_ROUTING_USERS": "uTest, uOther"}
        with mock.patch.dict(os.environ, env):
            self.assertTrue(app._erp_seller_routing_enabled("uTest"))
            self.assertTrue(app._erp_seller_routing_enabled("uOther"))
            self.assertFalse(app._erp_seller_routing_enabled("uMrerp"))
            self.assertFalse(app._erp_seller_routing_enabled(None))


def _hist(hid, wcid=None):
    return {
        "id": hid,
        "workspace_client_id": wcid,
        "invoice_no": f"INV{hid}",
        "seller_name": "S",
        "total_amount": 1.0,
        "client_id": "c1",
    }


class SmartRoutingGroupingTests(unittest.IsolatedAsyncioTestCase):
    """只验路由/分组/兜底 · batch 与 fallback 落库被 stub。"""

    def setUp(self):
        self.batch_calls = []  # (endpoint_id, [history ids])
        self.fallback_calls = []  # history ids

        async def fake_batch(user_id, endpoint, histories, tenant_id=None):
            self.batch_calls.append((str(endpoint["id"]), [str(h["id"]) for h in histories]))

        async def fake_fallback(user_id, hid, eps, tenant_id=None):
            self.fallback_calls.append(str(hid))

        self._p1 = mock.patch.object(app, "_auto_push_batch_for_endpoint", fake_batch)
        self._p2 = mock.patch.object(app, "_auto_push_history", fake_fallback)
        self._p1.start()
        self._p2.start()
        self.addCleanup(self._p1.stop)
        self.addCleanup(self._p2.stop)

        # workspace_client_id → erp_endpoint_id 映射
        self._wc = {10: "epA", 20: "epB", 30: None, 40: "epDisabled"}
        self._eps = {
            "epA": {"id": "epA", "enabled": True, "adapter": "mrerp"},
            "epB": {"id": "epB", "enabled": True, "adapter": "mrerp"},
            "epDisabled": {"id": "epDisabled", "enabled": False, "adapter": "mrerp"},
        }

    def _patch_db(self, hists):
        by_id = {h["id"]: h for h in hists}
        mock.patch.object(
            db, "get_ocr_history_detail", side_effect=lambda u, hid, tenant_id=None: by_id.get(hid)
        ).start()
        mock.patch.object(
            db,
            "get_workspace_client",
            side_effect=lambda wcid, u, tenant_id=None: (
                {"id": wcid, "erp_endpoint_id": self._wc.get(int(wcid))}
                if int(wcid) in self._wc
                else None
            ),
        ).start()
        mock.patch.object(
            db, "get_erp_endpoint", side_effect=lambda u, eid: self._eps.get(eid)
        ).start()
        self.addCleanup(mock.patch.stopall)

    async def test_single_endpoint_one_group(self):
        hists = [_hist("1", 10), _hist("2", 10)]
        self._patch_db(hists)
        await app._auto_push_smart_routed("u1", ["1", "2"], None, [{"id": "fb"}])
        self.assertEqual(len(self.batch_calls), 1)
        self.assertEqual(self.batch_calls[0][0], "epA")
        self.assertEqual(sorted(self.batch_calls[0][1]), ["1", "2"])
        self.assertEqual(self.fallback_calls, [])

    async def test_multi_endpoint_each_routes(self):
        hists = [_hist("1", 10), _hist("2", 20), _hist("3", 10)]
        self._patch_db(hists)
        await app._auto_push_smart_routed("u1", ["1", "2", "3"], None, [{"id": "fb"}])
        groups = {eid: ids for eid, ids in self.batch_calls}
        self.assertEqual(sorted(groups["epA"]), ["1", "3"])
        self.assertEqual(groups["epB"], ["2"])
        self.assertEqual(self.fallback_calls, [])

    async def test_unmatched_goes_to_fallback(self):
        # 5=无 workspace · 6=workspace 未绑端点(wcid30) · 7=端点停用(wcid40)
        hists = [_hist("5", None), _hist("6", 30), _hist("7", 40), _hist("8", 10)]
        self._patch_db(hists)
        await app._auto_push_smart_routed("u1", ["5", "6", "7", "8"], None, [{"id": "fb"}])
        self.assertEqual(self.batch_calls[0][0], "epA")
        self.assertEqual(self.batch_calls[0][1], ["8"])
        self.assertEqual(sorted(self.fallback_calls), ["5", "6", "7"])


class BatchForEndpointTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.logs = []
        self.retries = []
        mock.patch.object(
            db, "insert_push_log", side_effect=lambda **kw: self.logs.append(kw) or "log-1"
        ).start()
        mock.patch.object(db, "update_endpoint_stats", side_effect=lambda *a: None).start()
        mock.patch.object(db, "update_history_push_status", side_effect=lambda *a: None).start()
        mock.patch.object(
            db, "is_user_data_error", side_effect=lambda m: bool(m and "NAME_MISMATCH" in m)
        ).start()
        mock.patch.object(db, "get_erp_retry_delay_sec", side_effect=lambda n: 60).start()
        mock.patch.object(
            db, "schedule_log_retry", side_effect=lambda lid, d: self.retries.append((lid, d))
        ).start()
        self.addCleanup(mock.patch.stopall)

    def _ep(self):
        return {"id": "epA", "name": "A", "adapter": "mrerp"}

    async def test_dedup_writes_skipped_and_skips_dispatch(self):
        mock.patch.object(
            db,
            "has_recent_successful_push",
            side_effect=lambda hid, eid, u: {"id": "prior", "response_body": "{}"},
        ).start()
        from services.erp import push_dispatch

        disp = mock.patch.object(push_dispatch, "dispatch_endpoint_batch")
        m = disp.start()
        self.addCleanup(disp.stop)
        await app._auto_push_batch_for_endpoint(
            "u1", self._ep(), [{"id": "1", "invoice_no": "INV1"}], None
        )
        m.assert_not_called()
        self.assertEqual(self.logs[0]["status"], "skipped_dup")

    async def test_results_persisted_and_failure_schedules_retry(self):
        mock.patch.object(db, "has_recent_successful_push", side_effect=lambda *a: None).start()
        from services.erp import push_dispatch

        results = [
            {
                "success": True,
                "http_status": 200,
                "response_body": "ok",
                "error_msg": None,
                "elapsed_ms": 5,
                "request_body": {},
                "adapter": "mrerp",
            },
            {
                "success": False,
                "http_status": 200,
                "response_body": "no",
                "error_msg": "ERR_TECHNICAL: x",
                "elapsed_ms": 6,
                "request_body": {},
                "adapter": "mrerp",
            },
            {
                "success": False,
                "http_status": 200,
                "response_body": "no",
                "error_msg": "ERR_CUSTOMER_NAME_MISMATCH",
                "elapsed_ms": 7,
                "request_body": {},
                "adapter": "mrerp",
            },
        ]
        disp = mock.patch.object(push_dispatch, "dispatch_endpoint_batch", return_value=results)
        disp.start()
        self.addCleanup(disp.stop)
        hists = [
            {"id": "1", "invoice_no": "INV1"},
            {"id": "2", "invoice_no": "INV2"},
            {"id": "3", "invoice_no": "INV3"},
        ]
        await app._auto_push_batch_for_endpoint("u1", self._ep(), hists, None)
        statuses = [lg["status"] for lg in self.logs]
        self.assertEqual(statuses, ["success", "failed", "failed"])
        # 仅技术失败(h2)入重试队列;用户数据错(h3)不入队
        self.assertEqual(len(self.retries), 1)

    async def test_per_invoice_isolation_on_persist_error(self):
        mock.patch.object(db, "has_recent_successful_push", side_effect=lambda *a: None).start()
        from services.erp import push_dispatch

        results = [
            {
                "success": True,
                "http_status": 200,
                "response_body": "ok",
                "error_msg": None,
                "elapsed_ms": 5,
                "request_body": {},
                "adapter": "mrerp",
            },
            {
                "success": True,
                "http_status": 200,
                "response_body": "ok",
                "error_msg": None,
                "elapsed_ms": 5,
                "request_body": {},
                "adapter": "mrerp",
            },
        ]
        disp = mock.patch.object(push_dispatch, "dispatch_endpoint_batch", return_value=results)
        disp.start()
        self.addCleanup(disp.stop)
        # 第一张 persist 抛 · 第二张仍应被处理
        calls = {"n": 0}

        def flaky(user_id, ep, h, result, trigger="auto"):
            calls["n"] += 1
            if h["id"] == "1":
                raise RuntimeError("boom")

        p = mock.patch.object(app, "_persist_push_outcome", side_effect=flaky)
        p.start()
        self.addCleanup(p.stop)
        await app._auto_push_batch_for_endpoint(
            "u1",
            self._ep(),
            [{"id": "1", "invoice_no": "INV1"}, {"id": "2", "invoice_no": "INV2"}],
            None,
        )
        self.assertEqual(calls["n"], 2, "一张异常不应中断后续张")


class HistoryDetailExposesWorkspaceTests(unittest.TestCase):
    """回归守门(沙箱实测抓到的真 bug):get_ocr_history_detail 必须返回
    workspace_client_id —— 否则 _auto_push_smart_routed 永远读到 None → 全兜底,
    智能分拣形同虚设。单测 mock 了 detail 故没抓到 · 这里用假 cursor 锁死映射。"""

    def test_detail_returns_workspace_client_id(self):
        from datetime import datetime
        import db

        row = {
            "id": "h1",
            "filename": "f.pdf",
            "page_count": 1,
            "confidence": 0.9,
            "elapsed_ms": 10,
            "pages": [],
            "invoice_no": "INV1",
            "invoice_date": None,
            "seller_name": "S",
            "total_amount": None,
            "archive_name": None,
            "category_tag": None,
            "fields_edited_at": None,
            "edit_count": 0,
            "created_at": datetime(2026, 5, 26),
            "updated_at": datetime(2026, 5, 26),
            "client_id": None,
            "workspace_client_id": 7,
        }

        class _Cur:
            def execute(self, *a, **k):
                pass

            def fetchone(self):
                return row

        class _CM:
            def __enter__(self):
                return _Cur()

            def __exit__(self, *a):
                return False

        with mock.patch.object(db, "get_cursor", lambda *a, **k: _CM()):
            out = db.get_ocr_history_detail("u1", "h1")
        self.assertIn("workspace_client_id", out)
        self.assertEqual(out["workspace_client_id"], 7)


if __name__ == "__main__":
    unittest.main()
