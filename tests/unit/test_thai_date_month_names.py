# -*- coding: utf-8 -*-
"""月份名正典收口守门:四个消费点的新表必须与收编前旧字面量逐字一致。

2026-08-12 qwen_direct / bank_recon_utils / summary_import.dates / archive_tree
四份月份名→月号表合一收进 core/thai_date.printed_month_map。旧表字面量原样抄在
这里钉死——参数选形、缩写差集、顺序漂移都会当场红。若有差集,不许改断言迁就,
要回去查 core/thai_date 正典。
"""

import unittest

from core import thai_date
from services.export import archive_tree
from services.ocr import qwen_direct
from services.recon import bank_recon_utils
from services.summary_import import dates as summary_dates

# —— 收编前旧字面量(2026-08-12 原样抄录,勿改)——

_OLD_QWEN_MONTH_NAMES = {
    "มกราคม": 1,
    "มค": 1,
    "กุมภาพันธ์": 2,
    "กพ": 2,
    "มีนาคม": 3,
    "มีค": 3,
    "เมษายน": 4,
    "เมย": 4,
    "พฤษภาคม": 5,
    "พค": 5,
    "มิถุนายน": 6,
    "มิย": 6,
    "กรกฎาคม": 7,
    "กค": 7,
    "สิงหาคม": 8,
    "สค": 8,
    "กันยายน": 9,
    "กย": 9,
    "ตุลาคม": 10,
    "ตค": 10,
    "พฤศจิกายน": 11,
    "พย": 11,
    "ธันวาคม": 12,
    "ธค": 12,
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_OLD_RECON_TH_MONTHS = {
    "มกราคม": 1,
    "กุมภาพันธ์": 2,
    "มีนาคม": 3,
    "เมษายน": 4,
    "พฤษภาคม": 5,
    "มิถุนายน": 6,
    "กรกฎาคม": 7,
    "สิงหาคม": 8,
    "กันยายน": 9,
    "ตุลาคม": 10,
    "พฤศจิกายน": 11,
    "ธันวาคม": 12,
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_OLD_SUMMARY_THAI_MONTHS = {
    "มกราคม": 1,
    "ม.ค": 1,
    "กุมภาพันธ์": 2,
    "ก.พ": 2,
    "มีนาคม": 3,
    "มี.ค": 3,
    "เมษายน": 4,
    "เม.ย": 4,
    "พฤษภาคม": 5,
    "พ.ค": 5,
    "มิถุนายน": 6,
    "มิ.ย": 6,
    "กรกฎาคม": 7,
    "ก.ค": 7,
    "สิงหาคม": 8,
    "ส.ค": 8,
    "กันยายน": 9,
    "ก.ย": 9,
    "ตุลาคม": 10,
    "ต.ค": 10,
    "พฤศจิกายน": 11,
    "พ.ย": 11,
    "ธันวาคม": 12,
    "ธ.ค": 12,
}

_OLD_ARCHIVE_TH = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]

_OLD_ARCHIVE_EN = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


class QwenDirectTableTests(unittest.TestCase):
    def test_table_unchanged(self):
        self.assertEqual(qwen_direct._MONTH_NAMES, _OLD_QWEN_MONTH_NAMES)


class BankReconTableTests(unittest.TestCase):
    def test_table_unchanged(self):
        self.assertEqual(bank_recon_utils._TH_MONTHS, _OLD_RECON_TH_MONTHS)


class SummaryImportTableTests(unittest.TestCase):
    def test_table_unchanged(self):
        self.assertEqual(summary_dates._THAI_MONTHS, _OLD_SUMMARY_THAI_MONTHS)


class ArchiveTreeTableTests(unittest.TestCase):
    def test_th_en_lists_unchanged(self):
        self.assertEqual(archive_tree._MONTHS["th"], _OLD_ARCHIVE_TH)
        self.assertEqual(archive_tree._MONTHS["en"], _OLD_ARCHIVE_EN)


if __name__ == "__main__":
    unittest.main()
