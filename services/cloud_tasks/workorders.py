"""Revalidate a queued work order's lease before any model or ERP operation."""

from core import db
from services.workorder import run_leases, runner


def _renew(tenant_id, work_order_id, owner):
    if not owner:
        raise ValueError("workorder_delivery_missing_owner")
    with db.get_cursor(commit=True) as cur:
        return run_leases.renew_run_lease(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            owner=owner,
            ttl_seconds=runner.run_lease_ttl_seconds(),
        )


def advance(tenant_id, work_order_id, owner):
    if not _renew(tenant_id, work_order_id, owner):
        return {"skipped": "lease_superseded"}
    return runner.advance(tenant_id, work_order_id, owner)


def bank_sales(*, tenant_id, work_order_id, claimed, lease_owner, trigger="manual"):
    from services.workorder.steps import bank_sales_brain as brain

    if not claimed or not _renew(tenant_id, work_order_id, lease_owner):
        return {"skipped": "lease_superseded"}
    if not brain.begin(work_order_id, 0):
        return {"skipped": "already_running"}
    return brain.run_async(
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        claimed=True,
        lease_owner=lease_owner,
        trigger=trigger,
    )
