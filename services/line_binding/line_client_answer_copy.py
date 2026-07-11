# -*- coding: utf-8 -*-
"""客户回答回执文案(D2 · 四语 · 客户侧 LINE push)。

从 line_client_answer 抽出的纯文案表 + 选取器,单一职责:答题回写只管裁决,
push 给客户看的话术集中在此(照 push 侧 _COPY_* 与 _BOUND_COPY 范式)。
"""

from services.line_binding import client_pool_vocab as vocab

_APPLIED = {
    "th": "ได้รับแล้วค่ะ ✅ อัปเดตตามที่แจ้งเรียบร้อยแล้วนะคะ",
    "en": "Got it! Updated as you said.",
    "zh": "收到,已按你说的更新。",
    "ja": "承知しました。ご回答の通り更新しました。",
}
_MANUAL = {
    "th": "ได้รับแล้วค่ะ 🙏 ขอบันทึกไว้ก่อน นักบัญชีจะดูให้อีกทีนะคะ",
    "en": "Got it! Noted — your accountant will take a look.",
    "zh": "收到,先记下,会计会再确认。",
    "ja": "承知しました。会計担当が確認いたします。",
}
_ALREADY_HANDLED = {
    "th": "ไม่ต้องแล้วค่ะ 🙏 รายการนี้จัดการเรียบร้อยแล้ว",
    "en": "No worries — this one's already been taken care of.",
    "zh": "不用麻烦了,这条已经处理好了。",
    "ja": "こちらはすでに処理済みですので大丈夫です。",
}


def ack_copy(to_status: str, already_handled: bool) -> dict:
    """回执四语词表:已处理 > applied > 其余人审。调用方按 lang 取值、th 兜底。"""
    if already_handled:
        return _ALREADY_HANDLED
    if to_status == vocab.APPLIED:
        return _APPLIED
    return _MANUAL
