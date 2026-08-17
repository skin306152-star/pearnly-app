# -*- coding: utf-8 -*-
"""DMS 订车逐问(DL-7 · batch 1/3)状态机单测:8 步逐问 + 支付循环 + 预览。

FakeStore + spy reply/push(照 test_line_dms_booking 范式)· masters 用固定行表,
masters_cache 与端点解析全 mock,零网络零登录。行表形状 [id, code, name, ...] 与
DMS bshsd 主档一致。
"""

import contextlib
import os
import unittest
from datetime import date
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-for-line-dms-qa-32bytes-long")

from services.erp import erp_dms_push  # noqa: E402
from services.line_binding import line_client  # noqa: E402
from services.line_dms import booking_qa as qa  # noqa: E402
from services.line_dms import qa_cards  # noqa: E402

_TID, _LUID = "T1", "L1"
_ADVISOR = {"id": "335", "name": "sale02"}

_CARS = [
    ["c1", "DMX", "D-Max"],
    ["c2", "MUX", "MU-X"],
    ["c3", "HRV", "Honda HR-V"],
]
_PAINTS = [["p1", "", "ขาว"], ["p2", "", "ดำ"], ["p3", "", "เทา"]]
_PLACES = [["pl1", "", "สาขาบางนา"], ["pl2", "", "สาขารามอินทรา"]]
_TERMS = [["t1", "", "เงินสด"], ["t2", "", "ผ่อน"]]
_REGIS = [["r1", "", "บริษัท"], ["r2", "", "บุคคลธรรมดา"]]
_COMPANY_BANKS = [["1", "SCB", "SCB"]]


class FakeStore:
    def __init__(self):
        self.data = {}

    def get_session(self, tenant, luid):
        return self.data.get((str(tenant), str(luid)))

    def set_session(self, tenant, luid, state, payload=None, ttl_minutes=None):
        # 缺省 TTL 走真实 store 的状态查表,锁住 booking_qa 的 120 分钟存活。
        if ttl_minutes is None:
            from services.line_dms import store as _store

            ttl_minutes = _store.state_ttl_minutes(state)
        self.data[(str(tenant), str(luid))] = {
            "state": state,
            "payload": payload or {},
            "ttl_minutes": ttl_minutes,
        }

    def clear_session(self, tenant, luid):
        self.data.pop((str(tenant), str(luid)), None)

    def get_binding_by_line_user(self, luid):
        return {"tenant_id": "T1", "user_id": "U1"}


class Env:
    def __init__(
        self,
        cars=_CARS,
        paints=_PAINTS,
        advisor=_ADVISOR,
        dms_username="sale02",
        company_banks=_COMPANY_BANKS,
    ):
        self.store = FakeStore()
        self.cars = cars
        self.paints = paints
        self.paints_calls = []
        self.advisor = advisor
        self.dms_username = dms_username
        self.company_banks = company_banks
        self.es = contextlib.ExitStack()

    def __enter__(self):
        es = self.es
        p = lambda *a, **k: es.enter_context(mock.patch.object(*a, **k))  # noqa: E731
        p(qa.store, "get_session", side_effect=self.store.get_session)
        p(qa.store, "set_session", side_effect=self.store.set_session)
        p(qa.store, "clear_session", side_effect=self.store.clear_session)
        p(qa.store, "get_binding_by_line_user", side_effect=self.store.get_binding_by_line_user)
        p(qa._id_ocr, "resolve_dms_endpoint", return_value={"id": "E1", "config": {}})
        p(
            qa.masters_cache,
            "get_masters",
            return_value={
                "cars": self.cars,
                "place_books": _PLACES,
                "term_sales": _TERMS,
                "regis_behalfs": _REGIS,
                "company_banks": self.company_banks,
            },
        )

        def _paints(ep, cid, *a):
            self.paints_calls.append(cid)
            return self.paints

        p(qa.masters_cache, "get_paints", side_effect=_paints)
        p(
            qa.dms_advisor,
            "resolve_operator_advisor",
            return_value=(self.advisor, self.dms_username),
        )
        self.reply = p(line_client, "reply_messages")
        self.push = p(line_client, "push_messages")
        return self

    def __exit__(self, *a):
        self.es.close()
        return False

    def session(self):
        return self.store.get_session(_TID, _LUID)

    def qa_payload(self):
        return (self.session() or {}).get("payload", {}).get("qa") or {}


