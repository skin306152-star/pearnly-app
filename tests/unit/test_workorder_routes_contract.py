# -*- coding: utf-8 -*-
"""工单制路由契约 + fail-closed 守门(routes/workorder_routes.py · M1-B1 + C3 四权分立)。

锁定:①端点按 path+method 注册且挂进 app;②M1 闸关时任一端点 404(对存量用户路由等于
不存在);③闸开 + 鉴权后开单外形正确;④非法裁决 → 422、item 不属该单 → 404;⑤C3:每个
端点传给 require_perm 的 tax.filing.* 细码与方案闸点表逐一对齐(PermCodeWiringTests)。
交付物清单/下载(deliverables)与月度报表下载(financials/download)已并进
routes/workorder_financials_routes.py,守门在 test_workorder_financials_routes_contract.py。
"""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from core import route_helpers
from routes.workorder_routes import router as workorder_router
from tests.unit._route_contract_fakes import FakeCur as _Cur
from tests.unit._route_contract_fakes import FakeDB as _FakeDB
from tests.unit._route_contract_fakes import route_set as _route_set


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        rs = _route_set(workorder_router)
        expected = {
            ("POST", "/api/workorder/orders"),
            ("GET", "/api/workorder/orders"),
            ("GET", "/api/workorder/orders/{work_order_id}"),
            ("POST", "/api/workorder/orders/{work_order_id}/run"),
            ("POST", "/api/workorder/orders/{work_order_id}/decisions"),
            ("POST", "/api/workorder/orders/{work_order_id}/sales-summary"),
            ("POST", "/api/workorder/orders/{work_order_id}/materials"),
            ("GET", "/api/workorder/orders/{work_order_id}/items/{item_id}/image"),
            ("POST", "/api/workorder/orders/{work_order_id}/review"),
            ("POST", "/api/workorder/orders/{work_order_id}/archive"),
            ("GET", "/api/workorder/orders/{work_order_id}/verify"),
            ("POST", "/api/workorder/orders/{work_order_id}/receipt"),
        }
        self.assertTrue(expected.issubset(rs), f"缺路由: {expected - rs}")


class RouterMountedTests(unittest.TestCase):
    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/workorder/orders", paths)


_USER = {"id": "u1", "tenant_id": "t-1"}


class GateClosedTests(unittest.IsolatedAsyncioTestCase):
    async def test_gate_closed_hides_route_as_404(self):
        from routes import workorder_routes as wr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.list_orders(mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)


class CreateOrderTests(unittest.IsolatedAsyncioTestCase):
    async def test_open_order_returns_shape(self):
        from routes import workorder_routes as wr

        wo = {
            "id": "wo-1",
            "workspace_client_id": 7,
            "period": "2569-05",
            "intent": "monthly_vat",
            "status": "collecting",
            "current_step": None,
        }
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur(fetch=(1,)))),
            mock.patch.object(wr.api, "open_order", return_value=wo),
        ):
            out = await wr.create_order(
                wr.OrderCreate(workspace_client_id=7, period="2569-05"), mock.Mock()
            )
        self.assertEqual(out["id"], "wo-1")
        self.assertEqual(out["status"], "collecting")

    async def test_unowned_workspace_is_404(self):
        from routes import workorder_routes as wr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "db", _FakeDB(_Cur(fetch=None))),  # 归属查询空 = 不属本租户
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.create_order(
                    wr.OrderCreate(workspace_client_id=99, period="2569-05"), mock.Mock()
                )
        self.assertEqual(ctx.exception.status_code, 404)


