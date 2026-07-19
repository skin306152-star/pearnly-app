# -*- coding: utf-8 -*-
"""DMS LINE 菜单层(波2)· menu_flow + flow/cards/webhook 接线。

覆盖:เมนู/问候语弹菜单、menu 态单字 1/2、mode 门控订车串联(customer 不自动订车、
booking/缺省 逐字节照旧)、continue 卡 cid 防串、重拍 nonce 只验不消费、菜单态 เริ่มใหม่ 全清。
fake OCR/DMS(全 mock)+ spy reply/push,dict 背板会话;重活经 flow._spawn 收集后 drain。
"""

import contextlib
import unittest
from unittest import mock

from services.line_dms import cards, flow, menu_flow

_BINDING = {"tenant_id": "T1", "user_id": "U1"}
_LUID = "L1"
_PHONE = "0812345678"

_RAW_ID = {
    "prefix_name": "นาย",
    "first_name": "สมชาย",
    "last_name": "ใจดี",
    "people_id": "1234567890121",
    "birthday_be": "2530-01-01",
    "address": {
        "house_no": "99",
        "moo": "4",
        "soi": "",
        "road": "สุขุมวิท",
        "province": "กรุงเทพมหานคร",
        "district": "คลองเตย",
        "subdistrict": "คลองเตย",
        "zipcode": "10110",
    },
}
_GEO = {
    "provinces": [["1", "กรุงเทพมหานคร"]],
    "districts": [["101", "คลองเตย"]],
    "subdistricts": [["1001", "คลองเตย"]],
    "zipcodes": [["10110", "10110"]],
    "selected": {
        "province_id": "1",
        "district_id": "101",
        "subdistrict_id": "1001",
        "zipcode_id": "10110",
    },
    "text": {"house_no": "99", "moo": "4", "soi": "", "road": "สุขุมวิท"},
}
_PREFIXES = [["17", "นาย"]]


def _ep():
    return {"id": "E1", "config": {}}


def _ocr_ok():
    return {"needs_review": False, "missing_fields": [], "id_card": dict(_RAW_ID)}


def _lookup(scenario, *, customer_id=None):
    return {
        "ok": True,
        "scenario": scenario,
        "match": {"found": scenario == "exact", "customer_id": customer_id, "current_fields": {}},
        "field_diffs": [],
        "candidates": [],
        "geo": _GEO,
        "prefixes": _PREFIXES,
    }


def _pb(action, nonce="", cid=""):
    from urllib.parse import urlencode

    q = {"action": action}
    if nonce:
        q["nonce"] = nonce
    if cid:
        q["cid"] = cid
    return {"data": urlencode(q)}


class FakeStore:
    def __init__(self):
        self.data = {}

    def get_session(self, tenant, luid):
        return self.data.get((str(tenant), str(luid)))

    def set_session(self, tenant, luid, state, payload=None, ttl_minutes=30):
        self.data[(str(tenant), str(luid))] = {"state": state, "payload": payload or {}}

    def clear_session(self, tenant, luid):
        self.data.pop((str(tenant), str(luid)), None)


class _Env:
    """一处装齐 mock;offer_pick 用 spy(不动会话)以便区分「自动订车」与「continue 卡」。"""

    def __init__(self, *, ocr=None, lookup=None, push_result=None):
        self.store = FakeStore()
        self.spawned = []
        self._ocr = ocr or _ocr_ok()
        self._lookup = lookup or _lookup("none")
        self._ep = _ep()
        self._push_result = push_result or {
            "success": True,
            "customer_id": "C99",
            "elapsed_ms": 5,
            "response_body": {},
        }
        self._es = contextlib.ExitStack()

    def __enter__(self):
        es = self._es
        p = lambda *a, **k: es.enter_context(mock.patch.object(*a, **k))  # noqa: E731
        p(flow.store, "get_session", side_effect=self.store.get_session)
        p(flow.store, "set_session", side_effect=self.store.set_session)
        p(flow.store, "clear_session", side_effect=self.store.clear_session)
        p(flow, "_spawn", side_effect=self.spawned.append)
        self.offer = p(flow.booking_flow, "offer_pick", new_callable=mock.AsyncMock)
        self.reply = p(flow.line_client, "reply_text")
        self.reply_msgs = p(flow.line_client, "reply_messages")
        self.push_text = p(flow.line_client, "push_text")
        self.push_msgs = p(flow.line_client, "push_messages")
        p(flow.line_client, "start_loading")
        p(flow.line_client, "download_message_content", return_value=b"imgbytes")
        p(flow.db, "find_user_by_id", return_value={"id": "U1", "tenant_id": "T1"})
        self.insert_log = p(flow.db, "insert_push_log", return_value="LOG1")
        p(flow._id_ocr, "recognize_id_card", return_value=(self._ep, self._ocr, 10))
        p(flow._id_ocr, "resolve_dms_endpoint", return_value=self._ep)
        p(flow._id_ocr, "recent_dms_customer_ids_by_tail", return_value=[])
        self.lookup = p(flow._dms_intake, "recognize_lookup_mrerp_dms", return_value=self._lookup)
        self.push_idcard = p(
            flow._dms_intake, "push_idcard_fields_mrerp_dms", return_value=self._push_result
        )
        return self

    def __exit__(self, *a):
        self._es.close()
        return False

    async def drain(self):
        while self.spawned:
            await self.spawned.pop(0)

    def session(self):
        return self.store.get_session("T1", "L1")

    def continue_card_pushed(self):
        return any(
            c.args[1][0].get("altText") == cards.BTN_CONTINUE_BOOKING
            for c in self.push_msgs.call_args_list
        )


