# -*- coding: utf-8 -*-
"""AI Gateway 统一入口 run_task。

业务代码只请求 task + payload,Gateway 选 provider、计时、估成本、记元信息日志,返回 AiResult。
确定性边界(docs/line-platform/03 §5):Gateway 绝不写采购单/过账/撤销/冲销,不决定状态机,不算
金额/VAT。它只返回结构化数据;金额/状态/审计仍由调用方的确定性代码处理。
"""

from __future__ import annotations

import time
from typing import Any, Optional

from services.ai_gateway import costing
from services.ai_gateway import logging as ai_log
from services.ai_gateway import tasks


def _default_provider():
    from services.ai_gateway.providers import gemini

    return gemini


def run_task(
    task: str,
    *,
    prompt: str,
    text: str,
    api_key=None,
    timeout_s: Optional[int] = None,
    tenant_id=None,
    user_id=None,
    trace_id=None,
    provider: Any = None,
) -> tasks.AiResult:
    """跑一个 AI task → AiResult(ok/data/error_kind + 成本元信息)。

    provider=None → 默认 Gemini 适配器;测试可注入 fake provider。timeout_s 不传 → 用 task 默认。
    任何失败都收敛进 AiResult(ok=False + error_kind),不抛给业务层(业务层据此走 fallback/review)。
    """
    sp = tasks.spec(task)
    timeout = int(timeout_s if timeout_s is not None else sp["timeout_s"])
    prov = provider or _default_provider()
    name = getattr(prov, "NAME", getattr(prov, "name", "")) or "unknown"

    start = time.time()
    outcome = prov.generate_json(
        prompt=prompt,
        text=text,
        api_key=api_key,
        model_tier=sp["model_tier"],
        timeout_s=timeout,
        max_retries=sp["max_retries"],
    )
    latency_ms = int((time.time() - start) * 1000)

    result = tasks.AiResult(
        ok=bool(outcome.ok),
        task=task,
        schema_version=sp["schema_version"],
        data=outcome.data,
        provider=name,
        model=outcome.model,
        error_kind=outcome.error_kind,
        latency_ms=latency_ms,
        input_tokens=outcome.input_tokens,
        output_tokens=outcome.output_tokens,
        cost_thb=costing.estimate_thb(outcome.model, outcome.input_tokens, outcome.output_tokens),
        fallback_used=False,
    )
    ai_log.log_call(result, text=text, tenant_id=tenant_id, user_id=user_id, trace_id=trace_id)
    return result
