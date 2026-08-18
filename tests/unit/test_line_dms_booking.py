# -*- coding: utf-8 -*-
"""DMS 订车阶段(DL-4a/DL-7)· 逐问完成态 → 确认建单 + 附件挂载 + nonce 防双建。

覆盖:qa 完成态 payload → 确认 postback → create_booking_via_form 收到含
payments/regis_name/delivery 的 booking、defaults 含 place/term/regis id;附件按
qa.files 下载并同会话挂载(attach 结果进 result 与台账 response_body);建单成功但
附件失败 → 回执如实追加「แนบไฟล์ไม่ครบ」;台账 request_body.qa 摘要;nonce 双击第二次拒。
"""

import contextlib
import dataclasses
import json
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-for-line-dms-qa-32bytes-long")

from services.line_dms import booking_flow as bf  # noqa: E402
from services.line_dms import cards, qa_cards  # noqa: E402

_BINDING = {"tenant_id": "T1", "user_id": "U1"}
_LUID = "L1"

_JPEG = b"\xff\xd8jpeg-bytes"


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
    regis_name: str = ""
    payments: tuple = ()


class _FakeClient:
    """记录建单/附件入参,供断言逐问选择与附件透传。"""

    def __init__(self, rec):
        self.rec = rec

    def resolve_booking_payload(self, defaults, card, today=None):
        self.rec["defaults"] = defaults
        self.rec["card"] = card
        return _FakeBooking()

    def save_customer(self, **kwargs):
        self.rec["customer_save"] = kwargs
        return kwargs.get("customer_id"), False

    def create_booking_via_form(self, *, customer_id, booking, card):
        self.rec["customer_id"] = customer_id
        self.rec["booking"] = booking
        return ("BID1", "BK123")

    def attach_booking_files(self, *, booking_id, files):
        self.rec["attach_booking_id"] = booking_id
        self.rec["attach_files"] = list(files)
        return {"ok": True, "attached": len(files), "failed": []}

    def fetch_masters(self):
        return {}


def _qa_payload(**over):
    qa = {
        "step": "pay_more",
        "endpoint_id": "E1",
        "customer": {"id": "C1", "name": "สมชาย ใจดี"},
        "advisor": {"id": "335", "name": "sale02"},
        "draft": {"people_id": "1234567890121", "name": "สมชาย"},
        "user_id": "U1",
        "files": {"id_card_mid": "mid-card", "slip_mid": "mid-slip"},
        "answers": {
            "place": {"id": "pl1", "name": "สาขาบางนา"},
            "car": {"id": "c1", "label": "DMX D-Max"},
            "paint": {"id": "p1", "name": "ขาว"},
            "delivery_date_be": "01/01/2570",
            "term": {"id": "t1", "name": "เงินสด"},
            "regis": {"id": "r1", "name": "บริษัท"},
            "regis_name": "บริษัท สมชาย จำกัด",
        },
        "payments": [
            {
                "channel": "transfer",
                "amount": "5000.00",
                "extra": {"src": "SCB", "dst_id": "1", "dst": "old"},
            }
        ],
        "pending_channel": {},
        "audit": [{"step": "slip", "input": "image:mid-slip"}],
    }
    qa.update(over)
    return qa


def _review(nonce="N1", **over):
    """booking_review 会话:顶层只有 nonce,业务数据一律在 qa(顾问归属在 qa.advisor)。"""
    return {"nonce": nonce, "qa": _qa_payload(**over)}


class _Env:
    def __init__(self, *, book_result=None, download=_JPEG):
        self.store = FakeStore()
        self.spawned = []
        self._book_result = book_result
        self._download = download
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
        self.download = p(bf.line_client, "download_message_content", return_value=self._download)
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


