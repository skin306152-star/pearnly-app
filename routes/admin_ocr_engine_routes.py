# -*- coding: utf-8 -*-
"""OCR 引擎策略超管路由(Earn 后台「OCR 引擎」页)。

读/写 platform_settings["ocr_engine_policy"](写留审计)+ 成本/延迟/触发率指标。
全部 _require_super_admin 守门;普通用户完全无感。策略消费方在
services/ocr/engine_policy(fail-safe direct35,这里写坏值也停不了 OCR)。

覆盖:
  GET  /api/admin/ocr-engine          · 读当前策略(含默认值合并)+ 可选项
  POST /api/admin/ocr-engine          · 写策略(校验 + 审计)
  GET  /api/admin/ocr-engine/costs    · 逐入口 × 单据的成本/每页成本/p50 延迟
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request

from core.route_helpers import _log_op, _require_super_admin
from services.cost.ai_usage_store import get_cost_by_entry_point
from services.ocr.contracts import OCR_TASKS
from services.ocr.engine_policy import (
    CONCRETE_MODES,
    DEFAULT_CONFIG,
    MODES,
    PARTIAL_MODES,
    SETTING_KEY,
    load_config,
)
from services.platform_settings import store

logger = logging.getLogger("mr-pilot")

router = APIRouter()

# defaults_by_plan 只许落到具体档(auto 进套餐表会循环,resolve 侧也会兜回 direct35)

# 能力未齐的档(engine_policy.PARTIAL_MODES)只准按账号灰度:全局档与套餐默认档是「整机切
# 过去」,而这些档还缺 document_type,切了会让贷记单方向复核静默失效。账号覆写不受限 ——
# 灰度本来就是拿少数账号对比读数,风险有边界。
_PARTIAL_MODE_ERROR = "ocr_engine.partial_mode_account_only"


def _reject_partial_mode(mode: str) -> None:
    if mode in PARTIAL_MODES:
        raise HTTPException(400, detail=f"{_PARTIAL_MODE_ERROR}:{mode}")


@router.get("/api/admin/ocr-engine")
async def get_ocr_engine_policy(request: Request):
    _require_super_admin(request)
    row = store.get_setting(SETTING_KEY)
    return {
        "policy": load_config(),
        "updated_at": (row["updated_at"].isoformat() if row and row.get("updated_at") else None),
        "options": {
            "modes": list(MODES),
            "plan_modes": list(CONCRETE_MODES),
            "partial_modes": sorted(PARTIAL_MODES),
            "tasks": list(OCR_TASKS),
        },
    }


def _clean_overrides_by_account(raw, current: dict) -> dict:
    """账号灰度名单校验(邮箱统一小写)。键缺席 = 保持库里现状 —— 旧版前端不发这个键,
    不保持的话每次在这页点一次保存,都会把按人开的新引擎悄悄关掉。"""
    if raw is None:
        return dict(current or {})
    if not isinstance(raw, dict):
        raise HTTPException(400, detail="ocr_engine.bad_overrides_by_account")
    out = {}
    for k, v in raw.items():
        email = (k or "").strip().lower()
        mode = (v or "").strip()
        if not email:
            continue
        if "@" not in email:
            raise HTTPException(400, detail=f"ocr_engine.bad_account:{k}")
        if not mode:
            continue  # 空 = 跟全局,不落库
        if mode not in MODES:
            raise HTTPException(400, detail=f"ocr_engine.bad_account_mode:{email}")
        out[email] = mode
    return out


@router.post("/api/admin/ocr-engine")
async def set_ocr_engine_policy(request: Request):
    """body: {mode, defaults_by_plan, overrides_by_task, overrides_by_account}。校验后落库 + 审计。"""
    user = _require_super_admin(request)
    body = await request.json()

    mode = (body.get("mode") or "").strip()
    if mode not in MODES:
        raise HTTPException(400, detail="ocr_engine.bad_mode")
    _reject_partial_mode(mode)

    plans = body.get("defaults_by_plan") or {}
    if not isinstance(plans, dict):
        raise HTTPException(400, detail="ocr_engine.bad_defaults_by_plan")
    defaults_by_plan = dict(DEFAULT_CONFIG["defaults_by_plan"])
    for k in defaults_by_plan:
        v = (plans.get(k) or defaults_by_plan[k]).strip()
        if v not in CONCRETE_MODES:
            raise HTTPException(400, detail=f"ocr_engine.bad_plan_mode:{k}")
        _reject_partial_mode(v)
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
        "overrides_by_account": _clean_overrides_by_account(
            body.get("overrides_by_account"), load_config().get("overrides_by_account")
        ),
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


@router.get("/api/admin/ocr-engine/costs")
async def ocr_engine_costs(request: Request, days: int = Query(7, ge=1, le=90)):
    """逐入口 × 单据类型的成本与每页成本(ai_usage 归因列)。

    读 ai_usage(逐网关调用,一份多页票会有多行)。这条回答的是「哪个入口贵」,不是「跑了多少张」。"""
    _require_super_admin(request)
    return get_cost_by_entry_point(days=days)
