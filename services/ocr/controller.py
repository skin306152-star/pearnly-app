# -*- coding: utf-8 -*-
"""统一 OCR 编排入口:五类任务都经 run() 分发到 handlers,旧入口是它的 facade。

编排职责止于「校验 task + 找 handler + 计时」;不吞不改各 handler 的
原生错误语义(见 contracts 模块 docstring)。handler 按 task 名懒加载,
避免 facade 模块(entrypoints/bank_recon_v2/...)与本模块的导入环。
"""

from __future__ import annotations

import time
from importlib import import_module

from services.ocr.contracts import OcrRequest, OcrResult
from services.ocr.policy import policy_for

_HANDLER_PKG = "services.ocr.handlers"


def run(req: OcrRequest) -> OcrResult:
    policy_for(req.task)
    handler = import_module(f"{_HANDLER_PKG}.{req.task}")
    t0 = time.monotonic()
    data = handler.handle(req)
    return OcrResult(task=req.task, data=data, elapsed_ms=int((time.monotonic() - t0) * 1000))
