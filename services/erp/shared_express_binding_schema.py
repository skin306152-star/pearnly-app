# -*- coding: utf-8 -*-
"""Additive typed foundation for one bound and one live Express profile."""

from __future__ import annotations

from core import db

SHARED_EXPRESS_BINDING_COLUMNS = (
    ("bound_account_set", "TEXT", "text", False, None),
    ("bound_profile_key", "TEXT", "text", False, None),
    ("live_account_set", "TEXT", "text", False, None),
    ("live_profile_key", "TEXT", "text", False, None),
    ("agent_last_seen_at", "TIMESTAMPTZ", "timestamp with time zone", False, None),
    ("agent_version", "TEXT", "text", False, None),
    ("binding_generation", "BIGINT NOT NULL DEFAULT 0", "bigint", True, "0"),
)


def _column_contract_ddl(columns) -> str:
    values = ",\n        ".join(
        "("
        + ", ".join(
            (
                f"'{name}'",
                f"'{catalog_type}'",
                "TRUE" if not_null else "FALSE",
                "NULL" if default is None else f"'{default}'",
            )
        )
        + ")"
        for name, _add_type, catalog_type, not_null, default in columns
    )
    return f"""
DO $pearnly$
DECLARE
    v_mismatch TEXT;
BEGIN
    WITH expected(column_name, type_name, not_null, default_expr) AS (
        VALUES
        {values}
    )
    SELECT string_agg(expected.column_name, ', ' ORDER BY expected.column_name)
      INTO v_mismatch
      FROM expected
      LEFT JOIN pg_attribute column_meta
        ON column_meta.attrelid = 'erp_endpoints'::regclass
       AND column_meta.attname = expected.column_name
       AND column_meta.attnum > 0
       AND NOT column_meta.attisdropped
      LEFT JOIN pg_attrdef default_meta
        ON default_meta.adrelid = column_meta.attrelid
       AND default_meta.adnum = column_meta.attnum
     WHERE column_meta.attname IS NULL
        OR lower(format_type(column_meta.atttypid, column_meta.atttypmod))
           IS DISTINCT FROM expected.type_name
        OR column_meta.attnotnull IS DISTINCT FROM expected.not_null
        OR regexp_replace(
               regexp_replace(
                   lower(pg_get_expr(default_meta.adbin, default_meta.adrelid)),
                   '::(bigint|int8)', '', 'g'
               ),
               '[[:space:]()]', '', 'g'
           ) IS DISTINCT FROM expected.default_expr;
    IF v_mismatch IS NOT NULL THEN
        RAISE EXCEPTION
            'erp_endpoints binding column contract mismatch: %', v_mismatch;
    END IF;
END
$pearnly$
"""


SHARED_EXPRESS_BINDING_COLUMN_DDL = tuple(
    f"ALTER TABLE erp_endpoints ADD COLUMN IF NOT EXISTS {name} {add_type}"
    for name, add_type, _catalog_type, _not_null, _default in (SHARED_EXPRESS_BINDING_COLUMNS)
)
SHARED_EXPRESS_BINDING_COLUMN_CONTRACT_DDL = _column_contract_ddl(SHARED_EXPRESS_BINDING_COLUMNS)


def _check_constraint(name: str, expression: str, normalized_definition: str) -> tuple[str, str]:
    contract = f"""
DO $pearnly$
DECLARE
    v_definition TEXT;
BEGIN
    SELECT regexp_replace(lower(pg_get_constraintdef(oid)), '[[:space:]()]', '', 'g')
      INTO v_definition
      FROM pg_constraint
     WHERE conrelid = 'erp_endpoints'::regclass
       AND conname = '{name}';
    IF NOT FOUND THEN
        ALTER TABLE erp_endpoints
            ADD CONSTRAINT {name} CHECK ({expression}) NOT VALID;
    ELSIF v_definition <> '{normalized_definition}' THEN
        RAISE EXCEPTION '{name} does not match the F1-B3B1 contract';
    END IF;
END
$pearnly$
"""
    return contract, f"ALTER TABLE erp_endpoints VALIDATE CONSTRAINT {name}"


SHARED_EXPRESS_BINDING_DDL = (
    SHARED_EXPRESS_BINDING_COLUMN_DDL
    + (SHARED_EXPRESS_BINDING_COLUMN_CONTRACT_DDL,)
    + _check_constraint(
        "erp_endpoints_bound_profile_pair_chk",
        "(bound_account_set IS NULL) = (bound_profile_key IS NULL)",
        "checkbound_account_setisnull=bound_profile_keyisnull",
    )
    + _check_constraint(
        "erp_endpoints_live_profile_pair_chk",
        "(live_account_set IS NULL) = (live_profile_key IS NULL)",
        "checklive_account_setisnull=live_profile_keyisnull",
    )
    + _check_constraint(
        "erp_endpoints_binding_generation_chk",
        "binding_generation >= 0",
        "checkbinding_generation>=0",
    )
)


def apply_shared_express_binding_foundation(cur) -> None:
    """Apply the idempotent B3B1 DDL on an existing cursor."""
    for statement in SHARED_EXPRESS_BINDING_DDL:
        cur.execute(statement)


def ensure_shared_express_binding_foundation() -> None:
    """Mirror the migration on deployments that do not execute Alembic."""
    with db.get_cursor(commit=True) as cur:
        apply_shared_express_binding_foundation(cur)


__all__ = [
    "SHARED_EXPRESS_BINDING_COLUMNS",
    "SHARED_EXPRESS_BINDING_COLUMN_CONTRACT_DDL",
    "SHARED_EXPRESS_BINDING_DDL",
    "apply_shared_express_binding_foundation",
    "ensure_shared_express_binding_foundation",
]
