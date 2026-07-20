# -*- coding: utf-8 -*-
"""OCR 统一编排契约:controller 与 handlers 之间的稳定接口。

行为不变约定:OcrResult.data 保持各 handler 的原生返回形状
(invoice=PipelineResult,其余=dict),旧入口 facade 原样透传给调用方;
错误语义也不归一(invoice 抛 ValueError、id_card 抛 IdCardExtractError、
对账三件返回 ok=False dict),归一留待所有调用方迁到 controller 之后。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

OCR_TASKS: Tuple[str, ...] = ("invoice", "id_card", "bank_statement", "gl_ledger", "vat_report")


@dataclass(frozen=True)
class OcrRequest:
    """一次 OCR 任务的全部输入。options 装 task 专属参数
    (invoice: max_pages · gl_ledger: account_code),不往签名里加一次性字段。

    task 与 policy_task 是两个正交概念:task 定 handler 路由(走哪个 handlers/*.py),
    policy_task 定引擎策略档的生效域(overrides_by_task/资费档按它解析)。银行窄读复用发票
    handler(task=invoice)却要按银行档解析(policy_task=bank_statement),两者才拆开。
    policy_task=None → 跟 task(绝大多数入口两者同值,不必显式传)。"""

    task: str
    file_bytes: bytes
    filename: str
    policy_task: Optional[str] = None
    api_key: Optional[str] = None
    tenant_id: Optional[str] = None
    plan_code: Optional[str] = None
    is_exempt: bool = False
    user_type: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OcrResult:
    task: str
    data: Any
    elapsed_ms: int
