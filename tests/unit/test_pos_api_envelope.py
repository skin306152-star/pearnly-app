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


class ValidationHandlerScopeTests(unittest.TestCase):
    """POS 路径的请求体校验错误走信封;非 POS 路径委托 FastAPI 默认。"""

    class _Req:
        def __init__(self, path):
            self.url = type("U", (), {"path": path})()

    def _render_pos(self, path):
        from fastapi.exceptions import RequestValidationError

        exc = RequestValidationError([])
        resp = _run(pos_api._pos_validation_handler(self._Req(path), exc))
        return resp.status_code, json.loads(bytes(resp.body))

    def test_inventory_path_enveloped(self):
        status, body = self._render_pos("/api/inventory/in")
        self.assertEqual(status, 422)
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"]["code"], "pos.line_invalid")

    def test_pos_path_enveloped(self):
        _status, body = self._render_pos("/api/pos/sales")
        self.assertEqual(body["error"]["code"], "pos.line_invalid")

    def test_modules_path_enveloped(self):
        _status, body = self._render_pos("/api/me/modules")
        self.assertFalse(body["ok"])

    def test_non_pos_path_delegates_to_default(self):
        # 非 POS 路径不应被信封接管(委托 FastAPI 默认 · 返回 {detail:...} 非 {ok:...})
        _status, body = self._render_pos("/api/sales/products")
        self.assertNotIn("ok", body)
        self.assertIn("detail", body)


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
    """用调用方传入的游标(不另起连接);开/关分别通过/抛 module_disabled。"""

    def test_disabled_module_raises_module_disabled(self):
        from services.modules import store

        saved = store.is_enabled
        store.is_enabled = lambda cur, *, tenant_id, module_key: False
        try:
            with self.assertRaises(PosError) as ctx:
                pos_api.assert_module_enabled(object(), "t-1", "pos")
            self.assertEqual(ctx.exception.code, "pos.module_disabled")
            self.assertEqual(ctx.exception.http_status, 403)
        finally:
            store.is_enabled = saved

    def test_enabled_module_passes(self):
        from services.modules import store

        saved = store.is_enabled
        store.is_enabled = lambda cur, *, tenant_id, module_key: True
        try:
            pos_api.assert_module_enabled(object(), "t-1", "pos")  # 不抛即通过
        finally:
            store.is_enabled = saved


if __name__ == "__main__":
    unittest.main()
