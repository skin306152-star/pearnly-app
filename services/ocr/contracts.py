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
    (invoice: max_pages · gl_ledger: account_code),不往签名里加一次性字段。"""

    task: str
    file_bytes: bytes
    filename: str
    api_key: Optional[str] = None
    tenant_id: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OcrResult:
    task: str
    data: Any
    elapsed_ms: int
