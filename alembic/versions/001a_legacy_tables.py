"""遗留表 baseline · 把 26 张只存在于活库里的表补进迁移史

Revision ID: 001a_legacy_tables
Revises: 001_baseline
Create Date: 2026-08-01

001_baseline 当年的写法是"当前 prod schema 已经是 v001",空 upgrade + 一次
`alembic stamp`。锚点因此只是个记号:锚住的那份 schema 从没落进仓库,
users / ocr_history / erp_endpoints / erp_push_logs 这 26 张表的建表语句
全仓一句都没有(迁移史里只有 ALTER,services/ 里只有读写)。空库跑不出它们,
真库测试只能在测试文件里手抄 DDL——而手抄的抄本抄错了没人知道。本迁移补的
就是 001_baseline 当年该带上的那份 DDL,所以挂在它后面、002 前面。

DDL 载荷在 alembic/sql/001a_legacy_tables.sql(逐字来自 docs/db/prod-schema.sql,
两处机械变换见该文件头)。放同目录的 .py 里会让这个文件破 500 行,且纯 DDL
用 .sql 存能直接跟快照 diff。

对生产是可证的空操作,不是"应该没事":prod 的 alembic_version 停在
0020_sales_doc_paper_lang(2026-08-01 只读核实),本修订是它的祖先,
`alembic upgrade` 永远不会走到这里;何况 DDL 本身全是 IF NOT EXISTS。

⚠️ 空库跑 `alembic upgrade head` 仍然到不了头 —— 002 / 007 / 0030 三条历史迁移
引用了生产根本不存在的 schema(002 写 gl_vat_tasks / bank_recon_v2_tasks,生产是
单数 gl_vat_task / bank_recon_v2_task;007 给 erp_push_logs 加 adapter CHECK,
生产这张表没有 adapter 列;0030 回填 products.workspace_client_id,这列没有任何
迁移建过)。空库要重建到本修订为止,跑:
    alembic upgrade 001a_legacy_tables
把 head 修通要改那三条历史迁移,是另一件事、另一份风险评估。
"""

from pathlib import Path

from alembic import op

revision = "001a_legacy_tables"
down_revision = "001_baseline"
branch_labels = None
depends_on = None

_DDL = Path(__file__).resolve().parent.parent / "sql" / "001a_legacy_tables.sql"


def upgrade() -> None:
    op.execute(_DDL.read_text(encoding="utf-8"))


def downgrade() -> None:
    """不 DROP。这 26 张表装着用户、租户、OCR 历史、推送日志——降级删表 =
    删生产数据。降级回 001_baseline 的语义是"回到那个记号",不是"回到无表"。"""
