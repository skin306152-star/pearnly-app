# -*- coding: utf-8 -*-
"""
Lock down the v118.35.0.3 fix:
- pydantic ValidationError must NEVER reach the user as a multi-line block with
  pydantic.dev documentation URLs.
- short_error() must return a single line ≤ 160 chars regardless of input.

If this breaks, the bug where the bank-recon / GL-VAT upload pipeline spat a
3-screen red toast at the user can come back.
"""

import unittest


class ShortErrorTests(unittest.TestCase):
    def test_pydantic_validation_collapses_to_one_line(self):
        from pydantic import BaseModel, ValidationError
        from services.ocr.error_format import short_error

        class M(BaseModel):
            bank_code: str
            account_name: str
            account_number: str
            opening_balance: str
            closing_balance: str
            period_start: str
            period_end: str

        try:
            M(
                bank_code=None,
                account_name=None,
                account_number=None,
                opening_balance=None,
                closing_balance=None,
                period_start=None,
                period_end=None,
            )
            self.fail("expected ValidationError")
        except ValidationError as e:
            out = short_error(e)

        self.assertNotIn("\n", out)
        self.assertNotIn("pydantic.dev", out)
        self.assertNotIn("https://", out)
        self.assertLessEqual(len(out), 160)
        # Should still tell the user *something* (count) so we don't return
        # an empty/cryptic string.
        self.assertTrue(any(ch.isdigit() for ch in out),
                        f"expected a field count in: {out!r}")

    def test_value_error_with_long_message_truncates(self):
        from services.ocr.error_format import short_error
        long_msg = "layer2: page 1: layer2 " + ("x" * 400)
        out = short_error(ValueError(long_msg))
        self.assertNotIn("\n", out)
        self.assertLessEqual(len(out), 160)

    def test_strips_pydantic_doc_urls_from_wrapped_text(self):
        from services.ocr.error_format import short_error
        wrapped = ValueError(
            "field_x: bad value "
            "https://errors.pydantic.dev/2.13/v/string_type extra trailing"
        )
        out = short_error(wrapped)
        self.assertNotIn("pydantic.dev", out)
        self.assertNotIn("https://", out)

    def test_handles_empty_exception(self):
        from services.ocr.error_format import short_error
        out = short_error(RuntimeError(""))
        self.assertTrue(out)  # falls back to class name


if __name__ == "__main__":
    unittest.main()
