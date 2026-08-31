"""Read-only document checks for a selected Cowork LINE ERP target."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from core import db
from services.erp.express_push.posting_kind import normalize as normalize_posting_kind
from services.erp.express_push.preflight import preflight_express
from services.erp.shared_express_schema import enable_shared_express_select
from services.erp.shared_express_store import fetch_visible_endpoint_rows

_DIRECTIONS = frozenset({"purchase", "sales"})
_PAYMENTS = frozenset({"cash", "credit"})


def _result(missing: list[str], *, checks: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ok": not missing,
        "missing": missing,
        "block_reason": missing[0] if missing else None,
        "ready_checks": checks,
    }


def _with_manual_fields(history: dict[str, Any], direction: str, payment: str | None):
    prepared = deepcopy(history)
    pages = prepared.get("pages") if isinstance(prepared.get("pages"), list) else []
    primary = next(
        (
            page
            for page in pages
            if isinstance(page, dict) and not page.get("is_duplicate") and not page.get("is_copy")
        ),
        pages[0] if pages and isinstance(pages[0], dict) else None,
    )
    if primary is None:
        primary = {"fields": {}}
        pages = [primary]
        prepared["pages"] = pages
    fields = primary.get("fields") if isinstance(primary.get("fields"), dict) else {}
    fields = dict(fields)
    fields["direction"] = direction
    if payment is not None:
        fields["posting_payment_manual"] = payment
    primary["fields"] = fields
    return prepared


def _party(history: dict[str, Any], direction: str) -> tuple[str, str]:
    from services.erp.erp_payload import flatten_history_for_mrerp

    flat = flatten_history_for_mrerp(history)
    fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
    prefix = "seller" if direction == "sales" else "buyer"
    tax_id = str(fields.get(f"{prefix}_tax") or fields.get(f"{prefix}_tax_id") or "").strip()
    name = str(fields.get(f"{prefix}_name") or "").strip()
    return tax_id, name


def _subject_matches(
    identity: dict[str, Any], history: dict[str, Any], direction: str, workspace_id: int
) -> tuple[bool, str | None]:
    tax_id, name = _party(history, direction)
    if not tax_id and not name:
        return False, "workspace_subject_missing"
    user_id = str(identity.get("user_id") or "")
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
    if int(routed) != workspace_id:
        return False, "workspace_subject_mismatch"
    return True, None


def _managed_endpoint(identity: dict[str, Any], target: dict[str, Any]) -> dict[str, Any] | None:
    tenant_id = str(identity.get("tenant_id") or "")
    user_id = str(identity.get("user_id") or "")
    workspace_id = int(target["workspace_client_id"])
    endpoint_id = str(target["endpoint_id"])
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute("SELECT set_config('app.current_workspace_id', %s, true)", (str(workspace_id),))
        if not enable_shared_express_select(cur, tenant_id, workspace_id):
            return None
        rows = fetch_visible_endpoint_rows(
            cur,
            actor_id=user_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_id,
        )
    matches = [row for row in rows if str(row.get("id") or "") == endpoint_id]
    return matches[0] if len(matches) == 1 else None


def _express_projection(
    identity: dict[str, Any],
    target: dict[str, Any],
    history: dict[str, Any],
    direction: str,
    posting_kind: str | None,
    payment: str | None,
) -> dict[str, Any]:
    kind = normalize_posting_kind(posting_kind)
    if kind is None:
        code = "posting_kind_required" if posting_kind in (None, "") else "posting_kind_invalid"
        return _result([code], checks={"target_ready": True, "document_preflight": False})
    endpoint = _managed_endpoint(identity, target)
    if endpoint is None:
        return _result(
            ["endpoint_not_found"],
            checks={"target_ready": False, "document_preflight": False},
        )
    config = dict(endpoint.get("config") or {})
    config["account_set"] = endpoint.get("bound_account_set")
    prepared_endpoint = {**endpoint, "config": config, "user_id": str(identity["user_id"])}
    prepared_history = _with_manual_fields(history, direction, payment)
    result = preflight_express(prepared_endpoint, prepared_history, posting_kind=kind)
    reason = "express_disabled" if result.disabled else result.reason
    missing = [str(reason)] if reason else []
    return _result(missing, checks=result.checks_json())


def preflight_document(
    identity: dict[str, Any],
    target: dict[str, Any],
    history_id: str,
    direction: str,
    posting_kind: str | None = None,
    payment: str | None = None,
) -> dict[str, Any]:
    from services.cowork_line.erp_targets import CoworkLineErpTargetError, require_target

    direction = str(direction or "").strip().lower()
    if direction not in _DIRECTIONS:
        return _result(["direction_required"], checks={"target_ready": False})
    payment = str(payment).strip().lower() if payment is not None else None
    if payment not in _PAYMENTS | {None}:
        return _result(["payment_invalid"], checks={"target_ready": False})
    endpoint_id = str(target.get("endpoint_id") or "")
    workspace_id = target.get("workspace_client_id")
    try:
        fresh = require_target(identity, endpoint_id, workspace_id)
    except CoworkLineErpTargetError as exc:
        missing = list(exc.missing) or [exc.code]
        return _result(missing, checks={"target_ready": False})
    if fresh.get("workspace_client_id") is None:
        return _result(["workspace_required"], checks={"target_ready": True})
    workspace_id = int(fresh["workspace_client_id"])
    history = db.get_ocr_history_detail(
        str(identity.get("user_id") or ""),
        str(history_id),
        tenant_id=str(identity.get("tenant_id") or ""),
    )
    if not history:
        return _result(["history_not_found"], checks={"target_ready": True})
    if history.get("workspace_client_id") != workspace_id:
        return _result(["history_workspace_mismatch"], checks={"target_ready": True})
    subject_ok, subject_error = _subject_matches(identity, history, direction, workspace_id)
    if not subject_ok:
        return _result(
            [str(subject_error)],
            checks={"target_ready": True, "workspace_subject": False},
        )
    if fresh.get("adapter") == "express":
        return _express_projection(identity, fresh, history, direction, posting_kind, payment)
    if fresh.get("adapter") != "mrerp":
        return _result(["adapter_not_supported"], checks={"target_ready": True})
    if payment is None:
        return _result(
            ["payment_required"],
            checks={"target_ready": True, "workspace_subject": True},
        )
    if direction == "purchase" and payment == "cash":
        return _result(
            ["mrerp_purchase_cash_unverified"],
            checks={
                "target_ready": True,
                "workspace_subject": True,
                "live_connection": None,
                "payment_mode": False,
            },
        )
    return _result(
        [],
        checks={
            "target_ready": True,
            "workspace_subject": True,
            "erp_connection_configured": bool(fresh.get("configured")),
            "live_connection": None,
            "payment_mode": True,
        },
    )


__all__ = ["preflight_document"]
