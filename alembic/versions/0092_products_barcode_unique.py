# -*- coding: utf-8 -*-
"""条码唯一约束:products / product_units 各一条部分唯一索引(POS 扫码 P1-F)。

Revision ID: 0092_products_barcode_unique
Revises: 0091_steward_attachments
Create Date: 2026-07-30

在此之前 idx_products_barcode 是【非唯一】索引,撞码只有建品弹窗那层 UX 拦——Excel 导入
(services/sales/product_import.py)和直调 API 都绕得过。重码建出来后,要到收银台扫出错
商品才暴露,那时已经卖错价、也改不动历史单。谓词带 is_active:停用的老商品不占码。

product_units 一并收:POS 的 product_by_barcode 对单位码是 `LIMIT 1` 无 ORDER BY,
两条同码单位存在时扫出哪个商品不确定 —— 那是钱路径。该表删单位是硬删,无 is_active。

存量:先跑 DO 块前置校验,有重复直接 RAISE 中止(不留半截),报冲突组数 + 最大一组 + 清理
路径;再把 ''/首尾空白条码归一成 NULL(空串会进 `WHERE barcode IS NOT NULL` 的索引 →
几个"没填条码"的商品互撞)。归一不可逆,downgrade 只撤索引 —— 空串条码本就不携带信息。

体检查询与建索引 SQL 在 services/sales/products.py 有等价实现(barcode_conflicts /
create_barcode_unique_indexes),但这里逐字写死不 import:迁移是历史快照,不能跟着常量漂
(同 0006 的约定)。留档性质:prod 不跑 alembic upgrade,真正生效靠
services/products/units.ensure_schema() 启动期调 create_barcode_unique_indexes()。
"""

from alembic import op

revision = "0092_products_barcode_unique"
down_revision = "0091_steward_attachments"
branch_labels = None
depends_on = None

# 前置校验:同 (租户, 套账) 下归一后重复的条码。按 btrim 归组 —— 归一后才撞的
# (` 8850` vs `8850`)也得算,否则校验放行、下面 UPDATE 归一完 CREATE UNIQUE INDEX
# 才炸,迁移半截死在生产库上。消息用 USING MESSAGE 拼接而非 RAISE 的 % 占位:
# op.execute 走 SQLAlchemy text(),裸 % 在带参执行路径上会被当成占位符。
_PRECHECK = """
DO $precheck$
DECLARE
    dup record;
    groups int;
BEGIN
    SELECT count(*) INTO groups FROM (
        SELECT 1 FROM {table}
        WHERE btrim(coalesce(barcode, '')) <> ''{active}
        GROUP BY tenant_id, workspace_client_id, btrim(barcode)
        HAVING count(*) > 1
    ) x;
    IF groups = 0 THEN
        RETURN;
    END IF;
    SELECT tenant_id, workspace_client_id, btrim(barcode) AS barcode, count(*) AS n
    INTO dup FROM {table}
    WHERE btrim(coalesce(barcode, '')) <> ''{active}
    GROUP BY tenant_id, workspace_client_id, btrim(barcode)
    HAVING count(*) > 1
    ORDER BY count(*) DESC
    LIMIT 1;
    RAISE EXCEPTION USING MESSAGE =
        '{table}: ' || groups || ' 组重复条码,唯一索引建不了。最大一组 tenant=' || dup.tenant_id
        || ' workspace=' || dup.workspace_client_id || ' barcode=' || dup.barcode
        || ' 共 ' || dup.n || ' 行。清理:同码里留一条,其余改码或停用'
        || '(products 置 is_active=FALSE;product_units 删行)。'
        || '全量清单见 services.sales.products.barcode_conflicts';
END
$precheck$;
"""

_NORMALIZE = (
    "UPDATE {table} SET barcode = nullif(btrim(barcode), '') "
    "WHERE barcode IS DISTINCT FROM nullif(btrim(barcode), '')"
)

_SCOPES = (("products", " AND is_active = TRUE"), ("product_units", ""))


def upgrade() -> None:
    for table, active in _SCOPES:
        op.execute(_PRECHECK.format(table=table, active=active))
        op.execute(_NORMALIZE.format(table=table))
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_products_ws_barcode ON products "
        "(tenant_id, workspace_client_id, barcode) WHERE barcode IS NOT NULL AND is_active = TRUE"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_product_units_ws_barcode ON product_units "
        "(tenant_id, workspace_client_id, barcode) WHERE barcode IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_products_ws_barcode")
    op.execute("DROP INDEX IF EXISTS uq_product_units_ws_barcode")
