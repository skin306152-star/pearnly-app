"""erp_endpoints / erp_push_logs adapter CHECK · 加 'mrerp_dms'(MR.ERP DMS 汽车销售集成)

新增 adapter 'mrerp_dms'(身份证→订车单 · 独立于财务 'mrerp')。adapter CHECK
白名单需含它,否则创建 DMS endpoint / 写 DMS 推送日志触发 CheckViolation。

⚠️ 双跑(与 006 同范式):生产不跑 `alembic upgrade`(git-deploy 无钩子)· 真改
约束由启动期 services.erp.push_schema.ensure_erp_endpoints_adapter_constraint /
ensure_erp_push_logs_adapter_constraint(查 pg_catalog → drop+rebuild · 幂等 ·
canonical 已含 mrerp_dms)执行。本迁移留档 + 本地/未来钩子用。

canonical 与 erp_push.py ADAPTER_REGISTRY 对齐:webhook/xero/flowaccount/mrerp/mrerp_dms。

Revision ID: 007_erp_adapter_mrerp_dms
Revises: 005_workspace_clients
Create Date: 2026-05-31
"""

from typing import Sequence, Union

from alembic import op

revision: str = "007_erp_adapter_mrerp_dms"
down_revision: Union[str, Sequence[str], None] = "005_workspace_clients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_WITH_DMS = "('webhook', 'xero', 'flowaccount', 'mrerp', 'mrerp_dms')"
_WITHOUT_DMS = "('webhook', 'xero', 'flowaccount', 'mrerp')"


def _rebuild(table: str, in_list: str) -> None:
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_adapter_chk")
    op.execute(
        f"ALTER TABLE {table} ADD CONSTRAINT {table}_adapter_chk " f"CHECK (adapter IN {in_list})"
    )


def upgrade() -> None:
    _rebuild("erp_endpoints", _WITH_DMS)
    _rebuild("erp_push_logs", _WITH_DMS)


def downgrade() -> None:
    # 回滚前应先确保没有 mrerp_dms 行,否则新约束会拒绝(见交接文档回滚策略)。
    _rebuild("erp_endpoints", _WITHOUT_DMS)
    _rebuild("erp_push_logs", _WITHOUT_DMS)
