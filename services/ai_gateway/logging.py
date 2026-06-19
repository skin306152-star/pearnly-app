# -*- coding: utf-8 -*-
"""AI Gateway 调用日志(轻量·只记工程元信息)。

隐私红线:绝不记 LINE 原文 / prompt 原文 / API key / 供应商 raw response。只记 task/provider/
model/状态/error_kind/延迟/token/成本/payload_hash。payload 仅留 hash 供关联,不可反推原文。
"""

from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger("ai_gateway")


def payload_hash(text) -> str:
    """输入文本的短 hash(关联用·不存原文·不可反推)。"""
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


def log_call(result, *, text=None, tenant_id=None, user_id=None, trace_id=None) -> None:
    """记一次调用的工程元信息(无原文/prompt/key/raw response)。"""
    logger.info(
        "ai_call task=%s schema=%s provider=%s model=%s status=%s error_kind=%s latency_ms=%s "
        "in_tok=%s out_tok=%s cost_thb=%.6f payload_hash=%s tenant=%s user=%s trace=%s",
        result.task,
        result.schema_version,
        result.provider,
        result.model,
        "ok" if result.ok else "error",
        result.error_kind or "-",
        result.latency_ms,
        result.input_tokens,
        result.output_tokens,
        result.cost_thb,
        payload_hash(text),
        tenant_id or "-",
        user_id or "-",
        trace_id or "-",
    )
