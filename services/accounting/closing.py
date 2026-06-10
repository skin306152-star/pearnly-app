# -*- coding: utf-8 -*-
"""月末结账(docs/accounting/02 R9 + 03 §5 close-period)。

流程:期未锁 + 无待审 → 算本期销/进项 VAT(剔除 vat_closing 自身)→ 经引擎套 R9 生成
结转凭证 → 直接 posted(结账是人点了二次确认的动作,不再排队待审)→ 推进
accounting_settings.closed_through 水位(锁 ≤ period 的所有期)。
待审凭证挡结账:pending_review 可能是缺映射的不平壳,锁了就改不了(acct.unbalanced)。
"""

from __future__ import annotations

import calendar
import re
from datetime import date
from decimal import Decimal

from core.pos_api import PosError
from services.accounting import posting
from services.accounting import settings as acct_settings
from services.accounting import store as acct_store
from services.accounting import vouchers as jv

ZERO = Decimal("0")
_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validate_period(period) -> str:
    if not period or not _PERIOD_RE.match(str(period)):
        raise PosError("acct.unexpected", 422, detail="bad_period")
    return str(period)


def period_end(period: str) -> date:
    year, month = int(period[:4]), int(period[5:7])
    return date(year, month, calendar.monthrange(year, month)[1])


def pending_count_through(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> int:
    """≤ period 的待审凭证数(closed_through 锁的是整段历史,所以历史待审也挡)。"""
    cur.execute(
        "SELECT count(*) AS n FROM journal_vouchers "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND period <= %s AND status = 'pending_review'",
        (tenant_id, workspace_client_id, period),
    )
    return int(cur.fetchone()["n"])


def vat_totals(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> tuple:
    """本期销项/进项 VAT 净额(贷-借 / 借-贷),只数已过账、剔除 vat_closing 自身。

    红冲反向行天然抵减(销项税借方=负销项),与 R8 反向模板一致。
    """
    mappings = acct_store.resolve_mappings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    out_id, in_id = mappings.get("output_vat"), mappings.get("input_vat")
    if not out_id or not in_id:
        # 角色未映射 ⇒ 引擎从未往这两科目落过分录,本期 VAT 必为零(空套账结账放行)
        return ZERO, ZERO
    cur.execute(
        "SELECT "
        "COALESCE(SUM(CASE WHEN l.account_id = %s AND l.dr_cr = 'credit' THEN l.amount "
        "              WHEN l.account_id = %s AND l.dr_cr = 'debit' THEN -l.amount "
        "              ELSE 0 END), 0) AS output_vat, "
        "COALESCE(SUM(CASE WHEN l.account_id = %s AND l.dr_cr = 'debit' THEN l.amount "
        "              WHEN l.account_id = %s AND l.dr_cr = 'credit' THEN -l.amount "
        "              ELSE 0 END), 0) AS input_vat "
        "FROM journal_lines l JOIN journal_vouchers v ON v.id = l.voucher_id "
        "WHERE v.tenant_id = %s AND v.workspace_client_id = %s AND v.period = %s "
        "AND v.status IN ('posted', 'auto_posted') AND v.source_type != 'vat_closing'",
        (out_id, out_id, in_id, in_id, tenant_id, workspace_client_id, period),
    )
    row = cur.fetchone()
    return Decimal(str(row["output_vat"])), Decimal(str(row["input_vat"]))


def close_period(
    cur, *, tenant_id: str, workspace_client_id: int, period: str, closed_by=None
) -> dict:
    """结账:R9 VAT 结转 + 锁期。返回 {closed, vat_payable, voucher}。"""
    period = validate_period(period)
    settings = acct_settings.get_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    if acct_settings.is_period_closed(settings, period):
        raise PosError("acct.period_closed", 409)

    pending = pending_count_through(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    if pending:
        raise PosError("acct.unbalanced", 422, detail=f"pending_review:{pending}")

    out_vat, in_vat = vat_totals(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    voucher = None
    if out_vat != ZERO or in_vat != ZERO:
        voucher = posting.generate_for_source(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            source_type="vat_closing",
            source_id=None,
            created_by=closed_by,
            context={
                "period": period,
                "voucher_date": period_end(period),
                "output_vat_total": out_vat,
                "input_vat_total": in_vat,
            },
        )
        if voucher and (voucher.get("review_reason") or "").startswith("mapping_missing"):
            raise PosError("acct.mapping_missing", 422, detail=voucher["review_reason"])
        if voucher and voucher["status"] == "pending_review":
            # 结账动作本身就是人工确认,结转凭证不再排队
            jv.set_status(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                voucher_id=voucher["id"],
                status="posted",
                method="manual",
                reviewed_by=closed_by,
            )
            voucher = {**voucher, "status": "posted", "method": "manual"}

    _advance_closed_through(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        prior=settings.get("closed_through"),
    )
    return {"closed": period, "vat_payable": out_vat - in_vat, "voucher": voucher}


def _advance_closed_through(cur, *, tenant_id, workspace_client_id, period, prior) -> None:
    """水位只前进不后退;settings 行可能还没物化(纯默认),先 upsert 空改动再推水位。"""
    acct_settings.update_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, data={}
    )
    if prior and prior >= period:
        return
    cur.execute(
        "UPDATE accounting_settings SET closed_through = %s, updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND (closed_through IS NULL OR closed_through < %s)",
        (period, tenant_id, workspace_client_id, period),
    )
