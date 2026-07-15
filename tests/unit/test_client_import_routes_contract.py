# -*- coding: utf-8 -*-
"""IN-0d · routes/client_import_routes.py 契约测试。

命门断言:导入 commit/parse 逐行调用的是 routes.workspace_routes._create_validated_client
——单建端点与导入共用同一个校验/创建函数,不是抄了第二套判定(mock 钉住调用路径:
patch 掉这一个函数就能让所有行为化,证明没有旁路实现)。
"""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from routes import client_import_routes as r
from routes.workspace_routes import WorkspaceClientCreate


class SharedValidationPathTests(unittest.TestCase):
    """commit/parse 都只通过 workspace_routes._create_validated_client 落地,
    不在本模块另起校验/创建实现。"""

    def test_commit_calls_shared_validated_creator_not_db_directly(self):
        row = r.ClientImportRow(row_index=0, name="ACME Co Ltd", tax_id="0105546015062")
        with mock.patch(
            "routes.client_import_routes._create_validated_client", return_value=99
        ) as shared:
            out = r._judge_row(row, {"id": "u1"}, "tenant-1", dry_run=False)
        shared.assert_called_once()
        called_req = shared.call_args.args[0]
        self.assertIsInstance(called_req, WorkspaceClientCreate)
        self.assertEqual(called_req.name, "ACME Co Ltd")
        self.assertEqual(
            out,
            {
                "row_index": 0,
                "status": "created",
                "id": 99,
                "name": "ACME Co Ltd",
                "tax_id": "0105546015062",
            },
        )

    def test_parse_preview_uses_dry_run_true(self):
        row = r.ClientImportRow(row_index=0, name="ACME Co Ltd")
        with mock.patch(
            "routes.client_import_routes._create_validated_client", return_value=None
        ) as shared:
            out = r._judge_row(row, {"id": "u1"}, "tenant-1", dry_run=True)
        self.assertEqual(shared.call_args.kwargs, {"dry_run": True})
        self.assertEqual(out["status"], "valid")

    def test_tax_id_duplicate_maps_to_skip_not_error(self):
        row = r.ClientImportRow(row_index=2, name="ACME Co Ltd", tax_id="0105546015062")
        with mock.patch(
            "routes.client_import_routes._create_validated_client",
            side_effect=HTTPException(422, detail="workspace.tax_id_duplicate"),
        ):
            out = r._judge_row(row, {"id": "u1"}, "tenant-1", dry_run=False)
        self.assertEqual(out["status"], "skip")
        self.assertEqual(out["reason"], "workspace.tax_id_duplicate")

    def test_thai_name_gate_failure_maps_to_error(self):
        row = r.ClientImportRow(row_index=3, name="Sister Makeup Co Ltd")
        with mock.patch(
            "routes.client_import_routes._create_validated_client",
            side_effect=HTTPException(
                422, detail={"code": "workspace.thai_name_required", "message": {}}
            ),
        ):
            out = r._judge_row(row, {"id": "u1"}, "tenant-1", dry_run=False)
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["reason"], "workspace.thai_name_required")

    def test_pos_single_store_gate_maps_to_error(self):
        row = r.ClientImportRow(row_index=4, name="ACME Co Ltd")
        with mock.patch(
            "routes.client_import_routes._create_validated_client",
            side_effect=HTTPException(403, detail="pos.workspace_single_store"),
        ):
            out = r._judge_row(row, {"id": "u1"}, "tenant-1", dry_run=False)
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["reason"], "pos.workspace_single_store")

    def test_missing_name_short_circuits_before_shared_creator(self):
        # 结构性错误(缺 name)在本模块自己拦,压根不该打共享校验体一次往返。
        row = r.ClientImportRow(row_index=5, name="   ")
        with mock.patch("routes.client_import_routes._create_validated_client") as shared:
            out = r._judge_row(row, {"id": "u1"}, "tenant-1", dry_run=False)
        shared.assert_not_called()
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["reason"], "client_import.err_missing_name")

    def test_bad_tax_id_format_short_circuits_before_shared_creator(self):
        row = r.ClientImportRow(row_index=6, name="ACME Co Ltd", tax_id="12345")
        with mock.patch("routes.client_import_routes._create_validated_client") as shared:
            out = r._judge_row(row, {"id": "u1"}, "tenant-1", dry_run=False)
        shared.assert_not_called()
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["reason"], "client_import.err_bad_tax_id")


class RouteRegisteredTests(unittest.TestCase):
    def test_parse_and_commit_routes_registered(self):
        paths = {
            (m, route.path)
            for route in r.router.routes
            for m in getattr(route, "methods", set()) or set()
        }
        self.assertIn(("POST", "/api/workspace/clients/import/parse"), paths)
        self.assertIn(("POST", "/api/workspace/clients/import/commit"), paths)

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(route, "path", None) for route in app.app.routes}
        self.assertIn("/api/workspace/clients/import/parse", paths)
        self.assertIn("/api/workspace/clients/import/commit", paths)


class EndpointWiringTests(unittest.IsolatedAsyncioTestCase):
    async def test_parse_endpoint_rejects_file_too_large(self):
        big = b"x" * (r.import_svc.MAX_BYTES + 1)

        class _FakeFile:
            filename = "clients.xlsx"

            async def read(self):
                return big

        with mock.patch.object(r, "require_perm", return_value={"id": "u1"}):
            with self.assertRaises(HTTPException) as ctx:
                await r.api_client_import_parse(mock.Mock(), file=_FakeFile())
        self.assertEqual(ctx.exception.status_code, 413)
        self.assertEqual(ctx.exception.detail, "client_import.file_too_large")

    async def test_commit_endpoint_rejects_over_row_limit(self):
        rows = [
            r.ClientImportRow(row_index=i, name=f"C{i}") for i in range(r.import_svc.MAX_ROWS + 1)
        ]
        cfg = r.ClientImportCommitRequest(rows=rows)
        with mock.patch.object(r, "require_perm", return_value={"id": "u1"}):
            with self.assertRaises(HTTPException) as ctx:
                await r.api_client_import_commit(cfg, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "client_import.too_many_rows")


if __name__ == "__main__":
    unittest.main()