class MenuTriggerTests(unittest.IsolatedAsyncioTestCase):
    async def test_a1_menu_keyword_shows_menu_card(self):
        """A1:เมนู → 菜单卡,会话置 menu。"""
        with _Env() as env:
            await flow.handle_text(_BINDING, _LUID, "rt", "เมนู")
            card = env.reply_msgs.call_args.args[1][0]
            self.assertEqual(card["altText"], cards.TXT_MENU_TITLE)
            self.assertEqual(env.session()["state"], "menu")

    async def test_a1_greeting_shows_menu_card_and_keeps_collected(self):
        """A1:问候语 → 菜单卡;已收料(id_card/phone)并入 menu 态不丢。"""
        with _Env() as env:
            env.store.set_session(
                "T1", "L1", "collecting", {"id_card": dict(_RAW_ID), "phone": _PHONE}
            )
            await flow.handle_text(_BINDING, _LUID, "rt", "สวัสดีครับ")
            msgs = env.reply_msgs.call_args.args[1]
            self.assertEqual(msgs[0]["text"], cards.TXT_MENU_GREETING)  # 问候气泡先行
            self.assertEqual(msgs[1]["altText"], cards.TXT_MENU_TITLE)
            sess = env.session()
            self.assertEqual(sess["state"], "menu")
            self.assertIn("id_card", sess["payload"])
            self.assertEqual(sess["payload"]["phone"], _PHONE)

    async def test_a1_menu_typo_prefix_opens_menu(self):
        """A1:เมน/เมนB 打错字也弹菜单(2026-07-19 真机实拍),不带问候气泡。"""
        with _Env() as env:
            await flow.handle_text(_BINDING, _LUID, "rt", "เมนB")
            msgs = env.reply_msgs.call_args.args[1]
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0]["altText"], cards.TXT_MENU_TITLE)

    async def test_a1_no_session_chatter_shows_menu_card(self):
        """A1:无会话闲聊 → 菜单卡(取代旧 TXT_INTRO 文本)。"""
        with _Env() as env:
            await flow.handle_text(_BINDING, _LUID, "rt", "อยากทำอะไรดี")
            env.reply.assert_not_called()
            card = env.reply_msgs.call_args.args[1][0]
            self.assertEqual(card["altText"], cards.TXT_MENU_TITLE)


class MenuChoiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_a2_menu_button_customer_sets_mode(self):
        """A2:menu 态点「จัดทำข้อมูลลูกค้า」→ customer 模式,无料提示拍卡。"""
        with _Env() as env:
            env.store.set_session("T1", "L1", "menu", {})
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_MENU_CUSTOMER))
            sess = env.session()
            self.assertEqual(sess["state"], "collecting")
            self.assertEqual(sess["payload"]["mode"], "customer")
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_MENU_SEND_CARD)

    async def test_a2_text_1_and_2_map_to_modes(self):
        """A2:menu 态打「1」→ customer,「2」→ booking。"""
        with _Env() as env:
            env.store.set_session("T1", "L1", "menu", {})
            await flow.handle_text(_BINDING, _LUID, "rt", "1")
            self.assertEqual(env.session()["payload"]["mode"], "customer")

            env.store.set_session("T1", "L1", "menu", {})
            await flow.handle_text(_BINDING, _LUID, "rt", "2")
            self.assertEqual(env.session()["payload"]["mode"], "booking")

    async def test_a2_menu_phone_not_eaten_as_menu(self):
        """A2:menu 态发手机号 → 按号码并入(不被吃成菜单),缺卡提示拍卡。"""
        with _Env() as env:
            env.store.set_session("T1", "L1", "menu", {})
            await flow.handle_text(_BINDING, _LUID, "rt", _PHONE)
            sess = env.session()
            self.assertEqual(sess["state"], "collecting")
            self.assertEqual(sess["payload"]["phone"], _PHONE)
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_ASK_CARD)

    async def test_a2_non_menu_digit_1_passes_through(self):
        """A2 守门:非 menu 态的「1」不被当菜单项(交回 flow 走号码透传)。"""
        handled = await menu_flow.handle_text(
            _BINDING, _LUID, "rt", {"state": "collecting", "payload": {}}, "1"
        )
        self.assertFalse(handled)

    async def test_menu_choice_with_full_data_runs_dedup(self):
        """齐料时选菜单项 → 直接查重(不再要料),mode 落到 reviewing 卡。"""
        with _Env(lookup=_lookup("none")) as env:
            env.store.set_session(
                "T1",
                "L1",
                "menu",
                {"id_card": dict(_RAW_ID), "phone": _PHONE, "endpoint_id": "E1"},
            )
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_MENU_BOOKING))
            await env.drain()
            sess = env.session()
            self.assertEqual(sess["state"], "reviewing")
            self.assertEqual(sess["payload"]["mode"], "booking")


class ModeGateTests(unittest.IsolatedAsyncioTestCase):
    async def _seed_reviewing(self, env, mode=""):
        payload = {"phone": _PHONE}
        if mode:
            payload["mode"] = mode
        env.store.set_session("T1", "L1", "collecting", payload)
        await flow.process_image(_BINDING, _LUID, "mid1")
        return env.session()["payload"]["nonce"]

    async def test_a3_customer_save_pushes_done_no_booking(self):
        """A3(2026-07-19 拍板):customer 模式建档成功 → 完成话术,不提订车不推选车。"""
        with _Env(lookup=_lookup("none")) as env:
            nonce = await self._seed_reviewing(env, mode="customer")
            self.assertEqual(env.session()["payload"]["mode"], "customer")
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_CREATE, nonce))
            await env.drain()
            self.assertFalse(env.continue_card_pushed())
            self.assertFalse(env.offer.called)
            self.assertIsNone(env.session())  # 收尾清会话
            texts = [c.args[1] for c in env.push_text.call_args_list]
            self.assertIn(cards.TXT_DONE_SAVED, texts)

    async def test_a3_continue_triggers_offer_pick(self):
        """A3:continue 卡点「ทำใบจองต่อ」(cid 对齐)→ offer_pick。"""
        with _Env() as env:
            env.store.set_session(
                "T1",
                "L1",
                "menu_after_save",
                {
                    "endpoint_id": "E1",
                    "customer_id": "C99",
                    "draft": {"name": "x"},
                    "name": "x",
                    "mode": "customer",
                },
            )
            await flow.handle_postback(
                _BINDING, _LUID, "rt", _pb(cards.ACT_CONTINUE_BOOKING, cid="C99")
            )
            self.assertTrue(env.offer.called)
            self.assertEqual(env.offer.call_args.kwargs["customer_id"], "C99")

    async def test_a3_continue_cid_mismatch_expired(self):
        """A3:continue 的 cid 与会话客户号不符 → 过期话术,不 offer_pick。"""
        with _Env() as env:
            env.store.set_session(
                "T1", "L1", "menu_after_save", {"customer_id": "C99", "mode": "customer"}
            )
            await flow.handle_postback(
                _BINDING, _LUID, "rt", _pb(cards.ACT_CONTINUE_BOOKING, cid="WRONG")
            )
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_EXPIRED)
            self.assertFalse(env.offer.called)

    async def test_a4_no_mode_auto_offers_pick_no_continue_card(self):
        """A4 守门:mode 缺省(不经菜单直拍)→ offer_pick 照旧,不出 continue 卡。"""
        with _Env(lookup=_lookup("none")) as env:
            nonce = await self._seed_reviewing(env)  # 无 mode
            self.assertEqual(env.session()["payload"]["mode"], "")
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_CREATE, nonce))
            await env.drain()
            self.assertTrue(env.offer.called)
            self.assertEqual(env.offer.call_args.kwargs["customer_id"], "C99")
            self.assertFalse(env.continue_card_pushed())

    async def test_a4_exact_same_no_mode_previews_then_keep_offers_pick(self):
        """A4(2026-07-19 拍板):缺省模式 exact 零差异 → 也先出预览卡;点保持才 offer_pick。"""
        with _Env(lookup=_lookup("exact", customer_id="C7")) as env:
            env.store.set_session("T1", "L1", "collecting", {"phone": _PHONE})
            await flow.process_image(_BINDING, _LUID, "mid1")
            await env.drain()
            self.assertFalse(env.offer.called)
            self.assertEqual(env.session()["state"], "reviewing")
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_KEEP))
            await env.drain()
            self.assertTrue(env.offer.called)
            self.assertEqual(env.offer.call_args.kwargs["customer_id"], "C7")
            self.assertFalse(env.continue_card_pushed())

    async def test_exact_same_customer_mode_shows_preview_card(self):
        """customer 模式 exact 零差异 → 同资料预览卡(保持/修改),识别错有入口改,不提订车。"""
        with _Env(lookup=_lookup("exact", customer_id="C7")) as env:
            env.store.set_session("T1", "L1", "collecting", {"phone": _PHONE, "mode": "customer"})
            await flow.process_image(_BINDING, _LUID, "mid1")
            await env.drain()
            self.assertFalse(env.continue_card_pushed())
            self.assertFalse(env.offer.called)
            sess = env.session()
            self.assertEqual(sess["state"], "reviewing")
            self.assertEqual(sess["payload"]["customer_id"], "C7")
            card = env.push_msgs.call_args.args[1][0]
            self.assertEqual(card["altText"], cards.same_customer_card({}, "x")["altText"])

    async def test_exact_same_preview_keep_finishes_without_booking(self):
        """同资料预览卡点「ใช้ข้อมูลเดิม」→ same 完成话术 + 清会话,不订车。"""
        with _Env(lookup=_lookup("exact", customer_id="C7")) as env:
            env.store.set_session("T1", "L1", "collecting", {"phone": _PHONE, "mode": "customer"})
            await flow.process_image(_BINDING, _LUID, "mid1")
            await env.drain()
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_KEEP))
            await env.drain()
            self.assertIsNone(env.session())
            self.assertFalse(env.offer.called)
            texts = [c.args[1] for c in env.push_text.call_args_list]
            self.assertIn(cards.TXT_DONE_SAME, texts)


