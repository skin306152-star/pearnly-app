# -*- coding: utf-8 -*-
"""core.workspace_context 单测(套账隔离 PO-0 地基)。

覆盖:请求头解析(有 / 无 / 非数字)· require fail-closed · 归属校验(命中 / 不命中)。
不用 pytest(CI 不装 · 见 memory no-pytest-tests-unittest-only)。
"""

import unittest

from fastapi import HTTPException

from core import workspace_context as wc


class _FakeHeaders:
    def __init__(self, data):
        self._d = data

    def get(self, key, default=None):
        return self._d.get(key, default)


class _FakeRequest:
    def __init__(self, headers):
        self.headers = _FakeHeaders(headers)


class _FakeCursor:
    """execute() 记下参数;fetchone() 按预置 row 返回。"""

    def __init__(self, row):
        self._row = row
        self.executed = None

    def execute(self, sql, params=None):
        self.executed = (sql, params)

    def fetchone(self):
        return self._row


class ReadWorkspaceIdTest(unittest.TestCase):
    def test_present_numeric(self):
        req = _FakeRequest({wc.WS_HEADER: "42"})
        self.assertEqual(wc.read_workspace_id(req), 42)

    def test_present_with_whitespace(self):
        req = _FakeRequest({wc.WS_HEADER: "  7 "})
        self.assertEqual(wc.read_workspace_id(req), 7)

    def test_absent(self):
        self.assertIsNone(wc.read_workspace_id(_FakeRequest({})))

    def test_non_numeric(self):
        self.assertIsNone(wc.read_workspace_id(_FakeRequest({wc.WS_HEADER: "abc"})))


class RequireWorkspaceIdTest(unittest.TestCase):
    def test_returns_id_when_present(self):
        req = _FakeRequest({wc.WS_HEADER: "5"})
        self.assertEqual(wc.require_workspace_id(req), 5)

    def test_fail_closed_when_missing(self):
        with self.assertRaises(HTTPException) as ctx:
            wc.require_workspace_id(_FakeRequest({}))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "workspace.required")


class AssertWorkspaceInTenantTest(unittest.TestCase):
    def test_passes_when_row_found(self):
        cur = _FakeCursor(row={"?column?": 1})
        wc.assert_workspace_in_tenant(cur, tenant_id="t1", workspace_client_id=9)
        # 校验 SQL 同时按 id 与 tenant_id 过滤(防越租户)
        sql, params = cur.executed
        self.assertIn("workspace_clients", sql)
        self.assertIn("tenant_id", sql)
        self.assertEqual(params, (9, "t1"))

    def test_forbidden_when_no_row(self):
        cur = _FakeCursor(row=None)
        with self.assertRaises(HTTPException) as ctx:
            wc.assert_workspace_in_tenant(cur, tenant_id="t1", workspace_client_id=9)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "workspace.forbidden")


class WorkspaceScopeTest(unittest.TestCase):
    def test_scope_from_request_packs_fields(self):
        req = _FakeRequest({wc.WS_HEADER: "12"})
        scope = wc.scope_from_request(req, tenant_id="t1", user_id="u9")
        self.assertEqual(scope.tenant_id, "t1")
        self.assertEqual(scope.workspace_client_id, 12)
        self.assertEqual(scope.user_id, "u9")

    def test_scope_from_request_fail_closed(self):
        with self.assertRaises(HTTPException) as ctx:
            wc.scope_from_request(_FakeRequest({}), tenant_id="t1")
        self.assertEqual(ctx.exception.detail, "workspace.required")

    def test_assert_scope_delegates(self):
        scope = wc.WorkspaceScope(tenant_id="t1", workspace_client_id=3)
        cur_ok = _FakeCursor(row={"?column?": 1})
        wc.assert_scope(cur_ok, scope)  # 不抛
        cur_bad = _FakeCursor(row=None)
        with self.assertRaises(HTTPException):
            wc.assert_scope(cur_bad, scope)


if __name__ == "__main__":
    unittest.main()
