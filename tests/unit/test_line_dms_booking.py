# -*- coding: utf-8 -*-
"""DMS 订车阶段(DL-4a)· offer_pick 选车入口 + 预览确认建单 + nonce 防双建。

覆盖:offer_pick 置 picking + 推 URI 按钮;D4(面板所选 advisor/paint 传进建单 +
push 台账 trigger='line_dms' + 回执含 BK 号 · 失败原样回);D5(nonce 双击第二次拒)。
"""

import contextlib
import dataclasses
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-for-dms-pick-32bytes-long")

from services.line_dms import booking_flow as bf  # noqa: E402
from services.line_dms import cards  # noqa: E402

_BINDING = {"tenant_id": "T1", "user_id": "U1"}
_LUID = "L1"


class FakeStore:
    def __init__(self):
        self.data = {}

    def get_session(self, tenant, luid):
        return self.data.get((str(tenant), str(luid)))

    def set_session(self, tenant, luid, state, payload=None, ttl_minutes=30):
        self.data[(str(tenant), str(luid))] = {
            "state": state,
            "payload": payload or {},
            "ttl_minutes": ttl_minutes,
        }

    def clear_session(self, tenant, luid):
        self.data.pop((str(tenant), str(luid)), None)


@dataclasses.dataclass(frozen=True)
class _FakeBooking:
    delivery_date_be: str = "old"


class _FakeClient:
    """记录建单入参(defaults/booking),供断言面板所选透传。"""

    def __init__(self, rec):
        self.rec = rec

    def resolve_booking_payload(self, defaults, card, today=None):
        self.rec["defaults"] = defaults
        self.rec["card"] = card
        return _FakeBooking()

    def create_booking_via_form(self, *, customer_id, booking, card):
        self.rec["customer_id"] = customer_id
        self.rec["delivery"] = booking.delivery_date_be
        return ("BID1", "BK123")

    def fetch_masters(self):
        return {}


class _Env:
    def __init__(self, *, book_result=None):
        self.store = FakeStore()
        self.spawned = []
        self._book_result = book_result
        self.es = contextlib.ExitStack()

    def __enter__(self):
        es = self.es
        p = lambda *a, **k: es.enter_context(mock.patch.object(*a, **k))  # noqa: E731
        p(bf.store, "get_session", side_effect=self.store.get_session)
        p(bf.store, "set_session", side_effect=self.store.set_session)
        p(bf.store, "clear_session", side_effect=self.store.clear_session)
        p(bf, "_spawn", side_effect=self.spawned.append)
        self.reply = p(bf.line_client, "reply_text")
        self.push_text = p(bf.line_client, "push_text")
        self.push_msgs = p(bf.line_client, "push_messages")
        p(bf.line_client, "start_loading")
        p(bf._id_ocr, "resolve_dms_endpoint", return_value={"id": "E1", "config": {}})
        self.insert_log = p(bf.db, "insert_push_log", return_value="LOG1")
        if self._book_result is not None:
            p(bf, "_book_in_session", return_value=self._book_result)
        return self

    def __exit__(self, *a):
        self.es.close()
        return False

    async def drain(self):
        while self.spawned:
            await self.spawned.pop(0)

    def session(self):
        return self.store.get_session("T1", "L1")


def _review(nonce="N1"):
    return {
        "nonce": nonce,
        "endpoint_id": "E1",
        "customer_id": "C1",
        "user_id": "U1",
        "draft": {"people_id": "1234567890121", "name": "สมชาย"},
        "name": "สมชาย ใจดี",
        "car_id": "c9",
        "paint_id": "p9",
        "advisor_id": "a9",
        "delivery_date_be": "01/01/2570",
        "car": "CODE9 Car Nine",
    }