class RunLeaseRouteTests(unittest.IsolatedAsyncioTestCase):
    """/run 防重入:抢不到租约 → 409;抢到 → queued 且把 owner 交后台 advance。"""

    def _patches(self, wr):
        return (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            # 推进原语下沉后事务在 runner 层开(MC2-A1),假库也要打在 runner 上。
            mock.patch.object(wr.runner, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "ensure_runtime", return_value=None),
            mock.patch.object(
                wr.store,
                "get_work_order",
                return_value={"workspace_client_id": 7, "status": "collecting"},
            ),
        )

    async def test_lease_held_returns_409(self):
        from routes import workorder_routes as wr

        with (
            mock.patch.object(wr.store, "acquire_run_lease", return_value=False),
            mock.patch.object(wr.store, "append_event") as append,
        ):
            for p in self._patches(wr):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await wr.run_order("wo-1", mock.Mock(), mock.Mock())
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "workorder.run_in_progress")
        append.assert_not_called()  # 抢不到就不落 run_requested、不排后台

    async def test_lease_acquired_queues_advance_with_owner(self):
        from routes import workorder_routes as wr

        bg = mock.Mock()
        with (
            mock.patch.object(wr.store, "acquire_run_lease", return_value=True),
            mock.patch.object(wr.store, "append_event", return_value={"id": 1}),
        ):
            for p in self._patches(wr):
                self.enterContext(p)
            out = await wr.run_order("wo-1", mock.Mock(), bg)
        self.assertTrue(out["queued"])
        bg.add_task.assert_called_once()
        # add_task(runner.advance, tenant, wo, owner);owner 形如 run:<hex>
        args = bg.add_task.call_args[0]
        self.assertEqual(args[2], "wo-1")
        self.assertTrue(str(args[3]).startswith("run:"))


class DecisionMappingTests(unittest.IsolatedAsyncioTestCase):
    async def _call(self, decision, item_ok):
        from routes import workorder_routes as wr

        wo = {"workspace_client_id": 7}
        err = None if item_ok else wr.api.WorkOrderApiError("workorder.item_not_found")

        def _rec(*a, **k):
            if err:
                raise err
            return {"id": 5}

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "get_work_order", return_value=wo),
            mock.patch.object(wr.api, "record_decision", side_effect=_rec),
            mock.patch.object(wr, "_schedule_advance", return_value=True),
        ):
            return await wr.add_decision(
                "wo-1", wr.DecisionIn(item_id="it-1", decision=decision), mock.Mock(), mock.Mock()
            )

    async def test_valid_decision_ok(self):
        out = await self._call("face_value", item_ok=True)
        self.assertTrue(out["ok"])

    async def test_invalid_decision_maps_422(self):
        from routes import workorder_routes as wr

        wo = {"workspace_client_id": 7}
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "get_work_order", return_value=wo),
            mock.patch.object(
                wr.api,
                "record_decision",
                side_effect=wr.api.WorkOrderApiError("workorder.decision_invalid"),
            ),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.add_decision(
                    "wo-1",
                    wr.DecisionIn(item_id="it-1", decision="bogus"),
                    mock.Mock(),
                    mock.Mock(),
                )
        self.assertEqual(ctx.exception.status_code, 422)

    async def test_item_not_found_maps_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await self._call("face_value", item_ok=False)
        self.assertEqual(ctx.exception.status_code, 404)


class SalesSummaryMappingTests(unittest.IsolatedAsyncioTestCase):
    """人工填销项路由:合法落库返 ok;校验错(sales_summary_*)→ 422,其它业务错 → 404。"""

    async def _call(self, err_code=None):
        from routes import workorder_routes as wr

        wo = {"workspace_client_id": 7}

        def _rec(*a, **k):
            if err_code:
                raise wr.api.WorkOrderApiError(err_code)
            return {"id": 5}

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "get_work_order", return_value=wo),
            mock.patch.object(wr.api, "record_sales_summary", side_effect=_rec),
            mock.patch.object(wr, "_schedule_advance", return_value=True),
        ):
            return await wr.add_sales_summary(
                "wo-1",
                wr.SalesSummaryIn(sales_amount="858780.16", output_vat="60114.61", note="ยื่นเอง"),
                mock.Mock(),
                mock.Mock(),
            )

    async def test_valid_entry_ok(self):
        out = await self._call()
        self.assertTrue(out["ok"])
        self.assertEqual(out["event_id"], 5)

    async def test_invalid_amount_maps_422(self):
        with self.assertRaises(HTTPException) as ctx:
            await self._call(err_code="workorder.sales_summary_invalid")
        self.assertEqual(ctx.exception.status_code, 422)

    async def test_overlong_note_maps_422(self):
        with self.assertRaises(HTTPException) as ctx:
            await self._call(err_code="workorder.sales_summary_note_too_long")
        self.assertEqual(ctx.exception.status_code, 422)


