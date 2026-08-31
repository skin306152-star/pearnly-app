import unittest
from unittest import mock

from services.line_erp import intake


class ErpIntakePdfTests(unittest.TestCase):
    @mock.patch("services.ocr_history.mutations.update_ocr_history_pdf_storage", return_value=1)
    @mock.patch("services.ocr.pdf_backfill.generate_and_save_pdf", return_value=("u/p.pdf", 12))
    def test_saves_and_backfills_without_ocr_or_billing(self, save, update):
        result = intake.generate_and_save_pdf(b"%PDF", [{"fields": {}}], ["h1"], "u1", "t1")
        self.assertEqual(result["updated"], 1)
        update.assert_called_once_with(["h1"], "u/p.pdf", 12, "u1", tenant_id="t1")

    @mock.patch("services.ocr_history.mutations.update_ocr_history_pdf_storage", return_value=1)
    @mock.patch("services.ocr.pdf_backfill.generate_and_save_pdf", return_value=("u/p.pdf", 12))
    @mock.patch("services.line_platform.client.image_to_pdf_bytes", return_value=b"%PDF-image")
    def test_wraps_line_image_as_pdf_before_backfill(self, convert, save, _update):
        result = intake.generate_and_save_pdf(b"jpeg", [], ["h1"], "u1", "t1")
        self.assertTrue(result["saved"])
        convert.assert_called_once_with(b"jpeg")
        self.assertEqual(save.call_args.args[0], b"%PDF-image")

    @mock.patch("services.ocr.pdf_backfill.generate_and_save_pdf", return_value=(None, None))
    def test_save_failure_keeps_draft_path(self, save):
        self.assertEqual(intake.generate_and_save_pdf(b"%PDF", [], ["h1"], "u1")["saved"], False)


if __name__ == "__main__":
    unittest.main()
