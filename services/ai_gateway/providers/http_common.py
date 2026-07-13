# -*- coding: utf-8 -*-
"""OpenAI 兼容 HTTP provider(openai/selfhost)的公共件:状态码→error_kind、多模态 parts。

anthropic 有意不入列:它把 529(overloaded)也归 timeout,是 Anthropic 专属差异。
"""

from __future__ import annotations

import base64
from typing import List, Tuple


def error_kind_for_status(status: int) -> str:
    if status in (401, 403):
        return "auth"
    if status == 429:
        return "quota"
    if status in (500, 502, 503, 504):
        return "timeout"
    return "provider"


def image_content_parts(prompt: str, images: List[Tuple[bytes, str]]) -> list:
    parts: list = [{"type": "text", "text": prompt}]
    for data, mime in images:
        b64 = base64.b64encode(data).decode("ascii")
        parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    return parts
