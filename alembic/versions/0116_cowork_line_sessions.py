"""Add the independent Cowork LINE conversation session store."""

from alembic import op

revision = "0116_cowork_line_sessions"
down_revision = "0115_cowork_line_friendship"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
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
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_cowork_line_sessions_expiry "
        "ON cowork_line_sessions (expires_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cowork_line_sessions")
