# -*- coding: utf-8 -*-
"""Stock Card 路由契约闸(TestClient 打真路由,不直调 handler)。

2026-08-27 拍板:网页主视图只保留一次只读请求 GET /api/stockcard/report + 期初读/写
/openings;旧「汇总→单品详情」流程的 /summary、/card、/excluded、/merge 路由被删。
本文件与 src/home/stock-card-api.ts 的真实 URL / 载荷形状互锁:任何一侧单改契约就红,
并显式断言旧 / 旧交互不存在(谁把删掉的路由加回来这条就红)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from routes import stock_card_routes as routes  # noqa: E402

_TS_API = PROJECT_ROOT / "src" / "home" / "stock-card-api.ts"

EXPECTED_ROUTES = {
    ("GET", "/api/stockcard/status"),
    ("GET", "/api/stockcard/report"),
    ("GET", "/api/stockcard/openings"),
    ("POST", "/api/stockcard/openings"),
}

# 旧「汇总→单品详情」流程的路由:已删除,前端也不得再调用(断言在 TsSide 与路由双锁)。
LEGACY_ROUTES = {
    ("GET", "/api/stockcard/summary"),
    ("GET", "/api/stockcard/card"),
    ("GET", "/api/stockcard/excluded"),
    ("POST", "/api/stockcard/merge"),
}

SAMPLE_GROUPS = [
    {
        "product": {"key": "p:PROD-1", "product_id": "PROD-1", "name": "WPC", "unit": "条"},
        "rows": [
            {
                "date": "2024-06-01",
                "doc_no": "",
                "kind": "open",
                "desc": "",
                "qty": "10",
                "unit_price": None,
                "amount": None,
                "bal_qty": "10",
                "bal_unit_cost": "250.00",
                "bal_value": "2500.00",
            }
        ],
        "totals": {
            "in_qty": "0",
            "in_amount": "0",
            "out_qty": "0",
            "out_amount": "0",
            "bal_qty": "10",
            "bal_unit_cost": "250.00",
            "bal_value": "2500.00",
        },
    }
]


class _CurCM:
    def __enter__(self):
        return mock.MagicMock()

    def __exit__(self, *a):
        return False


class _FakeDb:
    def get_cursor_rls(self, tenant_id, commit=False):
        return _CurCM()


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app)


def _patches(groups_result=SAMPLE_GROUPS):
    return (
        mock.patch.object(routes, "auth_member", return_value=({"id": "u1"}, "tenant-1")),
        mock.patch.object(routes, "gate", lambda cur, tid: None),
        mock.patch.object(routes, "resolve_ws", lambda cur, request, tid, ws: int(ws)),
        mock.patch.object(routes, "db", _FakeDb()),
        mock.patch.object(routes.report_svc, "groups", return_value=groups_result),
        mock.patch.object(routes.opening_svc, "upsert_openings", return_value=[]),
    )


class StockCardRoutesContractTests(unittest.TestCase):
    def setUp(self):
        self._active = [p.start() for p in _patches()]
        self.addCleanup(mock.patch.stopall)
        self.client = _client()

    def test_router_registers_expected_routes(self):
        got = set()
        for r in routes.router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED_ROUTES)

    def test_legacy_routes_are_dead(self):
        # 旧「汇总→单品详情」流程路由必须不存在:谁把它们加回来自我断言就红。
        got = set()
        for r in routes.router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                    got.add((m, r.path))
        self.assertTrue(LEGACY_ROUTES.isdisjoint(got))

    # ── 主视图:一次请求返回 groups ────────────────────────────────

    def test_report_returns_groups(self):
        r = self.client.get(
            "/api/stockcard/report",
            params={"workspace_client_id": 1, "date_from": "2024-06-01", "date_to": "2024-06-30"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["groups"], SAMPLE_GROUPS)

    def test_report_without_query_workspace_is_422(self):
        r = self.client.get(
            "/api/stockcard/report",
            params={"date_from": "2024-06-01", "date_to": "2024-06-30"},
        )
        self.assertEqual(r.status_code, 422)

    # ── 期初:同一条 Query 契约 ────────────────────────────────────

    def test_openings_accepts_frontend_shape(self):
        rows = [
            {"name": "น้ำแข็งหลอด", "qty": "10", "unit_cost": "5.00", "as_of_date": "2026-08-01"}
        ]
        r = self.client.post("/api/stockcard/openings?workspace_client_id=1", json={"rows": rows})
        self.assertEqual(r.status_code, 200, r.text)

    def test_openings_without_query_workspace_is_422(self):
        r = self.client.post("/api/stockcard/openings", json={"workspace_client_id": 1, "rows": []})
        self.assertEqual(r.status_code, 422)


class TsSideContractLockTests(unittest.TestCase):
    """TS 适配层与本路由互锁:report 只打 /api/stockcard/report,旧 URL 已删净。"""

    @classmethod
    def setUpClass(cls):
        cls.src = _TS_API.read_text(encoding="utf-8")

    def test_ts_report_url_carries_query(self):
        # report 取数带 query 字符串(workspace 参数由后端 Query(...) 强制,见
        # test_report_without_query_workspace_is_422);这里锁住前端打的是 report 端点。
        self.assertIn(
            "/api/stockcard/report?",
            self.src,
            "stock-card-api.ts 的 report 取数 URL 丢了 query 字符串",
        )
        for fragment in (
            "workspace_client_id: String(wsId)",
            "date_from: dateFrom",
            "date_to: dateTo",
        ):
            self.assertIn(fragment, self.src)

    def test_ts_legacy_urls_are_gone(self):
        for frag in (
            "/api/stockcard/summary",
            "/api/stockcard/card",
            "/api/stockcard/excluded",
            "/api/stockcard/merge",
        ):
            self.assertNotIn(
                frag,
                self.src,
                f"stock-card-api.ts 仍引用旧路由 {frag} —— 2026-08-27 口径已删净",
            )

    def test_ts_keeps_openings_write_url_query(self):
        self.assertIn("openings?workspace_client_id=", self.src)


if __name__ == "__main__":
    unittest.main()
