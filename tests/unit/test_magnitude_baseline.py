# -*- coding: utf-8 -*-
"""供应商历史量级基线闸 · 抓 pur05-44.67 那类"语义选错列/读错位"。

[[ocr-determinism-layer-root-cause]] 头号缺口:pur05 加油票真值 ~1780,却被读成总额
44.67(选了"单价/小计"列当总额),内部自洽、sanity 抓不住(无明细佐证时)。唯一能抓它的
确定性信号 = 这家供应商历史上从来都是几千铢,这张 44.67 低了 ~40 倍。

本测钉住纯决策:给定供应商历史总额 + 这张总额 → 偏离量级则揪出;历史不足/缺额则不判
(宁可漏,不误杀)。
"""

import unittest

from services.ocr.magnitude_baseline import magnitude_anomaly_reason


class MagnitudeBaselineTests(unittest.TestCase):
    HIST = [1780.0, 1819.85, 1750.0, 1800.0, 1900.0, 1680.0]

    def test_pur05_low_outlier_flagged(self):
        r = magnitude_anomaly_reason(44.67, self.HIST)
        self.assertIsNotNone(r)
        self.assertIn("低", r)

    def test_normal_total_not_flagged(self):
        self.assertIsNone(magnitude_anomaly_reason(1850.0, self.HIST))

    def test_high_outlier_flagged(self):
        # 把 1780 多读一位成 17800+ → 高出量级
        self.assertIsNotNone(magnitude_anomaly_reason(53400.0, self.HIST))

    def test_insufficient_history_no_baseline(self):
        # 历史不足 → 没基线,不判(新供应商免误杀)
        self.assertIsNone(magnitude_anomaly_reason(44.67, [1780.0, 1800.0]))

    def test_missing_or_zero_total_skipped(self):
        self.assertIsNone(magnitude_anomaly_reason(None, self.HIST))
        self.assertIsNone(magnitude_anomaly_reason(0.0, self.HIST))

    def test_median_robust_to_single_outlier(self):
        # 历史里混进一个脏值,中位数仍稳,正常票不被误杀
        hist = self.HIST + [0.01]
        self.assertIsNone(magnitude_anomaly_reason(1820.0, hist))

    def test_zero_totals_in_history_ignored(self):
        # 历史里的 0/None 不计入有效基线
        self.assertIsNone(magnitude_anomaly_reason(44.67, [0, 0, None, 1780.0]))


if __name__ == "__main__":
    unittest.main()
