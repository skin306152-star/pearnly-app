# -*- coding: utf-8 -*-
"""anthropic provider:Claude Messages API 适配器(与 aistudio/vertex/selfhost 同契约)。

接口与其它 provider 一致 → transport 无感切换(backend="anthropic" 即整条 Agent 大脑走 Claude)。
env:
  ANTHROPIC_API_KEY     Claude API key(缺 → auth 类·上层 fallback,不抛)
  ANTHROPIC_FLASH_MODEL  flash 档模型(默认 Haiku 4.5·便宜快)
  ANTHROPIC_BEST_MODEL   best 档模型(默认 Sonnet 5·强推理)
  ANTHROPIC_BASE_URL     可选自定义 base(默认官方)

提示缓存:大脑「入多出少」——固定前缀(persona+工具表 ~2k token)每次调用重发。传 system(带
cache_control)→ Anthropic 缓存该前缀,命中读价降到 10%,是这类 workload 的核心省钱杠杆。
"""

from __future__ import annotations

import os
import re
from typing import Optional, Tuple

from services.ai_gateway.tasks import ProviderOutcome

NAME = "anthropic"
_VERSION = "2023-06-01"
# 带 8 位日期后缀的模型(如 ...-20251001)仍收 temperature;新别名(claude-sonnet-5 等)已废弃该参数,
# 传了报 400。用日期后缀区分,避免硬编码型号清单(自维护)。
_DATED = re.compile(r"-\d{8}$")


def _accepts_temperature(model: str) -> bool:
    return bool(_DATED.search(model or ""))


def _base() -> str:
    return (os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/")


def _key() -> str:
    return (os.environ.get("ANTHROPIC_API_KEY") or "").strip()


def _model(tier: str) -> str:
    """抽象档位 → 具体 Claude 模型(集中此处·业务/文档不出现型号名)。"""
    flash = os.environ.get("ANTHROPIC_FLASH_MODEL", "").strip() or "claude-haiku-4-5-20251001"
    best = os.environ.get("ANTHROPIC_BEST_MODEL", "").strip() or "claude-sonnet-5"
    return {"flash": flash, "flash_lite": flash, "best": best, "fallback": best}.get(tier, flash)


def _error_kind_status(status: int) -> str:
    if status in (401, 403):
        return "auth"
    if status == 429:
        return "quota"
    if status in (500, 502, 503, 504, 529):
        return "timeout"
    return "provider"


def _messages(
    *,
    system: Optional[str],
    user: str,
    model: str,
    max_tokens: int,
    temperature: float,
    timeout_s: int,
    cache_system: bool,
) -> Tuple[Optional[str], dict, Optional[str]]:
    """低层 Claude 调用 → (text, usage, error_kind)。usage 含缓存 token 明细(计费/AB 用)。"""
    import httpx

    if not _key():
        return None, {}, "auth"
    payload: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user}],
    }
    if _accepts_temperature(model):
        payload["temperature"] = temperature
    if system:
        block = {"type": "text", "text": system}
        if cache_system:
            block["cache_control"] = {"type": "ephemeral"}
        payload["system"] = [block]
    headers = {
        "x-api-key": _key(),
        "anthropic-version": _VERSION,
        "content-type": "application/json",
    }
    try:
        resp = httpx.post(
            f"{_base()}/v1/messages", headers=headers, json=payload, timeout=timeout_s
        )
    except httpx.TimeoutException:
        return None, {}, "timeout"
    except httpx.HTTPError:
        return None, {}, "provider"
    if resp.status_code >= 400:
        return None, {}, _error_kind_status(resp.status_code)
    try:
        body = resp.json()
        text = "".join(
            b.get("text", "") for b in body.get("content", []) if b.get("type") == "text"
        )
        return text.strip(), (body.get("usage") or {}), None
    except Exception:  # noqa: BLE001
        return None, {}, "parse"


def _billed_input(usage: dict) -> int:
    """计费口径的总输入 token(未缓存 + 缓存写 + 缓存读),供观测/成本估算合并成单值。"""
    return (
        int(usage.get("input_tokens", 0) or 0)
        + int(usage.get("cache_creation_input_tokens", 0) or 0)
        + int(usage.get("cache_read_input_tokens", 0) or 0)
    )


def text_to_action(prompt, *, tools, **kw) -> ProviderOutcome:
    """原生 function-calling:Claude tool_use 与 Gemini FC 语义不同,暂不实现 →
    调用方(loop)回落 JSON 协议(text_to_json),行为等价·不炸。"""
    return ProviderOutcome(ok=False, error_kind="unsupported", model=NAME)


def text_to_json(
    prompt: str,
    *,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    response_mime: bool = True,
    max_tokens: int = 1200,
    timeout_s: int = 30,
    max_retries: int = 1,
    system: Optional[str] = None,
    cache_system: bool = True,
) -> ProviderOutcome:
    """结构化 JSON 决策。prompt 组合体走 user;可选 system(稳定前缀)分离并缓存以省 input 价。
    解析失败带回原文(loop 可把散文当回复救援)。无 key/HTTP 错 → 标准 error_kind,不抛。"""
    from services.ocr.layer2_gemini import _parse_json

    model = _model(tier)
    last_raw = ""
    for attempt in range(max_retries + 1):
        text, usage, kind = _messages(
            system=system,
            user=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
            cache_system=cache_system,
        )
        if kind:
            return ProviderOutcome(ok=False, error_kind=kind, model=model)
        if text:
            last_raw = text
            try:
                return ProviderOutcome(
                    ok=True,
                    data=_parse_json(text),
                    model=model,
                    input_tokens=_billed_input(usage),
                    output_tokens=int(usage.get("output_tokens", 0) or 0),
                )
            except Exception:  # noqa: BLE001
                pass
        if attempt < max_retries:
            continue
    return ProviderOutcome(ok=False, error_kind="parse", model=model, raw=last_raw)


def text_to_text(
    prompt: str,
    *,
    system: Optional[str] = None,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.2,
    timeout_s: int = 120,
) -> ProviderOutcome:
    model = _model(tier)
    text, usage, kind = _messages(
        system=system,
        user=prompt,
        model=model,
        max_tokens=4096,
        temperature=temperature,
        timeout_s=timeout_s,
        cache_system=bool(system),
    )
    if kind:
        return ProviderOutcome(ok=False, error_kind=kind, model=model)
    if not text:
        return ProviderOutcome(ok=False, error_kind="parse", model=model)
    return ProviderOutcome(
        ok=True,
        data=text,
        model=model,
        input_tokens=_billed_input(usage),
        output_tokens=int(usage.get("output_tokens", 0) or 0),
    )
