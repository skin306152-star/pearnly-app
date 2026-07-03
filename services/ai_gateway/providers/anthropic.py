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
from typing import Optional, Tuple

from services.ai_gateway.tasks import ProviderOutcome

NAME = "anthropic"
_VERSION = "2023-06-01"
# temperature 在较新代际(Sonnet 5 / Opus 4.7+ / Fable 5 …)已废弃,传了报 400;老代际(Haiku 4.5 等)
# 仍收。规则按模型代际走,与命名形状无关 → 不猜:发一次,若因 temperature 被拒就记下该模型、去掉重发。
# 运行时自适配,零型号清单维护;命中后进程内记忆,不重复试错。
_NO_TEMP: set[str] = set()


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
    """低层 Claude 调用 → (text, usage, error_kind)。usage 含缓存 token 明细(计费/AB 用)。
    temperature 被某代际拒(400)时:记下该模型、去掉 temperature 重发一次(见 _NO_TEMP)。"""
    import httpx

    key = _key()
    if not key:
        return None, {}, "auth"
    headers = {"x-api-key": key, "anthropic-version": _VERSION, "content-type": "application/json"}
    payload: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user}],
    }
    if model not in _NO_TEMP:  # 已知拒 temperature 的代际直接不带,省一次试错
        payload["temperature"] = temperature
    if system:
        block = {"type": "text", "text": system}
        if cache_system:
            block["cache_control"] = {"type": "ephemeral"}
        payload["system"] = [block]

    for _ in range(2):  # 首发若因 temperature 被拒 → 记忆该模型 + 去掉重发一次
        url = f"{_base()}/v1/messages"
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=timeout_s)
        except httpx.TimeoutException:
            return None, {}, "timeout"
        except httpx.HTTPError:
            return None, {}, "provider"
        if (
            resp.status_code == 400
            and "temperature" in payload
            and "temperature" in resp.text.lower()
        ):
            _NO_TEMP.add(model)
            payload.pop("temperature")
            continue
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
    return None, {}, "provider"  # 理论不可达(第二次已不带 temperature,必走到返回)


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
    for _ in range(max_retries + 1):
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
                pass  # 坏 JSON → 继续下一次重试(循环自然推进),重试用尽后落 parse
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
