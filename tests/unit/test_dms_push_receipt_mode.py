# -*- coding: utf-8 -*-
"""/api/dms/id-card/push 回执诚实性契约。

服务层会把 create 幂等/撞码转成覆盖(返回 mode='update'),路由层必须照实转出:
回执与 erp_push_logs 都说「更新」。谎称新建 = 老板按成功页以为多了个新客,
实际是覆盖了老客户档案。服务层没给 mode(失败路径)才回落请求里的 mode。
"""

import asyncio
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

import routes.dms_routes as dms  # noqa: E402

_USER = {"id": "u1", "tenant_id": "t1", "entry": "dms"}
_FIELDS = {"people_id": "1234567890123", "name": "สมชาย ใจดี"}


class _FakeRequest:
    def __init__(self, body):
        self._body = body

    async def json(self):
        return self._body


def _push(body, service_result):
    """跑一次 push 端点,返回 (响应, 写进台账的 meta)。"""
    captured = {}

    def _insert_push_log(*args, **kwargs):
        captured["meta"] = next(a for a in args if isinstance(a, dict))
        return "log-1"

    with (
        mock.patch.object(dms, "_authorize", return_value=_USER),
        mock.patch.object(dms, "_resolve_dms_endpoint", return_value={"id": "ep1"}),
        mock.patch.object(
            dms._dms_intake, "push_idcard_fields_mrerp_dms", return_value=service_result
        ),
        mock.patch.object(dms.db, "insert_push_log", side_effect=_insert_push_log),
    ):
        resp = asyncio.run(dms.dms_id_card_push(_FakeRequest(body)))
    return resp, captured.get("meta")


class PushReceiptModeTests(unittest.TestCase):
    def test_service_update_overrides_requested_create(self):
        resp, meta = _push(
            {"mode": "create", "fields": _FIELDS},
            {"ok": True, "success": True, "customer_id": "95", "mode": "update"},
        )
        self.assertEqual(resp["dms_push"]["mode"], "update")
        self.assertEqual(meta["mode"], "update")

    def test_requested_mode_kept_when_service_silent(self):
        resp, meta = _push(
            {"mode": "create", "fields": _FIELDS},
            {"ok": False, "success": False, "error_code": "ERR_DMS_AUTH"},
        )
        self.assertFalse(resp["ok"])
        self.assertEqual(resp["dms_push"]["mode"], "create")
        self.assertEqual(meta["mode"], "create")

    def test_real_create_still_reports_create(self):
        resp, meta = _push(
            {"mode": "create", "fields": _FIELDS},
            {"ok": True, "success": True, "customer_id": "96", "mode": "create"},
        )
        self.assertEqual(resp["dms_push"]["mode"], "create")
        self.assertEqual(meta["mode"], "create")

    def test_update_request_passes_through(self):
        resp, _meta = _push(
            {"mode": "update", "customer_id": "95", "fields": _FIELDS},
            {"ok": True, "success": True, "customer_id": "95", "mode": "update"},
        )
        self.assertEqual(resp["dms_push"]["mode"], "update")


if __name__ == "__main__":
    unittest.main()
