# -*- coding: utf-8 -*-
"""DMS LINE 对话流状态机(DL-3)· 四分支 / nonce / 计费用真实用户行 / push 台账。

fake DMS client(recognize_lookup/push_idcard 全 mock)+ fake OCR + spy reply/push,
dict 背板会话态。重活(_write_*)经 flow._spawn 挂后台,测试里改为收集 coro 后手动
drain,保持确定性。
"""

import contextlib
import unittest
from unittest import mock

from services.line_dms import cards, flow

# 网页确认页 fields 键形状(static/dms/dms-intake-core.js)· LINE 侧必须同形。
SPA_CREATE_FIELD_KEYS = {"prefix_id", "name", "people_id", "tax_id", "birthday_be", "phone"}
SPA_ADDR_KEYS = {
    "house_no",
    "building",
    "floor",
    "room",
    "village",
    "moo",
    "soi",
    "road",
    "province_id",
    "district_id",
    "subdistrict_id",
    "zipcode_id",
}

_BINDING = {"tenant_id": "T1", "user_id": "U1"}
_LUID = "L1"
_PHONE = "0812345678"

_RAW_ID = {
    "prefix_name": "นาย",
    "first_name": "สมชาย",
    "last_name": "ใจดี",
    "people_id": "1234567890121",
    "birthday_be": "2530-01-01",
    "issue_date_be": "",
    "expiry_date_be": "",
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


def _ep(admin=False):
    cfg = {"admin_username": "a", "admin_password": "b"} if admin else {}
    return {"id": "E1", "config": cfg}


def _ocr_ok():
    return {"needs_review": False, "missing_fields": [], "id_card": dict(_RAW_ID)}


def _lookup(scenario, *, field_diffs=None, customer_id=None, candidates=None):
    return {
        "ok": True,
        "scenario": scenario,
        "match": {"found": scenario == "exact", "customer_id": customer_id, "current_fields": {}},
        "field_diffs": field_diffs or [],
        "candidates": candidates or [],
        "geo": _GEO,
        "prefixes": _PREFIXES,
    }


class FakeStore:
    """dict 背板会话:key=(tenant, luid) → {'state','payload'}。"""

    def __init__(self):
        self.data = {}

    def get_session(self, tenant, luid):
        return self.data.get((str(tenant), str(luid)))

    def set_session(self, tenant, luid, state, payload=None, ttl_minutes=30):
        self.data[(str(tenant), str(luid))] = {"state": state, "payload": payload or {}}

    def clear_session(self, tenant, luid):
        self.data.pop((str(tenant), str(luid)), None)


class _Env:
    """一处装齐所有 mock;进入返回自身,退出还原。"""

    def __init__(self, *, ocr=None, ocr_error=None, lookup=None, admin=False, push_result=None):
        self.store = FakeStore()
        self.spawned = []
        self._ocr = ocr
        self._ocr_error = ocr_error
        self._lookup = lookup
        self._ep = _ep(admin)
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
        self.reply = p(flow.line_client, "reply_text")
        self.push_text = p(flow.line_client, "push_text")
        self.push_msgs = p(flow.line_client, "push_messages")
        p(flow.line_client, "start_loading")
        p(flow.line_client, "download_message_content", return_value=b"imgbytes")
        p(flow.db, "find_user_by_id", return_value={"id": "U1", "tenant_id": "T1"})
        self.insert_log = p(flow.db, "insert_push_log", return_value="LOG1")
        if self._ocr_error is not None:
            p(flow._id_ocr, "recognize_id_card", side_effect=self._ocr_error)
        else:
            p(flow._id_ocr, "recognize_id_card", return_value=(self._ep, self._ocr, 10))
        p(flow._id_ocr, "resolve_dms_endpoint", return_value=self._ep)
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

    def pushed_card(self):
        return self.push_msgs.call_args.args[1][0]


def _pb(action, nonce="", cid=""):
    from urllib.parse import urlencode

    q = {"action": action}
    if nonce:
        q["nonce"] = nonce
    if cid:
        q["cid"] = cid
    return {"data": urlencode(q)}


class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def _seed_reviewing(self, env):
        """预置 phone → 送图 → 走完查重,落到 reviewing。返回 session nonce。"""
        env.store.set_session("T1", "L1", "collecting", {"phone": _PHONE})
        await flow.process_image(_BINDING, _LUID, "mid1")
        return (env.session() or {}).get("payload", {}).get("nonce")

    async def test_c1_new_customer_create_fields_match_spa(self):
        """C1:图+手机号→分支①→确认→push_idcard mode='create' 且 fields 键形状同 SPA。"""
        with _Env(ocr=_ocr_ok(), lookup=_lookup("none")) as env:
            nonce = await self._seed_reviewing(env)
            self.assertIsNotNone(nonce)
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_CREATE, nonce))
            await env.drain()

        kw = env.push_idcard.call_args.kwargs
        self.assertEqual(kw["mode"], "create")
        self.assertIsNone(kw["customer_id"])
        self.assertEqual(set(kw["fields"].keys()), SPA_CREATE_FIELD_KEYS)
        self.assertEqual(set(kw["addresses"].keys()), {"", "_ct", "_sd"})
        for blk in kw["addresses"].values():
            self.assertEqual(set(blk.keys()), SPA_ADDR_KEYS)
        # 值取自 OCR/geo(证同口径 buildNewVals)
        self.assertEqual(kw["fields"]["people_id"], "1234567890121")
        self.assertEqual(kw["fields"]["prefix_id"], "17")
        self.assertEqual(kw["fields"]["phone"], _PHONE)
        self.assertEqual(kw["addresses"][""]["province_id"], "1")

    async def test_c2_exact_no_diff_zero_write(self):
        """C2:exact 无 diff → 零写入 + session 清 + 提示已存在。"""
        with _Env(ocr=_ocr_ok(), lookup=_lookup("exact", customer_id="C7")) as env:
            await self._seed_reviewing(env)
            await env.drain()
            env.push_idcard.assert_not_called()
            self.assertIsNone(env.session())
            self.assertEqual(env.push_text.call_args.args[1], cards.TXT_SAME)

    async def test_c3_exact_addr_diff_update_only_changed(self):
        """C3:exact+地址 diff → 卡恰 1 条 diff;确认→overwrite 且 fields 有地址键、无生日。"""
        diffs = [{"field": "house_no", "old": "88", "new": "99"}]
        with _Env(
            ocr=_ocr_ok(), lookup=_lookup("exact", field_diffs=diffs, customer_id="C7"), admin=True
        ) as env:
            nonce = await self._seed_reviewing(env)
            # 卡内容恰 1 条 diff(数颜色为红的差异文本行)
            card = env.pushed_card()
            body = card["contents"]["body"]["contents"]
            diff_rows = [
                b
                for b in body
                if b.get("type") == "box"
                and b.get("layout") == "vertical"
                and any(c.get("color") == "#c0392b" for c in b.get("contents", []))
            ]
            self.assertEqual(len(diff_rows), 1)

            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_UPDATE, nonce))
            await env.drain()

        kw = env.push_idcard.call_args.kwargs
        self.assertEqual(kw["mode"], "overwrite")
        self.assertEqual(kw["customer_id"], "C7")
        self.assertIsNone(kw["addresses"])
        self.assertIn("house_no", kw["fields"])
        self.assertNotIn("birthday_be", kw["fields"])
        self.assertEqual(set(kw["fields"].keys()), {"people_id", "name", "house_no"})

    async def test_c4_similar_pick_targets_chosen_customer(self):
        """C4:similar → 选候选 → overwrite 对准所选 customer_id。"""
        cands = [
            {"customer_id": "C1", "cuscode": "A001", "name": "สมชาย", "people_id": "1234567890121"},
            {
                "customer_id": "C2",
                "cuscode": "A002",
                "name": "สมชาย ใจดี",
                "people_id": "1234567890121",
            },
        ]
        with _Env(ocr=_ocr_ok(), lookup=_lookup("similar", candidates=cands)) as env:
            nonce = await self._seed_reviewing(env)
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_PICK, nonce, cid="C2"))
            await env.drain()

        kw = env.push_idcard.call_args.kwargs
        self.assertEqual(kw["mode"], "overwrite")
        self.assertEqual(kw["customer_id"], "C2")

    async def test_c5_nonce_replay_and_expiry_refuse_second_write(self):
        """C5:nonce 重放 → 拒且不二次写;session 过期 → 过期话术。"""
        with _Env(ocr=_ocr_ok(), lookup=_lookup("none")) as env:
            nonce = await self._seed_reviewing(env)
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_CREATE, nonce))
            await env.drain()
            self.assertEqual(env.push_idcard.call_count, 1)
            self.assertIsNone(env.session())  # 成功后已清

            # 重放同一 nonce → 会话已清 → 过期话术,不二次写
            await flow.handle_postback(_BINDING, _LUID, "rt2", _pb(cards.ACT_CREATE, nonce))
            await env.drain()
            self.assertEqual(env.push_idcard.call_count, 1)
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_EXPIRED)

    async def test_c5b_wrong_nonce_refused(self):
        """C5:reviewing 在,但 nonce 不符 → 过期话术,零写。"""
        with _Env(ocr=_ocr_ok(), lookup=_lookup("none")) as env:
            await self._seed_reviewing(env)
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_CREATE, "BADNONCE"))
            await env.drain()
            env.push_idcard.assert_not_called()
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_EXPIRED)

    async def test_c6_checksum_bounce_no_lookup(self):
        """C6:people_id_checksum 命中(needs_review)→ 打回重拍,不调 recognize_lookup。"""
        ocr = {
            "needs_review": True,
            "missing_fields": ["people_id_checksum"],
            "id_card": dict(_RAW_ID),
        }
        with _Env(ocr=ocr, lookup=_lookup("none")) as env:
            env.store.set_session("T1", "L1", "collecting", {"phone": _PHONE})
            await flow.process_image(_BINDING, _LUID, "mid1")
            env.lookup.assert_not_called()
            self.assertTrue(env.push_text.call_args.args[1].startswith(cards.TXT_BLURRY))

    async def test_c8_push_log_trigger_and_field_diffs(self):
        """C8:insert_push_log 被调 · request_body.trigger='line_dms' 且含 field_diffs · push_type='id_card'。"""
        diffs = [{"field": "road", "old": "x", "new": "สุขุมวิท"}]
        with _Env(
            ocr=_ocr_ok(), lookup=_lookup("exact", field_diffs=diffs, customer_id="C7"), admin=True
        ) as env:
            nonce = await self._seed_reviewing(env)
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_UPDATE, nonce))
            await env.drain()

        args = env.insert_log.call_args.args
        request_body = args[8]
        self.assertEqual(request_body["trigger"], "line_dms")
        self.assertEqual(request_body["field_diffs"], diffs)
        self.assertEqual(args[13], "id_card")  # push_type(trigger 位)保持 id_card

    async def test_c9_no_admin_diff_card_has_no_update_button(self):
        """C9:没配 admin + 有 diff → 卡无 [อัปเดตข้อมูล] 按钮、有设置提示。"""
        diffs = [{"field": "house_no", "old": "88", "new": "99"}]
        with _Env(
            ocr=_ocr_ok(), lookup=_lookup("exact", field_diffs=diffs, customer_id="C7"), admin=False
        ) as env:
            await self._seed_reviewing(env)
            card = env.pushed_card()
            labels = _all_button_labels(card)
            self.assertNotIn(cards.BTN_UPDATE, labels)
            self.assertIn(cards.BTN_KEEP, labels)
            self.assertTrue(_card_has_text(card, cards.TXT_ADMIN_NEEDED))

    async def test_keep_no_write_clears_session(self):
        """[ใช้ข้อมูลเดิม] → 不写档 + 清 session + 回 ใช้ข้อมูลเดิมต่อ。"""
        with _Env(ocr=_ocr_ok(), lookup=_lookup("none")) as env:
            await self._seed_reviewing(env)
            await flow.handle_postback(_BINDING, _LUID, "rt", _pb(cards.ACT_KEEP))
            await env.drain()
            env.push_idcard.assert_not_called()
            self.assertIsNone(env.session())
            self.assertEqual(env.reply.call_args.args[1], cards.TXT_KEEP)


def _all_button_labels(card):
    out = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "button":
                out.append(node.get("action", {}).get("label"))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(card)
    return out


def _card_has_text(card, text):
    found = [False]

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text" and node.get("text") == text:
                found[0] = True
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(card)
    return found[0]


if __name__ == "__main__":
    unittest.main()
