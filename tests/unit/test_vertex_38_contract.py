import unittest
from types import SimpleNamespace
from unittest.mock import patch, Mock

from services.ai_gateway.providers import vertex


def response(text, finish="STOP", prompt=10, output=20, thoughts=30):
    return SimpleNamespace(
        text=text,
        candidates=[SimpleNamespace(finish_reason=finish)],
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt, candidates_token_count=output, thoughts_token_count=thoughts
        ),
    )


class Vertex38ContractTest(unittest.TestCase):
    def test_global_not_overridden_by_legacy_region_env(self):
        with patch.dict("os.environ", {"VERTEX_LOCATION_25": "asia-southeast1"}):
            self.assertEqual("global", vertex._location_for_model("gemini-3.8-flash"))

    def test_low_on_structured_vision(self):
        config = vertex._config(0, 16384, True, structured_vision_model="gemini-3.8-flash")
        self.assertEqual("LOW", config.thinking_config.thinking_level.value)

    @patch.object(vertex, "_gen_json")
    @patch.object(vertex, "_resolve_model", return_value="gemini-3.8-flash")
    def test_low_on_text_path_too(self, model, generate):
        vertex.text_to_json("test")
        self.assertEqual(
            "LOW", generate.call_args.kwargs["config"].thinking_config.thinking_level.value
        )

    def test_output_includes_billed_thoughts(self):
        self.assertEqual((10, 50), vertex._usage(response("{}")))

    @patch.object(vertex, "_client")
    def test_parse_retry_costs_not_discarded(self, client):
        client.return_value.models.generate_content.side_effect = [
            response("broken"),
            response("{}"),
        ]
        out = vertex._gen_json("p", model_name="gemini-3.8-flash", config=None, max_retries=1)
        self.assertTrue(out.ok)
        self.assertEqual((20, 100), (out.input_tokens, out.output_tokens))

    @patch.object(vertex, "_client")
    def test_parseable_but_truncated_is_failure(self, client):
        client.return_value.models.generate_content.return_value = response("{}", "MAX_TOKENS")
        out = vertex._gen_json("p", model_name="gemini-3.8-flash", config=None, max_retries=0)
        self.assertFalse(out.ok)
        self.assertEqual("parse", out.error_kind)

    @patch.object(vertex, "_client")
    def test_transport_failure_keeps_prior_billed_usage(self, client):
        client.return_value.models.generate_content.side_effect = [
            response("bad"),
            RuntimeError("provider"),
        ]
        out = vertex._gen_json("p", model_name="gemini-3.8-flash", config=None, max_retries=1)
        self.assertFalse(out.ok)
        self.assertEqual((10, 50), (out.input_tokens, out.output_tokens))


if __name__ == "__main__":
    unittest.main()
