"""Resolve the Pearnly workspace for a selected LINE ERP document batch."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core import db


def _history_party(history: dict[str, Any], direction: str) -> tuple[str, str]:
    from services.erp.erp_payload import flatten_history_for_mrerp

    flat = flatten_history_for_mrerp(history)
    fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
    prefix = "seller" if direction == "sales" else "buyer"
    tax_id = str(fields.get(f"{prefix}_tax") or fields.get(f"{prefix}_tax_id") or "").strip()
    name = str(fields.get(f"{prefix}_name") or "").strip()
    return tax_id, name


def _route_workspace(
    *, direction: str, tax_id: str, name: str, user_id: str, tenant_id: str
) -> dict[str, Any]:
    if direction == "sales":
        return db.match_workspace_for_seller(tax_id, name, user_id, tenant_id)
    return db.match_workspace_for_buyer(tax_id, name, user_id, tenant_id)


def resolve(
    identity: dict[str, Any],
    target: dict[str, Any],
    history_ids: list[str],
    direction: str,
    *,
    select_target: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    require_workspace_actor: Callable[[dict[str, Any]], dict[str, Any]],
    error_type: type[Exception],
    history_party: Callable[[dict[str, Any], str], tuple[str, str]] = _history_party,
    route_workspace: Callable[..., dict[str, Any]] = _route_workspace,
    finalize_target: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None,
    provisional_history_assignment: bool = False,
) -> dict[str, Any]:
    direction = str(direction or "").strip().lower()
    if direction not in {"purchase", "sales"}:
        raise error_type("direction_required")
    ids = list(
        dict.fromkeys(str(value).strip() for value in history_ids or [] if str(value).strip())
    )
    if not ids:
        raise error_type("history_required")
    fresh_target = select_target(identity, target)
    user_id = str(identity.get("user_id") or "")
    tenant_id = str(identity.get("tenant_id") or "")
    histories = db.get_ocr_history_details_bulk(user_id, ids, tenant_id=tenant_id)
    if len(histories) != len(ids):
        raise error_type("history_not_found")

    may_reassign = provisional_history_assignment
    existing_ids = {
        int(history["workspace_client_id"])
        for history in histories.values()
        if history.get("workspace_client_id") is not None and not may_reassign
    }
    if len(existing_ids) > 1:
        raise error_type("history_workspace_mismatch")
    target_workspace = fresh_target.get("workspace_client_id")
    if existing_ids and target_workspace is not None and int(target_workspace) not in existing_ids:
        raise error_type("history_workspace_mismatch")

    subjects: set[tuple[str, str]] = set()
    routed_ids: set[int] = set()
    for history_id in ids:
        history = histories[history_id]
        if may_reassign and target_workspace is not None:
            continue
        if history.get("workspace_client_id") is not None and not may_reassign:
            continue
        tax_id, name = history_party(history, direction)
        route = route_workspace(
            direction=direction,
            tax_id=tax_id,
            name=name,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        action = route.get("action")
        if action == "multi":
            raise error_type("workspace_ambiguous")
        if route.get("reason") == "lookup_error":
            raise error_type("workspace_lookup_failed")
        routed = route.get("workspace_client_id") if action in {"assigned", "unbound"} else None
        if routed is not None:
            routed_ids.add(int(routed))
            continue
        normalized_tax = tax_id.replace("-", "").replace(" ", "")
        normalized_name = " ".join(name.casefold().split())
        if not normalized_tax and not normalized_name:
            raise error_type("workspace_subject_missing")
        subjects.add((normalized_tax, normalized_name))
    if len(routed_ids) > 1 or len(subjects) > 1 or (routed_ids and subjects):
        raise error_type("workspace_ambiguous")

    chosen = next(iter(existing_ids or routed_ids), None)
    if target_workspace is not None:
        if chosen is not None and chosen != int(target_workspace):
            raise error_type("history_workspace_mismatch")
        chosen = int(target_workspace)
    elif chosen is not None:
        require_workspace_actor(identity)
        if not db.bind_workspace_endpoint(chosen, fresh_target["endpoint_id"], user_id, tenant_id):
            raise error_type("workspace_binding_failed")
    else:
        user = require_workspace_actor(identity)
        tax_id, name = history_party(histories[ids[0]], direction)
        if not name:
            raise error_type("workspace_subject_missing")
        chosen = db.create_workspace_client(
            user["id"],
            user["tenant_id"],
            name,
            tax_id=tax_id or None,
            erp_endpoint_id=fresh_target["endpoint_id"],
        )
        if chosen is None:
            raise error_type("workspace_create_failed")

    for history_id in ids:
        history = histories[history_id]
        if history.get("workspace_client_id") is not None and not may_reassign:
            continue
        if not db.update_history_workspace_client_id(history_id, chosen, user_id, tenant_id):
            raise error_type("history_workspace_update_failed")
    resolver = finalize_target or select_target
    return resolver(identity, {**fresh_target, "workspace_client_id": int(chosen)})


__all__ = ["resolve"]
