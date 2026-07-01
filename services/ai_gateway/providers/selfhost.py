# -*- coding: utf-8 -*-
"""selfhost provider:OpenAI 兼容端点(自托管 Qwen2.5-VL / vLLM 等)。

数据零出门 · 量大后只付电费。接口与 aistudio/vertex 完全一致 → transport 无感切换。
env:
  SELFHOST_OCR_URL    OpenAI 兼容 base(如 http://host:8000/v1)
  SELFHOST_OCR_KEY    可选 Bearer(vLLM 默认无鉴权可空)
  SELFHOST_OCR_MODEL  视觉/文本模型名(如 Qwen2.5-VL-32B-Instruct)
  SELFHOST_EMBED_MODEL  embedding 模型名(可选)
注:模型档位 tier 对自托管统一映射到同一个 VLM(单模型);需要分档时再按 env 细分。
"""

from __future__ import annotations

import base64
import os
from typing import List, Optional, Tuple

from services.ai_gateway.tasks import ProviderOutcome

NAME = "selfhost"


def _base() -> str:
    return (os.environ.get("SELFHOST_OCR_URL") or "").rstrip("/")


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    key = os.environ.get("SELFHOST_OCR_KEY")
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def _model() -> str:
    return os.environ.get("SELFHOST_OCR_MODEL", "").strip()


def _embed_model() -> str:
    return os.environ.get("SELFHOST_EMBED_MODEL", "").strip() or _model()


def _error_kind_status(status: int) -> str:
    if status in (401, 403):
        return "auth"
    if status == 429:
        return "quota"
    if status in (500, 502, 503, 504):
        return "timeout"
    return "provider"


def _post(path: str, payload: dict, timeout_s: int):
    """POST → (json, error_kind)。网络/HTTP 错收敛为 error_kind。"""
    import httpx

    base = _base()
    if not base:
        return None, "auth"  # 未配置端点 → 当作不可用(auth 类·上层走 fallback)
    try:
        resp = httpx.post(f"{base}{path}", headers=_headers(), json=payload, timeout=timeout_s)
    except httpx.TimeoutException:
        return None, "timeout"
    except httpx.HTTPError:
        return None, "provider"
    if resp.status_code >= 400:
        return None, _error_kind_status(resp.status_code)
    try:
        return resp.json(), None
    except Exception:  # noqa: BLE001
        return None, "parse"


def _content_parts(prompt: str, images: List[Tuple[bytes, str]]) -> list:
    parts: list = [{"type": "text", "text": prompt}]
    for data, mime in images:
        b64 = base64.b64encode(data).decode("ascii")
        parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    return parts


def _chat_text(payload, timeout_s):
    body, kind = _post("/chat/completions", payload, timeout_s)
    if kind:
        return None, kind, (0, 0)
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


def _chat_json(prompt, images, *, temperature, response_mime, max_tokens, timeout_s, max_retries):
    from services.ocr.layer2_gemini import _parse_json

    model_name = _model()
    content = _content_parts(prompt, images) if images else prompt
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_mime:
        payload["response_format"] = {"type": "json_object"}
    last_raw = ""
    for attempt in range(max_retries + 1):
        text, kind, toks = _chat_text(payload, timeout_s)
        if kind:
            return ProviderOutcome(ok=False, error_kind=kind, model=model_name)
        if text:
            last_raw = text
            try:
                return ProviderOutcome(
                    ok=True,
                    data=_parse_json(text),
                    model=model_name,
                    input_tokens=toks[0],
                    output_tokens=toks[1],
                )
            except Exception:  # noqa: BLE001
                pass
        if attempt < max_retries:
            continue
    # 解析失败带回原文(Agent 可把散文当回复救援)· raw 绝不进日志(_observe 只记 error_kind/token)
    return ProviderOutcome(ok=False, error_kind="parse", model=model_name, raw=last_raw)


def text_to_json(
    prompt: str,
    *,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    response_mime: bool = True,
    max_tokens: int = 16384,
    timeout_s: int = 30,
    max_retries: int = 1,
) -> ProviderOutcome:
    return _chat_json(
        prompt,
        None,
        temperature=temperature,
        response_mime=response_mime,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        max_retries=max_retries,
    )


def multimodal_to_json(
    prompt: str,
    images: List[Tuple[bytes, str]],
    *,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    response_mime: bool = True,
    max_tokens: int = 8192,
    timeout_s: int = 60,
    max_retries: int = 1,
) -> ProviderOutcome:
    return _chat_json(
        prompt,
        images,
        temperature=temperature,
        response_mime=response_mime,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        max_retries=max_retries,
    )


def text_to_text(
    prompt: str,
    *,
    system: Optional[str] = None,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.2,
    timeout_s: int = 120,
) -> ProviderOutcome:
    model_name = _model()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model_name, "messages": messages, "temperature": temperature}
    text, kind, toks = _chat_text(payload, timeout_s)
    if kind:
        return ProviderOutcome(ok=False, error_kind=kind, model=model_name)
    if not text:
        return ProviderOutcome(ok=False, error_kind="parse", model=model_name)
    return ProviderOutcome(
        ok=True, data=text, model=model_name, input_tokens=toks[0], output_tokens=toks[1]
    )


def embed(
    texts: List[str],
    *,
    is_query: bool = False,
    api_key: Optional[str] = None,
    dim: int = 768,
    timeout_s: int = 120,
) -> ProviderOutcome:
    model_name = _embed_model()
    body, kind = _post("/embeddings", {"model": model_name, "input": texts}, timeout_s)
    if kind:
        return ProviderOutcome(ok=False, error_kind=kind, model=model_name)
    try:
        rows = sorted(body["data"], key=lambda d: d.get("index", 0))
        out = [list(r["embedding"]) for r in rows]
    except Exception:  # noqa: BLE001
        return ProviderOutcome(ok=False, error_kind="parse", model=model_name)
    return ProviderOutcome(ok=True, data=out, model=model_name)
