"""Field projections shared by Cowork LINE draft review operations."""

from __future__ import annotations


def selection_from_payload(payload: dict) -> dict:
    adapter = str(payload.get("adapter") or "").lower()
    posting_mode = payload.get("posting_mode")
    return {
        "endpoint_id": payload.get("endpoint_id"),
        "workspace_client_id": payload.get("workspace_client_id"),
        "adapter": payload.get("adapter"),
        "target_label": payload.get("target_label"),
        "account_root": payload.get("account_root"),
        "account_set": payload.get("account_set"),
        "direction": payload.get("direction"),
        "posting_kind": payload.get("posting_kind")
        or (posting_mode if adapter == "express" else None),
        "payment": payload.get("payment") or (posting_mode if adapter == "mrerp" else None),
        "master_refresh_request_id": payload.get("master_refresh_request_id"),
    }


def pages_with_direction(pages: list, direction: str) -> list:
    updated = []
    for page in pages:
        current = dict(page) if isinstance(page, dict) else {}
        fields = dict(current.get("fields") or {})
        fields["direction"] = direction
        current["fields"] = fields
        updated.append(current)
    return updated


__all__ = ["pages_with_direction", "selection_from_payload"]