def _qa(step="slip", **over):
    base = {
        "step": step,
        "endpoint_id": "E1",
        "customer": {"id": "C1", "name": "สมชาย ใจดี"},
        "advisor": dict(_ADVISOR),
        "files": {"id_card_mid": "mid-card", "slip_mid": None},
        "answers": {},
        "payments": [],
        "pending_channel": {},
        "audit": [],
    }
    base.update(over)
    return base


def _seed(env, qa_dict):
    env.store.set_session(_TID, _LUID, "booking_qa", {"qa": qa_dict})


def _replied_text(env):
    return env.reply.call_args.args[1][0]["text"]


def _replied_items(env):
    return env.reply.call_args.args[1][0]["quickReply"]["items"]


def _pushed_text(env):
    return env.push.call_args.args[1][0]["text"]


class BookingQaTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_initializes_payload_and_asks_slip(self):
        with Env() as env:
            await qa.start(_TID, _LUID, "E1", "C1", "สมชาย ใจดี", "mid-card", "rt")
            sess = env.session()
            self.assertEqual(sess["state"], "booking_qa")
            self.assertGreater(sess["ttl_minutes"], 30)  # 120 分钟,别按默认 30 过期
            p = env.qa_payload()
            self.assertEqual(p["step"], "slip")
            self.assertEqual(p["customer"], {"id": "C1", "name": "สมชาย ใจดี"})
            self.assertEqual(p["files"]["id_card_mid"], "mid-card")
            self.assertIsNone(p["files"]["slip_mid"])
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_SLIP)
            # 提成归属开局定死在 qa.advisor,建单执行器只认这一处
            self.assertEqual(p["advisor"], _ADVISOR)
            self.assertEqual(set(sess["payload"]), {"qa"})

    async def test_start_blocked_when_advisor_unmatched(self):
        """认不出顾问 → 发拦截话术且不开局(答完 8 问才拦 = 白占销售时间)。"""
        with Env(advisor=None, dms_username="dmstest") as env:
            env.store.set_session(_TID, _LUID, "reviewing", {"nonce": "n"})  # 上一阶段的复述卡
            await qa.start(_TID, _LUID, "E1", "C1", "สมชาย ใจดี", "mid-card", "rt")
            self.assertIsNone(env.session())  # 连旧会话一起清,别让下一句话撞旧卡
            # 拦截话术走 push:顾问解析可能含一次慢登录,reply_token 早过期了
            env.reply.assert_not_called()
            said = _pushed_text(env)
            self.assertIn("dmstest", said)
            self.assertIn("ที่ปรึกษาการขาย", said)

    async def test_start_blocked_message_degrades_without_username(self):
        with Env(advisor=None, dms_username="") as env:
            await qa.start(_TID, _LUID, "E1", "C1", "สมชาย ใจดี", "mid-card", "rt")
            self.assertIsNone(env.session())
            self.assertEqual(_pushed_text(env), qa_cards.TXT_ADVISOR_BLOCK_NO_USER)

    async def test_block_copy_stays_in_sync_with_error_catalog(self):
        """补救指引单源:改了错误码目录的泰语原文,LINE 拦截话术必须跟着变(防两处漂)。"""
        catalog = erp_dms_push._DMS_FRIENDLY["ERR_DMS_ADVISOR_UNMATCHED"]["th"]
        self.assertIn(catalog, qa_cards.TXT_ADVISOR_BLOCK)
        self.assertIn(catalog, qa_cards.TXT_ADVISOR_BLOCK_NO_USER)

    async def test_start_without_endpoint_does_not_open_session(self):
        with Env() as env:
            with mock.patch.object(qa._id_ocr, "resolve_dms_endpoint", return_value=None):
                await qa.start(_TID, _LUID, "E1", "C1", "สมชาย ใจดี", "mid-card", "rt")
            self.assertIsNone(env.session())
            self.assertEqual(_pushed_text(env), qa_cards.TXT_NO_ENDPOINT)

    # ── slip ──────────────────────────────────────────────────────────────
    async def test_slip_image_advances_to_place(self):
        with Env() as env:
            _seed(env, _qa())
            self.assertTrue(await qa.handle_image(_TID, _LUID, "mid-slip", "rt"))
            p = env.qa_payload()
            self.assertEqual(p["files"]["slip_mid"], "mid-slip")
            self.assertEqual(p["step"], "place")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_PLACE)

    async def test_slip_cash_word_skips_without_slip(self):
        with Env() as env:
            _seed(env, _qa())
            self.assertTrue(await qa.handle_text(_TID, _LUID, "เงินสด", "rt"))
            p = env.qa_payload()
            self.assertIsNone(p["files"]["slip_mid"])
            self.assertEqual(p["step"], "place")
            self.assertEqual(p["audit"][-1]["input"], "เงินสด")

    async def test_slip_other_text_reprompts(self):
        with Env() as env:
            _seed(env, _qa())
            self.assertTrue(await qa.handle_text(_TID, _LUID, "hello", "rt"))
            self.assertEqual(env.qa_payload()["step"], "slip")
            self.assertEqual(_replied_text(env), qa_cards.TXT_SLIP_ONLY_IMAGE)

    # ── place ─────────────────────────────────────────────────────────────
    async def test_place_button(self):
        with Env() as env:
            _seed(env, _qa("place"))
            self.assertTrue(await qa.handle_postback(_TID, _LUID, "qa:place:pl1", {}, "rt"))
            p = env.qa_payload()
            self.assertEqual(p["answers"]["place"], {"id": "pl1", "name": "สาขาบางนา"})
            self.assertEqual(p["step"], "car_search")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_CAR)

    # ── car_search 三分支 ─────────────────────────────────────────────────
    async def test_car_search_none(self):
        with Env() as env:
            _seed(env, _qa("car_search"))
            await qa.handle_text(_TID, _LUID, "zzz", "rt")
            self.assertEqual(_replied_text(env), qa_cards.TXT_CAR_NONE)
            self.assertEqual(env.qa_payload()["step"], "car_search")

    async def test_car_search_hits_show_buttons(self):
        with Env() as env:
            _seed(env, _qa("car_search"))
            await qa.handle_text(_TID, _LUID, "dmax", "rt")
            msg = env.reply.call_args.args[1][0]
            self.assertEqual(msg["text"], qa_cards.TXT_CAR_PICK.format(n=1))
            items = msg["quickReply"]["items"]
            self.assertEqual(items[0]["action"]["data"], "qa:car:c1")
            self.assertEqual(env.qa_payload()["step"], "car_search")  # 等按钮,不推进

    async def test_car_search_many_prompts_specific(self):
        cars = [[f"c{i}", f"C{i}", f"Toyota Vios {i}"] for i in range(12)]
        with Env(cars=cars) as env:
            _seed(env, _qa("car_search"))
            await qa.handle_text(_TID, _LUID, "vios", "rt")
            self.assertEqual(_replied_text(env), qa_cards.TXT_CAR_MANY.format(n=12))

    async def test_car_button_selects(self):
        with Env() as env:
            _seed(env, _qa("car_search"))
            await qa.handle_postback(_TID, _LUID, "qa:car:c1", {}, "rt")
            p = env.qa_payload()
            self.assertEqual(p["answers"]["car"]["id"], "c1")
            self.assertEqual(p["answers"]["car"]["label"], "DMX D-Max")
            self.assertEqual(p["step"], "paint")
            self.assertEqual(env.paints_calls[-1], "c1")  # 颜色惰性级联带 car_id

    # ── paint ─────────────────────────────────────────────────────────────
    async def test_paint_button_then_date_picker(self):
        with Env() as env:
            _seed(env, _qa("paint", answers={"car": {"id": "c1", "label": "DMX D-Max"}}))
            self.assertTrue(await qa.handle_postback(_TID, _LUID, "qa:paint:p1", {}, "rt"))
            p = env.qa_payload()
            self.assertEqual(p["answers"]["paint"], {"id": "p1", "name": "ขาว"})
            self.assertEqual(p["step"], "date")
            action = _replied_items(env)[0]["action"]
            self.assertEqual(action["type"], "datetimepicker")
            self.assertEqual(action["mode"], "date")
            self.assertEqual(action["data"], "qa:date")

    async def test_paint_text_exact_one_hit_selects(self):
        with Env() as env:
            _seed(env, _qa("paint", answers={"car": {"id": "c1", "label": "DMX D-Max"}}))
            await qa.handle_text(_TID, _LUID, "ขาว", "rt")
            p = env.qa_payload()
            self.assertEqual(p["answers"]["paint"]["id"], "p1")
            self.assertEqual(p["step"], "date")

    async def test_paint_text_no_hit_reprompts(self):
        with Env() as env:
            _seed(env, _qa("paint", answers={"car": {"id": "c1", "label": "DMX D-Max"}}))
            await qa.handle_text(_TID, _LUID, "ม่วง", "rt")
            self.assertEqual(env.qa_payload()["step"], "paint")
            self.assertIn(qa_cards.TXT_ASK_PAINT.format(car="DMX D-Max"), _replied_text(env))

    def test_ask_date_picker_bounds(self):
        msg = qa_cards.ask_date(date(2026, 8, 9))
        action = msg["quickReply"]["items"][0]["action"]
        self.assertEqual(action["initial"], "2026-08-16")
        self.assertEqual(action["min"], "2026-08-09")
        self.assertEqual(action["max"], "2028-08-09")

    # ── date 公历→佛历 ────────────────────────────────────────────────────
    async def test_date_postback_converts_to_be(self):
        with Env() as env:
            _seed(env, _qa("date"))
            self.assertTrue(
                await qa.handle_postback(_TID, _LUID, "qa:date", {"date": "2026-08-20"}, "rt")
            )
            p = env.qa_payload()
            self.assertEqual(p["answers"]["delivery_date_be"], "20/08/2569")
            self.assertEqual(p["step"], "term")

    async def test_date_text_reprompts_picker(self):
        with Env() as env:
            _seed(env, _qa("date"))
            await qa.handle_text(_TID, _LUID, "พรุ่งนี้", "rt")
            self.assertEqual(env.qa_payload()["step"], "date")
            self.assertEqual(_replied_items(env)[0]["action"]["type"], "datetimepicker")

    # ── term / regis / regis_name ─────────────────────────────────────────
    async def test_term_then_regis_buttons(self):
        with Env() as env:
            _seed(env, _qa("term"))
            await qa.handle_postback(_TID, _LUID, "qa:term:t1", {}, "rt")
            p = env.qa_payload()
            self.assertEqual(p["answers"]["term"], {"id": "t1", "name": "เงินสด"})
            self.assertEqual(p["step"], "regis")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_REGIS)
            await qa.handle_postback(_TID, _LUID, "qa:regis:r1", {}, "rt")
            p = env.qa_payload()
            self.assertEqual(p["answers"]["regis"], {"id": "r1", "name": "บริษัท"})
            self.assertEqual(p["step"], "regis_name")

    async def test_regis_name_button_uses_card_name(self):
        with Env() as env:
            _seed(env, _qa("regis_name"))
            await qa.handle_postback(_TID, _LUID, "qa:regisname:card", {}, "rt")
            p = env.qa_payload()
            self.assertEqual(p["answers"]["regis_name"], "สมชาย ใจดี")
            self.assertEqual(p["step"], "pay_channel")

    async def test_regis_name_typed(self):
        with Env() as env:
            _seed(env, _qa("regis_name"))
            await qa.handle_text(_TID, _LUID, "นายแดง ใจงาม", "rt")
            p = env.qa_payload()
            self.assertEqual(p["answers"]["regis_name"], "นายแดง ใจงาม")
            self.assertEqual(p["step"], "pay_channel")

    # ── 支付:现金单渠道 ───────────────────────────────────────────────────
    async def test_cash_single_channel(self):
        with Env() as env:
            _seed(env, _qa("pay_channel"))
            await qa.handle_postback(_TID, _LUID, "qa:pay:cash", {}, "rt")
            self.assertEqual(env.qa_payload()["step"], "pay_amount")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_AMOUNT.format(channel="เงินสด"))
            await qa.handle_text(_TID, _LUID, "5000", "rt")
            p = env.qa_payload()
            self.assertEqual(p["payments"], [{"channel": "cash", "amount": "5000.00"}])
            self.assertEqual(p["pending_channel"], {})
            self.assertEqual(p["step"], "pay_more")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_MORE)

    # ── 支付:非法金额重问 ─────────────────────────────────────────────────
    async def test_bad_amount_reprompts(self):
        with Env() as env:
            _seed(env, _qa("pay_amount", pending_channel={"channel": "cash"}))
            for bad in ("abc", "0", "99999999999999", "1.234", ""):
                await qa.handle_text(_TID, _LUID, bad, "rt")
                self.assertEqual(_replied_text(env), qa_cards.TXT_BAD_AMOUNT)
                self.assertEqual(env.qa_payload()["step"], "pay_amount")
            self.assertEqual(env.qa_payload()["payments"], [])

    # ── 支付:transfer 渠道 + 无凭证 → slip_after ──────────────────────────
    async def test_transfer_without_slip_goes_slip_after(self):
        with Env() as env:
            _seed(env, _qa("pay_channel"))
            await qa.handle_postback(_TID, _LUID, "qa:pay:transfer", {}, "rt")
            await qa.handle_text(_TID, _LUID, "10000", "rt")
            p = env.qa_payload()
            self.assertEqual(p["step"], "pay_src")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_PAY_SRC)
            await qa.handle_text(_TID, _LUID, "-", "rt")
            self.assertEqual(env.qa_payload()["step"], "pay_dst")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_PAY_DST)
            self.assertEqual(_replied_items(env)[0]["action"]["data"], "qa:bank:1")
            await qa.handle_text(_TID, _LUID, "SCB", "rt")
            self.assertEqual(env.qa_payload()["step"], "pay_dst")
            await qa.handle_postback(_TID, _LUID, "qa:bank:1", {}, "rt")
            p = env.qa_payload()
            self.assertEqual(p["step"], "pay_more")
            self.assertEqual(p["payments"][0]["channel"], "transfer")
            self.assertEqual(p["payments"][0]["extra"], {"src": "", "dst_id": "1", "dst": "SCB"})
            # done → 有转账渠道但没凭证 → 补要
            await qa.handle_postback(_TID, _LUID, "qa:more:done", {}, "rt")
            self.assertEqual(env.qa_payload()["step"], "slip_after")
            self.assertEqual(_replied_text(env), qa_cards.TXT_NEED_SLIP)
            # 此处打 เงินสด 不放行,仍补要
            await qa.handle_text(_TID, _LUID, "เงินสด", "rt")
            self.assertEqual(env.qa_payload()["step"], "slip_after")
            self.assertEqual(_replied_text(env), qa_cards.TXT_NEED_SLIP)
            # 收图 → 直接预览
            await qa.handle_image(_TID, _LUID, "mid-slip2", "rt")
            sess = env.session()
            self.assertEqual(sess["state"], "booking_review")
            self.assertEqual(sess["payload"]["qa"]["files"]["slip_mid"], "mid-slip2")
            self.assertTrue(sess["payload"]["nonce"])

    async def test_transfer_blocks_when_company_bank_master_is_empty(self):
        with Env(company_banks=[]) as env:
            _seed(
                env,
                _qa(
                    "pay_dst",
                    pending_channel={
                        "channel": "transfer",
                        "amount": "1500.00",
                        "extra": {"src": "บัญชีลูกค้า 123-4"},
                    },
                ),
            )
            await qa.send_step(_TID, _LUID, env.qa_payload(), "pay_dst", "rt")
            self.assertEqual(_replied_text(env), qa_cards.TXT_NO_COMPANY_BANK)
            self.assertNotIn("quickReply", env.reply.call_args.args[1][0])
            await qa.handle_text(_TID, _LUID, "SCB", "rt")
            self.assertEqual(env.qa_payload()["step"], "pay_dst")
            self.assertEqual(env.qa_payload()["payments"], [])

    # ── 支付:cheque 补充信息 ──────────────────────────────────────────────
    async def test_cheque_ref(self):
        with Env() as env:
            _seed(env, _qa("pay_channel"))
            await qa.handle_postback(_TID, _LUID, "qa:pay:cheque", {}, "rt")
            await qa.handle_text(_TID, _LUID, "5000", "rt")
            self.assertEqual(env.qa_payload()["step"], "pay_ref")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_CHEQUE_REF)
            await qa.handle_text(_TID, _LUID, "CHK123 KTB", "rt")
            p = env.qa_payload()
            self.assertEqual(p["payments"][0]["extra"], {"ref": "CHK123 KTB"})
            self.assertEqual(p["step"], "pay_more")

    # ── 支付:多渠道 + Decimal 求和 ────────────────────────────────────────
    async def test_multi_channel_sum_and_duplicate_channel(self):
        with Env() as env:
            _seed(env, _qa("pay_more"))
            await qa.handle_postback(_TID, _LUID, "qa:more:add", {}, "rt")
            self.assertEqual(env.qa_payload()["step"], "pay_channel")
            await qa.handle_postback(_TID, _LUID, "qa:pay:cash", {}, "rt")
            await qa.handle_text(_TID, _LUID, "1,000.50", "rt")  # 泰式千分位也接受
            await qa.handle_postback(_TID, _LUID, "qa:more:add", {}, "rt")
            await qa.handle_postback(_TID, _LUID, "qa:pay:cash", {}, "rt")
            await qa.handle_text(_TID, _LUID, "2000", "rt")
            p = env.qa_payload()
            self.assertEqual(len(p["payments"]), 2)  # 同渠道可重复选,各记一条
            amounts = [pay["amount"] for pay in p["payments"]]
            self.assertEqual(amounts, ["1000.50", "2000.00"])
            total = qa_cards.deposit_total(p["payments"])
            self.assertEqual(str(total), "3000.50")

    # ── 预览卡 ────────────────────────────────────────────────────────────
    async def test_preview_card_full_fields(self):
        # 无 summary 的 legacy qa → 回退从 draft 拼五要素(邮编并入地址行)。
        qa_dict = _qa(
            "pay_more",
            draft={
                "people_id": "1234567890121",
                "birthday_be": "01/01/2530",
                "house_no": "99",
                "zipcode": "10110",
            },
            answers={
                "place": {"id": "pl1", "name": "สาขาบางนา"},
                "car": {"id": "c1", "label": "DMX D-Max"},
                "paint": {"id": "p1", "name": "ขาว"},
                "delivery_date_be": "20/08/2569",
                "term": {"id": "t1", "name": "เงินสด"},
                "regis": {"id": "r1", "name": "บริษัท"},
                "regis_name": "สมชาย ใจดี",
            },
            payments=[{"channel": "cash", "amount": "5000.00"}],
        )
        with Env() as env:
            _seed(env, qa_dict)
            await qa.handle_postback(_TID, _LUID, "qa:more:done", {}, "rt")
            sess = env.session()
            self.assertEqual(sess["state"], "booking_review")
            self.assertTrue(sess["payload"]["nonce"])
            self.assertEqual(sess["payload"]["qa"]["answers"]["regis_name"], "สมชาย ใจดี")
            card = env.reply.call_args.args[1][0]
            body = card["contents"]["body"]["contents"]
            flat = " | ".join(
                f"{row['contents'][0]['text']}={row['contents'][1]['text']}"
                for row in body
                if row.get("type") == "box"
            )
            # 客户资料区 = cards._summary_rows 同一套标签(เลขบัตร/ชื่อ/วันเกิด/ที่อยู่/เบอร์โทร)
            self.assertIn("ชื่อ=สมชาย ใจดี", flat)
            self.assertIn("เลขบัตร=1234567890121", flat)
            self.assertIn("วันเกิด=01/01/2530", flat)
            self.assertIn("ที่อยู่=99 10110", flat)  # 邮编并入地址行,不再单列
            self.assertIn("ที่ปรึกษาการขาย=sale02", flat)  # 提成归属确认前可见
            self.assertIn("สถานที่รับจอง=สาขาบางนา", flat)
            self.assertIn("รุ่น/สี=DMX D-Max · ขาว", flat)
            self.assertIn("วันส่งมอบ=20/08/2569", flat)
            self.assertIn("เงื่อนไขการขาย=เงินสด", flat)
            self.assertIn("จดทะเบียนในนาม=บริษัท · สมชาย ใจดี", flat)
            self.assertIn("เงินสด=5000.00", flat)
            self.assertIn("ยอดเงินจองรวม=5,000.00", flat)
            self.assertIn("สำเนาบัตรประชาชน=แนบแล้ว", flat)
            self.assertIn("ใบโอนเงินจอง=—", flat)
            footer = card["contents"]["footer"]["contents"]
            actions = [b["action"] for b in footer]
            self.assertEqual(actions[0]["label"], qa_cards.BTN_CONFIRM)
            self.assertIn("action=confirm_booking", actions[0]["data"])
            self.assertIn("nonce=", actions[0]["data"])
            self.assertEqual(actions[1]["label"], qa_cards.BTN_EDIT)
            self.assertIn("/dms-booking", actions[1]["uri"])
            self.assertEqual(actions[2]["label"], qa_cards.BTN_DISCARD)
            self.assertIn("action=cancel_booking", actions[2]["data"])

    async def test_preview_card_uses_summary_rows(self):
        """预览卡客户资料区复用客户确认卡的 summary:同一套标签/顺序/完整地址。"""
        qa_dict = _qa(
            "pay_more",
            summary={
                "people_id": "1234567890121",
                "name": "สมชาย ใจดี",
                "birthday_be": "01/01/2530",
                "address": "99 หมู่ 2 ต.คลองเตย อ.คลองเตย จ.กรุงเทพมหานคร 10230",
                "phone": "0812345678",
            },
            answers={
                "place": {"id": "pl1", "name": "สาขาบางนา"},
                "car": {"id": "c1", "label": "DMX D-Max"},
                "paint": {"id": "p1", "name": "ขาว"},
                "delivery_date_be": "20/08/2569",
                "term": {"id": "t1", "name": "เงินสด"},
                "regis": {"id": "r1", "name": "บริษัท"},
                "regis_name": "สมชาย ใจดี",
            },
            payments=[{"channel": "cash", "amount": "5000.00"}],
        )
        card = qa_cards.preview_card(qa_dict, "nonce")
        body = card["contents"]["body"]["contents"]
        flat = " | ".join(
            f"{row['contents'][0]['text']}={row['contents'][1]['text']}"
            for row in body
            if row.get("type") == "box"
        )
        self.assertIn("เลขบัตร=1234567890121", flat)
        self.assertIn("ชื่อ=สมชาย ใจดี", flat)
        self.assertIn("วันเกิด=01/01/2530", flat)
        self.assertIn("ที่อยู่=99 หมู่ 2 ต.คลองเตย อ.คลองเตย จ.กรุงเทพมหานคร 10230", flat)
        self.assertIn("เบอร์โทร=0812345678", flat)

    def test_preview_shows_selected_company_bank_for_transfer(self):
        card = qa_cards.preview_card(
            _qa(
                payments=[
                    {
                        "channel": "transfer",
                        "amount": "1500.00",
                        "extra": {"dst_id": "1", "dst": "SCB"},
                    }
                ]
            ),
            "nonce",
        )
        body = card["contents"]["body"]["contents"]
        flat = " | ".join(
            f"{row['contents'][0]['text']}={row['contents'][1]['text']}"
            for row in body
            if row.get("type") == "box"
        )
        self.assertIn("เงินโอน=1500.00 · SCB", flat)

    # ── audit / 全局命令 / 态守卫 ─────────────────────────────────────────
    async def test_audit_records_all_inputs_in_order(self):
        with Env() as env:
            _seed(env, _qa())
            await qa.handle_text(_TID, _LUID, "เงินสด", "rt")
            await qa.handle_postback(_TID, _LUID, "qa:place:pl1", {}, "rt")
            await qa.handle_text(_TID, _LUID, "dmax", "rt")
            audit = env.qa_payload()["audit"]
            self.assertEqual([a["input"] for a in audit], ["เงินสด", "qa:place:pl1", "dmax"])
            self.assertEqual([a["step"] for a in audit], ["slip", "place", "car_search"])

    async def test_global_commands_bypass_module(self):
        with Env() as env:
            _seed(env, _qa())
            for word in ("เริ่มใหม่", "เมนู", "สวัสดี"):
                self.assertFalse(await qa.handle_text(_TID, _LUID, word, "rt"))
            self.assertEqual(env.qa_payload()["step"], "slip")  # 会话未被吃掉

    async def test_handlers_skip_other_states(self):
        with Env() as env:
            env.store.set_session(_TID, _LUID, "picking", {"nonce": "x"})
            self.assertFalse(await qa.handle_text(_TID, _LUID, "hi", "rt"))
            self.assertFalse(await qa.handle_image(_TID, _LUID, "mid", "rt"))
            self.assertFalse(await qa.handle_postback(_TID, _LUID, "qa:place:pl1", {}, "rt"))
            self.assertFalse(
                await qa.handle_postback(_TID, _LUID, "qa:date", {"date": "2026-08-20"}, "rt")
            )
            # 非 qa: 前缀(预览卡的确认/取消等既有 postback)→ 不接
            self.assertFalse(
                await qa.handle_postback(_TID, _LUID, "action=confirm_booking&nonce=x", {}, "rt")
            )

    async def test_stray_postback_from_old_card_does_not_jump(self):
        with Env() as env:
            _seed(env, _qa("place"))
            # 在 place 步误点 term 按钮(旧卡残留)→ 吃下但不推进,重问 place
            await qa.handle_postback(_TID, _LUID, "qa:term:t1", {}, "rt")
            self.assertEqual(env.qa_payload()["step"], "place")
            self.assertEqual(_replied_text(env), qa_cards.TXT_ASK_PLACE)

    async def test_pay_amount_thai_digits(self):
        with Env() as env:
            _seed(env, _qa("pay_amount", pending_channel={"channel": "cash"}))
            await qa.handle_text(_TID, _LUID, "๕,๐๐๐", "rt")
            p = env.qa_payload()
            self.assertEqual(p["payments"][0]["amount"], "5000.00")
            self.assertEqual(p["step"], "pay_more")


if __name__ == "__main__":
    unittest.main()
