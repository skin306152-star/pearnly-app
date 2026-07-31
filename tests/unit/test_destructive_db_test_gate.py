# -*- coding: utf-8 -*-
"""反证:破坏性 DB 测试闸(scripts/check_destructive_db_tests.py)+ 运行期哨兵
(tests/integration/_helpers.py::require_disposable_db)。

分四组:
  PoisonTests      喂已知有毒写法,断言闸真会红(闸装上当天在未修的树上就是这么红的)
  NoFalseAlarmTests 喂合法写法,断言闸不误报 —— 全仓 19 个文件的 DDL 只出现在
                    assertIn 的断言文本里(migration SQL 守门那批),把它们扫红这道闸就废了
  RealTreeTests    真树上必须绿,且必须真扫到东西(防「闸在但空扫」)
  DisposableGuardTests 哨兵函数四条分支:没 env / 连不上 / 没哨兵表 / 有哨兵表
"""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_destructive_db_tests as gate  # noqa: E402

GUARD_LINE = "from tests.integration._helpers import require_disposable_db\n"


def _restore_env(key: str, value: str | None) -> None:
    """把一个 env 键还原成取快照时的样子(原本没有 → 删掉,而不是留个空串)。"""
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value


def _scan_source(source: str, *, name: str = "test_probe.py"):
    """把一份源码写进临时目录跑闸,返回 (退出码, findings)。"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(source, encoding="utf-8")
        findings = gate.collect((Path(tmp),))
        code = gate.main([str(tmp), "--quiet"])
    return code, findings


class PoisonTests(unittest.TestCase):
    """每种真实存在过的写法都喂一遍,断言闸真会红。"""

    def _assert_red(self, source: str, msg: str) -> None:
        code, findings = _scan_source(source)
        self.assertEqual(code, 1, msg)
        self.assertTrue([f for f in findings if f.verdict == "RED"], msg)

    def test_plain_drop_table(self) -> None:
        self._assert_red(
            'cur.execute("DROP TABLE IF EXISTS users CASCADE")\n',
            "字面量 DROP TABLE 必须红",
        )

    def test_fstring_with_interpolated_table_name(self) -> None:
        # test_erp_credentials_rls_real_tables.py 的真实写法
        self._assert_red(
            'for table in TABLES:\n    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")\n',
            "f-string 里的 DROP TABLE 必须红",
        )

    def test_fstring_joining_a_module_constant(self) -> None:
        # test_billing_rls_real_tables.py 的真实写法:表名藏在模块级常量里
        self._assert_red(
            '_TABLES = ("ocr_cost_log", "ai_usage")\n'
            "cur.execute(f\"DROP TABLE IF EXISTS {', '.join(_TABLES)} CASCADE\")\n",
            "表名来自模块常量也必须红",
        )

    def test_sql_hidden_in_a_module_constant(self) -> None:
        self._assert_red(
            '_SQL = "DROP TABLE IF EXISTS ocr_history CASCADE"\ncur.execute(_SQL)\n',
            "整条 SQL 藏进常量也必须红",
        )

    def test_truncate(self) -> None:
        self._assert_red('cur.execute("TRUNCATE TABLE clients")\n', "TRUNCATE 必须红")

    def test_drop_schema(self) -> None:
        self._assert_red('cur.execute("DROP SCHEMA public CASCADE")\n', "DROP SCHEMA 必须红")

    def test_executemany(self) -> None:
        self._assert_red(
            'cur.executemany("DROP TABLE IF EXISTS %s", rows)\n', "executemany 也算执行"
        )

    def test_string_concat(self) -> None:
        self._assert_red(
            'cur.execute("DROP TABLE IF EXISTS " + name + " CASCADE")\n', "拼接出来的也必须红"
        )

    def test_guard_removed_from_a_real_module_turns_red(self) -> None:
        """把真文件里的 require_disposable_db 摘掉 —— 闸必须当场红。"""
        real = PROJECT_ROOT / "tests/integration/test_clients_ocr_history_rls_real_tables.py"
        stripped = real.read_text(encoding="utf-8").replace("require_disposable_db", "require_db")
        self._assert_red(stripped, "真模块摘掉哨兵调用后必须红")


class NoFalseAlarmTests(unittest.TestCase):
    """合法写法一处都不许报。误报一次这道闸就会被人静音,等于没装。"""

    def _assert_green(self, source: str, msg: str) -> None:
        code, findings = _scan_source(source)
        self.assertEqual(code, 0, msg)
        self.assertFalse([f for f in findings if f.verdict == "RED"], msg)

    def test_ddl_only_asserted_on_is_ignored(self) -> None:
        # tests/unit/test_workorder_schema.py 那一批:只断言迁移 SQL 文本里有这句
        self._assert_green(
            'self.assertIn("DROP TABLE IF EXISTS work_orders", text)\n',
            "断言 SQL 文本不是执行",
        )

    def test_ddl_in_docstring_is_ignored(self) -> None:
        self._assert_green('"""本迁移会 DROP TABLE 旧表。"""\nx = 1\n', "文档字符串不是执行")

    def test_ddl_in_comment_is_ignored(self) -> None:
        self._assert_green("# 早年这里 DROP TABLE 过\nx = 1\n", "注释不是执行")

    def test_delete_and_alter_are_out_of_scope(self) -> None:
        self._assert_green(
            'cur.execute("DELETE FROM clients WHERE id = %s")\n'
            'cur.execute("ALTER TABLE clients ADD COLUMN x TEXT")\n',
            "DELETE/ALTER 刻意不收:收了会把闸淹掉",
        )

    def test_module_that_calls_the_guard_is_green(self) -> None:
        self._assert_green(
            GUARD_LINE + 'cur.execute("DROP TABLE IF EXISTS users CASCADE")\n',
            "接了哨兵就放行",
        )

    def test_dropped_index_is_not_a_table(self) -> None:
        self._assert_green('cur.execute("DROP INDEX IF EXISTS idx_clients_tenant")\n', "索引不是表")


class RealTreeTests(unittest.TestCase):
    def test_gate_is_green_on_the_real_tree(self) -> None:
        self.assertEqual(gate.main([str(PROJECT_ROOT / "tests"), "--quiet"]), 0)

    def test_gate_actually_sees_something(self) -> None:
        """防空扫:真树上必须扫得到破坏性 DDL,数量掉到 60 以下先来看看是不是判据漂了。"""
        findings = gate.collect((PROJECT_ROOT / "tests",))
        self.assertGreaterEqual(len(findings), 60, "扫到的破坏性 DDL 太少,判据可能漂了")
        self.assertGreaterEqual(len({f.path for f in findings}), 25)

    def test_every_destructive_module_imports_the_guard(self) -> None:
        for path in sorted({f.path for f in gate.collect((PROJECT_ROOT / "tests",))}):
            text = (PROJECT_ROOT / path).read_text(encoding="utf-8")
            self.assertIn("require_disposable_db", text, f"{path} 会 DROP 真表却没接哨兵")

    def test_plain_require_db_still_exists_for_readonly_cases(self) -> None:
        """不破坏性的集成用例继续走 require_db —— 哨兵不该把它们一起挡掉。"""
        helpers = (PROJECT_ROOT / "tests/integration/_helpers.py").read_text(encoding="utf-8")
        self.assertIn("def require_db(", helpers)
        self.assertIn("def require_disposable_db(", helpers)


class _FakeCursor:
    def __init__(self, marked: bool) -> None:
        self._marked = marked
        self.queries: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.queries.append(sql)

    def fetchone(self):
        return ("_pearnly_disposable_test_db" if self._marked else None,)


class _FakeConn:
    def __init__(self, marked: bool) -> None:
        self.cur = _FakeCursor(marked)
        self.closed = False

    def cursor(self):
        return self.cur

    def close(self):
        self.closed = True


class DisposableGuardTests(unittest.TestCase):
    """哨兵函数四条分支。用假 psycopg2 顶掉真连接:分支判定要确定性可跑,
    真库那一路由手工反证覆盖(记在提交信息里)。"""

    def setUp(self) -> None:
        # tests/integration/_helpers.py 在 import 期 setdefault("RATE_LIMIT_ENABLED","false")。
        # 全量 discovery 里这一句会活到进程结束,而 test_ratelimit_limiter 排在本模块之后、
        # 在构造中间件时读这个 env —— 于是限流器被关掉,三条限流用例集体假绿式地"请求打到了
        # 应用层"。谁把 env 弄脏谁负责还原。
        env_before = os.environ.get("RATE_LIMIT_ENABLED")
        self.helpers = importlib.import_module("tests.integration._helpers")
        self.addCleanup(_restore_env, "RATE_LIMIT_ENABLED", env_before)
        self.helpers._DISPOSABLE_CHECKED.clear()
        self.addCleanup(self.helpers._DISPOSABLE_CHECKED.clear)

    def _install_fake_psycopg2(self, *, marked: bool = True, boom: Exception | None = None):
        conns: list[_FakeConn] = []

        def connect(dsn, **kwargs):
            if boom is not None:
                raise boom
            conn = _FakeConn(marked)
            conns.append(conn)
            return conn

        module = types.SimpleNamespace(connect=connect)
        real = sys.modules.get("psycopg2")
        sys.modules["psycopg2"] = module

        def restore():
            if real is None:
                sys.modules.pop("psycopg2", None)
            else:
                sys.modules["psycopg2"] = real

        self.addCleanup(restore)
        return conns

    def _env(self, **values: str) -> None:
        for key, value in values.items():
            old = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
            self.addCleanup(_restore_env, key, old)

    def test_without_integration_env_it_skips_like_before(self) -> None:
        self._env(PEARNLY_INTEGRATION_DB="", DATABASE_URL="postgresql://x/y")
        with self.assertRaises(unittest.SkipTest):
            self.helpers.require_disposable_db()

    def test_unreachable_db_is_a_skip_not_a_failure(self) -> None:
        self._env(PEARNLY_INTEGRATION_DB="1", DATABASE_URL="postgresql://x/y")
        self._install_fake_psycopg2(boom=OSError("connection refused"))
        with self.assertRaises(unittest.SkipTest):
            self.helpers.require_disposable_db()

    def test_unmarked_db_is_refused_loudly(self) -> None:
        """核心反证:没哨兵表就得抛错,不能 skip —— skip 会让人以为跑过了。"""
        self._env(PEARNLY_INTEGRATION_DB="1", DATABASE_URL="postgresql://x/unmarked")
        self._install_fake_psycopg2(marked=False)
        with self.assertRaises(RuntimeError) as ctx:
            self.helpers.require_disposable_db()
        self.assertIn("_pearnly_disposable_test_db", str(ctx.exception))
        self.assertNotIsInstance(ctx.exception, unittest.SkipTest)

    def test_marked_db_passes_and_is_only_probed_once(self) -> None:
        self._env(PEARNLY_INTEGRATION_DB="1", DATABASE_URL="postgresql://x/throwaway")
        conns = self._install_fake_psycopg2(marked=True)
        self.helpers.require_disposable_db()
        self.helpers.require_disposable_db()
        self.assertEqual(len(conns), 1, "同一个 DSN 只该探一次")
        self.assertTrue(conns[0].closed, "探完必须关连接")


if __name__ == "__main__":
    unittest.main()
