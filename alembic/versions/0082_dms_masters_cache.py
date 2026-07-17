"""DMS 车辆选择面板主档缓存 dms_masters_cache(DL-4a)。

Revision ID: 0082_dms_masters_cache
Revises: 0081_line_dms_channel
Create Date: 2026-07-17

选车面板的下拉主档(顾问/车型/颜色…)每次开面板都登录 DMS 抓全量太贵 → 缓存 <12h 复用。
endpoint_id 作 PK(非租户键,不施 RLS);paints 依赖 car,惰性按 car_id 存进 masters jsonb
的 paints_by_car 键。Dual-run:services/line_dms/masters_cache.ensure_table()(prod 无
alembic 钩子,走首用 ensure 自愈;本文件留档)。
"""

from alembic import op

revision = "0082_dms_masters_cache"
down_revision = "0081_line_dms_channel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS dms_masters_cache (
            endpoint_id text PRIMARY KEY,
            masters jsonb NOT NULL,
            refreshed_at timestamptz NOT NULL
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dms_masters_cache")
