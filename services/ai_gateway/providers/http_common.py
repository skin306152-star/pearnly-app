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


def bearer_headers(key):
    """Content-Type + 可选 Bearer。key 空 = 无鉴权(vLLM 场景)。"""
    h = {"Content-Type": "application/json"}
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def chat_json_outcome(do_call, parse, model_name, max_retries):
    """三 provider 同构的重试→ProviderOutcome 循环:传输错立即带 kind 返回;
    解析失败重读;用尽落 parse 并带回原文(raw 绝不进日志,_observe 只记 error_kind/token)。
    do_call() -> (text, kind, (in_tokens, out_tokens));parse(text) -> data。"""
    from services.ai_gateway.tasks import ProviderOutcome

    last_raw = ""
    for _ in range(max_retries + 1):
        text, kind, toks = do_call()
        if kind:
            return ProviderOutcome(ok=False, error_kind=kind, model=model_name)
        if text:
            last_raw = text
            try:
                return ProviderOutcome(
                    ok=True,
                    data=parse(text),
                    model=model_name,
                    input_tokens=toks[0],
                    output_tokens=toks[1],
                )
            except Exception:  # noqa: BLE001 — 坏 JSON → 重试;用尽落 parse
                pass
    return ProviderOutcome(ok=False, error_kind="parse", model=model_name, raw=last_raw)
