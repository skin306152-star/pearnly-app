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
    """记一次调用的工程元信息(无原文/prompt/key/raw response)+ 落库 ai_usage。"""
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
    _record_usage(result, tenant_id=tenant_id, user_id=user_id, trace_id=trace_id)


def _record_usage(result, *, tenant_id, user_id, trace_id) -> None:
    """转发到 ai_usage 落库(懒 import 防循环)。store 层已全量吞异常,这里再兜一层——
    成本记账绝不能是打断 AI 调用主路径的理由(如 ai_usage_store 导入失败)。

    归因(入口/单据/页数)在这里读而不在 transport 读:log_call 有两个上游(transport 4 形态
    + router.run_task),读在汇合点才两条路都盖到。"""
    try:
        from services.cost.ai_usage_store import log_ai_usage
        from services.cost.usage_context import current as usage_current
        from services.cost.usage_context import restore_pages, take_pages

        usage = usage_current() or {}
        # 页数只记在本请求的第一行:一份 N 页票会落多行(逐页/逐层各一次调用),
        # 行行都记 N 的话 SUM(pages) 按调用次数翻倍,每页成本被稀释成假的便宜。
        # take 在写库前、写库失败还回(restore):写入成功才算消费,DB 抖动不丢分母。
        pages = take_pages()
        written = log_ai_usage(
            tenant_id=tenant_id,
            user_id=user_id,
            task=result.task,
            provider=result.provider,
            model=result.model,
            status="ok" if result.ok else "error",
            error_kind=result.error_kind,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_thb=result.cost_thb,
            trace_id=trace_id,
            entry_point=usage.get("entry_point"),
            doc_type=usage.get("doc_type"),
            pages=pages,
        )
        if not written:
            restore_pages(pages)
    except Exception as e:
        logger.warning("ai_usage record skipped: %s", e)
