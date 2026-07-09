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


if __name__ == "__main__":
    unittest.main()