class _FakeUpload:
    """UploadFile 替身:read(n) 尊重封顶字节数(验证路由的封顶读法,不整读)。"""

    def __init__(self, content: bytes, filename: str = "a.jpg"):
        self._content = content
        self.filename = filename
        self.read_sizes: list = []

    async def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return self._content if size < 0 else self._content[:size]


class PermCodeWiringTests(unittest.IsolatedAsyncioTestCase):
    """C3 拍板2 闸点表落地:每个端点传给 require_perm 的细码与方案表逐一对齐。_authorize
    是每个端点的第一句,只需它成功即可捕获传入的码——之后无论下游怎么炸都不影响本测试
    目的(db 一律 fake 短路,不碰真库,广播 except 吞掉必然发生的后续假数据错误)。"""

    async def _perm_code_used(self, wr, coro):
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur(fetch=(1,)))),
            mock.patch.object(wr.store, "ensure_runtime", return_value=None),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER) as perm,
            # 兜底:任何未拦到的 feature-flag 读侧(如 api.open_order 内的 pearnly_ai_m1_enabled_for)
            # 一律短路,不许真碰 DB——本测试只关心 require_perm 传的码,不关心业务后续。
            mock.patch("services.platform_settings.store.is_enabled_for_user", return_value=False),
        ):
            try:
                await coro
            except Exception:
                pass
        self.assertTrue(perm.called, "端点未走 require_perm")
        return perm.call_args[0][1]

    async def test_endpoint_perm_codes_match_gate_table(self):
        from routes import workorder_routes as wr

        cases = (
            (wr.list_orders(mock.Mock()), wr._C_VIEW),
            (wr.get_order("wo-1", mock.Mock()), wr._C_VIEW),
            (wr.get_item_image("wo-1", "it-1", mock.Mock()), wr._C_VIEW),
            (wr.verify_order("wo-1", mock.Mock()), wr._C_VIEW),
            (
                wr.create_order(
                    wr.OrderCreate(workspace_client_id=7, period="2569-05"), mock.Mock()
                ),
                wr._C_PREPARE,
            ),
            (wr.run_order("wo-1", mock.Mock(), mock.Mock()), wr._C_PREPARE),
            (
                wr.add_decision(
                    "wo-1",
                    wr.DecisionIn(item_id="it-1", decision="face_value"),
                    mock.Mock(),
                    mock.Mock(),
                ),
                wr._C_PREPARE,
            ),
            (
                wr.add_sales_summary(
                    "wo-1",
                    wr.SalesSummaryIn(sales_amount="1", output_vat="1"),
                    mock.Mock(),
                    mock.Mock(),
                ),
                wr._C_PREPARE,
            ),
            (wr.add_materials("wo-1", mock.Mock(), mock.Mock(), files=[]), wr._C_PREPARE),
            (wr.review_signoff("wo-1", wr.ReviewSignoffIn(), mock.Mock()), wr._C_REVIEW),
            (wr.archive_order("wo-1", mock.Mock()), wr._C_APPROVE),
            (
                wr.attach_receipt("wo-1", mock.Mock(), file=_FakeUpload(b"x")),
                wr._C_FILE,
            ),
        )
        for coro, expected in cases:
            with self.subTest(expected=expected):
                got = await self._perm_code_used(wr, coro)
                self.assertEqual(got, expected)


