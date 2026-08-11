# -*- coding: utf-8 -*-
"""OpenAI 兼容 HTTP provider(openai/selfhost/qwen)的公共件:
状态码→error_kind、POST、响应取文本+用量、多模态 parts。

anthropic 有意不入列:它把 529(overloaded)也归 timeout,是 Anthropic 专属差异。
"""

from __future__ import annotations

import base64
from typing import List, Optional, Tuple


def error_kind_for_status(status: int) -> str:
    if status in (401, 403):
        return "auth"
    if status == 429:
        return "quota"
    if status in (500, 502, 503, 504):
        return "timeout"
    return "provider"


def post_json(url: str, headers: dict, payload: dict, timeout_s: int):
    """POST → (json, error_kind)。网络/HTTP 错一律收敛为 error_kind,不抛给热路径。"""
    import httpx

    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=timeout_s)
    except httpx.TimeoutException:
        return None, "timeout"
    except httpx.HTTPError:
        return None, "provider"
    if resp.status_code >= 400:
        return None, error_kind_for_status(resp.status_code)
    try:
        return resp.json(), None
    except Exception:  # noqa: BLE001
        return None, "parse"


def chat_text_and_usage(
    body: Optional[dict],
) -> Tuple[Optional[str], Optional[str], Tuple[int, int]]:
    """chat/completions 响应 → (正文, error_kind, (输入token, 输出token))。形状不对 = parse。"""
    try:
        text = body["choices"][0]["message"]["content"] or ""
        usage = body.get("usage") or {}
        toks = (
            int(usage.get("prompt_tokens", 0) or 0),
            int(usage.get("completion_tokens", 0) or 0),
        )
        return text.strip(), None, toks
    except Exception:  # noqa: BLE001
        return None, "parse", (0, 0)


def image_content_parts(prompt: str, images: List[Tuple[bytes, str]]) -> list:
    parts: list = [{"type": "text", "text": prompt}]
    for data, mime in images:
        b64 = base64.b64encode(data).decode("ascii")
        parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    return parts
