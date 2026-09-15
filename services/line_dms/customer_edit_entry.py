"""Open the browser editor; retired text-edit events cannot change customer fields."""

from __future__ import annotations

import secrets

from services.line_dms import binding_guard, cards, edit_link, store
from services.line_dms._out import _reply, _thr
from services.line_platform import client

# Only redirect historical cards; no field selection or text application remains.
EDIT_ACTIONS = frozenset({"edit", "edit_field", "edit_cancel"})


def _open(reply_token: str, nonce: str) -> None:
    if not edit_link.url(nonce, customer=True):
        _reply(reply_token, "ยังเปิดหน้าแก้ไขไม่ได้ กรุณาลองใหม่อีกครั้งครับ")
        return
    client.reply_messages(
        reply_token,
        [cards._bubble(cards.BTN_EDIT, [], [cards._edit_button(nonce)], cards.BTN_EDIT)],
        channel=binding_guard.current_channel(),
    )


async def retire_session(binding: dict, line_user_id: str, reply_token: str, sess: dict) -> None:
    """Keep the pre-edit draft, ignore the text, and open a freshly numbered browser review."""
    payload = {k: v for k, v in (sess.get("payload") or {}).items() if k != "editing_field"}
    payload["nonce"] = secrets.token_hex(8)
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "reviewing", payload)
    _open(reply_token, payload["nonce"])


async def handle_postback(binding, line_user_id, reply_token, action, pb, sess) -> None:
    state = (sess or {}).get("state")
    if state not in {"reviewing", "editing"} or not store.verify_nonce(
        sess, pb.get("nonce"), state
    ):
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    if state == "editing":
        await retire_session(binding, line_user_id, reply_token, sess)
    else:
        _open(reply_token, pb["nonce"])
