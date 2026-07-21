# -*- coding: utf-8 -*-
"""posting_profile 画像推断守门。

阈值钉死在 6 家真账套(事务所真实客户 · DBF 取证扫 STMAS/STCRD 得)的实测形状,
既当 non-regression 闸,也当"判据来自真数据非拍脑袋"的证据。核心还守一条铁律:
永续客户在库存路未开时必须 escalate,绝不静默按周期制落账(会双重计成本)。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.erp.express_push.posting_profile import (  # noqa: E402
    classify_inventory_usage,
    infer_profile,
    profile_from_config,
)

# 6 家真账套实测指纹(stock_master_count=STKTYP=0 主档数 · stcrd_lines=明细行 ·
# stcrd_lines_moving_stock=动真实滚动库存余额的行)。括号=动库存行占比。
_REAL = {
    "AsiaSports": {
        "stock_master_count": 672,
        "stcrd_lines": 9300,
        "stcrd_lines_moving_stock": 8102,
    },  # .871
    "Moritomo": {
        "stock_master_count": 1770,
        "stcrd_lines": 47341,
        "stcrd_lines_moving_stock": 46987,
    },  # .993
    "SKChemical": {
        "stock_master_count": 1055,
        "stcrd_lines": 5631,
        "stcrd_lines_moving_stock": 4818,
    },  # .856
    "WorldNaturalFood": {
        "stock_master_count": 159,
        "stcrd_lines": 2250,
        "stcrd_lines_moving_stock": 853,
    },  # .379
    "IceFactory": {
        "stock_master_count": 4,
        "stcrd_lines": 1530,
        "stcrd_lines_moving_stock": 75,
    },  # .049
    "Saengjit": {"stock_master_count": 0, "stcrd_lines": 7560, "stcrd_lines_moving_stock": 0},  # 0
}


class TestInventoryClassify(unittest.TestCase):
    def test_perpetual_traders(self):
        for name in ("AsiaSports", "Moritomo", "SKChemical"):
            self.assertEqual(classify_inventory_usage(_REAL[name]), "perpetual", name)

    def test_none_service_and_cashsale(self):
        for name in ("Saengjit", "IceFactory"):
            self.assertEqual(classify_inventory_usage(_REAL[name]), "none", name)

    def test_mixed_middle(self):
        self.assertEqual(classify_inventory_usage(_REAL["WorldNaturalFood"]), "mixed")

    def test_zero_stock_masters_is_none(self):
        fp = {"stock_master_count": 0, "stcrd_lines": 100, "stcrd_lines_moving_stock": 50}
        self.assertEqual(classify_inventory_usage(fp), "none")

    def test_missing_or_bad_fingerprint_is_unknown(self):
        self.assertEqual(classify_inventory_usage(None), "unknown")
        self.assertEqual(classify_inventory_usage({}), "unknown")
        self.assertEqual(classify_inventory_usage({"stcrd_lines": "x"}), "unknown")


class TestInferProfile(unittest.TestCase):
    def test_perpetual_without_stock_lane_escalates(self):
        # ★永续客户 + 库存路未开 → manual_review(绝不静默按周期制错账)。
        p = infer_profile(_REAL["AsiaSports"], stock_enabled=False)
        self.assertEqual(p.posting_mode, "manual_review")
        self.assertTrue(p.needs_confirm)

    def test_perpetual_with_stock_lane(self):
        p = infer_profile(_REAL["Moritomo"], stock_enabled=True)
        self.assertEqual(p.posting_mode, "stock")

    def test_none_auto_non_stock(self):
        p = infer_profile(_REAL["IceFactory"], stock_enabled=False)
        self.assertEqual(p.posting_mode, "non_stock")
        self.assertFalse(p.needs_confirm)

    def test_mixed_escalates_for_human(self):
        p = infer_profile(_REAL["WorldNaturalFood"])
        self.assertEqual(p.posting_mode, "manual_review")
        self.assertTrue(p.needs_confirm)

    def test_unknown_conservative_non_stock(self):
        p = infer_profile(None)
        self.assertEqual(p.posting_mode, "non_stock")
        self.assertTrue(p.needs_confirm)
        self.assertEqual(p.source, "default")


class TestProfileFromConfig(unittest.TestCase):
    def test_confirmed_override_wins_over_inference(self):
        cfg = {
            "posting_profile": {"posting_mode": "stock", "inventory_usage": "perpetual"},
            "catalog_fingerprint": _REAL["IceFactory"],
        }
        p = profile_from_config(cfg)
        self.assertEqual(p.posting_mode, "stock")
        self.assertEqual(p.source, "confirmed")
        self.assertFalse(p.needs_confirm)

    def test_falls_back_to_inference(self):
        p = profile_from_config({"catalog_fingerprint": _REAL["Saengjit"]})
        self.assertEqual(p.inventory_usage, "none")
        self.assertEqual(p.posting_mode, "non_stock")

    def test_empty_config_is_unknown_default(self):
        p = profile_from_config(None)
        self.assertEqual(p.posting_mode, "non_stock")
        self.assertTrue(p.needs_confirm)


if __name__ == "__main__":
    unittest.main()
