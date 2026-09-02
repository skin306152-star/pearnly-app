# -*- coding: utf-8 -*-
"""Compatibility envelopes backed by the canonical MR.ERP projection."""

from __future__ import annotations

from services.erp.mrerp_target_projection import refresh_mrerp_projection


def projection_listing(user: dict, endpoint: dict, listing_kind: str) -> dict:
    result = refresh_mrerp_projection(
        tenant_id=str(user["tenant_id"]),
        user_id=str(user["id"]),
        endpoint=endpoint,
    )
    state = result.get("data") or {}
    snapshot = state.get("snapshot") or {}
    masters = snapshot.get("masters") or {}
    rows = []
    for item in masters.get(listing_kind) or []:
        attributes = item.get("attributes") or {}
        if listing_kind == "products":
            row = {
                "code": item.get("source_id"),
                "name": item.get("label"),
                "category_code": attributes.get("category_code"),
                "category_name": attributes.get("category_name"),
            }
        else:
            row = {
                "code": item.get("source_id"),
                "name": item.get("label"),
                "type_name": attributes.get("type_name"),
                "prefix": attributes.get("prefix"),
            }
        rows.append(row)
    freshness = state.get("freshness") or {}
    observed_at = freshness.get("observed_at")
    return {
        "ok": bool(result.get("ok")),
        listing_kind: rows,
        "error_code": result.get("error_code"),
        "error_friendly": None,
        "elapsed_ms": 0,
        "last_fetched_at": (
            observed_at.isoformat() if hasattr(observed_at, "isoformat") else observed_at
        ),
        "cached": False,
        "stale": not bool(result.get("ok")) and bool(snapshot),
        "projection_revision": snapshot.get("revision"),
        "master_revision": snapshot.get("master_revision"),
    }


def projection_endpoint(user: dict, endpoint_id: str):
    from core import db
    from services.erp import team_access

    endpoint = team_access.assigned_endpoint_for_request(user, endpoint_id)
    return endpoint if endpoint is not None else db.get_erp_endpoint(user["id"], endpoint_id)


__all__ = ["projection_endpoint", "projection_listing"]
