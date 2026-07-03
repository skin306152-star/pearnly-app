# -*- coding: utf-8 -*-
"""OCR 引擎策略超管路由(Earn 后台「OCR 引擎」页)。

读/写 platform_settings["ocr_engine_policy"](写留审计)+ 成本/延迟/触发率指标。
全部 _require_super_admin 守门;普通用户完全无感。策略消费方在
services/ocr/engine_policy(fail-safe direct35,这里写坏值也停不了 OCR)。

覆盖:
  GET  /api/admin/ocr-engine          · 读当前策略(含默认值合并)+ 可选项
  POST /api/admin/ocr-engine          · 写策略(校验 + 审计)
  GET  /api/admin/ocr-engine/metrics  · 成本/每张成本/延迟/模型占比/L3 触发率/失败率
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request

from core.route_helpers import _log_op, _require_super_admin
from services.cost.store import get_ocr_engine_metrics
from services.ocr.contracts import OCR_TASKS
from services.ocr.engine_policy import DEFAULT_CONFIG, MODES, SETTING_KEY, load_config
from services.platform_settings import store

logger = logging.getLogger("mr-pilot")

router = APIRouter()

# defaults_by_plan 只许落到具体档(auto 进套餐表会循环,resolve 侧也会兜回 direct35)
_CONCRETE_MODES = ("direct35", "economy")


@router.get("/api/admin/ocr-engine")
async def get_ocr_engine_policy(request: Request):
    _require_super_admin(request)
    row = store.get_setting(SETTING_KEY)
    return {
        "policy": load_config(),
        "updated_at": (row["updated_at"].isoformat() if row and row.get("updated_at") else None),
        "options": {
            "modes": list(MODES),
            "plan_modes": list(_CONCRETE_MODES),
            "tasks": list(OCR_TASKS),
        },
    }


@router.post("/api/admin/ocr-engine")
async def set_ocr_engine_policy(request: Request):
    """body: {mode, defaults_by_plan, overrides_by_task}。整体校验后落库 + 审计。"""
    user = _require_super_admin(request)
    body = await request.json()

    mode = (body.get("mode") or "").strip()
    if mode not in MODES:
        raise HTTPException(400, detail="ocr_engine.bad_mode")

    plans = body.get("defaults_by_plan") or {}
    if not isinstance(plans, dict):
        raise HTTPException(400, detail="ocr_engine.bad_defaults_by_plan")
    defaults_by_plan = dict(DEFAULT_CONFIG["defaults_by_plan"])
    for k in defaults_by_plan:
        v = (plans.get(k) or defaults_by_plan[k]).strip()
        if v not in _CONCRETE_MODES:
            raise HTTPException(400, detail=f"ocr_engine.bad_plan_mode:{k}")
        defaults_by_plan[k] = v

    tasks = body.get("overrides_by_task") or {}
    if not isinstance(tasks, dict):
        raise HTTPException(400, detail="ocr_engine.bad_overrides_by_task")
    overrides_by_task = {}
    for k, v in tasks.items():
        if k not in OCR_TASKS:
            raise HTTPException(400, detail=f"ocr_engine.bad_task:{k}")
        v = (v or "").strip()
        if not v:
            continue  # 空 = 跟全局,不落库
        if v not in MODES:
            raise HTTPException(400, detail=f"ocr_engine.bad_task_mode:{k}")
        overrides_by_task[k] = v

    value = {
        "mode": mode,
        "defaults_by_plan": defaults_by_plan,
        "overrides_by_task": overrides_by_task,
    }
    store.set_setting(SETTING_KEY, value, True, by=str(user["id"]))
    _log_op(
        request,
        user,
        action="ocr_engine_policy_update",
        target_type="platform_setting",
        target_id=SETTING_KEY,
        details=value,
    )
    return {"ok": True, "policy": load_config()}


@router.get("/api/admin/ocr-engine/metrics")
async def ocr_engine_metrics(request: Request, days: int = Query(7, ge=1, le=90)):
    _require_super_admin(request)
    return get_ocr_engine_metrics(days=days)
