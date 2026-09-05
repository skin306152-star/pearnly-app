"""Persist before dispatch; failed delivery is recovered by Cloud Scheduler."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time

logger = logging.getLogger(__name__)


def enabled() -> bool:
    return os.environ.get("PEARNLY_RUNTIME_ROLE", "") in {"web", "worker"}


def enqueue(handler: str, *args, **kwargs) -> str:
    from services.cloud_tasks import registry, store

    registry.validate(handler)
    task_id = store.insert(handler, {"args": args, "kwargs": kwargs})
    try:
        deliver(task_id)
    except Exception:
        logger.exception("cloud_task_delivery_pending id=%s handler=%s", task_id, handler)
    return task_id


def deliver(task_id: str) -> None:
    from google.api_core.exceptions import AlreadyExists
    from google.cloud import tasks_v2
    from google.protobuf.duration_pb2 import Duration

    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.environ["PEARNLY_TASK_LOCATION"]
    queue = os.environ["PEARNLY_TASK_QUEUE"]
    worker_url = os.environ["PEARNLY_WORKER_URL"].rstrip("/")
    account = os.environ["PEARNLY_TASK_SERVICE_ACCOUNT"]
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue)
    # A fresh recovery slot allows re-delivery after Cloud Tasks exhausts a prior task.
    name = f"{parent}/tasks/{task_id}-{int(time.time()) // 300}"
    task = {
        "name": name,
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": worker_url + "/internal/cloud-tasks/run",
            "headers": {
                "Content-Type": "application/json",
                "X-Pearnly-Task-Key": os.environ["PEARNLY_TASK_SHARED_SECRET"],
            },
            "body": json.dumps({"task_id": task_id}).encode(),
            "oidc_token": {"service_account_email": account, "audience": worker_url},
        },
        "dispatch_deadline": Duration(seconds=1800),
    }
    try:
        client.create_task(request={"parent": parent, "task": task}, timeout=10)
    except AlreadyExists:
        pass


def spawn(handler: str, function, *args, _legacy_spawn=None, **kwargs):
    """Explicit named dispatch, with legacy event-loop scheduling outside Cloud Run."""
    if enabled():
        return enqueue(handler, *args, **kwargs)
    if _legacy_spawn is not None:
        return _legacy_spawn(function(*args, **kwargs))
    return asyncio.get_running_loop().create_task(function(*args, **kwargs))


def spawn_sync(handler: str, function, *args, **kwargs):
    if enabled():
        return enqueue(handler, *args, **kwargs)
    return asyncio.get_running_loop().create_task(asyncio.to_thread(function, *args, **kwargs))


def wake_queue(name: str) -> None:
    if not enabled():
        return
    try:
        enqueue("queue." + name)
    except Exception:
        # Domain queue rows are already durable; the scheduled sweep will see them.
        logger.exception("cloud_queue_wakeup_pending queue=%s", name)
