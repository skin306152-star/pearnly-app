# -*- coding: utf-8 -*-
"""做账应用层隔离机械闸(docs/accounting/01 §套账隔离 · 同 POS 闸范式)。

RLS 被 BYPASSRLS 架空 → 应用层每句 SQL 是唯一隔离防线。AST 扫 services/accounting +
routes/accounting_routes.py 每条 execute:
  1. 所有 DML 必带 tenant_id(DDL/SAVEPOINT 豁免)。
  2. 碰套账主表(凭证/科目/映射/设置/记忆)必带 workspace_client_id
     (journal_lines 经 voucher_id 归属,豁免)。
  3. SQL 内插点只能是列常量/白名单,值一律 %s 参数化。"""

import ast
import pathlib
import re
import unittest

_FILES = sorted(pathlib.Path("services/accounting").glob("*.py")) + [
    pathlib.Path("routes/accounting_routes.py")
]
_DML = re.compile(r"\b(SELECT|UPDATE|DELETE|INSERT)\b", re.I)
_DDL = re.compile(r"\b(create|alter|drop|comment\s+on)\b|set\s+local|savepoint", re.I)
_ALLOWED_INTERP = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
_ALLOWED_NAMES = {"placeholders", "set_clause", "cols", "sql"}

# 套账隔离主表:每句 DML 必带 workspace_client_id。journal_lines 经 voucher 归属(行表无 ws 列)。
_WS_TABLES = (
    "chart_of_accounts",
    "account_mappings",
    "journal_vouchers",
    "accounting_settings",
    "review_learned",
)


def _iter_execute_calls():
    for f in _FILES:
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("execute", "executemany")
                and node.args
            ):
                yield f.name, node.lineno, node.args[0]


def _sql_and_interps(arg):
    text, interps = [], []

    def walk(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            text.append(n.value)
        elif isinstance(n, ast.JoinedStr):
            for v in n.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    text.append(v.value)
                elif isinstance(v, ast.FormattedValue):
                    interps.append(_name_of(v.value))
        elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            walk(n.left)
            walk(n.right)

    walk(arg)
    return " ".join(text), interps


def _name_of(expr):
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Attribute)
        and expr.func.attr == "join"
        and expr.args
    ):
        return _name_of(expr.args[0])
    return "{COMPLEX}"


class AccountingSqlIsolationTests(unittest.TestCase):
    def test_every_dml_carries_tenant_id(self):
        missing = []
        for fname, lineno, arg in _iter_execute_calls():
            sql, _ = _sql_and_interps(arg)
            if not _DML.search(sql) or _DDL.search(sql):
                continue
            if "tenant_id" not in sql.lower():
                missing.append(f"{fname}:{lineno} → {sql.strip()[:90]}")
        self.assertEqual(missing, [], "DML 缺 tenant_id:\n" + "\n".join(missing))

    def test_workspace_tables_carry_workspace_client_id(self):
        missing = []
        for fname, lineno, arg in _iter_execute_calls():
            sql, _ = _sql_and_interps(arg)
            if not _DML.search(sql) or _DDL.search(sql):
                continue
            low = sql.lower()
            if any(t in low for t in _WS_TABLES) and "workspace_client_id" not in low:
                missing.append(f"{fname}:{lineno} → {sql.strip()[:90]}")
        self.assertEqual(missing, [], "套账主表 DML 缺 workspace_client_id:\n" + "\n".join(missing))

    def test_sql_interpolations_are_column_constants_only(self):
        bad = []
        for fname, lineno, arg in _iter_execute_calls():
            sql, interps = _sql_and_interps(arg)
            if not _DML.search(sql):
                continue
            for name in interps:
                if not (_ALLOWED_INTERP.match(name) or name in _ALLOWED_NAMES):
                    bad.append(f"{fname}:{lineno} 内插 `{name}`")
        self.assertEqual(bad, [], "SQL 内插了非列常量:\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
