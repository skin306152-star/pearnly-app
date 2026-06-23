#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守门测试 · Express 待补科目卡(选科目 + 覆盖重推 + 可选记住为账套默认)。

闭环:Express 缺科目留人工的票 → 用户从账套科目表补选科目 → 覆盖重推(更新原行,不新建)。
- derive_account_fix:从失败码推导该问哪些科目槽(direction + slots)。
- 路由:写前白名单(科目须 ∈ 上报科目表)· remember=True 并入端点 config 默认。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core import db  # noqa: E402,F401 · 先 import db 再 import push_store(避免 partial-init 循环)
from services.erp import erp_push as _erp  # noqa: E402
from services.erp.push_store import derive_account_fix  # noqa: E402


class DeriveAccountFixTests(unittest.TestCase):
    def test_single_missing_slot(self):
        self.assertEqual(
            derive_account_fix("EXPRESS_MANUAL: no_revenue_account"),
            {"direction": "sales", "slots": ["revenue_acc"]},
        )
        self.assertEqual(
            derive_account_fix("EXPRESS_MANUAL: no_ap_account"),
            {"direction": "purchase", "slots": ["ap_acc"]},
        )
        self.assertEqual(
            derive_account_fix("EXPRESS_MANUAL: no_input_vat_account"),
            {"direction": "purchase", "slots": ["vat_input_acc"]},
        )

    def test_not_in_chart_uses_request_direction(self):
        fix = derive_account_fix(
            "EXPRESS_MANUAL: account_not_in_chart:11-99", {"direction": "sales"}
        )
        self.assertEqual(fix["direction"], "sales")
        self.assertEqual(fix["slots"], ["revenue_acc", "ar_acc", "vat_output_acc"])
        self.assertEqual(fix["bad_code"], "11-99")

    def test_not_in_chart_unknown_direction_shows_all(self):
        fix = derive_account_fix("EXPRESS_MANUAL: account_not_in_chart:9-9", None)
        self.assertEqual(len(fix["slots"]), 6)

    def test_non_account_reason_is_none(self):
        self.assertIsNone(derive_account_fix("EXPRESS_MANUAL: direction_unknown"))
        self.assertIsNone(derive_account_fix(None))


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed",
)
class ExpressAccountFixRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401
        from routes import erp_express_account_routes as erp_routes  # noqa: F401

        cls.app_module = app
        cls.erp_routes = erp_routes

    def _client(self):
        from fastapi.testclient import TestClient

        return TestClient(self.app_module.app)

    def _endpoint(self, reported=True):
        cfg = {"account_set": "DATAT"}
        if reported:
            cfg["reported_accounts"] = [
                {"code": "41-01-00-00", "name": "รายได้"},
                {"code": "11-02-01-00", "name": "ลูกหนี้"},
                {"code": "11-05-04-02", "name": "ภาษีขาย"},
            ]
        return {"id": "ep-1", "adapter": "express", "config": cfg}

    def _run(self, body, *, reported=True, push_result=None, update_ep=None):
        app = self.app_module
        erp_routes = self.erp_routes
        log_row = {"id": "log-1", "status": "manual", "history_id": "h-1", "endpoint_id": "ep-1"}
        push_result = push_result or {
            "success": False,
            "error_msg": "EXPRESS_QUEUED",
            "http_status": 202,
            "elapsed_ms": 5,
            "request_body": {"adapter": "express"},
        }
        update_ep = update_ep if update_ep is not None else MagicMock(return_value=True)
        push_mock = MagicMock(return_value=push_result)
        with (
            patch.object(erp_routes, "get_current_user_from_request", return_value={"id": "u"}),
            patch.object(erp_routes, "_check_push_access", return_value=None),
            patch.object(erp_routes, "_tid", return_value="t-1"),
            patch.object(app.db, "get_push_log_detail", return_value=log_row),
            patch.object(app.db, "get_erp_endpoint", return_value=self._endpoint(reported)),
            patch.object(app.db, "get_ocr_history_detail", return_value={"id": "h-1"}),
            patch.object(app.db, "update_erp_endpoint", update_ep),
            patch.object(app.db, "increment_retry_count", MagicMock(return_value=2)),
            patch.object(app.db, "update_log_status_after_retry", MagicMock()),
            patch.object(app.db, "update_endpoint_stats", MagicMock()),
            patch.object(app.db, "update_history_push_status", MagicMock()),
            patch.object(_erp, "push_to_endpoint", push_mock),
        ):
            with self._client() as client:
                r = client.post("/api/erp/logs/log-1/express-account-fix", json=body)
        return r, push_mock, update_ep

    def test_one_shot_repush_no_persist(self):
        r, push_mock, update_ep = self._run({"accounts": {"revenue_acc": "41-01-00-00"}})
        self.assertEqual(r.status_code, 200, r.text)
        b = r.json()
        self.assertEqual(b["status"], "pending")
        self.assertTrue(b["ok"])
        self.assertFalse(b["remembered"])
        update_ep.assert_not_called()  # remember=False → 不写 config
        # 覆盖科目进了重推用的 endpoint config
        pushed_cfg = push_mock.call_args.args[0]["config"]
        self.assertEqual(pushed_cfg["revenue_acc"], "41-01-00-00")

    def test_remember_persists_config(self):
        r, push_mock, update_ep = self._run(
            {"accounts": {"revenue_acc": "41-01-00-00"}, "remember": True}
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["remembered"])
        update_ep.assert_called_once()
        cfg = update_ep.call_args.kwargs["config"]
        self.assertEqual(cfg["revenue_acc"], "41-01-00-00")

    def test_account_not_in_chart_rejected(self):
        r, push_mock, _ = self._run({"accounts": {"revenue_acc": "99-99-99-99"}})
        self.assertEqual(r.status_code, 400, r.text)
        push_mock.assert_not_called()  # 白名单拦下 · 不重推

    def test_no_chart_skips_whitelist(self):
        # 账套没上报科目表 → 跳过校验,允许重推。
        r, push_mock, _ = self._run({"accounts": {"revenue_acc": "41-01-00-00"}}, reported=False)
        self.assertEqual(r.status_code, 200, r.text)
        push_mock.assert_called_once()

    def test_empty_accounts_rejected(self):
        r, push_mock, _ = self._run({"accounts": {}})
        self.assertEqual(r.status_code, 400, r.text)
        push_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