class MaterialsUploadLimitTests(unittest.IsolatedAsyncioTestCase):
    """补料上限防护:超文件数/超单文件字节 → 413 结构化码,且一字不落盘。"""

    def _patches(self, wr):
        return (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "get_work_order", return_value={"workspace_client_id": 7}),
            mock.patch.object(wr, "_schedule_advance", return_value=True),
        )

    async def test_too_many_files_maps_413(self):
        from routes import workorder_routes as wr

        files = [_FakeUpload(b"x") for _ in range(wr._MAX_MATERIAL_FILES + 1)]
        with mock.patch.object(wr.storage, "save_material") as save:
            for p in self._patches(wr):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await wr.add_materials("wo-1", mock.Mock(), mock.Mock(), files=files)
        self.assertEqual(ctx.exception.status_code, 413)
        self.assertEqual(ctx.exception.detail, "workorder.too_many_files")
        save.assert_not_called()

    async def test_oversize_file_maps_413_with_capped_read(self):
        from routes import workorder_routes as wr

        big = _FakeUpload(b"z" * (wr._MAX_MATERIAL_BYTES + 1), filename="huge.pdf")
        with mock.patch.object(wr.storage, "save_material") as save:
            for p in self._patches(wr):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await wr.add_materials("wo-1", mock.Mock(), mock.Mock(), files=[big])
        self.assertEqual(ctx.exception.status_code, 413)
        self.assertEqual(ctx.exception.detail, "workorder.file_too_large")
        # 封顶读法:只请求上限+1 字节,不整读超大文件。
        self.assertEqual(big.read_sizes, [wr._MAX_MATERIAL_BYTES + 1])
        save.assert_not_called()

    async def test_within_limits_still_registers(self):
        from routes import workorder_routes as wr

        ok_file = _FakeUpload(b"bytes", filename="a.jpg")
        with (
            mock.patch.object(wr.storage, "save_material", return_value=mock.Mock()) as save,
            mock.patch.object(
                wr.intake,
                "register_file",
                return_value={"id": "it-1", "file_ref": "/m/a.jpg"},
            ),
        ):
            for p in self._patches(wr):
                self.enterContext(p)
            out = await wr.add_materials("wo-1", mock.Mock(), mock.Mock(), files=[ok_file])
        self.assertEqual(out["count"], 1)
        save.assert_called_once()


class ArchivedReadonlyGuardTests(unittest.IsolatedAsyncioTestCase):
    """冻结(archive)后 mutating 端点结构化拒 409 archived_readonly。"""

    def _patches(self, wr, wo_status):
        return (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "ensure_runtime", return_value=None),
            mock.patch.object(
                wr.store,
                "get_work_order",
                return_value={"workspace_client_id": 7, "status": wo_status},
            ),
        )

    async def test_run_on_archived_is_409(self):
        from routes import workorder_routes as wr

        with mock.patch.object(wr.store, "acquire_run_lease") as acquire:
            for p in self._patches(wr, "archive"):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await wr.run_order("wo-1", mock.Mock(), mock.Mock())
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "workorder.archived_readonly")
        acquire.assert_not_called()  # 冻结后连租约都不抢


class ArchiveEndpointTests(unittest.IsolatedAsyncioTestCase):
    """冻结端点:成功透传状态;fail-closed 源缺失 → 409 且 detail 带 missing 点名。"""

    def _patches(self, wr):
        return (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "ensure_runtime", return_value=None),
            mock.patch.object(wr.store, "get_work_order", return_value={"workspace_client_id": 7}),
        )

    async def test_archive_success(self):
        from routes import workorder_routes as wr

        out_payload = {"status": "archive", "deliverable_version": 1, "manifest": {"item_count": 3}}
        with mock.patch.object(wr.archive, "archive_order", return_value=out_payload):
            for p in self._patches(wr):
                self.enterContext(p)
            out = await wr.archive_order("wo-1", mock.Mock())
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "archive")

    async def test_freeze_source_missing_maps_409_with_named_files(self):
        from routes import workorder_routes as wr

        err = wr.api.WorkOrderApiError(
            "workorder.freeze_source_missing", context={"missing": ["gone.jpg"]}
        )
        with mock.patch.object(wr.archive, "archive_order", side_effect=err):
            for p in self._patches(wr):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await wr.archive_order("wo-1", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail["code"], "workorder.freeze_source_missing")
        self.assertEqual(ctx.exception.detail["missing"], ["gone.jpg"])


