# -*- coding: utf-8 -*-
"""B8 RLS 契约:vat_recon_tasks store 走带租户上下文的 RLS 游标(REFACTOR-B8 wave2)。

vat_recon_tasks 是 tenant_or_user 模板(tenant 可空 + user 兜底),CRUD 必须同时把
tenant_id + user_id 注入 get_cursor_rls,否则启用 RLS 后孤立用户(tenant_id NULL)行
被隐藏。锁定:不回退到裸 get_cursor。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

import core.db  # noqa: F401 — 先初始化 core.db,避免 leaf-first 触发 dal_reexports 循环导入
from services.recon import vat_recon_tasks_store as store


class _Cur:
    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return {"id": "t-1", "n": 0}

    def fetchall(self):
        return []


def _capture():
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur()

    return calls, fake


class VatReconTasksRlsContractTests(unittest.TestCase):
    def test_create_passes_tenant_and_user(self):
        calls, fake = _capture()
        with (
            mock.patch("core.db.get_cursor_rls", fake),
            mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls")),
        ):
            store.create_vat_recon_task(
                "ten-1", "usr-1", "c", "p", 1, 1, 1, 0, 0.0, 0.0, None, {}, workspace_client_id=5
            )
        self.assertEqual(calls[0].get("tenant_id"), "ten-1")
        self.assertEqual(calls[0].get("user_id"), "usr-1")
        self.assertEqual(calls[0].get("workspace_client_id"), 5)

    def test_list_passes_tenant_and_user(self):
        calls, fake = _capture()
        with (
            mock.patch("core.db.get_cursor_rls", fake),
            mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls")),
        ):
            store.list_vat_recon_tasks("ten-1", "usr-1")
        self.assertEqual(calls[0].get("tenant_id"), "ten-1")
        self.assertEqual(calls[0].get("user_id"), "usr-1")

    def test_delete_passes_tenant_and_user(self):
        calls, fake = _capture()
        with (
            mock.patch("core.db.get_cursor_rls", fake),
            mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls")),
        ):
            store.delete_vat_recon_task("task-1", "ten-1", "usr-1")
        self.assertEqual(calls[0].get("tenant_id"), "ten-1")
        self.assertEqual(calls[0].get("user_id"), "usr-1")


if __name__ == "__main__":
    unittest.main()
