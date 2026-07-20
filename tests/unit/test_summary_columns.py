# -*- coding: utf-8 -*-
"""汇总表列角色识别守门测试(services/summary_import/columns.py)。

真实客户版式钉死。此前工单 R2 用「先从左找第一个命中关键词的列」认列,在冰厂 7-11
月度汇总表上把数量列当销售额、税前列当销项税,还 used=True 不报错,错数一路进 ภ.พ.30。
本文件用那张表的真表头当第一条用例——它塌了,那条静默错数就回来了。
"""

import unittest

from services.summary_import import columns

# 冰厂 7-11 月度销售汇总(tests/e2e/_fixtures/summary-7-11-ice.xlsx)真表头。
ICE_711_HEADERS = ["วันที่", "ยอด", "ราคา", "ยอดเงินก่อน vat", "ยอดเงิน vat", "ยอดเงินรวม"]


class DetectColumnsTests(unittest.TestCase):
    def test_ice_711_real_headers(self):
        """六列真表头逐角色钉死:数量/单价不得抢销售额位,税前列不得被认成 VAT 列。"""
        cols = columns.detect_columns(ICE_711_HEADERS)
        self.assertEqual(cols[columns.DATE], 0)
        self.assertEqual(cols[columns.QUANTITY], 1)
        self.assertEqual(cols[columns.UNIT_PRICE], 2)
        self.assertEqual(cols[columns.SUBTOTAL], 3)
        self.assertEqual(cols[columns.VAT], 4)
        self.assertEqual(cols[columns.TOTAL], 5)

    def test_before_vat_column_never_taken_as_vat(self):
        """「ยอดเงินก่อน vat」含裸 vat 子串,最长命中必须让它归税前而非税额。"""
        cols = columns.detect_columns(["ยอดเงินก่อน vat", "ยอดเงิน vat"])
        self.assertEqual(cols[columns.SUBTOTAL], 0)
        self.assertEqual(cols[columns.VAT], 1)

    def test_clean_thai_headers(self):
        """存量干净表头(现有 R2 用例形状)行为不变。"""
        cols = columns.detect_columns(["วันที่", "ยอดขาย", "ภาษีขาย"])
        self.assertEqual(cols[columns.DATE], 0)
        self.assertEqual(cols[columns.SUBTOTAL], 1)
        self.assertEqual(cols[columns.VAT], 2)
        self.assertIsNone(cols[columns.TOTAL])

    def test_manual_entry_two_column_shape(self):
        """人工填销项落的两列合成表(api.record_sales_summary 契约)必须继续认得出。"""
        cols = columns.detect_columns(["ยอดขาย", "ภาษีขาย"])
        self.assertEqual(cols[columns.SUBTOTAL], 0)
        self.assertEqual(cols[columns.VAT], 1)

    def test_english_headers(self):
        cols = columns.detect_columns(["Date", "Qty", "Unit Price", "Subtotal", "VAT", "Total"])
        self.assertEqual(
            [cols[r] for r in columns.ROLES],
            [0, 1, 2, 3, 4, 5],
        )

    def test_english_amount_headers_do_not_collide(self):
        """「VAT Amount」不得被 sales amount 的 amount 抢走。"""
        cols = columns.detect_columns(["Date", "Sales Amount", "VAT Amount", "Total Amount"])
        self.assertEqual(cols[columns.SUBTOTAL], 1)
        self.assertEqual(cols[columns.VAT], 2)
        self.assertEqual(cols[columns.TOTAL], 3)

    def test_thai_amount_word_is_not_quantity(self):
        """จำนวนเงิน(金额)含 จำนวน(数量)前缀,长词必须压过短词。"""
        cols = columns.detect_columns(["วันที่", "จำนวน", "ราคา", "จำนวนเงิน", "ภาษี", "รวม"])
        self.assertEqual(cols[columns.QUANTITY], 1)
        self.assertEqual(cols[columns.SUBTOTAL], 3)
        self.assertEqual(cols[columns.VAT], 4)
        self.assertEqual(cols[columns.TOTAL], 5)

    def test_chinese_headers(self):
        cols = columns.detect_columns(["日期", "数量", "单价", "税前", "税额", "合计"])
        self.assertEqual([cols[r] for r in columns.ROLES], [0, 1, 2, 3, 4, 5])

    def test_each_column_serves_one_role(self):
        """角色独占:同一列不会被两个角色同时占用。"""
        taken = [i for i in columns.detect_columns(ICE_711_HEADERS).values() if i is not None]
        self.assertEqual(len(taken), len(set(taken)))

    def test_unknown_headers_all_none(self):
        cols = columns.detect_columns(["aaa", "bbb"])
        self.assertEqual(set(cols), set(columns.ROLES))
        self.assertTrue(all(v is None for v in cols.values()))

    def test_empty_and_none_headers_survive(self):
        cols = columns.detect_columns([None, "", "ยอดขาย"])
        self.assertEqual(cols[columns.SUBTOTAL], 2)


# 真件冰厂 7-11 PDF 文字层抽出的表头(声调符号被 pdfplumber 按 x 排序挪到基字符之后)。
# 这一串是从真 PDF 实抽的原样字节,不是手打的——手打不出这种错位,而它正是漏检的载体。
ICE_711_PDF_HEADERS = [
    "วนั ที่",
    "ยอด",
    "ราคา",
    "ยอดเงนิ กอ่ น vat",
    "ยอดเงนิ vat",
    "ยอดเงนิ รวม",
]


class ThaiMarkMisplacementTests(unittest.TestCase):
    """PDF 文字层的泰文声调错位不得动摇认列(真件语料·2026-07-20 端到端实锤)。

    错位表头在子串匹配下 subtotal 落空、税前列被当成 VAT 列,销项税与销售额整体对调,
    且合计行交叉校验因两边取同一错列而自洽通过——两道闸同时失效,故必须在认列这层挡住。
    """

    def test_misaligned_pdf_headers_detect_same_as_clean(self):
        self.assertEqual(
            columns.detect_columns(ICE_711_PDF_HEADERS),
            columns.detect_columns(ICE_711_HEADERS),
        )

    def test_misaligned_pdf_headers_roles_exact(self):
        cols = columns.detect_columns(ICE_711_PDF_HEADERS)
        self.assertEqual([cols[r] for r in columns.ROLES], [0, 1, 2, 3, 4, 5])

    def test_skeleton_strips_marks_not_consonants(self):
        self.assertEqual(columns.skeleton("ยอดเงนิ กอ่ น vat"), columns.skeleton("ยอดเงินก่อน vat"))
        self.assertNotEqual(columns.skeleton("ยอดเงินก่อน"), columns.skeleton("ยอดเงินรวม"))


if __name__ == "__main__":
    unittest.main()
