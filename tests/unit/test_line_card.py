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
        self.assertEqual(out, {"action": line_postback.ACTION_UNDO, "doc_id": "D1", "token": ""})

    def test_confirm_roundtrip(self):
        out = line_postback.parse(line_postback.confirm_data("D9"))
        self.assertEqual(out, {"action": line_postback.ACTION_CONFIRM, "doc_id": "D9", "token": ""})

    def test_discard_roundtrip(self):
        out = line_postback.parse(line_postback.discard_data("D2"))
        self.assertEqual(out, {"action": line_postback.ACTION_DISCARD, "doc_id": "D2", "token": ""})

    def test_inbox_post_roundtrip(self):
        out = line_postback.parse(line_postback.inbox_post_data("I7"))
        self.assertEqual(
            out, {"action": line_postback.ACTION_INBOX_POST, "doc_id": "I7", "token": ""}
        )

    def test_inbox_drop_roundtrip(self):
        out = line_postback.parse(line_postback.inbox_drop_data("I7"))
        self.assertEqual(
            out, {"action": line_postback.ACTION_INBOX_DROP, "doc_id": "I7", "token": ""}
        )

    def test_bad_data_rejected(self):
        self.assertEqual(line_postback.parse("garbage")["action"], "")
        self.assertEqual(line_postback.parse("")["action"], "")
        self.assertEqual(line_postback.parse("a=bogus&doc=x")["action"], "")

    def test_token_roundtrip(self):
        out = line_postback.parse(line_postback.confirm_data("D1", token="TOK9"))
        self.assertEqual(
            out, {"action": line_postback.ACTION_CONFIRM, "doc_id": "D1", "token": "TOK9"}
        )

    def test_no_token_empty(self):
        self.assertEqual(line_postback.parse(line_postback.confirm_data("D1"))["token"], "")


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
        # 状态条移到 bubble.header 后,body.contents: [金额meta, separator, 字段表, ...]
        return card["contents"]["body"]["contents"][2]["contents"]

    def test_flex_shape(self):
        c = self._card("posted")
        self.assertEqual(c["type"], "flex")
        self.assertEqual(c["contents"]["type"], "bubble")

    def test_status_is_full_bleed_header(self):
        # 状态条 = bubble.header(满宽贴边·带底色),不再是 body 内浮动圆角胶囊。
        c = self._card("posted")
        header = c["contents"]["header"]
        self.assertIn("backgroundColor", header)
        self.assertNotIn("cornerRadius", header)  # 不再是浮动胶囊
        self.assertIn("已入账", str(header))
        # body 第一项不应再是带 cornerRadius 的状态胶囊
        self.assertNotIn("已入账", str(c["contents"]["body"]["contents"][0]))

    def _footer_contents(self, card):
        return card["contents"]["footer"]["contents"]

    def test_buttons_stacked_vertically_not_crammed(self):
        # 动作区每个按钮独占一行(footer 直接子元素),不再塞进 horizontal box(治截断)。
        for state in ("posted", "confirm", "dup", "inbox"):
            foot = self._footer_contents(self._card(state, source="text"))
            for node in foot:
                self.assertIn(
                    node["type"], ("button", "separator"), f"{state} 动作区只许按钮/分隔线"
                )
                if node["type"] == "box":
                    self.fail(f"{state} 动作区不应再有 box(横排挤压)")
            self.assertTrue(any(n["type"] == "button" for n in foot))

    def test_warn_total_shows_amber_hint(self):
        import json

        s = json.dumps(self._card("confirm", warn_total=True), ensure_ascii=False)
        self.assertIn("请核对", s)
        self.assertIn("不符", s)

    def test_no_warn_total_no_hint(self):
        import json

        s = json.dumps(self._card("confirm"), ensure_ascii=False)
        self.assertNotIn("不符", s)

    def test_buttons_each_separated_by_divider(self):
        # 每个动作之间都有分隔线(posted: 复核·替代收据·撤销 三者两两之间)。
        foot = self._footer_contents(self._card("posted", source="text"))
        btns = sum(1 for n in foot if n["type"] == "button")
        seps = sum(1 for n in foot if n["type"] == "separator")
        self.assertEqual(seps, btns - 1)  # N 个按钮 → N-1 条线

    def test_action_groups_separated_by_divider(self):
        # 查看组与危险组之间有分隔线(按内容分组画线)。
        for state in ("posted", "confirm", "dup", "inbox"):
            foot = self._footer_contents(self._card(state, source="text"))
            self.assertTrue(any(n["type"] == "separator" for n in foot), f"{state} 应有分组分隔线")

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

    def test_token_embedded_in_postback_buttons(self):
        c = self._card("confirm", token="TOK9")
        toks = [
            line_postback.parse(b["action"]["data"])["token"]
            for b in self._buttons(c)
            if b["action"]["type"] == "postback"
        ]
        self.assertTrue(toks)
        self.assertTrue(all(t == "TOK9" for t in toks))

    def test_posted_text_has_substitute_receipt_link(self):
        # PO-7:文字录入(无原票)已入账卡 → 出「替代收据」深链(LIFF 落详情页 view=receipt)。
        import json

        s = json.dumps(self._card("posted", source="text"), ensure_ascii=False)
        self.assertIn("替代收据", s)
        self.assertIn("/liff/purchase/D1?view=receipt", s)

    def test_posted_doc_no_receipt_link(self):
        # 有原票(source=doc)→ 不给替代收据链接(本就有真凭证)。
        import json

        s = json.dumps(self._card("posted", source="doc"), ensure_ascii=False)
        self.assertNotIn("替代收据", s)
        self.assertNotIn("view=receipt", s)

    def test_four_langs_render(self):
        for lang in ("zh", "th", "en", "ja"):
            c = line_card.result_card(
                state="confirm", amount="50", fields=self.FIELDS, doc_id="D1", lang=lang
            )
            self.assertEqual(c["type"], "flex")
            self.assertIn(line_postback.ACTION_CONFIRM, self._actions(c))