class ItemImageTests(unittest.IsolatedAsyncioTestCase):
    """item 原图端点(W3 契约 §1.2 缺口 A):只放行库里登记过且落在工单目录内的 file_ref。"""

    def _patches(self, wr):
        return (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "get_work_order", return_value={"workspace_client_id": 7}),
        )

    async def test_item_without_file_ref_is_404_without_disk_touch(self):
        from routes import workorder_routes as wr

        with (
            mock.patch.object(wr.store, "get_item", return_value={"id": "it-1", "file_ref": None}),
            mock.patch.object(wr.storage, "resolve_within_order") as resolve,
        ):
            for p in self._patches(wr):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await wr.get_item_image("wo-1", "it-1", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "workorder.item_image_not_found")
        resolve.assert_not_called()

    async def test_file_outside_order_dir_is_404(self):
        from routes import workorder_routes as wr

        with (
            mock.patch.object(
                wr.store, "get_item", return_value={"id": "it-1", "file_ref": "/etc/passwd"}
            ),
            mock.patch.object(wr.storage, "resolve_within_order", return_value=None) as resolve,
        ):
            for p in self._patches(wr):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await wr.get_item_image("wo-1", "it-1", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "workorder.item_image_not_found")
        resolve.assert_called_once_with("t-1", "wo-1", "/etc/passwd")

    async def test_valid_image_served_with_extension_media_type(self):
        import tempfile
        from pathlib import Path

        from routes import workorder_routes as wr

        req = mock.Mock()
        req.headers = {"X-Forwarded-For": "1.2.3.4", "User-Agent": "ua"}
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "IMG_2647.jpg"
            img.write_bytes(b"jpeg-bytes")
            with (
                mock.patch.object(
                    wr.store, "get_item", return_value={"id": "it-1", "file_ref": str(img)}
                ),
                mock.patch.object(wr.storage, "resolve_within_order", return_value=img),
                mock.patch("services.audit.store.insert_operation_log") as log_mock,
            ):
                for p in self._patches(wr):
                    self.enterContext(p)
                resp = await wr.get_item_image("wo-1", "it-1", req)
        self.assertEqual(resp.media_type, "image/jpeg")
        # 密文经 storage.read_bytes 解回明文再出流(off 态=原字节);下载名进 Content-Disposition。
        self.assertEqual(resp.body, b"jpeg-bytes")
        self.assertIn("IMG_2647.jpg", resp.headers["content-disposition"])
        # ENC-b:取件恰记一条 file.material_viewed 审计(字段齐)。
        log_mock.assert_called_once()
        kw = log_mock.call_args.kwargs
        self.assertEqual(kw["action"], "file.material_viewed")
        self.assertEqual(kw["tenant_id"], "t-1")
        self.assertEqual(kw["target_id"], "it-1")

    async def test_image_view_audit_failure_is_fail_open(self):
        import tempfile
        from pathlib import Path

        from routes import workorder_routes as wr

        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "IMG_2647.jpg"
            img.write_bytes(b"jpeg-bytes")
            with (
                mock.patch.object(
                    wr.store, "get_item", return_value={"id": "it-1", "file_ref": str(img)}
                ),
                mock.patch.object(wr.storage, "resolve_within_order", return_value=img),
                mock.patch(
                    "services.audit.store.insert_operation_log", side_effect=RuntimeError("boom")
                ),
            ):
                for p in self._patches(wr):
                    self.enterContext(p)
                resp = await wr.get_item_image("wo-1", "it-1", mock.Mock())
        self.assertEqual(resp.body, b"jpeg-bytes")


