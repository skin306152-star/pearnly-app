# -*- coding: utf-8 -*-
"""Atomic publish/read store for versioned ERP target projections."""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from services.erp.target_projection_contract import (
    ENTITY_TYPES,
    NormalizedProjection,
    ProjectionContractError,
    normalize_collector,
    normalize_observed_at,
    normalize_projection,
    normalize_refresh_status,
    normalize_scope,
)

_COMPONENT_REVISIONS = {
    "account_sets": "account_sets_revision",
    "masters": "master_revision",
    "form_schema": "form_schema_revision",
    "capabilities": "capability_revision",
}


class ProjectionStoreError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _row_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "keys"):
        return dict(row)
    raise ProjectionStoreError("erp.target_projection_db_contract")


def _json(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    if isinstance(value, str):
        return json.loads(value)
    return value


def _lock_endpoint(cur, tenant_id: str, endpoint_id: str, adapter: str | None = None) -> dict:
    cur.execute(
        "SELECT id, tenant_id, adapter FROM erp_endpoints "
        "WHERE id = %s AND tenant_id = %s AND enabled = TRUE FOR UPDATE",
        (endpoint_id, tenant_id),
    )
    endpoint = _row_dict(cur.fetchone())
    if not endpoint:
        raise ProjectionStoreError("erp.endpoint_not_found")
    if adapter and str(endpoint.get("adapter") or "").lower() != adapter:
        raise ProjectionStoreError("erp.target_projection_adapter_mismatch")
    return endpoint


def _head_for_update(
    cur, tenant_id: str, endpoint_id: str, scope_kind: str, scope_key: str
) -> dict[str, Any]:
    cur.execute(
        """
        SELECT h.*, s.source_hash, s.component_hashes
        FROM erp_target_projection_heads h
        LEFT JOIN erp_target_projection_snapshots s ON s.id = h.current_snapshot_id
        WHERE h.tenant_id = %s AND h.endpoint_id = %s
          AND h.scope_kind = %s AND h.scope_key = %s
        FOR UPDATE OF h
        """,
        (tenant_id, endpoint_id, scope_kind, scope_key),
    )
    return _row_dict(cur.fetchone())


def _next_component_revisions(
    head: Mapping[str, Any], projection: NormalizedProjection
) -> dict[str, int]:
    previous_hashes = _json(head.get("component_hashes"), {})
    revisions: dict[str, int] = {}
    for component, column in _COMPONENT_REVISIONS.items():
        previous = int(head.get(column) or 0)
        changed = previous_hashes.get(component) != projection.component_hashes[component]
        revisions[column] = previous + 1 if changed or previous == 0 else previous
    return revisions


def _flatten_items(projection: NormalizedProjection) -> list[dict[str, Any]]:
    return [
        {"entity_type": entity_type, **item}
        for entity_type in ENTITY_TYPES
        for item in projection.masters[entity_type]
    ]


def publish_with_cursor(
    cur,
    *,
    tenant_id: str,
    endpoint_id: str,
    projection: NormalizedProjection,
) -> dict[str, Any]:
    tenant_id = str(tenant_id)
    endpoint_id = str(endpoint_id)
    _lock_endpoint(cur, tenant_id, endpoint_id, projection.adapter)
    head = _head_for_update(
        cur, tenant_id, endpoint_id, projection.scope_kind, projection.scope_key
    )
    if head.get("current_snapshot_id") and head.get("source_hash") == projection.source_hash:
        cur.execute(
            """
            UPDATE erp_target_projection_heads
            SET last_refresh_status = 'fresh', last_refresh_error_code = NULL,
                last_refresh_source = %s::jsonb, last_refresh_attempted_at = %s,
                last_observed_at = %s, updated_at = now()
            WHERE tenant_id = %s AND endpoint_id = %s AND scope_kind = %s AND scope_key = %s
            """,
            (
                json.dumps(projection.collector),
                projection.observed_at,
                projection.observed_at,
                tenant_id,
                endpoint_id,
                projection.scope_kind,
                projection.scope_key,
            ),
        )
        return {
            "published": False,
            "snapshot_id": str(head["current_snapshot_id"]),
            "revision": int(head["current_revision"]),
            **{column: int(head[column]) for column in _COMPONENT_REVISIONS.values()},
            "source_hash": projection.source_hash,
        }

    revision = int(head.get("current_revision") or 0) + 1
    component_revisions = _next_component_revisions(head, projection)
    cur.execute(
        """
        INSERT INTO erp_target_projection_snapshots (
            tenant_id, endpoint_id, scope_kind, scope_key, revision,
            account_sets_revision, master_revision, form_schema_revision, capability_revision,
            source_hash, component_hashes, observed_at, adapter, collector,
            account_sets, form_schema, capabilities, entity_counts
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s::jsonb, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb
        ) RETURNING id
        """,
        (
            tenant_id,
            endpoint_id,
            projection.scope_kind,
            projection.scope_key,
            revision,
            component_revisions["account_sets_revision"],
            component_revisions["master_revision"],
            component_revisions["form_schema_revision"],
            component_revisions["capability_revision"],
            projection.source_hash,
            json.dumps(projection.component_hashes),
            projection.observed_at,
            projection.adapter,
            json.dumps(projection.collector),
            json.dumps(projection.account_sets, ensure_ascii=False),
            json.dumps(projection.form_schema, ensure_ascii=False),
            json.dumps(projection.capabilities, ensure_ascii=False),
            json.dumps(projection.entity_counts),
        ),
    )
    snapshot_id = str(_row_dict(cur.fetchone())["id"])
    items = _flatten_items(projection)
    if items:
        cur.execute(
            """
            INSERT INTO erp_target_projection_items (
                snapshot_id, tenant_id, endpoint_id, entity_type,
                source_id, label, active, attributes
            )
            SELECT %s, %s, %s, item.entity_type, item.source_id,
                   item.label, item.active, item.attributes
            FROM jsonb_to_recordset(%s::jsonb) AS item(
                entity_type text, source_id text, label text, active boolean, attributes jsonb
            )
            """,
            (
                snapshot_id,
                tenant_id,
                endpoint_id,
                json.dumps(items, ensure_ascii=False),
            ),
        )
    cur.execute(
        """
        INSERT INTO erp_target_projection_heads (
            tenant_id, endpoint_id, scope_kind, scope_key, current_snapshot_id,
            current_revision, account_sets_revision, master_revision,
            form_schema_revision, capability_revision, last_refresh_status,
            last_refresh_error_code, last_refresh_source,
            last_refresh_attempted_at, last_observed_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            'fresh', NULL, %s::jsonb, %s, %s
        )
        ON CONFLICT (tenant_id, endpoint_id, scope_kind, scope_key) DO UPDATE SET
            current_snapshot_id = EXCLUDED.current_snapshot_id,
            current_revision = EXCLUDED.current_revision,
            account_sets_revision = EXCLUDED.account_sets_revision,
            master_revision = EXCLUDED.master_revision,
            form_schema_revision = EXCLUDED.form_schema_revision,
            capability_revision = EXCLUDED.capability_revision,
            last_refresh_status = 'fresh', last_refresh_error_code = NULL,
            last_refresh_source = EXCLUDED.last_refresh_source,
            last_refresh_attempted_at = EXCLUDED.last_refresh_attempted_at,
            last_observed_at = EXCLUDED.last_observed_at, updated_at = now()
        """,
        (
            tenant_id,
            endpoint_id,
            projection.scope_kind,
            projection.scope_key,
            snapshot_id,
            revision,
            component_revisions["account_sets_revision"],
            component_revisions["master_revision"],
            component_revisions["form_schema_revision"],
            component_revisions["capability_revision"],
            json.dumps(projection.collector),
            projection.observed_at,
            projection.observed_at,
        ),
    )
    return {
        "published": True,
        "snapshot_id": snapshot_id,
        "revision": revision,
        **component_revisions,
        "source_hash": projection.source_hash,
    }


def publish_projection(
    *, tenant_id: str, endpoint_id: str, observation: Mapping[str, Any]
) -> dict[str, Any]:
    from core import db

    projection = normalize_projection(observation)
    with db.get_cursor(commit=True) as cur:
        return publish_with_cursor(
            cur, tenant_id=tenant_id, endpoint_id=endpoint_id, projection=projection
        )


def record_refresh_state_with_cursor(
    cur,
    *,
    tenant_id: str,
    endpoint_id: str,
    account_set_key: Any,
    status: Any,
    observed_at: Any,
    collector: Any = None,
    error_code: Any = None,
) -> dict[str, Any]:
    tenant_id = str(tenant_id)
    endpoint_id = str(endpoint_id)
    normalized_status = normalize_refresh_status(status)
    normalized_observed_at = normalize_observed_at(observed_at)
    normalized_collector = normalize_collector(collector)
    normalized_error = str(error_code or "").strip()[:200] or None
    scope_kind, scope_key = normalize_scope(account_set_key)
    _lock_endpoint(cur, tenant_id, endpoint_id)
    cur.execute(
        """
        INSERT INTO erp_target_projection_heads (
            tenant_id, endpoint_id, scope_kind, scope_key, last_refresh_status,
            last_refresh_error_code, last_refresh_source, last_refresh_attempted_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
        ON CONFLICT (tenant_id, endpoint_id, scope_kind, scope_key) DO UPDATE SET
            last_refresh_status = EXCLUDED.last_refresh_status,
            last_refresh_error_code = EXCLUDED.last_refresh_error_code,
            last_refresh_source = EXCLUDED.last_refresh_source,
            last_refresh_attempted_at = EXCLUDED.last_refresh_attempted_at,
            updated_at = now()
        """,
        (
            tenant_id,
            endpoint_id,
            scope_kind,
            scope_key,
            normalized_status,
            normalized_error,
            json.dumps(normalized_collector),
            normalized_observed_at,
        ),
    )
    return {
        "scope_kind": scope_kind,
        "scope_key": scope_key,
        "status": normalized_status,
        "observed_at": normalized_observed_at,
        "error_code": normalized_error,
    }


def record_refresh_state(**kwargs) -> dict[str, Any]:
    from core import db

    with db.get_cursor(commit=True) as cur:
        return record_refresh_state_with_cursor(cur, **kwargs)


def _entity_filter(entity_types: Iterable[str] | None) -> tuple[str, ...]:
    requested = tuple(dict.fromkeys(str(value).strip().lower() for value in entity_types or ()))
    if set(requested) - set(ENTITY_TYPES):
        raise ProjectionContractError("erp.target_projection_unknown_entity")
    return requested


def load_state_with_cursor(
    cur,
    *,
    tenant_id: str,
    endpoint_id: str,
    account_set_key: Any = None,
    entity_types: Iterable[str] | None = None,
) -> dict[str, Any] | None:
    scope_kind, scope_key = normalize_scope(account_set_key)
    cur.execute(
        """
        SELECT h.current_snapshot_id, h.current_revision, h.account_sets_revision,
               h.master_revision, h.form_schema_revision, h.capability_revision,
               h.last_refresh_status, h.last_refresh_error_code,
               h.last_refresh_source, h.last_refresh_attempted_at,
               h.last_observed_at, h.updated_at,
               s.source_hash, s.observed_at AS snapshot_observed_at, s.adapter,
               s.collector, s.account_sets, s.form_schema, s.capabilities, s.entity_counts
        FROM erp_target_projection_heads h
        LEFT JOIN erp_target_projection_snapshots s ON s.id = h.current_snapshot_id
        WHERE h.tenant_id = %s AND h.endpoint_id = %s
          AND h.scope_kind = %s AND h.scope_key = %s
        """,
        (str(tenant_id), str(endpoint_id), scope_kind, scope_key),
    )
    row = _row_dict(cur.fetchone())
    if not row:
        return None
    state: dict[str, Any] = {
        "endpoint_id": str(endpoint_id),
        "scope_kind": scope_kind,
        "scope_key": scope_key,
        "freshness": {
            "status": row["last_refresh_status"],
            "error_code": row.get("last_refresh_error_code"),
            "attempted_at": row.get("last_refresh_attempted_at"),
            "observed_at": row.get("last_observed_at"),
            "source": _json(row.get("last_refresh_source"), {}),
            "updated_at": row.get("updated_at"),
        },
        "snapshot": None,
    }
    snapshot_id = row.get("current_snapshot_id")
    if not snapshot_id:
        return state
    requested = _entity_filter(entity_types)
    masters = {entity: [] for entity in requested}
    if requested:
        cur.execute(
            """
            SELECT entity_type, source_id, label, active, attributes
            FROM erp_target_projection_items
            WHERE tenant_id = %s AND endpoint_id = %s AND snapshot_id = %s
              AND entity_type = ANY(%s)
            ORDER BY entity_type, source_id
            """,
            (str(tenant_id), str(endpoint_id), snapshot_id, list(requested)),
        )
        for item in cur.fetchall():
            item = _row_dict(item)
            masters[item.pop("entity_type")].append(
                {**item, "attributes": _json(item.get("attributes"), {})}
            )
    state["snapshot"] = {
        "snapshot_id": str(snapshot_id),
        "revision": int(row["current_revision"]),
        "account_sets_revision": int(row["account_sets_revision"]),
        "master_revision": int(row["master_revision"]),
        "form_schema_revision": int(row["form_schema_revision"]),
        "capability_revision": int(row["capability_revision"]),
        "source_hash": row["source_hash"],
        "observed_at": row["snapshot_observed_at"],
        "adapter": row["adapter"],
        "collector": _json(row.get("collector"), {}),
        "account_sets": _json(row.get("account_sets"), []),
        "form_schema": _json(row.get("form_schema"), {"fields": []}),
        "capabilities": _json(row.get("capabilities"), {"actions": []}),
        "entity_counts": _json(row.get("entity_counts"), {}),
        "masters": masters,
    }
    return state


def load_state(
    *,
    tenant_id: str,
    user_id: str,
    endpoint_id: str,
    account_set_key: Any = None,
    entity_types: Iterable[str] | None = None,
) -> dict[str, Any] | None:
    from core import db

    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
        return load_state_with_cursor(
            cur,
            tenant_id=tenant_id,
            endpoint_id=endpoint_id,
            account_set_key=account_set_key,
            entity_types=entity_types,
        )


__all__ = [
    "ProjectionStoreError",
    "load_state",
    "load_state_with_cursor",
    "publish_projection",
    "publish_with_cursor",
    "record_refresh_state",
    "record_refresh_state_with_cursor",
]
