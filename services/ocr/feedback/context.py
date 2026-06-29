# -*- coding: utf-8 -*-
"""OCR 请求级上下文(user/tenant),给 L2 few-shot 注入按租户取例。

管线是无上下文的纯 OCR,不往深层签名穿 user/tenant。用 contextvar 在请求入口设、在 L2 拼
prompt 处读 —— web 上传/LINE 单图为同上下文直调,可读到;多页 PDF 的线程池工作线程读不到,
退化为无 few-shot(安全)。"""

import contextvars
from contextlib import contextmanager
from typing import Optional

_ctx: contextvars.ContextVar[Optional[dict]] = contextvars.ContextVar(
    "ocr_request_ctx", default=None
)


@contextmanager
def ocr_request_context(user_id: Optional[str], tenant_id: Optional[str]):
    token = _ctx.set({"user_id": user_id, "tenant_id": tenant_id})
    try:
        yield
    finally:
        _ctx.reset(token)


def current() -> Optional[dict]:
    return _ctx.get()
