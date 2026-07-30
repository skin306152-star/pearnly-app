# -*- coding: utf-8 -*-
"""没设价 ≠ ฿0,单位码让位不抹值(POS 扫码 P0-① / P1-⑥)。

Revision ID: 0093_product_price_null_unit_visible
Revises: 0092_products_barcode_unique
Create Date: 2026-07-31

两件事,都是"数据层分不清两种状态"的同一类病:

1) products.unit_price 带着 `NOT NULL DEFAULT 0`,于是"没设价"进库就是 0,跟真的 ฿0(赠品)
   一模一样。收银台的零元闸只拦得住 null,拦不住 0 —— 扫码就地建品建出来的货全部 ฿0 可售,
   小票和报表上都看不出异常。去掉 NOT NULL + DEFAULT,空价格落 NULL。
   存量的 0 不回填成 NULL:分不清哪些是真 ฿0、哪些是老默认值顶上的,一刀切会让今天卖得好好
   的商品明天在收银台被拦下。只有本次之后新建/改动的商品才可能是 NULL。

2) product_units 停用时曾经把 barcode 抹成 NULL 来让出码 —— 值一去不回,而软删的契约是
   "保留引用、可复活":季节性下架再上架,商品和主码都回来了,三条单位码全空,扫箱码 404
   「商品不存在」而商品就在列表里。改成跟主码同一套:加 product_active 标记,唯一索引带谓词,
   停用退出索引、复活重新进来,值全程不动。
   该表没有 is_active(删单位是硬删),部分索引谓词又只能引用本表列,所以标记必须落在本表;
   由 services/sales/products.py 的三条 is_active 写路径维护。

索引改名不是洁癖:老名 uq_product_units_ws_barcode 跟新的只差谓词,`CREATE UNIQUE INDEX
IF NOT EXISTS` 撞上同名旧索引会当没事发生,生产上就留个"看着建好了、其实还是老谓词"的索引。

留档性质:prod 不跑 alembic upgrade,真正生效靠 services/products/units.ensure_schema() 启动期
调 relax_price_not_null / ensure_unit_visibility_column / create_barcode_unique_indexes。
SQL 在那边有等价实现,这里逐字写死不 import(迁移是历史快照,不跟着常量漂 · 同 0006 的约定)。
"""

from alembic import op

revision = "0093_product_price_null_unit_visible"
down_revision = "0092_products_barcode_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE products ALTER COLUMN unit_price DROP DEFAULT")
    op.execute("ALTER TABLE products ALTER COLUMN unit_price DROP NOT NULL")
    op.execute(
        "ALTER TABLE product_units ADD COLUMN IF NOT EXISTS product_active boolean "
        "NOT NULL DEFAULT TRUE"
    )
    op.execute(
        "UPDATE product_units pu SET product_active = p.is_active FROM products p "
        "WHERE p.id = pu.product_id AND pu.product_active IS DISTINCT FROM p.is_active"
    )
    op.execute("DROP INDEX IF EXISTS uq_product_units_ws_barcode")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_product_units_live_barcode ON product_units "
        "(tenant_id, workspace_client_id, barcode) WHERE barcode IS NOT NULL AND product_active"
    )


def downgrade() -> None:
    """回退要先把 NULL 价填回 0 —— 不然 SET NOT NULL 直接失败,回退卡在半路。

    填回去之后"没设价"和 ฿0 就再也分不开了(这正是 0093 之前的状态),不可逆,认了。
    单位码索引换回老谓词:停用商品的单位行会重新占码,回退前得先自己确认没有这种行。
    """
    op.execute("UPDATE products SET unit_price = 0 WHERE unit_price IS NULL")
    op.execute("ALTER TABLE products ALTER COLUMN unit_price SET NOT NULL")
    op.execute("ALTER TABLE products ALTER COLUMN unit_price SET DEFAULT 0")
    op.execute("DROP INDEX IF EXISTS uq_product_units_live_barcode")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_product_units_ws_barcode ON product_units "
        "(tenant_id, workspace_client_id, barcode) WHERE barcode IS NOT NULL"
    )
    op.execute("ALTER TABLE product_units DROP COLUMN IF EXISTS product_active")
