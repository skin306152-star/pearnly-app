# -*- coding: utf-8 -*-
"""MR.ERP 建桥器单测(services/accounting/mrerp_coa_matcher.py · T4b-SM)。

建桥金标:合成 SM 式科目(扁平码 + 泰文名)→ 现金 เงินสด→1010、进项税 ภาษีซื้อ→1140、销项税
ภาษีขาย→2030 必中;覆盖率报告 + 未映射清单;零臆造(名不中不硬塞)。关键差异测试:MR.ERP 扁平码
末段 00(3200-00 กำไรสะสม)是过账叶子,必须命中 3020 而非被当汇总头丢弃(证明不套 Express 逻辑)。
同名多码进 conflicts 交人裁不乱挑。
"""

import unittest

from services.accounting import mrerp_coa_matcher as matcher

# 合成 SM 式科目(扁平码)· 含末段 00 叶子 / 名不中 / 未知,测边界
_ACCOUNTS = [
    {"code": "1111-01", "name_th": "เงินสด"},  # 现金 → 1010
    {"code": "1112-01", "name_th": "เงินฝากธนาคาร"},  # 银行 → 1020
    {"code": "1130-01", "name_th": "ลูกหนี้การค้า"},  # 应收 → 1130
    {"code": "1161-10", "name_th": "ภาษีซื้อ"},  # 进项税 → 1140
    {"code": "2160-11", "name_th": "ภาษีขาย"},  # 销项税 → 2030
    {"code": "4110-01", "name_th": "รายได้จากการขาย"},  # 销售收入 → 4010
    {"code": "5010-01", "name_th": "ต้นทุนขาย"},  # 销售成本 → 5010
    {"code": "3200-00", "name_th": "กำไรสะสม"},  # 末段 00 但 MR.ERP 是叶子 → 3020 必中
    {"code": "1161-11", "name_th": "ภาษีซื้อ-ยังไม่ถึงกำหนด"},  # 名不中 → unmapped
    {"code": "9999-99", "name_th": "อะไรก็ไม่รู้"},  # 未知 → 不臆造
]


def _by_coa(suggestions):
    return {s["coa_code"]: s["erp_code"] for s in suggestions}


class GoldenBridgeTests(unittest.TestCase):
    def test_required_accounts_must_hit(self):
        m = _by_coa(matcher.suggest_bridge(_ACCOUNTS).suggestions)
        self.assertEqual(m["1010"], "1111-01")  # 现金
        self.assertEqual(m["1140"], "1161-10")  # 进项税
        self.assertEqual(m["2030"], "2160-11")  # 销项税

    def test_full_semantic_hits(self):
        m = _by_coa(matcher.suggest_bridge(_ACCOUNTS).suggestions)
        self.assertEqual(m["1020"], "1112-01")
        self.assertEqual(m["1130"], "1130-01")
        self.assertEqual(m["4010"], "4110-01")
        self.assertEqual(m["5010"], "5010-01")

    def test_flat_code_trailing_00_is_leaf_not_header(self):
        # 关键差异:扁平码 3200-00 是过账叶子,必命中 3020,绝不当 Express 式汇总头丢弃。
        res = matcher.suggest_bridge(_ACCOUNTS)
        self.assertEqual(_by_coa(res.suggestions)["3020"], "3200-00")
        self.assertNotIn("3200-00", {u["erp_code"] for u in res.unmapped})

    def test_zero_fabrication_unmapped_listed(self):
        res = matcher.suggest_bridge(_ACCOUNTS)
        codes = _by_coa(res.suggestions)
        unmapped = {u["erp_code"] for u in res.unmapped}
        self.assertIn("1161-11", unmapped)  # 名不中
        self.assertIn("9999-99", unmapped)  # 未知
        self.assertNotIn("1161-11", codes.values())
        self.assertNotIn("9999-99", codes.values())

    def test_coverage_report(self):
        cov = matcher.suggest_bridge(_ACCOUNTS).coverage()
        self.assertEqual(cov["total_accounts"], 10)
        self.assertEqual(cov["mapped"], 8)
        self.assertEqual(cov["unmapped"], 2)
        self.assertEqual(cov["conflict_groups"], 0)

    def test_suggestions_are_upsert_shaped(self):
        s = matcher.suggest_bridge(_ACCOUNTS).suggestions[0]
        self.assertTrue(set(s) >= {"coa_code", "erp_code", "erp_name", "match_source"})
        self.assertEqual(s["match_source"], "auto")
        self.assertEqual(matcher.ERP_TYPE, "mrerp")


class ConflictTests(unittest.TestCase):
    def test_two_codes_same_name_is_conflict_not_guess(self):
        # 两个扁平码同名 เงินสด = 真歧义(无汇总头可让位)→ conflicts,不随便挑。
        rows = [
            {"code": "1111-01", "name_th": "เงินสด"},
            {"code": "1111-09", "name_th": "เงินสด"},
        ]
        res = matcher.suggest_bridge(rows)
        self.assertEqual(res.suggestions, [])
        self.assertEqual(len(res.conflicts), 1)
        self.assertEqual(res.conflicts[0]["coa_code"], "1010")
        self.assertEqual(len(res.conflicts[0]["candidates"]), 2)


class NormalizationTests(unittest.TestCase):
    def test_whitespace_and_zero_width_tolerated(self):
        rows = [{"code": "1161-10", "name_th": "  ภาษีซื้อ​ "}]
        self.assertEqual(_by_coa(matcher.suggest_bridge(rows).suggestions)["1140"], "1161-10")

    def test_from_uppercase_keys_tolerated(self):
        rows = [{"ACCNUM": "1111-01", "ACCNAM": "เงินสด"}]
        self.assertEqual(_by_coa(matcher.suggest_bridge(rows).suggestions)["1010"], "1111-01")


if __name__ == "__main__":
    unittest.main()
