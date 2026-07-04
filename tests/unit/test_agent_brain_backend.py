"""Agent brain backend selection tests."""

import unittest
from unittest import mock

from services.agent import brain
from services.ai_gateway import backends


class AgentBrainBackendTests(unittest.TestCase):
    def test_unset_follows_global_backend(self):
        with mock.patch.dict(
            "os.environ",
            {"OCR_LLM_BACKEND": "vertex"},
            clear=True,
        ):
            self.assertIsNone(brain._brain_backend())
            self.assertEqual(backends.active_backend(), "vertex")

    def test_empty_follows_global_backend(self):
        with mock.patch.dict(
            "os.environ",
            {"OCR_LLM_BACKEND": "selfhost", "AGENT_BRAIN_BACKEND": "  "},
            clear=True,
        ):
            self.assertIsNone(brain._brain_backend())
            self.assertEqual(backends.active_backend(), "selfhost")

    def test_valid_override_is_used(self):
        for value in ("aistudio", "vertex", "selfhost", "anthropic"):
            with self.subTest(value=value):
                with mock.patch.dict("os.environ", {"AGENT_BRAIN_BACKEND": value.upper()}):
                    self.assertEqual(brain._brain_backend(), value)

    def test_invalid_override_is_ignored(self):
        with mock.patch.dict(
            "os.environ",
            {"OCR_LLM_BACKEND": "vertex", "AGENT_BRAIN_BACKEND": "gemini"},
            clear=True,
        ):
            self.assertIsNone(brain._brain_backend())
            self.assertEqual(backends.active_backend(), "vertex")


if __name__ == "__main__":
    unittest.main()
