# -*- coding: utf-8 -*-
"""回归闸 · 找回密码邮件的 SMTP 主通道 import 必须指向定义处。

背景(2026-07-09 生产事故):`_send_password_reset_via_email` 曾写
`from app import _smtp_send_email`,但 app.py 只 include 了 auth_email_code_routes
的 router,并未把 `_smtp_send_email` 提升到 app 命名空间——该 import 每次 ImportError、
被 except 静默吞掉,SMTP 主通道形同虚设,全部退到未验证发件人的 Resend 而发不出,
password_reset_log 全记 audit_only,用户永远收不到重置邮件(前端却显示"已发送")。

这条测试用纯 AST 静态检查锁死该坑,不拉起 fastapi 依赖链。
"""

import ast
import os
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(path):
    with open(os.path.join(_ROOT, path), encoding="utf-8") as f:
        return f.read()


def _imports_of(path):
    """收集模块内所有 `from X import name` 三元组 (module, name, lineno)。"""
    src = _read(path)
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                out.append((node.module, alias.name, node.lineno))
    return out


class ResetEmailChannelImportGuard(unittest.TestCase):
    def test_smtp_import_targets_definition_module(self):
        imports = _imports_of("routes/auth_password_routes.py")
        smtp = [(m, n) for (m, n, _l) in imports if n == "_smtp_send_email"]
        self.assertTrue(smtp, "auth_password_routes 应导入 _smtp_send_email")
        for module, _name in smtp:
            self.assertEqual(
                module,
                "routes.auth_email_code_routes",
                "_smtp_send_email 必须从定义处 routes.auth_email_code_routes 导入,"
                "不能从 app(app 只 include router,不提升该函数名 → 静默 ImportError)",
            )

    def test_app_does_not_export_smtp_sender(self):
        """坐实 `from app import _smtp_send_email` 之所以坏:app 顶层无此名字。"""
        src = _read("app.py")
        top = set()
        for node in ast.parse(src).body:
            if isinstance(node, ast.ImportFrom):
                top.update(a.asname or a.name for a in node.names)
            elif isinstance(node, ast.Import):
                top.update(a.asname or a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.FunctionDef):
                top.add(node.name)
            elif isinstance(node, ast.Assign):
                top.update(t.id for t in node.targets if isinstance(t, ast.Name))
        self.assertNotIn(
            "_smtp_send_email",
            top,
            "app.py 顶层不导出 _smtp_send_email——任何 `from app import _smtp_send_email` 都会 ImportError",
        )

    def test_smtp_sender_is_defined_in_email_code_routes(self):
        src = _read("routes/auth_email_code_routes.py")
        defined = any(
            isinstance(n, ast.FunctionDef) and n.name == "_smtp_send_email"
            for n in ast.parse(src).body
        )
        self.assertTrue(defined, "_smtp_send_email 应定义在 routes/auth_email_code_routes.py")


if __name__ == "__main__":
    unittest.main()
