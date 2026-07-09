# -*- coding: utf-8 -*-
"""
services/billing/subscription.py · 订阅套餐(铁律 #26 钱写入路径)

模型(2026-06-28 拍板):
- 一公司一行当前订阅(tenant_subscriptions)· 周期 = 订阅日起 30 天。
- 月费从 tenant_credits.balance_thb 扣;余额不足不能订阅/续订。
- 扫描优先吃套餐额度(免费)· 超额部分按套餐 over_rate 从余额扣。
- 到期惰性续订(无 cron):读/扣费时若过期 → 自动续(扣费 + 重置额度 + 延周期),
  余额不够则套餐失效(删行)→ 回落按量计费;status='cancelled' 到期同样失效。

PDF/图片按物理页占额度(1 页=1 张);Excel/Word/CSV 文档按 doc_quota_pages 折算成张。

范式(ADR-007):import db 在所有 def 之后(解 charge ↔ db 循环);纯常量直接 import pricing。
"""

from __future__ import annotations

import logging
from decimal import Decimal as _Dec, ROUND_HALF_UP as _RH

from services.billing.pricing import (
    SUBSCRIPTION_CYCLE_DAYS,
    SUBSCRIPTION_PLANS,
    subscription_plan_spec,
)

logger = logging.getLogger(__name__)


def _iso(dt):
    return dt.isoformat() if dt is not None else None


def _row_to_sub(row: dict) -> dict:
    """DB 行 → 对外 dict(JSON 友好 · remaining 现算)。"""
    quota = int(row["quota"])
    used = int(row["pages_used_this_cycle"])
    return {
        "plan_code": row["plan_code"],
        "status": row["status"],
        "quota": quota,
        "over_rate": float(row["over_rate"]),
        "monthly_fee": float(row["monthly_fee"]),
        "pages_used_this_cycle": used,
        "remaining": max(0, quota - used),
        "auto_renew": bool(row["auto_renew"]),
        "cycle_start": _iso(row.get("cycle_start")),
        "cycle_end": _iso(row.get("cycle_end")),
    }


_SUB_COLS = (
    "plan_code, status, quota, over_rate, monthly_fee, pages_used_this_cycle, "
    "auto_renew, cycle_start, cycle_end"
)


def active_sub_usage_join_sql(alias: str, tenant_ref: str) -> str:
    """本月用量读侧 join 片段:显示用量 = monthly_page_usage.pages_used +
    活跃订阅(status='active' AND cycle_end>NOW())的 pages_used_this_cycle。

    两计数器写侧互斥(充值/按量走 monthly_page_usage · 订阅走本表 · 见
    credits_schema.py 建表注释 4c),读侧相加不会重复计。tenant_subscriptions
    PRIMARY KEY(tenant_id) 一对一,join 不放大行数,无需 LATERAL/子查询。

    四个读点共用本片段(billing_credits_routes / credits.store / tenant_core /
    account_status),避免各自手写漂移。tenant_ref 是调用方 SQL 里代表租户的
    列引用或参数占位符(如 "t.id" / "%s::uuid")。
    """
    return (
        f"LEFT JOIN tenant_subscriptions {alias} ON {alias}.tenant_id = {tenant_ref} "
        f"AND {alias}.status = 'active' AND {alias}.cycle_end > NOW()"
    )


def get_active_subscription(tenant_id) -> dict | None:
    """当前有效订阅(无则 None)· 惰性续订/失效。

    两阶段:周期内只读直接返(热路径 0 写);已过期才进 _renew_or_expire 加锁处理。
    """
    if not tenant_id:
        return None
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id)) as cur:
            cur.execute(
                f"SELECT {_SUB_COLS}, (cycle_end > NOW()) AS in_cycle "
                "FROM tenant_subscriptions WHERE tenant_id = %s::uuid",
                (str(tenant_id),),
            )
            row = cur.fetchone()
        if not row:
            return None
        if row["in_cycle"]:
            return _row_to_sub(row)
    except Exception as e:
        logger.warning(f"get_active_subscription read error tenant={tenant_id}: {e}")
        return None
    return _renew_or_expire(tenant_id)


