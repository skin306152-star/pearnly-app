# -*- coding: utf-8 -*-
"""超管 admin.js `_adminDate` 日期渲染契约(2026-08-27)。

锁住两件事:
  ① 完整 ISO 时间戳(created_at 等 postgres timestamptz 存 UTC)必须解析**真实时刻**并
     按 Asia/Bangkok(+7)呈现,不许再被日期前缀正则截成本地 00:00(用户看"xx:00"的
     创建/加入时间=全是假时间);
  ② 仅整串 `YYYY-MM-DD` 才按"日期"处理 —— 无时间语义,诚实显示当天 00:00。

`_adminDate` 是 admin.js 大 IIFE 内既有函数,本测试用真 node 子进程把函数体抽出来跑,
不加载整份 admin.js(否则顶层 DOM 访问当场炸)。抽法:从 `function _adminDate(` 起做
花括号配对取完整函数源。判据从真源读,不在测试里另抄一份正文(else admin.js 改了正文、
测试还按旧正文断言就永远照绿)。
"""

import json
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADMIN_JS = REPO_ROOT / "static" / "admin" / "admin.js"

# 曼谷渲染判据:UTC 03:00 是曼谷 10:00 · 而 2026-08-27 白天任意时刻都应 != 00:00。
_FIXED_UTC_ISO = "2026-08-27T03:00:00+00:00"
_FIXED_BKK_ISO = "2026-08-27T10:30:00+07:00"


def _run_node(cases: list) -> list:
    r"""真 node 子进程从 admin.js 抽 _adminDate 函数体并跑 cases,回 JSON。

    函数体抽取放 node 里做:只有 node 认 JS,省掉 Python→JS 字符串转义边界(函数体含
    `\d`/引号/正则,repr 拼接易踩坑)。抽法:从 `function _adminDate(` 起花括号配对。
    """
    payload = json.dumps(cases)
    script = """
const fs = require('fs');
const src = fs.readFileSync('static/admin/admin.js', 'utf-8');
const start = src.indexOf('function _adminDate(');
if (start < 0) throw new Error('_adminDate not found');
const braceStart = src.indexOf('{', start);
let depth = 0, end = -1;
for (let i = braceStart; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
}
const fn = new Function('return(' + src.slice(start, end) + ')')();
const cases = %s;
const out = cases.map(([input, withTime]) => ({ input, withTime, out: fn(input, withTime) }));
process.stdout.write(JSON.stringify(out));
""" % payload
    proc = subprocess.run(
        ["node", "-e", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        timeout=15,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"node failed: {proc.stderr.decode('utf-8', 'replace')}")
    return json.loads(proc.stdout.decode("utf-8"))


def _time_of(rendered: str) -> str:
    return rendered.split(" ")[1] if " " in rendered else ""


class AdminDateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = _run_node(
            [
                [_FIXED_UTC_ISO, True],
                [_FIXED_UTC_ISO, False],
                [_FIXED_BKK_ISO, True],
                ["2026-08-27", True],
                ["2026-08-27", False],
                ["", True],
                ["not-a-date", True],
            ]
        )
        cls.by = {(r["input"], r["withTime"]): r["out"] for r in cls.results}

    # ── 完整 ISO:必须解析真实时刻,不许截成 00:00 ──────────────────────

    def test_utc_iso_shows_real_bangkok_time_not_midnight(self):
        rendered = self.by[(_FIXED_UTC_ISO, True)]
        self.assertIn(" ", rendered, "含时间的 ISO 必须带 HH:MM")
        self.assertNotEqual(_time_of(rendered), "00:00", f"完整 ISO 被截成 00:00: {rendered}")
        # UTC 03:00 = 曼谷 10:00(佛历 2569 = 公历 2026)
        self.assertEqual(rendered, "2569-08-27 10:00")

    def test_utc_iso_date_is_bangkok_date(self):
        # 时间戳的日期也按曼谷落地,UTC 03:00 当天曼谷还是同一天。
        self.assertEqual(self.by[(_FIXED_UTC_ISO, False)], "2569-08-27")

    def test_bkk_offset_iso_is_preserved(self):
        # 已带 +07:00 的 ISO 直接解析出曼谷墙上时间,不二次偏移。
        self.assertEqual(self.by[(_FIXED_BKK_ISO, True)], "2569-08-27 10:30")

    # ── 日期-only:仍诚实 ──────────────────────────────────────────────

    def test_date_only_is_honest_with_time_shows_midnight(self):
        # 无时间语义 → 不带时间是日期,带时间是当天 00:00,不假装有真实时刻。
        self.assertEqual(self.by[("2026-08-27", False)], "2569-08-27")
        self.assertEqual(self.by[("2026-08-27", True)], "2569-08-27 00:00")

    # ── 边界与异常 ────────────────────────────────────────────────────

    def test_empty_input_returns_empty(self):
        self.assertEqual(self.by[("", True)], "")

    def test_invalid_input_returns_raw(self):
        self.assertEqual(self.by[("not-a-date", True)], "not-a-date")

    # ── 正则必须锚定全串(防回归把前缀正则改回来)────────────────────────

    def test_match_regex_is_end_anchored(self):
        # 根因是旧的 `/^(\d{4})-(\d{2})-(\d{2})/` 无 $,匹配 ISO 前缀即截断时间。
        src = ADMIN_JS.read_text(encoding="utf-8")
        self.assertIn(r"/^(\d{4})-(\d{2})-(\d{2})$/", src)


if __name__ == "__main__":
    unittest.main()
