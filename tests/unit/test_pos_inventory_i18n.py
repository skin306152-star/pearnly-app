#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_inventory_i18n.py

POS PO-A4 库存后台(屏7)+ POS 错误码字典(docs/pos/06)i18n 守门。

钉死(对齐 09 §A.3「失败只露人话」+ 06「每个 code 必在 4 语」):
  1. 屏7 库存导航/页面 i18n key 在 zh/en/th/ja 四语都在且非空。
  2. 06 全部 pos.* 错误码在四语都在且非空(缺翻译 → 前端裸露 code / 回退英文)。
  3. pos.* 的 ja 是真日文(≠ en),不是英文兜底(check_i18n 查不出"有键但抄英文")。
  4. inventory.ts / inventory-modals.ts 的失败分支统一走 invErrMsg/posErrMsg(不裸抛 code、
     不直接 showToast(err)、无 'HTTP '+status 拼接)。
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

APP_UI_LANGS = ("zh", "en", "th", "ja")

# docs/pos/06-error-codes.md 全集(信封 error.code)
POS_ERROR_CODES = (
    "pos.pin_invalid",
    "pos.cashier_inactive",
    "pos.product_not_found",
    "pos.out_of_stock",
    "pos.shift_already_open",
    "pos.shift_closed",
    "pos.line_invalid",
    "pos.void_not_allowed",
    "pos.tax_id_invalid",
    "pos.already_upgraded",
    "pos.over_refund",
    "pos.module_disabled",
    "pos.forbidden",
    "pos.offline_saved",
    "pos.sync_partial",
    "pos.server_busy",
    "pos.unexpected",
)

# 屏7 库存后台 i18n key(导航 + 页面 + 弹窗)
INVENTORY_KEYS = (
    "nav-group-pos",
    "nav-inventory",
    "nav-sales-report",
    "nav-pos-switch",
    "inv-title",
    "inv-act-count",
    "inv-act-transfer",
    "inv-act-export",
    "inv-act-in",
    "inv-stat-sku",
    "inv-stat-value",
    "inv-stat-low",
    "inv-stat-out",
    "inv-search-ph",
    "inv-chip-lowout",
    "inv-chip-all",
    "inv-col-product",
    "inv-col-barcode",
    "inv-col-unit",
    "inv-col-onhand",
    "inv-col-cost",
    "inv-col-status",
    "inv-st-ok",
    "inv-st-low",
    "inv-st-out",
    "inv-near-expiry",
    "inv-empty",
    "inv-empty-filtered",
    "inv-error",
    "inv-retry",
    "inv-export-ok",
    "inv-transfer-soon",
    "inv-in-title",
    "inv-in-submit",
    "inv-count-title",
    "inv-count-submit",
    "inv-cancel",
    "inv-add-row",
    "inv-row-remove",
    "inv-f-qty",
    "inv-f-cost",
    "inv-f-batch",
    "inv-f-batch-exp",
    "inv-f-counted",
    "inv-err-no-lines",
    "inv-in-ok",
    "inv-count-ok",
    "inv-submit-fail",
)

I18N_PATH = PROJECT_ROOT / "static" / "i18n-data.js"
SRC_HOME = PROJECT_ROOT / "src" / "home"


def _lang_slices() -> dict[str, str]:
    """把 window.I18N 文本按语言块切片(zh/en/th/ja),用块边界界定 key 归属。"""
    text = I18N_PATH.read_text(encoding="utf-8")
    starts = {}
    for lang in APP_UI_LANGS:
        m = re.search(r"\n    " + lang + r": \{", text)
        assert m, f"language block {lang} not found in i18n-data.js"
        starts[lang] = m.start()
    order = sorted(starts, key=lambda k: starts[k])
    slices = {}
    for i, lang in enumerate(order):
        begin = starts[lang]
        end = starts[order[i + 1]] if i + 1 < len(order) else len(text)
        slices[lang] = text[begin:end]
    return slices


def _value(slice_text: str, key: str) -> str | None:
    """取某语言块内某 key 的字符串值(兼容单/双引号包裹)。"""
    m = re.search(r"'" + re.escape(key) + r"':\s*(['\"])(.*?)\1\s*,", slice_text)
    return m.group(2) if m else None


class TestPosInventoryI18n(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.slices = _lang_slices()

    def test_inventory_keys_cover_four_langs(self):
        for key in INVENTORY_KEYS:
            for lang in APP_UI_LANGS:
                val = _value(self.slices[lang], key)
                self.assertIsNotNone(val, f"{key} missing in lang {lang}")
                self.assertTrue(str(val).strip(), f"{key}.{lang} empty")

    def test_pos_error_codes_cover_four_langs(self):
        for code in POS_ERROR_CODES:
            for lang in APP_UI_LANGS:
                val = _value(self.slices[lang], code)
                self.assertIsNotNone(val, f"{code} missing in lang {lang}")
                self.assertTrue(str(val).strip(), f"{code}.{lang} empty")

    def test_pos_error_codes_ja_is_real_japanese(self):
        for code in POS_ERROR_CODES:
            ja = _value(self.slices["ja"], code)
            en = _value(self.slices["en"], code)
            self.assertNotEqual(ja, en, f"{code} ja equals en (English fallback, not real 日文)")

    def test_failure_paths_use_localized_helper(self):
        # 09 §A.3:失败只露人话。库存前端不得 showToast(err) / 'HTTP '+status / 裸抛 code。
        for name in ("inventory.ts", "inventory-modals.ts"):
            src = (SRC_HOME / name).read_text(encoding="utf-8")
            self.assertNotIn("'HTTP '", src, f"{name} 拼了 HTTP 状态码给用户看")
            self.assertNotIn("showToast(err", src, f"{name} 直接把异常对象弹给用户")
            self.assertIn("invErrMsg", src, f"{name} 未走统一本地化失败文案 invErrMsg")


if __name__ == "__main__":
    unittest.main()
