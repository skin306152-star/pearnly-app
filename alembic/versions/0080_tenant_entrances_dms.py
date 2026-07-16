# -*- coding: utf-8 -*-
"""tenant_entrances.entrance CHECK 约束扩容:加入 'dms' 入口(MR.ERP 订车单门)。

Revision ID: 0080_tenant_entrances_dms
Revises: 0079_front_desk_contracts
Create Date: 2026-07-16

0078 建表时 CHECK 收窄为 IN ('main','pos','ai');新增 dms 入口后,发放侧对 dms 的
grant_entrance 会被旧约束拒。本迁移 DROP 旧 CHECK、ADD 含 dms 的新 CHECK(down 反向)。
0078 是无名内联 CHECK,Postgres 惯例命名 tenant_entrances_entrance_check;此处显式给约束
命名,DROP/ADD 都用同一名,避免再落无名约束。表其它部分(索引/RLS 终态)一律不动。
"""

from alembic import op

revision = "0080_tenant_entrances_dms"
down_revision = "0079_front_desk_contracts"
branch_labels = None
depends_on = None

_CONSTRAINT = "tenant_entrances_entrance_check"


def upgrade() -> None:
    op.execute(f"ALTER TABLE tenant_entrances DROP CONSTRAINT IF EXISTS {_CONSTRAINT}")
    op.execute(
        f"ALTER TABLE tenant_entrances ADD CONSTRAINT {_CONSTRAINT} "
        "CHECK (entrance IN ('main','pos','ai','dms'))"
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE tenant_entrances DROP CONSTRAINT IF EXISTS {_CONSTRAINT}")
    op.execute(
        f"ALTER TABLE tenant_entrances ADD CONSTRAINT {_CONSTRAINT} "
        "CHECK (entrance IN ('main','pos','ai'))"
    )
