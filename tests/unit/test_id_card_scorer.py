# -*- coding: utf-8 -*-
"""id_card_scorer 确定性打分器单测(不连模型 · 进 CI)。

锁住:公民号只比数字、泰国身份证校验位算法(≠税号 mod-11)、生日跨格式归一
(真值 YYYY-MM-DD ↔ prod dd/mm/yyyy)、嵌套 address 取值、关键漏判判定、
完全命中=1.0、最小真值只比给出的字段、称谓/名字空白等价。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "eval")))

import id_card_scorer as sc  # noqa: E402

# 合法号(前12位加权 mod-11 → 校验位 6)。
_VALID_ID = "1101700123456"


class NormalizeTests(unittest.TestCase):
    def test_be_date_cross_format_equal(self):
        # 真值年-月-日 与 prod 日/月/年 归一到同一 BE canonical。
        self.assertEqual(sc.normalize_be_date("2530-05-12"), "2530-05-12")
        self.assertEqual(sc.normalize_be_date("12/05/2530"), "2530-05-12")

    def test_be_date_gregorian_promoted(self):
        # 公元年 +543 转 BE(读出 ค.ศ. 时兜底)。
        self.assertEqual(sc.normalize_be_date("12/05/1987"), "2530-05-12")

    def test_be_date_unparsable_blank(self):
        for v in (None, "", "  ", "not a date", "13-2000"):
            self.assertEqual(sc.normalize_be_date(v), "", v)

    def test_zip_digits_only(self):
        self.assertEqual(sc.normalize_zip("10500 "), "10500")
        self.assertEqual(sc.normalize_zip("10-500"), "10500")


class ChecksumTests(unittest.TestCase):
    def test_valid_id_passes(self):
        self.assertTrue(sc.thai_citizen_id_checkdigit_ok(_VALID_ID))
        # 带空格/破折号照样过(先去噪)。
        self.assertTrue(sc.thai_citizen_id_checkdigit_ok("1-1017-00123-45-6"))

    def test_wrong_checkdigit_fails(self):
        self.assertFalse(sc.thai_citizen_id_checkdigit_ok("1101700123457"))

    def test_wrong_length_fails(self):
        for v in ("", "123", "11017001234567", None):
            self.assertFalse(sc.thai_citizen_id_checkdigit_ok(v))


class ScoreTests(unittest.TestCase):
    def _gt(self, **over):
        gt = {
            "people_id": _VALID_ID,
            "prefix_name": "นาย",
            "first_name": "สมชาย",
            "last_name": "ใจดี",
            "birthday_be": "2530-05-12",
            "issue_date_be": "2563-01-15",
            "expiry_date_be": "2573-05-11",
            "address": {"subdistrict": "บางรัก", "district": "บางรัก", "zipcode": "10500"},
        }
        gt.update(over)
        return gt

    def _actual(self, **over):
        # prod editable_id_card 形状:生日是 dd/mm/yyyy。
        a = {
            "people_id": _VALID_ID,
            "prefix_name": "นาย",
            "first_name": "สมชาย",
            "last_name": "ใจดี",
            "birthday_be": "12/05/2530",
            "issue_date_be": "15/01/2563",
            "expiry_date_be": "11/05/2573",
            "address": {"subdistrict": "บางรัก", "district": "บางรัก", "zipcode": "10500"},
        }
        a.update(over)
        return a

    def test_perfect_match_is_one(self):
        r = sc.score_id_card(self._gt(), self._actual())
        self.assertEqual(r["weighted_score"], 1.0)
        self.assertEqual(r["critical_misses"], [])
        self.assertTrue(r["id_valid"])

    def test_wrong_people_id_is_critical(self):
        r = sc.score_id_card(self._gt(), self._actual(people_id="1101700123457"))
        self.assertIn("people_id", r["critical_misses"])
        self.assertLess(r["weighted_score"], 1.0)

    def test_expiry_cross_format_matches(self):
        # #14:GT YYYY-MM-DD 到期日 与 prod dd/mm/yyyy 归一后相等。
        r = sc.score_id_card(self._gt(), self._actual())
        self.assertTrue(r["fields"]["expiry_date_be"]["match"])
        self.assertTrue(r["fields"]["issue_date_be"]["match"])

    def test_wrong_expiry_is_scored_miss(self):
        r = sc.score_id_card(self._gt(), self._actual(expiry_date_be="11/05/2571"))
        self.assertFalse(r["fields"]["expiry_date_be"]["match"])
        self.assertLess(r["weighted_score"], 1.0)

    def test_nested_address_scored(self):
        r = sc.score_id_card(self._gt(), self._actual(address={"zipcode": "99999"}))
        self.assertFalse(r["fields"]["address.zipcode"]["match"])
        # 邮编只 1 分,不算 critical。
        self.assertNotIn("address.zipcode", r["critical_misses"])

    def test_minimal_gt_scores_only_given_fields(self):
        r = sc.score_id_card({"people_id": _VALID_ID}, self._actual())
        self.assertEqual(r["scored_fields"], 1)
        self.assertEqual(r["weighted_score"], 1.0)

    def test_invalid_gt_id_flagged_in_aggregate(self):
        r = sc.score_id_card(
            {"people_id": "1101700123457", "first_name": "x"},
            {"people_id": "1101700123457", "first_name": "x"},
        )
        self.assertFalse(r["id_valid"])
        agg = sc.aggregate([r])
        self.assertEqual(agg["invalid_id_gt"], 1)


if __name__ == "__main__":
    unittest.main()
