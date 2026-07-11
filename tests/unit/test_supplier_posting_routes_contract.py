# -*- coding: utf-8 -*-
"""F4 供应商过账档案能力层路由单测(routes/supplier_posting_routes.py)。

钉死:GET/PUT/DELETE 挂对权限码(读=doc.view、写=supplier.manage)· PUT 值域外 422 ·
PUT 一律 source="user_rule"(client 传不了别的值,schema 没暴露 source 字段)· 税号入参统一
clean_tax_id 清洗后才进 DAL(preflight/回流同款清洗,带空格/连字符也命中同一行)· DELETE 幂等
no-op(删不存在的税号不报错,与 purchase_config_routes 的 DELETE /expense-rules 同惯例)。
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import unittest
from unittest import mock

from core.pos_api import PosError
from routes import supplier_posting_routes as routes_mod

TAX_RAW = "010-756-1000013"
TAX_CLEAN = "0107561000013"


def _run(coro):
    return asyncio.run(coro)


@contextlib.contextmanager
def _cm(cur):
    yield cur


class _FakeCur:
    """够用的假游标:INSERT ON CONFLICT(upsert)+ SELECT ANY(get_profiles 单行回读)。

    与 tests/unit/test_supplier_posting.py 的 _FakeCur 同构(独立小副本,不跨测试文件借私有类)。
    """

    def __init__(self, rows=None):
        self.rows = {(r["tenant_id"], r["ws"], r["seller_tax_id"]): dict(r) for r in (rows or [])}
        self._res: list = []

    def execute(self, sql, params):
        s = " ".join(sql.split())
        if s.startswith("SELECT"):
            tenant_id, ws, tax_ids = params
            self._res = [
                r
                for (t, w, tax), r in self.rows.items()
                if t == tenant_id and w == ws and tax in tax_ids
            ]
        elif s.startswith("INSERT INTO supplier_posting_profiles"):
            tenant_id, ws, tax, payment_val, item_type_val, source, raw_payment, raw_item = params
            key = (tenant_id, ws, tax)
            existing = self.rows.get(key)
            if existing is None:
                self.rows[key] = {
                    "tenant_id": tenant_id,
                    "ws": ws,
                    "seller_tax_id": tax,
                    "default_payment": payment_val,
                    "default_item_type": item_type_val,
                    "source": source,
                }
            elif existing["source"] != "user_rule" or source == "user_rule":
                if raw_payment is not None:
                    existing["default_payment"] = payment_val
                if raw_item is not None:
                    existing["default_item_type"] = item_type_val
                existing["source"] = source
        else:
            raise AssertionError(f"unexpected SQL: {s}")

    def fetchall(self):
        return list(self._res)


class RouteWiringTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in routes_mod.router.routes:
            for m in getattr(r, "methods", set()) or set():
                got.add((m, r.path))
        self.assertEqual(
            got,
            {
                ("GET", "/api/purchase/supplier-profiles"),
                ("PUT", "/api/purchase/supplier-profiles/{seller_tax_id}"),
                ("DELETE", "/api/purchase/supplier-profiles/{seller_tax_id}"),
            },
        )

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/purchase/supplier-profiles/{seller_tax_id}", paths)

    def test_permission_codes_wired(self):
        src = inspect.getsource(routes_mod.api_list_supplier_profiles)
        self.assertIn('auth_member(request, "purchase.doc.view")', src)
        for fn in (routes_mod.api_upsert_supplier_profile, routes_mod.api_delete_supplier_profile):
            self.assertIn('auth_member(request, "purchase.supplier.manage")', inspect.getsource(fn))

    def test_not_gated_on_pearnly_ai_m1(self):
        # 能力与壳分家铁则:不许挂 authorize_pearnly_ai / pearnly_ai_m1_enabled_for(闸群共享鉴权
        # 见 core/route_helpers.py)。模块级 docstring 提这个名字做说明是合理的,不算违规,
        # 只检真正的调用点(函数体源码,不含模块 docstring)。
        for fn in (
            routes_mod.api_list_supplier_profiles,
            routes_mod.api_upsert_supplier_profile,
            routes_mod.api_delete_supplier_profile,
        ):
            src = inspect.getsource(fn)
            self.assertNotIn("authorize_pearnly_ai", src)
            self.assertNotIn("pearnly_ai_m1_enabled_for", src)
        self.assertNotIn("authorize_pearnly_ai", dir(routes_mod))
        self.assertNotIn("pearnly_ai_m1_enabled_for", dir(routes_mod))

    def test_payment_and_item_type_values_share_posting_manual_source(self):
        # 422 值域集必须同源 import,不是另抄一份常量。
        from services.ocr_history import posting_manual

        self.assertIs(routes_mod._PAYMENT_VALUES, posting_manual._PAYMENT_VALUES)
        self.assertIs(routes_mod._ITEM_TYPE_VALUES, posting_manual._ITEM_TYPE_VALUES)


class _RouteTestBase(unittest.TestCase):
    def _patch_auth(self, tid="t1", ws=7):
        patches = [
            mock.patch.object(routes_mod, "auth_member", return_value=({"id": "u1"}, tid)),
            mock.patch.object(routes_mod, "gate", return_value=None),
            mock.patch.object(routes_mod, "resolve_ws", return_value=ws),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)


class ListRouteTests(_RouteTestBase):
    def test_limit_forwarded_to_dal(self):
        self._patch_auth()
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(mock.Mock())
        ):
            with mock.patch.object(
                routes_mod.sp_svc, "list_profiles_with_supplier_names", return_value=[]
            ) as m:
                _run(
                    routes_mod.api_list_supplier_profiles(
                        mock.Mock(), workspace_client_id=None, limit=5
                    )
                )
        _, kwargs = m.call_args
        self.assertEqual(kwargs["limit"], 5)
        self.assertEqual(kwargs["tenant_id"], "t1")
        self.assertEqual(kwargs["workspace_client_id"], 7)

    def test_supplier_name_passthrough_to_response(self):
        # Z3-b:GET 列表响应每行带 supplier_name(读侧富化,查不到给 None)。
        self._patch_auth()
        rows = [{"seller_tax_id": "0107561000013", "supplier_name": "冰厂"}]
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(mock.Mock())
        ):
            with mock.patch.object(
                routes_mod.sp_svc, "list_profiles_with_supplier_names", return_value=rows
            ):
                resp = _run(
                    routes_mod.api_list_supplier_profiles(
                        mock.Mock(), workspace_client_id=None, limit=None
                    )
                )
        self.assertEqual(resp["data"]["profiles"][0]["supplier_name"], "冰厂")


class UpsertRouteTests(_RouteTestBase):
    def test_invalid_payment_value_raises_422(self):
        self._patch_auth()
        req = routes_mod.SupplierProfileIn(default_payment="maybe")
        with mock.patch.object(routes_mod.sp_svc, "upsert_profile") as m:
            with self.assertRaises(PosError) as ctx:
                _run(routes_mod.api_upsert_supplier_profile(TAX_CLEAN, req, mock.Mock()))
        self.assertEqual(ctx.exception.http_status, 422)
        m.assert_not_called()

    def test_invalid_item_type_value_raises_422(self):
        self._patch_auth()
        req = routes_mod.SupplierProfileIn(default_item_type="services")
        with mock.patch.object(routes_mod.sp_svc, "upsert_profile") as m:
            with self.assertRaises(PosError) as ctx:
                _run(routes_mod.api_upsert_supplier_profile(TAX_CLEAN, req, mock.Mock()))
        self.assertEqual(ctx.exception.http_status, 422)
        m.assert_not_called()

    def test_malformed_tax_id_raises_422_before_dal_call(self):
        self._patch_auth()
        req = routes_mod.SupplierProfileIn(default_payment="cash")
        with mock.patch.object(routes_mod.sp_svc, "upsert_profile") as m:
            with self.assertRaises(PosError) as ctx:
                _run(routes_mod.api_upsert_supplier_profile("not-a-tax-id", req, mock.Mock()))
        self.assertEqual(ctx.exception.http_status, 422)
        m.assert_not_called()

    def test_always_writes_source_user_rule(self):
        self._patch_auth()
        req = routes_mod.SupplierProfileIn(default_payment="cash")
        cur = mock.Mock()
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(cur)
        ):
            with mock.patch.object(routes_mod.sp_svc, "upsert_profile") as m:
                with mock.patch.object(routes_mod.sp_svc, "get_profiles", return_value={}):
                    _run(routes_mod.api_upsert_supplier_profile(TAX_CLEAN, req, mock.Mock()))
        self.assertEqual(m.call_args.kwargs["source"], "user_rule")

    def test_dirty_tax_id_cleaned_before_dal_call(self):
        self._patch_auth()
        req = routes_mod.SupplierProfileIn(default_payment="cash")
        cur = mock.Mock()
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(cur)
        ):
            with mock.patch.object(routes_mod.sp_svc, "upsert_profile") as m:
                with mock.patch.object(routes_mod.sp_svc, "get_profiles", return_value={}):
                    _run(routes_mod.api_upsert_supplier_profile(f" {TAX_RAW} ", req, mock.Mock()))
        self.assertEqual(m.call_args.kwargs["seller_tax_id"], TAX_CLEAN)

    def test_omitted_field_forwarded_as_none_not_changed(self):
        self._patch_auth()
        req = routes_mod.SupplierProfileIn(default_payment="cash")  # item_type 缺省不传
        cur = mock.Mock()
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(cur)
        ):
            with mock.patch.object(routes_mod.sp_svc, "upsert_profile") as m:
                with mock.patch.object(routes_mod.sp_svc, "get_profiles", return_value={}):
                    _run(routes_mod.api_upsert_supplier_profile(TAX_CLEAN, req, mock.Mock()))
        self.assertEqual(m.call_args.kwargs["default_payment"], "cash")
        self.assertIsNone(m.call_args.kwargs["default_item_type"])

    def test_correction_backflow_cannot_override_route_created_user_rule(self):
        """端到端回归:PUT(真 DAL,不 mock)建 user_rule 行后,模拟复核屏回流(correction)
        直接调 DAL 想覆盖同一行——必须覆盖不了(supplier_posting.upsert_profile 既有保证)。"""
        self._patch_auth()
        req = routes_mod.SupplierProfileIn(default_payment="cash")
        cur = _FakeCur()
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(cur)
        ):
            _run(routes_mod.api_upsert_supplier_profile(TAX_CLEAN, req, mock.Mock()))
        row = cur.rows[("t1", 7, TAX_CLEAN)]
        self.assertEqual(row["source"], "user_rule")
        self.assertEqual(row["default_payment"], "cash")

        routes_mod.sp_svc.upsert_profile(
            cur,
            tenant_id="t1",
            workspace_client_id=7,
            seller_tax_id=TAX_CLEAN,
            default_payment="credit",
            source="correction",
        )
        row = cur.rows[("t1", 7, TAX_CLEAN)]
        self.assertEqual(row["source"], "user_rule")
        self.assertEqual(row["default_payment"], "cash")  # correction 没能覆盖


class DeleteRouteTests(_RouteTestBase):
    def test_missing_row_returns_ok_deleted_false_not_404(self):
        self._patch_auth()
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(mock.Mock())
        ):
            with mock.patch.object(routes_mod.sp_svc, "delete_profile", return_value=False):
                resp = _run(
                    routes_mod.api_delete_supplier_profile(
                        TAX_CLEAN, mock.Mock(), workspace_client_id=None
                    )
                )
        self.assertEqual(resp, {"ok": True, "data": {"deleted": False}})

    def test_repeated_delete_never_raises(self):
        self._patch_auth()
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(mock.Mock())
        ):
            with mock.patch.object(routes_mod.sp_svc, "delete_profile", side_effect=[True, False]):
                first = _run(
                    routes_mod.api_delete_supplier_profile(
                        TAX_CLEAN, mock.Mock(), workspace_client_id=None
                    )
                )
                second = _run(
                    routes_mod.api_delete_supplier_profile(
                        TAX_CLEAN, mock.Mock(), workspace_client_id=None
                    )
                )
        self.assertEqual(first["data"]["deleted"], True)
        self.assertEqual(second["data"]["deleted"], False)

    def test_dirty_tax_id_cleaned_before_dal_call(self):
        self._patch_auth()
        with mock.patch.object(
            routes_mod.db, "get_cursor_rls", side_effect=lambda *a, **k: _cm(mock.Mock())
        ):
            with mock.patch.object(routes_mod.sp_svc, "delete_profile", return_value=True) as m:
                _run(
                    routes_mod.api_delete_supplier_profile(
                        f" {TAX_RAW} ", mock.Mock(), workspace_client_id=None
                    )
                )
        self.assertEqual(m.call_args.kwargs["seller_tax_id"], TAX_CLEAN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
