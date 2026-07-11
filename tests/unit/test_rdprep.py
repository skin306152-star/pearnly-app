# -*- coding: utf-8 -*-
"""RD Prep 中央格式装配守门(方案 §8 D1-1):字段数/头尾无 pipe/N(15,2) 补零/佛历/
禁用字符/字段 4 PIN-NID 分流/文件名规约——逐条对齐官方 PDF FormatPND3·53 V2.0。"""

import unittest
from datetime import date
from decimal import Decimal

from services.tax import rdprep


def _header_values():
    return {
        "SENDER_ID": "0000",
        "SENDER_NID": "0105551234567",
        "SENDER_BRANCH": "000000",
        "SENDER_ROLE": "1",
        "NID": "0105551234567",
        "BRANCH_NO": "000000",
        "DEPT_NAME": "สำนักงานใหญ่",
        "SECTION3": "1",
        "SECTION_B": "0",
        "SECTION_C": "0",
        "LTO": "0",
        "TAX_MONTH": "07",
        "TAX_YEAR": "2569",
        "BRANCH_TYPE": "V",
        "FORM_TYPE": "00",
        "TOT_NUM": 1,
        "TOT_AMT": Decimal("140.00"),
        "TOT_TAX": Decimal("4.20"),
        "SUR_AMT": Decimal("0"),
        "GTOT_TAX": Decimal("4.20"),
        "TRANS_AMT": Decimal("0"),
        "USER_ID": "PLACEHOLDER",
        "FORM_FLAG": "1",
    }


class FieldCountTest(unittest.TestCase):
    def test_field_count_pnd3_header(self):
        rec = rdprep.build_header(rdprep.PND3, _header_values())
        self.assertEqual(len(rec.split("|")), 25)
        self.assertEqual(rdprep.HEADER_FIELD_COUNT, 25)

    def test_field_count_pnd3_detail(self):
        rec = rdprep.build_detail(rdprep.PND3, {"PIN": "1101700200111"})
        self.assertEqual(len(rec.split("|")), 38)
        self.assertEqual(rdprep.DETAIL_FIELD_COUNT, 38)


class DelimiterTest(unittest.TestCase):
    def test_pipe_no_leading_trailing(self):
        # 末字段有值方能验"无多余尾分隔符"(末字段留空是合法的空字段,与多余尾 pipe 不同)
        header = rdprep.build_header(rdprep.PND53, _header_values())
        detail = rdprep.build_detail(rdprep.PND53, {"NID": "0105551234567", "POSTAL_CODE": "10110"})
        for rec, count in ((header, 25), (detail, 38)):
            self.assertFalse(rec.startswith("|"))
            self.assertFalse(rec.endswith("|"))
            self.assertEqual(len(rec.split("|")), count)


class NumericTest(unittest.TestCase):
    def test_numeric_15_2_zero_fill(self):
        # 空数值 → "0.00";฿140 → "140.00"(官方 §8/§13)
        detail = rdprep.build_detail(
            rdprep.PND53, {"NID": "0105551234567", "PAID_AMT1": Decimal("140")}
        )
        cells = detail.split("|")
        self.assertEqual(cells[10], "140.00")  # 字段 11 PAID_AMT1
        self.assertEqual(cells[16], "0.00")  # 字段 17 PAID_AMT2 空 → 0.00
        self.assertEqual(cells[9], "0.00")  # 字段 10 TAX_RATE1 空 → 0.00


class BuddhistYearTest(unittest.TestCase):
    def test_buddhist_year(self):
        self.assertEqual(rdprep.to_buddhist_paid_date(date(2026, 7, 1)), "01072569")
        self.assertEqual(rdprep.to_buddhist_year(2026), "2569")


class ForbiddenCharTest(unittest.TestCase):
    def test_forbidden_chars_rejected(self):
        for bad in ("A,B", 'X"Y', "foo@bar", "a|b"):
            with self.assertRaises(rdprep.RdPrepFormatError):
                rdprep.build_detail(rdprep.PND53, {"NID": "0105551234567", "FNAME": bad})


class PayeeIdTest(unittest.TestCase):
    def test_pnd53_field4_is_nid_pnd3_is_pin(self):
        nid = "0105551234567"  # 法人税号
        pin = "1101700200111"  # 个人身份证
        d53 = rdprep.build_detail(rdprep.PND53, {"NID": nid, "PIN": "ignored"})
        d3 = rdprep.build_detail(rdprep.PND3, {"PIN": pin, "NID": "ignored"})
        self.assertEqual(d53.split("|")[3], nid)  # 字段 4 取 NID
        self.assertEqual(d3.split("|")[3], pin)  # 字段 4 取 PIN
        self.assertEqual(len(d53.split("|")[3]), 13)
        self.assertEqual(len(d3.split("|")[3]), 13)


class FilenameTest(unittest.TestCase):
    def test_filename_convention(self):
        name = rdprep.build_filename(
            form=rdprep.PND53,
            nid="0105551234567",
            branch_no="000000",
            tax_year_be="2569",
            tax_month="07",
            form_type="00",
            submission_seq="00",
        )
        self.assertEqual(name, "PND53_0105551234567_000000_2569_07_00_00.txt")


class AssembleTest(unittest.TestCase):
    """加测(不减 §8 七断言):CR/LF 分隔、record 类型常量、未知 form 拦截。"""

    def test_assemble_crlf_and_record_types(self):
        header = rdprep.build_header(rdprep.PND53, _header_values())
        detail = rdprep.build_detail(rdprep.PND53, {"NID": "0105551234567"})
        text = rdprep.assemble(header, [detail])
        self.assertEqual(text, header + "\r\n" + detail)
        self.assertTrue(text.startswith("H|"))
        self.assertIn("\r\nD|", text)

    def test_unknown_form_rejected(self):
        with self.assertRaises(rdprep.RdPrepFormatError):
            rdprep.build_header("PND54", _header_values())


if __name__ == "__main__":
    unittest.main()
