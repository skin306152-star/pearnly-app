# -*- coding: utf-8 -*-
"""DMS LINE 逐字段修正(DL-6):OCR 误读的人防封口。

真实场景:身份证姓氏尾梢 นารถ 被读成 นาก,错值一路确认入库无从纠。给新建卡与差异卡各
加一颗 [แก้ไข] → 选字段 → 输新值 → 逐字段校验 → 写回 id_card 对应位 → 整体重跑
flow._run_dedup(重新查重 + 重算 diff + 新卡 + 新 nonce)。统一走「改源值再重跑」这一条
机制,天然覆盖新建(A)/差异(C)两分支,也覆盖「证号改了→查重落到别的分支」。

nonce 语义:开菜单/选字段只校验会话 nonce 不消费(编辑是读操作);真正写档仍由 flow 的
consume_nonce 守卫。编辑期间态转 editing,旧卡的确认(仍带旧 nonce)因态不符/重跑后
nonce 轮换而必被拒。地理四级 id 不开放直改——改地址文本后 geo 由既有级联匹配重解。
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from services.erp.dms_id_validate import is_valid_thai_id, normalize_thai_id
from services.line_binding import line_client
from services.line_dms import cards, store
from services.line_dms._out import _CHANNEL, PHONE_RE, _reply, _thr

EDIT_ACTIONS = frozenset({cards.ACT_EDIT, cards.ACT_EDIT_FIELD, cards.ACT_EDIT_CANCEL})

_ADDR_FIELDS = ("house_no", "moo", "soi", "road")
# 可改字段以卡片菜单为唯一真值源——菜单里有的准入必须放行,防两处清单漂移。
_EDITABLE_FIELDS = tuple(key for key, _ in cards.EDIT_FIELDS)

_BIRTHDAY_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_MIN_BE_YEAR = 2400


# ── postback:开菜单 / 选字段 / 取消 ────────────────────────────────────────
async def handle_postback(
    binding: dict, line_user_id: str, reply_token: str, action: str, pb: dict, sess: Optional[dict]
) -> None:
    nonce = pb.get("nonce")
    if action == cards.ACT_EDIT:
        _open_menu(reply_token, sess, nonce)
    elif action == cards.ACT_EDIT_FIELD:
        await _pick_field(binding, line_user_id, reply_token, sess, nonce, pb.get("field"))
    else:  # ACT_EDIT_CANCEL
        _cancel(binding, line_user_id, reply_token, sess, nonce)


def _open_menu(reply_token: str, sess: Optional[dict], nonce: Optional[str]) -> None:
    if not _nonce_ok(sess, nonce):
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    line_client.reply_messages(reply_token, [cards.edit_menu_message(nonce)], channel=_CHANNEL)


async def _pick_field(
    binding: dict,
    line_user_id: str,
    reply_token: str,
    sess: Optional[dict],
    nonce: Optional[str],
    field: Optional[str],
) -> None:
    if not _nonce_ok(sess, nonce) or field not in _EDITABLE_FIELDS:
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    payload = (sess or {}).get("payload") or {}
    await _thr(
        store.set_session,
        binding["tenant_id"],
        line_user_id,
        "editing",
        {**payload, "editing_field": field},
    )
    _reply(reply_token, cards.edit_prompt(field))


def _cancel(
    binding: dict, line_user_id: str, reply_token: str, sess: Optional[dict], nonce: Optional[str]
) -> None:
    payload = (sess or {}).get("payload") or {}
    if not _nonce_ok(sess, nonce) or not payload.get("id_card"):
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    _reply(reply_token, cards.TXT_EDIT_CANCELLED)
    _rerun(binding, line_user_id, payload)


# ── text:editing 态收新值 / 文本取消 ───────────────────────────────────────
async def handle_text(
    binding: dict, line_user_id: str, reply_token: str, sess: Optional[dict], text: str
) -> None:
    """editing 态的下一条文本 = 新值(或 ยกเลิก 放弃)。flow 已先拦 เริ่มใหม่ 全局重置。"""
    payload = (sess or {}).get("payload") or {}
    if text.strip() == cards.BTN_EDIT_CANCEL:
        _reply(reply_token, cards.TXT_EDIT_CANCELLED)
        _rerun(binding, line_user_id, payload)
        return

    field = payload.get("editing_field")
    cleaned, err = _validate(field, text)
    if err:
        _reply(reply_token, err)  # 校验不过 → 打回,停留 editing 等重输
        return

    id_card = _apply(payload.get("id_card") or {}, field, cleaned)
    phone = cleaned if field == "phone" else (payload.get("phone") or "")
    _rerun(binding, line_user_id, payload, id_card=id_card, phone=phone)


# ── 逐字段校验 ──────────────────────────────────────────────────────────────
def _validate(field: Optional[str], text: str) -> Tuple[str, str]:
    """返回 (cleaned, error_text)。error_text 非空 = 打回。"""
    v = (text or "").strip()
    if field == "people_id":
        norm = normalize_thai_id(v)
        return (norm, "") if is_valid_thai_id(norm) else ("", cards.TXT_EDIT_BAD_ID)
    if field == "birthday_be":
        # 真日历校验(45/99/2569 这类不存在的日期正是 OCR 典型误读);年段按佛历。
        if _BIRTHDAY_RE.match(v) and _MIN_BE_YEAR <= int(v[6:10]) <= _current_be_year():
            try:
                datetime.strptime(v[:6] + "2000", "%d/%m/%Y")
                return v, ""
            except ValueError:
                pass
        return "", cards.TXT_EDIT_BAD_BIRTHDAY
    if field == "phone":
        return (v, "") if PHONE_RE.match(v) else ("", cards.TXT_EDIT_BAD_PHONE)
    if field == "name" or field in _ADDR_FIELDS:
        return (v, "") if v else ("", cards.TXT_EDIT_EMPTY)
    return "", cards.TXT_EDIT_EMPTY


def _current_be_year() -> int:
    return datetime.now(timezone.utc).year + 543


# ── 把新值落到 id_card 对应位(重跑 _run_dedup 从此重建 draft/查重) ───────────
def _apply(id_card: Dict[str, Any], field: str, value: str) -> Dict[str, Any]:
    ic = copy.deepcopy(id_card)
    if field in _ADDR_FIELDS:
        addr = dict(ic.get("address") or {})
        addr[field] = value
        ic["address"] = addr
    elif field in ("name", "people_id", "birthday_be"):
        ic[field] = value
    return ic


def _nonce_ok(sess: Optional[dict], nonce: Optional[str]) -> bool:
    """会话须在 reviewing 且 nonce 吻合(只校验不消费)。"""
    payload = (sess or {}).get("payload") or {}
    return bool(
        sess and sess.get("state") == "reviewing" and nonce and payload.get("nonce") == nonce
    )


def _rerun(
    binding: dict,
    line_user_id: str,
    payload: dict,
    *,
    id_card: Optional[dict] = None,
    phone: Optional[str] = None,
) -> None:
    """整体重跑查重(离主线程后台跑)。改值取覆盖参数,取消取会话原值。"""
    from services.line_dms import flow  # 延迟导入避免 flow ↔ edit_flow 环依赖

    ic = id_card if id_card is not None else (payload.get("id_card") or {})
    ph = phone if phone is not None else (payload.get("phone") or "")
    flow._spawn(flow._run_dedup(binding, line_user_id, None, ic, ph, payload.get("endpoint_id")))
