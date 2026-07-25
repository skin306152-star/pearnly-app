# -*- coding: utf-8 -*-
"""跨仓库端到端:小助手建库存档猜了单位 → 推送日志上标出来。

这条缝今天断过三次(字段没接 / 函数没调 / 键名对不上),所以不许两头各测各的半截。本文件
一路压过去,任何一段字段名对不上都红:

  ① 小助手真跑 —— 真 DBF 账套上推一张没写单位的库存票,拿它**真实产出**的 line_modes;
  ② 主站派生 —— 同一份回执喂 push_log_meta,必须派生出 unit_guessed_lines / unit_guessed_codes;
  ③ 列表接线 —— 派生走的是 _derive_v3_meta,列表项才带得上这两个键;
  ④ 前端读的是同两个键 —— 卡片源码里读的键名必须就是 ② 产出的那几个;
  ⑤ 四语文案齐 —— 卡片用到的 i18n 键在四个语种里都在,且占位符对得上。

①拿不到时(没配 PEARNLY_REAL_ACCT / 没有小助手源码)退到 _GOLDEN —— 一份从真账套跑出来的
回执快照,测试照跑不 skip;小助手在场时还会拿真跑结果和快照对一遍,快照过期就红。
真浏览器渲染另有 scripts/_erp_unit_guessed_ui_verify.cjs(琥珀标记 getComputedStyle + 四语截图)。
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import push_log_meta as meta  # noqa: E402
from services.erp import push_log_queries as q  # noqa: E402

# 小助手真跑出来的回执快照(70EXP 真账套 · 票面 unit="" · 新品)。字段名就是两仓库的契约。
_GOLDEN = {
    "ok": True,
    "line_modes": [
        {
            "seq": 1,
            "name": "PEARNLY PROBE ITEM",
            "mode": "stock_item",
            "stkcod": "PN00054",
            "reason": "",
            "created": True,
            "unit_guessed": True,
            "unit_code": "พค",
        }
    ],
}

_COMPANION_SRC = Path(
    os.environ.get("PEARNLY_COMPANION_SRC", PROJECT_ROOT.parent / "pearnly-companion" / "src")
)
_REAL_ACCT = os.environ.get("PEARNLY_REAL_ACCT", "")


def _companion_line_modes():
    """真跑小助手:真账套副本上推一张没写单位的库存进货票,返回它产出的 line_modes。

    缺账套/缺小助手源码/缺 dbf 包 → None(退快照)。绝不写源目录,一律先 copytree。
    """
    if not (_REAL_ACCT and (Path(_REAL_ACCT) / "STMAS.DBF").is_file()):
        return None
    if not (_COMPANION_SRC / "companion" / "stock_purchase.py").is_file():
        return None
    if str(_COMPANION_SRC) not in sys.path:
        sys.path.insert(0, str(_COMPANION_SRC))
    try:
        from companion import stock_purchase
    except ImportError:  # dbf 包不在本环境
        return None
    tmp = Path(tempfile.mkdtemp())
    try:
        acct = tmp / "acct"
        shutil.copytree(_REAL_ACCT, acct)
        modes, _by_acc = stock_purchase.write_stock_in_lines(
            acct,
            "SEAM-001",
            dt.date(2026, 5, 31),
            [{"name": "PEARNLY SEAM ITEM", "qty": "3", "amount": "300.00", "unit": ""}],
            "SEAMSUP",
        )
        return json.loads(json.dumps(modes, default=str))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class UnitGuessedSeamTests(unittest.TestCase):
    """一条测试压在缝上:小助手猜了单位 → 卡片标出来。"""

    @classmethod
    def setUpClass(cls):
        cls.live = _companion_line_modes()
        cls.body = {"ok": True, "line_modes": cls.live} if cls.live else _GOLDEN
        cls.card_src = (PROJECT_ROOT / "src" / "home" / "erp-log-card.ts").read_text(
            encoding="utf-8"
        )
        cls.i18n_src = (PROJECT_ROOT / "static" / "i18n-data.js").read_text(encoding="utf-8")

    # ① 小助手真跑:回执确实带着「猜了单位」
    def test_companion_reports_the_guess_on_a_real_account(self):
        if not self.live:
            self.skipTest("没配 PEARNLY_REAL_ACCT / 没有小助手源码 —— 走快照,见下面几条")
        line = self.live[0]
        self.assertTrue(line["unit_guessed"], f"小助手没标「单位是猜的」:{line}")
        self.assertTrue(line["unit_code"], "标了猜却没回传猜的是哪个单位码")
        self.assertTrue(line["created"], "这条本该是新建的库存品")

    def test_golden_snapshot_still_matches_the_companion(self):
        """快照过期 = 后面几条其实在测一份已经不存在的契约,必须红。"""
        if not self.live:
            self.skipTest("小助手不在场,无从比对")
        self.assertEqual(
            set(self.live[0]) & {"unit_guessed", "unit_code", "created", "mode", "reason"},
            set(_GOLDEN["line_modes"][0])
            & {"unit_guessed", "unit_code", "created", "mode", "reason"},
            "小助手回执的键名变了,_GOLDEN 快照没跟着改",
        )

    # ② 主站派生:同一份回执必须派生出标注要的两个标量
    def test_backend_derives_the_marker_from_that_receipt(self):
        out = meta.derive_guessed_unit(self.body)
        self.assertEqual(out["unit_guessed_lines"], 1)
        self.assertTrue(out["unit_guessed_codes"], "猜的单位码没带出来,提示条会显空")

    # ③ 列表接线:走的是列表项真正用的那条派生路径
    def test_list_item_carries_it_through_v3_meta(self):
        out = meta._derive_v3_meta(self.body)
        self.assertEqual(out["unit_guessed_lines"], 1)
        self.assertIs(q._derive_v3_meta, meta._derive_v3_meta)  # DAL 与派生同一个对象

    # ④ 前端读的键名 = 后端产出的键名
    def test_card_reads_exactly_the_keys_the_backend_emits(self):
        for key in meta.derive_guessed_unit(self.body):
            self.assertIn(f"log.{key}", self.card_src, f"卡片没读 {key} —— 后端派生了但前端取不到")

    # ⑤ 卡片用到的文案键四语齐全,且占位符与卡片传的参数对得上
    def test_card_i18n_keys_exist_in_every_language(self):
        keys = sorted(set(re.findall(r"t\('(erp-unit-guessed-[a-z-]+)'", self.card_src)))
        self.assertEqual(keys, ["erp-unit-guessed-note", "erp-unit-guessed-tag"])
        for key in keys:
            self.assertEqual(self.i18n_src.count(f"'{key}':"), 4, f"{key} 不是四语齐全")
        for placeholder in ("{n}", "{u}"):  # 卡片传 n/u,文案里少一个就显不出来
            self.assertIn(placeholder, _note_text(self.i18n_src))

    # 阴性对照:没猜过的单不许被标
    def test_nothing_marked_when_the_unit_came_from_the_invoice(self):
        clean = {
            "ok": True,
            "line_modes": [
                {
                    "seq": 1,
                    "mode": "stock_item",
                    "created": True,
                    "unit_guessed": False,
                    "unit_code": "",
                }
            ],
        }
        self.assertEqual(meta.derive_guessed_unit(clean), {})
        self.assertNotIn("unit_guessed_lines", meta._derive_v3_meta(clean))

    def test_bad_shapes_do_not_raise(self):
        for body in (None, "not a dict", {}, {"line_modes": "nope"}, {"line_modes": [None, "x"]}):
            self.assertEqual(meta.derive_guessed_unit(body), {})

    def test_codes_are_deduped_and_ordered(self):
        body = {
            "line_modes": [
                {"unit_guessed": True, "unit_code": "พค"},
                {"unit_guessed": True, "unit_code": "กน"},
                {"unit_guessed": True, "unit_code": "พค"},
            ]
        }
        out = meta.derive_guessed_unit(body)
        self.assertEqual(out["unit_guessed_lines"], 3)
        self.assertEqual(out["unit_guessed_codes"], ["พค", "กน"])


def _note_text(i18n_src: str) -> str:
    """四语 note 文案拼一串(只为查占位符在不在,不比对具体译文)。"""
    return "".join(re.findall(r"'erp-unit-guessed-note': '([^']*)'", i18n_src))


if __name__ == "__main__":
    unittest.main()
