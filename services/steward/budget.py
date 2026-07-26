# -*- coding: utf-8 -*-
"""管家模型调用成本硬封顶(B3)—— 单任务与单会话两级上限,超限即停。

钱的口径与全站一致:THB · Decimal(services/billing/charge.py 同款 _Dec 纪律),成本数字
本身仍由 ai_gateway.costing 按实际模型单价算(网关照旧落 ai_usage 台账,这里不重复记账,
只做封顶判据的台账 steward_cost_entries —— ai_usage 的写入是 fire-and-forget 允许丢行,
拿它当封顶判据会漏计)。

并发正确性(两个任务各自没超但合计超也要拦)靠"预留-结算"两段式:
  reserve  锁本会话行(steward_sessions FOR UPDATE 串行化同会话的并发预留)→ 汇总已花
           (含别人在飞未结算的预留)→ 超限拒;没超先按预留额记一行占坑;
  settle   调用回来后把占坑行改成真实成本。
在飞预留计入合计,并发窗口内第二路看得见第一路 —— check-then-spend 的赛道被锁+占坑封死。
进程死在 reserve 与 settle 之间 → 占坑额永久计入(偏保守:宁可少烧,封顶不放水)。

封顶判据自身的基础设施故障(建表/连接失败)走 fail-open + 告警日志:与 charge.py
「记账不连坐主路径」同一取舍 —— 封顶是防烧穿的保险丝,不该是全功能停摆的单点。
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger(__name__)

ERR_TASK = "steward.budget_task_exceeded"
ERR_SESSION = "steward.budget_session_exceeded"

# 默认上限(THB)。planner 单次调用 <฿0.1,任务 ฿1/会话 ฿5 够正常用、烧不穿。
_DEFAULT_TASK_CAP = "1"
_DEFAULT_SESSION_CAP = "5"
# 单次调用的预留额:占坑用,结算时改成真实成本。必须小于两级上限,否则一次都批不出去。
_DEFAULT_CALL_RESERVE = "0.1"

_TABLE = """
CREATE TABLE IF NOT EXISTS steward_cost_entries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    session_id uuid NOT NULL,
    task_id uuid,
    cost_thb numeric(12, 6) NOT NULL DEFAULT 0,
    settled boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
)
"""

_INDEX = (
    "CREATE INDEX IF NOT EXISTS ix_steward_cost_entries_session "
    "ON steward_cost_entries (tenant_id, session_id)"
)

_ensured = False


def ensure_tables() -> None:
    """幂等建台账 + tenant RLS(alembic 0090 留档,prod 靠首用自愈 —— 照 store 先例)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_INDEX)
        apply_tenant_rls(cur, "steward_cost_entries")


def ensure_once() -> None:
    global _ensured
    if _ensured:
        return
    ensure_tables()
    _ensured = True


def _env_decimal(name: str, default: str) -> Decimal:
    raw = os.environ.get(name, "") or default
    try:
        return Decimal(raw)
    except InvalidOperation:
        return Decimal(default)


def task_cap_thb() -> Optional[Decimal]:
    """单任务上限(env STEWARD_TASK_COST_CAP_THB)。≤0 = 该级封顶关闭。"""
    cap = _env_decimal("STEWARD_TASK_COST_CAP_THB", _DEFAULT_TASK_CAP)
    return cap if cap > 0 else None


def session_cap_thb() -> Optional[Decimal]:
    """单会话上限(env STEWARD_SESSION_COST_CAP_THB)。≤0 = 该级封顶关闭。"""
    cap = _env_decimal("STEWARD_SESSION_COST_CAP_THB", _DEFAULT_SESSION_CAP)
    return cap if cap > 0 else None


def call_reserve_thb() -> Decimal:
    """单次调用预留额(env STEWARD_CALL_COST_RESERVE_THB)。负数归零(零预留只削弱并发
    封口、不放开封顶 —— 已花超限照拦)。"""
    return max(Decimal("0"), _env_decimal("STEWARD_CALL_COST_RESERVE_THB", _DEFAULT_CALL_RESERVE))


