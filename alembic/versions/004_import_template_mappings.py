"""import_template_mappings · 通用模板学习层 列映射记忆表 · ADR-006

新模板第一次确认列对应后存这里,下次同格式(header_signature 命中)自动套用,不再问用户/不再失败。
mapping_json 是与 bank_recon_v2._parse_stmt_sheet 兼容的 col_map:
    {date:i, description:i, withdrawal:i, deposit:i, balance:i, amount:i}(statement)
    {date:i, doc_no:i, account:i, description:i, debit:i, credit:i, balance:i}(gl)

按 (tenant, document_type, header_signature) 唯一 · 租户隔离(A 公司确认不泄给 B 公司)。

Revision ID: 004_import_template_mappings
Revises: 003_recon_jobs
Create Date: 2026-05-24
"""

from typing import Sequence, Union

from alembic import op

revision: str = "004_import_template_mappings"
down_revision: Union[str, Sequence[str], None] = "003_recon_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("""
        CREATE TABLE IF NOT EXISTS import_template_mappings (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id        UUID NOT NULL,
            document_type    TEXT NOT NULL,            -- statement | gl
            header_signature TEXT NOT NULL,
            template_name    TEXT,
            sheet_hint       TEXT,
            mapping_json     JSONB NOT NULL,
            sample_headers   JSONB,
            source           TEXT,                     -- local | ai | user
            created_by       UUID,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, document_type, header_signature)
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_import_tmpl_tenant_type "
        "ON import_template_mappings (tenant_id, document_type)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS import_template_mappings")
