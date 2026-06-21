# -*- coding: utf-8 -*-
"""LINE 端主动解绑(确认卡 + postback + 一次性 nonce · 破坏性动作必经确认)。

用户发「解绑 / unbind / ยกเลิกการเชื่อมต่อ / 連携解除」→ 出确认卡(A8a 横幅 + 确认/取消)。
点确认 → 消费一次性令牌 + db.unbind_line_by_line_user_id + A8b 成功卡。绝不一句话直接解。
关键词刻意要求「绑定/连接/เชื่อมต่อ」完整语境,不与「取消交易」(批量撤销)冲突。卡走泰语图卡皮肤。
"""

from __future__ import annotations

import logging

from core import db
from services.line_binding import line_card_sections as s
from services.line_binding import line_imagemap, line_postback, line_reply

logger = logging.getLogger(__name__)

_REF_PREFIX = "unbind:"

# 解绑关键词(确定性·需完整语境):不含裸「取消/撤/ยกเลิก」,故不抢批量撤销的交易取消。
_KEYWORDS = (
    "解绑",
    "解除绑定",
    "取消绑定",
    "解除连接",
    "断开连接",
    "解除关联",
    "unbind",
    "unlink",
    "disconnect",
    "ยกเลิกการเชื่อมต่อ",
    "เลิกเชื่อมต่อ",
    "ยกเลิกการผูกบัญชี",
    "ยกเลิกการผูก",
    "連携解除",
    "連携を解除",
    "リンク解除",
)

# 卡文案(泰语·与 A8 横幅一致;Zihao 定只做泰语图卡)。
_CONFIRM_BODY = (
    "หลังจากยกเลิกการเชื่อมต่อ คุณจะไม่สามารถถ่ายบิล บันทึกบัญชี "
    "หรือค้นหาข้อมูลบัญชีในแชทนี้ได้ ข้อมูลบัญชีของคุณยังคงถูกเก็บไว้ใน Pearnly"
)
_BTN_CONFIRM = "ยืนยันยกเลิก"
_BTN_CANCEL = "ยกเลิก"
_SUCCESS_BODY = (
    "ยกเลิกการเชื่อมต่อ LINE แล้ว ข้อมูลบัญชีของคุณยังคงถูกเก็บไว้ใน Pearnly "
    "หากต้องการใช้งานต่อ เพียงเชื่อมต่อใหม่อีกครั้ง"
)
_CANCEL_REPLY = "ยังเชื่อมต่ออยู่เหมือนเดิมค่ะ"


def detect_unbind(text: str) -> bool:
    t = (text or "").strip().lower()
    return bool(t) and any(k.lower() in t for k in _KEYWORDS)


def _card(hero_stem: str, body: str, footer: list) -> dict:
    bubble = {
        "type": "bubble",
        "size": "mega",
        "hero": line_imagemap.hero(hero_stem),
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "16px",
            "spacing": "sm",
            "contents": [s.txt(body, size="sm", color="#374151", wrap=True)],
        },
    }
    if footer:
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "12px",
            "contents": footer,
        }
    return s.prune_empty_text(
        {"type": "flex", "altText": "ยกเลิกการเชื่อมต่อ Pearnly", "contents": bubble}
    )


def confirm_card(token: str) -> dict:
    footer = [
        s.btn(
            _BTN_CONFIRM,
            primary=True,
            postback=line_postback.unbind_confirm_data(token),
            danger=True,
        ),
        s.btn(_BTN_CANCEL, primary=False, postback=line_postback.unbind_cancel_data(token)),
    ]
    return _card(line_imagemap.UNBIND_CONFIRM_BANNER, _CONFIRM_BODY, footer)


def success_card() -> dict:
    return _card(line_imagemap.UNBIND_SUCCESS_BANNER, _SUCCESS_BODY, [])


def route(bound_user, reply_token, line_user_id, *, quote_token="") -> bool:
    """检测到解绑命令 → 出确认卡(mint 一次性令牌防重放)。返回 True=已处理。"""
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    uid = str(bound_user["id"])
    token = ""
    try:
        from services.line_binding import line_action_nonce as nonce

        with db.get_cursor(commit=True) as cur:
            token = nonce.mint(
                cur,
                tenant_id=tid,
                workspace_client_id="",
                action_ref=f"{_REF_PREFIX}{uid}",
                user_id=line_user_id,
            )
    except Exception:
        logger.warning("[line unbind] mint nonce failed", exc_info=True)
    line_reply.reply_messages_context(
        reply_token,
        [confirm_card(token)],
        line_user_id=line_user_id,
        tenant_id=tid,
        quote_token=quote_token,
    )
    return True


def handle_postback(bound_user, reply_token, action, token, lang) -> None:
    """解绑 postback:确认 → 消费令牌 + 解绑 + 成功卡;取消 → 友好回执。绝不抛(主路径不崩)。"""
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    luid = bound_user.get("line_user_id") or ""
    try:
        from services.line_binding import line_action_nonce as nonce

        with db.get_cursor(commit=True) as cur:
            res = nonce.consume(cur, tenant_id=tid, token=token)
        if action == line_postback.ACTION_UNBIND_CANCEL:
            line_reply.reply_text_context(
                reply_token, _CANCEL_REPLY, line_user_id=luid, tenant_id=tid
            )
            return
        # confirm:令牌 ok/used 都执行解绑(幂等:已解绑再点无副作用)。missing/expired → 友好提示不解。
        if res.get("status") in ("ok", "used"):
            db.unbind_line_by_line_user_id(luid)
            line_reply.reply_messages_context(reply_token, [success_card()], line_user_id=luid)
            return
        line_reply.reply_text_context(reply_token, _CANCEL_REPLY, line_user_id=luid, tenant_id=tid)
    except Exception:
        logger.warning("[line unbind] postback failed", exc_info=True)
