# -*- coding: utf-8 -*-
"""DMS 车辆选择面板端点(DL-4a)· token/scope/nonce 门 + dms_line 闸 + submit 预览卡。

真 JWT(core.auth 签/验)· FakeStore 会话 · mock 主档缓存/端点解析/LINE 出口。
覆盖 D2(token/scope/nonce/一次性)、D3(submit 预览卡)、D6(闸关 404)。
"""

import contextlib
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-for-dms-pick-32bytes-long")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core import auth  # noqa: E402
from routes import dms_pick_routes as pr  # noqa: E402

_EP = {"id": "E1", "config": {}}
_MASTERS = {"cars": [["c1", "CODE1", "Car One"]], "advisors": [["a1", "A1", "Adv"]]}
_PAINTS = [["p1", "PC1", "Red"]]


class FakeStore:
    def __init__(self):
        self.data = {}

    def get_session(self, tenant, luid):
        return self.data.get((str(tenant), str(luid)))

    def set_session(self, tenant, luid, state, payload=None, ttl_minutes=30):
        self.data[(str(tenant), str(luid))] = {"state": state, "payload": payload or {}}


def _pick_payload():
    return {
        "nonce": "NONCE1",
        "endpoint_id": "E1",
        "customer_id": "C1",
        "user_id": "U1",
        "draft": {"people_id": "1234567890121"},
        "name": "สมชาย ใจดี",
    }


class PickRoutesTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore()
        self.es = contextlib.ExitStack()
        p = lambda *a, **k: self.es.enter_context(mock.patch.object(*a, **k))  # noqa: E731
        p(pr.store, "get_session", side_effect=self.store.get_session)
        p(pr.store, "set_session", side_effect=self.store.set_session)
        p(pr, "dms_line_enabled_for", return_value=True)
        p(pr._id_ocr, "resolve_dms_endpoint", return_value=_EP)
        p(pr.masters_cache, "get_masters", return_value=_MASTERS)
        p(pr.masters_cache, "read_fresh_masters", return_value=_MASTERS)  # submit 只读缓存校验(S7)
        p(pr.masters_cache, "get_paints", return_value=_PAINTS)
        self.push = p(pr.line_client, "push_messages")

        app = FastAPI()
        app.include_router(pr.router)
        self.client = TestClient(app)
        # 预置 picking 会话 + 有效 token。
        self.store.set_session("T1", "L1", "picking", _pick_payload())
        self.token = auth.create_dms_pick_token(
            tenant_id="T1", line_user_id="L1", endpoint_id="E1", nonce="NONCE1"
        )

    def tearDown(self):
        self.es.close()

    # ── D2:token / scope / nonce / 一次性 ────────────────────────────────
    def test_d2_bad_token_401(self):
        r = self.client.get("/api/dms/pick/data", params={"t": "garbage"})
        self.assertEqual(r.status_code, 401)

    def test_d2_wrong_scope_401(self):
        # 别的 token(无 scope='dms_pick')不得当面板 token 用。
        other = auth.create_pos_store_token(tenant_id="T1", workspace_client_id=1, version=1)
        r = self.client.get("/api/dms/pick/data", params={"t": other})
        self.assertEqual(r.status_code, 401)

    def test_d2_nonce_mismatch_401(self):
        bad = auth.create_dms_pick_token(
            tenant_id="T1", line_user_id="L1", endpoint_id="E1", nonce="OTHER"
        )
        r = self.client.get("/api/dms/pick/data", params={"t": bad})
        self.assertEqual(r.status_code, 401)

    def test_d2_valid_data_ok(self):
        r = self.client.get("/api/dms/pick/data", params={"t": self.token})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["cars"], _MASTERS["cars"])
        self.assertEqual(body["customer"]["name"], "สมชาย ใจดี")
        self.assertTrue(body["defaults"]["delivery_date_be"])

    def test_d2_replay_after_submit_refused(self):
        ok = self.client.post(
            "/api/dms/pick/submit",
            json={
                "t": self.token,
                "car_id": "c1",
                "paint_id": "p1",
                "advisor_id": "a1",
                "delivery_date_be": "01/01/2570",
            },
        )
        self.assertEqual(ok.status_code, 200)
        # 提交成功后 nonce 轮换(picking→booking_review)→ 旧 token 再用必拒。
        replay = self.client.get("/api/dms/pick/data", params={"t": self.token})
        self.assertEqual(replay.status_code, 401)

    # ── D3:submit → 预览卡含所选车型 code 与颜色 ─────────────────────────
    def test_d3_submit_pushes_preview_card(self):
        r = self.client.post(
            "/api/dms/pick/submit",
            json={
                "t": self.token,
                "car_id": "c1",
                "paint_id": "p1",
                "advisor_id": "a1",
                "delivery_date_be": "01/01/2570",
            },
        )
        self.assertEqual(r.status_code, 200)
        sess = self.store.get_session("T1", "L1")
        self.assertEqual(sess["state"], "booking_review")
        self.assertEqual(sess["payload"]["car_id"], "c1")
        self.assertNotEqual(sess["payload"]["nonce"], "NONCE1")  # 轮换

        card = self.push.call_args.args[1][0]
        texts = _all_text(card)
        self.assertTrue(any("CODE1" in t for t in texts))  # 车型 code
        self.assertTrue(any("Red" in t for t in texts))  # 颜色

    def test_submit_bad_selection_422(self):
        r = self.client.post(
            "/api/dms/pick/submit",
            json={"t": self.token, "car_id": "nope", "paint_id": "p1", "advisor_id": "a1"},
        )
        self.assertEqual(r.status_code, 422)

    # ── D6:dms_line 闸关 → 三 API 404 ───────────────────────────────────
    def test_d6_gate_off_404(self):
        with mock.patch.object(pr, "dms_line_enabled_for", return_value=False):
            for path, params in (
                ("/api/dms/pick/data", {"t": self.token}),
                ("/api/dms/pick/paints", {"t": self.token, "car_id": "c1"}),
            ):
                self.assertEqual(self.client.get(path, params=params).status_code, 404)
            sub = self.client.post(
                "/api/dms/pick/submit",
                json={"t": self.token, "car_id": "c1", "paint_id": "p1", "advisor_id": "a1"},
            )
            self.assertEqual(sub.status_code, 404)


def _all_text(node, out=None):
    out = [] if out is None else out
    if isinstance(node, dict):
        if node.get("type") == "text" and isinstance(node.get("text"), str):
            out.append(node["text"])
        for v in node.values():
            _all_text(v, out)
    elif isinstance(node, list):
        for v in node:
            _all_text(v, out)
    return out


if __name__ == "__main__":
    unittest.main()
