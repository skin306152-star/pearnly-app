# -*- coding: utf-8 -*-
"""出口护栏(确定性 · 可复用):判一段【要发给用户的】文案是否安全。

语气层用 LLM 组织自然回复,但模型输出不可信 —— 发给用户前必须过这层。命中以下任意一类即
不安全(调用方回落确定性模板):
- 供应商/系统信息泄露(模型名/系统提示/API key 等)。
- 假执行结果:语气层从不写账/过账/删除/申报,出现「已记录/บันทึกแล้ว/recorded」这类完成态
  即模型幻觉,严禁外泄给用户。

纯函数,无副作用,大小写不敏感。
"""

from __future__ import annotations

import re

# a) 供应商/系统/密钥泄露(「api key」由 _APIKEY_RE 兜中间分隔形式)。
_LEAK_KEYWORDS = (
    "gemini",
    "gpt",
    "chatgpt",
    "claude",
    "openai",
    "anthropic",
    "deepseek",
    "llama",
    "system prompt",
    "模型",
    "提示词",
    "系统提示",
    "โมเดล",
)

# b) 假执行结果:这层从不执行动作,出现完成态即幻觉。
_FAKE_RESULT_KEYWORDS = (
    "已记录",
    "已记账",
    "已入账",
    "已保存",
    "已删除",
    "已撤销",
    "已申报",
    "已提交",
    "记好了",
    "帮你记好",
    "บันทึกแล้ว",
    "บันทึกให้แล้ว",
    "ลบแล้ว",
    "ยกเลิกแล้ว",
    "ยื่นแล้ว",
    "ส่งให้แล้ว",
    "recorded",
    "saved it",
    "logged it",
    "deleted",
    "cancelled it",
    "submitted",
    "filed it",
    "i've recorded",
    "記録しました",
    "保存しました",
    "削除しました",
    "取り消しました",
    "申告しました",
)

_APIKEY_RE = re.compile(r"api[\s_\-]*key", re.IGNORECASE)


def is_safe(text: str) -> bool:
    """文案可发给用户 → True;泄露供应商/系统信息或谎称已执行动作 → False。"""
    t = str(text or "").lower()
    if _APIKEY_RE.search(t):
        return False
    if any(kw in t for kw in _LEAK_KEYWORDS):
        return False
    if any(kw in t for kw in _FAKE_RESULT_KEYWORDS):
        return False
    return True