class BookingTests(unittest.IsolatedAsyncioTestCase):
    async def test_browser_customer_edits_are_written_before_booking(self):
        rec = {}

        def fake_run(ep, do):
            return do(_FakeClient(rec), object())

        qa = _qa_payload(
            customer_dirty=True,
            customer={"id": "C1", "name": "แก้แล้ว"},
            draft={"people_id": "1101700998118", "phone": "0899999999"},
        )
        with (
            mock.patch("services.erp.erp_dms_intake._run_logged_in", side_effect=fake_run),
            mock.patch(
                "services.erp.mrerp_dms_booking_customer.card_from_customer",
                side_effect=lambda client, customer_id, people_id: bf._card_payload({"qa": qa}),
            ),
            mock.patch.object(bf.masters_cache, "refresh_from_client"),
            mock.patch(
                "services.erp.mrerp_dms_company_banks.fetch_company_banks",
                return_value=[["1", "SCB", "SCB"]],
            ),
        ):
            result = bf._book_in_session({"id": "E1", "config": {}}, {"qa": qa})

        self.assertTrue(result["ok"])
        self.assertEqual(rec["customer_save"]["fields"]["name"], "แก้แล้ว")
        self.assertEqual(rec["customer_save"]["fields"]["phone"], "0899999999")
        self.assertEqual(rec["customer_save"]["mode"], "overwrite")

    async def test_d4_confirm_creates_booking_and_logs(self):
        result = {
            "ok": True,
            "booking_id": "BID1",
            "booking_no": "BK9",
            "attach_ok": True,
            "attached": 2,
            "attach_failed": [],
        }
        with _Env(book_result=result) as env:
            env.store.set_session("T1", "L1", "booking_review", _review())
            await bf.handle_postback(
                _BINDING, _LUID, "rt", cards.ACT_CONFIRM_BOOKING, {"nonce": "N1"}
            )
            await env.drain()
        # 回执含 BK 号 + 车型(label 来自 qa.answers.car)+ 顾问(提成归属当场可核对)
        self.assertIn("BK9", env.push_text.call_args.args[1])
        self.assertIn("DMX D-Max", env.push_text.call_args.args[1])
        self.assertIn("ที่ปรึกษา: sale02", env.push_text.call_args.args[1])
        # push 台账 trigger='line_dms' + request_body.qa 摘要
        request_body = env.insert_log.call_args.args[8]
        self.assertEqual(request_body["trigger"], "line_dms")
        self.assertEqual(request_body["mode"], "booking")
        self.assertEqual(request_body["advisor_id"], "335")
        # 台账留归属名,对账不用回查主档;与 advisor_id 同层,别拆两处
        self.assertEqual(request_body["advisor_name"], "sale02")
        qa = request_body["qa"]
        self.assertEqual(qa["place_id"], "pl1")
        self.assertEqual(qa["term_id"], "t1")
        self.assertEqual(qa["regis_id"], "r1")
        self.assertEqual(qa["regis_name"], "บริษัท สมชาย จำกัด")
        self.assertEqual(qa["payments"], [{"channel": "transfer", "amount": "5000.00"}])
        self.assertEqual(qa["earnest_total"], "5000.00")
        self.assertTrue(qa["slip_attached"])
        self.assertEqual(env.insert_log.call_args.args[3], "BK9")  # invoice_no ← BK 号
        self.assertIsNone(env.session())  # 成功后清

    async def test_d4_book_in_session_passes_qa_selection_and_attaches(self):
        """逐问选择覆盖端点默认、交车日/登记人/支付渠道进 booking,附件同会话挂载。"""
        rec = {}

        def fake_run(ep, do):
            return do(_FakeClient(rec), object())

        with (
            mock.patch("services.erp.erp_dms_intake._run_logged_in", side_effect=fake_run),
            mock.patch(
                "services.erp.mrerp_dms_booking_customer.card_from_customer",
                side_effect=lambda client, customer_id, people_id: (
                    rec.__setitem__("customer_lookup", (customer_id, people_id))
                    or bf._card_payload(_review())
                ),
            ),
            mock.patch.object(bf.masters_cache, "refresh_from_client"),
            mock.patch(
                "services.erp.mrerp_dms_company_banks.fetch_company_banks",
                return_value=[["1", "SCB", "SCB"]],
            ),
        ):
            res = bf._book_in_session(
                {"id": "E1", "config": {}},
                _review(),
                attach_files=[
                    {
                        "display_name": "สำเนาบัตรประชาชน",
                        "filename": "idcard.jpg",
                        "content_type": "image/jpeg",
                        "content": _JPEG,
                    },
                    {
                        "display_name": "ใบโอนเงินจอง",
                        "filename": "slip.jpg",
                        "content_type": "image/jpeg",
                        "content": _JPEG,
                    },
                ],
                attach_failed=[{"display_name": "y", "error": "down"}],
            )
        self.assertTrue(res["ok"])
        self.assertEqual(res["booking_no"], "BK123")
        self.assertFalse(res["attach_ok"])  # 下载失败件仍在 → 附件不谎报全挂
        self.assertEqual(res["attached"], 2)
        self.assertEqual([f["display_name"] for f in res["attach_failed"]], ["y"])
        d = rec["defaults"]
        # 顾问归属:开局匹配好的 id/name 一路传到建单层(建单层按 id 严格解析)
        self.assertEqual(d.advisor_id, "335")
        self.assertEqual(d.advisor_name, "sale02")
        self.assertEqual(d.car_id, "c1")
        self.assertEqual(d.paint_id, "p1")
        self.assertEqual(d.place_book_id, "pl1")
        self.assertEqual(d.term_sale_id, "t1")
        self.assertEqual(d.regis_behalf_id, "r1")
        self.assertEqual(rec["customer_id"], "C1")
        self.assertEqual(rec["customer_lookup"], ("C1", "1234567890121"))
        b = rec["booking"]
        self.assertEqual(b.delivery_date_be, "01/01/2570")  # 逐问交车日覆盖
        self.assertEqual(b.regis_name, "บริษัท สมชาย จำกัด")
        self.assertEqual(
            b.payments,
            (
                {
                    "channel": "transfer",
                    "amount": "5000.00",
                    "extra": {"src": "SCB", "dst_id": "1", "dst": "SCB"},
                },
            ),
        )
        self.assertEqual(rec["attach_booking_id"], "BID1")
        self.assertEqual([f["filename"] for f in rec["attach_files"]], ["idcard.jpg", "slip.jpg"])
        self.assertEqual(rec["attach_files"][0]["content_type"], "image/jpeg")

    async def test_d4_attach_failure_appends_attach_note(self):
        """建单成功但附件没挂全 → 回执如实追加 TXT_ATTACH_FAIL,不谎报附件成功。"""
        result = {
            "ok": True,
            "booking_id": "BID1",
            "booking_no": "BK9",
            "attach_ok": False,
            "attached": 0,
            "attach_failed": [
                {"display_name": "ใบโอนเงินจอง", "error": "line content download failed"}
            ],
        }
        with _Env(book_result=result) as env:
            env.store.set_session("T1", "L1", "booking_review", _review())
            await bf.handle_postback(
                _BINDING, _LUID, "rt", cards.ACT_CONFIRM_BOOKING, {"nonce": "N1"}
            )
            await env.drain()
        said = env.push_text.call_args.args[1]
        self.assertIn("BK9", said)
        self.assertTrue(said.endswith(qa_cards.TXT_ATTACH_FAIL))
        # 台账 response_body 带附件结果(json 串)
        response_body = json.loads(env.insert_log.call_args.args[9])
        self.assertFalse(response_body["attach_ok"])
        self.assertEqual(len(response_body["attach_failed"]), 1)

    async def test_d4_download_failure_blocks_only_that_attach(self):
        """LINE 内容下载不到(slip 过期)→ 按 attach_failed 记,不阻断建单。"""
        rec = {}

        def fake_run(ep, do):
            return do(_FakeClient(rec), object())

        with (
            mock.patch("services.erp.erp_dms_intake._run_logged_in", side_effect=fake_run),
            mock.patch(
                "services.erp.mrerp_dms_booking_customer.card_from_customer",
                side_effect=lambda client, customer_id, people_id: bf._card_payload(_review()),
            ),
            mock.patch.object(bf.masters_cache, "refresh_from_client"),
            mock.patch(
                "services.erp.mrerp_dms_company_banks.fetch_company_banks",
                return_value=[["1", "SCB", "SCB"]],
            ),
        ):
            qa = _qa_payload()
            files = qa["files"]
            # slip 下载失败 → 只有 id_card 进挂载
            res = bf._book_in_session(
                {"id": "E1", "config": {}},
                _review(),
                attach_files=[
                    {"display_name": "สำเนาบัตรประชาชน", "filename": "idcard.jpg", "content": _JPEG}
                ],
                attach_failed=[
                    {"display_name": "ใบโอนเงินจอง", "error": "line content download failed"}
                ],
            )
        self.assertTrue(res["ok"])
        self.assertFalse(res["attach_ok"])
        self.assertEqual([f["filename"] for f in rec["attach_files"]], ["idcard.jpg"])

    async def test_d4_create_booking_runs_inside_shared_account_lock(self):
        """create_booking_via_form 在账套级 mrerp_booking_lock 内执行;附件在锁释放后挂载。"""
        rec = {}
        lock_events: list = []

        @contextlib.contextmanager
        def fake_lock(ep, timeout_sec=180.0, poll_sec=1.0):
            rec["lock_ep_id"] = ep.get("id")
            lock_events.append("enter")
            yield True
            lock_events.append("exit")

        class _ProbeClient(_FakeClient):
            def create_booking_via_form(self, *, customer_id, booking, card):
                rec["create_in_lock"] = lock_events == ["enter"]
                return super().create_booking_via_form(
                    customer_id=customer_id, booking=booking, card=card
                )

            def attach_booking_files(self, *, booking_id, files):
                rec["attach_lock_state"] = list(lock_events)
                return super().attach_booking_files(booking_id=booking_id, files=files)

        def fake_run(ep, do):
            return do(_ProbeClient(rec), object())

        ep = {"id": "E1", "config": {"system_url": "https://dms.example.com/dms/index.php"}}
        with (
            mock.patch("services.erp.erp_dms_intake._run_logged_in", side_effect=fake_run),
            mock.patch(
                "services.erp.mrerp_dms_booking_customer.card_from_customer",
                side_effect=lambda client, customer_id, people_id: bf._card_payload(_review()),
            ),
            mock.patch.object(bf.masters_cache, "refresh_from_client"),
            mock.patch(
                "services.erp.mrerp_dms_company_banks.fetch_company_banks",
                return_value=[["1", "SCB", "SCB"]],
            ),
            mock.patch.object(bf, "mrerp_booking_lock", fake_lock),
        ):
            res = bf._book_in_session(
                ep,
                _review(),
                attach_files=[
                    {"display_name": "สำเนาบัตรประชาชน", "filename": "idcard.jpg", "content": _JPEG}
                ],
            )

        self.assertTrue(res["ok"])
        self.assertEqual(rec["lock_ep_id"], "E1")  # 锁按 endpoint 取键
        self.assertTrue(rec["create_in_lock"])  # 建单在锁上下文内执行
        # 附件挂载在锁退出后(慢步骤不进共享锁 · 锁只护取号→提交)
        self.assertEqual(rec["attach_lock_state"], ["enter", "exit"])

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

    async def test_concurrent_login_failure_keeps_draft_and_sends_retry_card(self):
        result = {
            "ok": False,
            "error_code": "ERR_DMS_CONCURRENT_LOGIN",
            "error_friendly": {"th": "บัญชี DMS นี้กำลังถูกใช้งานที่อื่น"},
            "booking_id": "",
        }
        with _Env(book_result=result) as env:
            env.store.set_session("T1", "L1", "booking_review", _review())
            await bf.handle_postback(
                _BINDING, _LUID, "rt", cards.ACT_CONFIRM_BOOKING, {"nonce": "N1"}
            )
            await env.drain()

        card = env.push_msgs.call_args.args[1][0]
        self.assertEqual(card["type"], "flex")
        self.assertEqual(env.session()["state"], "booking_review")
        self.assertEqual(env.session()["ttl_minutes"], 30)
        self.assertNotEqual(env.session()["payload"]["nonce"], "N1")

    async def test_retry_postback_resumes_draft_and_finishes_booking(self):
        failure = {
            "ok": False,
            "error_code": "ERR_DMS_CONCURRENT_LOGIN",
            "error_friendly": {"th": "บัญชี DMS นี้กำลังถูกใช้งานที่อื่น"},
            "booking_id": "",
        }
        success = {
            "ok": True,
            "booking_id": "BID2",
            "booking_no": "BK2",
            "attach_ok": True,
        }
        with (
            _Env() as env,
            mock.patch.object(bf, "_book_in_session", side_effect=[failure, success]),
        ):
            env.store.set_session("T1", "L1", "booking_review", _review())
            await bf.handle_postback(
                _BINDING, _LUID, "rt", cards.ACT_CONFIRM_BOOKING, {"nonce": "N1"}
            )
            await env.drain()
            retry_nonce = env.session()["payload"]["nonce"]
            await bf.handle_postback(
                _BINDING,
                _LUID,
                "rt-retry",
                cards.ACT_RETRY_BOOKING,
                {"nonce": retry_nonce},
            )
            await env.drain()

        self.assertIsNone(env.session())
        self.assertIn("BK2", env.push_text.call_args.args[1])

    async def test_d5_double_click_single_booking(self):
        with _Env(book_result={"ok": True, "booking_no": "BK9", "attach_ok": True}) as env:
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
