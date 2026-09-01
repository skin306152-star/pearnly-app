"""Sanitize and persist Express account sets reported by the companion."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_ACCOUNT_SET_KEYS = (
    "code",
    "name",
    "name_en",
    "company",
    "tax_id",
    "path",
    "root",
    "root_label",
    "row",
    "writable",
)
_ACCOUNT_MAPPING_KEYS = (
    "revenue_acc",
    "ar_acc",
    "vat_output_acc",
    "fallback_acc",
    "ap_acc",
    "vat_input_acc",
)
_MAX_ACCOUNT_SETS = 50


def _sanitize_account_sets(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw[:_MAX_ACCOUNT_SETS]:
        if not isinstance(item, dict):
            continue
        clean: dict[str, Any] = {}
        for key in _ACCOUNT_SET_KEYS:
            value = item.get(key)
            if key == "writable":
                clean[key] = bool(value)
            elif key == "row" and value not in (None, ""):
                try:
                    clean[key] = max(0, int(value))
                except (TypeError, ValueError):
                    pass
            elif value is not None:
                clean[key] = str(value)[:200]
        mapping = item.get("mapping")
        if isinstance(mapping, dict):
            clean_mapping = {
                key: str(mapping.get(key) or "").strip()[:40]
                for key in _ACCOUNT_MAPPING_KEYS
                if str(mapping.get(key) or "").strip()
            }
            if clean_mapping:
                clean["mapping"] = clean_mapping
        if clean.get("code") or clean.get("name"):
            out.append(clean)
    return out


def store_account_sets(endpoint_id: str, account_sets: Any) -> int:
    sets = _sanitize_account_sets(account_sets)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_endpoints
                SET config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
                        'reported_account_sets', %s::jsonb,
                        'account_sets_seen_at', to_jsonb(NOW()::text))
                WHERE id = %s AND adapter = 'express' AND binding_generation = 0
                """,
                (json.dumps(sets, ensure_ascii=False), endpoint_id),
            )
            changed = cur.rowcount
        return len(sets) if changed == 1 else 0
    except Exception as exc:
        logger.error("store_account_sets failed: %s", exc)
        return 0


__all__ = ["_sanitize_account_sets", "store_account_sets"]
