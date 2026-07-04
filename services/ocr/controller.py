# -*- coding: utf-8 -*-
"""统一 OCR 编排入口:五类任务都经 run() 分发到 handlers,旧入口是它的 facade。

编排职责止于「校验 task + 找 handler + 引擎策略生效域 + 计时」;不吞不改各
handler 的原生错误语义(见 contracts 模块 docstring)。handler 按 task 名
懒加载,避免 facade 模块(entrypoints/bank_recon_v2/...)与本模块的导入环。
"""

from __future__ import annotations

import time
from importlib import import_module

from services.ocr.contracts import OcrRequest, OcrResult
from services.ocr.engine_policy import engine_context
from services.ocr.policy import policy_for

_HANDLER_PKG = "services.ocr.handlers"


def run(req: OcrRequest) -> OcrResult:
    policy_for(req.task)
    handler = import_module(f"{_HANDLER_PKG}.{req.task}")
    t0 = time.monotonic()
    # Controller 只消费调用方传入的套餐上下文,不在这里查 DB;没有上下文时按 none 档回落。
    with engine_context(req.task, plan_code=req.plan_code, is_exempt=req.is_exempt):
        data = handler.handle(req)
    return OcrResult(task=req.task, data=data, elapsed_ms=int((time.monotonic() - t0) * 1000))
