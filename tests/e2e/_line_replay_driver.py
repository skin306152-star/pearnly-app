# -*- coding: utf-8 -*-
"""跑真状态机、捕获它实际发出的 LINE 消息,导出给 _line_replay.html 渲染成验收证据。

复用 tests/unit/test_line_dms_flow 的 _Env(fake 会话背板 + fake OCR/DMS + spy 出口),
所以走的是真分发路径,不是脚本自己编的对话。
"""

import asyncio
import io
import json
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from tests.unit.test_line_dms_flow import _Env, _RAW_ID, _lookup, _pb, _pb_field  # noqa: E402
from services.line_dms import cards, flow, ocr_review  # noqa: E402

BINDING = {"tenant_id": "T1", "user_id": "U1"}
LUID = "L1"


def _hook(env, turns):
    """把四个出口的调用按发生顺序记进 turns。"""

    def rec_text(token_or_uid, text, **kw):
        turns.append({"dir": "out", "msg": {"type": "text", "text": text}})

    def rec_msgs(token_or_uid, msgs, **kw):
        for m in msgs:
            turns.append({"dir": "out", "msg": m})

    env.reply.side_effect = rec_text
    env.push_text.side_effect = rec_text
    env.reply_msgs.side_effect = rec_msgs
    env.push_msgs.side_effect = rec_msgs


def _ocr(needs_review=False, missing=None):
    return {
        "needs_review": needs_review,
        "missing_fields": missing or [],
        "id_card": dict(_RAW_ID),
    }


async def scene_p1_10():
    """P1-10:改姓名途中打 เมนู —— 旧行为把姓名改成「เมนู」并重跑查重。"""
    turns = []
    with _Env(ocr=_ocr(), lookup=_lookup("none")) as env:
        _hook(env, turns)
        turns.append({"dir": "in", "text": "[ส่งรูปบัตรประชาชน]"})
        await flow.process_image(BINDING, LUID, "M1")
        turns.append({"dir": "in", "text": "0812345678"})
        await flow.handle_text(BINDING, LUID, "TK", "0812345678")
        await env.drain()
        nonce = env.session()["payload"]["nonce"]

        turns.append({"dir": "in", "text": "[กด แก้ไข]"})
        await flow.handle_postback(BINDING, LUID, "TK", _pb(cards.ACT_EDIT, nonce))
        turns.append({"dir": "in", "text": "[เลือก ชื่อ-นามสกุล]"})
        await flow.handle_postback(
            BINDING, LUID, "TK", _pb_field(cards.ACT_EDIT_FIELD, nonce, "name")
        )
        turns.append({"dir": "in", "text": "เมนู"})
        await flow.handle_text(BINDING, LUID, "TK", "เมนู")
        await env.drain()

        sess = env.session()
        name = (sess["payload"].get("id_card") or {}).get("name", "")
        asserts = [
            {"ok": name != "เมนู", "text": f"客户姓名未被写成「เมนู」(实际 = {name!r})"},
            {
                "ok": sess["state"] == "menu",
                "text": f"会话进菜单态而非停在 editing(实际 = {sess['state']})",
            },
            {
                "ok": "editing_field" not in sess["payload"],
                "text": "编辑上下文已结束,没有残留 editing_field",
            },
            {
                "ok": env.lookup.call_count == 1,
                "text": f"没有因为打 เมนู 白跑一次 DMS 查重(查重次数 = {env.lookup.call_count})",
            },
        ]
    return {
        "name": "P1-10 · 改姓名途中打「เมนู」",
        "note": "预期:弹菜单,姓名保持原值,不白跑一次 DMS 登录查重。",
        "turns": turns,
        "asserts": asserts,
    }


async def scene_p1_11():
    """P1-11:身份证号校验位不过 —— 旧行为回一句笼统「拍不清请重拍」。"""
    turns = []
    with _Env(ocr=_ocr(True, ["people_id_checksum"]), lookup=_lookup("none")) as env:
        _hook(env, turns)
        turns.append({"dir": "in", "text": "[ส่งรูปบัตร · เลขบัตรหลักตรวจสอบไม่ผ่าน]"})
        await flow.process_image(BINDING, LUID, "M2")
        await env.drain()
        said = turns[-1]["msg"]["text"]
        asserts = [
            {
                "ok": said == ocr_review.TXT_ID_CHECKSUM,
                "text": "说的是「13 位读到了但校验位不过」,不是笼统的拍不清",
            },
            {
                "ok": cards.TXT_BLURRY not in said,
                "text": "不再出现「อ่านบัตรไม่ชัด」(重拍解决不了的场景不喊重拍)",
            },
        ]
    turns2 = []
    with _Env(ocr=_ocr(True, ["first_name", "last_name"]), lookup=_lookup("none")) as env:
        _hook(env, turns2)
        turns2.append({"dir": "in", "text": "[ส่งรูปบัตร · อ่านชื่อ-นามสกุลไม่ออก]"})
        await flow.process_image(BINDING, LUID, "M3")
        await env.drain()
        said2 = turns2[-1]["msg"]["text"]
        asserts += [
            {
                "ok": "(" in said2 and "ชื่อ" in said2,
                "text": f"真读不清时括号里印出了缺项(实际 = {said2})",
            },
        ]
    return {
        "name": "P1-11 · 读不清 / 校验位不过",
        "note": "上:校验位错。下:真读不清 —— 括号里的缺项从前恒不出现(死代码)。",
        "turns": turns + turns2,
        "asserts": asserts,
    }