def _renew_or_expire(tenant_id) -> dict | None:
    """周期已过 · 加锁续订或失效。auto_renew 且余额够 → 扣费续 30 天 + 重置额度;
    否则(cancelled / 关续订 / 余额不足)删行 → 回落按量。"""
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                f"SELECT {_SUB_COLS}, (cycle_end > NOW()) AS in_cycle "
                "FROM tenant_subscriptions WHERE tenant_id = %s::uuid FOR UPDATE",
                (str(tenant_id),),
            )
            row = cur.fetchone()
            if not row:
                return None
            if row["in_cycle"]:  # 并发已被别处续订
                return _row_to_sub(row)
            if row["status"] == "cancelled" or not row["auto_renew"]:
                cur.execute(
                    "DELETE FROM tenant_subscriptions WHERE tenant_id = %s::uuid", (str(tenant_id),)
                )
                return None

            fee = _Dec(str(row["monthly_fee"]))
            cur.execute(
                "SELECT balance_thb FROM tenant_credits WHERE tenant_id = %s::uuid FOR UPDATE",
                (str(tenant_id),),
            )
            brow = cur.fetchone()
            bal = _Dec(str(brow["balance_thb"])) if brow else _Dec("0")
            if bal < fee:  # 余额不够续 → 套餐失效 · 回落按量计费
                cur.execute(
                    "DELETE FROM tenant_subscriptions WHERE tenant_id = %s::uuid", (str(tenant_id),)
                )
                logger.info(f"[subscription] expire(insufficient) tenant={str(tenant_id)[:8]}")
                return None

            new_bal = bal - fee
            cur.execute(
                "UPDATE tenant_credits SET balance_thb = %s, updated_at = NOW() "
                "WHERE tenant_id = %s::uuid",
                (str(new_bal), str(tenant_id)),
            )
            cur.execute(
                "INSERT INTO credit_transactions "
                "(tenant_id, user_id, type, amount_thb, pages, balance_after, description) "
                "VALUES (%s::uuid, NULL, 'subscription', %s, 0, %s, %s)",
                (str(tenant_id), str(-fee), str(new_bal), f"套餐续订 Package {row['plan_code']}"),
            )
            cur.execute(
                f"UPDATE tenant_subscriptions SET cycle_start = NOW(), "
                "cycle_end = NOW() + make_interval(days => %s), pages_used_this_cycle = 0, "
                "updated_at = NOW() WHERE tenant_id = %s::uuid "
                f"RETURNING {_SUB_COLS}",
                (SUBSCRIPTION_CYCLE_DAYS, str(tenant_id)),
            )
            logger.info(f"[subscription] renewed tenant={str(tenant_id)[:8]} fee=฿{fee}")
            return _row_to_sub(cur.fetchone())
    except Exception as e:
        logger.warning(f"_renew_or_expire error tenant={tenant_id}: {e}")
        return None


def consume_subscription_quota(cur, tenant_id, pages_needed: int):
    """在已开启的 RLS 扣费事务里:锁订阅行 · 把 pages_needed 张先抵套餐额度 · 累加周期用量。

    返 (billable_pages, over_rate) — 套餐内 billable=0;无有效订阅(被并发失效)返 None,
    调用方回落按量计费。pages_needed 含免费+超额全部计入 pages_used_this_cycle。
    """
    cur.execute(
        "SELECT quota, pages_used_this_cycle, over_rate, (cycle_end > NOW()) AS in_cycle "
        "FROM tenant_subscriptions WHERE tenant_id = %s::uuid FOR UPDATE",
        (str(tenant_id),),
    )
    row = cur.fetchone()
    if not row or not row["in_cycle"]:
        return None
    quota = int(row["quota"])
    used = int(row["pages_used_this_cycle"])
    over_rate = _Dec(str(row["over_rate"]))
    remaining = max(0, quota - used)
    billable = max(0, int(pages_needed) - remaining)
    cur.execute(
        "UPDATE tenant_subscriptions SET pages_used_this_cycle = pages_used_this_cycle + %s, "
        "updated_at = NOW() WHERE tenant_id = %s::uuid",
        (int(pages_needed), str(tenant_id)),
    )
    return billable, over_rate


