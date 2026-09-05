"""Request parity and page boundaries must survive production integration."""

import unittest
from unittest.mock import Mock, patch

from services.ai_gateway.providers import enterprise
from services.ocr.enterprise_request import build_request, contract_hash
from services.ocr.layer1_base import Layer1AuthError, Layer1Error, Layer1QuotaError


class EnterpriseRequestTests(unittest.TestCase):
    def test_pinned_generation_parameters(self):
        request = build_request("bank", "printed text")
        self.assertEqual(request["location"], "global")
        self.assertEqual(request["model"], "gemini-3.8-flash")
        self.assertEqual(request["config"]["thinking_config"], {"thinking_level": "LOW"})
        self.assertEqual(request["config"]["max_output_tokens"], 16384)
        self.assertTrue(request["prompt"].endswith("---\nprinted text\n---"))
        self.assertIn("entries", request["config"]["response_json_schema"]["required"])

    def test_schema_mutation_does_not_change_next_request(self):
        before = contract_hash("gl")
        build_request("gl", "x")["config"]["response_json_schema"]["required"].clear()
        self.assertEqual(contract_hash("gl"), before)

    def test_each_pdf_page_uses_its_own_unicode_text(self):
        payload = {
            "document": {
                "text": "ไทยABC",
                "pages": [
                    {
                        "pageNumber": 1,
                        "layout": {"textAnchor": {"textSegments": [{"endIndex": "3"}]}},
                    },
                    {
                        "pageNumber": 2,
                        "layout": {
                            "textAnchor": {"textSegments": [{"startIndex": "3", "endIndex": "6"}]}
                        },
                    },
                ],
            }
        }
        self.assertEqual([p.text for p in enterprise.page_texts(payload)], ["ไทย", "ABC"])

    def test_missing_pages_is_not_success(self):
        with self.assertRaises(Layer1Error):
            enterprise.page_texts({"document": {"text": "orphan"}})

    @patch.dict(
        "os.environ", {"ENTERPRISE_OCR_PROJECT": "test", "ENTERPRISE_OCR_PROCESSOR_ID": "processor"}
    )
    def test_request_does_not_use_processor_default_version(self):
        session = Mock()
        session.post.return_value.status_code = 200
        session.post.return_value.json.return_value = {"document": {"text": "abc", "pages": [{}]}}
        enterprise.process(b"image", "image/jpeg", session=session)
        args, kwargs = session.post.call_args
        self.assertIn("/processorVersions/pretrained-ocr-v2.1.1-2025-01-31:process", args[0])
        self.assertTrue(kwargs["json"]["imagelessMode"])
        self.assertFalse(kwargs["json"]["processOptions"]["ocrConfig"]["enableNativePdfParsing"])

    @patch.dict(
        "os.environ", {"ENTERPRISE_OCR_PROJECT": "test", "ENTERPRISE_OCR_PROCESSOR_ID": "processor"}
    )
    def test_quota_and_auth_do_not_become_empty_success(self):
        for code, error in [(429, Layer1QuotaError), (403, Layer1AuthError)]:
            with self.subTest(code=code):
                session = Mock()
                session.post.return_value.status_code = code
                with self.assertRaises(error):
                    enterprise.process(b"image", "image/jpeg", session=session)
