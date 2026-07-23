# -*- coding: utf-8 -*-
"""身份证 OCR 打回话术(ocr_review)· 键覆盖 + 校验位单独归因(P1-11)。

覆盖闸按源码对账:OCR 侧新增 missing_fields 键而没配标签,这里就红——旧实现拿 DMS
建档表单词表查 OCR 键,两套命名空间零交集,缺项从来没印出来过,机械闸缺位是根因。
"""

import inspect
import re
import unittest
from pathlib import Path

from services.erp import dms_id_ocr
from services.line_dms import cards, ocr_review
from services.ocr import id_card_extract

_APPEND_RE = re.compile(r"missing(?:_fields)?\.append\(\s*[\"'](\w+)[\"']\s*\)")


def _produced_keys(module) -> set:
    src = Path(inspect.getfile(module)).read_text(encoding="utf-8")
    return set(_APPEND_RE.findall(src))


class LabelCoverageTests(unittest.TestCase):
    def test_labels_cover_exactly_what_ocr_produces(self):
        produced = _produced_keys(id_card_extract) | _produced_keys(dms_id_ocr)
        self.assertIn(ocr_review.CHECKSUM_KEY, produced)  # 正则真扫到了,不是空集自证
        labelled = set(ocr_review.MISSING_LABELS_TH) | {ocr_review.CHECKSUM_KEY}
        self.assertEqual(produced, labelled)


class ReviewTextTests(unittest.TestCase):
    def test_checksum_says_number_failed_not_blurry(self):
        said = ocr_review.review_text([ocr_review.CHECKSUM_KEY])
        self.assertEqual(said, ocr_review.TXT_ID_CHECKSUM)
        self.assertNotIn(cards.TXT_BLURRY, said)

    def test_checksum_text_does_not_claim_missing_number(self):
        """校验位不过 = 13 位读到了但对不上,不能说成缺号。"""
        self.assertIn("13", ocr_review.TXT_ID_CHECKSUM)

    def test_missing_fields_are_listed(self):
        said = ocr_review.review_text(["first_name", "birthday"])
        self.assertTrue(said.startswith(cards.TXT_BLURRY))
        self.assertIn(ocr_review.MISSING_LABELS_TH["first_name"], said)
        self.assertIn(ocr_review.MISSING_LABELS_TH["birthday"], said)

    def test_unknown_or_empty_keys_fall_back_to_blurry(self):
        self.assertEqual(ocr_review.review_text([]), cards.TXT_BLURRY)
        self.assertEqual(ocr_review.review_text(["prefix_id"]), cards.TXT_BLURRY)

    def test_checksum_plus_missing_field_keeps_both(self):
        said = ocr_review.review_text([ocr_review.CHECKSUM_KEY, "last_name"])
        self.assertTrue(said.startswith(ocr_review.TXT_ID_CHECKSUM))
        self.assertIn(ocr_review.MISSING_LABELS_TH["last_name"], said)


if __name__ == "__main__":
    unittest.main()
