# -*- coding: utf-8 -*-
"""ocr_history 补 posting_kind 可空列(C1+C3 · 过账去向落盘)。

Revision ID: 0086_ocr_history_posting_kind
Revises: 0085_bank_sales_recovery_scan_index
Create Date: 2026-07-25

过账去向此前只活在录入向导的单次会话里,只有手动推带得上;改成跟着票走后,识别后自动推 /
失败重试 / 批量分拣三条腿零改动即读得到。语义与优先级见 services/erp/express_push/posting_kind.py。

存量行不回填——回填=编造会计当时的记账政策。

留档性质:prod 不跑 alembic upgrade,真正落列靠 services/clients/store.py 的
ensure_clients_table()(ocr_history 补列的既有归口,client_id/ai_raw/staged 同住)
启动期自愈(dual-run,与本迁移逐字对齐)。
"""

from alembic import op

revision = "0086_ocr_history_posting_kind"
down_revision = "0085_bank_sales_recovery_scan_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS posting_kind TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE ocr_history DROP COLUMN IF EXISTS posting_kind")