async def scene_p1_12():
    """P1-12:待选车态被随手一句话掐死链接,且无重发入口。"""
    turns = []
    with _Env(ocr=_ocr(), lookup=_lookup("exact", customer_id="C99")) as env:
        _hook(env, turns)
        env.store.set_session(
            "T1",
            LUID,
            "picking",
            {
                "nonce": "n1",
                "endpoint_id": "E1",
                "customer_id": "C99",
                "user_id": "U1",
                "draft": {"name": "สมชาย ใจดี"},
                "name": "สมชาย ใจดี",
            },
        )
        before = json.dumps(env.session(), ensure_ascii=False, sort_keys=True)

        turns.append({"dir": "in", "text": "รอสักครู่นะครับ 5 นาที"})
        await flow.handle_text(BINDING, LUID, "TK", "รอสักครู่นะครับ 5 นาที")
        await env.drain()
        after = json.dumps(env.session(), ensure_ascii=False, sort_keys=True)

        turns.append({"dir": "in", "text": "เมนู"})
        await flow.handle_text(BINDING, LUID, "TK", "เมนู")
        await env.drain()
        after_menu = env.session()

        turns.append({"dir": "in", "text": "[กด ขอลิงก์เลือกรถใหม่]"})
        await flow.handle_postback(BINDING, LUID, "TK", _pb(cards.ACT_REISSUE_PICK, cid="C99"))
        await env.drain()

        asserts = [
            {
                "ok": before == after,
                "text": "含数字的闲聊没有覆写会话(手上那条没过期的链接不会被掐死)",
            },
            {
                "ok": after_menu["state"] == "picking",
                "text": f"打 เมนู 仍停在 picking,菜单照发(实际 = {after_menu['state']})",
            },
            {
                "ok": env.offer.call_count == 1,
                "text": f"点重发按钮真的重签了一条选车链接(offer_pick 调用 = {env.offer.call_count})",
            },
            {"ok": env.push_idcard.call_count == 0, "text": "重发过程零写档"},
            {
                "ok": not any(
                    cards.TXT_NEED_BOTH in (t.get("msg", {}).get("text") or "")
                    for t in turns
                    if t["dir"] == "out"
                ),
                "text": "不再对已建档的用户说「请发身份证和手机号」",
            },
        ]
    return {
        "name": "P1-12 · 选车链接过期后的自救",
        "note": "档已建好,只差选车。预期:闲聊不毁会话、菜单不掐链接、一键重发且不必重拍身份证。",
        "turns": turns,
        "asserts": asserts,
    }


async def scene_keep_guard():
    """翻聊天记录点旧卡白拿链接的后门(ACT_KEEP 无守卫)。"""
    turns = []
    with _Env(ocr=_ocr(), lookup=_lookup("exact", customer_id="C99")) as env:
        _hook(env, turns)
        env.store.set_session(
            "T1", LUID, "reviewing", {"nonce": "good", "customer_id": "C99", "endpoint_id": "E1"}
        )
        turns.append({"dir": "in", "text": "[กดการ์ดเก่าในประวัติแชท · ไม่มี nonce]"})
        await flow.handle_postback(BINDING, LUID, "TK", _pb(cards.ACT_KEEP))
        await env.drain()
        said = turns[-1]["msg"]["text"]
        asserts = [
            {"ok": said == cards.TXT_EXPIRED, "text": "无 nonce 的旧卡被拒(后门关闭)"},
            {"ok": env.offer.call_count == 0, "text": "没有因此白签一条新链接"},
        ]
    return {
        "name": "旁证 · 旧卡后门已关",
        "note": "ACT_KEEP 原来无 state/nonce 守卫,翻聊天记录点旧卡就能白拿链接。",
        "turns": turns,
        "asserts": asserts,
    }


async def main():
    scenes = [
        await scene_p1_10(),
        await scene_p1_11(),
        await scene_p1_12(),
        await scene_keep_guard(),
    ]
    out = {"title": "DMS LINE 侧修复验收 · 状态机真跑捕获", "scenes": scenes}
    io.open(sys.argv[1], "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    bad = [(s["name"], a["text"]) for s in scenes for a in s["asserts"] if not a["ok"]]
    print(
        f"scenes={len(scenes)} asserts={sum(len(s['asserts']) for s in scenes)} failed={len(bad)}"
    )
    for n, t in bad:
        print("  FAIL", n, "|", t)
    sys.exit(1 if bad else 0)


asyncio.run(main())
