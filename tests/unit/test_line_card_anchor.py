# -*- coding: utf-8 -*-
"""可引用卡片契约(06):凡"代表真单据"的卡发出时都登记 message_id→doc 锚点(+ 焦点)。

真机 bug:图片 OCR / push 发出的卡没登记 → 引用即 ANCHOR_EXPIRED。本测试钉死:push 路重发卡、
终态卡、posted 卡、reply 路都登记锚点;终态卡只登记不设焦点(引用它仍可「恢复」)。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.expense import line_correct
from services.line_binding import line_booker, line_client, line_message_refs


class AnchorCardHelperTests(unittest.TestCase):
    """line_booker.anchor_card:登记锚点(有 cur→record / 无 cur→record_safe)+ 按状态设焦点。"""

    def _patches(self):
        return (
            mock.patch.object(line_message_refs, "record"),
            mock.patch.object(line_message_refs, "record_safe"),
            mock.patch.object(line_correct, "_set_active"),
        )

    def test_with_cur_records_and_focuses(self):
        rec, rec_safe, set_active = self._patches()
        with rec as m_rec, rec_safe as m_safe, set_active as m_act:
            line_booker.anchor_card(
                [{"id": "M1"}, {"id": "M2"}],
                tenant_id="T",
                ws=1,
                line_user_id="U",
                doc_id="D9",
                state="confirm",
                cur=object(),
            )
        self.assertTrue(m_rec.called)  # 有 cur → 用 record(不另开连接)
        self.assertFalse(m_safe.called)
        self.assertEqual(m_rec.call_args.kwargs["message_ids"], ["M1", "M2"])
        self.assertEqual(m_rec.call_args.kwargs["ref_id"], "D9")
        self.assertTrue(m_act.called)  # 草稿卡设焦点

    def test_no_cur_uses_record_safe(self):
        rec, rec_safe, set_active = self._patches()
        with rec as m_rec, rec_safe as m_safe, set_active:
            line_booker.anchor_card(
                [{"id": "M1"}], tenant_id="T", ws=1, line_user_id="U", doc_id="D9", state="posted"
            )
        self.assertTrue(m_safe.called)  # 无 cur → record_safe 自开事务
        self.assertFalse(m_rec.called)

    def test_terminal_records_anchor_but_no_focus(self):
        # ★终态卡(voided/discarded):登记锚点(引用它仍可「恢复」)但不动焦点。
        rec, rec_safe, set_active = self._patches()
        with rec, rec_safe as m_safe, set_active as m_act:
            line_booker.anchor_card(
                [{"id": "M1"}], tenant_id="T", ws=1, line_user_id="U", doc_id="D9", state="voided"
            )
        self.assertTrue(m_safe.called)  # 锚点登记了
        self.assertFalse(m_act.called)  # 焦点不动

    def test_empty_sent_best_effort(self):
        # push 拿不到消息 id → 锚点本次缺(best-effort 不阻塞),焦点仍设(卡照常显示)。
        rec, rec_safe, set_active = self._patches()
        with rec as m_rec, rec_safe as m_safe, set_active as m_act:
            line_booker.anchor_card(
                [],
                tenant_id="T",
                ws=1,
                line_user_id="U",
                doc_id="D9",
                state="confirm",
                cur=object(),
            )
        self.assertFalse(m_rec.called)
        self.assertFalse(m_safe.called)
        self.assertTrue(m_act.called)

    def test_state_from_status(self):
        self.assertEqual(line_booker.state_from_status("draft"), "confirm")
        self.assertEqual(line_booker.state_from_status("posted"), "posted")
        self.assertEqual(line_booker.state_from_status("void"), "voided")
        self.assertEqual(line_booker.state_from_status("discarded"), "discarded")


class EmitSiteRegistersTests(unittest.TestCase):
    """审计:所有发 doc 卡的地方都登记锚点(push 重发卡 / 终态卡 / posted 卡 / reply 路)。"""

    def test_fastpath_reshow_registers_anchor(self):
        # ★真机 bug 回归:重复图快路重发当前状态卡 → 必须登记锚点(否则引用 ANCHOR_EXPIRED)。
        from services.ocr import line_image_fastpath as fp

        detail = {"doc": {"status": "draft", "grand_total": "75.00"}}
        with (
            mock.patch.object(fp, "_mint", return_value="tok"),
            mock.patch(
                "services.line_binding.line_posted_card.build_state_card",
                return_value={"type": "flex", "altText": "card"},
            ),
            mock.patch.object(line_client, "push_messages_with_meta", return_value=[{"id": "PM1"}]),
            mock.patch.object(line_message_refs, "record") as m_rec,
            mock.patch.object(line_correct, "_set_active"),
        ):
            fp._push_state_card(
                object(), "U", "th", detail, doc_id="D1", ws=1, tid="T", created_by="u"
            )
        self.assertTrue(m_rec.called)
        self.assertEqual(m_rec.call_args.kwargs["ref_id"], "D1")
        self.assertEqual(m_rec.call_args.kwargs["message_ids"], ["PM1"])

    def test_terminal_card_registers_anchor(self):
        # 终态卡发出 → 登记锚点(record_safe·无 cur),让"已撤销卡"可被引用说「恢复」。
        from services.line_binding import line_card_actions

        with (
            mock.patch(
                "services.line_binding.line_card.terminal_card",
                return_value={"type": "flex", "altText": "voided"},
            ),
            mock.patch.object(
                line_client, "reply_messages_with_meta", return_value=[{"id": "TM1"}]
            ),
            mock.patch.object(line_message_refs, "record_safe") as m_safe,
        ):
            line_card_actions.send_terminal(
                "rt",
                state="voided",
                doc_id="DV",
                ws=1,
                amount="75.00",
                lang="th",
                tid="T",
                luid="U",
            )
        self.assertTrue(m_safe.called)
        self.assertEqual(m_safe.call_args.kwargs["ref_id"], "DV")

    def test_send_posted_registers_and_focuses(self):
        from services.line_binding import line_card_actions

        with (
            mock.patch(
                "services.line_binding.line_posted_card.build",
                return_value={"type": "flex", "altText": "posted"},
            ),
            mock.patch.object(
                line_client, "reply_messages_with_meta", return_value=[{"id": "PM1"}]
            ),
            mock.patch.object(line_message_refs, "record") as m_rec,
            mock.patch.object(line_correct, "_set_active") as m_act,
        ):
            line_card_actions._send_posted(
                object(), "rt", {"doc": {}}, ref="DP", ws=1, lang="th", tid="T", luid="U"
            )
        self.assertTrue(m_rec.called and m_act.called)
        self.assertEqual(m_rec.call_args.kwargs["ref_id"], "DP")

    def test_emit_result_card_reply_still_registers(self):
        # reply 路不回归:emit_result_card 仍登记锚点(_bind_refs → record_safe)。
        with (
            mock.patch(
                "services.line_binding.line_card.result_card",
                return_value={"type": "flex", "altText": "card"},
            ),
            mock.patch.object(
                line_client, "reply_messages_with_meta", return_value=[{"id": "RM1"}]
            ),
            mock.patch.object(line_message_refs, "record_safe") as m_safe,
            mock.patch.object(line_correct, "_set_active"),
        ):
            line_booker.emit_result_card(
                "rt",
                state="confirm",
                amount="75.00",
                fields={},
                doc_id="DR",
                lang="th",
                tenant_id="T",
                workspace_client_id=1,
                line_user_id="U",
            )
        self.assertTrue(m_safe.called)
        self.assertEqual(m_safe.call_args.kwargs["ref_id"], "DR")


if __name__ == "__main__":
    unittest.main()
