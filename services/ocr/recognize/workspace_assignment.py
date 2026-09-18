"""Workspace assignment helpers for OCR persistence."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException

from core import db
from core.route_helpers import _tid
from services.workspace import document_assignment

WorkspaceAssignmentError = document_assignment.WorkspaceAssignmentError
logger = logging.getLogger("mr-pilot")


def _policy(user: dict):
    if user.get("is_super_admin"):
        return None
    from services.authz.resolver import resolve

    return resolve(user)


def _require_create(user: dict, authz=None) -> None:
    if user.get("is_super_admin"):
        return
    authz = authz or _policy(user)
    if not authz.has("settings.workspace.manage") or authz.scope_mode == "assigned":
        raise HTTPException(403, detail="authz.forbidden")


def _require_workspace(user: dict, workspace_client_id: int, authz=None) -> None:
    if user.get("is_super_admin"):
        return
    authz = authz or _policy(user)
    if authz is None or not authz.allows_workspace(workspace_client_id):
        raise HTTPException(404, detail="authz.not_found")


def _log_created(user: dict, decision: dict, source: str, direction: str) -> None:
    try:
        from services.audit import store as audit_store

        audit_store.insert_operation_log(
            _tid(user),
            str(user["id"]),
            user.get("username"),
            bool(user.get("is_super_admin")),
            "workspace.client.auto_create",
            target_type="workspace_client",
            target_id=str(decision["workspace_client_id"]),
            target_name=decision.get("workspace_name"),
            details={"source": source, "direction": direction},
        )
    except Exception as exc:
        logger.warning("auto-created workspace audit failed: %s", exc)


def _archive_empty_created(user: dict, workspace_ids: list[int]) -> list[int]:
    ids = sorted({int(value) for value in workspace_ids if value})
    if not ids:
        return []
    tenant_id = _tid(user)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"]), commit=True) as cur:
            scope = "wc.tenant_id = %s::uuid" if tenant_id else "wc.tenant_id IS NULL"
            params: list[Any] = [ids, str(user["id"])]
            if tenant_id:
                params.append(tenant_id)
            cur.execute(
                "UPDATE workspace_clients AS wc SET is_active = FALSE, updated_at = NOW() "
                "WHERE wc.id = ANY(%s::bigint[]) AND wc.user_id = %s::uuid AND "
                f"{scope} AND wc.is_active = TRUE "
                "AND NOT EXISTS (SELECT 1 FROM ocr_history h "
                "WHERE h.workspace_client_id = wc.id) "
                "AND NOT EXISTS (SELECT 1 FROM purchase_docs p "
                "WHERE p.workspace_client_id = wc.id) "
                "AND NOT EXISTS (SELECT 1 FROM sales_documents s "
                "WHERE s.seller_workspace_client_id = wc.id) "
                "AND NOT EXISTS (SELECT 1 FROM erp_push_logs l "
                "WHERE l.workspace_client_id = wc.id) "
                "AND NOT EXISTS (SELECT 1 FROM erp_endpoints e "
                "WHERE e.workspace_client_id = wc.id) RETURNING wc.id",
                tuple(params),
            )
            return [int(row["id"]) for row in cur.fetchall() or []]
    except Exception as exc:
        logger.error("auto-created workspace compensation failed ids=%s: %s", ids, exc)
        return []


def _route_existing(fields: dict, user: dict, authz) -> dict | None:
    tenant_id = _tid(user)
    matches: dict[int, dict] = {}
    for party, matcher in (
        ("seller", db.match_workspace_for_seller),
        ("buyer", db.match_workspace_for_buyer),
    ):
        match = matcher(
            fields.get(f"{party}_tax"),
            fields.get(f"{party}_name"),
            str(user["id"]),
            tenant_id,
        )
        candidate = match if isinstance(match, dict) else {}
        action = str(candidate.get("action") or "").strip().lower()
        if candidate.get("reason") == "lookup_error":
            raise WorkspaceAssignmentError("workspace_lookup_failed")
        if action == "multi":
            raise WorkspaceAssignmentError("workspace_ambiguous")
        if action in {"", "none"}:
            continue
        if action not in {"assigned", "unbound"}:
            raise WorkspaceAssignmentError("workspace_lookup_failed")
        try:
            workspace_id = int(candidate.get("workspace_client_id"))
        except (TypeError, ValueError) as exc:
            raise WorkspaceAssignmentError("workspace_lookup_failed") from exc
        if workspace_id <= 0:
            raise WorkspaceAssignmentError("workspace_lookup_failed")
        matches.setdefault(workspace_id, candidate)

    if len(matches) > 1:
        raise WorkspaceAssignmentError("workspace_ambiguous")
    if not matches:
        return None

    workspace_id, match = next(iter(matches.items()))
    _require_workspace(user, workspace_id, authz)
    return {
        "workspace_client_id": workspace_id,
        "action": "matched",
        "workspace_name": match.get("workspace_name"),
    }


def _has_party_identity(fields: dict) -> bool:
    values = fields if isinstance(fields, dict) else {}
    return any(
        str(values.get(key) or "").strip()
        for key in (
            "seller_name",
            "seller_tax",
            "seller_tax_id",
            "buyer_name",
            "buyer_tax",
            "buyer_tax_id",
        )
    )


def _subject_of(plan: dict) -> dict:
    subject = plan.get("subject")
    return subject if isinstance(subject, dict) else {}


def _subject_name(plan: dict) -> str:
    """公司名归一(大小写/空白折叠)· 同名 = 同一家公司,用于本批内归组。"""
    return " ".join(str(_subject_of(plan).get("name") or "").casefold().split())


def _subject_tax(plan: dict) -> str:
    return str(_subject_of(plan).get("tax_id") or "")


def _same_company(left: str, right: str) -> bool:
    """税号相同、或任一方没读到(税号读不出来的页)时视作同一家公司。

    两家真不同的公司各有非空且不同的税号 → 不收拢(该分开建就分开建)。
    """
    return left == right or not left or not right


def _canonical_by_name(plans: list) -> dict[int, int]:
    """按公司名归组 → {同组待建账套的计划序号: 组内规范计划序号}。

    同一份 PDF 里,同一家公司的税号有可能某页读得出来、某页读不出来。旧行为按
    ("tax")/("name") 两个不同身份键各自处理,同一家公司于是出现两个账套;下次上传时
    名字匹配到两个 → 整批 409 workspace_ambiguous。

    这里让"要新建账套"的计划先看同批同名的其他计划:同组已有结论(无论是刚建还是命中了
    某个已有账套)就复用,不再建第二个。组内规范计划优先取带税号的那页 —— 用它的税号
    命中的账套最可靠。同名但各自有不同非空税号 = 两家公司,不归组。
    """
    groups: dict[str, list[int]] = {}
    for index, plan in enumerate(plans):
        if not isinstance(plan, dict):
            continue
        name = _subject_name(plan)
        if name:
            groups.setdefault(name, []).append(index)
    followers: dict[int, int] = {}
    for indexes in groups.values():
        with_tax = [index for index in indexes if _subject_tax(plans[index])]
        head = with_tax[0] if with_tax else indexes[0]
        for index in indexes:
            if index == head or plans[index].get("action") != "create":
                continue
            if _same_company(_subject_tax(plans[index]), _subject_tax(plans[head])):
                followers[index] = head
    return followers


def resolve_batch(
    assignments: list[tuple[dict, str | None]],
    user: dict,
    source: str,
    *,
    fallback_workspace_id: int | None,
) -> list[dict | None]:
    """Validate the whole OCR batch before creating any missing workspaces."""
    authz = _policy(user)
    authorize = lambda workspace_id: _require_workspace(user, workspace_id, authz)
    plans: list[dict | None] = []
    for fields, direction in assignments:
        if not direction:
            if fallback_workspace_id is not None:
                authorize(int(fallback_workspace_id))
            routed = _route_existing(fields, user, authz)
            if routed is None:
                code = (
                    "direction_required"
                    if _has_party_identity(fields)
                    else "workspace_subject_missing"
                )
                raise WorkspaceAssignmentError(code)
            plans.append(routed)
            continue
        plans.append(
            document_assignment.prepare_assignment(
                fields,
                direction,
                str(user["id"]),
                _tid(user),
                require_create_actor=lambda: _require_create(user, authz),
                authorize_workspace=authorize,
            )
        )

    decisions: list[dict | None] = []
    created_ids: list[int] = []
    missing_cache: dict[tuple[str, str], dict] = {}
    by_name: dict[str, dict] = {}
    canonical_by_name = _canonical_by_name(plans)

    def _materialize(plan: dict) -> dict:
        decision = document_assignment.materialize_assignment(
            plan,
            str(user["id"]),
            _tid(user),
            authorize_workspace=authorize,
        )
        name = _subject_name(plan)
        tax_id = _subject_tax(plan)
        if plan.get("action") == "create":
            missing_cache[("tax", tax_id) if tax_id else ("name", name)] = decision
        if name:
            # 命中已有账套的计划也要登记:同批同名、但税号读不出来的那页靠它复用,不再新建
            by_name.setdefault(name, decision)
        if decision.get("action") == "created":
            created_ids.append(int(decision["workspace_client_id"]))
            _log_created(user, decision, source, str(plan.get("direction") or ""))
        return decision

    try:
        for index, plan in enumerate(plans):
            if plan is None:
                decisions.append(None)
                continue
            tax_id = _subject_tax(plan)
            normalized_name = _subject_name(plan)
            cache_key = ("tax", tax_id) if tax_id else ("name", normalized_name)
            if plan.get("action") != "create":
                decision = _materialize(plan)
            elif cache_key in missing_cache:
                decision = missing_cache[cache_key]
            else:
                head_index = canonical_by_name.get(index)
                if head_index is None:
                    decision = _materialize(plan)
                else:
                    # 同名同公司:复用本批已定下的那个账套,不再建第二个
                    decision = dict(by_name.get(normalized_name) or _materialize(plans[head_index]))
                    missing_cache[cache_key] = decision
            decisions.append(decision)
    except Exception:
        _archive_empty_created(user, created_ids)
        raise
    return decisions


def cleanup_failed_batch(user: dict, history_ids: list[str], decisions: list[dict | None]) -> None:
    if history_ids:
        try:
            deleted, _paths = db.delete_ocr_history_with_pdf_paths(
                str(user["id"]), history_ids, tenant_id=_tid(user)
            )
            if deleted != len(history_ids):
                logger.error(
                    "OCR batch compensation incomplete deleted=%s expected=%s",
                    deleted,
                    len(history_ids),
                )
        except Exception as exc:
            logger.error("OCR history compensation failed ids=%s: %s", history_ids, exc)
    created_ids = [
        int(decision["workspace_client_id"])
        for decision in decisions
        if decision and decision.get("action") == "created"
    ]
    _archive_empty_created(user, created_ids)


def resolve_or_create(fields: dict, direction: str, user: dict, source: str) -> dict:
    authz = _policy(user)
    decision = document_assignment.resolve_or_create(
        fields,
        direction,
        str(user["id"]),
        _tid(user),
        require_create_actor=lambda: _require_create(user, authz),
        authorize_workspace=lambda workspace_id: _require_workspace(user, workspace_id, authz),
    )
    if decision["action"] == "created":
        _log_created(user, decision, source, direction)
    return decision


def route_existing(fields: dict, user: dict) -> dict | None:
    authz = _policy(user)
    return _route_existing(fields, user, authz)


__all__ = [
    "WorkspaceAssignmentError",
    "cleanup_failed_batch",
    "resolve_batch",
    "resolve_or_create",
    "route_existing",
]
