# -*- coding: utf-8 -*-
"""LINE 入账编排共享口(/simplify #10)守门测试。

锁定:ack_key 状态映射;book_and_mint 把参数原样转发 book_by_confidence + nonce.mint 并
返回 (doc_id, state, token)——证明三路抽取是行为等价(归类/总额/过账逻辑全在下游不变)。"""

import unittest
from unittest import mock

from services.line_binding import line_booker


class AckKeyTests(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual(line_booker.ack_key("posted"), "exp_ack_posted")
        self.assertEqual(line_booker.ack_key("dup"), "exp_ack_dup")
        self.assertEqual(line_booker.ack_key("confirm"), "exp_ack_confirm")
        self.assertEqual(line_booker.ack_key("whatever"), "exp_ack_confirm")


class BookAndMintTests(unittest.TestCase):
    def test_forwards_and_chains(self):
        with (
            mock.patch(
                "services.purchase.confidence_post.book_by_confidence",
                return_value=("doc7", "posted"),
            ) as bbc,
            mock.patch("services.line_binding.line_action_nonce.mint", return_value="tok9") as mnt,
        ):
            out = line_booker.book_and_mint(
                "CUR",
                tenant_id="t",
                workspace_client_id=9,
                data={"x": 1},
                settings={"auto_book": True},
                verdict="V",
                created_by="u",
            )
        self.assertEqual(out, ("doc7", "posted", "tok9"))
        bk = bbc.call_args.kwargs
        self.assertEqual(
            (bk["tenant_id"], bk["workspace_client_id"], bk["created_by"]), ("t", 9, "u")
        )
        self.assertEqual(bk["data"], {"x": 1})
        mk = mnt.call_args.kwargs
        self.assertEqual((mk["action_ref"], mk["user_id"]), ("doc7", "u"))

    def test_dup_invoice_points_to_existing_doc(self):
        from core.pos_api import PosError

        with (
            mock.patch(
                "services.purchase.confidence_post.book_by_confidence",
                side_effect=PosError("purchase.dup_invoice", 409),
            ),
            mock.patch(
                "services.line_binding.line_booker._find_dup_doc", return_value={"id": "existing9"}
            ),
            mock.patch("services.line_binding.line_action_nonce.mint", return_value="tok"),
        ):
            doc_id, state, token = line_booker.book_and_mint(
                "CUR",
                tenant_id="t",
                workspace_client_id=9,
                data={},
                settings={"dedupe_block": True},
                verdict="V",
                created_by="u",
            )
        # 重复票 → 指向已有单 + dup 态(出「可能重复」卡,不再回落纯文字/静默丢)
        self.assertEqual((doc_id, state, token), ("existing9", "dup", "tok"))

    def test_dup_without_existing_still_dup_no_mint(self):
        from core.pos_api import PosError

        with (
            mock.patch(
                "services.purchase.confidence_post.book_by_confidence",
                side_effect=PosError("purchase.dup_invoice", 409),
            ),
            mock.patch("services.line_binding.line_booker._find_dup_doc", return_value=None),
            mock.patch("services.line_binding.line_action_nonce.mint", return_value="tok") as mnt,
        ):
            out = line_booker.book_and_mint(
                "CUR",
                tenant_id="t",
                workspace_client_id=9,
                data={},
                settings={"dedupe_block": True},
                verdict="V",
                created_by="u",
            )
        self.assertEqual(out, ("", "dup", ""))
        mnt.assert_not_called()  # 无 doc 不铸 token

    def test_non_dup_poserror_propagates(self):
        from core.pos_api import PosError

        with mock.patch(
            "services.purchase.confidence_post.book_by_confidence",
            side_effect=PosError("purchase.amount_mismatch", 422),
        ):
            with self.assertRaises(PosError):
                line_booker.book_and_mint(
                    "CUR",
                    tenant_id="t",
                    workspace_client_id=9,
                    data={},
                    settings={},
                    verdict="V",
                    created_by="u",
                )


class ToPurchaseDataTests(unittest.TestCase):
    """单/多项路共用建单组装:expense 默认已付(等于多项路原硬编码 'paid')+ 字段直传。"""

    def test_expense_defaults_paid_and_shape(self):
        data = line_booker.to_purchase_data(
            lines=[{"description": "x"}],
            doc_date="2026-06-17",
            supplier={"name": "v"},
            category_id="p1",
        )
        self.assertEqual((data["doc_kind"], data["source"]), ("expense", "line"))
        self.assertEqual(data["payment_status"], "paid")  # 空单据类型费用 → 已付
        self.assertEqual(data["currency"], "THB")
        self.assertIsNone(data["doc_no"])
        self.assertEqual(data["lines"], [{"description": "x"}])

    def test_passthrough_doc_no_and_currency(self):
        data = line_booker.to_purchase_data(
            lines=[], doc_date=None, supplier={}, doc_no="INV1", currency="USD"
        )
        self.assertEqual((data["doc_no"], data["currency"]), ("INV1", "USD"))


class EmitResultCardTests(unittest.TestCase):
    """三路共用发卡口:引用回执(posted/dup/confirm 文案 key)+ Flex 卡 → 两条消息。"""

    def test_builds_ack_and_card_two_messages(self):
        with (
            mock.patch("services.line_binding.line_client.t_line", return_value="ACK") as tl,
            mock.patch(
                "services.line_binding.line_card.result_card", return_value={"type": "flex"}
            ) as rc,
            mock.patch(
                "services.line_binding.line_client.reply_messages_with_meta", return_value=[]
            ) as rm,
        ):
            line_booker.emit_result_card(
                "RT",
                state="posted",
                amount="120",
                fields={"a": 1},
                doc_id="d1",
                lang="zh",
                quote_token="q",
                workspace_name="WS",
                token="tok",
                workspace_client_id="9",
            )
        self.assertEqual(tl.call_args.args[1], "exp_ack_posted")
        self.assertEqual(rc.call_args.kwargs["state"], "posted")
        self.assertEqual(rc.call_args.kwargs["amount"], "120")
        msgs = rm.call_args.args[1]
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["quoteToken"], "q")
        self.assertEqual(msgs[1], {"type": "flex"})

    def test_no_quote_token_omits_quote(self):
        with (
            mock.patch("services.line_binding.line_client.t_line", return_value="ACK"),
            mock.patch("services.line_binding.line_card.result_card", return_value={}),
            mock.patch(
                "services.line_binding.line_client.reply_messages_with_meta", return_value=[]
            ) as rm,
        ):
            line_booker.emit_result_card(
                "RT", state="confirm", amount="1", fields={}, doc_id="", lang="zh"
            )
        self.assertNotIn("quoteToken", rm.call_args.args[1][0])


