# -*- coding: utf-8 -*-
"""发票方向自动判定单测(纯函数 · 无库无网络)。

钉死确定性口径:自家=卖方→sales / 自家=买方→purchase / 都不匹配或没读到→ambiguous(None)/
显式标签优先 / 银行 deposit-withdrawal 等非进销标签不当方向。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.direction import (  # noqa: E402
    detect_by_tax,
    explicit_direction,
    resolve_direction,
)

OWN = "0994000333444"  # 自家公司税号
VENDOR = "0107561000013"
CUSTOMER = "0105551234567"


def _flat(seller=None, buyer=None, direction=None):
    flat = {"fields": {}}
    if seller is not None:
        flat["fields"]["seller_tax"] = seller
    if buyer is not None:
        flat["fields"]["buyer_tax"] = buyer
    if direction is not None:
        flat["direction"] = direction
    return flat


class DetectByTaxTests(unittest.TestCase):
    def test_own_is_seller_to_sales(self):
        self.assertEqual(detect_by_tax(_flat(seller=OWN, buyer=CUSTOMER), OWN), "sales")

    def test_own_is_buyer_to_purchase(self):
        self.assertEqual(detect_by_tax(_flat(seller=VENDOR, buyer=OWN), OWN), "purchase")

    def test_neither_matches_ambiguous(self):
        self.assertIsNone(detect_by_tax(_flat(seller=VENDOR, buyer=CUSTOMER), OWN))

    def test_own_tax_missing_ambiguous(self):
        self.assertIsNone(detect_by_tax(_flat(seller=OWN, buyer=CUSTOMER), ""))

    def test_invoice_tax_unread_ambiguous(self):
        self.assertIsNone(detect_by_tax(_flat(seller=None, buyer=None), OWN))

    def test_both_match_ambiguous(self):
        # 自家同时是买卖双方(自开票异常)→ 判不出,留人工。
        self.assertIsNone(detect_by_tax(_flat(seller=OWN, buyer=OWN), OWN))

    def test_only_seller_read_and_matches_sales(self):
        self.assertEqual(detect_by_tax(_flat(seller=OWN), OWN), "sales")

    def test_only_buyer_read_and_matches_purchase(self):
        self.assertEqual(detect_by_tax(_flat(buyer=OWN), OWN), "purchase")

    def test_tax_normalized_ignores_formatting(self):
        # 票面带空格/连字符 → 归一后仍匹配。
        self.assertEqual(
            detect_by_tax(_flat(seller="0-99 4000 333 444", buyer=CUSTOMER), OWN), "sales"
        )


class ExplicitDirectionTests(unittest.TestCase):
    def test_explicit_sales(self):
        self.assertEqual(explicit_direction(_flat(direction="sales"), {}), "sales")
        self.assertEqual(explicit_direction(_flat(direction="income"), {}), "sales")

    def test_explicit_purchase(self):
        self.assertEqual(explicit_direction(_flat(direction="purchase"), {}), "purchase")
        self.assertEqual(explicit_direction(_flat(direction="expense"), {}), "purchase")

    def test_bank_tokens_not_direction(self):
        # 银行流水 deposit/withdrawal 不是进销方向 → None,交税号判定。
        self.assertIsNone(explicit_direction(_flat(direction="deposit"), {}))
        self.assertIsNone(explicit_direction(_flat(direction="withdrawal"), {}))

    def test_history_level_direction(self):
        self.assertEqual(explicit_direction({}, {"direction": "sales"}), "sales")


class ResolveDirectionTests(unittest.TestCase):
    def test_explicit_wins_over_tax(self):
        # 显式 sales 即便税号像进项也按 sales。
        flat = _flat(seller=VENDOR, buyer=OWN, direction="sales")
        self.assertEqual(resolve_direction(flat, {}, own_tax_id=OWN), "sales")

    def test_falls_back_to_tax_when_no_label(self):
        self.assertEqual(
            resolve_direction(_flat(seller=OWN, buyer=CUSTOMER), {}, own_tax_id=OWN), "sales"
        )
        self.assertEqual(
            resolve_direction(_flat(seller=VENDOR, buyer=OWN), {}, own_tax_id=OWN), "purchase"
        )

    def test_ambiguous_returns_none(self):
        self.assertIsNone(
            resolve_direction(_flat(seller=VENDOR, buyer=CUSTOMER), {}, own_tax_id=OWN)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
