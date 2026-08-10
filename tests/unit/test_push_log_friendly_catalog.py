#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_push_log_friendly_catalog.py

推送失败码 4 语目录扩编守门(2026-08-10 派单):mrerp _ERR_CATALOG 补 ERR_DB_IMPORT /
ERR_NO_SUPPLIER / ERR_UNKNOWN_UPLOAD_OUTCOME + _match_catalog 支持 "ERR_xxx: 后缀" 命中;
push_log_friendly 补 5 个 DMS 键 + Express 桥接层 _COMPANION_BRIDGE_FRIENDLY + 纯技术态
兜底 _tech_fallback_friendly。本测锁 friendly_any 六层链各层的命中与互不误伤:
① ERR_ 码带后缀(正则抠 token) ② 桥接层整串/小写码 ③ DMS 新键 ④ 技术态兜底
⑤ 未知串不误伤(返 None) ⑥ 长码 ERR_DMS_IMPORT_REPORT 不被 ERR_DMS_IMPORT 抢占。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import push_log_friendly as plf  # noqa: E402

LANGS = ("zh", "th", "en", "ja")


class MatchCatalogSuffixTests(unittest.TestCase):
    def test_err_code_with_suffix_hits_catalog(self):
        # 生产 error_msg 常带后缀:整串精确匹配永远 miss → 正则从开头抠 ERR_ token。
        hit = plf.friendly_any("ERR_AUTH: login failed")
        self.assertIsNotNone(hit, "ERR_AUTH: login failed 未命中")
        for lang in LANGS:
            self.assertTrue(str(hit[lang]).strip(), f"命中缺 {lang} 语文案")


class CompanionBridgeTests(unittest.TestCase):
    def test_readback_verify_failed_full_line(self):
        hit = plf.friendly_any("[READBACK_VERIFY_FAILED] STCRD line count 2 != 1")
        self.assertEqual(hit, plf._COMPANION_BRIDGE_FRIENDLY["READBACK_VERIFY_FAILED"])

    def test_bridge_failed_prefix(self):
        # bridge.failed 是小写码:原样子串匹配,不做大小写归一。
        hit = plf.friendly_any("bridge.failed: connection lost")
        self.assertIsNotNone(hit)
        self.assertEqual(hit, plf._COMPANION_BRIDGE_FRIENDLY["bridge.failed"])

    def test_agent_failed_still_hits(self):
        # agent_failed 也是小写码,别被 bridge.failed 等长码变化误伤。
        hit = plf.friendly_any("agent_failed: no detail returned")
        self.assertEqual(hit, plf._COMPANION_BRIDGE_FRIENDLY["agent_failed"])

    def test_every_bridge_key_has_4_langs_nonempty(self):
        for code, d in plf._COMPANION_BRIDGE_FRIENDLY.items():
            for lang in LANGS:
                self.assertIn(lang, d, f"{code} 缺 {lang}")
                self.assertTrue(str(d[lang]).strip(), f"{code}.{lang} 空")


class NewDmsCodeTests(unittest.TestCase):
    def test_err_dms_customer_save_hits(self):
        hit = plf.friendly_any("ERR_DMS_CUSTOMER_SAVE")
        self.assertEqual(hit, plf._DMS_PUSH_FRIENDLY["ERR_DMS_CUSTOMER_SAVE"])

    def test_new_dms_keys_all_hit_and_4_langs(self):
        for code in (
            "ERR_DMS_ADMIN_AUTH",
            "ERR_DMS_CUSTOMER_SAVE",
            "ERR_DMS_ORDER_FAILED",
            "ERR_PLAYWRIGHT_MISSING",
            "ERR_KMS_MISSING",
        ):
            d = plf.friendly_any(code)
            self.assertIsNotNone(d, f"{code} 未命中")
            self.assertEqual(d, plf._DMS_PUSH_FRIENDLY[code])
            for lang in LANGS:
                self.assertTrue(str(d[lang]).strip(), f"{code}.{lang} 空")


class TechFallbackTests(unittest.TestCase):
    def test_connection_error_prefix(self):
        hit = plf.friendly_any(
            "connection error: HTTPConnectionPool(host='erp.example', port=80): Max retries exceeded"
        )
        self.assertIsNotNone(hit, "connection error 未命中技术态兜底")
        self.assertIn("网络", hit["zh"])

    def test_doctype_html_page(self):
        hit = plf.friendly_any("<!doctype html>\n<html><body>502 Bad Gateway</body></html>")
        self.assertIsNotNone(hit, "<!doctype html 未命中技术态兜底")
        self.assertIn("异常页面", hit["zh"])

    def test_push_failed_exact(self):
        hit = plf.friendly_any("push failed")
        self.assertIsNotNone(hit)
        self.assertIn("请重试", hit["zh"])

    def test_tech_fallback_none_on_unknown(self):
        self.assertIsNone(plf._tech_fallback_friendly("totally unrelated text"))


class NoFalsePositiveTests(unittest.TestCase):
    def test_unknown_string_returns_none(self):
        self.assertIsNone(plf.friendly_any("ERR_TOTALLY_UNRELATED_XYZ"))
        self.assertIsNone(plf.friendly_any(None))
        self.assertIsNone(plf.friendly_any(""))

    def test_import_report_not_shadowed_by_import(self):
        # 长码先于前缀短码:ERR_DMS_IMPORT_REPORT 必须命中自己的条目(防前缀回归)。
        hit = plf.friendly_any("ERR_DMS_IMPORT_REPORT")
        self.assertEqual(hit, plf._DMS_PUSH_FRIENDLY["ERR_DMS_IMPORT_REPORT"])
        self.assertNotEqual(hit, plf._DMS_PUSH_FRIENDLY["ERR_DMS_IMPORT"])

    def test_readback_does_not_leak_into_friendly_for_ui(self):
        # 桥接层码不在发票 catalog 里,走了自己那层就不该再被 friendly_for_ui 消费到。
        self.assertIsNone(plf.friendly_for_ui("[READBACK_VERIFY_FAILED] STCRD line count 2 != 1"))


if __name__ == "__main__":
    unittest.main()
