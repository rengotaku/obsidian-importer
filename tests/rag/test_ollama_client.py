"""
Tests for Ollama Client module

All HTTP calls are mocked - no running Ollama server required.
"""
import json
import unittest
from unittest.mock import MagicMock, patch


class TestCheckConnection(unittest.TestCase):
    """check_connection() tests"""

    @patch("src.rag.clients.ollama.requests.get")
    def test_success(self, mock_get):
        """Successful connection returns (True, None)"""
        from src.rag.clients.ollama import check_connection

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        success, error = check_connection("http://localhost:11434")

        self.assertTrue(success)
        self.assertIsNone(error)
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", timeout=5
        )

    @patch("src.rag.clients.ollama.requests.get")
    def test_custom_timeout(self, mock_get):
        """Custom timeout is passed to requests"""
        from src.rag.clients.ollama import check_connection

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        check_connection("http://localhost:11434", timeout=10)

        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", timeout=10
        )

    @patch("src.rag.clients.ollama.requests.get")
    def test_timeout_error(self, mock_get):
        """Timeout returns (False, error_message)"""
        import requests

        from src.rag.clients.ollama import check_connection

        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        success, error = check_connection("http://localhost:11434", timeout=5)

        self.assertFalse(success)
        self.assertIn("timeout", error.lower())
        self.assertIn("5s", error)

    @patch("src.rag.clients.ollama.requests.get")
    def test_connection_error(self, mock_get):
        """Connection error returns (False, error_message)"""
        import requests

        from src.rag.clients.ollama import check_connection

        mock_get.side_effect = requests.exceptions.ConnectionError("refused")

        success, error = check_connection("http://localhost:11434")

        self.assertFalse(success)
        self.assertIn("Connection failed", error)

    @patch("src.rag.clients.ollama.requests.get")
    def test_http_error(self, mock_get):
        """HTTP error returns (False, error_message)"""
        import requests

        from src.rag.clients.ollama import check_connection

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "500 Server Error"
        )
        mock_get.return_value = mock_response

        success, error = check_connection("http://localhost:11434")

        self.assertFalse(success)
        self.assertIn("HTTP error", error)


class TestGetEmbedding(unittest.TestCase):
    """get_embedding() tests"""

    @patch("src.rag.clients.ollama.requests.post")
    def test_success(self, mock_post):
        """Successful embedding returns (embedding, None)"""
        from src.rag.clients.ollama import get_embedding

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3, 0.4, 0.5]]
        }
        mock_post.return_value = mock_response

        embedding, error = get_embedding("test text")

        self.assertIsNone(error)
        self.assertEqual(embedding, [0.1, 0.2, 0.3, 0.4, 0.5])

    @patch("src.rag.clients.ollama.requests.post")
    def test_custom_parameters(self, mock_post):
        """Custom model/url/timeout are used"""
        from src.rag.clients.ollama import get_embedding

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"embeddings": [[0.1]]}
        mock_post.return_value = mock_response

        get_embedding(
            "test",
            model="custom-model",
            url="http://custom:11434",
            timeout=60,
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://custom:11434/api/embed")
        self.assertEqual(call_args[1]["json"]["model"], "custom-model")
        self.assertEqual(call_args[1]["timeout"], 60)

    @patch("src.rag.clients.ollama.requests.post")
    def test_default_url_and_model(self, mock_post):
        """Default URL is remote server (ollama-server.local)"""
        from src.rag.clients.ollama import get_embedding

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"embeddings": [[0.1]]}
        mock_post.return_value = mock_response

        get_embedding("test")

        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://ollama-server.local:11434/api/embed")
        self.assertEqual(call_args[1]["json"]["model"], "bge-m3")

    def test_empty_text(self):
        """Empty text returns (None, error)"""
        from src.rag.clients.ollama import get_embedding

        embedding, error = get_embedding("")

        self.assertIsNone(embedding)
        self.assertIn("Empty", error)

    def test_whitespace_only_text(self):
        """Whitespace-only text returns (None, error)"""
        from src.rag.clients.ollama import get_embedding

        embedding, error = get_embedding("   ")

        self.assertIsNone(embedding)
        self.assertIn("Empty", error)

    @patch("src.rag.clients.ollama.requests.post")
    def test_timeout_error(self, mock_post):
        """Timeout returns (None, error)"""
        import requests

        from src.rag.clients.ollama import get_embedding

        mock_post.side_effect = requests.exceptions.Timeout("timeout")

        embedding, error = get_embedding("test text")

        self.assertIsNone(embedding)
        self.assertIn("timeout", error.lower())

    @patch("src.rag.clients.ollama.requests.post")
    def test_connection_error(self, mock_post):
        """Connection error returns (None, error)"""
        import requests

        from src.rag.clients.ollama import get_embedding

        mock_post.side_effect = requests.exceptions.ConnectionError("refused")

        embedding, error = get_embedding("test text")

        self.assertIsNone(embedding)
        self.assertIn("Connection failed", error)

    @patch("src.rag.clients.ollama.requests.post")
    def test_invalid_json_response(self, mock_post):
        """Invalid JSON returns (None, error)"""
        from src.rag.clients.ollama import get_embedding

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
        mock_post.return_value = mock_response

        embedding, error = get_embedding("test text")

        self.assertIsNone(embedding)
        self.assertIn("Invalid JSON", error)

    @patch("src.rag.clients.ollama.requests.post")
    def test_no_embeddings_in_response(self, mock_post):
        """Response without embeddings returns (None, error)"""
        from src.rag.clients.ollama import get_embedding

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"other": "data"}
        mock_post.return_value = mock_response

        embedding, error = get_embedding("test text")

        self.assertIsNone(embedding)
        self.assertIn("No embeddings", error)


