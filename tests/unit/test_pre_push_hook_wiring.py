# -*- coding: utf-8 -*-
"""pre-push 钩子接线闸 · 钩子 ↔ docs/GATES.md ↔ 磁盘上的闸脚本三者不许漂。

出身(2026-07-31):`scripts/git-hooks/pre-push` 在仓里躺了两个月,而 `core.hooksPath`
从没指过它 —— 25 道闸只有进了 CI 的那几道真跑过。追根问底,没人装的直接原因是**没人知道
怎么装**:GATES.md 通篇讲「怎么自查」,唯独没有那一句 `git config core.hooksPath ...`。
所以本闸盯的不是钩子写得对不对,是三类「装了也白装」的漂移:

  1. 钩子调的闸脚本被改名/挪走 —— push 当场炸在 `No such file`,而且是在别人 push 的
     时候才炸,改名的人早就走了。
  2. 钩子加了闸但 GATES.md 没加行(反过来也算)—— GATES.md 是每个窗口开工第 0 步读的
     那页,它漏一道 = 那道闸对所有人都是隐形的,撞上了才知道。
  3. GATES.md 自己标题写「N 道闸」而表里不是 N 行 —— 清单式的闸必须配覆盖率断言,
     否则「闸报绿」只等于「没人数过」。

本闸只读文件、不跑 git、不看本机配置:CI 是全新 clone,`core.hooksPath` 在那儿本来就
是空的,断言它会把 CI 钉死。「这台机器装没装」由 `git config --get core.hooksPath` 自己
回答,不归本闸管。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = PROJECT_ROOT / "scripts" / "git-hooks" / "pre-push"
GATES_PATH = PROJECT_ROOT / "docs" / "GATES.md"

# 装钩子的唯一正规写法。钩子头注与 GATES.md 必须都写它,且写的是同一个值。
HOOKS_PATH_VALUE = "scripts/git-hooks"
INSTALL_COMMAND = f"git config core.hooksPath {HOOKS_PATH_VALUE}"

# 闸脚本引用:python scripts/x.py / node scripts/x.mjs 里的那个路径。
GATE_SCRIPT_RE = re.compile(r"scripts/[A-Za-z0-9_./-]+\.(?:py|mjs)")

# GATES.md 表体行:以 "| " 起头。表头也长这样,分隔行 "|---" 不是。
TABLE_ROW_RE = re.compile(r"^\| ", re.MULTILINE)
DECLARED_COUNT_RE = re.compile(r"^## (\d+) 道闸", re.MULTILINE)


def gate_scripts(text: str) -> set[str]:
    """文本里引用到的闸脚本路径集合。"""
    return set(GATE_SCRIPT_RE.findall(text))


def declared_gate_count(text: str) -> int | None:
    """GATES.md 标题自报的道数;没有那行标题则 None。"""
    m = DECLARED_COUNT_RE.search(text)
    return int(m.group(1)) if m else None


def table_row_count(text: str) -> int:
    """表体行数 = 以 '| ' 起头的行数 - 1 行表头。"""
    return max(len(TABLE_ROW_RE.findall(text)) - 1, 0)


def hooks_path_in_install_lines(text: str) -> set[str]:
    """文本里所有 `git config core.hooksPath <值>` 写的那个 <值>。

    收集成集合是为了抓「同一份文档里两处写了不同路径」——那种漂移读的人不会发现,
    照着错的那句装完 `--get` 也有输出,看起来还挺像装上了。
    """
    return set(re.findall(r"git config core\.hooksPath\s+([^\s`,;)]+)", text))


class HookFileTests(unittest.TestCase):
    """钩子文件本身:在、有内容、shell 能解析。"""

    def test_hook_file_exists(self):
        self.assertTrue(
            HOOK_PATH.is_file(),
            f"{HOOK_PATH} 不在了 —— core.hooksPath 指过来会静默无闸(git 找不到钩子就直接放行)",
        )

    def test_hook_is_not_a_stub(self):
        body = HOOK_PATH.read_text(encoding="utf-8")
        self.assertGreater(len(body.splitlines()), 50, "钩子被掏空成壳了")
        self.assertIn("exit 1", body, "钩子里没有 exit 1 —— 拦不住任何东西")

    def test_hook_forces_utf8_output(self):
        # Windows 控制台默认 cp874,闸脚本打中文会 UnicodeEncodeError → 退出码 1 →
        # 通过的闸报假红。这行掉了会让所有窗口在本机撞一堵看不懂的墙。
        body = HOOK_PATH.read_text(encoding="utf-8")
        self.assertIn("PYTHONIOENCODING=utf-8", body)

    @unittest.skipIf(
        os.name == "nt" and shutil.which("sh") is None,
        "本机没有 sh(Windows 且不在 Git Bash 环境);CI 是 ubuntu,那边不会跳过",
    )
    def test_hook_parses_as_shell(self):
        result = subprocess.run(["sh", "-n", str(HOOK_PATH)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"钩子语法错:{result.stderr}")


class GateScriptsResolveTests(unittest.TestCase):
    """钩子点名的每个闸脚本都得真在磁盘上。"""

    def setUp(self):
        self.hook_text = HOOK_PATH.read_text(encoding="utf-8")
        self.scripts = gate_scripts(self.hook_text)

    def test_extraction_is_not_empty(self):
        # 防空扫:正则一旦被改瞎,下面那条「全都存在」会对空集合恒真地报绿。
        self.assertGreaterEqual(len(self.scripts), 10, "从钩子里一个闸脚本都没抽出来 —— 判据空转了")

    def test_every_referenced_gate_script_exists(self):
        missing = sorted(s for s in self.scripts if not (PROJECT_ROOT / s).is_file())
        self.assertEqual(missing, [], f"钩子调了不存在的闸脚本(下次谁 push 谁撞):{missing}")


class HookAndGatesDocAgreeTests(unittest.TestCase):
    """钩子跑的闸 == GATES.md 写的闸(两个方向都查)。"""

    def setUp(self):
        self.hook_scripts = gate_scripts(HOOK_PATH.read_text(encoding="utf-8"))
        self.doc_scripts = gate_scripts(GATES_PATH.read_text(encoding="utf-8"))

    def test_no_undocumented_gate(self):
        undocumented = sorted(self.hook_scripts - self.doc_scripts)
        self.assertEqual(
            undocumented,
            [],
            f"钩子会跑但 GATES.md 没登记 —— 对所有窗口是隐形闸,撞上才知道:{undocumented}",
        )

    def test_no_documented_gate_that_never_runs(self):
        # GATES.md 里写了 `python scripts/x.py` 却没进钩子 = 纸面规矩。真要只在 CI 跑的
        # (如 pg-smoke)本来就不是 scripts/*.py 命令,不会落进这个集合。
        never_run = sorted(self.doc_scripts - self.hook_scripts)
        self.assertEqual(
            never_run,
            [],
            f"GATES.md 承诺了但 pre-push 不跑(纸面闸):{never_run}",
        )


class GatesDocSelfConsistentTests(unittest.TestCase):
    """GATES.md 标题自报的道数得等于表里真有的行数。"""

    def setUp(self):
        self.text = GATES_PATH.read_text(encoding="utf-8")

    def test_declared_count_matches_table_rows(self):
        declared = declared_gate_count(self.text)
        self.assertIsNotNone(declared, "GATES.md 没有 `## N 道闸` 那行标题")
        self.assertEqual(
            declared,
            table_row_count(self.text),
            "GATES.md 标题写的道数与表体行数对不上 —— 加了闸没加行 / 加了行没改标题",
        )


class InstallCommandDocumentedTests(unittest.TestCase):
    """装法必须白纸黑字写在 GATES.md 里,且与钩子头注同一个值。

    这条不是洁癖:钩子两个月没人装,直接原因就是没人知道该敲哪句。
    """

    def setUp(self):
        self.doc_text = GATES_PATH.read_text(encoding="utf-8")
        self.hook_text = HOOK_PATH.read_text(encoding="utf-8")

    def test_gates_doc_carries_copy_pasteable_install_command(self):
        self.assertIn(
            INSTALL_COMMAND,
            self.doc_text,
            f"GATES.md 里没有那句可复制的装法:`{INSTALL_COMMAND}`",
        )

    def test_hook_header_documents_the_same_path(self):
        self.assertIn(INSTALL_COMMAND, self.hook_text, "钩子头注里的安装说明不见了")

    def test_doc_and_hook_never_name_two_different_paths(self):
        paths = hooks_path_in_install_lines(self.doc_text) | hooks_path_in_install_lines(
            self.hook_text
        )
        self.assertEqual(
            paths,
            {HOOKS_PATH_VALUE},
            f"装法里出现了不止一个 hooksPath 值:{sorted(paths)} —— 照错的那句装,--get 一样有输出",
        )


class HelperCounterProofTests(unittest.TestCase):
    """给判据喂坏输入,确认它们真会喊 —— 上面那些绿不是因为判据是瞎的。"""

    def test_gate_scripts_finds_nothing_in_text_without_gates(self):
        self.assertEqual(gate_scripts("echo hello\nnpm run lint\n"), set())

    def test_gate_scripts_picks_up_both_python_and_node(self):
        text = "python scripts/check_a.py --quiet\nnode scripts/b_lint.mjs --gate\n"
        self.assertEqual(gate_scripts(text), {"scripts/check_a.py", "scripts/b_lint.mjs"})

    def test_declared_count_is_none_when_heading_missing(self):
        self.assertIsNone(declared_gate_count("# 手册\n\n没有道数标题\n"))

    def test_table_row_count_excludes_header_and_separator(self):
        table = "## 2 道闸\n\n| 闸 | 查什么 |\n|---|---|\n| a | x |\n| b | y |\n"
        self.assertEqual(table_row_count(table), 2)
        self.assertEqual(declared_gate_count(table), 2)

    def test_mismatched_count_is_detectable(self):
        table = "## 5 道闸\n\n| 闸 | 查什么 |\n|---|---|\n| a | x |\n"
        self.assertNotEqual(declared_gate_count(table), table_row_count(table))

    def test_missing_gate_in_doc_is_detectable(self):
        hook = "python scripts/check_new_gate.py --quiet\n"
        doc = "| 别的闸 | `python scripts/check_old.py` |\n"
        self.assertEqual(gate_scripts(hook) - gate_scripts(doc), {"scripts/check_new_gate.py"})

    def test_two_different_hooks_paths_are_detectable(self):
        text = (
            "装:`git config core.hooksPath scripts/git-hooks`\n"
            "或:`git config core.hooksPath .githooks`\n"
        )
        self.assertEqual(hooks_path_in_install_lines(text), {"scripts/git-hooks", ".githooks"})

    def test_backtick_and_punctuation_do_not_leak_into_the_path(self):
        # 文档里那句多半被反引号/句号包着,判据不能把 `scripts/git-hooks` 抓成带反引号的串。
        text = "想挂:`git config core.hooksPath scripts/git-hooks`(逐机器各设一次)。"
        self.assertEqual(hooks_path_in_install_lines(text), {"scripts/git-hooks"})


if __name__ == "__main__":
    unittest.main()
