# -*- coding: utf-8 -*-
"""餐厅 POS 应用层隔离守门(AST 扫 services/pos/restaurant 每条 execute)。餐厅 POS · PO-R。

prod 角色 BYPASSRLS → RLS 不强制,真隔离=每条 DML 带 tenant_id + SQL 内插只许列常量/占位符(见
[[pos-rls-bypass-app-layer-isolation]])。本测试镜像 test_pos_inventory_sql_isolation,覆盖 restaurant 子目录
(原闸只扫 services/pos 顶层 *.py,不递归)。
"""

import ast
import pathlib
import unittest

_DIR = "services/pos/restaurant"
# 不直接读写业务表的纯编排/格式化文件(无 cur.execute)。
_DML_KEYWORDS = ("INSERT", "UPDATE", "DELETE", "SELECT")


def _string_of(node):
    """取 execute 第一参的 SQL 字面量(常量串 / f-string 拼接的常量片段合并)。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                out.append(v.value)
            else:
                out.append(" ")  # 占位(变量片段),不参与关键词判定
        return "".join(out)
    if isinstance(node, ast.BinOp):
        return (_string_of(node.left) or "") + (_string_of(node.right) or "")
    return None


def _collect_executes():
    stmts = []
    for f in sorted(pathlib.Path(_DIR).glob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "execute"
                and n.args
            ):
                sql = _string_of(n.args[0])
                if sql:
                    stmts.append((f.name, sql))
    return stmts


class RestaurantSqlIsolationTests(unittest.TestCase):
    def test_every_dml_filters_tenant_id(self):
        offenders = []
        for fname, sql in _collect_executes():
            up = sql.upper()
            if not any(k in up for k in _DML_KEYWORDS):
                continue
            # SAVEPOINT/RELEASE 等非业务 DML 不在 restaurant 层;这里都是表 DML。
            if "TENANT_ID" not in up:
                offenders.append(f"{fname}: {sql.strip()[:80]}")
        self.assertFalse(offenders, "DML 缺 tenant_id 过滤:\n" + "\n".join(offenders))

    def test_has_executes(self):
        # 保护:若重构挪走 DAL 导致 0 条 execute,提醒更新本闸路径。
        self.assertGreater(len(_collect_executes()), 20)


if __name__ == "__main__":
    unittest.main()
