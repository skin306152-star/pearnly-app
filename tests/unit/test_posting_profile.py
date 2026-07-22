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

    def test_zero_masters_no_movement_is_none(self):
        # Saengjit 形:0 库存主档 + 0 动库存行 → none。
        fp = {"stock_master_count": 0, "stcrd_lines": 100, "stcrd_lines_moving_stock": 0}
        self.assertEqual(classify_inventory_usage(fp), "none")

    def test_zero_masters_but_moving_not_silently_none(self):
        # ★指纹自相矛盾(masters=0 却有动库存行)→ 绝不静默判 none(会让真永续客户按周期制落)。
        # 高比例落 perpetual → 上层 escalate 交人,不当 none 自动 non_stock。
        fp = {"stock_master_count": 0, "stcrd_lines": 100, "stcrd_lines_moving_stock": 80}
        self.assertEqual(classify_inventory_usage(fp), "perpetual")

    def test_threshold_boundaries(self):
        # 阈值边界钉死:恰 0.60→perpetual、恰 0.15→none(防随手挪阈值不被测试抓到)。
        self.assertEqual(
            classify_inventory_usage(
                {"stock_master_count": 5, "stcrd_lines": 100, "stcrd_lines_moving_stock": 60}
            ),
            "perpetual",
        )
        self.assertEqual(
            classify_inventory_usage(
                {"stock_master_count": 5, "stcrd_lines": 100, "stcrd_lines_moving_stock": 15}
            ),
            "none",
        )

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
        p = profile_from_config(cfg, stock_enabled=True)
        self.assertEqual(p.posting_mode, "stock")
        self.assertEqual(p.source, "confirmed")
        self.assertFalse(p.needs_confirm)

    def test_confirmed_stock_gated_when_lane_off(self):
        # 会计确认了库存,但库存路(V2-b)没开 → 降 manual_review,绝不硬发 stock_item。
        cfg = {"posting_profile": {"posting_mode": "stock", "inventory_usage": "perpetual"}}
        p = profile_from_config(cfg, stock_enabled=False)
        self.assertEqual(p.posting_mode, "manual_review")

    def test_falls_back_to_inference(self):
        p = profile_from_config({"catalog_fingerprint": _REAL["Saengjit"]})
        self.assertEqual(p.inventory_usage, "none")
        self.assertEqual(p.posting_mode, "non_stock")

    def test_empty_config_is_unknown_default(self):
        p = profile_from_config(None)
        self.assertEqual(p.posting_mode, "non_stock")
        self.assertTrue(p.needs_confirm)

    def test_bad_override_mode_falls_back_to_inference(self):
        # override 里非法 posting_mode 视为脏值 → 回落指纹推断,不当 confirmed(防 'banana' 直落)。
        cfg = {
            "posting_profile": {"posting_mode": "banana"},
            "catalog_fingerprint": _REAL["IceFactory"],
        }
        p = profile_from_config(cfg)
        self.assertEqual(p.source, "inferred")
        self.assertEqual(p.posting_mode, "non_stock")


if __name__ == "__main__":
    unittest.main()
