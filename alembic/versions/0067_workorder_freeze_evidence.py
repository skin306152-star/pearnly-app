"""Pearnly AI 工单制 · 冻结证据包地基(C-2):堵级联删除蒸发口 + 交付物版本化 + 原始文件名列。

Revision ID: 0067_workorder_freeze_evidence
Revises: 0066_workorder_runtime_hardening
Create Date: 2026-07-11

留档性质:prod alembic 指针停 0020,本迁移不自动上生产;真正落列/落索引/改外键靠
services/workorder/schema.py::ensure_runtime_hardening()(RUNTIME_ALTERS)懒加载自愈,
同 0060_ai_usage 的 dual-run 范式。两份 DDL(本迁移 + schema.RUNTIME_ALTERS)逐字对齐,
全部幂等且对存量库可重入:

  1. 三子表外键 ON DELETE CASCADE → RESTRICT:现状无任何删除代码路径(零行为变化),纯堵
     「一条 DELETE work_orders 即证据蒸发、磁盘原件成孤儿」的口子。DO 块只挑当前仍是 CASCADE
     ('c')的外键改,已是 RESTRICT 的跳过——重入不重复 drop/add,不做无谓 ACCESS EXCLUSIVE 锁。
  2. work_order_deliverables 加 version int NOT NULL DEFAULT 1:交付物版本化;唯一键从
     (tenant, wo, kind) 改成 (tenant, wo, kind, version),未冻结时重跑=新版本、旧版本文件不动。
     存量行经 DEFAULT 1 补齐,读侧默认取最新版。
  3. work_order_items 加 original_name text:冻结 manifest 要留无损原始文件名(现状原名有损内嵌
     落盘名 {uuid}__词干,启发式反解)。读侧优先取列、空回落 storage.original_name_of;存量不回填。
"""

from alembic import op

revision = "0067_workorder_freeze_evidence"
down_revision = "0066_workorder_runtime_hardening"
branch_labels = None
depends_on = None

# 三子表外键 CASCADE→RESTRICT:按 pg_constraint 现状挑 CASCADE 的改(重入安全)。
_FK_RESTRICT = """
DO $$
DECLARE r record;
BEGIN
    FOR r IN
        SELECT conrelid::regclass AS tbl, conname
        FROM pg_constraint
        WHERE contype = 'f'
          AND confrelid = 'work_orders'::regclass
          AND conrelid IN (
              'work_order_events'::regclass,
              'work_order_items'::regclass,
              'work_order_deliverables'::regclass
          )
          AND confdeltype = 'c'
    LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.tbl, r.conname);
        EXECUTE format(
            'ALTER TABLE %s ADD CONSTRAINT %I FOREIGN KEY (work_order_id) '
            'REFERENCES work_orders (id) ON DELETE RESTRICT', r.tbl, r.conname);
    END LOOP;
END $$;
"""

# 反向:RESTRICT→CASCADE(仅 downgrade 用,挑当前 RESTRICT 'r' 的改回)。
_FK_CASCADE = """
DO $$
DECLARE r record;
BEGIN
    FOR r IN
        SELECT conrelid::regclass AS tbl, conname
        FROM pg_constraint
        WHERE contype = 'f'
          AND confrelid = 'work_orders'::regclass
          AND conrelid IN (
              'work_order_events'::regclass,
              'work_order_items'::regclass,
              'work_order_deliverables'::regclass
          )
          AND confdeltype = 'r'
    LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.tbl, r.conname);
        EXECUTE format(
            'ALTER TABLE %s ADD CONSTRAINT %I FOREIGN KEY (work_order_id) '
            'REFERENCES work_orders (id) ON DELETE CASCADE', r.tbl, r.conname);
    END LOOP;
END $$;
"""


def upgrade() -> None:
    op.execute(_FK_RESTRICT)
    op.execute(
        "ALTER TABLE work_order_deliverables "
        "ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1"
    )
    op.execute("DROP INDEX IF EXISTS uq_wo_deliverables_kind")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_deliverables_kind_version "
        "ON work_order_deliverables (tenant_id, work_order_id, kind, version)"
    )
    op.execute("ALTER TABLE work_order_items ADD COLUMN IF NOT EXISTS original_name text")


def downgrade() -> None:
    op.execute("ALTER TABLE work_order_items DROP COLUMN IF EXISTS original_name")
    op.execute("DROP INDEX IF EXISTS uq_wo_deliverables_kind_version")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_deliverables_kind "
        "ON work_order_deliverables (tenant_id, work_order_id, kind)"
    )
    op.execute("ALTER TABLE work_order_deliverables DROP COLUMN IF EXISTS version")
    op.execute(_FK_CASCADE)
