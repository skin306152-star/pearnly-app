# -*- coding: utf-8 -*-
"""识别结果数据卡 + postback 编解码(docs/smart-intake/15 §3/§4)。

锁:四态外壳结构;低置信字段琥珀 +「请核对」;按状态出对应按钮(撤销/确认=postback,补全=uri);
postback 往返 + 非法拒。
"""

import unittest

from services.line_binding import line_card, line_postback


class PostbackTests(unittest.TestCase):
    def test_undo_roundtrip(self):
        out = line_postback.parse(line_postback.undo_data("D1"))
        self.assertEqual(out, {"action": line_postback.ACTION_UNDO, "doc_id": "D1"})

    def test_confirm_roundtrip(self):
        out = line_postback.parse(line_postback.confirm_data("D9"))
        self.assertEqual(out, {"action": line_postback.ACTION_CONFIRM, "doc_id": "D9"})

    def test_bad_data_rejected(self):
        self.assertEqual(line_postback.parse("garbage")["action"], "")
        self.assertEqual(line_postback.parse("")["action"], "")
        self.assertEqual(line_postback.parse("a=bogus&doc=x")["action"], "")


class CardTests(unittest.TestCase):
    FIELDS = {
        "document_type": "ใบกำกับภาษี",
        "expense_type": "goods",
        "date": "2026-06-14",
        "category": "ค่าอาหาร",
        "subcategory": "ค่าอาหารประชุม",
        "vendor": "Kodtalay",
        "invoice_number": "F33",
        "detail": "ค่าอาหาร",
    }

    def _card(self, state, fc=None):
        return line_card.result_card(
            state=state,
            amount="2,722.00",
            fields=self.FIELDS,
            field_confidence=fc or {},
            doc_id="D1",
            lang="zh",
        )

    def test_flex_shape(self):
        c = self._card("posted")
        self.assertEqual(c["type"], "flex")
        self.assertEqual(c["contents"]["type"], "bubble")

    def test_posted_has_undo_postback(self):
        c = self._card("posted")
        footer = c["contents"]["footer"]["contents"]
        actions = [b["action"]["type"] for b in footer]
        self.assertIn("postback", actions)
        pb = next(b for b in footer if b["action"]["type"] == "postback")
        self.assertEqual(
            line_postback.parse(pb["action"]["data"])["action"], line_postback.ACTION_UNDO
        )

    def test_confirm_has_confirm_postback(self):
        c = self._card("confirm")
        footer = c["contents"]["footer"]["contents"]
        pb = next(b for b in footer if b["action"]["type"] == "postback")
        self.assertEqual(
            line_postback.parse(pb["action"]["data"])["action"], line_postback.ACTION_CONFIRM
        )

    def test_inbox_only_uri_button(self):
        c = self._card("inbox")
        footer = c["contents"]["footer"]["contents"]
        self.assertEqual(len(footer), 1)
        self.assertEqual(footer[0]["action"]["type"], "uri")

    def test_low_confidence_field_ambered_and_marked(self):
        c = self._card("confirm", fc={"invoice_number": 0.5})
        rows = c["contents"]["body"]["contents"][3]["contents"]
        # 找到发票号行(label=发票号)
        target = None
        for r in rows:
            cells = r["contents"]
            if cells[1]["text"].startswith("F33"):
                target = cells[1]
        self.assertIsNotNone(target)
        self.assertIn("(请核对)", target["text"])
        self.assertEqual(target["color"], "#D97706")

    def test_high_confidence_field_not_marked(self):
        c = self._card("confirm", fc={"invoice_number": 0.99})
        rows = c["contents"]["body"]["contents"][3]["contents"]
        target = next(r["contents"][1] for r in rows if r["contents"][1]["text"].startswith("F33"))
        self.assertNotIn("(请核对)", target["text"])

    def test_dup_state_renders(self):
        c = self._card("dup")
        # dup 也出确认按钮
        footer = c["contents"]["footer"]["contents"]
        pb = next(b for b in footer if b["action"]["type"] == "postback")
        self.assertEqual(
            line_postback.parse(pb["action"]["data"])["action"], line_postback.ACTION_CONFIRM
        )

    def test_four_langs_render(self):
        for lang in ("zh", "th", "en", "ja"):
            c = line_card.result_card(
                state="posted", amount="50", fields=self.FIELDS, doc_id="D1", lang=lang
            )
            self.assertEqual(c["type"], "flex")


if __name__ == "__main__":
    unittest.main()
