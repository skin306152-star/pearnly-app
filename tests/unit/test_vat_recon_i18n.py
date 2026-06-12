# -*- coding: utf-8 -*-
"""销项税核查导出逐行差异文案跟用户语言(泰语报告别冒中文)。

血泪(2026-06-12):泰语导出 Excel 逐行差异列出现中文「差 -20819 天」——_diff_dims/
_build_recon_pairs 的差异/备注文案硬编码中文,不跟 lang。改 _DIFF_LABELS 4 语 + 接 lang。
"""

import unittest

from services.recon.vat_recon_core import _diff_dims, _build_recon_pairs, diff_labels


class DiffDimsI18nTests(unittest.TestCase):
    def _pair(self):
        inv = {"invoice_date": "2026-05-01", "buyer_tax_id": ""}
        rep = {"report_date": "1969-05-01", "report_buyer_tax_id": "0105551234567"}
        return inv, rep

    def test_date_diff_localized(self):
        inv, rep = self._pair()
        self.assertIn("天", _diff_dims(inv, rep, "zh")["date"])
        self.assertIn("วัน", _diff_dims(inv, rep, "th")["date"])  # 泰语「天」
        self.assertIn("d", _diff_dims(inv, rep, "en")["date"])
        self.assertIn("日", _diff_dims(inv, rep, "ja")["date"])

    def test_thai_export_no_chinese_chars(self):
        # 关键:泰语逐行差异不得出现中文字符(差/天/发/报 等)
        inv, rep = self._pair()
        th = _diff_dims(inv, rep, "th")
        for v in (th["date"], th["tax_id"]):
            for ch in "差天发报票空":
                self.assertNotIn(ch, v, f"泰语导出出现中文「{ch}」:{v}")

    def test_unknown_lang_falls_back_th(self):
        self.assertEqual(diff_labels("xx"), diff_labels("th"))

    def test_diff_labels_all_keys_4_langs(self):
        keys = set(diff_labels("zh").keys())
        for lang in ("th", "en", "ja"):
            self.assertEqual(set(diff_labels(lang).keys()), keys, f"{lang} 键集不齐")


class ReconPairsNoteI18nTests(unittest.TestCase):
    def test_cash_match_note_localized(self):
        # 散客三重匹配(名+号+金一致·双方无税号)
        inv = {"buyer_name": "ACME", "invoice_no": "INV1", "total_amount": 107}
        rep = {
            "report_buyer_name": "ACME",
            "report_invoice_no": "INV1",
            "report_amount_pre_vat": 100,
            "report_vat_amount": 7,
        }
        for lang in ("th", "en", "zh", "ja"):
            r = _build_recon_pairs([inv], [rep], lang)
            note = r["pairs"][0]["note"]
            self.assertEqual(note, diff_labels(lang)["cash_match"])
        # 泰语不含中文「散客」
        th_note = _build_recon_pairs([inv], [rep], "th")["pairs"][0]["note"]
        self.assertNotIn("散", th_note)


if __name__ == "__main__":
    unittest.main()
