# -*- coding: utf-8 -*-
"""管家模型调用成本硬封顶(B3)—— 单任务/单会话/租户日额三级上限,超限即停。

钱的口径与全站一致:THB · Decimal(services/billing/charge.py 同款 _Dec 纪律),成本数字
本身仍由 ai_gateway.costing 按实际模型单价算(网关照旧落 ai_usage 台账,这里不重复记账,
只做封顶判据的台账 steward_cost_entries —— ai_usage 的写入是 fire-and-forget 允许丢行,
拿它当封顶判据会漏计)。

三级判据:任务 ฿1 / 会话 ฿5 / 租户 24 小时 ฿50(各自 env 可配,≤0 关闭该级)。
租户级是失控用户的顶:前两级都以 session_id 为界,「烧满就开新会话」能无限重置,
建会话又无频控 —— 没有跨会话的总量顶,封顶只挡得住失控循环、挡不住失控用户。
按滚动 24 小时计(不按日历日),没有午夜清零可蹲。

并发正确性(两路各自没超但合计超也要拦)靠"预留-结算"两段式:
  reserve  取租户级事务咨询锁(pg_advisory_xact_lock 串行化同租户的并发预留 ——
           会话级顶收窄自然被盖住)→ 汇总已花(含别人在飞未结算的预留)→ 超限拒;
           没超先按预留额记一行占坑;
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
ERR_TENANT = "steward.budget_tenant_exceeded"

# 默认上限(THB)。口径随大脑循环上线上调一档(单次分类 ฿0.1 → 一条多步任务 ฿0.34-1.29,
# 观测截断后的实测区间见设计报告 §5):
#   任务 ฿2  —— ฿1 会在第 5-6 步把长任务砍在半路,「查了一半不说话」比多花 ฿1 糟得多;
#               与步数上限 6 互为兜底,谁先到谁拦。
#   会话 ฿12 —— 一次月结对话 20+ 条消息 × ฿0.5。
#   租户 24h ฿150 —— 3-5 个会计的所会顶到旧的 ฿50;这一级是失控用户的顶,不是正常用量的顶。
_DEFAULT_TASK_CAP = "2"
_DEFAULT_SESSION_CAP = "12"
_DEFAULT_TENANT_DAILY_CAP = "150"
# 单次调用的预留额:占坑用,结算时改成真实成本。必须小于两级上限,否则一次都批不出去。
# 循环里单步实际 ฿0.13-0.25 —— 预留低于实际 = 并发封口偏松,宁可多占一点。
_DEFAULT_CALL_RESERVE = "0.25"

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

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_steward_cost_entries_session "
    "ON steward_cost_entries (tenant_id, session_id)",
    # 租户日额判据按 (tenant, created_at) 扫最近 24h,不能蹭 session 索引。
    "CREATE INDEX IF NOT EXISTS ix_steward_cost_entries_tenant_day "
    "ON steward_cost_entries (tenant_id, created_at)",
)

_ensured = False


def ensure_tables() -> None:
    """幂等建台账 + tenant RLS(alembic 0090 留档,prod 靠首用自愈 —— 照 store 先例)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        for idx in _INDEXES:
            cur.execute(idx)
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


def tenant_daily_cap_thb() -> Optional[Decimal]:
    """租户滚动 24h 上限(env STEWARD_TENANT_DAILY_CAP_THB)。≤0 = 该级封顶关闭。
    这是「开新会话重置」绕不过去的那一级 —— 台账按 tenant_id 汇总,不看会话。"""
    cap = _env_decimal("STEWARD_TENANT_DAILY_CAP_THB", _DEFAULT_TENANT_DAILY_CAP)
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
    tenant_spent: Decimal = Decimal("0"),
    tenant_cap: Optional[Decimal] = None,
) -> Optional[str]:
    """封顶判据(纯函数)。含预留额判:已花 + 这次的预留会破线就不放行,上限绝不被越过。
    窄口径先判(任务 → 会话 → 租户,报因更准);None = 放行。"""
    if task_cap is not None and task_spent + estimate > task_cap:
        return ERR_TASK
    if session_cap is not None and session_spent + estimate > session_cap:
        return ERR_SESSION
    if tenant_cap is not None and tenant_spent + estimate > tenant_cap:
        return ERR_TENANT
    return None


