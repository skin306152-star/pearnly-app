# -*- coding: utf-8 -*-
"""alembic 0102_line_dms_login_tickets 契约:链挂对头 + 双跑 DDL 与模块逐字一致 + 启动不漏 ensure。

留档迁移与模块幂等 DDL 是同一张表的两个事实源(0101 同款内联范式),
任一处改了另一处没改 → 本测试红。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_MIGRATION = ROOT / "alembic" / "versions" / "0102_line_dms_login_tickets.py"
# 终止符两态:留档源文本里是 `)` + `"""`;模块 _DDL 是已求值字符串,`)` 后直接到结尾。
_TABLE_RE = re.compile(
    r"CREATE TABLE IF NOT EXISTS line_dms_login_tickets \((.*?)\)\s*(?:\"\"\"|\Z)", re.S
)


def _norm(text: str) -> str:
    # 去引号:留档源文本里索引语句是隐式拼接的两段字符串,求值前后差一对引号壳。
    return " ".join(text.replace('"', " ").replace("'", " ").split())


class MigrationChainTests(unittest.TestCase):
    def test_revision_chains_onto_head(self):
        src = _MIGRATION.read_text(encoding="utf-8")
        self.assertIn('revision = "0102_line_dms_login_tickets"', src)
        self.assertIn('down_revision = "0101_daily_entries"', src)


class DualRunDdlTests(unittest.TestCase):
    def test_create_table_matches_module_ddl(self):
        from services.line_dms import login_tickets as lt

        mig_body = _TABLE_RE.search(_MIGRATION.read_text(encoding="utf-8"))
        mod_body = _TABLE_RE.search(lt._DDL)
        self.assertIsNotNone(mig_body, "留档迁移里找不到建表 DDL")
        self.assertIsNotNone(mod_body, "模块 _DDL 里找不到建表 DDL")
        self.assertEqual(_norm(mig_body.group(1)), _norm(mod_body.group(1)))

    def test_indexes_match_module(self):
        from services.line_dms import login_tickets as lt

        mig = _norm(_MIGRATION.read_text(encoding="utf-8"))
        for stmt in lt._INDEXES:
            self.assertIn(_norm(stmt), mig)


class StartupWiringTests(unittest.TestCase):
    def test_startup_ensures_login_tickets(self):
        """prod 无 alembic 钩子:启动 ensure 漏接 = 线上永远没这张表。"""
        src = (ROOT / "services" / "startup.py").read_text(encoding="utf-8")
        self.assertIn("services.line_dms.login_tickets", src)


if __name__ == "__main__":
    unittest.main()
