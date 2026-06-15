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

    def test_discard_roundtrip(self):
        out = line_postback.parse(line_postback.discard_data("D2"))
        self.assertEqual(out, {"action": line_postback.ACTION_DISCARD, "doc_id": "D2"})

    def test_inbox_post_roundtrip(self):
        out = line_postback.parse(line_postback.inbox_post_data("I7"))
        self.assertEqual(out, {"action": line_postback.ACTION_INBOX_POST, "doc_id": "I7"})

    def test_inbox_drop_roundtrip(self):
        out = line_postback.parse(line_postback.inbox_drop_data("I7"))
        self.assertEqual(out, {"action": line_postback.ACTION_INBOX_DROP, "doc_id": "I7"})

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

    def _card(self, state, fc=None, **kw):
        kw.setdefault("amount", "2,722.00")
        return line_card.result_card(
            state=state,
            fields=self.FIELDS,
            field_confidence=fc or {},
            doc_id="D1",
            lang="zh",
            **kw,
        )

    def _buttons(self, card):
        """递归收集卡内所有 button 节点。"""
        out = []

        def walk(n):
            if isinstance(n, dict):
                if n.get("type") == "button":
                    out.append(n)
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for x in n:
                    walk(x)

        walk(card)
        return out

    def _actions(self, card):
        out = []
        for b in self._buttons(card):
            a = b["action"]
            out.append(
                line_postback.parse(a["data"])["action"] if a["type"] == "postback" else "uri"
            )
        return out

    def _fields_box(self, card):
        # body.contents: [状态条, 金额meta, separator, 字段表, ...]
        return card["contents"]["body"]["contents"][3]["contents"]

    def test_flex_shape(self):
        c = self._card("posted")
        self.assertEqual(c["type"], "flex")
        self.assertEqual(c["contents"]["type"], "bubble")

    def test_posted_has_undo_no_primary(self):
        c = self._card("posted")
        acts = self._actions(c)
        self.assertIn(line_postback.ACTION_UNDO, acts)
        self.assertIn("uri", acts)  # 复核
        # 已入账态无实心主按钮
        self.assertFalse(any(b["style"] == "primary" for b in self._buttons(c)))

    def test_confirm_one_primary_plus_links(self):
        c = self._card("confirm")
        acts = self._actions(c)
        self.assertIn(line_postback.ACTION_CONFIRM, acts)
        self.assertIn("uri", acts)
        self.assertIn(line_postback.ACTION_DISCARD, acts)
        self.assertEqual(sum(1 for b in self._buttons(c) if b["style"] == "primary"), 1)

    def test_inbox_not_dead_end(self):
        acts = self._actions(self._card("inbox"))
        self.assertIn(line_postback.ACTION_INBOX_POST, acts)
        self.assertIn("uri", acts)
        self.assertIn(line_postback.ACTION_INBOX_DROP, acts)

    def test_inbox_no_amount_no_post_button(self):
        c = self._card("inbox", amount=None, can_post=False)
        acts = self._actions(c)
        self.assertNotIn(line_postback.ACTION_INBOX_POST, acts)
        self.assertIn("uri", acts)
        self.assertIn(line_postback.ACTION_INBOX_DROP, acts)

    def test_low_confidence_field_ambered_and_marked(self):
        rows = self._fields_box(self._card("confirm", fc={"invoice_number": 0.5}))
        target = next(r["contents"][1] for r in rows if r["contents"][1]["text"].startswith("F33"))
        self.assertIn("(请核对)", target["text"])
        self.assertEqual(target["color"], "#B45309")

    def test_high_confidence_field_not_marked(self):
        rows = self._fields_box(self._card("confirm", fc={"invoice_number": 0.99}))
        target = next(r["contents"][1] for r in rows if r["contents"][1]["text"].startswith("F33"))
        self.assertNotIn("(请核对)", target["text"])

    def test_dup_primary_and_note(self):
        c = self._card("dup", dup_info={"amount": "2,722.00", "vendor": "X", "date": "2026-06-14"})
        self.assertIn(line_postback.ACTION_CONFIRM, self._actions(c))
        # 红框原记录(dup_seen 文案出现)
        flat = str(c)
        self.assertIn("已存在记录", flat)

    def test_workspace_and_source_meta(self):
        c = self._card("posted", source="text", workspace_name="Bangkok Retail")
        flat = str(c)
        self.assertIn("Bangkok Retail", flat)
        self.assertIn("来自文字", flat)

    def test_four_langs_render(self):
        for lang in ("zh", "th", "en", "ja"):
            c = line_card.result_card(
                state="confirm", amount="50", fields=self.FIELDS, doc_id="D1", lang=lang
            )
            self.assertEqual(c["type"], "flex")
            self.assertIn(line_postback.ACTION_CONFIRM, self._actions(c))


