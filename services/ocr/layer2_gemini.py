# -*- coding: utf-8 -*-
"""
services/ocr/layer2_gemini.py · REFACTOR-WA-OCRSPLIT L2-A(纯搬家·0 逻辑改)

从 layer2_structure.py 抽出的 Gemini 传输/解析纯 helper(无 prompt/抽取算法耦合):
  Layer2Error 及 3 子类 · _parse_json · _classify_gemini_exception ·
  model 懒加载单例(_model_cache/_model_lock/_get_model)+ 2 个模型配置常量。
layer2_structure 文件头 re-export 回原命名空间 → 调用方 / COV4 单测 0 改动 · 对象身份不变。
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Optional, Tuple

from .layer2_prompts import (
    _RETRY_TRIM_HINT,
    _SYSTEM_PROMPT,
    _USER_PROMPT_PREFIX,
)

logger = logging.getLogger(__name__)


DEFAULT_TEMPERATURE = 0.0


DEFAULT_MAX_OUTPUT_TOKENS = 16384


class Layer2Error(Exception):
    """Base exception for layer 2 errors. Catch this for generic dispatch."""


class Layer2AuthError(Layer2Error):
    """Missing or invalid GOOGLE_API_KEY / GEMINI_API_KEY (NOT retryable)."""


class Layer2QuotaError(Layer2Error):
    """Quota or rate-limit exceeded. Retry after backoff."""


class Layer2TransientError(Layer2Error):
    """Network / timeout / 5xx. Potentially retryable."""


def _parse_json(text: str) -> dict:
    """Parse Gemini's response as JSON, stripping markdown fences if present.

    With response_mime_type='application/json' Gemini SHOULD not add ```json
    fences. But occasionally it does anyway. Be defensive.

    Raises json.JSONDecodeError on parse failure.
    """
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl > 0:
            s = s[first_nl + 1 :]
        else:
            s = s[3:]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3].rstrip()
    obj = json.loads(s)
    if not isinstance(obj, dict):
        # Gemini returned a list / scalar / etc. — treat as parse failure
        raise json.JSONDecodeError(
            f"expected JSON object, got {type(obj).__name__}",
            s,
            0,
        )
    return obj


def _classify_gemini_exception(e: Exception) -> Exception:
    """Translate raw google-generativeai SDK exception into Layer2 hierarchy.

    The SDK's exception types vary across versions; rather than match
    exception classes directly, we sniff the message + type name. This is
    less precise than catch-by-class but more portable.
    """
    name = type(e).__name__
    msg = str(e)[:400]
    msg_lower = msg.lower()

    # Auth / permission errors
    if (
        name in ("Unauthenticated", "PermissionDenied")
        or "permission denied" in msg_lower
        or "unauthenticated" in msg_lower
        or "api key not valid" in msg_lower
        or "invalid api key" in msg_lower
        or "403" in msg
        or "401" in msg
    ):
        return Layer2AuthError(f"layer2: auth ({name}): {msg}")

    # Quota / rate limit
    if (
        name in ("ResourceExhausted",)
        or "429" in msg
        or "quota" in msg_lower
        or "resource_exhausted" in msg_lower
        or "rate limit" in msg_lower
    ):
        return Layer2QuotaError(f"layer2: quota ({name}): {msg}")

    # Transient (timeout / 5xx / network)
    if (
        name in ("DeadlineExceeded", "ServiceUnavailable", "InternalServerError", "Timeout")
        or "timeout" in msg_lower
        or "deadline" in msg_lower
        or "unavailable" in msg_lower
        or "503" in msg
        or "502" in msg
        or "504" in msg
        or "500" in msg
        or "connection" in msg_lower
    ):
        return Layer2TransientError(f"layer2: transient ({name}): {msg}")

    return Layer2Error(f"layer2: {name}: {msg}")


_model_cache: dict = {}


_model_lock = threading.Lock()


def _get_model(api_key: str, model_name: str):
    """Return a GenerativeModel for the given (api_key, model_name).

    Cached up to 10 distinct combinations to bound memory. Each cache entry
    is a fully-configured GenerativeModel (handles its own connection pool
    internally so we don't need a separate lock for usage, only for init).
    """
    cache_key = (api_key, model_name)

    if cache_key in _model_cache:
        return _model_cache[cache_key]

    with _model_lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]

        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ImportError(
                "layer2: google-generativeai required. " "Install: pip install google-generativeai"
            ) from e

        # Note: direct endpoint (no Cloudflare proxy). If/when dev machine
        # cannot reach generativelanguage.googleapis.com, plumb a proxy via
        # env var rather than hardcoding here.
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
                "response_mime_type": "application/json",
            },
        )

        # Bound cache size — pop oldest if at limit
        if len(_model_cache) >= 10:
            _model_cache.pop(next(iter(_model_cache)))
        _model_cache[cache_key] = model

        logger.info("layer2: GenerativeModel initialized: %s", model_name)
        return model


def _call_gemini_with_retry(
    text: str,
    api_key: str,
    model_name: str,
    max_retries: int,
    timeout: int,
    system_prompt_override: Optional[str] = None,
) -> Tuple[dict, dict]:
    """Make Gemini API call with JSON-parse retry budget.

    Retries ONLY on JSON parse failure / empty response. Network / auth /
    quota errors propagate immediately (no point retrying them at this layer
    — pipeline.py decides whether to retry transient errors).

    When system_prompt_override is provided, that prompt is used instead of
    the default invoice prompt (multi-schema refactor).

    Returns (data: dict, metadata: dict)
    metadata keys: input_tokens, output_tokens, retries
    """
    model = _get_model(api_key=api_key, model_name=model_name)
    sys_prompt = system_prompt_override if system_prompt_override else _SYSTEM_PROMPT
    base_prompt = sys_prompt + "\n\n" + _USER_PROMPT_PREFIX + text

    last_parse_error: Optional[str] = None
    last_raw_preview: str = ""

    for attempt in range(max_retries + 1):
        # v118.35.0.5 · 重试时追加"精简输出"指令 · 救 token 上限截断场景
        prompt = base_prompt + (_RETRY_TRIM_HINT if attempt > 0 else "")
        # v118.35.0.25 · 埋点 · 记 Gemini 调用统计(给 Earn 监控面板 + LINE 告警用)
        import time as _t_v25

        _t_start = _t_v25.time()
        try:
            response = model.generate_content(
                prompt,
                request_options={"timeout": timeout},
            )
            try:
                from services.monitoring import record_gemini_call as _rec

                _rec(
                    success=True, http_status=200, latency_ms=int((_t_v25.time() - _t_start) * 1000)
                )
            except Exception:
                pass
        except Exception as e:
            try:
                from services.monitoring import record_gemini_call as _rec

                _http = 429 if ("ResourceExhausted" in type(e).__name__ or "429" in str(e)) else 500
                _rec(
                    success=False,
                    http_status=_http,
                    latency_ms=int((_t_v25.time() - _t_start) * 1000),
                )
            except Exception:
                pass
            # Network / auth / quota / unknown — classify and propagate
            raise _classify_gemini_exception(e) from e

        raw = (response.text or "").strip() if hasattr(response, "text") else ""

        # Capture token usage (best effort)
        input_tokens = 0
        output_tokens = 0
        try:
            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
                output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        except Exception:  # pragma: no cover  (defensive only)
            pass

        if not raw:
            last_parse_error = "empty response"
            last_raw_preview = ""
            logger.warning(
                "layer2: empty response (attempt %d/%d)",
                attempt + 1,
                max_retries + 1,
            )
            if attempt < max_retries:
                continue
            raise ValueError(
                f"layer2: Gemini returned empty response after " f"{max_retries + 1} attempts"
            )

        try:
            data = _parse_json(raw)
        except json.JSONDecodeError as e:
            last_parse_error = str(e)
            last_raw_preview = raw[:300]
            logger.warning(
                "layer2: JSON parse failed (attempt %d/%d): %s; raw[:200]=%r",
                attempt + 1,
                max_retries + 1,
                e,
                raw[:200],
            )
            if attempt < max_retries:
                continue
            raise ValueError(
                f"layer2: Gemini returned invalid JSON after "
                f"{max_retries + 1} attempts: {last_parse_error}; "
                f"raw[:300]={last_raw_preview!r}"
            ) from e

        return data, {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "retries": attempt,
        }

    # Defensive fallback (loop should always either return or raise above)
    raise ValueError(f"layer2: unreachable; last parse error: {last_parse_error}")
