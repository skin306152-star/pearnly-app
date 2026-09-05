"""Read-only model/config facts, never substitutes old benchmarks for live metrics."""

import os

from services.ai_gateway.routing_matrix import resolve_routes
from services.ai_gateway.providers.enterprise import PROCESSOR_VERSION
from services.ocr.enterprise_request import contract_hash


def snapshot(config=None) -> dict:
    from services.ocr.engine_policy import resolve_mode, load_config, MODE_BACKENDS
    from services.ai_gateway.backends import active_backend
    from services.ocr.contracts import OCR_TASKS

    config = config if config is not None else load_config()
    tiers = {}
    for lane, route in resolve_routes().items():
        if not lane.startswith("ocr."):
            continue
        _, mode, tier = lane.split(".")
        backend = MODE_BACKENDS.get(mode) or active_backend()
        item = tiers.setdefault(mode, {"models": {}, "metrics": {}})
        item["models"][tier] = {
            "model": route.model,
            "backend": backend,
            "location": route.vertex_location if backend == "vertex" else "",
            "thinking": (
                "LOW" if route.model.startswith("gemini-3.8") and backend == "vertex" else None
            ),
        }
    tiers["enterprise"]["document_ocr"] = {
        "version": PROCESSOR_VERSION,
        "location": os.environ.get("ENTERPRISE_OCR_LOCATION", "asia-southeast1"),
        "processor_configured": bool(os.environ.get("ENTERPRISE_OCR_PROCESSOR_ID")),
        "contract_hashes": {
            category: contract_hash(category) for category in ("bank", "gl", "vat")
        },
    }
    return {
        "scope": "current_service_config_not_worker_execution",
        "service": os.environ.get("K_SERVICE", "local"),
        "revision": os.environ.get("K_REVISION", "local"),
        "tiers": tiers,
        "task_modes": {task: resolve_mode(task, config=config) for task in OCR_TASKS},
        "cost_basis": "estimated_paid_usage_before_free_tier_and_credits",
        "latency_basis": "provider_call_not_document_end_to_end",
    }
