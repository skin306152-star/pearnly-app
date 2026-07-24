#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_express_stock_friendly.py

Express 本地小助手「库存过账」回执码 4 语友好文案守门(2026-07-23 真料排障 F1)。

背景:小助手推库存模式失败时回 DBF_WRITE_FAILED / STOCK_ITEM_NOT_FOUND —— 这两码不带
ERR_ 前缀、不在 mrerp_business_friendly 发票 catalog 里,friendly_any 未收录时原始码直接
裸露在推送日志/详情/异常里给泰国会计看。本测锁:① 每码 zh/th/en/ja 4 语非空 ② 真实
error_msg 原串(带中文尾巴)能命中 ③ friendly_any 走到 Express 库存兜底层。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import push_log_friendly as plf  # noqa: E402

LANGS = ("zh", "th", "en", "ja")

# 生产真实 error_msg 原串(docs/integrations/express-push/35-...:21-22 逐字)
REAL_MSGS = {
    "DBF_WRITE_FAILED": "DBF_WRITE_FAILED 账套无真库存品模板(STKTYP=0)",
    "STOCK_ITEM_NOT_FOUND": "STOCK_ITEM_NOT_FOUND 零/负库存",
}


class TestExpressStockFriendly(unittest.TestCase):
    def test_every_code_has_4_langs_nonempty(self):
        for code, d in plf._EXPRESS_STOCK_FRIENDLY.items():
            for lang in LANGS:
                self.assertIn(lang, d, f"{code} 缺 {lang}")
                self.assertTrue(str(d[lang]).strip(), f"{code}.{lang} 空")

    def test_hits_real_world_error_msgs(self):
        # 码作为子串出现在真实回执里(带中文尾巴)也要命中。
        for code, msg in REAL_MSGS.items():
            d = plf.express_stock_friendly(msg)
            self.assertIsNotNone(d, f"{code} 未命中真实串:{msg}")
            self.assertEqual(d, plf._EXPRESS_STOCK_FRIENDLY[code])

    def test_none_on_unknown_or_empty(self):
        self.assertIsNone(plf.express_stock_friendly(None))
        self.assertIsNone(plf.express_stock_friendly(""))
        self.assertIsNone(plf.express_stock_friendly("ERR_TOTALLY_UNRELATED"))

    def test_friendly_any_falls_back_to_express_stock(self):
        # 发票 catalog / 单据防呆 / DMS 三层都不覆盖这两码 → 退到 Express 库存层。
        for code, msg in REAL_MSGS.items():
            hit = plf.friendly_any(msg)
            self.assertIsNotNone(hit, f"friendly_any 未命中 {code}")
            self.assertEqual(hit, plf._EXPRESS_STOCK_FRIENDLY[code])
            # 命中即不再裸露原始码给用户看
            self.assertNotIn(code, hit["th"])


if __name__ == "__main__":
    unittest.main()
