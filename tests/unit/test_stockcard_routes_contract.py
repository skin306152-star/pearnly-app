# -*- coding: utf-8 -*-
"""Stock Card 路由契约闸(TestClient 打真路由,不直调 handler)。

2026-08-08 真机实锤:期初/归并两条写路径上线以来从没成功过一次 —— 前端把
workspace_client_id 塞 body(路由签名是 Query)+ 归并字段名前后端各写一套
(name_key/product_id vs name_keys/target_product_id),而 e2e 把这两个端点整个打了桩、
集成测试只测服务层,三层守卫全看不见路由这条缝。本文件用 TestClient 走完整 FastAPI
请求解析,并与 src/home/stock-card-api.ts 的真实 URL / 载荷形状互锁:任何一侧单改契约就红。
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.pos_api import PosError  # noqa: E402
from routes import stock_card_routes as routes  # noqa: E402

_TS_API = PROJECT_ROOT / "src" / "home" / "stock-card-api.ts"

EXPECTED_ROUTES = {
    ("GET", "/api/stockcard/status"),
    ("GET", "/api/stockcard/summary"),
    ("GET", "/api/stockcard/card"),
    ("GET", "/api/stockcard/excluded"),
    ("GET", "/api/stockcard/openings"),
    ("POST", "/api/stockcard/openings"),
    ("POST", "/api/stockcard/merge"),
}

# 前端 saveMerge 真实发出的两种载荷形状(stock-card.ts):目标已建档 / 名字轨代建。
FRONTEND_MERGE_PAYLOADS = (
    {"name_keys": ["น้ำแข็งหลอด", "น้ำแข็งหลอดเล็ก"], "target_product_id": "prod-1"},
    {"name_keys": ["น้ำแข็งหลอดเล็ก"], "new_product_name": "น้ำแข็งหลอด", "unit": "ถุง"},
)

MERGE_OK = {
    "product_id": "prod-1",
    "product_created": False,
    "purchase_lines_merged": 1,
    "sales_lines_merged": 1,
}


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


def _patches(merge_result=MERGE_OK):
    return (
        mock.patch.object(routes, "auth_member", return_value=({"id": "u1"}, "tenant-1")),
        mock.patch.object(routes, "gate", lambda cur, tid: None),
        mock.patch.object(routes, "resolve_ws", lambda cur, request, tid, ws: int(ws)),
        mock.patch.object(routes, "db", _FakeDb()),
        mock.patch.object(routes.merge_svc, "merge_into_product", return_value=merge_result),
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

    # ── 归并:前端真实载荷必须被路由原样接受 ────────────────────────

    def test_merge_accepts_both_frontend_payload_shapes(self):
        for payload in FRONTEND_MERGE_PAYLOADS:
            with self.subTest(payload=payload):
                r = self.client.post("/api/stockcard/merge?workspace_client_id=1", json=payload)
                self.assertEqual(r.status_code, 200, r.text)
                self.assertTrue(r.json()["ok"])

    def test_merge_without_query_workspace_is_422(self):
        # 2026-08-08 前的前端真形状:workspace_client_id 在 body 不在 query → 必须持续被拒,
        # 谁把 Query 签名改松了这条就红,提醒同步看 TS 侧。
        r = self.client.post(
            "/api/stockcard/merge",
            json={"workspace_client_id": 1, **FRONTEND_MERGE_PAYLOADS[0]},
        )
        self.assertEqual(r.status_code, 422)

    def test_merge_old_v1_field_names_stay_dead(self):
        r = self.client.post(
            "/api/stockcard/merge?workspace_client_id=1",
            json={"name_key": "x", "product_id": "prod-1"},
        )
        self.assertEqual(r.status_code, 422)

    def test_merge_invalid_target_translates_to_pos_error(self):
        mock.patch.stopall()
        self._active = [p.start() for p in _patches(merge_result=None)]
        with self.assertRaises(PosError) as ctx:
            self.client.post(
                "/api/stockcard/merge?workspace_client_id=1", json=FRONTEND_MERGE_PAYLOADS[0]
            )
        self.assertEqual(ctx.exception.http_status, 422)
        self.assertEqual(ctx.exception.code, "stockcard.merge_target_missing")

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
    """TS 适配层与本路由互锁:URL 必带 query · StcMergePayload 字段面 = MergeIn 字段面。"""

    @classmethod
    def setUpClass(cls):
        cls.src = _TS_API.read_text(encoding="utf-8")

    def test_ts_write_urls_carry_workspace_query(self):
        for frag in ("openings?workspace_client_id=", "merge?workspace_client_id="):
            self.assertIn(frag, self.src, f"stock-card-api.ts 写路径 URL 丢了 {frag}")

    def test_ts_merge_payload_fields_match_pydantic_model(self):
        m = re.search(r"interface StcMergePayload \{([^}]*)\}", self.src)
        self.assertIsNotNone(m, "stock-card-api.ts 里找不到 StcMergePayload")
        ts_fields = set(re.findall(r"^\s*(\w+)\??:", m.group(1), re.M))
        self.assertEqual(ts_fields, set(routes.MergeIn.model_fields))


if __name__ == "__main__":
    unittest.main()
