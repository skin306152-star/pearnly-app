#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守门测试 · 失败卡补选过账去向(没声明 → 留人工的票就地补选一次 → 写回票上 → 重推)。

钉住三件事:
  1. 补选走的是 mapper 同一个 normalize —— 认不出的值一律 400,绝不静默当成 stock
     (错记库存会真扣客户库存并结转 COGS,Express 里不可逆);
  2. 声明写回 ocr_history 而不是只当这一次的入参 —— 否则这次点通了,下一次自动重试
     还会 escalate(推送四条腿都读票上那一列);
  3. 重推真把 posting_kind 传下去,且更新原日志行(不新建)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core import db  # noqa: E402,F401
from services.erp import erp_push as _erp  # noqa: E402


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed",
)
class ExpressPostingKindRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401
        from routes import erp_express_account_routes as erp_routes

        cls.app_module = app
        cls.erp_routes = erp_routes

    def _run(self, body, *, adapter="express", write_ok=True):
        app = self.app_module
        erp_routes = self.erp_routes
        log_row = {"id": "log-1", "status": "manual", "history_id": "h-1", "endpoint_id": "ep-1"}
        endpoint = {"id": "ep-1", "adapter": adapter, "config": {"account_set": "DATAT"}}
        push_result = {
            "success": False,
            "error_msg": "EXPRESS_QUEUED",
            "http_status": 202,
            "elapsed_ms": 5,
            "request_body": {"adapter": "express"},
        }
        write_mock = MagicMock(return_value=write_ok)
        push_mock = MagicMock(return_value=push_result)
        with (
            patch.object(erp_routes, "get_current_user_from_request", return_value={"id": "u"}),
            patch.object(erp_routes, "_check_push_access", return_value=None),
            patch.object(erp_routes, "_tid", return_value="t-1"),
            patch.object(app.db, "get_push_log_detail", return_value=log_row),
            patch.object(app.db, "get_erp_endpoint", return_value=endpoint),
            patch.object(app.db, "update_history_posting_kind", write_mock),
            patch.object(app.db, "get_ocr_history_detail", return_value={"id": "h-1"}),
            patch.object(app.db, "classify_push_status", return_value="pending"),
            patch.object(app.db, "counts_as_endpoint_success", return_value=True),
            patch.object(app.db, "increment_retry_count", MagicMock(return_value=1)),
            patch.object(app.db, "update_log_status_after_retry", MagicMock()),
            patch.object(app.db, "update_endpoint_stats", MagicMock()),
            patch.object(app.db, "update_history_push_status", MagicMock()),
            patch.object(_erp, "push_to_endpoint", push_mock),
        ):
            from fastapi.testclient import TestClient

            with TestClient(app.app) as client:
                r = client.post("/api/erp/logs/log-1/express-posting-kind", json=body)
        return r, write_mock, push_mock

    def test_stock_writes_declaration_then_repushes(self):
        r, write_mock, push_mock = self._run({"posting_kind": "stock"})
        self.assertEqual(r.status_code, 200, r.text)
        b = r.json()
        self.assertTrue(b["ok"])
        self.assertEqual(b["posting_kind"], "stock")
        self.assertEqual(b["status"], "pending")
        # 声明跟着票走:写回 history 那一列,四条推送腿下次都读得到。
        self.assertEqual(write_mock.call_args.args[:3], ("h-1", "stock", "u"))
        # 本次重推也真带上,不指望写回后再读一遍才生效。
        self.assertEqual(push_mock.call_args.kwargs.get("posting_kind"), "stock")

    def test_service_accepted_case_insensitive(self):
        r, write_mock, push_mock = self._run({"posting_kind": " Service "})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["posting_kind"], "service")
        self.assertEqual(push_mock.call_args.kwargs.get("posting_kind"), "service")

    def test_unknown_kind_rejected_not_silently_stock(self):
        for bad in ("", "goods", "STOCKS", "1"):
            with self.subTest(bad=bad):
                r, write_mock, push_mock = self._run({"posting_kind": bad})
                self.assertEqual(r.status_code, 400, r.text)
                write_mock.assert_not_called()
                push_mock.assert_not_called()

    def test_history_gone_does_not_repush(self):
        r, _, push_mock = self._run({"posting_kind": "stock"}, write_ok=False)
        self.assertEqual(r.status_code, 404, r.text)
        push_mock.assert_not_called()

    def test_non_express_rejected(self):
        r, write_mock, push_mock = self._run({"posting_kind": "stock"}, adapter="mrerp")
        self.assertEqual(r.status_code, 400, r.text)
        write_mock.assert_not_called()
        push_mock.assert_not_called()


class PostingKindWriteContractTests(unittest.TestCase):
    """update_history_posting_kind 窄更新契约(mock cursor · 不连库)。"""

    class _Cur:
        def __init__(self):
            self.rowcount = 1
            self.sql = ""
            self.params = None

        def execute(self, sql, params=None):
            self.sql = sql
            self.params = params

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _patch(self, cur):
        from contextlib import contextmanager

        from services.ocr_history import posting_kind_store

        @contextmanager
        def _fake(**kw):
            yield cur

        return patch.object(posting_kind_store.db, "get_cursor_rls", lambda **kw: _fake(**kw))

    def _write(self, tenant_id):
        from services.ocr_history import posting_kind_store

        cur = self._Cur()
        with self._patch(cur):
            ok = posting_kind_store.update_history_posting_kind("h1", "stock", "u1", tenant_id)
        return ok, cur

    def test_writes_only_that_column(self):
        ok, cur = self._write("t1")
        self.assertTrue(ok)
        self.assertIn("posting_kind = %s", cur.sql)
        # pages 不能碰:走 update_ocr_history_pages 会触发反馈捕获、冒充用户编辑 bump edit_count。
        self.assertNotIn("pages", cur.sql)
        self.assertEqual(cur.params[0], "stock")

    def test_tenant_predicate_in_sql_not_only_rls(self):
        _, cur = self._write("t1")
        self.assertIn("tenant_id = %s", cur.sql)
        self.assertEqual(cur.params[2], "t1")

    def test_falls_back_to_user_scope_without_tenant(self):
        _, cur = self._write(None)
        self.assertIn("user_id = %s", cur.sql)
        self.assertNotIn("tenant_id", cur.sql)
        self.assertEqual(cur.params[2], "u1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
