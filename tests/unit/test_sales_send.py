# -*- coding: utf-8 -*-
"""销项 PO-7 · 发送(SMTP 带附件 / 投递日志 / 邮件正文)守门 · 不连库不发真信。"""

import os
import unittest

from routes.sales_send_routes import _email_content
from services.sales import send


class CaptureCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


class SendTests(unittest.TestCase):
    def setUp(self):
        for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
            os.environ.pop(k, None)

    def test_smtp_not_configured(self):
        ok, err = send.send_email_with_pdf(
            to_email="a@b.com",
            subject="s",
            html_body="<p>h</p>",
            pdf_bytes=b"%PDF-1",
            pdf_name="inv",
            from_name="ACME",
        )
        self.assertFalse(ok)
        self.assertEqual(err, "smtp_not_configured")

    def test_recipient_required_when_configured(self):
        os.environ["SMTP_HOST"] = "smtp.test"
        os.environ["SMTP_USER"] = "u@test"
        os.environ["SMTP_PASSWORD"] = "pw"
        try:
            ok, err = send.send_email_with_pdf(
                to_email="",
                subject="s",
                html_body="<p>h</p>",
                pdf_bytes=b"%PDF-1",
                pdf_name="inv",
                from_name="ACME",
            )
        finally:
            for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
                os.environ.pop(k, None)
        self.assertFalse(ok)
        self.assertEqual(err, "recipient_required")

    def test_smtp_configured_helper(self):
        self.assertFalse(send.smtp_configured())

    def test_record_send_inserts_log(self):
        cur = CaptureCursor()
        send.record_send(
            cur,
            tenant_id="t",
            doc_id="d",
            channel="email",
            identity="official",
            recipient="a@b.com",
            status="sent",
            error=None,
            created_by="u",
        )
        sql, params = cur.calls[0]
        self.assertIn("INSERT INTO sales_document_sends", sql)
        self.assertIn("a@b.com", params)
        self.assertIn("sent", params)

    def test_email_content_has_seller_number_message(self):
        subject, html = _email_content(
            {"doc_type": "tax_invoice", "doc_number": "INV2026-00001"}, {"name": "ACME"}, "thanks"
        )
        self.assertIn("INV2026-00001", subject)
        self.assertIn("ACME", subject)
        self.assertIn("thanks", html)
        self.assertIn("ACME", html)

    def test_email_content_no_message(self):
        subject, html = _email_content(
            {"doc_type": "receipt", "doc_number": "RCP-1"}, {"name": "S"}, None
        )
        self.assertIn("RCP-1", subject)
        self.assertNotIn("white-space:pre-wrap", html)


if __name__ == "__main__":
    unittest.main()
