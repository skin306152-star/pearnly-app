# -*- coding: utf-8 -*-
"""POS/库存应用层隔离机械闸(POS 项目 · 安全审计 · docs/pos/10 §5)。

RLS 被 BYPASSRLS 架空(见 memory pos-rls-bypass-app-layer-isolation),应用层每句 SQL 是唯一
隔离防线。本测试 AST 扫 services/pos + services/inventory 每条 execute:
  1. 所有 DML(SELECT/UPDATE/DELETE/INSERT)必带 tenant_id(DDL/会话语句豁免)。
  2. SQL 里的 f-string/字符串拼接内插点只能是「全大写模块常量」或 placeholders(列名白名单),
     杜绝把用户输入拼进 SQL 结构(值一律 %s 参数化)。
新增/改 SQL 漏带 tenant_id 或拼接用户输入 → 本闸红。"""

import ast
import pathlib
import re
import unittest

_DIRS = ("services/pos", "services/inventory")
_DML = re.compile(r"\b(SELECT|UPDATE|DELETE|INSERT)\b", re.I)
_DDL = re.compile(r"\b(create|alter|drop|comment\s+on)\b|set\s+local", re.I)
# 允许内插进 SQL 的标识符:全大写常量(列清单)、或生成的 placeholders 串。
_ALLOWED_INTERP = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
_ALLOWED_NAMES = {"placeholders", "set_clause", "cols", "sql"}


def _iter_execute_calls():
    for d in _DIRS:
        for f in sorted(pathlib.Path(d).glob("*.py")):
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
    """拼出 SQL 字面量 + 收集所有非字面量内插点的标识符名。"""
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
    # ", ".join(cols) / ", ".join(...) → 取被 join 的标识符(列名拼接,非值)。
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Attribute)
        and expr.func.attr == "join"
        and expr.args
    ):
        return _name_of(expr.args[0])
    return "{COMPLEX}"


class SqlIsolationTests(unittest.TestCase):
    def test_every_dml_carries_tenant_id(self):
        missing = []
        for fname, lineno, arg in _iter_execute_calls():
            sql, _ = _sql_and_interps(arg)
            if not _DML.search(sql):
                continue
            if _DDL.search(sql):
                continue
            if "tenant_id" not in sql.lower():
                missing.append(f"{fname}:{lineno} → {sql.strip()[:90]}")
        self.assertEqual(missing, [], "DML 缺 WHERE/含 tenant_id:\n" + "\n".join(missing))

    def test_sql_interpolations_are_column_constants_only(self):
        bad = []
        for fname, lineno, arg in _iter_execute_calls():
            sql, interps = _sql_and_interps(arg)
            if not _DML.search(sql):
                continue
            for name in interps:
                if not (_ALLOWED_INTERP.match(name) or name in _ALLOWED_NAMES):
                    bad.append(f"{fname}:{lineno} 内插 `{name}`(疑似拼接非常量)")
        self.assertEqual(bad, [], "SQL 内插了非列常量(值必须走 %s 参数化):\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