def subscription_subscribe(user_id, tenant_id, plan_code: str) -> dict:
    """订阅/换套餐 · 从余额扣月费 · 立即生效并重新计周期(无按比例退款)。

    余额不足返 {ok:False, error:'insufficient_balance', balance_thb, needed_thb}。
    """
    if not tenant_id:
        return {"ok": False, "error": "no_tenant"}
    spec = subscription_plan_spec(plan_code)
    if not spec:
        return {"ok": False, "error": "unknown_plan"}
    code = plan_code.strip().upper()
    fee = spec["fee"]
    quota = int(spec["quota"])
    over_rate = spec["over_rate"]
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            # 统一锁序:先锁订阅行再锁余额行(与 _renew_or_expire/consume 一致),消除 AB-BA 死锁。
            # 首次订阅尚无订阅行,FOR UPDATE 空集无副作用;此时也不可能有并发续订(续订需已存在行)。
            cur.execute(
                "SELECT 1 FROM tenant_subscriptions WHERE tenant_id = %s::uuid FOR UPDATE",
                (str(tenant_id),),
            )
            cur.execute(
                "SELECT balance_thb FROM tenant_credits WHERE tenant_id = %s::uuid FOR UPDATE",
                (str(tenant_id),),
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    "INSERT INTO tenant_credits (tenant_id, balance_thb) "
                    "VALUES (%s::uuid, 0) RETURNING balance_thb",
                    (str(tenant_id),),
                )
                row = cur.fetchone()
            bal = _Dec(str(row["balance_thb"]))
            if bal < fee:
                return {
                    "ok": False,
                    "error": "insufficient_balance",
                    "balance_thb": float(bal),
                    "needed_thb": float(fee),
                }
            new_bal = bal - fee
            cur.execute(
                "UPDATE tenant_credits SET balance_thb = %s, updated_at = NOW() "
                "WHERE tenant_id = %s::uuid",
                (str(new_bal), str(tenant_id)),
            )
            cur.execute(
                "INSERT INTO credit_transactions "
                "(tenant_id, user_id, type, amount_thb, pages, balance_after, description) "
                "VALUES (%s::uuid, %s::uuid, 'subscription', %s, 0, %s, %s)",
                (
                    str(tenant_id),
                    str(user_id) if user_id else None,
                    str(-fee),
                    str(new_bal),
                    f"订阅 Package {code}",
                ),
            )
            cur.execute(
                "INSERT INTO tenant_subscriptions "
                "(tenant_id, plan_code, status, cycle_start, cycle_end, quota, over_rate, "
                " monthly_fee, pages_used_this_cycle, auto_renew) "
                "VALUES (%s::uuid, %s, 'active', NOW(), NOW() + make_interval(days => %s), "
                "        %s, %s, %s, 0, TRUE) "
                "ON CONFLICT (tenant_id) DO UPDATE SET "
                "  plan_code = EXCLUDED.plan_code, status = 'active', cycle_start = NOW(), "
                "  cycle_end = NOW() + make_interval(days => %s), quota = EXCLUDED.quota, "
                "  over_rate = EXCLUDED.over_rate, monthly_fee = EXCLUDED.monthly_fee, "
                "  pages_used_this_cycle = 0, auto_renew = TRUE, updated_at = NOW() "
                f"RETURNING {_SUB_COLS}",
                (
                    str(tenant_id),
                    code,
                    SUBSCRIPTION_CYCLE_DAYS,
                    quota,
                    str(over_rate),
                    str(fee),
                    SUBSCRIPTION_CYCLE_DAYS,
                ),
            )
            sub = _row_to_sub(cur.fetchone())
        logger.info(f"[subscription] subscribe tenant={str(tenant_id)[:8]} plan={code} fee=฿{fee}")
        return {"ok": True, "balance_after": float(new_bal), "subscription": sub}
    except Exception as e:
        logger.error(f"[subscription] subscribe FAIL tenant={tenant_id} plan={plan_code}: {e}")
        return {"ok": False, "error": str(e)[:200]}


def subscription_cancel(tenant_id) -> dict:
    """取消订阅(到期不再续)· 当前周期额度仍可用到 cycle_end · 到期惰性失效。"""
    if not tenant_id:
        return {"ok": False, "error": "no_tenant"}
    try:
        with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
            cur.execute(
                "UPDATE tenant_subscriptions SET status = 'cancelled', auto_renew = FALSE, "
                "updated_at = NOW() WHERE tenant_id = %s::uuid AND status = 'active'",
                (str(tenant_id),),
            )
            changed = cur.rowcount > 0
        return {"ok": True, "cancelled": changed}
    except Exception as e:
        logger.error(f"[subscription] cancel FAIL tenant={tenant_id}: {e}")
        return {"ok": False, "error": str(e)[:200]}


def subscription_catalog() -> list[dict]:
    """套餐目录(前端套餐卡渲染用)· 金额转 float。"""
    return [
        {
            "code": code,
            "quota": int(spec["quota"]),
            "fee": float(spec["fee"]),
            "over_rate": float(spec["over_rate"]),
        }
        for code, spec in SUBSCRIPTION_PLANS.items()
    ]


# 量化超额费用到分(satang)· 与 _debit_balance 一致用 HALF_UP。
def overage_cost(billable_pages: int, over_rate: _Dec) -> _Dec:
    if billable_pages <= 0:
        return _Dec("0.00")
    return (over_rate * billable_pages).quantize(_Dec("0.01"), rounding=_RH)


# ⚠️ 见模块 docstring · `import db` 在所有 def 之后,解 subscription ↔ db 循环 import。
from core import db  # noqa: E402
