"""Tests for Ollama exception classes.

Phase 3 RED tests: OllamaError hierarchy and context_len attribute.
These tests verify:
- OllamaError base class with message and context_len attributes
- OllamaEmptyResponseError subclass
- OllamaTimeoutError subclass
- OllamaConnectionError subclass
- context_len attribute accessibility from exception objects
"""

from __future__ import annotations

import unittest


class TestOllamaErrorBase(unittest.TestCase):
    """OllamaError: 基底例外クラスのテスト。"""

    def test_ollama_error_is_exception(self):
        """OllamaError は Exception のサブクラスであること。

        FR-006: システムは OllamaError 基底例外クラスを提供しなければならない
        """
        from obsidian_etl.utils.ollama import OllamaError

        self.assertTrue(issubclass(OllamaError, Exception))

    def test_ollama_error_with_message(self):
        """OllamaError が message 属性を持つこと。

        data-model.md: OllamaError.message: str - エラーメッセージ
        """
        from obsidian_etl.utils.ollama import OllamaError

        error = OllamaError("test error message", context_len=100)
        self.assertEqual(error.message, "test error message")

    def test_ollama_error_with_context_len(self):
        """OllamaError が context_len 属性を持つこと。

        data-model.md: OllamaError.context_len: int - 入力コンテキストの文字数
        """
        from obsidian_etl.utils.ollama import OllamaError

        error = OllamaError("error", context_len=1698)
        self.assertEqual(error.context_len, 1698)

    def test_ollama_error_context_len_default_zero(self):
        """OllamaError の context_len デフォルト値は 0 であること。

        data-model.md: def __init__(self, message: str, context_len: int = 0)
        """
        from obsidian_etl.utils.ollama import OllamaError

        error = OllamaError("error")
        self.assertEqual(error.context_len, 0)

    def test_ollama_error_str_representation(self):
        """OllamaError の文字列表現にメッセージが含まれること。"""
        from obsidian_etl.utils.ollama import OllamaError

        error = OllamaError("Connection failed", context_len=500)
        self.assertIn("Connection failed", str(error))

    def test_ollama_error_can_be_raised_and_caught(self):
        """OllamaError を raise して except でキャッチできること。"""
        from obsidian_etl.utils.ollama import OllamaError

        with self.assertRaises(OllamaError) as ctx:
            raise OllamaError("test", context_len=42)

        self.assertEqual(ctx.exception.message, "test")
        self.assertEqual(ctx.exception.context_len, 42)


class TestOllamaEmptyResponseError(unittest.TestCase):
    """OllamaEmptyResponseError: 空レスポンスエラーのテスト。"""

    def test_is_subclass_of_ollama_error(self):
        """OllamaEmptyResponseError は OllamaError のサブクラスであること。

        FR-007: システムは空レスポンスを表す OllamaEmptyResponseError を提供
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError, OllamaError

        self.assertTrue(issubclass(OllamaEmptyResponseError, OllamaError))

    def test_can_be_caught_as_ollama_error(self):
        """OllamaEmptyResponseError は OllamaError としてキャッチできること。

        US2 Acceptance Scenario 1:
        Given: LLM が空のレスポンスを返した場合
        When: call_ollama が呼ばれるとき
        Then: OllamaEmptyResponseError がスローされる
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError, OllamaError

        with self.assertRaises(OllamaError):
            raise OllamaEmptyResponseError("Empty response", context_len=1698)

    def test_has_message_and_context_len(self):
        """OllamaEmptyResponseError が message と context_len を持つこと。"""
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError

        error = OllamaEmptyResponseError("Empty response from LLM", context_len=2500)
        self.assertEqual(error.message, "Empty response from LLM")
        self.assertEqual(error.context_len, 2500)

    def test_is_exception(self):
        """OllamaEmptyResponseError は Exception のサブクラスであること。"""
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError

        self.assertTrue(issubclass(OllamaEmptyResponseError, Exception))


