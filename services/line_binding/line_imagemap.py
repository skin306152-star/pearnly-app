# -*- coding: utf-8 -*-
"""泰语图卡(imagemap)构建器 —— 把设计师的整图卡接成 LINE imagemap/图片消息。

设计师交付的泰语卡是"整张图 + 画进图里的按钮"。带按钮的卡用 imagemap(在按钮位置切
可点区,点了开官网或触发指令);无按钮的卡用普通图片消息。图片由 line_card_image_routes
按 LINE 约定的 baseUrl/{size} 提供(返回 1040 母图,LINE 自适配)。

只做泰语:泰语用户看图卡,其他语言由调用方回落现有文字版(line_bind_i18n / line_i18n)。
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from services.line_binding.line_bind_i18n import CONNECT_URL

# 图片服务基址(LINE 会追加 /{size};见 line_card_image_routes)。
# _CARD_VER:改图后 bump 一位,破 LINE/客户端按 URL 的图片缓存(URL 变 = 强制重取)。
_CARD_VER = "2"
_IMG_BASE = f"https://pearnly.com/api/line/card/{_CARD_VER}"

_URI = "uri"
_MSG = "message"

# 触发某指令的消息动作文本(点按钮 = 用户发这句 → 走分类路由)。
_CAP_TRIGGER = "ทำอะไรได้บ้าง"  # → line_classify.intro_intent == "capability"

# 单按钮底部点击区(整宽底部条,够手指点)。
_BOTTOM_1040 = {"x": 20, "y": 870, "width": 1000, "height": 160}
_BOTTOM_1560 = {"x": 20, "y": 1390, "width": 1000, "height": 160}
# 双按钮底部左右切分。
_BOTTOM_1560_L = {"x": 20, "y": 1390, "width": 486, "height": 160}
_BOTTOM_1560_R = {"x": 534, "y": 1390, "width": 486, "height": 160}


def _act(kind: str, value: str, area: dict) -> dict:
    if kind == _URI:
        return {"type": "uri", "linkUri": value, "area": area}
    return {"type": "message", "text": value, "area": area}


# card_key -> (图文件名 stem, 高度, altText, [actions])。actions 空 = 普通图片(无可点区)。
_CARDS: Dict[str, Tuple[str, int, str, List[dict]]] = {
    "welcome": (
        "A1-welcome",
        1560,
        "ยินดีต้อนรับสู่ Pearnly ผู้ช่วยบัญชีของคุณ",
        [
            _act(_URI, CONNECT_URL, _BOTTOM_1560_L),
            _act(_MSG, _CAP_TRIGGER, _BOTTOM_1560_R),
        ],
    ),
    "capability": (
        "A2-capability",
        1560,
        "Pearnly ช่วยอะไรได้บ้าง",
        [_act(_URI, CONNECT_URL, _BOTTOM_1560)],
    ),
    "need_bind": (
        "A3-need-connect-text",
        1040,
        "กรุณาเชื่อมต่อบัญชี Pearnly ก่อนเริ่มใช้งาน",
        [_act(_URI, CONNECT_URL, _BOTTOM_1040)],
    ),
    "image_not_bound": (
        "A4-need-connect-image",
        1040,
        "ได้รับรูปภาพแล้ว กรุณาเชื่อมต่อบัญชี Pearnly ก่อน",
        [_act(_URI, CONNECT_URL, _BOTTOM_1040)],
    ),
    "bind_success": ("A5-connect-success", 1040, "เชื่อมต่อ Pearnly สำเร็จแล้ว", []),
    "bind_invalid": (
        "A6-code-invalid",
        1040,
        "ลิงก์เชื่อมต่อหมดอายุ กรุณาขอลิงก์ใหม่",
        [_act(_URI, CONNECT_URL, _BOTTOM_1040)],
    ),
    "bind_conflict": (
        "A7-connect-conflict",
        1560,
        "บัญชี LINE นี้เชื่อมต่อกับบัญชี Pearnly อื่นอยู่แล้ว",
        [
            _act(_URI, CONNECT_URL, _BOTTOM_1560_L),
            _act(_URI, CONNECT_URL, _BOTTOM_1560_R),
        ],
    ),
    "ocr_failed": ("A9-ocr-failed", 1040, "ยังอ่านบิลใบนี้ไม่ชัด ลองถ่ายใหม่อีกครั้ง", []),
    "unsupported": ("A10-unsupported", 1040, "ข้อความประเภทนี้ยังไม่รองรับ", []),
    "no_credit": (
        "A11-no-credit",
        1040,
        "เครดิตการอ่านบิลของเดือนนี้หมดแล้ว",
        [_act(_URI, CONNECT_URL, _BOTTOM_1040)],
    ),
}

# B 组动态卡的 hero 横幅(无文字·状态色皮肤)· result_card 顶部按状态贴。2132×738(≈2.9:1)。
_BANNERS: Dict[str, str] = {
    "posted": "B-banner-posted",
    "confirm": "B-banner-review",
    "review": "B-banner-incomplete",
    "dup": "B-banner-duplicate",
}
_BANNER_RATIO = "2132:738"

# 其它横幅(非 result_card 状态):解绑确认/成功、查账汇总、凭证 PDF。
UNBIND_CONFIRM_BANNER = "A8a-unbind-confirm-banner"
UNBIND_SUCCESS_BANNER = "A8b-unbind-success-banner"
SUMMARY_BANNER = "B-banner-summary"
PROOF_BANNER = "B-banner-proof"
_EXTRA_BANNERS = frozenset(
    {UNBIND_CONFIRM_BANNER, UNBIND_SUCCESS_BANNER, SUMMARY_BANNER, PROOF_BANNER}
)

# 已交付图卡 + 横幅的 stem 白名单(出图路由用)。
CARD_STEMS = (
    frozenset(stem for stem, _h, _alt, _a in _CARDS.values())
    | frozenset(_BANNERS.values())
    | _EXTRA_BANNERS
    | frozenset(f"A12-onboard-{i}" for i in range(1, 7))
)


def hero(stem: str) -> dict:
    """任意横幅 stem → Flex hero 图块(2132:738 cover)。"""
    return {
        "type": "image",
        "url": f"{_IMG_BASE}/{stem}/1040",
        "size": "full",
        "aspectRatio": _BANNER_RATIO,
        "aspectMode": "cover",
    }


def banner_hero(state: str) -> Optional[dict]:
    """按 result_card 状态返回 Flex hero 图块(横幅皮肤)。无对应状态 → None。"""
    stem = _BANNERS.get(state)
    return hero(stem) if stem else None


# A12 新手教程轮播(绑定成功后推):每张方形图卡 = 一个卖点,点开官网看示例。
_ONBOARD_STEMS = tuple(f"A12-onboard-{i}" for i in range(1, 7))


def onboarding_carousel() -> dict:
    """新手轮播:Flex carousel·6 张方形图卡(hero 整图可点→官网)。一条消息横滑。"""
    bubbles = [
        {
            "type": "bubble",
            "size": "mega",
            "hero": {
                "type": "image",
                "url": f"{_IMG_BASE}/{stem}/1040",
                "size": "full",
                "aspectRatio": "1:1",
                "aspectMode": "cover",
                "action": {"type": "uri", "uri": CONNECT_URL},
            },
        }
        for stem in _ONBOARD_STEMS
    ]
    return {
        "type": "flex",
        "altText": "แนะนำการใช้งาน Pearnly",
        "contents": {"type": "carousel", "contents": bubbles},
    }


def has_card(card_key: str) -> bool:
    return card_key in _CARDS


def card_message(card_key: str) -> Optional[dict]:
    """构建泰语图卡消息(有按钮→imagemap,无按钮→image)。未知 key → None。"""
    spec = _CARDS.get(card_key)
    if not spec:
        return None
    stem, height, alt, actions = spec
    base = f"{_IMG_BASE}/{stem}"
    if not actions:
        url = f"{base}/1040"
        return {"type": "image", "originalContentUrl": url, "previewImageUrl": url}
    return {
        "type": "imagemap",
        "baseUrl": base,
        "altText": alt[:400],
        "baseSize": {"width": 1040, "height": height},
        "actions": actions,
    }
