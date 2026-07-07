# -*- coding: utf-8 -*-
"""安全上报端点:接收浏览器 CSP 违规报告,结构化落日志供观察。

安全评估 2026-07-07:CSP report-only/enforce 的违规此前只进用户浏览器 console,服务端收不到,
无法数据驱动地把完整策略升格强制。本端点作 report-uri 目标:只解析关键字段
(违规指令/被挡资源/来源页)记 structured log,**不落库**——无鉴权写库会引入撑爆/注入面。
body 超限直接丢;全局限流兜底防灌;%r 记录防日志注入。恒回 204 不给探测者回信息。
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import Response

logger = logging.getLogger("mr-pilot")
router = APIRouter()

_MAX_BODY = 16 * 1024  # 单条报告上限 · 超限丢弃


def _extract_report(data: object) -> dict | None:
    """兼容两种上报形状:report-uri {"csp-report":{...}} 与 report-to [{...,"body":{...}}]。"""
    if isinstance(data, dict):
        rep = data.get("csp-report")
        return rep if isinstance(rep, dict) else data
    if isinstance(data, list) and data and isinstance(data[0], dict):
        body = data[0].get("body")
        return body if isinstance(body, dict) else data[0]
    return None


@router.post("/api/csp-report")
async def csp_report(request: Request):
    try:
        if int(request.headers.get("content-length") or 0) > _MAX_BODY:
            return Response(status_code=204)
    except ValueError:
        return Response(status_code=204)

    raw = await request.body()
    if len(raw) > _MAX_BODY:
        return Response(status_code=204)
    try:
        rep = _extract_report(json.loads(raw or b"{}"))
    except (ValueError, TypeError):
        rep = None
    if not isinstance(rep, dict):
        return Response(status_code=204)

    def _field(hyphen: str, camel: str) -> str:
        val = rep.get(hyphen)
        if val is None:
            val = rep.get(camel)
        return str(val)[:300] if val is not None else ""

    logger.warning(
        "csp_violation directive=%r blocked=%r doc=%r",
        _field("violated-directive", "effectiveDirective"),
        _field("blocked-uri", "blockedURL"),
        _field("document-uri", "documentURL"),
    )
    return Response(status_code=204)
