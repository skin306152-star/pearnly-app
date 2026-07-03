# -*- coding: utf-8 -*-
"""aistudio provider:google-generativeai + API key(现状后端)。

实现 4 形态(text→json / image→json / free-text / embedding),供网关 transport 调用。
复用 layer2_gemini 的 JSON 解析与异常分类、services.monitoring 埋点,口径与现状一致。
模型档位(flash/flash_lite/best/...)经 gemini_models 解析具体模型名 —— 本文件不出现具体型号。
"""

from __future__ import annotations

import os
import time
from typing import List, Optional, Tuple

from services.ai_gateway.tasks import ProviderOutcome

NAME = "aistudio"


def _resolve_model(tier: str) -> str:
    from services.ocr import gemini_models

    return {
        "flash": gemini_models.flash,
        "flash_lite": gemini_models.flash_lite,
        "best": gemini_models.best,
        "fallback": gemini_models.fallback,
        "escalate": gemini_models.escalate,
        "brain": gemini_models.brain,
    }.get(tier, gemini_models.flash)()


def _embed_model() -> str:
    return (
        os.environ.get("AISTUDIO_EMBED_MODEL", "gemini-embedding-001").strip()
        or "gemini-embedding-001"
    )


def _error_kind(exc: Exception) -> str:
    """google-generativeai 原始异常 → 标准 error_kind(复用 layer2 分类)。"""
    from services.ocr.layer2_gemini import (
        Layer2AuthError,
        Layer2QuotaError,
        Layer2TransientError,
        _classify_gemini_exception,
    )

    mapped = _classify_gemini_exception(exc)
    if isinstance(mapped, Layer2AuthError):
        return "auth"
    if isinstance(mapped, Layer2QuotaError):
        return "quota"
    if isinstance(mapped, Layer2TransientError):
        return "timeout"
    return "provider"


def _record(success: bool, status: int, ms: int) -> None:
    try:
        from services.monitoring import record_gemini_call

        record_gemini_call(success=success, http_status=status, latency_ms=ms)
    except Exception:
        pass


def _gen_config(temperature: float, max_tokens: int, response_mime: bool) -> dict:
    cfg = {"temperature": temperature, "max_output_tokens": max_tokens}
    if response_mime:
        cfg["response_mime_type"] = "application/json"
    return cfg


def _model(api_key: str, model_name: str, cfg: dict):
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name=model_name, generation_config=cfg)


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


def _json_or_outcome(model_name, contents, *, timeout_s, max_retries, model):
    """调用 + JSON 解析重试(parse/empty 才重试);其余异常即收敛为 error_kind。"""
    from services.ocr.layer2_gemini import _parse_json

    last_err = None
    for attempt in range(max_retries + 1):
        t0 = time.time()
        try:
            resp = model.generate_content(contents, request_options={"timeout": timeout_s})
            _record(True, 200, int((time.time() - t0) * 1000))
        except Exception as e:  # noqa: BLE001
            kind = _error_kind(e)
            _record(False, 429 if kind == "quota" else 500, int((time.time() - t0) * 1000))
            return ProviderOutcome(ok=False, error_kind=kind, model=model_name)
        raw = (resp.text or "").strip() if hasattr(resp, "text") else ""
        it, ot = _usage(resp)
        if not raw:
            last_err = "empty"
        else:
            try:
                data = _parse_json(raw)
                return ProviderOutcome(
                    ok=True, data=data, model=model_name, input_tokens=it, output_tokens=ot
                )
            except Exception as e:  # noqa: BLE001 — JSONDecodeError 等
                last_err = str(e)
        if attempt < max_retries:
            continue
    return ProviderOutcome(ok=False, error_kind="parse", model=model_name)


def text_to_action(prompt: str, *, tools, **kw) -> ProviderOutcome:
    """原生 function-calling 暂未实现(旧 SDK·非 prod agent 后端)→ 调用方回落 JSON 协议。"""
    return ProviderOutcome(ok=False, error_kind="unsupported", model=NAME)


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
    if not api_key:
        return ProviderOutcome(ok=False, error_kind="auth")
    model_name = _resolve_model(tier)
    model = _model(api_key, model_name, _gen_config(temperature, max_tokens, response_mime))
    return _json_or_outcome(
        model_name, prompt, timeout_s=timeout_s, max_retries=max_retries, model=model
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
    """images = [(bytes, mime_type), ...];contents = [prompt, {img}, {img}...]。"""
    if not api_key:
        return ProviderOutcome(ok=False, error_kind="auth")
    model_name = _resolve_model(tier)
    model = _model(api_key, model_name, _gen_config(temperature, max_tokens, response_mime))
    contents: list = [prompt]
    for data, mime in images:
        contents.append({"mime_type": mime, "data": data})
    return _json_or_outcome(
        model_name, contents, timeout_s=timeout_s, max_retries=max_retries, model=model
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
    if not api_key:
        return ProviderOutcome(ok=False, error_kind="auth")
    model_name = _resolve_model(tier)
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    kwargs = {"model_name": model_name, "generation_config": {"temperature": temperature}}
    if system:
        kwargs["system_instruction"] = system
    model = genai.GenerativeModel(**kwargs)
    t0 = time.time()
    try:
        resp = model.generate_content(prompt, request_options={"timeout": timeout_s})
        _record(True, 200, int((time.time() - t0) * 1000))
    except Exception as e:  # noqa: BLE001
        kind = _error_kind(e)
        _record(False, 429 if kind == "quota" else 500, int((time.time() - t0) * 1000))
        return ProviderOutcome(ok=False, error_kind=kind, model=model_name)
    text = (resp.text or "").strip() if hasattr(resp, "text") else ""
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
    """text → 向量。走 batchEmbedContents REST,与知识库旧实现字节级一致(向量空间不漂)。"""
    if not texts:
        return ProviderOutcome(ok=True, data=[])
    if not api_key:
        return ProviderOutcome(ok=False, error_kind="auth")
    import httpx

    model_name = _embed_model()
    task = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:batchEmbedContents"
    payload = {
        "requests": [
            {
                "model": f"models/{model_name}",
                "content": {"parts": [{"text": t}]},
                "taskType": task,
                "outputDimensionality": dim,
            }
            for t in texts
        ]
    }
    try:
        resp = httpx.post(url, params={"key": api_key}, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        out = [row["values"] for row in resp.json()["embeddings"]]
    except httpx.TimeoutException:
        return ProviderOutcome(ok=False, error_kind="timeout", model=model_name)
    except httpx.HTTPError:
        return ProviderOutcome(ok=False, error_kind="provider", model=model_name)
    return ProviderOutcome(ok=True, data=out, model=model_name)
