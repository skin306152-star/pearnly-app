#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_business_friendly_catalog.py

守门测试 · 2026-08-10 文件大小闸拆分:
数据目录(_ERR_CATALOG / _THAI_REASON_CATALOG)从 mrerp_business_friendly
拆到 mrerp_business_friendly_catalog,主文件 re-export 保公共 API 不变。

本测锁三件事:
1. 新目录模块可导入,两份 catalog 非空
2. re-export 后 friendly_for_ui 对带后缀的 "ERR_AUTH: ..." 仍命中
   (生产 error_msg 常带后缀,整串精确匹配永远 miss,靠 _match_catalog 抠 token)
3. 两个文件都 <500 行(用 open 数行,防再越线触发 check_file_size)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import mrerp_business_friendly as mbf  # noqa: E402
from services.erp import mrerp_business_friendly_catalog as cat  # noqa: E402

_CEILING = 500
_FILES = (
    PROJECT_ROOT / "services/erp/mrerp_business_friendly.py",
    PROJECT_ROOT / "services/erp/mrerp_business_friendly_catalog.py",
)


class CatalogModuleTests(unittest.TestCase):
    def test_catalog_module_imports_with_nonempty_data(self):
        self.assertTrue(cat._ERR_CATALOG, "_ERR_CATALOG 不应为空")
        self.assertTrue(cat._THAI_REASON_CATALOG, "_THAI_REASON_CATALOG 不应为空")

    def test_main_module_reexports_same_objects(self):
        # 主文件 import 的是同一个对象,不是副本:匹配逻辑与数据不能分家。
        self.assertIs(mbf._ERR_CATALOG, cat._ERR_CATALOG)
        self.assertIs(mbf._THAI_REASON_CATALOG, cat._THAI_REASON_CATALOG)


class ReexportBehaviourTests(unittest.TestCase):
    def test_friendly_for_ui_hits_err_auth_with_suffix(self):
        # 生产 error_msg 带后缀:"ERR_AUTH: login failed" 整串精确匹配必 miss,
        # 靠 _match_catalog 正则抠 token → 必须仍命中并返回主 UI 4 语。
        r = mbf.friendly_for_ui("ERR_AUTH: login failed")
        self.assertIsNotNone(r, "ERR_AUTH 带后缀应命中 catalog")
        self.assertEqual(set(r.keys()), {"zh", "th", "en", "ja"})
        for lang, text in r.items():
            self.assertTrue(text, f"{lang} 友好文案不应为空")
        self.assertNotEqual(r["zh"], "ERR_AUTH: login failed")

    def test_get_friendly_still_resolves_catalog(self):
        out = mbf.get_friendly("ERR_INVOICE_NO_TOO_LONG")
        self.assertIn("18", out["en"])


class FileSizeCeilingTests(unittest.TestCase):
    def test_both_files_stay_under_500_lines(self):
        for path in _FILES:
            with path.open("r", encoding="utf-8") as f:
                n_lines = sum(1 for _ in f)
            self.assertLess(
                n_lines,
                _CEILING,
                f"{path.name} 超 {_CEILING} 行硬闸({n_lines})· 数据目录与主文件都要守线",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
