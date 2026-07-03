# -*- coding: utf-8 -*-
"""
services/ocr/layer2_gemini.py · REFACTOR-WA-OCRSPLIT L2-A(纯搬家·0 逻辑改)

从 layer2_structure.py 抽出的 Gemini 传输/解析纯 helper(无 prompt/抽取算法耦合):
  Layer2Error 及 3 子类 · _parse_json · _classify_gemini_exception + 2 个模型配置常量。
layer2_structure 文件头 re-export 回原命名空间 → 调用方 / COV4 单测 0 改动 · 对象身份不变。
模型调用一律经 model_client→ai_gateway(2026-07-03 收口,aistudio 直连 SDK 老路删除,
aistudio 后端由 providers/aistudio.py 承接,埋点/解析/重试口径一致)。
"""

from __future__ import annotations

import json
import logging
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


def _first_json_object(s: str) -> str:
    """抠出首个括号平衡的 {...} 子串(字符串内的括号/转义不计);找不到抛 JSONDecodeError。"""
    start = s.find("{")
    if start < 0:
        raise json.JSONDecodeError("no JSON object found", s, 0)
    depth, in_str, esc = 0, False, False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    raise json.JSONDecodeError("unbalanced JSON object", s, start)


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
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        # 兜底:模型偶尔在 JSON 前后夹散文("Here's the result: {...}")→ 抠出首个完整 {...} 再解析。
        # 严格路先行,仅失败时才走(OCR 干净 JSON 零影响)。抠不出仍抛,交上层救援。
        obj = json.loads(_first_json_object(s))
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


def _record_gemini_call(success: bool, kind: Optional[str], ms: int) -> None:
    """监控埋点:保留 record_gemini_call 口径(网关后端 provider 不自带此埋点)。"""
    try:
        from services.monitoring import record_gemini_call

        http = 200 if success else (429 if kind == "quota" else 500)
        record_gemini_call(success=success, http_status=http, latency_ms=ms)
    except Exception:
        pass


def _l2_error_for_kind(kind: str, model_name: str) -> Exception:
    msg = f"layer2: gateway ({kind}) model={model_name}"
    if kind == "auth":
        return Layer2AuthError(msg)
    if kind == "quota":
        return Layer2QuotaError(msg)
    return Layer2TransientError(msg)


def _call_l2_via_gateway(
    base_prompt: str, api_key: str, model_name: str, max_retries: int, timeout: int
) -> Tuple[dict, dict]:
    """L2 文本→JSON 经 model_client(全后端统一)。保留 record_gemini_call 埋点
    + (data, meta) 元组契约;auth/quota/transient 映射回 Layer2 异常,
    parse/empty 在重试预算内追加 _RETRY_TRIM_HINT 再试(同原逻辑)。"""
    import time as _t

    from services.ocr import model_client

    last_kind = "parse"
    for attempt in range(max_retries + 1):
        prompt = base_prompt + (_RETRY_TRIM_HINT if attempt > 0 else "")
        t0 = _t.time()
        out = model_client.json_from_text(
            prompt,
            model_name=model_name,
            task="ocr.layer2",
            api_key=api_key,
            timeout_s=timeout,
            max_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
        )
        _record_gemini_call(out.ok, out.error_kind, int((_t.time() - t0) * 1000))
        if out.ok:
            return out.data, {
                "input_tokens": out.input_tokens,
                "output_tokens": out.output_tokens,
                "retries": attempt,
            }
        last_kind = out.error_kind or "parse"
        if last_kind in ("auth", "quota", "timeout"):
            raise _l2_error_for_kind(last_kind, model_name)
        # parse/empty:落入下一轮重试(预算用尽则退出循环抛下方 ValueError)
    raise ValueError(
        f"layer2: gateway returned no valid JSON after {max_retries + 1} attempts ({last_kind})"
    )


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
    sys_prompt = system_prompt_override if system_prompt_override else _SYSTEM_PROMPT
    # 反馈闭环 ② 消费侧:仅 invoice 路径(无 override)注入该主体历史修正 few-shot。
    # OCR_FEWSHOT_ENABLED 关 / 无上下文 / 例库空 → 返空串 → base_prompt 字节级不变。
    fewshot_hint = ""
    if system_prompt_override is None:
        from services.ocr.feedback import fewshot

        fewshot_hint = fewshot.maybe_block_for_text(text)
    base_prompt = sys_prompt + "\n\n" + fewshot_hint + _USER_PROMPT_PREFIX + text
    return _call_l2_via_gateway(base_prompt, api_key, model_name, max_retries, timeout)
