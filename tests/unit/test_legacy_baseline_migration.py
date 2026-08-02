# -*- coding: utf-8 -*-
"""alembic/sql/001a_legacy_tables.sql 必须是快照的抄本,不是手写的近似。

手写 DDL 抄错了没人知道 —— 这正是 26 张遗留表当年被 tests/integration 手抄一遍
就当数的病根。所以这份载荷的每一行都要能回推到 docs/db/prod-schema.sql:
列定义逐字相同,索引只准多 IF NOT EXISTS,序列只准按 serial 规则还原。
偏一个字都在这里红。
"""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_schema_ddl_coverage as gate  # noqa: E402

BASELINE_SQL = ROOT / "alembic" / "sql" / "001a_legacy_tables.sql"
BASELINE_PY = ROOT / "alembic" / "versions" / "001a_legacy_tables.py"

# 2026-07-31 盘点出的 26 张遗留表:建表 DDL 全仓一句都没有,只活在开发库和测试桩里。
# 这份名单是历史记录,不许因为"载荷里现在有别的表"而跟着改。
LEGACY_TABLES = frozenset(
    {
        "api_keys",
        "automation_rules",
        "bank_reconcile_candidates",
        "bank_reconcile_sessions",
        "bank_reconcile_transactions",
        "email_ingest_accounts",
        "email_ingest_logs",
        "email_ingest_seen_uids",
        "erp_endpoints",
        "erp_oauth_states",
        "erp_oauth_tokens",
        "erp_push_logs",
        "excel_templates",
        "expense_draft",
        "ip_usage",
        "line_binding_codes",
        "line_bindings",
        "mrerp_credentials",
        "ocr_history",
        "operation_logs",
        "rd_cache",
        "rd_daily_usage",
        "supplier_client_mapping",
        "tenants",
        "user_settings",
        "users",
    }
)

# 归后续迁移所有的索引:baseline 不建,由 005 / 0065 / 0076 各自建。
# 一个数据库对象只能有一个迁移当主人,两边都建就是两份会漂的事实源。
INDEXES_OWNED_BY_LATER_MIGRATIONS = frozenset(
    {"idx_ocr_history_workspace", "uq_users_username_lower", "ix_erp_push_logs_tenant_wo"}
)

_TABLE_RE = re.compile(r'^CREATE TABLE IF NOT EXISTS "([a-z0-9_]+)" \($', re.M)
_INDEX_RE = re.compile(r"^CREATE (UNIQUE )?INDEX (IF NOT EXISTS )?(\S+) ON (.*)$", re.M)
_SERIAL_RE = re.compile(r'^  "([a-z0-9_]+)" (bigserial|serial)( .*)?$')


def _split_blocks(text: str) -> dict:
    """把 CREATE TABLE ... ); 之后到空行为止的内容,按表名切开。"""
    blocks, table, buf = {}, None, []
    for line in text.splitlines():
        m = _TABLE_RE.match(line)
        if m:
            table, buf = m.group(1), [line]
            continue
        if table is None:
            continue
        if not line.strip():
            blocks[table] = "\n".join(buf)
            table, buf = None, []
            continue
        buf.append(line)
    if table is not None:
        blocks[table] = "\n".join(buf)
    return blocks


class BaselineShapeTests(unittest.TestCase):
    def test_covers_exactly_the_26_legacy_tables(self):
        got = set(_TABLE_RE.findall(BASELINE_SQL.read_text(encoding="utf-8")))
        self.assertEqual(got, set(LEGACY_TABLES))

    def test_gate_sees_the_payload(self):
        # 载荷是 .sql,覆盖闸的扫描面必须包含 alembic/sql,否则这 26 张表在闸眼里
        # 仍然"无 DDL"。这条把两个文件的契约钉在一起。
        self.assertTrue(LEGACY_TABLES <= gate.product_ddl_tables())

    def test_migration_points_at_the_payload(self):
        self.assertTrue(BASELINE_SQL.is_file())
        src = BASELINE_PY.read_text(encoding="utf-8")
        self.assertIn('"sql" / "001a_legacy_tables.sql"', src)
        self.assertIn('down_revision = "001_baseline"', src)

    def test_no_table_has_two_owners(self):
        # baseline 建的表,别的迁移不许再建一遍。
        others = set()
        for p in (ROOT / "alembic" / "versions").glob("*.py"):
            others |= {
                m.group(1).lower()
                for m in gate._CREATE_RE.finditer(p.read_text(encoding="utf-8", errors="replace"))
            }
        self.assertEqual(sorted(LEGACY_TABLES & others), [])


class CopiedFromSnapshotTests(unittest.TestCase):
    """逐行回推快照。列定义、约束行逐字一致;两处机械变换按规则放行。"""

    @classmethod
    def setUpClass(cls):
        cls.baseline = _split_blocks(BASELINE_SQL.read_text(encoding="utf-8"))
        cls.snapshot = _split_blocks(gate.SNAPSHOT.read_text(encoding="utf-8"))

    def test_every_column_line_matches_the_snapshot(self):
        for table in sorted(LEGACY_TABLES):
            snap_lines = set(self.snapshot[table].splitlines())
            for line in self.baseline[table].splitlines():
                if line.startswith("CREATE ") or line == ");":
                    continue
                serial = _SERIAL_RE.match(line)
                if serial:
                    col, kind = serial.group(1), serial.group(2)
                    base = "bigint" if kind == "bigserial" else "integer"
                    want = (
                        f'  "{col}" {base} '
                        f"DEFAULT nextval('{table}_{col}_seq'::regclass){serial.group(3) or ''}"
                    )
                    self.assertIn(want, snap_lines, f"{table}.{col} 的 serial 还原对不上快照")
                    continue
                self.assertIn(line, snap_lines, f"{table} 有一行不在快照里:{line}")

    def test_snapshot_columns_are_all_present(self):
        # 反方向:快照有而载荷没有 = 空库建出来的表缺列,真库测试又要靠手抄补。
        for table in sorted(LEGACY_TABLES):
            base_cols = set(re.findall(r'^  "([a-z0-9_]+)" ', self.baseline[table], re.M))
            snap_cols = set(re.findall(r'^  "([a-z0-9_]+)" ', self.snapshot[table], re.M))
            self.assertEqual(snap_cols - base_cols, set(), f"{table} 漏抄了列")

    def test_indexes_are_snapshot_lines_plus_if_not_exists(self):
        for table in sorted(LEGACY_TABLES):
            snap_lines = set(self.snapshot[table].splitlines())
            for m in _INDEX_RE.finditer(self.baseline[table]):
                uniq, guard, name, rest = m.groups()
                self.assertEqual(
                    guard, "IF NOT EXISTS ", f"{name} 少了 IF NOT EXISTS,整份 DDL 就不幂等"
                )
                self.assertNotIn(name, INDEXES_OWNED_BY_LATER_MIGRATIONS, f"{name} 有两个主人")
                self.assertIn(f"CREATE {uniq or ''}INDEX {name} ON {rest}", snap_lines)

    def test_constraint_backed_indexes_are_not_rebuilt(self):
        # 唯一约束自带同名索引,再 CREATE INDEX 一次 = 撞名建库失败。
        for table in sorted(LEGACY_TABLES):
            block = self.baseline[table]
            constraints = set(re.findall(r'CONSTRAINT "([a-z0-9_]+)"', block))
            index_names = {m.group(3) for m in _INDEX_RE.finditer(block)}
            self.assertEqual(sorted(constraints & index_names), [], table)


if __name__ == "__main__":
    unittest.main()
