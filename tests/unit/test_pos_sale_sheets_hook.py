# -*- coding: utf-8 -*-
"""POS 建单后台留档挂钩(routes.pos_sales_routes._schedule_sheets_sync)守门测试。

锁定:真新建单才排后台任务;client_uuid 命中去重(deduped=True)不重复排——防离线补单
重放时重复往 Google Sheet 追加同一笔。任务体本身(真调 sheets_sync)交 test_pos_sheets_sync 锁。
"""

import asyncio
import unittest
from unittest.mock import patch

from starlette.requests import Request

import routes.pos_sales_routes as psr


def _request():
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/pos/sales",
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


class _CursorCtx:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


def _req_body(**overrides):
    body = dict(
        workspace_client_id=7,
        client_uuid="cu-1",
        lines=[{"product_id": "p1", "sell_unit": "ea", "qty": "1", "unit_price": "10"}],
        payments=[{"method": "cash", "amount": 10}],
    )
    body.update(overrides)
    return psr.CreateSaleRequest(**body)


class ScheduleOnCreateSaleTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_sale_schedules_sheets_sync(self):
        with (
            patch.object(psr, "_subject", return_value=({"id": "u1", "tenant_id": "t-1"}, "t-1")),
            patch.object(psr, "_resolve_ws", return_value=7),
            patch.object(psr.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch.object(psr, "assert_module_enabled"),
            patch.object(psr, "require_workspace"),
            patch.object(
                psr.sale_svc,
                "create_sale",
                return_value={"sale": {"id": "sale-1"}, "deduped": False},
            ),
            patch.object(psr, "_schedule_sheets_sync") as sched,
        ):
            body = await psr.api_create_sale(_req_body(), _request())

        self.assertTrue(body["ok"])
        sched.assert_called_once_with("t-1", 7, "sale-1")

    async def test_deduped_replay_does_not_reschedule(self):
        with (
            patch.object(psr, "_subject", return_value=({"id": "u1", "tenant_id": "t-1"}, "t-1")),
            patch.object(psr, "_resolve_ws", return_value=7),
            patch.object(psr.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch.object(psr, "assert_module_enabled"),
            patch.object(psr, "require_workspace"),
            patch.object(
                psr.sale_svc,
                "create_sale",
                return_value={"sale": {"id": "sale-1"}, "deduped": True},
            ),
            patch.object(psr, "_schedule_sheets_sync") as sched,
        ):
            await psr.api_create_sale(_req_body(), _request())

        sched.assert_not_called()


class ScheduleSheetsSyncTaskTests(unittest.IsolatedAsyncioTestCase):
    async def test_sync_failure_does_not_raise_or_leak_task(self):
        with (
            patch.object(psr.db, "get_cursor_rls", return_value=_CursorCtx()),
            patch("services.pos.sheets_sync.sync_sale", side_effect=RuntimeError("boom")),
        ):
            psr._schedule_sheets_sync("t-1", 7, "sale-1")
            # 让事件循环跑一轮,给后台任务机会执行 + 触发 done_callback 清理引用集。
            await asyncio.sleep(0)
            await asyncio.sleep(0)

        self.assertEqual(len(psr._sheets_sync_tasks), 0)


if __name__ == "__main__":
    unittest.main()
