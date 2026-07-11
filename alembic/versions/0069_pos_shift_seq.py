"""POS 班次连号 shift_seq(PC-3 · Z 报表防删 · 防内盗 tamper-evidence)。

Revision ID: 0069_pos_shift_seq
Revises: 0068_pos_cashier_caps
Create Date: 2026-07-11

每 (tenant, ws) 单调递增连号。没有物理删班的端点(全仓无 DELETE FROM pos_shifts),连号本身
就是防篡改:收银员若绕库删掉亏空那张班,序号断裂 → 老板端台账缺号可见。唯一约束兜并发撞号
(一店同秒双开班极罕见),open_shift 捕获冲突重取一次。回填存量按 (tenant,ws) 内 opened_at
升序赋 1..N。Dual-run:services/pos/cashier.ensure_core_schema() 跑同一幂等 ADD COLUMN + 唯一索引。
"""

from alembic import op

revision = "0069_pos_shift_seq"
down_revision = "0068_pos_cashier_caps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE pos_shifts ADD COLUMN IF NOT EXISTS shift_seq integer")
    # 回填仅补空值(幂等):迁移时全为 NULL,row_number 每 (tenant,ws) 独立从 1 连号。
    # 排序键 opened_at,created_at,id 三重定序,存量同秒开班也得确定序不并列。
    op.execute(
        "WITH numbered AS ("
        "  SELECT id, row_number() OVER ("
        "    PARTITION BY tenant_id, workspace_client_id"
        "    ORDER BY opened_at, created_at, id"
        "  ) AS rn FROM pos_shifts"
        ") "
        "UPDATE pos_shifts s SET shift_seq = n.rn "
        "FROM numbered n WHERE s.id = n.id AND s.shift_seq IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_shift_seq "
        "ON pos_shifts (tenant_id, workspace_client_id, shift_seq)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_pos_shift_seq")
    op.execute("ALTER TABLE pos_shifts DROP COLUMN IF EXISTS shift_seq")
