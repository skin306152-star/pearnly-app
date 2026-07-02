# -*- coding: utf-8 -*-
"""图片侧大脑歧义问询(LI 设计 §3 第三层 · 2026-07-02 通电)。

没意图 + 单据歧义(读不清/形态怪)时问一次大脑该进哪个只读终端。大脑只许在
record / archive_only / nothing / ask 里选(push 永远来自用户原话——钱路红线在
image_intent._consult_brain 再守一道);答不上/超时/胡答 → 上层 fail-safe 回 default,
绝不因大脑抖动丢用户的图。一击式 JSON,与 agent 大脑走同一网关/后端开关。
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

_LANG_NAMES = {"th": "ไทย", "zh": "中文", "en": "English", "ja": "日本語"}

_PROMPT = """คุณคือผู้ช่วยบัญชี Pearnly ผู้ใช้เพิ่งส่งรูปเอกสารมา แต่ระบบอ่านได้ไม่มั่นใจ
สรุปที่อ่านได้: {summary}

เลือกการจัดการได้เฉพาะ:
- record: บันทึกเป็นค่าใช้จ่ายตามปกติ (เลือกเมื่อดูเป็นใบเสร็จ/ใบกำกับชัดเจน)
- archive_only: เก็บเป็นประวัติสแกนอย่างเดียว ไม่ลงบัญชี
- nothing: ไม่ต้องทำอะไร
- ask: ถามผู้ใช้กลับว่าจะให้ทำอะไร (ไม่แน่ใจ → เลือกอันนี้)

ห้ามเลือกส่งเข้า ERP เด็ดขาด ตอบเป็น JSON เท่านั้น:
{{"terminal":"record|archive_only|nothing|ask","say":"<ข้อความถึงผู้ใช้ เป็นภาษา {lang_name}>"}}"""


def decide_image(summary: dict, lang: str = "th") -> dict:
    """一次网关调用选终端。返回 {} / 非法形状由上层矫正(_consult_brain)。"""
    from services.agent.brain import _brain_backend
    from services.ai_gateway import transport

    prompt = _PROMPT.format(
        summary=json.dumps(summary or {}, ensure_ascii=False),
        lang_name=_LANG_NAMES.get(lang, _LANG_NAMES["en"]),
    )
    outcome = transport.text_to_json(
        prompt,
        tier="flash",
        response_mime=True,
        max_tokens=256,
        timeout_s=12,
        max_retries=1,
        task="agent_image_decide",
        backend=_brain_backend(),
    )
    data = getattr(outcome, "data", None)
    if not getattr(outcome, "ok", False) or not isinstance(data, dict):
        return {}
    return data
