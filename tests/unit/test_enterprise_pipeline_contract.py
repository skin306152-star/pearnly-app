import base64
import unittest
from unittest.mock import patch

from services.ocr.enterprise_adapter import make_page
from services.ocr.enterprise_local.result import Reconstruction
from services.ocr.enterprise_pipeline import run
from services.ocr.enterprise_reader import ReadResult
from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
from services.ocr.schemas import PipelineResult

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jH0kAAAAASUVORK5CYII="
)


class EnterprisePipelineContractTest(unittest.TestCase):
    def test_adapter_preserves_repair_audit_and_review(self):
        p = make_page(
            {"entries": [{"debit": "12", "direction": "debit"}]},
            "gl",
            1,
            audit=[{"row": 1, "field": "debit", "review_required": True}],
            local=True,
        )
        self.assertEqual("deposit", p.document.entries[0].direction)
        self.assertTrue(p.needs_manual_review)
        result = PipelineResult(pages=[p], page_count=1, elapsed_ms=1)
        legacy = pipeline_result_to_legacy_dict(result)
        self.assertTrue(legacy["pages"][0]["_needs_manual_review"])
        self.assertEqual("debit", legacy["pages"][0]["_extraction_audit"]["repairs"][0]["field"])

    @patch("services.ocr.enterprise_pipeline.enterprise_schema.extract")
    @patch("services.ocr.enterprise_pipeline.reconstruct")
    @patch("services.ocr.enterprise_pipeline.enterprise_reader.read")
    def test_local_success_does_not_call_gemini(self, read, reconstruct, extract):
        read.return_value = ReadResult({}, 1, 2, 3, 0.0525)
        reconstruct.return_value = Reconstruction(
            {
                "opening_balance": "0",
                "closing_balance": "10",
                "entries": [
                    {
                        "page": "1",
                        "deposit": "10",
                        "balance": "10",
                        "transaction_date": "2026-01-01",
                    }
                ],
            },
            [],
            [],
            [],
            1,
        )
        result = run([PNG], "bank")
        extract.assert_not_called()
        self.assertEqual(1, result.page_count)
        self.assertEqual(0.0525, result.estimated_cost_thb)
        self.assertEqual(["enterprise", "local_schema"], result.pages[0].layer_chain)

    @patch("services.ocr.enterprise_pipeline.enterprise_schema.extract")
    @patch(
        "services.ocr.enterprise_pipeline.enterprise_reader.read",
        side_effect=RuntimeError("provider"),
    )
    def test_provider_error_does_not_silently_enter_legacy_pipeline(self, read, extract):
        with self.assertRaisesRegex(RuntimeError, "provider"):
            run([PNG], "bank")
        extract.assert_not_called()


if __name__ == "__main__":
    unittest.main()
