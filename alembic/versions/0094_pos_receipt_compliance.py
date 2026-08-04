# -*- coding: utf-8 -*-
"""POS 小票合规字段(SM 缺口批次 G1/G4 · workspace_clients 两列)。

Revision ID: 0094_pos_receipt_compliance
Revises: 0093_product_price_null_unit_visible
Create Date: 2026-08-05

- pos_register_no:税务局收银机登记号(เครื่องบันทึกเงินสดเลขที่)。机打简式税票严格说需向
  税务局登记收银机;接真客户时按需办,先留字段位。票面规则:**有号才印整行,没号不印**
  (不印空标签,拿到号自动出现)。账套级(工单 G1 深水区拍板),不做 per-terminal。
- pos_receipt_qr_enabled:小票「凭小票号申请全式税票」二维码开关(G4 架子)。**默认关**:
  码内容指向 G2 预定的补开通路路由,G2 未施工前开了就是死链(扫码 404 · 四态诚实),
  G2 落地随批开。

留档性质:prod 不跑 alembic upgrade,真正生效靠 services/pos/receipt_settings.ensure_receipt_schema()
启动期双跑(经 bootstrap_pos_schema)。SQL 逐字写死不 import(迁移是历史快照 · 同 0006 约定)。
"""

from alembic import op

revision = "0094_pos_receipt_compliance"
down_revision = "0093_product_price_null_unit_visible"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS pos_register_no text")
    op.execute(
        "ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS pos_receipt_qr_enabled boolean "
        "NOT NULL DEFAULT FALSE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE workspace_clients DROP COLUMN IF EXISTS pos_receipt_qr_enabled")
    op.execute("ALTER TABLE workspace_clients DROP COLUMN IF EXISTS pos_register_no")