class RetakeTests(unittest.IsolatedAsyncioTestCase):
    async def test_a5_retake_clears_card_keeps_phone(self):
        """A5:reviewing 点重拍(nonce 对)→ 清 id_card 留 phone/mode 回 collecting。"""
        with _Env() as env:
            env.store.set_session(
                "T1",
                "L1",
                "reviewing",
                {
                    "nonce": "N1",
                    "id_card": {"people_id": "x"},
                    "phone": _PHONE,
                    "mode": "customer",
                    "endpoint_id": "E1",
                },
            )
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_RETAKE, nonce="N1"))
            sess = env.session()
            self.assertEqual(sess["state"], "collecting")
            self.assertNotIn("id_card", sess["payload"])
            self.assertEqual(sess["payload"]["phone"], _PHONE)
            self.assertEqual(sess["payload"]["mode"], "customer")
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_RETAKE)

    async def test_a5_retake_wrong_nonce_refused_session_untouched(self):
        """A5:重拍 nonce 不符 → 过期话术,会话原封不动。"""
        with _Env() as env:
            env.store.set_session(
                "T1", "L1", "reviewing", {"nonce": "N1", "id_card": {"people_id": "x"}}
            )
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_RETAKE, nonce="BAD"))
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_EXPIRED)
            sess = env.session()
            self.assertEqual(sess["state"], "reviewing")
            self.assertIn("id_card", sess["payload"])


class ResetTests(unittest.IsolatedAsyncioTestCase):
    async def test_a7_reset_from_menu_states_clears_all(self):
        """A7:menu / menu_after_save 态发 เริ่มใหม่ → 全清。"""
        with _Env() as env:
            for state in ("menu", "menu_after_save"):
                env.store.set_session("T1", "L1", state, {"customer_id": "C99", "mode": "customer"})
                await flow.handle_text(_BINDING, _LUID, "rt", cards.BTN_RESTART)
                self.assertIsNone(env.session())
                self.assertEqual(env.reply.call_args.args[1], cards.TXT_RESET)


if __name__ == "__main__":
    unittest.main()
