# -*- coding: utf-8 -*-
"""LINE 待问客户池 · 攒批推送(services/line_binding/line_client_pool_push)· D2-S4 契约。

钉死:①合批消息含编号且三行全 pending 同 batch_id ②超 5 条只推前 5+尾句附剩余数
③push 失败零 pending 残留(先发后置态,失败时压根没置态) ④无 contact 结构化
not_bound 且零副作用 ⑤闸关结构化拒且零副作用(连读都不读) ⑥泰语模板含答法提示。
外加 mark_sent 途中部分失败的原子回滚覆盖(先发后置态设计里唯一会触发"已置 pending
回退 staged"代码路径的场景)。
"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_pool_push as push


def _question(qid, qtype, payload, status=vocab.STAGED):
    return {
        "id": qid,
        "tenant_id": "t-1",
        "workspace_client_id": 84,
        "work_order_id": f"wo-{qid}",
        "item_id": f"item-{qid}",
        "period": "2026-07",
        "question_type": qtype,
        "question_payload": payload,
        "status": status,
        "batch_id": None,
        "answer_raw": None,
        "resolution": None,
        "created_by": "user:1",
        "created_at": None,
        "sent_at": None,
        "answered_at": None,
        "closed_at": None,
        "updated_at": None,
    }


_CONTACT = {
    "tenant_id": "t-1",
    "workspace_client_id": 84,
    "line_user_id": "U163",
    "preferred_lang": "th",
    "display_name": "Sister Makeup",
    "bound_at": None,
    "last_active_at": None,
}


def _mark_sent_recording(calls):
    """side_effect:记录每次调用 (tenant_id, question_id, batch_id, batch_seq),回一条已置 pending 的行。"""

    def _run(tenant_id, question_id, batch_id, batch_seq):
        calls.append((tenant_id, question_id, batch_id, batch_seq))
        return {
            "id": question_id,
            "status": vocab.PENDING,
            "batch_id": str(batch_id),
            "batch_seq": batch_seq,
        }

    return _run


class PushBatchGateTests(unittest.TestCase):
    def test_disabled_flag_rejects_with_zero_side_effects(self):
        """断言⑤:闸关 → 结构化拒,连 STAGED 都不读(零副作用)。"""
        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=False),
            patch("services.line_binding.line_client_pool_store.list_for_client") as list_fn,
            patch("services.line_binding.line_client_contact.get_contact") as get_contact,
            patch("services.line_binding.line_reply.push_text_context") as push_fn,
        ):
            out = push.push_batch_for_client("t-1", 84, actor="user:1")
        self.assertEqual(out, {"ok": False, "reason": "disabled"})
        list_fn.assert_not_called()
        get_contact.assert_not_called()
        push_fn.assert_not_called()

    def test_no_staged_questions_rejected(self):
        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch("services.line_binding.line_client_pool_store.list_for_client", return_value=[]),
        ):
            out = push.push_batch_for_client("t-1", 84, actor="user:1")
        self.assertEqual(out, {"ok": False, "reason": "no_staged"})

    def test_missing_contact_rejected_with_zero_state_change(self):
        """断言④:无 contact → not_bound,mark_sent/push 均未触发,状态零变化。"""
        staged = [_question(1, vocab.QUESTION_DIRECTION, {"supplier": "A", "invno": "INV-1"})]
        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_pool_store.list_for_client",
                return_value=staged,
            ),
            patch("services.line_binding.line_client_contact.get_contact", return_value=None),
            patch("services.line_binding.line_reply.push_text_context") as push_fn,
            patch("services.line_binding.line_client_pool_store.mark_sent") as mark_fn,
        ):
            out = push.push_batch_for_client("t-1", 84, actor="user:1")
        self.assertEqual(out, {"ok": False, "reason": "not_bound"})
        push_fn.assert_not_called()
        mark_fn.assert_not_called()


class PushBatchSuccessTests(unittest.TestCase):
    def test_three_staged_batch_into_one_message_all_pending_same_batch_id(self):
        """断言①:3 条 STAGED 合成一条消息含编号 1-3,三行全 pending 且同 batch_id。
        断言⑥:泰语模板含答法提示。"""
        staged = [
            _question(1, vocab.QUESTION_DIRECTION, {"supplier": "ร้าน A", "invno": "INV-001"}),
            _question(2, vocab.QUESTION_AMOUNT, {"amount": Decimal("1234.50")}),
            _question(3, vocab.QUESTION_DROP, {"supplier": "ร้าน C"}),
        ]
        mark_calls = []
        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_pool_store.list_for_client",
                return_value=staged,
            ),
            patch("services.line_binding.line_client_contact.get_contact", return_value=_CONTACT),
            patch(
                "services.line_binding.line_reply.push_text_context", return_value=True
            ) as push_fn,
            patch(
                "services.line_binding.line_client_pool_store.mark_sent",
                side_effect=_mark_sent_recording(mark_calls),
            ),
        ):
            out = push.push_batch_for_client("t-1", 84, actor="user:1")

        self.assertTrue(out["ok"])
        self.assertEqual(out["sent_count"], 3)
        self.assertEqual(out["remaining_count"], 0)
        self.assertEqual(set(out["question_ids"]), {1, 2, 3})

        sent_text = push_fn.call_args.args[1]
        self.assertIn("1)", sent_text)
        self.assertIn("2)", sent_text)
        self.assertIn("3)", sent_text)
        self.assertIn("ตอบกลับตามหมายเลข", sent_text)  # 断言⑥答法提示

        self.assertEqual(len(mark_calls), 3)
        batch_ids = {call[2] for call in mark_calls}
        self.assertEqual(len(batch_ids), 1)  # 同一 batch_id
        self.assertEqual(out["batch_id"], str(next(iter(batch_ids))))

    def test_seven_staged_only_first_five_sent_remainder_stays_staged(self):
        """断言②:>5 条只推前 5,尾句含剩余数「2」,另 2 条留 staged(不触碰)。"""
        staged = [_question(i, vocab.QUESTION_FREEFORM, {"note": f"note-{i}"}) for i in range(1, 8)]
        mark_calls = []
        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_pool_store.list_for_client",
                return_value=staged,
            ),
            patch("services.line_binding.line_client_contact.get_contact", return_value=_CONTACT),
            patch(
                "services.line_binding.line_reply.push_text_context", return_value=True
            ) as push_fn,
            patch(
                "services.line_binding.line_client_pool_store.mark_sent",
                side_effect=_mark_sent_recording(mark_calls),
            ),
        ):
            out = push.push_batch_for_client("t-1", 84, actor="user:1")

        self.assertTrue(out["ok"])
        self.assertEqual(out["sent_count"], 5)
        self.assertEqual(out["remaining_count"], 2)
        self.assertEqual(set(out["question_ids"]), {1, 2, 3, 4, 5})  # 只动前 5 条(oldest first)

        sent_text = push_fn.call_args.args[1]
        self.assertIn("2", sent_text)  # 尾句「还有 2 条」
        self.assertEqual(len(mark_calls), 5)  # 6/7 号从未被 mark_sent 触碰,原样留 staged
        self.assertEqual(
            [c[3] for c in mark_calls], [1, 2, 3, 4, 5]
        )  # batch_seq 与消息编号同序落列


class PushBatchFailureTests(unittest.TestCase):
    def test_push_failure_leaves_all_staged_no_pending_residue(self):
        """断言③:push 返回 False → 结构化 push_failed;先发后置态设计下,
        mark_sent 压根没机会跑,自然「全部回退 staged 无 pending 残留」。"""
        staged = [
            _question(1, vocab.QUESTION_DIRECTION, {"supplier": "A", "invno": "INV-1"}),
            _question(2, vocab.QUESTION_AMOUNT, {"amount": Decimal("50.00")}),
        ]
        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_pool_store.list_for_client",
                return_value=staged,
            ),
            patch("services.line_binding.line_client_contact.get_contact", return_value=_CONTACT),
            patch("services.line_binding.line_reply.push_text_context", return_value=False),
            patch("services.line_binding.line_client_pool_store.mark_sent") as mark_fn,
            patch("services.line_binding.line_client_pool_store.transition") as transition_fn,
        ):
            out = push.push_batch_for_client("t-1", 84, actor="user:1")

        self.assertEqual(out, {"ok": False, "reason": "push_failed"})
        mark_fn.assert_not_called()
        transition_fn.assert_not_called()

    def test_push_raises_is_treated_as_failure(self):
        staged = [_question(1, vocab.QUESTION_DROP, {"supplier": "A"})]
        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_pool_store.list_for_client",
                return_value=staged,
            ),
            patch("services.line_binding.line_client_contact.get_contact", return_value=_CONTACT),
            patch(
                "services.line_binding.line_reply.push_text_context",
                side_effect=RuntimeError("LINE API down"),
            ),
            patch("services.line_binding.line_client_pool_store.mark_sent") as mark_fn,
        ):
            out = push.push_batch_for_client("t-1", 84, actor="user:1")
        self.assertEqual(out, {"ok": False, "reason": "push_failed"})
        mark_fn.assert_not_called()

    def test_partial_mark_sent_failure_rolls_back_marked_rows_to_staged(self):
        """push 已成功送达客户后,逐行落定途中数据库抖动:第 3 行 mark_sent 抛,
        已落定的前 2 行原路 transition 回 staged——批状态保持原子,不留半吊子。"""
        staged = [
            _question(1, vocab.QUESTION_DIRECTION, {"supplier": "A", "invno": "INV-1"}),
            _question(2, vocab.QUESTION_DIRECTION, {"supplier": "B", "invno": "INV-2"}),
            _question(3, vocab.QUESTION_DIRECTION, {"supplier": "C", "invno": "INV-3"}),
        ]

        def _mark_sent_third_fails(tenant_id, question_id, batch_id, batch_seq):
            if question_id == 3:
                raise RuntimeError("db hiccup")
            return {"id": question_id, "status": vocab.PENDING, "batch_id": str(batch_id)}

        with (
            patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_client_pool_store.list_for_client",
                return_value=staged,
            ),
            patch("services.line_binding.line_client_contact.get_contact", return_value=_CONTACT),
            patch("services.line_binding.line_reply.push_text_context", return_value=True),
            patch(
                "services.line_binding.line_client_pool_store.mark_sent",
                side_effect=_mark_sent_third_fails,
            ),
            patch("services.line_binding.line_client_pool_store.transition") as transition_fn,
        ):
            out = push.push_batch_for_client("t-1", 84, actor="user:1")

        self.assertEqual(out, {"ok": False, "reason": "state_update_failed"})
        rolled_back_ids = {call.args[1] for call in transition_fn.call_args_list}
        self.assertEqual(rolled_back_ids, {1, 2})  # 只回滚已落定的前两行,第 3 行本就没落定
        for call in transition_fn.call_args_list:
            self.assertEqual(call.args[2], vocab.STAGED)


if __name__ == "__main__":
    unittest.main()
