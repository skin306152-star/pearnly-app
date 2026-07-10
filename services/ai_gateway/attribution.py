# -*- coding: utf-8 -*-
"""调用归因上下文:让上层业务把一段 LLM 调用的成本归到自己的 task/租户名下。

问题:OCR 管线内部按内部标签打点(task=ocr.image_json / ocr.layer2,tenant 为空),成本
台账 ai_usage 里看不出这批 OCR 是谁烧的。工单跑批要求「classify 的 OCR 成本落
task=workorder_classify + 本租户」,但 OCR 管线深处不该认识工单。

解法:一个请求/线程级归因上下文。业务在跑 OCR 前 set_attribution(task, tenant_id, ...),
transport 落点(_observe)在业务未逐调用显式传 task/tenant 时优先采用归因值。确定性边界不变
——只改「这条成本记给谁」的标签,不改模型/路由/返回数据。

线程注意:contextvars 是线程本地,ThreadPoolExecutor 子线程起始为空上下文。并发跑 OCR 时
必须在 worker 函数体内 set_attribution(而非仅主线程设置),否则子线程里的 transport 读不到。
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Optional

_ATTR: ContextVar[Optional[dict]] = ContextVar("ai_attribution", default=None)


def set_attribution(
    task: str,
    *,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Token:
    """设归因(task 必填 + 可选 tenant/user/trace)。返回 token,调用方 finally 里 reset。"""
    return _ATTR.set(
        {"task": task, "tenant_id": tenant_id, "user_id": user_id, "trace_id": trace_id}
    )


def reset_attribution(token: Token) -> None:
    _ATTR.reset(token)


def current() -> Optional[dict]:
    return _ATTR.get()
