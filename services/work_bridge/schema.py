"""Schema applied by the existing serialized Cloud Run schema job."""

TABLES = {
    "work_bridge_sessions": """
        CREATE TABLE IF NOT EXISTS work_bridge_sessions (
            session_hash text PRIMARY KEY,
            tenant_id uuid REFERENCES tenants(id),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            parent_jti text NOT NULL,
            parent_iat bigint NOT NULL,
            expires_at timestamptz NOT NULL,
            revoked_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """,
    "work_bridge_tickets": """
        CREATE TABLE IF NOT EXISTS work_bridge_tickets (
            ticket_hash text PRIMARY KEY,
            tenant_id uuid REFERENCES tenants(id),
            session_hash text NOT NULL REFERENCES work_bridge_sessions(session_hash) ON DELETE CASCADE,
            browser_state text NOT NULL,
            expires_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """,
    "work_bridge_member_requests": """
        CREATE TABLE IF NOT EXISTS work_bridge_member_requests (
            tenant_id uuid NOT NULL REFERENCES tenants(id),
            request_id text NOT NULL,
            actor_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account text NOT NULL,
            email text,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, request_id)
        )
    """,
}


def migrate_schema() -> None:
    from core import db

    with db.get_cursor(commit=True) as cur:
        apply(cur)


def apply(cur) -> None:
    from core.rls import apply_tenant_rls

    for name, ddl in TABLES.items():
        cur.execute(ddl)
        apply_tenant_rls(cur, name)
    for table, index in (("sessions", "session"), ("tickets", "ticket")):
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS work_bridge_{index}_expiry "
            f"ON work_bridge_{table} (expires_at)"
        )
