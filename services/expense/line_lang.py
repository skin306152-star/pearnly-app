# -*- coding: utf-8 -*-
"""LINE 回复语言中枢:先理解用户语言,再回应(账务/闲聊统一前置)。

两件事:
1. resolve_reply_lang —— 本轮该用哪国语言回。先按用户【这条消息实际打的字】跟随(强脚本信号
   zh/th/ja),拿不到才回落账号偏好 → LINE 事件语言 → 泰语兜底。en 是弱信号(ASCII 字母可能是
   品牌名 / 罗马音泰语)不自动切,免得泰国用户打个 "Makro" 就被甩成英文。
2. detect_lang_switch —— 用户明说「说中文 / speak English / พูดไทย / 日本語で」→ 返目标语言;
   调用方持久化偏好 + 用新语言回一句确认(锁定,之后图片卡 / postback 也跟着走)。

判语种是机械判断(脚本 + 短语),不走 LLM —— 语义才用 AI(见 line-accounting-honest-status-boundary)。
"""

from __future__ import annotations

from services.expense import line_classify

_STRONG = ("zh", "th", "ja")  # 脚本可靠;en 仅由 ASCII 字母推断,弱信号不自动切
_MAX_SWITCH_LEN = 40  # 「请你说中文」这类请求都短;长句里偶含 in thai 等子串不当切

# 明说换语言的短语(命中即锁)。带动词 / 请求语境,避免「这张发票是中文的」被误切。
_SWITCH = {
    "zh": (
        "说中文",
        "說中文",
        "讲中文",
        "講中文",
        "用中文",
        "中文回",
        "换中文",
        "換中文",
        "切中文",
        "speak chinese",
        "in chinese",
        "chinese please",
        "ภาษาจีน",
        "พูดจีน",
        "ตอบจีน",
        "เป็นจีน",
    ),
    "en": (
        "speak english",
        "in english",
        "english please",
        "reply in english",
        "说英文",
        "說英文",
        "用英文",
        "英文回",
        "换英文",
        "ภาษาอังกฤษ",
        "พูดอังกฤษ",
        "ตอบอังกฤษ",
        "เป็นอังกฤษ",
    ),
    "th": (
        "พูดไทย",
        "ภาษาไทย",
        "เป็นไทย",
        "ตอบไทย",
        "ตอบเป็นไทย",
        "speak thai",
        "in thai",
        "说泰",
        "說泰",
        "用泰",
        "泰语",
        "泰語",
        "泰文",
    ),
    "ja": (
        "日本語",
        "にほんご",
        "speak japanese",
        "in japanese",
        "说日语",
        "用日语",
        "日语",
        "日文",
    ),
}

# 切换确认(line_i18n 已满 500,这里内联 4 语,就一句轻量文案)。
_SWITCHED = {
    "zh": "好的，之后用中文跟你说😊 想记一笔或查账,随时发我。",
    "en": "Got it — I'll reply in English from now on 😊 Send an expense or ask anytime.",
    "th": "ได้เลยค่ะ ต่อไปจะตอบเป็นภาษาไทยนะคะ😊 ส่งค่าใช้จ่ายหรือถามได้ตลอดเลยค่ะ",
    "ja": "了解しました、これから日本語で対応しますね😊 経費の記録や照会はいつでもどうぞ。",
}


def detect_lang_switch(text: str) -> str | None:
    """用户明说切到某语言 → 返 'zh'|'en'|'th'|'ja';否则 None。"""
    low = (text or "").strip().lower()
    if not low or len(low) > _MAX_SWITCH_LEN:
        return None
    for lang, phrases in _SWITCH.items():
        if any(p.lower() in low for p in phrases):
            return lang
    return None


def switch_ack(lang: str) -> str:
    """切到 lang 后的确认文案(用新语言)。未知语言回落泰语。"""
    return _SWITCHED.get(lang) or _SWITCHED["th"]


def resolve_reply_lang(text, preferred_lang, ev_lang) -> str:
    """本轮回复语言:这条消息的强脚本信号(自动跟随)> 账号偏好 > LINE 事件语言 > 泰语。"""
    detected = line_classify.detect_text_lang(text)
    if detected in _STRONG:
        return detected
    return preferred_lang or ev_lang or "th"
