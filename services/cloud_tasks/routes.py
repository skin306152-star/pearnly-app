"""Private Cloud Run Worker endpoints with OIDC audience and caller checks."""

from __future__ import annotations

import asyncio
import secrets
import logging
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from services.cloud_tasks import dispatch, registry, store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/cloud-tasks", tags=["cloud-tasks"])


async def require_task_caller(request: Request):
    if os.environ.get("PEARNLY_RUNTIME_ROLE") != "worker":
        raise HTTPException(404)
    # Cloud Run IAM validates the OIDC token. The shared header also separates
    # Tasks/Scheduler calls from the Web service's user-request proxy.
    expected = os.environ.get("PEARNLY_TASK_SHARED_SECRET", "")
    supplied = request.headers.get("x-pearnly-task-key", "")
    if not expected or not secrets.compare_digest(expected, supplied):
        raise HTTPException(403)


class Delivery(BaseModel):
    task_id: UUID


@router.post("/run", dependencies=[Depends(require_task_caller)])
async def run_delivery(body: Delivery):
    task_id = str(body.task_id)
    row = await asyncio.to_thread(store.claim, task_id)
    if not row:
        raise HTTPException(404)
    if "handler" not in row:
        if row["status"] == "running":
            raise HTTPException(409, "delivery_in_progress")
        return {"status": row["status"]}
    try:
        await registry.execute(row["handler"], row["payload"])
    except asyncio.CancelledError:
        await asyncio.to_thread(store.finish, task_id, "uncertain", "request_cancelled")
        raise
    except Exception as exc:
        logger.exception("cloud_task_failed id=%s handler=%s", task_id, row["handler"])
        await asyncio.to_thread(store.finish, task_id, "failed", type(exc).__name__)
        # Failed domain work needs review; HTTP retry cannot make external writes atomic.
        return {"status": "failed"}
    await asyncio.to_thread(store.finish, task_id, "succeeded")
    return {"status": "succeeded"}


@router.post("/recover", dependencies=[Depends(require_task_caller)])
async def recover_deliveries():
    task_ids = await asyncio.to_thread(store.recoverable)
    for task_id in task_ids:
        await asyncio.to_thread(dispatch.deliver, task_id)
    for handler in ("queue.ocr", "queue.recon", "queue.steward", "maintenance"):
        await asyncio.to_thread(dispatch.enqueue, handler)
    return {"dispatched": len(task_ids), "queue_wakeups": 4}