class DocTypeLabelTests(unittest.TestCase):
    """单据类型显 4 语人话(PO-2):卡/详情不露 simplified_tax_invoice 等英文代号。"""

    CODES = ("tax_invoice", "simplified_tax_invoice", "receipt", "credit_note", "other")

    def test_all_codes_have_4_langs(self):
        for code in self.CODES:
            for lang in ("zh", "th", "en", "ja"):
                label = line_card.doc_type_label(code, lang)
                self.assertTrue(label and label != code, f"{code}/{lang} 未译")

    def test_simplified_invoice_thai_and_zh(self):
        self.assertEqual(
            line_card.doc_type_label("simplified_tax_invoice", "th"), "ใบกำกับภาษีอย่างย่อ"
        )
        self.assertEqual(line_card.doc_type_label("simplified_tax_invoice", "zh"), "简式税票")

    def test_empty_stays_empty(self):
        self.assertEqual(line_card.doc_type_label("", "zh"), "")

    def test_unknown_code_falls_back_to_raw(self):
        self.assertEqual(line_card.doc_type_label("weird_type", "zh"), "weird_type")


class RecordDeepLinkTests(unittest.TestCase):
    """PO-4:卡按钮深链到该记录(LINE 打开即定位该单/待归类),不跳通用页。"""

    WEB = "https://pearnly.com/home"

    def test_doc_state_links_to_record(self):
        self.assertEqual(
            line_card._record_link(self.WEB, "D9", "confirm"),
            "https://pearnly.com/liff/purchase/D9",
        )

    def test_inbox_links_to_inbox_page(self):
        self.assertEqual(
            line_card._record_link(self.WEB, "IT1", "inbox"),
            "https://pearnly.com/liff/purchase-inbox/IT1",
        )

    def test_no_ref_falls_back_to_web(self):
        self.assertEqual(line_card._record_link(self.WEB, "", "confirm"), self.WEB)

    def test_card_footer_embeds_deep_link(self):
        import json

        c = line_card.result_card(
            state="confirm",
            amount="50",
            fields={"document_type": "receipt"},
            doc_id="D9",
            lang="zh",
        )
        self.assertIn("/liff/purchase/D9", json.dumps(c, ensure_ascii=False))


class CardFieldEnrichTests(unittest.TestCase):
    """PO-3:完整税票卡显 税号/地址/税额拆解(有值才显·无则不堆空行)。"""

    def _json(self, fields):
        import json

        c = line_card.result_card(
            state="confirm", amount="1070", fields=fields, doc_id="D", lang="zh"
        )
        return json.dumps(c, ensure_ascii=False)

    def test_full_invoice_shows_tax_addr_breakdown(self):
        s = self._json(
            {
                "document_type": "tax_invoice",
                "vendor": "ACME",
                "seller_tax": "0105551234567",
                "seller_addr": "123 Bangkok",
                "subtotal": "1000",
                "vat": "70",
                "wht": "30",
            }
        )
        self.assertIn("0105551234567", s)
        self.assertIn("123 Bangkok", s)
        self.assertIn("税前 ฿1000", s)
        self.assertIn("VAT ฿70", s)
        self.assertIn("WHT ฿30", s)

    def test_minimal_no_empty_seller_rows(self):
        s = self._json({"vendor": "x"})
        self.assertNotIn("税号", s)
        self.assertNotIn("地址", s)


if __name__ == "__main__":
    unittest.main()
