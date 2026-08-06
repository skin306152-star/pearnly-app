# -*- coding: utf-8 -*-
"""画像卡智能判断:client_tax_profiles 加 field_meta JSONB(逐字段出处/置信度/依据)。

Revision ID: 0096_tax_profile_field_meta
Revises: 0095_full_invoice_source_receipt
Create Date: 2026-08-06

字段本值列只存人确认过/手填的值;推断候选(GET 现算,见 services/workorder/
profile_inference.py)先落 field_meta[field].proposal,用户点确认才转正写进本值列。
Dual-run:services/workspace/tax_profile_schema.ensure_tax_profile_schema() 跑同一 DDL
(ALTER ... ADD COLUMN IF NOT EXISTS 幂等,0064 建表时还没这一列,故用 ALTER 不改 0064)。
"""

from alembic import op

revision = "0096_tax_profile_field_meta"
down_revision = "0095_full_invoice_source_receipt"
branch_labels = None
depends_on = None

_ADD_COLUMN = "ALTER TABLE client_tax_profiles ADD COLUMN IF NOT EXISTS field_meta jsonb NOT NULL DEFAULT '{}'::jsonb"


def upgrade() -> None:
    op.execute(_ADD_COLUMN)


def downgrade() -> None:
    op.execute("ALTER TABLE client_tax_profiles DROP COLUMN IF EXISTS field_meta")
