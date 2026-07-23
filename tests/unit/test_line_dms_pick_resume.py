# -*- coding: utf-8 -*-
"""选车链接过期后的恢复路径(P1-12)· 待选车会话不被文本冲掉 + 显式重发入口。

覆盖:picking/booking_review 态收到任何文本都不覆写会话(手上那条链接不被掐死)、
重发卡按钮 cid 对齐才重签 token、重发不碰 OCR 不写档、缺客户号时如实说而不是再要材料。
"""

import contextlib
import unittest
from unittest import mock
from urllib.parse import urlencode

from services.line_dms import cards, flow, pick_resume

_BINDING = {"tenant_id": "T1", "user_id": "U1"}
_LUID = "L1"
_PHONE = "0812345678"

_PICK_PAYLOAD = {
    "nonce": "N1",
    "endpoint_id": "E1",
    "customer_id": "C1",
    "user_id": "U1",
    "draft": {"people_id": "1234567890121", "name": "สมชาย"},
    "name": "สมชาย ใจดี",
}


def _pb(action, cid=""):
    q = {"action": action}
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
    """会话用 dict 背板;offer_pick 用 spy(重发只需断言签发被触发,不跑真签名)。"""

    def __init__(self):
        self.store = FakeStore()
        self._es = contextlib.ExitStack()

    def __enter__(self):
        es = self._es
        p = lambda *a, **k: es.enter_context(mock.patch.object(*a, **k))  # noqa: E731
        p(flow.store, "get_session", side_effect=self.store.get_session)
        p(flow.store, "set_session", side_effect=self.store.set_session)
        p(flow.store, "clear_session", side_effect=self.store.clear_session)
        p(flow, "_spawn", side_effect=lambda coro: coro.close())
        self.offer = p(pick_resume.booking_flow, "offer_pick", new_callable=mock.AsyncMock)
        self.reply = p(flow.line_client, "reply_text")
        self.reply_msgs = p(flow.line_client, "reply_messages")
        return self

    def __exit__(self, *a):
        self._es.close()
        return False

    def seed(self, state, payload=None):
        self.store.set_session(
            "T1", "L1", state, dict(_PICK_PAYLOAD if payload is None else payload)
        )

    def session(self):
        return self.store.get_session("T1", "L1")

    def replied_cards(self):
        return [c.args[1] for c in self.reply_msgs.call_args_list]


def _button_data(card):
    return [
        b["action"]["data"]
        for b in card["contents"]["footer"]["contents"]
        if b.get("type") == "button"
    ]


class PickingTextGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_phone_text_does_not_overwrite_picking_session(self):
        """带数字的文本曾把会话冲成 collecting → 没过期的链接当场 401。现在会话纹丝不动。"""
        with _Env() as env:
            env.seed("picking")
            await flow.handle_text(_BINDING, _LUID, "rt", _PHONE)
            sess = env.session()
            self.assertEqual(sess["state"], "picking")
            self.assertEqual(sess["payload"], _PICK_PAYLOAD)

    async def test_chatter_offers_resume_card_not_ask_for_id(self):
        """已建档的用户不该再听见「请发身份证和手机号」,给的是重发按钮。"""
        with _Env() as env:
            env.seed("picking")
            await flow.handle_text(_BINDING, _LUID, "rt", "ราคาเท่าไร")
            env.reply.assert_not_called()
            card = env.replied_cards()[0][0]
            self.assertEqual(card["altText"], cards.BTN_REISSUE_PICK)
            self.assertIn(f"action={cards.ACT_REISSUE_PICK}&cid=C1", _button_data(card))

    async def test_booking_review_state_protected_too(self):
        """面板已提交、等确认那段同样受保护(会话是重发的唯一凭据)。"""
        with _Env() as env:
            env.seed("booking_review")
            await flow.handle_text(_BINDING, _LUID, "rt", "1")
            self.assertEqual(env.session()["state"], "booking_review")
            self.assertEqual(env.replied_cards()[0][0]["altText"], cards.BTN_REISSUE_PICK)

    async def test_menu_keyword_keeps_session_and_appends_resume(self):
        """เมนู 仍出菜单(用户的合法诉求),但不落 menu 态,并附重发卡带他回选车。"""
        with _Env() as env:
            env.seed("picking")
            await flow.handle_text(_BINDING, _LUID, "rt", "เมนู")
            self.assertEqual(env.session()["state"], "picking")
            msgs = env.replied_cards()[0]
            self.assertEqual(msgs[0]["altText"], cards.TXT_MENU_TITLE)
            self.assertEqual(msgs[1]["altText"], cards.BTN_REISSUE_PICK)

    async def test_lost_customer_id_says_so_instead_of_asking_material(self):
        """picking 态但档已丢:如实说这单过期了,不把人送回付费起点。"""
        with _Env() as env:
            env.seed("picking", {})
            await flow.handle_text(_BINDING, _LUID, "rt", "ราคาเท่าไร")
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_EXPIRED)
            self.assertEqual(env.session()["state"], "picking")

    async def test_menu_choice_from_picking_says_booking_abandoned(self):
        """菜单卡的按钮会覆写会话、掐死选车链接 —— 用户可以放弃,但系统必须说一声。"""
        with _Env() as env:
            env.seed("picking", {"customer_id": "C99", "endpoint_id": "E1"})
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_MENU_CUSTOMER))
            said = env.reply.call_args.args[1]
            self.assertIn(cards.TXT_PICK_ABANDONED, said)
            self.assertEqual(env.session()["state"], "collecting")

    async def test_collecting_state_untouched_by_guard(self):
        """守门:非待选车态照旧走原路(号码仍被当号码收)。"""
        with _Env() as env:
            env.seed("collecting", {})
            await flow.handle_text(_BINDING, _LUID, "rt", _PHONE)
            self.assertEqual(env.session()["payload"]["phone"], _PHONE)