def decide(
    *,
    session_spent: Decimal,
    task_spent: Decimal,
    estimate: Decimal,
    session_cap: Optional[Decimal],
    task_cap: Optional[Decimal],
) -> Optional[str]:
    """封顶判据(纯函数)。含预留额判:已花 + 这次的预留会破线就不放行,上限绝不被越过。
    任务级先判(口径更窄,报因更准);None = 放行。"""
    if task_cap is not None and task_spent + estimate > task_cap:
        return ERR_TASK
    if session_cap is not None and session_spent + estimate > session_cap:
        return ERR_SESSION
    return None


def reserve(*, tenant_id: str, session_id: str, task_id: Optional[str] = None) -> dict:
    """一次模型调用的预留闸。放行 → {allowed: True, entry_id}(调用后必须 settle);
    超限 → {allowed: False, code, cap_thb, spent_thb}(金额是两位小数字符串,直接进响应)。
    """
    estimate = call_reserve_thb()
    session_cap, task_cap = session_cap_thb(), task_cap_thb()
    if session_cap is None and task_cap is None:
        return {"allowed": True, "entry_id": None}
    try:
        from core import db

        ensure_once()
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "SELECT id FROM steward_sessions WHERE tenant_id = %s AND id = %s FOR UPDATE",
                (tenant_id, session_id),
            )
            cur.fetchone()
            cur.execute(
                "SELECT COALESCE(SUM(cost_thb), 0) AS session_spent, "
                "COALESCE(SUM(cost_thb) FILTER (WHERE task_id = %s), 0) AS task_spent "
                "FROM steward_cost_entries WHERE tenant_id = %s AND session_id = %s",
                (task_id, tenant_id, session_id),
            )
            row = cur.fetchone() or {}
            session_spent = Decimal(str(row.get("session_spent") or 0))
            task_spent = Decimal(str(row.get("task_spent") or 0))
            code = decide(
                session_spent=session_spent,
                task_spent=task_spent,
                estimate=estimate,
                session_cap=session_cap,
                task_cap=task_cap,
            )
            if code:
                cap = task_cap if code == ERR_TASK else session_cap
                spent = task_spent if code == ERR_TASK else session_spent
                return {
                    "allowed": False,
                    "code": code,
                    "cap_thb": _display(cap),
                    "spent_thb": _display(spent),
                }
            cur.execute(
                "INSERT INTO steward_cost_entries (tenant_id, session_id, task_id, cost_thb) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (tenant_id, session_id, task_id, estimate),
            )
            return {"allowed": True, "entry_id": str(cur.fetchone()["id"])}
    except Exception:  # noqa: BLE001 — 封顶基础设施故障不停全功能(fail-open · 顶注取舍)
        logger.warning("[steward.budget] reserve failed; allowing call", exc_info=True)
        return {"allowed": True, "entry_id": None}


def settle(*, tenant_id: str, entry_id: Optional[str], cost_thb=None) -> None:
    """把占坑行结算成真实成本。cost_thb=None(调用炸了拿不到成本)→ 保留预留额当最终值
    (保守多计,封顶不放水)。失败只告警 —— 结算不连坐已完成的调用。"""
    if not entry_id:
        return
    try:
        from core import db

        actual = None if cost_thb is None else max(Decimal("0"), Decimal(str(cost_thb)))
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE steward_cost_entries "
                "SET settled = true, cost_thb = COALESCE(%s, cost_thb) "
                "WHERE tenant_id = %s AND id = %s",
                (actual, tenant_id, entry_id),
            )
    except Exception:  # noqa: BLE001
        logger.warning("[steward.budget] settle failed entry=%s", entry_id, exc_info=True)


def _display(value: Optional[Decimal]) -> str:
    return str((value or Decimal("0")).quantize(Decimal("0.01")))
