# -*- coding: utf-8 -*-
"""POS 信封层守门测试(POS 项目 · PO-A1 · docs/pos/04 §0)。

锁定:
  1. ok() 成功信封形态 · data 缺省空对象(前端永远能读 body.data)
  2. PosError 渲染成 {"ok": false, "error": {"code", "message_key"}} + 对应 HTTP 码
  3. detail 可选透传;无 detail 不漏字段
  4. pos_auth 把鉴权 HTTPException 转成 PosError(保留原 code)
  5. assert_module_enabled 关模块 → pos.module_disabled(403)
"""

import asyncio
import json
import unittest

from fastapi import HTTPException

from core import pos_api
from core.pos_api import PosError, ok


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


class OkEnvelopeTests(unittest.TestCase):
    def test_ok_wraps_data(self):
        self.assertEqual(ok({"a": 1}), {"ok": True, "data": {"a": 1}})

    def test_ok_defaults_to_empty_object(self):
        self.assertEqual(ok(), {"ok": True, "data": {}})
        self.assertEqual(ok(None), {"ok": True, "data": {}})


class PosErrorHandlerTests(unittest.TestCase):
    def _render(self, exc):
        resp = _run(pos_api._pos_error_handler(None, exc))
        return resp.status_code, json.loads(bytes(resp.body))

    def test_renders_failure_envelope(self):
        status, body = self._render(PosError("pos.out_of_stock", 409))
        self.assertEqual(status, 409)
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"]["code"], "pos.out_of_stock")
        self.assertEqual(body["error"]["message_key"], "pos.out_of_stock")
        self.assertNotIn("detail", body["error"])

    def test_default_http_status_is_400(self):
        status, _ = self._render(PosError("pos.line_invalid"))
        self.assertEqual(status, 400)

    def test_detail_passed_through_when_present(self):
        _, body = self._render(PosError("pos.out_of_stock", 409, detail="coke x2"))
        self.assertEqual(body["error"]["detail"], "coke x2")


class PosAuthTests(unittest.TestCase):
    def test_translates_http_exception_to_pos_error(self):
        # pos_auth lazily imports get_current_user_from_request from core.auth — patch there.
        import core.auth as core_auth

        def _boom(_request):
            raise HTTPException(status_code=401, detail="auth.invalid_token")

        saved = core_auth.get_current_user_from_request
        core_auth.get_current_user_from_request = _boom
        try:
            with self.assertRaises(PosError) as ctx:
                pos_api.pos_auth(object())
            self.assertEqual(ctx.exception.code, "auth.invalid_token")
            self.assertEqual(ctx.exception.http_status, 401)
        finally:
            core_auth.get_current_user_from_request = saved


class AssertModuleEnabledTests(unittest.TestCase):
    def test_disabled_module_raises_module_disabled(self):
        from services.modules import store

        saved = store.is_enabled
        store.is_enabled = lambda cur, *, tenant_id, module_key: False

        import contextlib

        from core import db

        @contextlib.contextmanager
        def _fake_cursor(tenant_id=None, bypass=False, commit=False):
            yield object()

        saved_cursor = db.get_cursor_rls
        db.get_cursor_rls = _fake_cursor
        try:
            with self.assertRaises(PosError) as ctx:
                pos_api.assert_module_enabled("t-1", "pos")
            self.assertEqual(ctx.exception.code, "pos.module_disabled")
            self.assertEqual(ctx.exception.http_status, 403)
        finally:
            store.is_enabled = saved
            db.get_cursor_rls = saved_cursor

    def test_enabled_module_passes(self):
        from services.modules import store

        saved = store.is_enabled
        store.is_enabled = lambda cur, *, tenant_id, module_key: True

        import contextlib

        from core import db

        @contextlib.contextmanager
        def _fake_cursor(tenant_id=None, bypass=False, commit=False):
            yield object()

        saved_cursor = db.get_cursor_rls
        db.get_cursor_rls = _fake_cursor
        try:
            pos_api.assert_module_enabled("t-1", "pos")  # 不抛即通过
        finally:
            store.is_enabled = saved
            db.get_cursor_rls = saved_cursor


if __name__ == "__main__":
    unittest.main()
