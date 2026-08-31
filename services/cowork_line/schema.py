"""Idempotent schema bootstrap for Cowork LINE identity and workflow state."""

from __future__ import annotations

from core import db
from core.rls import apply_tenant_rls

DDL = (
    """
    CREATE TABLE IF NOT EXISTS cowork_line_connect_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        membership_id UUID NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        token_hash TEXT NOT NULL UNIQUE,
        expires_at TIMESTAMPTZ NOT NULL,
        used_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cowork_line_connect_tokens_active
    ON cowork_line_connect_tokens (membership_id, expires_at DESC)
    WHERE used_at IS NULL
    """,
    """
    CREATE TABLE IF NOT EXISTS cowork_line_identities (
        membership_id UUID PRIMARY KEY REFERENCES memberships(id) ON DELETE CASCADE,
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        line_user_id TEXT NOT NULL UNIQUE,
        display_name TEXT,
        picture_url TEXT,
        friendship_ready BOOLEAN NOT NULL DEFAULT FALSE,
        friendship_checked_at TIMESTAMPTZ,
        connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_seen_at TIMESTAMPTZ,
        revoked_at TIMESTAMPTZ
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cowork_line_identities_tenant
    ON cowork_line_identities (tenant_id)
    """,
    """
    ALTER TABLE cowork_line_identities
    ADD COLUMN IF NOT EXISTS friendship_ready BOOLEAN NOT NULL DEFAULT FALSE
    """,
    """
    ALTER TABLE cowork_line_identities
    ADD COLUMN IF NOT EXISTS friendship_checked_at TIMESTAMPTZ
    """,
    """
    CREATE TABLE IF NOT EXISTS cowork_line_sessions (
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        line_user_id TEXT NOT NULL,
        state TEXT NOT NULL,
        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (tenant_id, line_user_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cowork_line_sessions_expiry
    ON cowork_line_sessions (expires_at)
    """,
)


def ensure_schema() -> None:
    with db.get_cursor(commit=True) as cur:
        for statement in DDL:
            cur.execute(statement)
        apply_tenant_rls(
            cur,
            "cowork_line_connect_tokens",
            "cowork_line_identities",
            "cowork_line_sessions",
        )