class TestGenerateResponse(unittest.TestCase):
    """generate_response() tests"""

    @patch("src.rag.clients.ollama.requests.post")
    def test_success(self, mock_post):
        """Successful generation returns (response, None)"""
        from src.rag.clients.ollama import generate_response

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "response": "This is the generated response.",
            "done": True,
        }
        mock_post.return_value = mock_response

        response, error = generate_response("What is Python?")

        self.assertIsNone(error)
        self.assertEqual(response, "This is the generated response.")

    @patch("src.rag.clients.ollama.requests.post")
    def test_custom_parameters(self, mock_post):
        """Custom model/url/num_ctx/timeout are used"""
        from src.rag.clients.ollama import generate_response

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": "ok"}
        mock_post.return_value = mock_response

        generate_response(
            "test prompt",
            model="custom-llm",
            url="http://custom:11434",
            num_ctx=4096,
            timeout=300,
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://custom:11434/api/generate")
        self.assertEqual(call_args[1]["json"]["model"], "custom-llm")
        self.assertEqual(call_args[1]["json"]["options"]["num_ctx"], 4096)
        self.assertEqual(call_args[1]["timeout"], 300)

    @patch("src.rag.clients.ollama.requests.post")
    def test_default_url_and_model(self, mock_post):
        """Default URL is localhost (local LLM)"""
        from src.rag.clients.ollama import generate_response

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": "ok"}
        mock_post.return_value = mock_response

        generate_response("test")

        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://localhost:11434/api/generate")
        self.assertEqual(call_args[1]["json"]["model"], "gpt-oss:20b")

    @patch("src.rag.clients.ollama.requests.post")
    def test_stream_disabled(self, mock_post):
        """Stream is set to False"""
        from src.rag.clients.ollama import generate_response

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": "ok"}
        mock_post.return_value = mock_response

        generate_response("test")

        call_args = mock_post.call_args
        self.assertFalse(call_args[1]["json"]["stream"])

    def test_empty_prompt(self):
        """Empty prompt returns (None, error)"""
        from src.rag.clients.ollama import generate_response

        response, error = generate_response("")

        self.assertIsNone(response)
        self.assertIn("Empty", error)

    def test_whitespace_only_prompt(self):
        """Whitespace-only prompt returns (None, error)"""
        from src.rag.clients.ollama import generate_response

        response, error = generate_response("   ")

        self.assertIsNone(response)
        self.assertIn("Empty", error)

    @patch("src.rag.clients.ollama.requests.post")
    def test_timeout_error(self, mock_post):
        """Timeout returns (None, error)"""
        import requests

        from src.rag.clients.ollama import generate_response

        mock_post.side_effect = requests.exceptions.Timeout("timeout")

        response, error = generate_response("test prompt")

        self.assertIsNone(response)
        self.assertIn("timeout", error.lower())

    @patch("src.rag.clients.ollama.requests.post")
    def test_connection_error(self, mock_post):
        """Connection error returns (None, error)"""
        import requests

        from src.rag.clients.ollama import generate_response

        mock_post.side_effect = requests.exceptions.ConnectionError("refused")

        response, error = generate_response("test prompt")

        self.assertIsNone(response)
        self.assertIn("Connection failed", error)

    @patch("src.rag.clients.ollama.requests.post")
    def test_no_response_in_data(self, mock_post):
        """Response without 'response' field returns (None, error)"""
        from src.rag.clients.ollama import generate_response

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"other": "data"}
        mock_post.return_value = mock_response

        response, error = generate_response("test prompt")

        self.assertIsNone(response)
        self.assertIn("No response", error)

    @patch("src.rag.clients.ollama.requests.post")
    def test_empty_response_is_valid(self, mock_post):
        """Empty string response is valid (not an error)"""
        from src.rag.clients.ollama import generate_response

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response

        response, error = generate_response("test prompt")

        self.assertIsNone(error)
        self.assertEqual(response, "")


class TestImportFromPackage(unittest.TestCase):
    """Test imports from package level"""

    def test_import_from_clients_package(self):
        """Functions can be imported from clients package"""
        from src.rag.clients import (
            check_connection,
            generate_response,
            get_embedding,
        )

        self.assertTrue(callable(check_connection))
        self.assertTrue(callable(get_embedding))
        self.assertTrue(callable(generate_response))


if __name__ == "__main__":
    unittest.main()
