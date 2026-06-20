# -*- coding: utf-8 -*-
"""识别结果数据卡 + postback 编解码(docs/smart-intake/15 §3/§4)。

锁(待归类已下线·三态):状态外壳结构;低置信字段琥珀 +「请核对」;按状态出对应按钮
(撤销/确认=postback,编辑=uri);postback 往返 + 非法拒。
"""

import unittest

from services.line_binding import line_card, line_card_sections, line_postback


class PostbackTests(unittest.TestCase):
    def test_undo_roundtrip(self):
        out = line_postback.parse(line_postback.undo_data("D1"))
        self.assertEqual(
            out, {"action": line_postback.ACTION_UNDO, "doc_id": "D1", "token": "", "scope": ""}
        )

    def test_confirm_roundtrip(self):
        out = line_postback.parse(line_postback.confirm_data("D9"))
        self.assertEqual(
            out, {"action": line_postback.ACTION_CONFIRM, "doc_id": "D9", "token": "", "scope": ""}
        )

    def test_discard_roundtrip(self):
        out = line_postback.parse(line_postback.discard_data("D2"))
        self.assertEqual(
            out, {"action": line_postback.ACTION_DISCARD, "doc_id": "D2", "token": "", "scope": ""}
        )

    def test_bad_data_rejected(self):
        self.assertEqual(line_postback.parse("garbage")["action"], "")
        self.assertEqual(line_postback.parse("")["action"], "")
        self.assertEqual(line_postback.parse("a=bogus&doc=x")["action"], "")

    def test_token_roundtrip(self):
        out = line_postback.parse(line_postback.confirm_data("D1", token="TOK9"))
        self.assertEqual(
            out,
            {"action": line_postback.ACTION_CONFIRM, "doc_id": "D1", "token": "TOK9", "scope": ""},
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
        # 新版分区白卡:字段行散在各分区,递归收集所有「label+value 两列文本行」。
        out = []

        def walk(n):
            if isinstance(n, dict):
                c = n.get("contents")
                if (
                    n.get("type") == "box"
                    and n.get("layout") == "horizontal"
                    and isinstance(c, list)
                    and len(c) == 2
                    and all(isinstance(x, dict) and x.get("type") == "text" for x in c)
                ):
                    out.append(n)
                if isinstance(c, list):
                    for x in c:
                        walk(x)
            elif isinstance(n, list):
                for x in n:
                    walk(x)

        walk(card["contents"]["body"])
        return out

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
        self.assertIn("费用已入账", str(header))
        # body 第一项不应再是带 cornerRadius 的状态胶囊
        self.assertNotIn("费用已入账", str(c["contents"]["body"]["contents"][0]))

    def test_product_copy_uses_receipt_card_language(self):
        import json

        s = json.dumps(self._card("confirm"), ensure_ascii=False)
        self.assertIn("2,722.00 THB", s)
        self.assertIn("请确认后入账", s)
        self.assertIn("待确认", s)
        self.assertIn("建议分类", s)
        self.assertIn("费用明细", s)
        self.assertNotIn("A" + "I", s)

    def _footer_contents(self, card):
        return card["contents"]["footer"]["contents"]

    def test_buttons_stacked_vertically_not_crammed(self):
        # 动作区每个按钮独占一行(footer 直接子元素),不再塞进 horizontal box(治截断)。
        for state in ("posted", "confirm", "dup"):
            foot = self._footer_contents(self._card(state, source="text"))
            for node in foot:
                self.assertIn(
                    node["type"], ("button", "separator"), f"{state} 动作区只许按钮/分隔线"
                )
                if node["type"] == "box":
                    self.fail(f"{state} 动作区不应再有 box(横排挤压)")
            self.assertTrue(any(n["type"] == "button" for n in foot))

    def test_items_listed_all_with_prices(self):
        # 明细按票据全部显示:逐条编号 + 名称 + 价(对标 Paypers)。
        import json

        c = line_card.result_card(
            state="confirm",
            amount="544",
            fields={
                "document_type": "receipt",
                "items": [
                    {"name": "Buffet Premium", "amount": "397.00"},
                    {"name": "Drinks", "amount": "147.00"},
                ],
            },
            doc_id="D",
            lang="zh",
        )
        s = json.dumps(c, ensure_ascii=False)
        self.assertIn("1. Buffet Premium", s)
        self.assertIn("฿397.00", s)
        self.assertIn("2. Drinks", s)
        self.assertIn("฿147.00", s)

    def test_ledger_is_full_bleed_bar(self):
        # 套账 = 满宽填色条(带 backgroundColor),不再浮动胶囊。
        c = self._card("posted", workspace_name="Bangkok Retail")
        bars = [
            n
            for n in c["contents"]["body"]["contents"]
            if isinstance(n, dict) and n.get("backgroundColor") and "Bangkok Retail" in str(n)
        ]
        self.assertTrue(bars, "套账应是带底色的满宽条")
        self.assertNotIn("cornerRadius", str(bars[0]))

    def test_warn_total_shows_amber_hint(self):
        import json

        s = json.dumps(self._card("confirm", warn_total=True), ensure_ascii=False)
        self.assertIn("请核对", s)
        self.assertIn("金额可靠", s)  # P2B:金额可靠 · 明细需检查(措辞明确)

    def test_no_warn_total_no_hint(self):
        import json

        s = json.dumps(self._card("confirm"), ensure_ascii=False)
        self.assertNotIn("金额可靠", s)

    def test_buttons_each_separated_by_divider(self):
        # 每个动作之间都有分隔线(posted: 复核·替代收据·撤销 三者两两之间)。
        foot = self._footer_contents(self._card("posted", source="text"))
        btns = sum(1 for n in foot if n["type"] == "button")
        seps = sum(1 for n in foot if n["type"] == "separator")
        self.assertEqual(seps, btns - 1)  # N 个按钮 → N-1 条线

    def test_action_groups_separated_by_divider(self):
        # 查看组与危险组之间有分隔线(按内容分组画线)。
        for state in ("posted", "confirm", "dup"):
            foot = self._footer_contents(self._card(state, source="text"))
            self.assertTrue(any(n["type"] == "separator" for n in foot), f"{state} 应有分组分隔线")

    def test_posted_detail_primary_modify_and_undo(self):
        # P1D:已入账卡 主按钮=查看详情(实心 uri)·次=修改(uri)·危险=撤销(postback)。
        c = self._card("posted")
        acts = self._actions(c)
        self.assertIn(line_postback.ACTION_UNDO, acts)
        self.assertIn("uri", acts)
        primaries = [b for b in self._buttons(c) if b["style"] == "primary"]
        self.assertEqual(len(primaries), 1)
        self.assertEqual(primaries[0]["action"]["type"], "uri")  # 查看详情=深链非动作

    def test_confirm_one_primary_plus_links(self):
        c = self._card("confirm")
        acts = self._actions(c)
        self.assertIn(line_postback.ACTION_CONFIRM, acts)
        self.assertIn("uri", acts)
        self.assertIn(line_postback.ACTION_DISCARD, acts)
        self.assertEqual(sum(1 for b in self._buttons(c) if b["style"] == "primary"), 1)

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

    def test_workspace_id_threaded_into_deeplink(self):
        # step③:该单套账 id 串进复核深链 → 复核屏自动选套账、跳过套账门。
        import json

        # 回退站内路由(无 LIFF ID)
        s = json.dumps(
            self._card("posted", source="text", workspace_client_id=7), ensure_ascii=False
        )
        self.assertIn("/liff/purchase/D1?ws=7", s)
        self.assertIn("/liff/purchase/D1?view=receipt&ws=7", s)
        # 真 LIFF 链(配了 LIFF ID)
        s2 = json.dumps(
            self._card("confirm", workspace_client_id=7, liff_id="L1"), ensure_ascii=False
        )
        self.assertIn("https://liff.line.me/L1?liff=purchase&doc=D1&ws=7", s2)

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


class P2BHygieneCardTests(unittest.TestCase):
    """P2B:卡片不裸露脏数据 + 金额不可靠禁入账 + 脏字段「请检查」提示。"""

    def _card(self, fields, amount="100.00", **kw):
        f = {"document_type": "receipt", **fields}
        return line_card.result_card(
            state="confirm", amount=amount, fields=f, doc_id="D1", lang="th", **kw
        )

    def _postback_actions(self, card):
        out = []

        def walk(n):
            if isinstance(n, dict):
                if n.get("type") == "button" and n["action"]["type"] == "postback":
                    out.append(line_postback.parse(n["action"]["data"])["action"])
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for x in n:
                    walk(x)

        walk(card)
        return out

    def test_seller_unclear_shows_fallback_not_questionmarks(self):
        import json

        c = self._card({"vendor": "", "seller_unclear": True})
        sdump = json.dumps(c, ensure_ascii=False)
        self.assertIn("ผู้ขายไม่ชัดเจน", sdump)  # th seller_unclear
        self.assertNotIn("?????", sdump)

    def test_amount_unreliable_blocks_confirm_button(self):
        c = self._card({"amount_unreliable": True})
        acts = self._postback_actions(c)
        self.assertNotIn(line_postback.ACTION_CONFIRM, acts)  # 禁确认/继续入账
        self.assertIn(line_postback.ACTION_DISCARD, acts)  # 仅丢弃 + (uri)去详情

    def test_amount_reliable_items_dirty_keeps_post_anyway(self):
        # 金额可靠 + 明细不符(warn_total)→ 仍可「继续保存」(降级·非禁止)。
        acts = self._postback_actions(self._card({}, warn_total=True))
        self.assertIn(line_postback.ACTION_CONFIRM, acts)

    def test_dirty_fields_review_notice_lists_fields(self):
        import json

        c = self._card({"dirty_fields": ["seller", "date", "tax_id"]})
        sdump = json.dumps(c, ensure_ascii=False)
        self.assertIn("โปรดตรวจสอบ", sdump)  # th fields_review

    def test_garbled_items_show_placeholder_not_questionmarks(self):
        import json

        c = self._card(
            {"items": [{"name": "?????", "amount": "45.00"}, {"name": "TW", "amount": "35.00"}]}
        )
        sdump = json.dumps(c, ensure_ascii=False)
        self.assertNotIn("?????", sdump)
        self.assertIn("รายการที่ 1", sdump)  # th item_n 占位


class PostedCardNoDirtyTests(unittest.TestCase):
    """P2B:posted/终态卡不显脏地址(serialize_supplier 已清·fields_from_detail 读清洗值)。"""

    def test_fields_from_detail_drops_blank_address(self):
        from services.line_binding import line_posted_card

        detail = {
            "doc": {"doc_date": "2026-06-18", "doc_no": "INV1", "grand_total": "100"},
            "supplier": {"name": "บางจาก", "tax_id": "0107542000011", "address": None},
        }
        f = line_posted_card.fields_from_detail(detail)
        self.assertFalse(str(f.get("seller_addr") or "").strip())  # 清洗后地址空 → 不上卡


class RecordDeepLinkTests(unittest.TestCase):
    """PO-4:卡按钮深链到该记录(LINE 打开即定位该单),不跳通用页。"""

    WEB = "https://pearnly.com/home"

    def test_doc_fallback_no_liffid(self):
        # 未配 LIFF ID → 回退站内 /liff 路由。
        self.assertEqual(
            line_card_sections.liff_link("", self.WEB, "D9"),
            "https://pearnly.com/liff/purchase/D9",
        )

    def test_liffid_builds_liff_line_me(self):
        # 配了 LIFF ID → liff.line.me 链接(LINE 用 LIFF webview 打开)。
        self.assertEqual(
            line_card_sections.liff_link("2010411313-K4TWQwYo", self.WEB, "D9"),
            "https://liff.line.me/2010411313-K4TWQwYo?liff=purchase&doc=D9",
        )
        self.assertEqual(
            line_card_sections.liff_link("LID", self.WEB, "D9", "receipt"),
            "https://liff.line.me/LID?liff=purchase&doc=D9&view=receipt",
        )

    def test_no_ref_falls_back_to_web(self):
        self.assertEqual(line_card_sections.liff_link("", self.WEB, ""), self.WEB)

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


class P1DCardTests(unittest.TestCase):
    """P1D 成品化:来源/记录号/付款/舍入/费用类型/明细折叠/空行/引导/动作重排/终态卡。"""

    def _json(self, **kw):
        import json

        kw.setdefault("state", "confirm")
        kw.setdefault("amount", "120.00")
        kw.setdefault("doc_id", "abc-123456-AABBCC")
        kw.setdefault("lang", "zh")
        kw.setdefault("fields", {})
        return json.dumps(line_card.result_card(**kw), ensure_ascii=False)

    def test_record_short_id_shown(self):
        self.assertIn("记录 #AABBCC", self._json())

    def test_sources_labeled(self):
        self.assertIn("来自图片", self._json(source="image"))
        self.assertIn("来自文件", self._json(source="file"))
        self.assertIn("来自缓存", self._json(source="cache"))
        self.assertIn("来自文字", self._json(source="text"))

    def test_payment_method_shown_when_identified(self):
        s = self._json(fields={"payment_method": "transfer"})
        self.assertIn("付款方式", s)
        self.assertIn("转账", s)

    def test_payment_status_unpaid_shown(self):
        s = self._json(fields={"payment_status": "unpaid"})
        self.assertIn("付款状态", s)
        self.assertIn("未付", s)

    def test_default_paid_not_shown(self):
        # 系统默认 paid → 不显示付款行(不把默认当真实付款)。
        s = self._json(fields={"payment_status": "paid"})
        self.assertNotIn("付款状态", s)
        self.assertNotIn("付款方式", s)

    def test_rounding_in_breakdown_when_nonzero(self):
        s = self._json(fields={"subtotal": "100", "vat": "7", "rounding": "0.25"})
        self.assertIn("舍入 ฿0.25", s)

    def test_rounding_zero_hidden(self):
        s = self._json(fields={"subtotal": "100", "rounding": "0.00"})
        self.assertNotIn("舍入", s)

    def test_expense_type_neutral_not_goods(self):
        # 餐饮/服务类不粗暴显「商品」:expense → 中性「费用」。
        s = self._json(fields={"expense_type": "expense"})
        self.assertIn("费用", s)
        self.assertNotIn("🛍 商品", s)

    def test_empty_fields_no_blank_rows(self):
        s = self._json(fields={})
        for label in ("日期", "建议分类", "子分类", "单据类型", "支出类型"):
            self.assertNotIn(label, s)

    def test_items_capped_with_overflow_hint(self):
        s = self._json(fields={"items": [{"name": f"x{i}", "amount": "1"} for i in range(8)]})
        self.assertIn("x4", s)
        self.assertNotIn("x5", s)  # 顶 5 行 = x0..x4
        self.assertIn("还有 3 行", s)

    def test_reply_guide_at_bottom(self):
        self.assertIn("如需修改", self._json())

    def test_dup_primary_is_view_not_post_anyway(self):
        c = line_card.result_card(
            state="dup", amount="99", fields={"document_type": "receipt"}, doc_id="D2", lang="zh"
        )
        primaries = [b for b in _walk_buttons(c) if b["style"] == "primary"]
        self.assertEqual(len(primaries), 1)
        # 主按钮=查看重复(uri 深链),不再是「仍要入账」postback。
        self.assertEqual(primaries[0]["action"]["type"], "uri")

    def test_terminal_voided_has_view_record(self):
        import json

        c = line_card.terminal_card(state="voided", amount="190", doc_id="D9", lang="zh")
        s = json.dumps(c, ensure_ascii=False)
        self.assertIn("已撤销", s)
        self.assertIn("查看记录", s)
        self.assertIn("footer", c["contents"])

    def test_terminal_voided_shows_vat_breakdown(self):
        # P1G:撤销后终态卡带税前/VAT 拆解 → 与确认前/确认后展示一致(不置零 VAT)。
        c = line_card.terminal_card(
            state="voided",
            amount="140",
            doc_id="D9",
            lang="zh",
            fields={"subtotal": "130.84", "vat": "9.16"},
        )
        s = str(c)
        self.assertIn("130.84", s)
        self.assertIn("9.16", s)

    def test_terminal_discarded_no_action(self):
        # 草稿已删 → 无记录可看 → 不显示不可执行动作(无 footer)。
        c = line_card.terminal_card(state="discarded", doc_id="D9", lang="zh")
        self.assertIn("已丢弃", str(c))
        self.assertNotIn("footer", c["contents"])

    def test_terminal_four_langs(self):
        for lang in ("zh", "th", "en", "ja"):
            for state in ("voided", "discarded"):
                c = line_card.terminal_card(state=state, doc_id="D", lang=lang)
                self.assertEqual(c["type"], "flex")

    def test_warn_total_demotes_confirm_to_review_first(self):
        # 明细与总额不符:confirm 卡主按钮降级为「打开核对」(uri·非确认入账 postback),
        # 入账降为次按钮「บันทึกต่อ」(仍可继续)。不假装明细完整、不默认继续入账。
        def primary(card):
            for n in card["contents"]["footer"]["contents"]:
                if n.get("type") == "button" and n.get("style") == "primary":
                    return n["action"]
            return None

        warn = line_card.result_card(
            state="confirm",
            amount="431.00",
            fields={"vendor": "X"},
            doc_id="D1",
            lang="th",
            source="image",
            warn_total=True,
        )
        self.assertEqual(primary(warn)["type"], "uri")  # 主=打开核对(去详情)
        self.assertEqual(primary(warn)["label"], "เปิดเพื่อตรวจสอบ")
        # 次按钮里仍有「继续入账」postback(允许继续保存)
        labels = [
            n["action"]["label"]
            for n in warn["contents"]["footer"]["contents"]
            if n.get("type") == "button"
        ]
        self.assertIn("บันทึกต่อ", labels)

        ok = line_card.result_card(
            state="confirm",
            amount="70.00",
            fields={"vendor": "X"},
            doc_id="D1",
            lang="th",
            source="image",
            warn_total=False,
        )
        self.assertEqual(primary(ok)["type"], "postback")  # 对账正常 → 主=确认入账
        self.assertEqual(primary(ok)["label"], "ยืนยันบันทึก")

    def test_free_modifiers_shown_as_note_not_main_items(self):
        import json

        c = line_card.result_card(
            state="confirm",
            amount="140.00",
            fields={
                "vendor": "PTT",
                "items": [{"name": "TW กาแฟ", "amount": "120.00"}],
                "modifiers": "TW ไม่หวาน 0% · แก้ว Mickey (แถมฟรี)",
            },
            doc_id="X",
            lang="th",
            source="image",
        )
        s = json.dumps(c, ensure_ascii=False)
        self.assertIn("หมายเหตุ", s)  # 备注前缀
        self.assertIn("ไม่หวาน 0%", s)  # 赠品名进备注

    def test_items_unread_hint_when_no_items(self):
        # OCR 没抽出明细:明细区出「未能逐项识别·去详情页」诚实提示,不显假的卖家名单行。
        c = line_card.result_card(
            state="confirm",
            amount="431.00",
            fields={"vendor": "Little Betong", "items": [], "items_unread": True},
            doc_id="X",
            lang="th",
            source="image",
        )

        def texts(node):
            out = []

            def w(n):
                if isinstance(n, dict):
                    if n.get("type") == "text":
                        out.append(n.get("text", ""))
                    for v in n.values():
                        w(v)
                elif isinstance(n, list):
                    for x in n:
                        w(x)

            w(node)
            return out

        joined = " ".join(texts(c))
        self.assertIn("ยังอ่านรายการย่อยไม่ได้", joined)
        self.assertNotIn("1. Little Betong", joined)


def _walk_buttons(card):
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


class AmountUnreliableReviewHeaderTests(unittest.TestCase):
    """P2B:金额不可靠/读不出 → 卡头走 review 警示态(非「请确认」成功态)+ 无确认入账主按钮。"""

    def _card(self, **fields):
        f = {"document_type": "", "vendor": "X", "date": "2026-06-19"}
        f.update(fields)
        return line_card.result_card(
            state="confirm",
            amount=f.pop("_amt", "100.00"),
            fields=f,
            doc_id="D1",
            lang="zh",
            token="t",
        )

    def test_unreliable_header_is_review_not_confirm(self):
        header = str(self._card(amount_unreliable=True)["contents"]["header"])
        self.assertIn("请先核对", header)  # t["review"]
        self.assertNotIn("请确认后入账", header)  # 不再「请确认」成功态

    def test_reliable_header_stays_confirm(self):
        self.assertIn("请确认后入账", str(self._card()["contents"]["header"]))

    def test_unreliable_has_no_confirm_postback_button(self):
        actions = []
        for b in _walk_buttons(self._card(amount_unreliable=True)):
            a = b["action"]
            actions.append(
                line_postback.parse(a["data"])["action"] if a["type"] == "postback" else "uri"
            )
        self.assertNotIn("confirm", actions)  # block_confirm:无确认入账主按钮
        self.assertIn("uri", actions)  # 仅留「打开核对」去详情


if __name__ == "__main__":
    unittest.main()
