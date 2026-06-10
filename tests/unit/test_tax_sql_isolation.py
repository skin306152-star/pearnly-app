# -*- coding: utf-8 -*-
"""报税应用层隔离机械闸(docs/tax-filing/01 §套账隔离机械闸 · 同做账闸范式)。

RLS 被 BYPASSRLS 架空 → 应用层每句 SQL 是唯一隔离防线。AST 扫 services/tax +
routes/tax_routes.py 每条 execute:
  1. 所有 DML 必带 tenant_id(DDL/SAVEPOINT 豁免)。
  2. 碰套账主表(tax_filings/tax_settings + 读侧 journal_vouchers/purchase_docs)
     必带 workspace_client_id(filing_lines 经 filing_id 归属,豁免)。
  3. SQL 内插点只能是列常量白名单,值一律 %s 参数化。"""

import ast
import pathlib
import re
import unittest

_FILES = sorted(pathlib.Path("services/tax").glob("*.py")) + [pathlib.Path("routes/tax_routes.py")]
_DML = re.compile(r"\b(SELECT|UPDATE|DELETE|INSERT)\b", re.I)
_DDL = re.compile(r"\b(create|alter|drop|comment\s+on)\b|set\s+local|savepoint", re.I)
_ALLOWED_INTERP = re.compile(r"^_?[A-Z][A-Z0-9_]*$")

_WS_TABLES = ("tax_filings", "tax_settings", "journal_vouchers", "purchase_docs")


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
    return "{COMPLEX}"


class TaxSqlIsolationTests(unittest.TestCase):
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
                if not _ALLOWED_INTERP.match(name):
                    bad.append(f"{fname}:{lineno} 内插 `{name}`")
        self.assertEqual(bad, [], "SQL 内插了非列常量:\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