class BindRefsTests(unittest.TestCase):
    """发完把消息 id 绑到 doc(引用底座):有 tenant+doc+消息才记;缺一不记。"""

    def test_records_when_complete(self):
        from services.line_binding import line_message_refs

        with mock.patch.object(line_message_refs, "record_safe") as rec:
            line_booker._bind_refs("t", 9, "U1", [{"id": "m1"}, {"id": "m2"}], "doc1", "posted")
        self.assertEqual(rec.call_args.kwargs["message_ids"], ["m1", "m2"])
        self.assertEqual(rec.call_args.kwargs["ref_id"], "doc1")

    def test_skips_without_tenant_or_doc(self):
        from services.line_binding import line_message_refs

        with mock.patch.object(line_message_refs, "record_safe") as rec:
            line_booker._bind_refs(None, 9, "U1", [{"id": "m1"}], "doc1", "posted")
            line_booker._bind_refs("t", 9, "U1", [{"id": "m1"}], "", "posted")
            line_booker._bind_refs("t", 9, "U1", [], "doc1", "posted")
        rec.assert_not_called()


class AckMessageTests(unittest.TestCase):
    """P2B:草稿态金额读不出/不可靠 → 引用回执不显 ✅、不说「已保存草稿」,改警示口径。"""

    def test_confirm_reliable_keeps_green_draft(self):
        m = line_booker.ack_message("th", "confirm", "58.00", {})
        self.assertIn("✅", m)
        self.assertIn("บันทึกฉบับร่างแล้ว", m)

    def test_confirm_zero_amount_no_success(self):
        m = line_booker.ack_message("th", "confirm", "0.00", {})
        self.assertNotIn("✅", m)
        self.assertNotIn("บันทึกฉบับร่างแล้ว", m)
        self.assertIn("ยังอ่านยอดเงินไม่ได้", m)
        self.assertNotIn("0.00", m)  # 0 金额不外显

    def test_confirm_unreliable_amount_review(self):
        m = line_booker.ack_message("th", "confirm", "2235.23", {"amount_unreliable": True})
        self.assertNotIn("✅", m)
        self.assertNotIn("บันทึกฉบับร่างแล้ว", m)
        self.assertIn("2235.23", m)
        self.assertIn("ตรวจสอบ", m)

    def test_dash_amount_treated_as_unread(self):
        m = line_booker.ack_message("th", "confirm", "—", {})
        self.assertIn("ยังอ่านยอดเงินไม่ได้", m)

    def test_posted_and_dup_unchanged(self):
        self.assertIn("✅", line_booker.ack_message("th", "posted", "58.00", {}))
        self.assertIn("⚠️", line_booker.ack_message("th", "dup", "58.00", {}))


if __name__ == "__main__":
    unittest.main()