class ReissueTests(unittest.IsolatedAsyncioTestCase):
    async def test_reissue_resigns_from_session_without_ocr(self):
        """重发只吃会话里现成的档:零 OCR、零写档,endpoint/draft/name 原样带回。"""
        with _Env() as env:
            env.seed("picking")
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_REISSUE_PICK, cid="C1"))
            kwargs = env.offer.call_args.kwargs
            self.assertEqual(kwargs["customer_id"], "C1")
            self.assertEqual(kwargs["endpoint_id"], "E1")
            self.assertEqual(kwargs["draft"], _PICK_PAYLOAD["draft"])
            self.assertEqual(kwargs["name"], _PICK_PAYLOAD["name"])

    async def test_reissue_from_booking_review_allowed(self):
        with _Env() as env:
            env.seed("booking_review")
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_REISSUE_PICK, cid="C1"))
            self.assertTrue(env.offer.called)

    async def test_reissue_cid_mismatch_refused(self):
        """翻聊天记录点到别人那张卡:cid 对不上会话客户号 → 拒,不串档。"""
        with _Env() as env:
            env.seed("picking")
            await flow.handle_postback(
                _BINDING, _LUID, "rt", _pb(cards.ACT_REISSUE_PICK, cid="WRONG")
            )
            self.assertFalse(env.offer.called)
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_EXPIRED)

    async def test_reissue_outside_pick_states_refused(self):
        """会话已走到别的态(或没了)→ 旧重发卡不再是白拿链接的后门。"""
        with _Env() as env:
            env.seed("collecting", {"customer_id": "C1"})
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_REISSUE_PICK, cid="C1"))
            self.assertFalse(env.offer.called)
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_EXPIRED)


class PendingSessionTests(unittest.TestCase):
    def test_is_pending_only_pick_states(self):
        self.assertTrue(pick_resume.is_pending({"state": "picking", "payload": {}}))
        self.assertTrue(pick_resume.is_pending({"state": "booking_review", "payload": {}}))
        self.assertFalse(pick_resume.is_pending({"state": "reviewing", "payload": {}}))
        self.assertFalse(pick_resume.is_pending(None))

    def test_pending_customer_id_is_pure_lookup(self):
        """状态判定归 is_pending;这里只取值,别再兼任守卫(两处判据就会漂移)。"""
        self.assertEqual(
            pick_resume.pending_customer_id({"state": "picking", "payload": {"customer_id": "C1"}}),
            "C1",
        )
        self.assertEqual(pick_resume.pending_customer_id({"payload": {}}), "")
        self.assertEqual(pick_resume.pending_customer_id(None), "")


if __name__ == "__main__":
    unittest.main()
