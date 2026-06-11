# -*- coding: utf-8 -*-
"""库存报表聚合(POS 项目 · C1 · docs/pos/01 §B / 04 §4)。

进销存(某期 期初/入/出/期末 按商品)+ 库存周转(售出量 / 平均库存)+ 近效期看板聚合(分桶
数量/价值)。全部从 inventory_transactions(immutable 流水 · 唯一真理)聚合,签名量用
qty_delta(入=正、出=负),不依赖 txn_type 标签;周转的「售出」用 txn_type='sale_out' 精确区分
(排除调整/报损)。每个分区一条独立查询——绝不把多张一对多事实表 join 进同一句(笛卡尔积翻倍,
见 [[pos-po-a1-shipped]]);products/batches 是一对一维度,join 安全。钱/量 Decimal 字符串化。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.2f}"


def _qty(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.3f}"


def _D(v) -> Decimal:
    return Decimal(str(v if v is not None else 0))


def inventory_report(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    date_from: date,
    date_to: date,
    near_expiry_days: int = 30,
    mask_cost: bool = False,
) -> dict:
    movement = _movement(cur, tenant_id, workspace_client_id, date_from, date_to)
    near_expiry = _near_expiry_summary(cur, tenant_id, workspace_client_id, near_expiry_days)
    if mask_cost:
        # value_at_risk = SUM(qty × 单位成本)= 成本派生列,无 field.cost.view 一律遮蔽(G4)
        near_expiry["value_at_risk"] = None
    return {
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "movement": movement,
        "near_expiry": near_expiry,
    }


def _movement(cur, tenant_id, workspace_client_id, date_from, date_to) -> list:
    """进销存 + 周转:每商品 期初/入/出/售出/期末,并派生周转率与周转天数。

    期初 = 期初前累计净额;期末 = 期末前(含 to 当天)累计净额;半开窗口 [from, to+1天)。
    周转率 = 售出量 / 平均库存((期初+期末)/2);周转天数 = 期间天数 / 周转率。
    """
    to_excl = date_to + timedelta(days=1)
    cur.execute(
        "SELECT t.product_id, p.name_th, p.name_en, p.name_zh, p.base_unit, "
        "COALESCE(SUM(t.qty_delta) FILTER (WHERE t.created_at < %s),0) AS opening, "
        "COALESCE(SUM(t.qty_delta) FILTER (WHERE t.qty_delta>0 AND t.created_at>=%s AND t.created_at<%s),0) AS qin, "
        "COALESCE(-SUM(t.qty_delta) FILTER (WHERE t.qty_delta<0 AND t.created_at>=%s AND t.created_at<%s),0) AS qout, "
        "COALESCE(-SUM(t.qty_delta) FILTER (WHERE t.txn_type='sale_out' AND t.created_at>=%s AND t.created_at<%s),0) AS sold, "
        "COALESCE(SUM(t.qty_delta) FILTER (WHERE t.created_at < %s),0) AS closing "
        "FROM inventory_transactions t JOIN products p ON p.id = t.product_id "
        "WHERE t.tenant_id=%s AND t.workspace_client_id=%s "
        "GROUP BY t.product_id, p.name_th, p.name_en, p.name_zh, p.base_unit "
        "ORDER BY qout DESC, t.product_id",
        (
            date_from,
            date_from,
            to_excl,
            date_from,
            to_excl,
            date_from,
            to_excl,
            to_excl,
            tenant_id,
            workspace_client_id,
        ),
    )
    period_days = (date_to - date_from).days + 1
    rows = []
    for r in cur.fetchall():
        opening, closing, sold = _D(r["opening"]), _D(r["closing"]), _D(r["sold"])
        avg_balance = (opening + closing) / 2
        turnover = (sold / avg_balance) if avg_balance > 0 else None
        days_on_hand = (Decimal(period_days) / turnover) if turnover and turnover > 0 else None
        rows.append(
            {
                "product_id": str(r["product_id"]),
                "name": {"th": r["name_th"], "en": r["name_en"], "zh": r["name_zh"]},
                "base_unit": r["base_unit"],
                "opening": _qty(opening),
                "in": _qty(r["qin"]),
                "out": _qty(r["qout"]),
                "sold": _qty(sold),
                "closing": _qty(closing),
                "turnover_ratio": (f"{turnover:.2f}" if turnover is not None else None),
                "days_on_hand": (f"{days_on_hand:.1f}" if days_on_hand is not None else None),
            }
        )
    return rows


def _near_expiry_summary(cur, tenant_id, workspace_client_id, near_expiry_days) -> dict:
    """近效期看板聚合:已过期 / ≤7天 / ≤窗口天 三桶的批次数+数量,及窗口内(含过期)总风险货值。

    inventory_stock ⋈ inventory_batches(batch_id 一对一,不翻倍)。只算在库为正、有效期非空的批。
    """
    days = int(near_expiry_days)
    cur.execute(
        "SELECT "
        "COUNT(*) FILTER (WHERE b.expiry_date < CURRENT_DATE) AS expired_batches, "
        "COALESCE(SUM(s.qty_on_hand) FILTER (WHERE b.expiry_date < CURRENT_DATE),0) AS expired_qty, "
        "COUNT(*) FILTER (WHERE b.expiry_date >= CURRENT_DATE AND b.expiry_date < CURRENT_DATE + 7) AS d7_batches, "
        "COALESCE(SUM(s.qty_on_hand) FILTER (WHERE b.expiry_date >= CURRENT_DATE AND b.expiry_date < CURRENT_DATE + 7),0) AS d7_qty, "
        "COUNT(*) FILTER (WHERE b.expiry_date >= CURRENT_DATE AND b.expiry_date < CURRENT_DATE + %s) AS window_batches, "
        "COALESCE(SUM(s.qty_on_hand) FILTER (WHERE b.expiry_date >= CURRENT_DATE AND b.expiry_date < CURRENT_DATE + %s),0) AS window_qty, "
        "COALESCE(SUM(s.qty_on_hand * COALESCE(b.unit_cost,0)) FILTER (WHERE b.expiry_date < CURRENT_DATE + %s),0) AS value_at_risk "
        "FROM inventory_stock s JOIN inventory_batches b ON b.id = s.batch_id "
        "WHERE s.tenant_id=%s AND s.workspace_client_id=%s AND s.qty_on_hand > 0 "
        "AND b.expiry_date IS NOT NULL",
        (days, days, days, tenant_id, workspace_client_id),
    )
    r = cur.fetchone() or {}
    return {
        "near_expiry_days": days,
        "buckets": [
            {
                "label": "expired",
                "batches": int(r.get("expired_batches") or 0),
                "qty": _qty(r.get("expired_qty")),
            },
            {
                "label": "le_7d",
                "batches": int(r.get("d7_batches") or 0),
                "qty": _qty(r.get("d7_qty")),
            },
            {
                "label": f"le_{days}d",
                "batches": int(r.get("window_batches") or 0),
                "qty": _qty(r.get("window_qty")),
            },
        ],
        "value_at_risk": _money(r.get("value_at_risk")),
    }
