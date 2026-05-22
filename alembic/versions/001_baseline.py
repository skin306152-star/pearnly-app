"""baseline · 锚定当前 prod schema 为 Alembic v001

REFACTOR-A2.1 (2026-05-22)

空迁移 · 不改任何 schema · 只是把当前 prod schema 锚定为"Alembic 起点版本"。
A2.2(后续 task)在 prod 第一次跑 `alembic stamp head` · 让 alembic_version 表
写入 001_baseline · 此时 Alembic 知道"当前 prod = v001"。

后续真正的 schema 改动从 002 开始:
- 002_vat_recon_tasks.py(设计文档 §3.2 · 第一批试点 ensure_vat_recon_tasks_table)
- 003_..._migration(后续 25 个 ensure_* 灰度迁移)

设计文档:docs/architecture/db-migration-plan.md §2.4

Revision ID: 001_baseline
Revises:
Create Date: 2026-05-22
"""
from typing import Sequence, Union

revision: str = "001_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """空 · 当前 prod schema 已经是 v001"""
    pass


def downgrade() -> None:
    """空 · 不可降级到"无表"状态(prod schema 由历史 ensure_* 函数累积建成)"""
    pass
