#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_dms_push_friendly.py

DMS 推送可视化闭环(Zihao 2026-06-01)· 身份证→订车单错误码 4 语友好文案守门。

背景:身份证订车流程的 ERR_ID_CARD_* / ERR_DMS_* 码不在 mrerp_business_friendly 的
发票推送 catalog 里,friendly_for_ui 返回 None → 日志/详情裸露 ERR_*(Zihao 指出问题)。
本测锁:① 每个 DMS 码都有 zh/th/en/ja 4 语非空 ② friendly_any 发票优先、DMS 兜底
③ 长码 ERR_DMS_IMPORT_REPORT 不被 ERR_DMS_IMPORT 子串抢占。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import push_log_queries as plq  # noqa: E402

LANGS = ("zh", "th", "en", "ja")


class TestDmsPushFriendly(unittest.TestCase):
    def test_every_dms_code_has_4_langs_nonempty(self):
        for code, d in plq._DMS_PUSH_FRIENDLY.items():
            for lang in LANGS:
                self.assertIn(lang, d, f"{code} 缺 {lang}")
                self.assertTrue(str(d[lang]).strip(), f"{code}.{lang} 空")

    def test_dms_push_friendly_hits_known_codes(self):
        for code in plq._DMS_PUSH_FRIENDLY:
            d = plq.dms_push_friendly(f"some prefix {code} trailing detail")
            self.assertIsNotNone(d, f"{code} 未命中")
            self.assertTrue(d["ja"].strip())

    def test_import_report_not_shadowed_by_import(self):
        d = plq.dms_push_friendly("ERR_DMS_IMPORT_REPORT")
        self.assertEqual(d, plq._DMS_PUSH_FRIENDLY["ERR_DMS_IMPORT_REPORT"])
        self.assertNotEqual(d, plq._DMS_PUSH_FRIENDLY["ERR_DMS_IMPORT"])

    def test_dms_push_friendly_none_on_unknown_or_empty(self):
        self.assertIsNone(plq.dms_push_friendly(None))
        self.assertIsNone(plq.dms_push_friendly(""))
        self.assertIsNone(plq.dms_push_friendly("ERR_TOTALLY_UNRELATED"))

    def test_friendly_any_falls_back_to_dms(self):
        # 身份证订车码:catalog 不覆盖 → 退 DMS 映射
        d = plq.friendly_any("ERR_ID_CARD_REQUIRED_FIELDS")
        self.assertIsNotNone(d)
        self.assertIn("ja", d)
        self.assertTrue(d["ja"].strip())

    def test_friendly_any_none_on_gibberish(self):
        self.assertIsNone(plq.friendly_any("ERR_TOTALLY_UNRELATED_XYZ"))
        self.assertIsNone(plq.friendly_any(None))


if __name__ == "__main__":
    unittest.main()
