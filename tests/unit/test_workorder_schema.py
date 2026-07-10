# -*- coding: utf-8 -*-
"""工单制 schema 双跑对齐闸(桌面 pearnly ai/M0-施工任务包-v1.md §3 · 铁律 #5)。

建表唯一走 alembic 0059(铁律 #5:无运行期 ensure 建表);services/workorder/schema.py
只留与 0059 逐字对齐的 DDL 常量(集成测试助手从中建表)。这两份 DDL 任一处漏建表/漏
隔离 → 红。纯静态扫文本,不连库(照 tests/unit/test_purchase_schema.py 同款配方)。
"""

import pathlib
import re
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_MIGRATION = "alembic/versions/0059_workorder_core.py"
_ENSURE = "services/workorder/schema.py"

_EXPECTED_TABLES = {
    "work_orders",
    "work_order_events",
    "work_order_items",
    "work_order_deliverables",
}

_CREATE_RE = re.compile(r"CREATE TABLE IF NOT EXISTS\s+(\w+)", re.I)


def _text(path: str) -> str:
    return (_ROOT / path).read_text(encoding="utf-8")


def _tables_in(path: str) -> set:
    return set(_CREATE_RE.findall(_text(path)))


class WorkOrderSchemaParityTests(unittest.TestCase):
    def test_ensure_covers_all_expected_tables(self):
        self.assertEqual(_tables_in(_ENSURE), _EXPECTED_TABLES)

    def test_migration_covers_all_expected_tables(self):
        self.assertEqual(_tables_in(_MIGRATION), _EXPECTED_TABLES)

    def test_every_table_has_rls_in_ensure(self):
        text = _text(_ENSURE)
        for t in _EXPECTED_TABLES:
            self.assertIn(f'"{t}"', text, f"{t} 未列入 ensure 的 RLS 清单")

    def test_every_table_has_rls_in_migration(self):
        text = _text(_MIGRATION)
        for t in _EXPECTED_TABLES:
            self.assertIn(f't="{t}"', text, f"{t} 缺 RLS policy 应用(_RLS.format)")

    def test_migration_down_revision_chains_to_declared_head(self):
        # 冻结「接在真正的 head 后」这条要求:防下次新迁移改 down_revision 时漏查链。
        text = _text(_MIGRATION)
        self.assertIn('down_revision = "0058_pos_sheets_settings"', text)

    def test_migration_has_matching_downgrade(self):
        text = _text(_MIGRATION)
        for t in _EXPECTED_TABLES:
            self.assertIn(f"DROP TABLE IF EXISTS {t}", text)

    def test_work_orders_unique_scope_index_present_both_sides(self):
        # 幂等开单铁律:唯一约束覆盖 tenant+账套+期间+意图,ensure 和迁移必须同款。
        needle = "ON work_orders (tenant_id, workspace_client_id, period, intent)"
        self.assertIn(needle, _text(_ENSURE))
        self.assertIn(needle, _text(_MIGRATION))

    def test_events_table_has_no_update_or_delete_ddl(self):
        # 只追加铁律的 schema 侧证据:两份 DDL 里 work_order_events 段落不含 UPDATE/DELETE 语句。
        for path in (_ENSURE, _MIGRATION):
            text = _text(path)
            self.assertNotIn("UPDATE work_order_events", text)
            self.assertNotIn("DELETE FROM work_order_events", text)


_HARDEN_MIGRATION = "alembic/versions/0066_workorder_runtime_hardening.py"

# 运行时加固(C-1)的 DDL 关键片段:ensure(schema.RUNTIME_ALTERS)与 0066 迁移必须同款。
_HARDEN_NEEDLES = (
    "ADD COLUMN IF NOT EXISTS run_lease_owner text",
    "ADD COLUMN IF NOT EXISTS run_lease_expires_at timestamptz",
    "ADD COLUMN IF NOT EXISTS dedupe_key text",
    "uq_wo_events_dedupe",
    "(tenant_id, work_order_id, step, event_type, dedupe_key)",
    "WHERE dedupe_key IS NOT NULL",
)


class RuntimeHardeningParityTests(unittest.TestCase):
    """C-1 §3/§4 dual-run 对齐:ensure 与 0066 迁移逐片段同款(prod alembic 停 0020,靠 ensure 自愈)。"""

    def test_ensure_and_migration_carry_same_hardening_ddl(self):
        ensure_text = _text(_ENSURE)
        migration_text = _text(_HARDEN_MIGRATION)
        for needle in _HARDEN_NEEDLES:
            self.assertIn(needle, ensure_text, f"ensure 缺加固 DDL: {needle}")
            self.assertIn(needle, migration_text, f"0066 迁移缺加固 DDL: {needle}")

    def test_migration_merges_both_heads(self):
        # 0066 收编 0058 之后分叉的两条链(0059 工单链 + 0065 主链)成单 head。
        text = _text(_HARDEN_MIGRATION)
        self.assertIn('"0065_users_username_lower_uniq"', text)
        self.assertIn('"0059_workorder_core"', text)

    def test_migration_downgrade_drops_everything(self):
        text = _text(_HARDEN_MIGRATION)
        self.assertIn("DROP INDEX IF EXISTS uq_wo_events_dedupe", text)
        self.assertIn("DROP COLUMN IF EXISTS dedupe_key", text)
        self.assertIn("DROP COLUMN IF EXISTS run_lease_owner", text)


_FREEZE_MIGRATION = "alembic/versions/0067_workorder_freeze_evidence.py"

# 冻结证据地基(C-2)DDL 关键片段:ensure(schema.RUNTIME_ALTERS)与 0067 迁移必须同款
# (dual-run,prod alembic 停 0020 靠 ensure 自愈)。
_FREEZE_NEEDLES = (
    "ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1",
    "uq_wo_deliverables_kind_version",
    "(tenant_id, work_order_id, kind, version)",
    "ADD COLUMN IF NOT EXISTS original_name text",
    "confdeltype = 'c'",  # 外键 CASCADE→RESTRICT 的 DO 块:只挑当前 CASCADE 的改(重入安全)
    "ON DELETE RESTRICT",
)


class FreezeEvidenceParityTests(unittest.TestCase):
    """C-2 dual-run 对齐:级联删除改 RESTRICT + 交付物版本化 + 原始文件名列,ensure 与 0067 同款。"""

    def test_ensure_and_migration_carry_same_freeze_ddl(self):
        ensure_text = _text(_ENSURE)
        migration_text = _text(_FREEZE_MIGRATION)
        for needle in _FREEZE_NEEDLES:
            self.assertIn(needle, ensure_text, f"ensure 缺 C-2 DDL: {needle}")
            self.assertIn(needle, migration_text, f"0067 迁移缺 C-2 DDL: {needle}")

    def test_migration_chains_to_hardening_head(self):
        text = _text(_FREEZE_MIGRATION)
        self.assertIn('down_revision = "0066_workorder_runtime_hardening"', text)

    def test_migration_downgrade_reverts_all(self):
        text = _text(_FREEZE_MIGRATION)
        self.assertIn("DROP COLUMN IF EXISTS original_name", text)
        self.assertIn("DROP INDEX IF EXISTS uq_wo_deliverables_kind_version", text)
        self.assertIn("DROP COLUMN IF EXISTS version", text)
        self.assertIn("ON DELETE CASCADE", text)  # 反向恢复


if __name__ == "__main__":
    unittest.main()
