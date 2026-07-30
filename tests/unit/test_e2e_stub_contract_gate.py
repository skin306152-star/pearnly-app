# -*- coding: utf-8 -*-
"""E2E 桩回包契约闸(scripts/check_e2e_stub_contracts.py)的三道锁。

闸本身只会按登记表比对,所以真正要防的是三件事:
  ① 登记表与真后端漂了 —— 用 ast 读 routes/steward_routes.py 的无条件返回字面量,
     逐键比对登记表。后端给某个端点加一个键,这里当场红,逼登记表跟着改。
  ② 登记表烂在那没人桩 —— 覆盖率:每个登记端点都必须真被至少一个 spec 桩到。
  ③ 闸根本没看 —— 反证:喂故意少键 / 写成 null 的桩,闸必须红;合法写法不许误报。
     清单式闸不喂坏样本,「PASS」分不清是代码干净还是闸眼瞎(本仓两周内栽过两次)。

顺带锁住桩用的那份上传限额 fixture 与 attachments.limits() 逐键相等 —— 键齐了值是编的,
拍出来的还是产品里不存在的界面。刷新命令见 test_limits_fixture_matches_backend。
"""

import ast
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_MOD_PATH = ROOT / "scripts" / "check_e2e_stub_contracts.py"
_spec = importlib.util.spec_from_file_location("check_e2e_stub_contracts", _MOD_PATH)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

E2E_DIR = ROOT / "tests" / "e2e"
STEWARD_ROUTES = ROOT / "routes" / "steward_routes.py"
LIMITS_FIXTURE = E2E_DIR / "_fixtures_steward_limits.json"


