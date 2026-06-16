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


if __name__ == "__main__":
    unittest.main()
