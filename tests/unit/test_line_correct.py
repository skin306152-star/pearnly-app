# -*- coding: utf-8 -*-
"""LINE 对话内改错单测(改错闭环 · P2):改什么字段 + 单/多行金额规则 + 编排顺序(mock svc)。

真库行为(克隆/连号/隔离/做账/已结期红冲)由真账号 E2E 守;这里锁纯逻辑 + 编排。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.expense import line_correct
from services.expense.expense_draft import ExpenseDraft


class _Ctx:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


class AffirmativeParseTests(unittest.TestCase):
    def test_affirmative(self):
        self.assertTrue(line_correct._affirmative("是"))
        self.assertTrue(line_correct._affirmative("ใช่"))
        self.assertTrue(line_correct._affirmative("ตกลง"))
        self.assertFalse(line_correct._affirmative("咖啡 70"))

    def test_negation_not_swallowed_as_yes(self):
        # 真实事故:泰文「ไม่ใช่(不是)」含「ใช่(是)」子串,绝不能被当确认。
        self.assertFalse(line_correct._affirmative("ไม่ใช่ กล่าวผิดไป"))
        self.assertFalse(line_correct._affirmative("ไม่ใช่"))
        self.assertFalse(line_correct._affirmative("ไม่เอา"))
        self.assertFalse(line_correct._affirmative("不对"))
        self.assertFalse(line_correct._affirmative("不是"))
        self.assertFalse(line_correct._affirmative("不用了"))
        self.assertFalse(line_correct._affirmative("no"))

    def test_parse_missing(self):
        # correct:<ws>:<doc_id>:<keys>
        self.assertEqual(
            line_correct._parse_missing("correct:5:D1:amount|vendor_name"),
            (5, "D1", ["amount", "vendor_name"]),
        )
        self.assertEqual(
            line_correct._parse_missing("correct:9:D9:category"), (9, "D9", ["category"])
        )


class CollectChangesTests(unittest.TestCase):
    def test_amount(self):
        self.assertEqual(line_correct._collect_changes({"amount": 550}), {"amount": Decimal("550")})

    def test_vendor_and_date(self):
        c = line_correct._collect_changes({"vendor_name": "7-11", "date": "2026-06-16"})
        self.assertEqual(c, {"vendor_name": "7-11", "doc_date": "2026-06-16"})

    def test_category_only_when_no_other_signal(self):
        # 「改成水电费」→ note 当科目;有金额/卖家/日期时 note 不当科目。
        self.assertEqual(line_correct._collect_changes({"note": "水电费"}), {"category": "水电费"})
        self.assertEqual(
            line_correct._collect_changes({"amount": 50, "note": "50"}), {"amount": Decimal("50")}
        )

    def test_bad_date_and_zero_amount_dropped(self):
        self.assertEqual(line_correct._collect_changes({"date": "昨天", "amount": 0}), {})

    def test_payment_only_when_named_in_text(self):
        # 点名付款方式才从原文归一;裸记账文本(无付款方式词)不误把「现金」当改付款。
        self.assertEqual(
            line_correct._collect_changes({}, "付款方式改成现金"), {"payment_method": "cash"}
        )
        self.assertEqual(
            line_correct._collect_changes({"amount": 50}, "现金买咖啡 50"),
            {"amount": Decimal("50")},
        )


class ApplyChangesTests(unittest.TestCase):
    def _data(self):
        return {"lines": [{"unit_price": Decimal("60"), "qty": Decimal("2"), "category_id": "old"}]}

    def test_vendor(self):
        data = self._data()
        line_correct._apply_changes(
            None, data, ExpenseDraft(vendor_name="7-11"), ["vendor_name"], "t", 1, {}
        )
        self.assertEqual(data["supplier"], {"name": "7-11", "tax_id": None})

    def test_date(self):
        data = self._data()
        line_correct._apply_changes(
            None, data, ExpenseDraft(doc_date="2026-06-16"), ["doc_date"], "t", 1, {}
        )
        self.assertEqual(data["doc_date"], "2026-06-16")

    def test_amount_single_line_sets_unit_price_qty1(self):
        data = self._data()
        line_correct._apply_changes(
            None, data, ExpenseDraft(amount=Decimal("550")), ["amount"], "t", 1, {}
        )
        self.assertEqual(data["lines"][0]["unit_price"], "550")
        self.assertEqual(data["lines"][0]["qty"], "1")
        self.assertIsNone(data["amount_override"])

    def test_payment_method_sets_doc_field(self):
        data = {"lines": [{}]}
        line_correct._apply_changes(
            None, data, ExpenseDraft(payment_method="cash"), ["payment_method"], "t", 1, {}
        )
        self.assertEqual(data["payment_method"], "cash")

    def test_category_resolves_and_sets_lines(self):
        data = {"lines": [{"category_id": "x"}, {"category_id": "y"}]}
        with mock.patch.object(line_correct, "_resolve_category", return_value=("p1", "c1")):
            line_correct._apply_changes(
                None, data, ExpenseDraft(note="水电费"), ["category"], "t", 1, {}
            )
        self.assertEqual(data["category_id"], "p1")
        self.assertTrue(
            all(ln["category_id"] == "p1" and ln["subcategory_id"] == "c1" for ln in data["lines"])
        )


class CloneLineTests(unittest.TestCase):
    def test_preserves_totals_fields(self):
        ln = {
            "item_type": "service",
            "description": "x",
            "qty": Decimal("2"),
            "unit_price": Decimal("60"),
            "discount": Decimal("0"),
            "vat_rate": Decimal("7"),
            "vat_applicable": True,
            "wht_rate": Decimal("0"),
            "category_id": "c",
            "subcategory_id": "s",
        }
        out = line_correct._clone_line(ln)
        self.assertEqual(out["qty"], Decimal("2"))
        self.assertEqual(out["unit_price"], Decimal("60"))
        self.assertEqual(out["vat_rate"], Decimal("7"))
        self.assertEqual(out["item_type"], "service")


class ApplyTests(unittest.TestCase):
    def test_voids_clones_updates_posts_when_autobook(self):
        from services.purchase import correct as correct_svc
        from services.purchase import docs as docs_svc
        from services.purchase import posting as posting_svc
        from services.purchase import settings as settings_svc

        orig = {"doc": {"status": "posted"}, "supplier": {}, "lines": []}
        clone = {"doc": {"id": "new1"}, "supplier": {}, "lines": []}
        calls = []
        with (
            mock.patch.object(docs_svc, "get_doc", return_value=orig),
            mock.patch.object(
                correct_svc,
                "correct_doc",
                side_effect=lambda *a, **k: calls.append("clone") or clone,
            ),
            mock.patch.object(
                docs_svc,
                "update_draft",
                side_effect=lambda *a, **k: calls.append("update")
                or {"doc": {"grand_total": Decimal("550")}},
            ),
            mock.patch.object(settings_svc, "get_settings", return_value={"auto_book": True}),
            mock.patch.object(
                posting_svc, "post_doc", side_effect=lambda *a, **k: calls.append("post")
            ),
        ):
            res = line_correct._apply(
                object(), {"id": "u"}, "t", 1, "D1", ExpenseDraft(amount=Decimal("550")), ["amount"]
            )
        self.assertEqual(
            res,
            {"new_id": "new1", "posted": True, "total": Decimal("550"), "mode": "posted_reclone"},
        )
        self.assertEqual(calls, ["clone", "update", "post"])  # 先克隆→改→过账

    def test_draft_when_autobook_off(self):
        from services.purchase import correct as correct_svc
        from services.purchase import docs as docs_svc
        from services.purchase import posting as posting_svc
        from services.purchase import settings as settings_svc

        orig = {"doc": {"status": "posted"}, "supplier": {}, "lines": []}
        with (
            mock.patch.object(docs_svc, "get_doc", return_value=orig),
            mock.patch.object(
                correct_svc,
                "correct_doc",
                return_value={"doc": {"id": "n"}, "supplier": {}, "lines": []},
            ),
            mock.patch.object(
                docs_svc, "update_draft", return_value={"doc": {"grand_total": Decimal("1")}}
            ),
            mock.patch.object(settings_svc, "get_settings", return_value={"auto_book": False}),
            mock.patch.object(posting_svc, "post_doc") as post,
        ):
            res = line_correct._apply(
                object(), {"id": "u"}, "t", 1, "D1", ExpenseDraft(vendor_name="X"), ["vendor_name"]
            )
        self.assertFalse(res["posted"])
        post.assert_not_called()

    def test_none_when_target_void(self):
        from services.purchase import docs as docs_svc

        with mock.patch.object(docs_svc, "get_doc", return_value={"doc": {"status": "void"}}):
            self.assertIsNone(
                line_correct._apply(object(), {"id": "u"}, "t", 1, "D1", ExpenseDraft(), ["amount"])
            )

    def test_draft_edits_in_place_no_void_no_post(self):
        # 草稿:原地 update_draft,不冲销(correct_doc 不调)、不过账,mode=draft_inplace。
        from services.purchase import correct as correct_svc
        from services.purchase import docs as docs_svc
        from services.purchase import posting as posting_svc
        from services.purchase import settings as settings_svc

        draft = {"doc": {"status": "draft", "id": "D1"}, "supplier": {}, "lines": [{}]}
        seen = {}
        with (
            mock.patch.object(docs_svc, "get_doc", return_value=draft),
            mock.patch.object(correct_svc, "correct_doc") as clone,
            mock.patch.object(
                docs_svc,
                "update_draft",
                side_effect=lambda *a, **k: seen.update(doc_id=k.get("doc_id"))
                or {"doc": {"grand_total": Decimal("200")}},
            ),
            mock.patch.object(settings_svc, "get_settings", return_value={"auto_book": True}),
            mock.patch.object(posting_svc, "post_doc") as post,
        ):
            res = line_correct._apply(
                object(), {"id": "u"}, "t", 1, "D1", ExpenseDraft(amount=Decimal("200")), ["amount"]
            )
        clone.assert_not_called()  # 草稿不冲销克隆
        post.assert_not_called()  # 草稿不自动过账(仍待卡片确认)
        self.assertEqual(seen["doc_id"], "D1")  # 原地改同一张
        self.assertEqual(res["mode"], "draft_inplace")
        self.assertFalse(res["posted"])


class RequestCorrectTests(unittest.TestCase):
    """request_correct:收集改动 + 定位目标 → 委托 _apply_or_confirm(风险三档在 ApplyOrConfirmTests 单测)。"""

    def _run(self, u, tgt, *, quoted_message_id=None, text="改"):
        from services.line_binding import line_message_refs

        replies, captured = [], {}
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(line_message_refs, "resolve_target", return_value=tgt),
            mock.patch.object(
                line_correct,
                "_apply_or_confirm",
                side_effect=lambda *a, **k: captured.update(ws=a[4], doc_id=a[5], changes=a[6])
                or True,
            ),
            mock.patch.object(
                line_correct.line_reply,
                "reply_text_context",
                side_effect=lambda tok, msg, **k: replies.append(msg) or True,
            ),
            mock.patch.object(
                line_correct.line_client, "t_line", side_effect=lambda lang, key, **k: key
            ),
        ):
            line_correct.request_correct(
                {"id": "u"}, "tok", "U1", text, u, quoted_message_id, "zh", "t", 1
            )
        return replies, captured

    _OK = {"doc_id": "D1", "ws": 1, "how": "last", "error": None}

    def test_no_changes_guides_reply(self):
        replies, cap = self._run({}, self._OK)
        self.assertEqual(replies, ["line_need_reply_record"])
        self.assertEqual(cap, {})  # 没抽出改动 → 不委托执行

    def test_ambiguous_prompts_reply(self):
        replies, _ = self._run({"amount": 500}, {"doc_id": None, "ws": 1, "error": "ambiguous"})
        self.assertEqual(replies, ["line_need_reply_record"])

    def test_ref_not_found_guides_detail_list(self):
        replies, _ = self._run({"amount": 500}, {"doc_id": None, "ws": 1, "error": "ref_not_found"})
        self.assertEqual(replies, ["guide_detail_list"])

    def test_resolved_delegates_with_changes_and_ws(self):
        _, cap = self._run(
            {"vendor_name": "7-11"}, {"doc_id": "D9", "ws": 3, "how": "quoted", "error": None}
        )
        self.assertEqual((cap["ws"], cap["doc_id"]), (3, "D9"))
        self.assertEqual(cap["changes"], {"vendor_name": "7-11"})


class ApplyOrConfirmTests(unittest.TestCase):
    """改错执行三档:草稿单非金额→直接改;已入账/金额/多字段→确认;多行金额→详情页。"""

    def _run(self, changes, detail):
        from services.purchase import docs as docs_svc

        replies, saved, applied = [], {}, []
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(docs_svc, "get_doc", return_value=detail),
            mock.patch.object(
                line_correct.conversation,
                "save_pending",
                side_effect=lambda *a, **k: saved.update(k),
            ),
            mock.patch.object(line_correct.conversation, "clear_pending"),
            mock.patch.object(
                line_correct,
                "_apply",
                side_effect=lambda *a, **k: applied.append(a)
                or {
                    "new_id": "D1",
                    "posted": False,
                    "total": Decimal("1"),
                    "mode": "draft_inplace",
                },
            ),
            mock.patch.object(
                line_correct.line_reply,
                "reply_text_context",
                side_effect=lambda tok, msg, **k: replies.append(msg) or True,
            ),
            mock.patch.object(
                line_correct.line_client, "t_line", side_effect=lambda lang, key, **k: key
            ),
        ):
            line_correct._apply_or_confirm(
                "tok", {"id": "u"}, "zh", "t", 1, "D1", changes, line_user_id="U1"
            )
        return replies, saved, applied

    def test_draft_single_nonamount_executes_directly(self):
        # 低风险:草稿改卖家 → 直接执行 + 完成回执,不存确认 pending。
        detail = {"doc": {"status": "draft"}, "supplier": {"name": "711"}, "lines": [{}]}
        replies, saved, applied = self._run({"vendor_name": "7-11"}, detail)
        self.assertEqual(len(applied), 1)  # 直接改
        self.assertEqual(saved, {})  # 不存确认态
        self.assertIn("7-11", replies[0])  # 完成回执(CHANGED_DONE)

    def test_posted_nonamount_confirms(self):
        # 高风险:已入账 → 确认(不直接改)。
        detail = {"doc": {"status": "posted"}, "supplier": {"name": "711"}, "lines": [{}]}
        replies, saved, applied = self._run({"vendor_name": "7-11"}, detail)
        self.assertEqual(applied, [])  # 不直接改
        self.assertEqual(saved["missing"], "correct:1:D1:vendor_name")
        self.assertIn("7-11", replies[0])  # 确认含新值

    def test_draft_amount_confirms(self):
        # 高风险:改金额(税额重算)→ 即便草稿也确认。
        detail = {"doc": {"status": "draft", "grand_total": "190"}, "lines": [{}]}
        replies, saved, applied = self._run({"amount": Decimal("200")}, detail)
        self.assertEqual(applied, [])
        self.assertEqual(saved["missing"], "correct:1:D1:amount")

    def test_amount_multiline_guides_detail(self):
        detail = {"doc": {"status": "draft"}, "lines": [{}, {}]}
        replies, saved, applied = self._run({"amount": Decimal("110")}, detail)
        self.assertEqual((applied, saved), ([], {}))
        self.assertIn("明细", replies[0])  # MULTILINE_EDIT

    def test_void_target_honest(self):
        replies, saved, applied = self._run({"vendor_name": "x"}, {"doc": {"status": "void"}})
        self.assertEqual((applied, saved), ([], {}))
        self.assertEqual(replies, ["exp_correct_none"])


class MaybeClarifyFeedbackTests(unittest.TestCase):
    """采购改错澄清(P1E-2):命中「识别错了/不对/wrong/ผิด」→ 本层接管(绝不当 OCR 失败重拍)。"""

    def _run(self, text, *, quoted="MID1", tgt=None, lines=None):
        from services.line_binding import line_message_refs
        from services.purchase import docs as docs_svc

        tgt = tgt if tgt is not None else {"doc_id": "D1", "ws": 1, "error": None}
        detail = {"doc": {"grand_total": "70.00"}, "lines": lines if lines is not None else [{}]}
        ctx = {"line_user_id": "U1", "tenant_id": "t", "quote_token": "q"}
        sent = {}
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(line_message_refs, "resolve_target", return_value=tgt),
            mock.patch.object(docs_svc, "get_doc", return_value=detail),
            mock.patch.object(
                line_correct.conversation, "save_pending"
            ),  # 多轮态存储(本测不验持久化)
            mock.patch.object(
                line_correct.line_reply,
                "reply_text_context",
                side_effect=lambda tok, body, **k: sent.update(body=body) or True,
            ),
        ):
            res = line_correct.maybe_clarify_feedback("tok", text, "th", 1, quoted, ctx)
        return res, sent.get("body", "")

    def test_vague_quoted_clarifies_fields_in_input_lang(self):
        # 验收 #1:笼统说错了 → 列可改字段(中文输入→中文,不被泰语主语言带偏)。
        res, body = self._run("这个你识别错了")
        self.assertTrue(res)
        self.assertIn("你想改金额", body)

    def test_thai_vague_clarifies_in_thai(self):
        res, body = self._run("อ่านผิด")
        self.assertTrue(res)
        self.assertIn("ต้องการแก้ส่วนไหน", body)

    def test_field_seller_asks_for_value(self):
        # 验收 #3:点名卖家但没给新值 → 问新卖家(并引导「改成」语法)。
        res, body = self._run("卖家不对")
        self.assertTrue(res)
        self.assertIn("卖家", body)
        self.assertIn("改成", body)

    def test_quoted_field_without_feedback_word_triggers(self):
        # 「卖家不是这个 / ผู้ขายไม่ใช่คนนี้」无反馈词,但引用了卡片且点名字段 → 仍走改错澄清,
        # 不被收入识别(ผู้ขาย 含 ขาย)劫持。
        res, body = self._run("卖家不是这个", quoted="MID1")
        self.assertTrue(res)
        self.assertIn("卖家", body)

    def test_items_guides_detail_page(self):
        # 验收 #4:明细错了 → 引导详情页核对(不假装明细完整)。
        res, body = self._run("明细错了")
        self.assertTrue(res)
        self.assertIn("详情页", body)

    def test_payment_asks_for_value(self):
        # 付款方式现可直接改(低风险)→ 点名但没给值 → 问新值(不再甩详情页/网页)。
        res, body = self._run("付款方式不对")
        self.assertTrue(res)
        self.assertIn("付款方式", body)
        self.assertIn("改成", body)  # ASK_VALUE 引导语法

    def test_concrete_edit_falls_through_to_edit(self):
        # 「改成X」是具体编辑 → 交 edit 流(request_correct),本层不接管。
        res, _ = self._run("金额改成 70")
        self.assertFalse(res)

    def test_unresolved_quote_guides_reply(self):
        # 验收 #5:引用过期/无法定位 → 引导回复要改的那条(不回 photo_failed)。
        res, body = self._run("识别错了", tgt={"doc_id": None, "ws": 1, "error": "ref_not_found"})
        self.assertTrue(res)
        self.assertTrue(body)

    def test_no_quote_no_amount_guides_reply(self):
        # 验收 #5:无引用纯说错了 → 引导回复记录,而非 OCR 失败帮助。
        res, body = self._run("这个识别错了", quoted=None, tgt={"error": "ambiguous"})
        self.assertTrue(res)
        self.assertTrue(body)

    def test_no_quote_with_amount_passes_through(self):
        # 「买错了 50」像新记账(有金额、无引用)→ 放行记账流,不劫持。
        res, _ = self._run("买错了 50", quoted=None, tgt={"error": "ambiguous"})
        self.assertFalse(res)


class TryConfirmTests(unittest.TestCase):
    def _peek(self, missing):
        return mock.patch.object(
            line_correct.conversation,
            "peek_pending",
            return_value={"missing": missing, "draft": ExpenseDraft()},
        )

    def test_ignores_amount_pending(self):
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            self._peek("amount"),
        ):
            self.assertFalse(
                line_correct.try_confirm({"id": "u"}, "tok", "U1", "咖啡 70", "t", 1, "zh")
            )

    def test_ignores_detail_pending(self):
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            self._peek("detail:A,B"),
        ):
            self.assertFalse(line_correct.try_confirm({"id": "u"}, "tok", "U1", "是", "t", 1, "zh"))

    def test_executes_on_yes(self):
        applied = {}
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            self._peek("correct:1:D1:amount"),
            mock.patch.object(line_correct.conversation, "clear_pending"),
            mock.patch.object(
                line_correct,
                "_apply",
                side_effect=lambda c, bu, tid, ws, oid, draft, keys: applied.update(
                    {"o": oid, "k": keys}
                )
                or {"new_id": "n", "posted": True, "total": Decimal("550")},
            ),
            mock.patch.object(line_correct.line_reply, "reply_text_context"),
        ):
            out = line_correct.try_confirm({"id": "u"}, "tok", "U1", "是", "t", 1, "zh")
        self.assertTrue(out)
        self.assertEqual(applied, {"o": "D1", "k": ["amount"]})

    def test_cancels_on_no(self):
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            self._peek("correct:1:D1:amount"),
            mock.patch.object(line_correct.conversation, "clear_pending") as clr,
            mock.patch.object(line_correct.line_reply, "reply_text_context"),
            mock.patch.object(line_correct, "_apply") as ap,
        ):
            out = line_correct.try_confirm({"id": "u"}, "tok", "U1", "不用了", "t", 1, "zh")
        self.assertTrue(out)
        clr.assert_called_once()
        ap.assert_not_called()

    def test_period_closed_guides(self):
        from core.pos_api import PosError

        replies = []
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            self._peek("correct:1:D1:amount"),
            mock.patch.object(line_correct.conversation, "clear_pending"),
            mock.patch.object(
                line_correct, "_apply", side_effect=PosError("acct.period_closed", 409)
            ),
            mock.patch.object(
                line_correct.line_reply,
                "reply_text_context",
                side_effect=lambda tok, msg, **k: replies.append(msg) or True,
            ),
            mock.patch.object(
                line_correct.line_client, "t_line", side_effect=lambda lang, key, **k: key
            ),
        ):
            out = line_correct.try_confirm({"id": "u"}, "tok", "U1", "是", "t", 1, "zh")
        self.assertTrue(out)
        self.assertEqual(replies, ["exp_correct_closed"])


if __name__ == "__main__":
    unittest.main()
