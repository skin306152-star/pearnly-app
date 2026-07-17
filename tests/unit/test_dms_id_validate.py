# -*- coding: utf-8 -*-
"""泰国身份证 mod-11 校验位纯函数 + 其接进 DMS 识别流的守门(A1)。

合法号的校验位在下方 test_valid_id_true 注释里逐步算出,避免"神秘常量"。
"""

import unittest
from unittest.mock import patch

from services.erp import dms_id_ocr
from services.erp.dms_id_validate import is_valid_thai_id

# 自造合法号:前 12 位 = 1 1 0 1 7 0 0 2 0 7 3 6,权重 13..2。
#   1*13+1*12+0*11+1*10+7*9+0*8+0*7+2*6+0*5+7*4+3*3+6*2
#   = 13+12+0+10+63+0+0+12+0+28+9+12 = 159
#   check = (11 - (159 % 11)) % 10 = (11 - 5) % 10 = 6  → 第 13 位 = 6
_VALID = "1101700207366"


class ThaiIdChecksumTests(unittest.TestCase):
    def test_valid_id_true(self):
        self.assertTrue(is_valid_thai_id(_VALID))

    def test_last_digit_plus_one_false(self):
        bad = _VALID[:12] + "7"  # 校验位 6→7,mod-11 对不上
        self.assertFalse(is_valid_thai_id(bad))

    def test_twelve_digits_false(self):
        self.assertFalse(is_valid_thai_id(_VALID[:12]))

    def test_valid_with_dashes_and_spaces_true(self):
        self.assertTrue(is_valid_thai_id("1-1017-00207-36-6"))
        self.assertTrue(is_valid_thai_id(" 1 1017 00207 36 6 "))

    def test_thai_digits_normalized_true(self):
        thai = _VALID.translate(str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙"))
        self.assertTrue(is_valid_thai_id(thai))

    def test_empty_and_nondigit_false(self):
        self.assertFalse(is_valid_thai_id(""))
        self.assertFalse(is_valid_thai_id(None))  # type: ignore[arg-type]
        self.assertFalse(is_valid_thai_id("11017002073ab"))


_USER = {"id": "u-1", "tenant_id": "t-1"}


def _run_recognize(id_card):
    ocr = {"id_card": id_card, "needs_review": False, "missing_fields": []}
    with (
        patch.object(dms_id_ocr, "resolve_dms_endpoint", return_value={"id": "e1"}),
        patch.object(
            dms_id_ocr.db,
            "get_billing_status_combined",
            return_value={"allowed": True, "is_exempt": True},
        ),
        patch("services.ocr.id_card_extract.extract_thai_id_card", return_value=ocr),
        patch("services.ocr.entrypoints.policy_context_from_billing", return_value={}),
        patch.object(dms_id_ocr.db, "charge_ocr_async"),
    ):
        _, out, _ = dms_id_ocr.recognize_id_card(_USER, b"img", "a.jpg")
    return out


class ChecksumWiringTests(unittest.TestCase):
    def test_bad_checksum_flags_needs_review(self):
        out = _run_recognize({"people_id": _VALID[:12] + "7", "address": {}})
        self.assertTrue(out["needs_review"])
        self.assertIn("people_id_checksum", out["missing_fields"])

    def test_valid_id_not_flagged(self):
        out = _run_recognize({"people_id": _VALID, "address": {}})
        self.assertNotIn("people_id_checksum", out["missing_fields"])

    def test_empty_id_not_flagged_by_checksum(self):
        # 空号已由上游列进 missing(people_id),校验位不再重复插旗。
        out = _run_recognize({"people_id": "", "address": {}})
        self.assertNotIn("people_id_checksum", out["missing_fields"])


if __name__ == "__main__":
    unittest.main()
