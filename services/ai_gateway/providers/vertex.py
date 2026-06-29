# -*- coding: utf-8 -*-
"""vertex provider:google-genai + Vertex AI(服务账号 · 企业配额/数据驻留/不训练)。

同模型(gemini-*),只是换"门":认证走 GCP 服务账号(GOOGLE_APPLICATION_CREDENTIALS / ADC),
区域 VERTEX_LOCATION(默认 asia-southeast1·离泰国最近)。api_key 参数对 Vertex 无意义(忽略)。
4 形态接口与 aistudio 完全一致 → 上层 transport 无感切换。
"""

from __future__ import annotations

import os
import threading
from typing import List, Optional, Tuple

from services.ai_gateway.tasks import ProviderOutcome

NAME = "vertex"

_client_cache: dict = {}
_lock = threading.Lock()


def _location() -> str:
    return os.environ.get("VERTEX_LOCATION", "asia-southeast1").strip() or "asia-southeast1"


def _project() -> Optional[str]:
    return (
        os.environ.get("GCP_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("VERTEX_PROJECT")
        or None
    )


def _resolve_model(tier: str) -> str:
    from services.ocr import gemini_models

    return {
        "flash": gemini_models.flash,
        "flash_lite": gemini_models.flash_lite,
        "best": gemini_models.best,
        "fallback": gemini_models.fallback,
        "escalate": gemini_models.escalate,
    }.get(tier, gemini_models.flash)()


def _embed_model() -> str:
    # 默认与 aistudio 同一向量空间(gemini-embedding-001)→ 知识库无需重建索引
    return (
        os.environ.get("VERTEX_EMBED_MODEL", "gemini-embedding-001").strip()
        or "gemini-embedding-001"
    )


def _client():
    loc = _location()
    proj = _project()
    key = (proj, loc)
    if key in _client_cache:
        return _client_cache[key]
    with _lock:
        if key in _client_cache:
            return _client_cache[key]
        from google import genai

        kwargs = {"vertexai": True, "location": loc}
        if proj:
            kwargs["project"] = proj
        c = genai.Client(**kwargs)
        if len(_client_cache) >= 8:
            _client_cache.pop(next(iter(_client_cache)))
        _client_cache[key] = c
        return c


def _error_kind(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc).lower()
    code = getattr(exc, "code", None)
    if code in (401, 403) or "permission" in msg or "unauthenticated" in msg or "api key" in msg:
        return "auth"
    if code == 429 or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg:
        return "quota"
    if (
        code in (500, 502, 503, 504)
        or "timeout" in msg
        or "deadline" in msg
        or "unavailable" in msg
        or "DeadlineExceeded" in name
    ):
        return "timeout"
    return "provider"


def _config(temperature, max_tokens, response_mime):
    from google.genai import types

    kw = {"temperature": temperature, "max_output_tokens": max_tokens}
    if response_mime:
        kw["response_mime_type"] = "application/json"
    return types.GenerateContentConfig(**kw)


def _usage(resp) -> Tuple[int, int]:
    try:
        u = getattr(resp, "usage_metadata", None)
        if u is not None:
            return (
                int(getattr(u, "prompt_token_count", 0) or 0),
                int(getattr(u, "candidates_token_count", 0) or 0),
            )
    except Exception:
        pass
    return (0, 0)


def _gen_json(contents, *, model_name, config, max_retries):
    from services.ocr.layer2_gemini import _parse_json

    client = _client()
    for attempt in range(max_retries + 1):
        try:
            resp = client.models.generate_content(
                model=model_name, contents=contents, config=config
            )
        except Exception as e:  # noqa: BLE001
            return ProviderOutcome(ok=False, error_kind=_error_kind(e), model=model_name)
        raw = (getattr(resp, "text", "") or "").strip()
        it, ot = _usage(resp)
        if raw:
            try:
                return ProviderOutcome(
                    ok=True,
                    data=_parse_json(raw),
                    model=model_name,
                    input_tokens=it,
                    output_tokens=ot,
                )
            except Exception:  # noqa: BLE001
                pass
        if attempt < max_retries:
            continue
    return ProviderOutcome(ok=False, error_kind="parse", model=model_name)


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
    model_name = _resolve_model(tier)
    return _gen_json(
        prompt,
        model_name=model_name,
        config=_config(temperature, max_tokens, response_mime),
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
    from google.genai import types

    model_name = _resolve_model(tier)
    contents: list = []
    for data, mime in images:
        contents.append(types.Part.from_bytes(data=data, mime_type=mime))
    contents.append(prompt)
    return _gen_json(
        contents,
        model_name=model_name,
        config=_config(temperature, max_tokens, response_mime),
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
    from google.genai import types

    model_name = _resolve_model(tier)
    kw = {"temperature": temperature}
    if system:
        kw["system_instruction"] = system
    try:
        resp = _client().models.generate_content(
            model=model_name, contents=prompt, config=types.GenerateContentConfig(**kw)
        )
    except Exception as e:  # noqa: BLE001
        return ProviderOutcome(ok=False, error_kind=_error_kind(e), model=model_name)
    text = (getattr(resp, "text", "") or "").strip()
    it, ot = _usage(resp)
    if not text:
        return ProviderOutcome(ok=False, error_kind="parse", model=model_name)
    return ProviderOutcome(ok=True, data=text, model=model_name, input_tokens=it, output_tokens=ot)


def embed(
    texts: List[str],
    *,
    is_query: bool = False,
    api_key: Optional[str] = None,
    dim: int = 768,
    timeout_s: int = 120,
) -> ProviderOutcome:
    from google.genai import types

    model_name = _embed_model()
    task = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    try:
        resp = _client().models.embed_content(
            model=model_name,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task, output_dimensionality=dim),
        )
        out = [list(e.values) for e in resp.embeddings]
    except Exception as e:  # noqa: BLE001
        return ProviderOutcome(ok=False, error_kind=_error_kind(e), model=model_name)
    return ProviderOutcome(ok=True, data=out, model=model_name)