class TestOllamaTimeoutError(unittest.TestCase):
    """OllamaTimeoutError: タイムアウトエラーのテスト。"""

    def test_is_subclass_of_ollama_error(self):
        """OllamaTimeoutError は OllamaError のサブクラスであること。

        FR-008: システムはタイムアウトを表す OllamaTimeoutError を提供
        """
        from obsidian_etl.utils.ollama import OllamaError, OllamaTimeoutError

        self.assertTrue(issubclass(OllamaTimeoutError, OllamaError))

    def test_can_be_caught_as_ollama_error(self):
        """OllamaTimeoutError は OllamaError としてキャッチできること。

        US2 Acceptance Scenario 2:
        Given: リクエストがタイムアウトした場合
        When: call_ollama が呼ばれるとき
        Then: OllamaTimeoutError がスローされる
        """
        from obsidian_etl.utils.ollama import OllamaError, OllamaTimeoutError

        with self.assertRaises(OllamaError):
            raise OllamaTimeoutError("Timeout (120s)", context_len=5000)

    def test_has_message_and_context_len(self):
        """OllamaTimeoutError が message と context_len を持つこと。"""
        from obsidian_etl.utils.ollama import OllamaTimeoutError

        error = OllamaTimeoutError("Timeout (120s)", context_len=5000)
        self.assertEqual(error.message, "Timeout (120s)")
        self.assertEqual(error.context_len, 5000)


class TestOllamaConnectionError(unittest.TestCase):
    """OllamaConnectionError: 接続エラーのテスト。"""

    def test_is_subclass_of_ollama_error(self):
        """OllamaConnectionError は OllamaError のサブクラスであること。

        data-model.md: OllamaConnectionError は OllamaError の派生クラス
        """
        from obsidian_etl.utils.ollama import OllamaConnectionError, OllamaError

        self.assertTrue(issubclass(OllamaConnectionError, OllamaError))

    def test_can_be_caught_as_ollama_error(self):
        """OllamaConnectionError は OllamaError としてキャッチできること。"""
        from obsidian_etl.utils.ollama import OllamaConnectionError, OllamaError

        with self.assertRaises(OllamaError):
            raise OllamaConnectionError("Connection refused", context_len=0)

    def test_has_message_and_context_len(self):
        """OllamaConnectionError が message と context_len を持つこと。"""
        from obsidian_etl.utils.ollama import OllamaConnectionError

        error = OllamaConnectionError("Connection refused", context_len=300)
        self.assertEqual(error.message, "Connection refused")
        self.assertEqual(error.context_len, 300)


class TestContextLenAttribute(unittest.TestCase):
    """context_len 属性のテスト (US3)。"""

    def test_context_len_accessible_from_empty_response_error(self):
        """OllamaEmptyResponseError から context_len が取得できること。

        US3 Acceptance Scenario 1:
        Given: OllamaEmptyResponseError がスローされた場合
        When: 例外オブジェクトにアクセスするとき
        Then: context_len 属性が取得できる
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError

        try:
            raise OllamaEmptyResponseError("Empty", context_len=1698)
        except OllamaEmptyResponseError as e:
            self.assertEqual(e.context_len, 1698)

    def test_context_len_accessible_from_timeout_error(self):
        """OllamaTimeoutError から context_len が取得できること。"""
        from obsidian_etl.utils.ollama import OllamaTimeoutError

        try:
            raise OllamaTimeoutError("Timeout", context_len=25000)
        except OllamaTimeoutError as e:
            self.assertEqual(e.context_len, 25000)

    def test_context_len_accessible_from_connection_error(self):
        """OllamaConnectionError から context_len が取得できること。"""
        from obsidian_etl.utils.ollama import OllamaConnectionError

        try:
            raise OllamaConnectionError("Refused", context_len=0)
        except OllamaConnectionError as e:
            self.assertEqual(e.context_len, 0)

    def test_context_len_accessible_via_base_class_catch(self):
        """OllamaError でキャッチしても context_len が取得できること。

        設計意図: 呼び出し元は OllamaError でキャッチして context_len を参照できる
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError, OllamaError

        try:
            raise OllamaEmptyResponseError("Empty", context_len=999)
        except OllamaError as e:
            self.assertEqual(e.context_len, 999)

    def test_context_len_large_value(self):
        """大きな context_len 値でも正しく保持されること。

        Edge case: 大きなデータ（チャンク分割される25000文字超のケース）
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError

        error = OllamaEmptyResponseError("Empty", context_len=100000)
        self.assertEqual(error.context_len, 100000)

    def test_context_len_zero(self):
        """context_len が 0 でも正しく保持されること。

        Edge case: 境界値
        """
        from obsidian_etl.utils.ollama import OllamaError

        error = OllamaError("error", context_len=0)
        self.assertEqual(error.context_len, 0)


if __name__ == "__main__":
    unittest.main()
