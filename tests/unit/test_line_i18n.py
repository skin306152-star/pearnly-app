# -*- coding: utf-8 -*-
"""LINE 主路径文案系统(P1E-1):12 新 key 四语齐、退役同义旧 key、语气约束、t_ocr re-export。"""

import json
import unittest

from services.line_binding import line_client, line_i18n

_P1E_KEYS = (
    "line_intro_capability",
    "line_greeting",
    "line_start_hint",
    "line_upload_hint",
    "line_processing_receipt",
    "line_ocr_failed_recovery",
    "line_not_receipt_recovery",
    "line_need_reply_record",
    "line_web_handoff",
    "line_unknown_intent",
    "line_query_summary_intro",
    "line_query_detail_intro",
)
_RETIRED = (
    "already_bound_hint",
    "guide_reply_to_record",
    "guide_need_reply_for_risk",
    "guide_open_detail",
    "exp_detail_head",
)


class KeyParityTests(unittest.TestCase):
    def test_four_langs_same_keys(self):
        keys = {lang: set(line_i18n.LINE_I18N[lang]) for lang in ("zh", "en", "th", "ja")}
        for lang in ("en", "th", "ja"):
            self.assertEqual(keys["zh"], keys[lang], f"{lang} 键与 zh 不一致")

    def test_p1e_keys_present_non_empty(self):
        for lang in ("th", "zh", "en", "ja"):
            for k in _P1E_KEYS:
                v = line_client.t_line(lang, k)
                self.assertTrue(v and v != k, f"{lang}/{k} 空或回退到 key 名")

    def test_retired_keys_gone(self):
        for k in _RETIRED:
            self.assertNotIn(k, line_i18n.LINE_I18N["zh"], f"{k} 应已退役")


class ToneTests(unittest.TestCase):
    def test_thai_uses_kha_not_khrap(self):
        th = json.dumps(line_i18n.LINE_I18N["th"], ensure_ascii=False)
        self.assertNotIn("ครับ", th)  # 统一温和专业 ค่ะ/นะคะ

    def test_capability_lists_web_handoff(self):
        # 能力说明要说明复杂业务会打开网页(不把能力说得过满)。
        for lang in ("th", "zh", "en", "ja"):
            self.assertIn("Pearnly", line_client.t_line(lang, "line_intro_capability"))

    def test_recovery_paths_actionable(self):
        # 失败恢复要给可操作路径(含重拍/输入信息的引导)。
        self.assertIn("วันที่", line_client.t_line("th", "line_ocr_failed_recovery"))
        self.assertIn("日期", line_client.t_line("zh", "line_ocr_failed_recovery"))


class OcrReexportTests(unittest.TestCase):
    def test_t_ocr_still_available_via_line_i18n(self):
        self.assertTrue(line_i18n.t_ocr("th", "err_ocr"))
        self.assertTrue(line_i18n.OCR_RESULT_I18N["zh"]["processing"])

    def test_client_contract_intact(self):
        self.assertTrue(line_client.t_ocr("en", "view_on_web"))
        self.assertTrue(line_client.t_line("ja", "line_greeting"))


if __name__ == "__main__":
    unittest.main()
