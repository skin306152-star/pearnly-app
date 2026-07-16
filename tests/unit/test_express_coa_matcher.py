# -*- coding: utf-8 -*-
"""Express 建桥器单测(services/accounting/express_coa_matcher.py · T4b)。

建桥金标:合成冰厂式 GLACC → 进项税 ภาษีซื้อ→coa 1140、销项税 ภาษีขาย→coa 2030 必中;
覆盖率报告 + 未映射清单;零臆造(名不中不硬塞);同名汇总头/明细取叶子;真同名多叶子进
conflicts 不乱挑。合成小样(冰厂式四段码),不碰桌面真料。
"""

import unittest

from services.accounting import express_coa_matcher as matcher

# 合成冰厂式 GLACC(四段码 + 泰文名 + 类型)· 含汇总头/未知科目测边界
_GLACC = [
    {"ACCNUM": "11-05-04-00", "ACCNAM": "ภาษีมูลค่าเพิ่ม", "ACCTYP": "A"},  # VAT 汇总头 · 名不中
    {"ACCNUM": "11-05-04-01", "ACCNAM": "ภาษีซื้อ", "ACCTYP": "A"},  # 进项税 → 1140
    {"ACCNUM": "21-05-04-02", "ACCNAM": "ภาษีขาย", "ACCTYP": "L"},  # 销项税 → 2030
    {"ACCNUM": "11-01-01-01", "ACCNAM": "เงินสด", "ACCTYP": "A"},  # 现金 → 1010
    {"ACCNUM": "11-01-02-01", "ACCNAM": "เงินฝากธนาคาร", "ACCTYP": "A"},  # 银行 → 1020
    {"ACCNUM": "11-02-01-01", "ACCNAM": "ลูกหนี้การค้า", "ACCTYP": "A"},  # 应收 → 1130
    {"ACCNUM": "41-01-01-01", "ACCNAM": "รายได้จากการขาย", "ACCTYP": "R"},  # 销售收入 → 4010
    {"ACCNUM": "51-01-01-01", "ACCNAM": "ต้นทุนขาย", "ACCTYP": "E"},  # 销售成本 → 5010
    {"ACCNUM": "99-99-99-99", "ACCNAM": "ค่าอะไรก็ไม่รู้", "ACCTYP": "E"},  # 未知 → 不臆造
]


def _by_coa(suggestions):
    return {s["coa_code"]: s["erp_code"] for s in suggestions}


class GoldenBridgeTests(unittest.TestCase):
    def test_vat_accounts_must_hit(self):
        res = matcher.suggest_bridge(_GLACC)
        m = _by_coa(res.suggestions)
        # 金标:进项税/销项税四段码必中对应 coa。
        self.assertEqual(m["1140"], "11-05-04-01")
        self.assertEqual(m["2030"], "21-05-04-02")

    def test_full_semantic_hits(self):
        m = _by_coa(matcher.suggest_bridge(_GLACC).suggestions)
        self.assertEqual(m["1010"], "11-01-01-01")
        self.assertEqual(m["1020"], "11-01-02-01")
        self.assertEqual(m["1130"], "11-02-01-01")
        self.assertEqual(m["4010"], "41-01-01-01")
        self.assertEqual(m["5010"], "51-01-01-01")

    def test_zero_fabrication_unmapped_listed(self):
        res = matcher.suggest_bridge(_GLACC)
        codes = _by_coa(res.suggestions)
        # 未知科目 + VAT 汇总头(名不中)都进未映射,绝不硬塞到某 coa。
        unmapped = {u["erp_code"] for u in res.unmapped}
        self.assertIn("99-99-99-99", unmapped)
        self.assertIn("11-05-04-00", unmapped)
        self.assertNotIn("99-99-99-99", codes.values())
        self.assertNotIn("11-05-04-00", codes.values())

    def test_coverage_report(self):
        res = matcher.suggest_bridge(_GLACC)
        cov = res.coverage()
        self.assertEqual(cov["total_accounts"], 9)
        self.assertEqual(cov["mapped"], 7)  # 7 命中
        self.assertEqual(cov["unmapped"], 2)  # 汇总头 + 未知
        self.assertEqual(cov["conflict_groups"], 0)

    def test_suggestions_are_upsert_shaped(self):
        s = matcher.suggest_bridge(_GLACC).suggestions[0]
        self.assertEqual(set(s) >= {"coa_code", "erp_code", "erp_name", "match_source"}, True)
        self.assertEqual(s["match_source"], "auto")


class LeafPreferenceTests(unittest.TestCase):
    def test_header_yields_to_leaf_on_same_name(self):
        # 同名「เงินสด」:汇总头 11-01-01-00 让位给明细叶子 11-01-01-01。
        rows = [
            {"ACCNUM": "11-01-01-00", "ACCNAM": "เงินสด", "ACCTYP": "A"},
            {"ACCNUM": "11-01-01-01", "ACCNAM": "เงินสด", "ACCTYP": "A"},
        ]
        res = matcher.suggest_bridge(rows)
        self.assertEqual(_by_coa(res.suggestions)["1010"], "11-01-01-01")
        self.assertEqual(res.conflicts, [])

    def test_two_leaves_same_name_is_conflict_not_guess(self):
        # 两个明细叶子同名 = 真歧义,进 conflicts 交人裁,不随便挑一个建桥。
        rows = [
            {"ACCNUM": "11-01-01-01", "ACCNAM": "เงินสด", "ACCTYP": "A"},
            {"ACCNUM": "11-01-02-05", "ACCNAM": "เงินสด", "ACCTYP": "A"},
        ]
        res = matcher.suggest_bridge(rows)
        self.assertEqual(res.suggestions, [])
        self.assertEqual(len(res.conflicts), 1)
        self.assertEqual(res.conflicts[0]["coa_code"], "1010")
        self.assertEqual(len(res.conflicts[0]["candidates"]), 2)


class NormalizationTests(unittest.TestCase):
    def test_whitespace_and_zero_width_tolerated(self):
        rows = [{"ACCNUM": "11-05-04-01", "ACCNAM": "  ภาษีซื้อ​ ", "ACCTYP": "A"}]
        self.assertEqual(_by_coa(matcher.suggest_bridge(rows).suggestions)["1140"], "11-05-04-01")


if __name__ == "__main__":
    unittest.main()
