"""Only reviewed named handlers can be invoked by a delivery."""

from __future__ import annotations

import asyncio
import importlib
import inspect

# Module paths are code-owned, never supplied by request payloads.
HANDLERS = {
    "queue.ocr": ("services.cloud_tasks.handlers", "drain_ocr"),
    "queue.recon": ("services.cloud_tasks.handlers", "drain_recon"),
    "queue.steward": ("services.cloud_tasks.handlers", "drain_steward"),
    "maintenance": ("services.cloud_tasks.handlers", "maintenance"),
    "ocr.official_name": ("services.rd.official_name", "enrich_records"),
    "pos.sheets": ("services.cloud_tasks.handlers", "sync_sale"),
    "erp.notify": ("services.erp.line_push_notification", "notify_success"),
    "erp.refresh": ("services.erp.target_refresh", "process_mrerp_request"),
    "erp.auto_push": ("services.erp.auto_push", "_auto_push_history"),
    "erp.smart_push": ("services.erp.auto_push", "_auto_push_smart_routed"),
    "ocr.exception_checks": ("services.exceptions.exception_checks", "_async_run_exception_checks"),
    "ocr.charge": ("core.db", "charge_ocr_async"),
    "workorder.advance": ("services.cloud_tasks.workorders", "advance"),
    "workorder.bank_sales": ("services.cloud_tasks.workorders", "bank_sales"),
    "cowork.document": ("services.cowork_line.webhook_documents", "process_document"),
    "line_erp.document": ("services.line_erp.webhook", "_process_document"),
    "dms.image": ("services.line_dms.flow", "_dispatch_image"),
    "dms.create": ("services.line_dms.flow", "_write_create"),
    "dms.update": ("services.line_dms.flow", "_write_update"),
    "dms.dedup": ("services.line_dms.flow", "_run_dedup"),
    "dms.approve": ("services.line_dms.approval_flow", "_execute_approved"),
    "dms.booking": ("services.line_dms.booking_flow", "_execute_booking"),
    "dms.records": ("services.line_dms.query_flow", "_run_records"),
    "dms.top": ("services.line_dms.query_flow", "_run_top"),
}


def validate(name: str):
    if name not in HANDLERS:
        raise ValueError("unknown_cloud_task_handler")


async def execute(name: str, payload: dict):
    validate(name)
    module, attribute = HANDLERS[name]
    function = getattr(importlib.import_module(module), attribute)
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})
    if not isinstance(args, list) or not isinstance(kwargs, dict):
        raise ValueError("invalid_cloud_task_arguments")
    if inspect.iscoroutinefunction(function):
        return await function(*args, **kwargs)
    return await asyncio.to_thread(function, *args, **kwargs)
