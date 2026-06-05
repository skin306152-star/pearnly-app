"""机械闸:测试文件禁止 import pytest。

项目统一用 unittest(CI 跑 `unittest discover`;pytest 不在任何 requirements)。
凡引入 pytest 的测试,本地能过(因本地恰好装了 pytest),却在 CI 抛 ModuleNotFoundError
把 master 弄红 —— 本地假绿、CI 才爆,几乎每个窗口都踩。这道测试把规则机器化,
任何窗口都无法再引入这个坑。pytest 风格的迁移函数走
tests/unit/knowledge/_pytest_adapter.py 桥接到 unittest,运行期不依赖 pytest。
"""

import re
import unittest
from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parent.parent  # tests/
# 只匹配真 import 语句(行尾 / as 别名 / 行内注释收尾),不误伤散文里的 "import pytest"
_PYTEST_IMPORT = re.compile(
    r"^[ \t]*(?:"
    r"import[ \t]+pytest(?:[ \t]+as[ \t]+\w+)?[ \t]*(?:#.*)?$"
    r"|from[ \t]+pytest[\w.]*[ \t]+import[ \t]"
    r")",
    re.M,
)


class NoPytestDependencyTests(unittest.TestCase):
    def test_no_test_file_imports_pytest(self):
        offenders = [
            str(p.relative_to(_TESTS_ROOT))
            for p in _TESTS_ROOT.rglob("*.py")
            if _PYTEST_IMPORT.search(p.read_text(encoding="utf-8", errors="replace"))
        ]
        self.assertEqual(
            offenders,
            [],
            "测试文件禁止 import pytest(CI 不装 pytest → 本地假绿 / master 红)· "
            "改用 unittest 风格或 _pytest_adapter 桥接 · 命中:" + ", ".join(offenders),
        )
