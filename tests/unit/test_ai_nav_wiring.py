"""/ai 侧栏导航接线闸:壳里的 nav id 与 ai.js 的 navJumps 表必须双向对齐。

2026-08-05 生产实锤:navSteward 在壳里可见(闸开)却没进点击接线,按钮点了毫无反应
(hash 不变、视图不切、console 零报错)——纯静态检查抓不到这种「漏一行就是死按钮」,
本测试把接线表与壳做双向核对,漏绑或僵尸键都当场红。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _nav_jump_ids(js):
    block = re.search(r"var navJumps = \{(.*?)\};", js, re.S)
    if not block:
        return None
    return re.findall(r"^\s*(\w+):", block.group(1), re.M)


class AiNavWiringTest(unittest.TestCase):
    def test_every_sidebar_nav_id_is_wired(self):
        html = _read("static/ai/ai.html")
        nav_ids = re.findall(r'<a[^>]*\bid="(nav[A-Za-z]+)"', html)
        self.assertIn("navSteward", nav_ids)
        wired = _nav_jump_ids(_read("static/ai/ai.js"))
        self.assertIsNotNone(wired, "ai.js 里找不到 navJumps 表(改名要同步本测试)")
        missing = [i for i in nav_ids if i not in wired]
        self.assertEqual(missing, [], f"侧栏项没进接线表 = 死按钮:{missing}")

    def test_wired_ids_exist_in_shell(self):
        html = _read("static/ai/ai.html")
        wired = _nav_jump_ids(_read("static/ai/ai.js"))
        ghosts = [i for i in wired if f'id="{i}"' not in html]
        self.assertEqual(ghosts, [], f"接线表引用了壳里不存在的 id:{ghosts}")


if __name__ == "__main__":
    unittest.main()
