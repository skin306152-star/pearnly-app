# -*- coding: utf-8 -*-
"""客户回答回写(services/line_binding/line_client_answer)· D2-S5 契约。

钉死主窗拍板修正硬门:①编号答题回写走 record_decision + 同票兄弟自动关闭;
②歧义答案不回写、原文存底转人审;③双重身份判不出答题时零介入、原路回落记账;
④竞态守卫——问题创建后已有人工裁决就不覆盖,转 resolved_internally;⑤闸关/
无 pending 时拦截零介入;⑥金额答案 Decimal 精确解析。
"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_answer as m
from services.workorder import decisions

_NOW = datetime(2026, 7, 11, 10, 0, tzinfo=timezone.utc)


def _question(**overrides) -> dict:
    row = {
        "id": 1,
        "tenant_id": "t-1",
        "workspace_client_id": 84,
        "work_order_id": "wo-1",
        "item_id": "item-1",
        "period": "2026-07",
        "question_type": vocab.QUESTION_DIRECTION,
        "question_payload": {},
        "status": vocab.PENDING,
        "batch_id": "batch-1",
        "answer_raw": None,
        "resolution": None,
        "created_by": "user:1",
        "created_at": _NOW - timedelta(hours=1),
        "sent_at": _NOW,
        "answered_at": None,
        "closed_at": None,
        "updated_at": _NOW,
    }
    row.update(overrides)
    return row


def _contact(tenant_id="t-1", workspace_client_id=84, lang="th"):
    return {
        "tenant_id": tenant_id,
        "workspace_client_id": workspace_client_id,
        "line_user_id": "U-163",
        "preferred_lang": lang,
    }


def _cm(cur):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cur)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _order_detail(flagged=None):
    return {"flagged": flagged or []}


class LooksLikeAnswerTests(unittest.TestCase):
    def test_leading_number_is_classifiable(self):
        self.assertTrue(m._looks_like_answer("1 ซื้อ"))

    def test_mid_sentence_number_is_classifiable(self):
        self.assertTrue(m._looks_like_answer("เอา 2 ขาย"))

    def test_keyword_without_number_is_classifiable(self):
        self.assertTrue(m._looks_like_answer("ตัดออกค่ะ"))

    def test_plain_expense_text_is_not_classifiable(self):
        self.assertFalse(m._looks_like_answer("กาแฟ 100"))

    def test_bare_amount_is_not_a_marker(self):
        self.assertFalse(m._looks_like_answer("2,647.50"))


class SplitNumberedSegmentsTests(unittest.TestCase):
    def test_single_marker_with_space(self):
        self.assertEqual(m._split_numbered_segments("1 ซื้อ"), [(1, "ซื้อ")])

    def test_marker_with_punctuation_no_space(self):
        self.assertEqual(m._split_numbered_segments("1)ซื้อ"), [(1, "ซื้อ")])

    def test_multi_answer_one_message(self):
        self.assertEqual(m._split_numbered_segments("1 ซื้อ 2 ขาย"), [(1, "ซื้อ"), (2, "ขาย")])

    def test_no_marker_returns_empty(self):
        self.assertEqual(m._split_numbered_segments("ไม่แน่ใจค่ะ"), [])


class ResolveTests(unittest.TestCase):
    def test_direction_purchase(self):
        self.assertEqual(
            m._resolve(vocab.QUESTION_DIRECTION, "ซื้อ"),
            (decisions.ASSIGN_KIND, decisions.PURCHASE_INVOICE, None),
        )

    def test_direction_conflicting_keywords_is_ambiguous(self):
        self.assertIsNone(m._resolve(vocab.QUESTION_DIRECTION, "ซื้อหรือขายดีนะ"))

    def test_direction_unrecognized_is_ambiguous(self):
        self.assertIsNone(m._resolve(vocab.QUESTION_DIRECTION, "ไม่แน่ใจ"))

    def test_drop_keyword(self):
        self.assertEqual(m._resolve(vocab.QUESTION_DROP, "ซ้ำค่ะ"), (decisions.EXCLUDE, None, None))

    def test_amount_unique_decimal(self):
        decision, kind, values = m._resolve(vocab.QUESTION_AMOUNT, "2,647.50 ใช่ค่ะ")
        self.assertEqual(decision, decisions.RECALC)
        self.assertIsNone(kind)
        self.assertEqual(values, {"vat": "2647.50"})

    def test_amount_multiple_numbers_is_ambiguous(self):
        self.assertIsNone(m._resolve(vocab.QUESTION_AMOUNT, "100 หรือ 200 ไม่แน่ใจ"))

    def test_freeform_always_ambiguous(self):
        self.assertIsNone(m._resolve(vocab.QUESTION_FREEFORM, "1234567890123"))


class SelectBatchTests(unittest.TestCase):
    def test_no_contacts_returns_none(self):
        with patch(
            "services.line_binding.line_client_contact.list_contacts_by_line_user", return_value=[]
        ):
            self.assertIsNone(m._select_batch("U-163"))

    def test_gate_closed_tenant_is_skipped(self):
        with (
            patch(
                "services.line_binding.line_client_contact.list_contacts_by_line_user",
                return_value=[_contact()],
            ),
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=False),
            patch(
                "services.line_binding.line_client_pool_store.list_for_client"
            ) as list_for_client,
        ):
            self.assertIsNone(m._select_batch("U-163"))
        list_for_client.assert_not_called()  # 闸关直接跳过,不查池

    def test_picks_most_recent_batch_across_clients(self):
        older = _question(id=1, workspace_client_id=1, sent_at=_NOW - timedelta(days=1))
        newer = _question(id=2, workspace_client_id=2, sent_at=_NOW)
        contacts = [_contact(workspace_client_id=1), _contact(workspace_client_id=2)]
        with (
            patch(
                "services.line_binding.line_client_contact.list_contacts_by_line_user",
                return_value=contacts,
            ),
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_pool_store.list_for_client",
                side_effect=[[older], [newer]],
            ),
        ):
            out = m._select_batch("U-163")
        self.assertEqual(out["workspace_client_id"], 2)
        self.assertEqual(out["rows"], [newer])


class HandleAnswerConsumptionGateTests(unittest.TestCase):
    """断言③:双重身份(登录用户)判不出答题 → 零介入,原样回落记账路径。"""

    def test_dual_identity_unclassifiable_text_returns_false(self):
        with (
            patch.object(
                m,
                "_select_batch",
                return_value={
                    "tenant_id": "t-1",
                    "workspace_client_id": 84,
                    "rows": [_question()],
                    "lang": "th",
                },
            ),
            patch("core.db.get_user_by_line_user_id", return_value={"id": "u-1"}),
            patch.object(m, "_consume") as consume,
        ):
            out = m.handle_answer("U-163", "กาแฟ 100", "rt-1", None)
        self.assertFalse(out)
        consume.assert_not_called()

    def test_dual_identity_numbered_text_is_consumed(self):
        with (
            patch.object(
                m,
                "_select_batch",
                return_value={
                    "tenant_id": "t-1",
                    "workspace_client_id": 84,
                    "rows": [_question()],
                    "lang": "th",
                },
            ),
            patch("core.db.get_user_by_line_user_id", return_value={"id": "u-1"}),
            patch.object(m, "_consume") as consume,
        ):
            out = m.handle_answer("U-163", "1 ซื้อ", "rt-1", None)
        self.assertTrue(out)
        consume.assert_called_once()

    def test_no_pending_returns_false(self):
        """断言⑤:无 pending(或闸关)→ 拦截零介入。"""
        with (
            patch.object(m, "_select_batch", return_value=None),
            patch("core.db.get_user_by_line_user_id") as get_user,
        ):
            out = m.handle_answer("U-163", "1 ซื้อ", "rt-1", None)
        self.assertFalse(out)
        get_user.assert_not_called()  # 没批次就不必再问身份

    def test_pure_customer_freeform_is_consumed(self):
        """非登录用户(纯客户)不受编号/关键词门槛约束,任何文本都进入消费阶段。"""
        with (
            patch.object(
                m,
                "_select_batch",
                return_value={
                    "tenant_id": "t-1",
                    "workspace_client_id": 84,
                    "rows": [_question()],
                    "lang": "th",
                },
            ),
            patch("core.db.get_user_by_line_user_id", return_value=None),
            patch.object(m, "_consume") as consume,
        ):
            out = m.handle_answer("U-163", "เดี๋ยวเช็คให้นะ", "rt-1", None)
        self.assertTrue(out)
        consume.assert_called_once()

    def test_selection_failure_fails_open(self):
        with patch.object(m, "_select_batch", side_effect=RuntimeError("db down")):
            self.assertFalse(m.handle_answer("U-163", "1 ซื้อ", "rt-1", None))


class HandleOneAppliedTests(unittest.TestCase):
    """断言①:「1 ซื้อ」→ human_decision(assign_kind,purchase_invoice,actor=line_client:…)
    落库 + 问题转 applied + 同票兄弟被关。"""

    def test_direction_answer_records_decision_and_closes_siblings(self):
        q = _question(id=10)
        sibling = _question(id=11, question_type=vocab.QUESTION_AMOUNT)  # 同票「兄弟」(防御性场景)
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch(
                "services.workorder.api.order_detail",
                return_value=_order_detail(),
            ),
            patch(
                "services.workorder.api.record_decision",
                return_value={"id": "evt-1"},
            ) as record,
            patch("services.line_binding.line_client_pool_store.transition") as transition,
            patch(
                "services.line_binding.line_client_pool_store.list_for_client",
                return_value=[q, sibling],
            ),
            patch("services.line_binding.line_reply.reply_text_context") as reply,
        ):
            m._handle_one("t-1", 84, q, "ซื้อ", "U-163", "rt-1", None, "th")

        record.assert_called_once_with(
            cur,
            tenant_id="t-1",
            work_order_id="wo-1",
            item_id="item-1",
            decision=decisions.ASSIGN_KIND,
            values=None,
            actor="line_client:U-163",
            kind=decisions.PURCHASE_INVOICE,
        )
        # 问题本身转 applied
        applied_call = next(c for c in transition.call_args_list if c.args[1] == 10)
        self.assertEqual(applied_call.args[2], vocab.APPLIED)
        # 同票兄弟(同 work_order_id + item_id,排除自己)转 resolved_internally
        sibling_call = next(c for c in transition.call_args_list if c.args[1] == 11)
        self.assertEqual(sibling_call.args[2], vocab.RESOLVED_INTERNALLY)
        reply.assert_called_once()


class HandleOneAmbiguousTests(unittest.TestCase):
    """断言②:歧义答案不回写,原文存底转人审。"""

    def test_ambiguous_answer_goes_to_manual_review_without_recording(self):
        q = _question(id=20)
        with (
            patch("services.workorder.api.record_decision") as record,
            patch("services.line_binding.line_client_pool_store.transition") as transition,
            patch("services.line_binding.line_reply.reply_text_context"),
        ):
            m._handle_one("t-1", 84, q, "ไม่แน่ใจ", "U-163", "rt-1", None, "th")

        record.assert_not_called()
        transition.assert_called_once_with(
            "t-1", 20, vocab.MANUAL_REVIEW, answer_raw="ไม่แน่ใจ", resolution=None
        )


class RaceGuardTests(unittest.TestCase):
    """断言④:先会计裁后客户答 → 客户答不成为 latest,问题转 resolved_internally。"""

    def test_decision_after_question_created_blocks_overwrite(self):
        created_at = _NOW - timedelta(hours=1)
        accountant_decision_at = _NOW - timedelta(minutes=10)  # 晚于问题创建,先会计裁了
        q = _question(id=30, created_at=created_at)
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch(
                "services.workorder.api.order_detail",
                return_value=_order_detail(
                    flagged=[
                        {
                            "item_id": "item-1",
                            "decision": {
                                "decision": decisions.EXCLUDE,
                                "actor": "user:9",
                                "at": accountant_decision_at,
                            },
                        }
                    ]
                ),
            ),
            patch("services.workorder.api.record_decision") as record,
            patch("services.line_binding.line_client_pool_store.transition") as transition,
            patch("services.line_binding.line_reply.reply_text_context") as reply,
        ):
            m._handle_one("t-1", 84, q, "ซื้อ", "U-163", "rt-1", None, "th")

        record.assert_not_called()  # 绝不覆盖会计裁决
        transition.assert_called_once_with(
            "t-1", 30, vocab.RESOLVED_INTERNALLY, answer_raw="ซื้อ", resolution=None
        )
        reply.assert_called_once()
        # 回的是「已处理」话术,不是普通 manual_review 文案(区分两种关闭原因)。
        self.assertEqual(reply.call_args.args[1], m._ALREADY_HANDLED_COPY["th"])

    def test_decision_before_question_created_does_not_block(self):
        created_at = _NOW
        old_decision_at = _NOW - timedelta(days=5)  # 早于问题创建,不算竞态
        q = _question(id=31, created_at=created_at)
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch(
                "services.workorder.api.order_detail",
                return_value=_order_detail(
                    flagged=[
                        {
                            "item_id": "item-1",
                            "decision": {"decision": decisions.EXCLUDE, "at": old_decision_at},
                        }
                    ]
                ),
            ),
            patch("services.workorder.api.record_decision", return_value={"id": "evt-2"}) as record,
            patch("services.line_binding.line_client_pool_store.transition"),
            patch("services.line_binding.line_client_pool_store.list_for_client", return_value=[q]),
            patch("services.line_binding.line_reply.reply_text_context"),
        ):
            m._handle_one("t-1", 84, q, "ซื้อ", "U-163", "rt-1", None, "th")
        record.assert_called_once()


class AckReplyFailureTests(unittest.TestCase):
    """断言⑥回执失败不影响已落库的裁决(裁决先落,回执后发,互不阻塞)。"""

    def test_reply_failure_does_not_raise(self):
        q = _question(id=40)
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch("services.workorder.api.order_detail", return_value=_order_detail()),
            patch("services.workorder.api.record_decision", return_value={"id": "evt-3"}),
            patch("services.line_binding.line_client_pool_store.transition") as transition,
            patch("services.line_binding.line_client_pool_store.list_for_client", return_value=[q]),
            patch(
                "services.line_binding.line_reply.reply_text_context",
                side_effect=RuntimeError("line api down"),
            ),
        ):
            m._handle_one("t-1", 84, q, "ซื้อ", "U-163", "rt-1", None, "th")  # 不抛异常
        transition.assert_called_once()  # 裁决/状态已落库,不受回执失败影响


class StrictShortFormGateTests(unittest.TestCase):
    """打回修正:自动回写(applied)判定收严,对所有 sender 一致——原全文子串判定会把
    「จ่ายค่าไฟ 500」「ได้รับเงินจากลูกค้า」这类记账句错吞成答题(§4.2 咬人测试)。"""

    def test_dual_identity_purchase_verb_in_expense_sentence_returns_false(self):
        """「จ่ายค่าไฟ 500」含 จ่าย 子串但是记账句 → 双身份不被吞,回落记账路。"""
        with (
            patch.object(
                m,
                "_select_batch",
                return_value={
                    "tenant_id": "t-1",
                    "workspace_client_id": 84,
                    "rows": [_question()],
                    "lang": "th",
                },
            ),
            patch("core.db.get_user_by_line_user_id", return_value={"id": "u-1"}),
            patch.object(m, "_consume") as consume,
        ):
            out = m.handle_answer("U-163", "จ่ายค่าไฟ 500", "rt-1", None)
        self.assertFalse(out)
        consume.assert_not_called()

    def test_dual_identity_sales_verb_in_sentence_returns_false(self):
        """「ได้รับเงินจากลูกค้า」含 รับ 子串但是记账句 → 双身份同样回落。"""
        with (
            patch.object(
                m,
                "_select_batch",
                return_value={
                    "tenant_id": "t-1",
                    "workspace_client_id": 84,
                    "rows": [_question()],
                    "lang": "th",
                },
            ),
            patch("core.db.get_user_by_line_user_id", return_value={"id": "u-1"}),
            patch.object(m, "_consume") as consume,
        ):
            out = m.handle_answer("U-163", "ได้รับเงินจากลูกค้า", "rt-1", None)
        self.assertFalse(out)
        consume.assert_not_called()

    def test_bare_keyword_short_form_is_applied(self):
        """「ซื้อ」整条就是关键词本身(短答形态 b)→ 单条 pending 正确裁决为购。"""
        q = _question(id=50)
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch("services.workorder.api.order_detail", return_value=_order_detail()),
            patch(
                "services.workorder.api.record_decision", return_value={"id": "evt-50"}
            ) as record,
            patch("services.line_binding.line_client_pool_store.transition"),
            patch("services.line_binding.line_client_pool_store.list_for_client", return_value=[q]),
            patch("services.line_binding.line_reply.reply_text_context"),
        ):
            m._consume(
                {"tenant_id": "t-1", "workspace_client_id": 84, "rows": [q], "lang": "th"},
                "ซื้อ",
                "U-163",
                "rt-1",
                None,
            )
        record.assert_called_once()
        self.assertEqual(record.call_args.kwargs["kind"], decisions.PURCHASE_INVOICE)

    def test_keyword_with_polite_tail_short_form_is_applied(self):
        """「ซื้อค่ะ」剥掉礼貌尾缀后恰是关键词本身 → 同样允许自动裁决。"""
        q = _question(id=51)
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch("services.workorder.api.order_detail", return_value=_order_detail()),
            patch(
                "services.workorder.api.record_decision", return_value={"id": "evt-51"}
            ) as record,
            patch("services.line_binding.line_client_pool_store.transition"),
            patch("services.line_binding.line_client_pool_store.list_for_client", return_value=[q]),
            patch("services.line_binding.line_reply.reply_text_context"),
        ):
            m._consume(
                {"tenant_id": "t-1", "workspace_client_id": 84, "rows": [q], "lang": "th"},
                "ซื้อค่ะ",
                "U-163",
                "rt-1",
                None,
            )
        record.assert_called_once()
        self.assertEqual(record.call_args.kwargs["kind"], decisions.PURCHASE_INVOICE)

    def test_numbered_short_segment_is_applied(self):
        """「1 ซื้อ」编号命中+该段含关键词(短答形态 a)→ 仍按老路正确裁决。"""
        q = _question(id=52)
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch("services.workorder.api.order_detail", return_value=_order_detail()),
            patch(
                "services.workorder.api.record_decision", return_value={"id": "evt-52"}
            ) as record,
            patch("services.line_binding.line_client_pool_store.transition"),
            patch("services.line_binding.line_client_pool_store.list_for_client", return_value=[q]),
            patch("services.line_binding.line_reply.reply_text_context"),
        ):
            m._consume(
                {"tenant_id": "t-1", "workspace_client_id": 84, "rows": [q], "lang": "th"},
                "1 ซื้อ",
                "U-163",
                "rt-1",
                None,
            )
        record.assert_called_once()
        self.assertEqual(record.call_args.kwargs["kind"], decisions.PURCHASE_INVOICE)

    def test_pure_customer_long_sentence_with_drop_keyword_goes_to_manual_review(self):
        """纯客户长句含 ไม่ต้อง 不是短答形态 → 不 auto-exclude,落 manual_review 交人审。"""
        q = _question(id=53, question_type=vocab.QUESTION_DROP)
        text = "เดือนนี้ไม่ต้องคิดตัวนี้เพราะจ่ายไปแล้วนะครับ"
        with (
            patch("services.workorder.api.record_decision") as record,
            patch("services.line_binding.line_client_pool_store.transition") as transition,
            patch("services.line_binding.line_reply.reply_text_context"),
        ):
            m._consume(
                {"tenant_id": "t-1", "workspace_client_id": 84, "rows": [q], "lang": "th"},
                text,
                "U-163",
                "rt-1",
                None,
            )
        record.assert_not_called()
        transition.assert_called_once_with(
            "t-1", 53, vocab.MANUAL_REVIEW, answer_raw=text, resolution=None
        )


if __name__ == "__main__":
    unittest.main()
