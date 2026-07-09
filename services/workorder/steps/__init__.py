# -*- coding: utf-8 -*-
"""工单流水线各步 handler(任务包 §5)。每步一文件,统一签名 run(ctx) -> StepResult;
纯编排:取料 → 调现有 service → 落库 → 返回。T3 交 intake/sort,T4-T6 交其余四步。"""

from __future__ import annotations

from services.workorder.engine import default_handlers
from services.workorder.steps import classify, compute, intake, package, reconcile, sort

# engine.default_handlers() 只给占位 handler(T2 骨架自测用)。T7 的 CLI 要跑真管线,
# 用真实 handler 覆盖对应步的键——review/archive 不在 RUNNABLE_STEPS 里,engine 本就不
# 会为它们找 handler,这里无需也不许注册(§4:两态是人审/归档,M0 只落状态位)。
_REAL = {
    "intake": intake.run,
    "sort": sort.run,
    "classify": classify.run,
    "reconcile": reconcile.run,
    "compute": compute.run,
    "package": package.run,
}


def real_handlers() -> dict:
    """六步真实 handler 的注册表,供 engine.run_work_order(ctx, handlers=...) 用。"""
    handlers = default_handlers()
    handlers.update(_REAL)
    return handlers
