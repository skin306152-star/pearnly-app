# -*- coding: utf-8 -*-
"""收银前台 caps 闸:建单折扣超限/改价的授权判定 + 审计(PC-1a · docs/pos/05 §2)。

从 sale.py 抽出(单一职责)。授权判定复用 approval.py 的「本人有权 / 店长 PIN 覆盖」骨架
(verify_manager_override),审计走 log_approval。放这里而非 caps.py:caps 是被 approval 依赖的
叶子,这层要反向调 approval,搁一块会成环。
"""

from __future__ import annotations

from decimal import Decimal

from core import feature_flags
from services.pos import approval as approval_svc
from services.pos import caps as caps_svc


def _discount_pct(totals: dict) -> Decimal:
    """本单折扣% = (行折扣 + 整单折扣) / 折前毛额 × 100(折前毛额 = subtotal + 行折扣合计)。"""
    gross = totals["subtotal"] + totals["discount_total"]
    disc = totals["discount_total"] + totals["header_discount_amount"]
    if gross <= 0 or disc <= 0:
        return Decimal("0.00")
    return (disc * Decimal("100") / gross).quantize(Decimal("0.01"))


def _has_price_override(resolved: list) -> bool:
    """任一行手工单价低于挂牌价 = 改价(挂牌价未设则该行不判定)。"""
    for it in resolved:
        lp = it.get("list_price")
        if lp is not None and it["unit_price"] < lp:
            return True
    return False


def enforce(
    cur, *, tenant_id: str, workspace_client_id: int, operator, approval, totals: dict, resolved: list
) -> list:
    """按操作者 caps 卡折扣上限/改价,超限须店长 PIN 覆盖。返回 [(action, approver, details)]。

    flag 关或无操作者上下文 → 返 [](完全跳过,建单逐字节走历史)。超限且无授权块 →
    pos.approval_required;授权块校验失败 → pos.approval_denied / pos.pin_invalid(approval.py)。
    """
    if operator is None or not feature_flags.pos_cashier_caps_enabled_for(tenant_id):
        return []
    caps = caps_svc.operator_caps(
        cur, user=operator, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    pending = []
    pct = _discount_pct(totals)
    limit = Decimal(str(caps["discount_limit_pct"]))
    if pct > limit:
        pending.append(
            ("pos.discount.approved", {"discount_pct": str(pct), "limit_pct": str(limit)})
        )
    if not caps["can_override_price"] and _has_price_override(resolved):
        pending.append(("pos.price.approved", {"reason": "unit_price_below_list"}))
    if not pending:
        return []
    approver = approval_svc.verify_manager_override(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, approval=approval
    )
    return [(action, approver, details) for action, details in pending]


def audit(tenant_id: str, sale_id: str, operator, events: list) -> None:
    """经店长覆盖的折扣/改价写 operation_logs(actor = 授权人)。best-effort,不阻塞收银。"""
    for action, approver, details in events:
        approval_svc.log_approval(
            tenant_id=tenant_id,
            action=action,
            sale_id=sale_id,
            operator=operator or {},
            approver=approver,
            details=details,
        )
