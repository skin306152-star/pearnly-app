"""Match one OCR document's own company to the selected Pearnly workspace."""

from __future__ import annotations

from typing import Any

from core import db


def party(history: dict[str, Any], direction: str) -> tuple[str, str]:
    from services.erp.erp_payload import flatten_history_for_mrerp

    flat = flatten_history_for_mrerp(history)
    fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
    prefix = "seller" if direction == "sales" else "buyer"
    tax_id = str(fields.get(f"{prefix}_tax") or fields.get(f"{prefix}_tax_id") or "").strip()
    name = str(fields.get(f"{prefix}_name") or "").strip()
    return tax_id, name


def matches(
    identity: dict[str, Any], history: dict[str, Any], direction: str, workspace_id: int
) -> tuple[bool, str | None]:
    tax_id, name = party(history, direction)
    if not tax_id and not name:
        return False, "workspace_subject_missing"
    user_id = str(identity.get("user_id") or identity.get("id") or "")
    tenant_id = str(identity.get("tenant_id") or "")
    if direction == "sales":
        route = db.match_workspace_for_seller(tax_id, name, user_id, tenant_id)
    else:
        route = db.match_workspace_for_buyer(tax_id, name, user_id, tenant_id)
    if route.get("reason") == "lookup_error":
        return False, "workspace_lookup_failed"
    if route.get("action") == "multi":
        return False, "workspace_ambiguous"
    routed = route.get("workspace_client_id")
    if routed is None:
        return False, "workspace_subject_unmatched"
    if int(routed) != int(workspace_id):
        return False, "workspace_subject_mismatch"
    return True, None


__all__ = ["matches", "party"]
