# -*- coding: utf-8 -*-
"""LINE 本月凭证命令(C-1):命令/期间识别 + 0 笔不生成回提示 + 有笔 ack+异步。"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from services.line_binding import line_proof


class _Ctx:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class ParseCommandTests(unittest.TestCase):
    T = date(2026, 6, 15)

    def test_this_month_variants(self):
        for txt in ("ขอ PDF เดือนนี้", "本月凭证", "导出凭证", "proof pdf", "รวมใบเสร็จเดือนนี้"):
            c = line_proof.parse_proof_command(txt, today=self.T)
            self.assertIsNotNone(c, txt)
            self.assertEqual(
                (c["date_from"], c["date_to"], c["period"]),
                ("2026-06-01", "2026-06-30", "2026-06"),
                txt,
            )

    def test_last_month(self):
        for txt in ("ขอ pdf เดือนที่แล้ว", "导出凭证 上月", "凭证打包上个月"):
            c = line_proof.parse_proof_command(txt, today=self.T)
            self.assertEqual(
                (c["date_from"], c["date_to"], c["period"]),
                ("2026-05-01", "2026-05-31", "2026-05"),
                txt,
            )

    def test_non_command_not_triggered(self):
        for txt in ("咖啡 65", "本月花了多少", "tops 水 20", "ขอบคุณ"):
            self.assertIsNone(line_proof.parse_proof_command(txt, today=self.T), txt)

    def test_month_range_year_boundary(self):
        c = line_proof.parse_proof_command("导出凭证 上月", today=date(2026, 1, 10))
        self.assertEqual(
            (c["date_from"], c["date_to"], c["period"]), ("2025-12-01", "2025-12-31", "2025-12")
        )


class StartTests(unittest.TestCase):
    CMD = {"date_from": "2026-06-01", "date_to": "2026-06-30", "period": "2026-06"}

    def _run(self, doc_ids):
        replies = []
        with (
            mock.patch.object(line_proof.db, "get_cursor_rls", return_value=_Ctx()),
            mock.patch.object(line_proof, "default_workspace_id", return_value=1),
            mock.patch.object(line_proof.archive, "_posted_doc_ids", return_value=doc_ids),
            mock.patch.object(
                line_proof.line_reply,
                "reply_text_context",
                side_effect=lambda tok, body, **k: replies.append(body),
            ),
            mock.patch.object(line_proof, "_run_and_push", new=lambda *a, **k: "coro"),
            mock.patch.object(line_proof.asyncio, "create_task") as ct,
        ):
            out = line_proof.start({"tenant_id": "t"}, "rt", "u1", "th", self.CMD)
        return out, replies, ct

    def test_zero_docs_replies_no_task(self):
        out, replies, ct = self._run([])
        self.assertTrue(out)
        self.assertEqual(replies, [line_proof._m("empty", "th")])  # 回提示
        ct.assert_not_called()  # ★不生成

    def test_has_docs_ack_and_task(self):
        out, replies, ct = self._run(["D1", "D2"])
        self.assertTrue(out)
        self.assertEqual(replies, [line_proof._m("ack", "th")])  # 生成中
        ct.assert_called_once()  # 异步打包


class DownloadCardTests(unittest.TestCase):
    def test_card_has_hero_and_uri_button(self):
        card = line_proof._download_card(
            {
                "url": "https://pearnly.com/api/purchase/proof-pdf/TOK",
                "n": 5,
                "total": 1200,
                "period": "2026-06",
            },
            "th",
        )
        bubble = card["contents"]
        self.assertIn("B-banner-proof", bubble["hero"]["url"])  # B5 横幅皮肤
        btn = bubble["footer"]["contents"][0]["action"]
        self.assertEqual(btn["type"], "uri")
        self.assertEqual(btn["uri"], "https://pearnly.com/api/purchase/proof-pdf/TOK")
        self.assertIn("2026-06", card["altText"])


if __name__ == "__main__":
    unittest.main()
