# -*- coding: utf-8 -*-
"""POS 收银台今日交易只读读模型(退货/作废入口用)。

从 sale.py 拆出以守单文件 <500(REFACTOR-WC 硬闸)。纯读:list_today_rows(DAL)+ voidable
判据(镜像 void_sale 边界)。依赖单向 sales_query → sale/sales_store,无循环(sale 不回引本模块)。
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from services.pos import sales_store
from services.pos.sale import _money

_BANGKOK = timezone(timedelta(hours=7))  # 泰国固定 UTC+7 无夏令时(同 services/sales/dates)


def _bangkok_day_start() -> datetime:
    """今日(曼谷本地)零点的绝对时刻。sold_at 存 UTC · 用 tz-aware 边界比较不差午夜那一天。"""
    from services.sales.dates import bangkok_today

    return datetime.combine(bangkok_today(), time.min, tzinfo=_BANGKOK)


def list_today(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """收银台今日已完成交易(退货/作废入口)。

    voidable 镜像 void_sale 的边界(单一事实源):未被退过 + 属当前未结班(无班次单也可,
    同 void_sale 跳过班次校验的分支)。非当班/已退过 → 前台不给作废入口(诚实),点了也被
    后端 void_not_allowed 兜住。method 是原始方式串,四语标签由前台按 posui.shift.method.* 出。
    """
    from services.pos import cashier as cashier_dal

    open_shift = cashier_dal.get_open_shift_for_workspace(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    open_shift_id = str(open_shift["id"]) if open_shift else None
    rows = sales_store.list_today_rows(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        since=_bangkok_day_start(),
    )
    items = []
    for r in rows:
        shift_id = str(r["shift_id"]) if r["shift_id"] else None
        voidable = (not r["has_refund"]) and (shift_id is None or shift_id == open_shift_id)
        items.append(
            {
                "id": str(r["id"]),
                "receipt_no": r["receipt_no"],
                "sold_at": r["sold_at"].isoformat() if r["sold_at"] else None,
                "grand_total": _money(r["grand_total"]),
                "method": r["top_method"] or "cash",
                "mixed": int(r["pay_count"] or 0) > 1,
                "voidable": voidable,
            }
        )
    return {"items": items}