class CardChromeI18nTests(unittest.TestCase):
    """卡片 chrome 文案 4 语键齐(抽出 line_card_i18n 后防漏键)。"""

    def test_four_langs_same_keys(self):
        from services.line_binding import line_card_i18n

        keys = {lang: set(line_card_i18n.chrome(lang)) for lang in ("zh", "th", "en", "ja")}
        for lang in ("th", "en", "ja"):
            self.assertEqual(keys["zh"], keys[lang], f"{lang} 键与 zh 不一致")
        self.assertIn("warn_total", keys["zh"])

    def test_unknown_lang_falls_back_zh(self):
        from services.line_binding import line_card_i18n

        self.assertEqual(line_card_i18n.chrome("xx"), line_card_i18n.chrome("zh"))


class DocTypeLabelTests(unittest.TestCase):
    """单据类型显 4 语人话(PO-2/PO-10):卡/详情不露 simplified_tax_invoice 等英文代号·扩到 ~26 类。"""

    def test_all_codes_have_4_langs(self):
        from services.line_binding import line_card_doctype

        codes = [c for c, *_ in line_card_doctype._DOC_TYPES]
        self.assertGreaterEqual(len(codes), 26, "doc_type 应扩到 docs/16 §2 的 ~26 类")
        for code in codes:
            for lang in ("zh", "th", "en", "ja"):
                label = line_card.doc_type_label(code, lang)
                self.assertTrue(label and label != code, f"{code}/{lang} 未译")

    def test_evidence_codes_labeled(self):
        # PO-10:银行/电商截图证据类型有人话标签(不显代号)。
        self.assertEqual(line_card.doc_type_label("payment_evidence", "zh"), "付款证据")
        self.assertEqual(line_card.doc_type_label("order_evidence", "th"), "หลักฐานคำสั่งซื้อ")

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