class AutoAdvanceTests(unittest.IsolatedAsyncioTestCase):
    """P-7 引擎自驱:裁决/补销项/补料落库成功后端点自动排 advance,用户不必手点 /run。"""

    def _base(self, wr):
        return (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(wr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(wr, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "get_work_order", return_value={"workspace_client_id": 7}),
        )

    async def test_decision_success_schedules_advance(self):
        from routes import workorder_routes as wr

        with (
            mock.patch.object(wr.api, "record_decision", return_value={"id": 5}),
            mock.patch.object(wr, "_schedule_advance", return_value=True) as sched,
        ):
            for p in self._base(wr):
                self.enterContext(p)
            out = await wr.add_decision(
                "wo-1",
                wr.DecisionIn(item_id="it-1", decision="face_value"),
                mock.Mock(),
                mock.Mock(),
            )
        self.assertTrue(out["ok"])
        sched.assert_called_once()

    async def test_sales_summary_success_schedules_advance(self):
        from routes import workorder_routes as wr

        with (
            mock.patch.object(wr.api, "record_sales_summary", return_value={"id": 5}),
            mock.patch.object(wr, "_schedule_advance", return_value=True) as sched,
        ):
            for p in self._base(wr):
                self.enterContext(p)
            out = await wr.add_sales_summary(
                "wo-1",
                wr.SalesSummaryIn(sales_amount="1", output_vat="1"),
                mock.Mock(),
                mock.Mock(),
            )
        self.assertTrue(out["ok"])
        sched.assert_called_once()

    async def test_materials_success_schedules_advance(self):
        from routes import workorder_routes as wr

        with (
            mock.patch.object(wr.storage, "save_material", return_value=mock.Mock()),
            mock.patch.object(
                wr.intake, "register_file", return_value={"id": "it-1", "file_ref": "/m/a.jpg"}
            ),
            mock.patch.object(wr, "_schedule_advance", return_value=True) as sched,
        ):
            for p in self._base(wr):
                self.enterContext(p)
            out = await wr.add_materials(
                "wo-1", mock.Mock(), mock.Mock(), files=[_FakeUpload(b"bytes", filename="a.jpg")]
            )
        self.assertEqual(out["count"], 1)
        sched.assert_called_once()

    async def test_auto_advance_swallows_scheduling_error(self):
        # 自驱是增益:排后台若抛错,已提交的裁决/销项不能被翻成 5xx。
        from routes import workorder_routes as wr

        with (
            mock.patch.object(wr.api, "record_decision", return_value={"id": 5}),
            mock.patch.object(wr, "_schedule_advance", side_effect=RuntimeError("lease down")),
        ):
            for p in self._base(wr):
                self.enterContext(p)
            out = await wr.add_decision(
                "wo-1",
                wr.DecisionIn(item_id="it-1", decision="face_value"),
                mock.Mock(),
                mock.Mock(),
            )
        self.assertTrue(out["ok"])  # 写成功,自驱失败被吞


class ScheduleAdvanceTests(unittest.TestCase):
    """_schedule_advance:抢到租约 → 落 run_requested + 排后台 advance;抢不到 → False,不排。
    行为逐字节回归(MC2-A1 换调 runner.request_run 原语后断言不变;事务落在 runner 层,
    故 db 假件打在 wr.runner 上)。"""

    def test_acquired_queues_advance(self):
        from routes import workorder_routes as wr

        bg = mock.Mock()
        with (
            mock.patch.object(wr.store, "ensure_runtime", return_value=None),
            mock.patch.object(wr.runner, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "acquire_run_lease", return_value=True),
            mock.patch.object(wr.store, "append_event", return_value={"id": 1}) as append,
        ):
            ok = wr._schedule_advance(bg, "t-1", "wo-1", _USER)
        self.assertTrue(ok)
        append.assert_called_once()
        self.assertEqual(append.call_args.kwargs["actor"], "user:u1")
        bg.add_task.assert_called_once()
        args = bg.add_task.call_args[0]
        self.assertEqual((args[1], args[2]), ("t-1", "wo-1"))
        self.assertTrue(str(args[3]).startswith("run:"))

    def test_lease_held_does_not_queue(self):
        from routes import workorder_routes as wr

        bg = mock.Mock()
        with (
            mock.patch.object(wr.store, "ensure_runtime", return_value=None),
            mock.patch.object(wr.runner, "db", _FakeDB(_Cur())),
            mock.patch.object(wr.store, "acquire_run_lease", return_value=False),
            mock.patch.object(wr.store, "append_event") as append,
        ):
            ok = wr._schedule_advance(bg, "t-1", "wo-1", _USER)
        self.assertFalse(ok)
        append.assert_not_called()
        bg.add_task.assert_not_called()


if __name__ == "__main__":
    unittest.main()
