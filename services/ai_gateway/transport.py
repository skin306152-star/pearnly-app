# -*- coding: utf-8 -*-
"""网关统一传输入口(4 形态)。全产品 OCR/VAT/银行/知识的 LLM 调用都经此。

按 OCR_LLM_BACKEND 选 provider(aistudio 默认 / vertex / selfhost),统一计时、估成本、记
隐私安全的元信息日志。返回 ProviderOutcome(ok/data/error_kind + token/model)。
确定性边界不变(docs/line-platform/03 §5):只返回结构化数据,绝不写库/过账/算钱。
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

from services.ai_gateway import backends, costing
from services.ai_gateway import logging as ai_log
from services.ai_gateway.tasks import AiResult, ProviderOutcome


def _observe(
    task: str, outcome: ProviderOutcome, latency_ms: int, *, provider, tenant_id, user_id, trace_id
):
    """复用 gateway 日志/计费口径(无原文/key/raw response)。"""
    result = AiResult(
        ok=bool(outcome.ok),
        task=task,
        schema_version="t1",
        data=None,  # 日志不带 data
        provider=provider,
        model=outcome.model,
        error_kind=outcome.error_kind,
        latency_ms=latency_ms,
        input_tokens=outcome.input_tokens,
        output_tokens=outcome.output_tokens,
        cost_thb=costing.estimate_thb(outcome.model, outcome.input_tokens, outcome.output_tokens),
    )
    ai_log.log_call(result, text=None, tenant_id=tenant_id, user_id=user_id, trace_id=trace_id)


def _run(
    method: str, args: tuple, kwargs: dict, *, task, backend=None, tenant_id, user_id, trace_id
) -> ProviderOutcome:
    # backend 优先级:显式传入(如 Agent 大脑) > 请求级覆盖(engine_policy 按档钉,如 economy→
    # aistudio) > 全局 OCR_LLM_BACKEND。所有形态(含 OCR multimodal)都经此,故三条选档路
    # (全局/套餐 auto/任务覆写)只要解析出同一档,后端就一致,不会上下游脱节。
    effective = (
        (backend or backends.override_backend() or backends.active_backend()).strip().lower()
    )
    prov = backends.get_provider(effective)
    fn = getattr(prov, method)
    start = time.time()
    outcome = fn(*args, **kwargs)
    latency_ms = int((time.time() - start) * 1000)
    if not isinstance(outcome, ProviderOutcome):  # 防御:provider 契约错
        outcome = ProviderOutcome(ok=False, error_kind="provider")
    _observe(
        task,
        outcome,
        latency_ms,
        provider=effective,
        tenant_id=tenant_id,
        user_id=user_id,
        trace_id=trace_id,
    )
    return outcome


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
    task: str = "ocr.text_json",
    backend: Optional[str] = None,
    tenant_id=None,
    user_id=None,
    trace_id=None,
) -> ProviderOutcome:
    return _run(
        "text_to_json",
        (prompt,),
        dict(
            tier=tier,
            api_key=api_key,
            temperature=temperature,
            response_mime=response_mime,
            max_tokens=max_tokens,
            timeout_s=timeout_s,
            max_retries=max_retries,
        ),
        task=task,
        backend=backend,
        tenant_id=tenant_id,
        user_id=user_id,
        trace_id=trace_id,
    )


def text_to_action(
    prompt: str,
    *,
    tools: List[dict],
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1200,
    timeout_s: int = 18,
    max_retries: int = 1,
    task: str = "agent_loop_fc",
    backend: Optional[str] = None,
    tenant_id=None,
    user_id=None,
    trace_id=None,
) -> ProviderOutcome:
    """原生 function-calling 决策:声明 tools,provider 结构化返回动作
    data={"kind":"tool","tool","args"} 或 {"kind":"reply","message"}。
    后端未实现 → error_kind="unsupported"(调用方回落 text_to_json 协议)。"""
    return _run(
        "text_to_action",
        (prompt,),
        dict(
            tools=tools,
            tier=tier,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_s=timeout_s,
            max_retries=max_retries,
        ),
        task=task,
        backend=backend,
        tenant_id=tenant_id,
        user_id=user_id,
        trace_id=trace_id,
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
    task: str = "ocr.image_json",
    tenant_id=None,
    user_id=None,
    trace_id=None,
) -> ProviderOutcome:
    return _run(
        "multimodal_to_json",
        (prompt, images),
        dict(
            tier=tier,
            api_key=api_key,
            temperature=temperature,
            response_mime=response_mime,
            max_tokens=max_tokens,
            timeout_s=timeout_s,
            max_retries=max_retries,
        ),
        task=task,
        tenant_id=tenant_id,
        user_id=user_id,
        trace_id=trace_id,
    )


def text_to_text(
    prompt: str,
    *,
    system: Optional[str] = None,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.2,
    timeout_s: int = 120,
    task: str = "ocr.text",
    tenant_id=None,
    user_id=None,
    trace_id=None,
) -> ProviderOutcome:
    return _run(
        "text_to_text",
        (prompt,),
        dict(
            system=system, tier=tier, api_key=api_key, temperature=temperature, timeout_s=timeout_s
        ),
        task=task,
        tenant_id=tenant_id,
        user_id=user_id,
        trace_id=trace_id,
    )


def embed(
    texts: List[str],
    *,
    is_query: bool = False,
    api_key: Optional[str] = None,
    dim: int = 768,
    timeout_s: int = 120,
    task: str = "ocr.embed",
    tenant_id=None,
    user_id=None,
    trace_id=None,
) -> ProviderOutcome:
    return _run(
        "embed",
        (texts,),
        dict(is_query=is_query, api_key=api_key, dim=dim, timeout_s=timeout_s),
        task=task,
        tenant_id=tenant_id,
        user_id=user_id,
        trace_id=trace_id,
    )