def _tracked_specs():
    """git 跟踪的 spec(仓库相对 · posix)。

    覆盖率只按跟踪文件算:开发机上常年躺着一批未跟踪的本机验收脚本(实测 2 个文件贡献
    4 处桩点),拿它们凑数会让「真树上读出了几处」在本机虚高、到 CI 少一截。
    """
    out = subprocess.run(
        ["git", "ls-files", "tests/e2e/*.spec.js"],
        cwd=str(ROOT),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    files = {line.strip() for line in out.stdout.splitlines() if line.strip()}
    if not files:
        raise AssertionError("git ls-files 一个 spec 都没列出来 —— 覆盖率判据会空转")
    return files


STATUS_STUB = """const { test } = require('@playwright/test');
test('x', async ({ page }) => {
    await page.route('**/api/ai/steward/status', (r) => r.fulfill({ json: %s }));
});
"""


def _returned_keys(func):
    """处理函数 → 它**无条件**回的顶层键。

    条件分支里补的键(get_session 的 current_task_id)不算 —— 那种键桩里可有可无,
    写进登记表就会对合法的桩误报。
    """
    literals = {}
    for node in func.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    literals[target.id] = node.value
    for node in func.body:
        if not isinstance(node, ast.Return):
            continue
        value = node.value
        if isinstance(value, ast.Name):
            value = literals.get(value.id)
        if isinstance(value, ast.Dict):
            return {k.value for k in value.keys if isinstance(k, ast.Constant)}
    return None


def _handlers(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


class ContractDriftTests(unittest.TestCase):
    """① 登记表 == 真后端的无条件投影。"""

    def setUp(self):
        self.handlers = _handlers(STEWARD_ROUTES)

    def test_every_contract_matches_backend_projection(self):
        for contract in gate.CONTRACTS:
            with self.subTest(contract["id"]):
                func = self.handlers.get(contract["handler"])
                self.assertIsNotNone(func, f"{contract['handler']} 在 {STEWARD_ROUTES.name} 里没了")
                backend = _returned_keys(func)
                self.assertIsNotNone(backend, "读不出该处理函数的返回字面量 —— 闸的登记表失去依据")
                self.assertEqual(
                    backend,
                    set(contract["keys"]),
                    f"{contract['id']} 的后端投影变了:登记表 {sorted(contract['keys'])} "
                    f"→ 真后端 {sorted(backend)}。改 CONTRACTS,并把各 spec 的桩补齐",
                )

    def test_status_carries_attachment_limits(self):
        # 出事的就是这一键:闸关也带,前端据此画回形针。钉死它,别哪天被当成条件键删了。
        self.assertIn("attachments", _returned_keys(self.handlers["get_status"]))


class CoverageTests(unittest.TestCase):
    """② 登记表里的端点都真被桩过 —— 没人桩的登记项 = 迟早烂掉没人发现。"""

    def setUp(self):
        tracked = _tracked_specs()
        self.sites = [s for s in gate.all_sites(E2E_DIR) if not s.loose and s.rel in tracked]

    def test_every_contract_is_stubbed_by_some_spec(self):
        stubbed = {s.contract["id"] for s in self.sites}
        for contract in gate.CONTRACTS:
            with self.subTest(contract["id"]):
                self.assertIn(
                    contract["id"],
                    stubbed,
                    "登记了却没有任何 spec 桩它:要么端点没了(删登记),要么闸认不出这种写法",
                )

    def test_every_contract_has_a_readable_stub(self):
        # 闸报绿也可能是「一处形状都没读出来」。判据按登记端点逐个来,不数总数 ——
        # 总数会随开发机上未跟踪的本机脚本上下浮动,写死一个门槛就是本机绿 CI 红。
        readable = [s for s in self.sites if s.keys]
        self.assertTrue(readable, "跟踪的 spec 里一处回包形状都没读出来 —— 闸在空扫")
        for contract in gate.CONTRACTS:
            with self.subTest(contract["id"]):
                self.assertTrue(
                    any(s.contract["id"] == contract["id"] for s in readable),
                    "这个端点只被认出路径、形状一处都没读出来 —— 少键那半截判据形同虚设",
                )

    def test_real_tree_is_green(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = gate.main(["--dir", str(E2E_DIR)])
        self.assertEqual(code, 0, buf.getvalue())


class GateFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def write(self, name, text):
        (self.dir / name).write_text(text, encoding="utf-8")

    def run_gate(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = gate.main(["--dir", str(self.dir)])
        return code, buf.getvalue()

    def assertGreen(self):
        code, out = self.run_gate()
        self.assertEqual(code, 0, out)
        return out

    def assertRed(self, needle):
        code, out = self.run_gate()
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)
        return out


class CounterEvidenceTests(GateFixture):
    """③ 反证:每一种「比真后端少给」的写法都必须红。"""

    def test_status_missing_attachments_fails(self):
        self.write("a.spec.js", STATUS_STUB % "{ enabled: true }")
        self.assertRed("attachments")

    def test_status_attachments_null_fails(self):
        # 键在值不在:前端 `resp && resp.attachments` 拿到 null,回形针照样不画。
        self.write("a.spec.js", STATUS_STUB % "{ enabled: true, attachments: null }")
        self.assertRed("写成 null")

    def test_status_attachments_undefined_fails(self):
        self.write("a.spec.js", STATUS_STUB % "{ enabled: true, attachments: undefined }")
        self.assertRed("写成 undefined")

    def test_dispatcher_style_missing_key_fails(self):
        self.write(
            "a.spec.js",
            "function json(route, payload) {\n"
            "    return route.fulfill({ body: JSON.stringify(payload) });\n"
            "}\n"
            "page.route('**/api/ai/steward/**', (r) => {\n"
            "    const p = new URL(r.request().url()).pathname;\n"
            "    if (p.endsWith('/steward/status')) return json(r, { enabled: true });\n"
            "});\n",
        )
        self.assertRed("attachments")

    def test_session_view_missing_messages_fails(self):
        self.write(
            "a.spec.js",
            "page.route('**/api/ai/steward/sessions/s-1', (r) =>\n"
            "    r.fulfill({ json: { session_id: 's-1' } })\n"
            ");\n",
        )
        self.assertRed("messages")

    def test_payload_from_helper_function_is_followed(self):
        # 回包藏在同文件的工厂函数里也要跟进去,否则「换个写法」就绕过整道闸。
        self.write(
            "a.spec.js",
            "function session() {\n"
            "    const view = { session_id: 's1' };\n"
            "    return view;\n"
            "}\n"
            "page.route('**/api/ai/steward/sessions/s-1', (r) =>\n"
            "    r.fulfill({ json: session() })\n"
            ");\n",
        )
        self.assertRed("messages")

    def test_unreadable_payload_is_reported_not_green(self):
        self.write(
            "a.spec.js",
            "page.route('**/api/ai/steward/status', (r) => r.fulfill({ json: buildIt() }));\n",
        )
        self.assertRed("读不出")


class NoFalseAlarmTests(GateFixture):
    """合法写法不许误报 —— 一开始就误报的闸会被 skip 掉,还不如不装。"""

    def test_full_status_stub_passes(self):
        self.write("a.spec.js", STATUS_STUB % "{ enabled: false, attachments: LIMITS }")
        self.assertGreen()

    def test_fault_injection_non_2xx_is_not_a_contract(self):
        self.write(
            "a.spec.js",
            "page.route('**/api/ai/steward/status', (r) =>\n"
            '    r.fulfill({ status: 401, body: \'{"detail":"auth.expired"}\' })\n'
            ");\n",
        )
        self.assertGreen()

    def test_path_in_assertion_is_not_a_stub(self):
        self.write(
            "a.spec.js",
            "const n = posts.filter((x) => x.path.endsWith('/steward/sessions'));\n"
            "expect(n.length).toBe(1);\n"
            "page.route('**/api/ai/steward/status', (r) =>\n"
            "    r.fulfill({ json: { enabled: true, attachments: LIMITS } })\n"
            ");\n",
        )
        self.assertGreen()

    def test_unregistered_endpoint_is_ignored(self):
        self.write(
            "a.spec.js",
            "page.route('**/api/ai/steward/sessions/*/messages', (r) =>\n"
            "    r.fulfill({ json: { reply: 'ok' } })\n"
            ");\n",
        )
        self.assertGreen()

    def test_commented_out_stub_is_ignored(self):
        self.write(
            "a.spec.js",
            "// 旧写法:page.route('**/api/ai/steward/status', (r) => r.fulfill({ json: {} }));\n",
        )
        self.assertGreen()

    def test_conditional_limits_variant_passes(self):
        # 「故意不给限额」是被验的一条真分支(f1 的 noLimits),三元不是裸 null,不该判红。
        self.write(
            "a.spec.js",
            STATUS_STUB % "{ enabled: true, attachments: opts.noLimits ? undefined : LIMITS }",
        )
        self.assertGreen()


class LimitsFixtureTests(unittest.TestCase):
    """桩里那份限额值必须是后端的真值(键齐了值是编的,照样拍到不存在的界面)。"""

    def test_limits_fixture_matches_backend(self):
        from services.steward import attachments

        fixture = json.loads(LIMITS_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(
            fixture,
            attachments.limits(),
            '限额 fixture 与后端漂了,重新生成:python -c "import json;'
            "from services.steward import attachments;"
            'print(json.dumps(attachments.limits(), ensure_ascii=False, indent=4))"',
        )


if __name__ == "__main__":
    unittest.main()
