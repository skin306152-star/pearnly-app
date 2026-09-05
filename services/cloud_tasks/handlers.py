"""Bounded wakeups for existing database queues and maintenance jobs."""

from __future__ import annotations

import asyncio

from services.cloud_tasks import dispatch


def sync_sale(tenant_id: str, workspace_client_id: int, sale_id: str):
    from core import db
    from services.pos import sheets_sync

    with db.get_cursor_rls(tenant_id, commit=True) as cur:
        return sheets_sync.sync_sale(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, sale_id=sale_id
        )


async def drain_ocr():
    from services.ocr.jobs import store, worker

    worker.bootstrap_handlers()
    await asyncio.to_thread(store.reclaim_stale)
    row = await asyncio.to_thread(store.claim_next, worker.WORKER_ID, worker.LEASE_SEC)
    if row:
        await asyncio.to_thread(worker._run_one, row)
        dispatch.enqueue("queue.ocr")


async def drain_recon():
    from services.recon_jobs import store, worker

    worker.bootstrap_handlers()
    await asyncio.to_thread(store.reclaim_stale)
    row = await asyncio.to_thread(store.claim_next, worker.WORKER_ID, worker.LEASE_SEC)
    if row:
        await asyncio.to_thread(worker._run_one, row)
        dispatch.enqueue("queue.recon")


async def drain_steward():
    from services.steward import store, worker

    await asyncio.to_thread(worker._sweep_stale)
    row = await asyncio.to_thread(
        store.claim_next_task, worker.WORKER_ID, grace_s=worker.STALE_GRACE_S
    )
    if row:
        await worker._execute(row)
        dispatch.enqueue("queue.steward")


async def maintenance():
    from services import background_loops
    from services.cloud_tasks import store

    owner = await asyncio.to_thread(store.acquire_maintenance)
    if not owner:
        return
    try:
        await background_loops.run_erp_retry_tick()
        await background_loops.run_email_ingest_tick()
    finally:
        await asyncio.to_thread(store.release_maintenance, owner)
