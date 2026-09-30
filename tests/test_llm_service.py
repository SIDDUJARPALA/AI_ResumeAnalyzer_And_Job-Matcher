import unittest
from unittest.mock import Mock, patch

import requests
from flask import Flask

from config import Config
from services.llm_service import LLMServiceError, generate_json


class LLMServiceTests(unittest.TestCase):
    def test_default_provider_is_groq(self):
        self.assertEqual(Config.LLM_PROVIDER, "groq")

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            LLM_PROVIDER="groq",
            GROQ_API_KEY="groq-test-key",
            GROQ_MODEL="openai/gpt-oss-120b",
        )
        self.context = self.app.app_context()
        self.context.push()

    def tearDown(self):
        self.context.pop()

    @patch("services.llm_service.requests.post")
    def test_groq_provider_uses_groq_endpoint_and_json_mode(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": '{"ok":true}'}}]}
        post.return_value = response

        self.assertEqual(generate_json("system", "user"), {"ok": True})
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer groq-test-key")
        self.assertEqual(kwargs["json"]["model"], "openai/gpt-oss-120b")
        self.assertEqual(kwargs["json"]["response_format"], {"type": "json_object"})

    @patch("services.llm_service.requests.post")
    def test_invalid_provider_fails_before_network_request(self, post):
        self.app.config["LLM_PROVIDER"] = "unknown"

        with self.assertRaisesRegex(LLMServiceError, "LLM_PROVIDER"):
            generate_json("system", "user")

        post.assert_not_called()

    @patch("services.llm_service.requests.post")
    def test_missing_selected_provider_key_is_reported(self, post):
        self.app.config["GROQ_API_KEY"] = ""

        with self.assertRaisesRegex(LLMServiceError, "GROQ_API_KEY"):
            generate_json("system", "user")

        post.assert_not_called()

    @patch("services.llm_service.requests.post")
    def test_http_error_without_response_shows_network_guidance(self, post):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("proxy failure")
        post.return_value = response

        with self.assertRaisesRegex(LLMServiceError, "No HTTP response was received"):
            generate_json("system", "user")

    @patch("services.llm_service.requests.post")
    def test_unauthorized_response_reports_key_guidance_and_provider_detail(self, post):
        response = requests.Response()
        response.status_code = 401
        response._content = b'{"error":{"message":"Incorrect API key provided","type":"invalid_api_key"}}'
        post.return_value = response

        with self.assertRaises(LLMServiceError) as context:
            generate_json("system", "user")

        message = str(context.exception)
        self.assertIn("HTTP 401", message)
        self.assertIn("provider dashboard", message)
        self.assertIn("Incorrect API key provided", message)
        self.assertNotIn("groq-test-key", message)


if __name__ == "__main__":
    unittest.main()