def precheck(*, tenant_id: str, session_id: str) -> dict:
    """只看不占坑的粗检(请求侧用):这条会话/这个租户还有没有额度开一条新任务。

    与 reserve 的差别是不写台账 —— 循环把模型调用整体搬进了 worker,请求侧一次模型都不调,
    再去占一次坑就会留下一串永不结算的 ฿0.25 幽灵行,把封顶判据本身撑爆。真正的闸在
    worker 每步的 reserve 上;这里只是别让明显没额度的消息白白建一条任务。
    """
    session_cap, tenant_cap = session_cap_thb(), tenant_daily_cap_thb()
    if session_cap is None and tenant_cap is None:
        return {"allowed": True}
    try:
        from core import db

        ensure_once()
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT COALESCE(SUM(cost_thb), 0) AS session_spent FROM steward_cost_entries "
                "WHERE tenant_id = %s AND session_id = %s",
                (tenant_id, session_id),
            )
            session_spent = Decimal(str((cur.fetchone() or {}).get("session_spent") or 0))
            tenant_spent = _tenant_spent_24h(cur, tenant_id) if tenant_cap else Decimal("0")
        code = decide(
            session_spent=session_spent,
            task_spent=Decimal("0"),
            estimate=call_reserve_thb(),
            session_cap=session_cap,
            task_cap=None,  # 新任务的 task_spent 必然是 0,任务级由 worker 每步现判
            tenant_spent=tenant_spent,
            tenant_cap=tenant_cap,
        )
        if not code:
            return {"allowed": True}
        cap = session_cap if code == ERR_SESSION else tenant_cap
        spent = session_spent if code == ERR_SESSION else tenant_spent
        return {
            "allowed": False,
            "code": code,
            "cap_thb": _display(cap),
            "spent_thb": _display(spent),
        }
    except Exception:  # noqa: BLE001 — 同 reserve 的取舍:封顶基础设施故障不停全功能
        logger.warning("[steward.budget] precheck failed; allowing turn", exc_info=True)
        return {"allowed": True}


def reserve(*, tenant_id: str, session_id: str, task_id: Optional[str] = None) -> dict:
    """一次模型调用的预留闸。放行 → {allowed: True, entry_id}(调用后必须 settle);
    超限 → {allowed: False, code, cap_thb, spent_thb}(金额是两位小数字符串,直接进响应)。
    """
    estimate = call_reserve_thb()
    session_cap, task_cap = session_cap_thb(), task_cap_thb()
    tenant_cap = tenant_daily_cap_thb()
    if session_cap is None and task_cap is None and tenant_cap is None:
        return {"allowed": True, "entry_id": None}
    try:
        from core import db

        ensure_once()
        with db.get_cursor(commit=True) as cur:
            # 租户级事务咨询锁:租户日额跨会话汇总,会话行锁串行化不了两个会话的并发预留。
            # 同租户的 reserve 全串行(占坑事务毫秒级,锁随提交自动释放)。
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended('steward_budget:' || %s, 0))",
                (str(tenant_id),),
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
            tenant_spent = Decimal("0")
            if tenant_cap is not None:
                tenant_spent = _tenant_spent_24h(cur, tenant_id)
            code = decide(
                session_spent=session_spent,
                task_spent=task_spent,
                estimate=estimate,
                session_cap=session_cap,
                task_cap=task_cap,
                tenant_spent=tenant_spent,
                tenant_cap=tenant_cap,
            )
            if code:
                cap = {ERR_TASK: task_cap, ERR_SESSION: session_cap}.get(code, tenant_cap)
                spent = {ERR_TASK: task_spent, ERR_SESSION: session_spent}.get(code, tenant_spent)
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


def _tenant_spent_24h(cur, tenant_id: str) -> Decimal:
    """租户滚动 24h 已花(含在飞预留)。滚动窗而非日历日:没有午夜清零可蹲。"""
    cur.execute(
        "SELECT COALESCE(SUM(cost_thb), 0) AS tenant_spent FROM steward_cost_entries "
        "WHERE tenant_id = %s AND created_at > now() - interval '24 hours'",
        (tenant_id,),
    )
    row = cur.fetchone() or {}
    return Decimal(str(row.get("tenant_spent") or 0))


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
