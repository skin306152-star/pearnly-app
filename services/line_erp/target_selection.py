"""Validate and persist one explicit ERP target snapshot for a LINE draft."""

from __future__ import annotations

from typing import Any

from core import db
from services.line_erp import target_preflight


class SelectionError(Exception):
    def __init__(
        self,
        code: str,
        status_code: int = 409,
        *,
        readiness: dict[str, Any] | None = None,
    ):
        self.code = code
        self.status_code = status_code
        self.readiness = readiness
        super().__init__(code)


def from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    adapter = str(payload.get("adapter") or "").lower()
    posting_mode = payload.get("posting_mode")
    return {
        "endpoint_id": payload.get("endpoint_id"),
        "workspace_client_id": payload.get("workspace_client_id"),
        "adapter": adapter or None,
        "target_label": payload.get("target_label"),
        "direction": payload.get("mode") or payload.get("direction"),
        "posting_kind": payload.get("posting_kind")
        or (posting_mode if adapter == "express" else None),
        "payment": payload.get("payment") or (posting_mode if adapter == "mrerp" else None),
    }


def normalize(
    binding: dict[str, Any], values: dict[str, Any], *, refresh: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    direction = str(values.get("direction") or values.get("mode") or "").lower()
    if direction not in {"purchase", "sales"}:
        raise SelectionError("line_erp.direction_required", 422)
    endpoint_id = str(values.get("endpoint_id") or "").strip()
    workspace_id = values.get("workspace_client_id")
    if not endpoint_id or workspace_id is None:
        raise SelectionError("line_erp.target_required", 422)
    try:
        readiness = target_preflight.require_ready(
            binding,
            endpoint_id=endpoint_id,
            workspace_client_id=int(workspace_id),
            refresh=refresh,
        )
    except (TypeError, ValueError):
        raise SelectionError("line_erp.target_required", 422) from None
    except target_preflight.TargetNotReady as exc:
        raise SelectionError(
            str(exc.result.get("block_reason") or "line_erp.target_not_ready"),
            readiness=exc.result,
        ) from exc
    target = dict(readiness["target"])
    adapter = str(target.get("adapter") or "").lower()
    if adapter == "express":
        posting_kind = str(values.get("posting_kind") or "").lower()
        if posting_kind not in {"stock", "service"}:
            raise SelectionError("line_erp.posting_kind_required", 422)
        payment = None
    elif adapter == "mrerp":
        payment = str(values.get("payment") or "").lower()
        allowed = {"credit"} if direction == "purchase" else {"cash", "credit"}
        if payment not in allowed:
            raise SelectionError("line_erp.payment_required", 422)
        posting_kind = None
    else:
        raise SelectionError("line_erp.adapter_not_supported", 422)
    normalized = {
        "endpoint_id": str(target["endpoint_id"]),
        "workspace_client_id": int(target["workspace_client_id"]),
        "adapter": adapter,
        "target_label": str(target.get("label") or "")[:200],
        "direction": direction,
        "mode": direction,
        "posting_kind": posting_kind,
        "payment": payment,
        "posting_mode": posting_kind or payment,
    }
    return readiness, normalized


def apply_to_records(records: list[dict[str, Any]], selection: dict[str, Any]) -> None:
    for record in records:
        pages = record.get("pages")
        if not isinstance(pages, list):
            continue
        for page in pages:
            if not isinstance(page, dict):
                continue
            fields = page.get("fields")
            if not isinstance(fields, dict):
                fields = {}
                page["fields"] = fields
            fields["direction"] = selection["direction"]
            if selection["adapter"] != "express":
                continue
            items = fields.get("items")
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and not item.get("posting_kind"):
                    item["posting_kind"] = selection["posting_kind"]


def update_scope(
    binding: dict[str, Any], history_ids: list[str], selection: dict[str, Any]
) -> None:
    with db.get_cursor_rls(
        tenant_id=str(binding["tenant_id"]),
        user_id=str(binding["user_id"]),
        commit=True,
    ) as cur:
        cur.execute(
            "UPDATE ocr_history SET workspace_client_id = %s, posting_kind = %s, "
            "updated_at = NOW() WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
            "AND user_id = %s::uuid AND staged = TRUE",
            (
                selection["workspace_client_id"],
                selection.get("posting_kind"),
                history_ids,
                str(binding["tenant_id"]),
                str(binding["user_id"]),
            ),
        )
        if cur.rowcount != len(set(history_ids)):
            raise SelectionError("line_erp.draft_save_failed")
    payment = selection.get("payment")
    if payment:
        from services.ocr_history.posting_manual import update_history_posting_manual

        for history_id in history_ids:
            result = update_history_posting_manual(
                str(binding["user_id"]),
                history_id,
                str(binding["tenant_id"]),
                payment=payment,
            )
            if not result.ok:
                raise SelectionError("line_erp.draft_save_failed")


__all__ = ["SelectionError", "apply_to_records", "from_payload", "normalize", "update_scope"]
