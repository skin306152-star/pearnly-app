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

from core import db
from core.route_helpers import _log_op, _require_super_admin
from services.billing.pricing import PDF_TIER1_PRICE_V21
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

# 能力未齐的档(engine_policy.PARTIAL_MODES)不准启用为任何档位(全局/套餐默认/任务覆写):
# 三个口都是「成批切过去」,能力缺口会随档全租户生效。集合当前为空(qwen 2026-08-12 补齐
# document_type 后移出),闸常驻当绊线:新档几乎都是能力先残后齐,写侧不拦,残档一上线就是
# 全租户事故。语义演变:建档时是「只准账号灰度」,2026-08-13 账号灰度机制退役后收紧为全面禁用。
_PARTIAL_MODE_ERROR = "ocr_engine.partial_mode_disabled"

# 账号灰度(overrides_by_account)2026-08-13 退役:写侧明确拒收,不静默丢弃——
# 旧脚本/旧前端还在发这个键时,400 比「保存成功但没生效」诚实。
_RETIRED_ACCOUNT_KEY = "overrides_by_account"
_RETIRED_ACCOUNT_ERROR = "ocr_engine.overrides_by_account_retired"


def _reject_partial_mode(mode: str) -> None:
    if mode in PARTIAL_MODES:
        raise HTTPException(400, detail=f"{_PARTIAL_MODE_ERROR}:{mode}")


@router.get("/api/admin/ocr-engine")
async def get_ocr_engine_policy(request: Request):
    _require_super_admin(request)
    from services.ocr.admin_runtime import snapshot

    row = store.get_setting(SETTING_KEY)
    config = load_config()
    return {
        "policy": config,
        "runtime": snapshot(config),
        "updated_at": (row["updated_at"].isoformat() if row and row.get("updated_at") else None),
        "options": {
            "modes": list(MODES),
            "plan_modes": list(CONCRETE_MODES),
            "partial_modes": sorted(PARTIAL_MODES),
            "tasks": list(OCR_TASKS),
        },
    }


@router.post("/api/admin/ocr-engine")
async def set_ocr_engine_policy(request: Request):
    """body: {mode, defaults_by_plan, overrides_by_task}。校验后落库 + 审计。

    落库 value 只含认识的键:存量配置里的退役键(账号灰度名单)在下一次保存时被自然剥离,
    不需要迁移脚本去改生产 DB。"""
    user = _require_super_admin(request)
    body = await request.json()
    if _RETIRED_ACCOUNT_KEY in body:
        raise HTTPException(400, detail=_RETIRED_ACCOUNT_ERROR)

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
        # 任务级覆写=该 task 全量切档(如 invoice 一钉全站发票都走),与全局同风险面,
        # 同样只准按账号灰度;此前只挡了全局与套餐两处,这是补上的第三个口。
        _reject_partial_mode(v)
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


def _quota_pages_deducted(days: int) -> int:
    """近 N 天走订阅套餐额度抵扣的总页数(credit_transactions 里 usage 且金额为 0 的行 ——
    只有套餐内抵扣这么落账,见 services/billing/charge.py::_charge_with_subscription)。

    成本页拿它标注「额度抵扣 N 页」:这些页扣费 ฿0 但不免费(营收在订阅月费里),
    不标出来 0 就冒充免费。查询失败回 0 —— 标注缺席不该让整块仪表盘白屏。"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(pages), 0) AS pages
                FROM credit_transactions
                WHERE type = 'usage' AND amount_thb = 0 AND pages > 0
                  AND created_at >= NOW() - make_interval(days => %s)
                """,
                (int(days),),
            )
            row = cur.fetchone()
            return int(row["pages"]) if row else 0
    except Exception as e:
        logger.warning("quota_pages_deducted failed: %s", e)
        return 0


@router.get("/api/admin/ocr-engine/costs")
async def ocr_engine_costs(request: Request, days: int = Query(7, ge=1, le=90)):
    """逐入口 × 单据类型的成本与每页成本(ai_usage 归因列)。

    读 ai_usage(逐网关调用,一份多页票会有多行)。这条回答的是「哪个入口贵」,不是「跑了多少张」。
    售价参考线一并下发(前端不再硬编 1.5):定价单源在 pricing.PDF_TIER1_PRICE_V21,
    改价只动一处,柱图参考线与明细提示自动跟上。额度抵扣页数走 credit_transactions
    (ai_usage 只有成本没有扣费,分不出「套餐内 ฿0」)。"""
    _require_super_admin(request)
    costs = get_cost_by_entry_point(days=days)
    costs["price_thb_per_page"] = float(PDF_TIER1_PRICE_V21)
    costs["quota_pages_deducted"] = _quota_pages_deducted(days)
    return costs