class BookingTests(unittest.IsolatedAsyncioTestCase):
    async def test_offer_pick_sets_picking_and_pushes_button(self):
        with _Env() as env:
            await bf.offer_pick(
                _BINDING,
                _LUID,
                endpoint_id="E1",
                customer_id="C1",
                draft={"people_id": "123", "name": "x"},
                name="x",
            )
            sess = env.session()
            self.assertEqual(sess["state"], "picking")
            self.assertTrue(sess["payload"]["nonce"])
            self.assertEqual(sess["payload"]["user_id"], "U1")
            card = env.push_msgs.call_args.args[1][0]
            uri = card["contents"]["footer"]["contents"][0]["action"]["uri"]
            self.assertIn("/dms-pick?t=", uri)
            # 会话须活过 15 分钟的面板 token:它是重发链接的唯一凭据(P1-12)。
            self.assertGreater(sess["ttl_minutes"], 15)

    async def test_offer_pick_no_customer_clears_and_says_so(self):
        """缺客户号 → 清会话,但要留一句交代,不静默(状态诚实)。"""
        with _Env() as env:
            await bf.offer_pick(_BINDING, _LUID, endpoint_id="E1", customer_id="", draft={})
            self.assertIsNone(env.session())
            env.push_msgs.assert_not_called()
            self.assertEqual(env.push_text.call_args.args[1], cards.TXT_PICK_UNAVAILABLE)

    async def test_d4_confirm_creates_booking_and_logs(self):
        result = {"ok": True, "booking_id": "BID1", "booking_no": "BK9"}
        with _Env(book_result=result) as env:
            env.store.set_session("T1", "L1", "booking_review", _review())
            await bf.handle_postback(
                _BINDING, _LUID, "rt", cards.ACT_CONFIRM_BOOKING, {"nonce": "N1"}
            )
            await env.drain()
        # 回执含 BK 号
        self.assertIn("BK9", env.push_text.call_args.args[1])
        # push 台账 trigger='line_dms'
        request_body = env.insert_log.call_args.args[8]
        self.assertEqual(request_body["trigger"], "line_dms")
        self.assertEqual(request_body["mode"], "booking")
        self.assertEqual(env.insert_log.call_args.args[3], "BK9")  # invoice_no ← BK 号
        self.assertIsNone(env.session())  # 成功后清

    async def test_d4_book_in_session_passes_panel_selection(self):
        """面板所选 advisor/car/paint 覆盖端点默认、交车日用面板值。"""
        rec = {}

        def fake_run(ep, do):
            return do(_FakeClient(rec), object())

        with (
            mock.patch("services.erp.erp_dms_intake._run_logged_in", side_effect=fake_run),
            mock.patch.object(bf.masters_cache, "refresh_from_client"),
        ):
            res = bf._book_in_session({"id": "E1", "config": {}}, _review())
        self.assertTrue(res["ok"])
        self.assertEqual(res["booking_no"], "BK123")
        self.assertEqual(rec["defaults"].advisor_id, "a9")
        self.assertEqual(rec["defaults"].car_id, "c9")
        self.assertEqual(rec["defaults"].paint_id, "p9")
        self.assertEqual(rec["customer_id"], "C1")
        self.assertEqual(rec["delivery"], "01/01/2570")  # 面板交车日覆盖

    async def test_d4_failure_returns_friendly_th(self):
        result = {
            "ok": False,
            "error_code": "ERR_DMS_IMPORT",
            "error_friendly": {"th": "สร้างใบจองรถไม่สำเร็จ"},
        }
        with _Env(book_result=result) as env:
            env.store.set_session("T1", "L1", "booking_review", _review())
            await bf.handle_postback(
                _BINDING, _LUID, "rt", cards.ACT_CONFIRM_BOOKING, {"nonce": "N1"}
            )
            await env.drain()
        self.assertEqual(env.push_text.call_args.args[1], "สร้างใบจองรถไม่สำเร็จ")

    async def test_d5_double_click_single_booking(self):
        with _Env(book_result={"ok": True, "booking_no": "BK9"}) as env:
            env.store.set_session("T1", "L1", "booking_review", _review())
            await bf.handle_postback(
                _BINDING, _LUID, "rt", cards.ACT_CONFIRM_BOOKING, {"nonce": "N1"}
            )
            # 第二次同 nonce:首次已清 nonce → 过期话术,不二次建单。
            await bf.handle_postback(
                _BINDING, _LUID, "rt2", cards.ACT_CONFIRM_BOOKING, {"nonce": "N1"}
            )
            self.assertEqual(len(env.spawned), 1)
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_EXPIRED)
            await env.drain()

    async def test_cancel_clears_and_confirms(self):
        with _Env() as env:
            env.store.set_session("T1", "L1", "booking_review", _review())
            await bf.handle_postback(_BINDING, _LUID, "rt", cards.ACT_CANCEL_BOOKING, {})
            self.assertIsNone(env.session())
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_BOOKING_CANCELLED)


if __name__ == "__main__":
    unittest.main()
