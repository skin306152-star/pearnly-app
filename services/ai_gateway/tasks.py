# -*- coding: utf-8 -*-
"""AI Gateway 契约:task 枚举/风险/默认超时/schema 版本 + 结果类型 + 标准 error_kind。

task 只对外暴露「要做什么」,不暴露供应商。model_tier 是抽象档位(flash/flash_lite/best/
fallback),由 provider 解析成具体模型 —— 业务与文档都不出现具体模型名。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# 标准错误类目(provider 把各家原始异常收敛到这 5 类;业务层据此走 fallback/review,不包装成功)。
ERROR_KINDS = ("auth", "quota", "timeout", "parse", "provider")

# task → 规格。risk 仅文档/观测用;model_tier 由 provider 映射具体模型(默认行为与现状一致)。
TASKS: dict[str, dict] = {
    "line_text_understand": {
        "risk": "medium",
        "timeout_s": 18,
        "max_retries": 1,
        "model_tier": "flash",
        "schema_version": "1",
    },
    "expense_category_choose": {
        "risk": "low",
        "timeout_s": 12,
        "max_retries": 1,
        "model_tier": "flash",
        "schema_version": "1",
    },
}


def spec(task: str) -> dict:
    """取 task 规格;未知 task → KeyError(调用方契约错误,早暴露)。"""
    try:
        return TASKS[task]
    except KeyError:
        raise KeyError(f"ai_gateway: unknown task {task!r}") from None


@dataclass
class ProviderOutcome:
    """provider 调用结果(内部)。失败时 error_kind ∈ ERROR_KINDS,data 为 None。"""

    ok: bool
    data: Any = None
    error_kind: Optional[str] = None
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class AiResult:
    """Gateway 对业务层的统一结果。业务层只读 ok/data/error_kind 与成本元信息;
    provider/model 仅内部日志与离线报告可见,绝不进用户可见回复。"""

    ok: bool
    task: str
    schema_version: str
    data: Any = None
    provider: str = ""
    model: str = ""
    error_kind: Optional[str] = None
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_thb: float = 0.0
    fallback_used: bool = False
