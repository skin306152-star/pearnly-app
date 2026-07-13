# -*- coding: utf-8 -*-
"""工单制 4 表 DDL 常量(建表唯一事实源 = alembic 0059 · 铁律 #5:schema 只走迁移)。

这里不再有运行期 ensure 建表入口(反模式已删):真正的建表由 alembic/versions/
0059_workorder_core.py 负责。本模块只冻结与 0059 逐字对齐的 DDL 常量,两处漂移由
tests/unit/test_workorder_schema.py 静态守;真表隔离集成测试从这些常量建表(见
tests/integration/_workorder_schema.py 的测试助手)。

四表关系:work_orders 是每客户每期一张的顶层单据,workspace_client_id 恒非空(每单
只属一个客户账套);其余三表以 work_order_id 挂在它下面,各自也带一份 tenant_id
(同 purchase_lines/journal_lines 的子表惯例)。四表统一纯 tenant RLS
——docs/refactor/b8-rls-HANDOFF §7.15.2/7.20 反复验过:仓库里 `apply_tenant_workspace_rls`
虽存在(core/rls.py)但实际零表采用,purchase_docs/journal_vouchers 等有 workspace_client_id
的表照样只挂纯 tenant policy,应用层 WHERE tenant_id+workspace_client_id 才是真正的隔离主力、
RLS 是第二道防线,不重复造未经验证的模板。

work_order_events 是唯一追加表:证据链底座 + 断点续跑的恢复源(重放到最后一条
step_done = 当前进度)。DAL 层(store.py)故意不给它 UPDATE/DELETE 函数。
"""

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS work_orders (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        period text NOT NULL,
        intent text NOT NULL DEFAULT 'monthly_vat',
        status text NOT NULL DEFAULT 'collecting',
        current_step text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    # 只追加:无 UPDATE/DELETE 路径(store.py 只给 append + 查询)。id 是 bigserial ——
    # 单写入者场景下自增序天然就是事件发生顺序,断点续跑靠它重放,不必依赖 created_at 去重时间戳。
    """
    CREATE TABLE IF NOT EXISTS work_order_events (
        id bigserial PRIMARY KEY,
        tenant_id uuid NOT NULL,
        work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
        step text NOT NULL,
        event_type text NOT NULL,
        payload jsonb NOT NULL DEFAULT '{}'::jsonb,
        actor text NOT NULL DEFAULT 'system',
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS work_order_items (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
        source text NOT NULL,
        kind text NOT NULL DEFAULT 'unknown',
        file_ref text,
        ocr_history_id uuid,
        status text NOT NULL DEFAULT 'pending',
        flag_reason text,
        dedupe_key text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    # numbers 快照关键数字(如销项/进项税额)供证据索引直接引用,不必每次重算。
    """
    CREATE TABLE IF NOT EXISTS work_order_deliverables (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
        kind text NOT NULL,
        artifact_path text,
        numbers jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
)

_INDEXES = (
    # 幂等开单:同租户同账套同期同意图只有一张工单(§3 唯一约束)。
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_work_orders_scope "
    "ON work_orders (tenant_id, workspace_client_id, period, intent)",
    "CREATE INDEX IF NOT EXISTS ix_wo_events_wo "
    "ON work_order_events (tenant_id, work_order_id, id)",
    "CREATE INDEX IF NOT EXISTS ix_wo_items_wo " "ON work_order_items (tenant_id, work_order_id)",
    # 幂等 intake:同一工单内同一 dedupe_key 只落一行(NULL 不参与去重——非全部 item 都算指纹)。
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_items_dedupe "
    "ON work_order_items (tenant_id, work_order_id, dedupe_key) WHERE dedupe_key IS NOT NULL",
    # 幂等 package:重跑同一 kind 的交付物覆盖而非累加(§6 金标测试 6·幂等)。
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_deliverables_kind "
    "ON work_order_deliverables (tenant_id, work_order_id, kind)",
)

_RLS_TABLES = (
    "work_orders",
    "work_order_events",
    "work_order_items",
    "work_order_deliverables",
)

# 运行时加固 DDL(C-1 + C-2)。与 alembic 0066/0067 逐字对齐(dual-run):prod alembic 指针
# 停 0020,建列/建索引/改外键靠这里懒加载自愈,同 0060_ai_usage 范式。全部幂等且对存量库
# 可重入(ADD COLUMN / CREATE INDEX 均 IF NOT EXISTS;外键改造用 DO 块只挑当前 CASCADE 的改)。
# 基表 DDL(_TABLES)保持与 0059 逐字对齐不动,增量走 ALTER 挂这里,不污染基表常量。
_FK_RESTRICT_DO = """
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

RUNTIME_ALTERS = (
    # C-1:租约 + 事件幂等键。
    "ALTER TABLE work_orders ADD COLUMN IF NOT EXISTS run_lease_owner text",
    "ALTER TABLE work_orders ADD COLUMN IF NOT EXISTS run_lease_expires_at timestamptz",
    "ALTER TABLE work_order_events ADD COLUMN IF NOT EXISTS dedupe_key text",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_events_dedupe "
    "ON work_order_events (tenant_id, work_order_id, step, event_type, dedupe_key) "
    "WHERE dedupe_key IS NOT NULL",
    # C-2:堵级联删除蒸发口 + 交付物版本化 + 原始文件名列。
    _FK_RESTRICT_DO,
    "ALTER TABLE work_order_deliverables "
    "ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1",
    "DROP INDEX IF EXISTS uq_wo_deliverables_kind",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_deliverables_kind_version "
    "ON work_order_deliverables (tenant_id, work_order_id, kind, version)",
    "ALTER TABLE work_order_items ADD COLUMN IF NOT EXISTS original_name text",
    # MC2-A1(效率8):收尸扫描的部分索引——过期租约支只扫 running 且持约的极少数行,
    # 不随工单总量线性变慢(与 0075 迁移 dual-run 对齐)。
    "CREATE INDEX IF NOT EXISTS ix_wo_dead_run_scan "
    "ON work_orders (run_lease_expires_at) "
    "WHERE status = 'running' AND run_lease_expires_at IS NOT NULL",
)


def ensure_runtime_hardening(cur) -> None:
    """把 RUNTIME_ALTERS 灌进当前事务游标(幂等)。store.py 首次用到租约/幂等键列时懒调。"""
    for ddl in RUNTIME_ALTERS:
        cur.execute(ddl)
