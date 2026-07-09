# -*- coding: utf-8 -*-
"""工单制应用层隔离机械闸(照 tests/unit/test_purchase_sql_isolation.py 同款配方)。

RLS 是第二道防线,应用层每句 SQL 才是隔离主力。AST 扫 services/workorder 每条
execute:① 所有 DML 必带 tenant_id(DDL/会话语句豁免)② f-string 内插点只能是
模块级全大写常量或受控 placeholders(杜绝把用户输入拼进 SQL 结构)。另加一条本域
专属闸:work_order_events 只准出现 INSERT/SELECT,不许出现 UPDATE/DELETE(§3 只追加
铁律的机械保证 —— 万一以后有人手滑加了改事件的函数,这里先红)。
"""

import ast
import pathlib
import re
import unittest

_DIRS = ("services/workorder",)
_DML = re.compile(r"\b(SELECT|UPDATE|DELETE|INSERT)\b", re.I)
_DDL = re.compile(r"\b(create|alter|drop|comment\s+on)\b|set\s+local|pg_advisory", re.I)
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


class WorkOrderSqlIsolationTests(unittest.TestCase):
    def test_every_dml_carries_tenant_id(self):
        missing = []
        for fname, lineno, arg in _iter_execute_calls():
            sql, _ = _sql_and_interps(arg)
            if not _DML.search(sql) or _DDL.search(sql):
                continue
            if "tenant_id" not in sql.lower():
                missing.append(f"{fname}:{lineno} → {sql.strip()[:90]}")
        self.assertEqual(missing, [], "DML 缺 tenant_id:\n" + "\n".join(missing))

    def test_sql_interpolations_are_column_constants_only(self):
        bad = []
        for fname, lineno, arg in _iter_execute_calls():
            sql, interps = _sql_and_interps(arg)
            if not _DML.search(sql):
                continue
            for name in interps:
                if not (_ALLOWED_INTERP.match(name) or name in _ALLOWED_NAMES):
                    bad.append(f"{fname}:{lineno} 内插 `{name}`(疑似拼接非常量)")
        self.assertEqual(bad, [], "SQL 内插非列常量(值必走 %s):\n" + "\n".join(bad))

    def test_work_order_events_never_updated_or_deleted(self):
        bad = []
        for fname, lineno, arg in _iter_execute_calls():
            if fname != "store.py":
                continue
            sql, _ = _sql_and_interps(arg)
            upper = sql.upper()
            if "WORK_ORDER_EVENTS" not in upper:
                continue
            if re.search(r"\bUPDATE\s+WORK_ORDER_EVENTS\b", upper) or re.search(
                r"\bDELETE\s+FROM\s+WORK_ORDER_EVENTS\b", upper
            ):
                bad.append(f"{fname}:{lineno} → {sql.strip()[:90]}")
        self.assertEqual(bad, [], "work_order_events 只追加,不许 UPDATE/DELETE:\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
