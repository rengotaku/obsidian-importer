"""Tests for log_context module.

Phase 2 RED tests: set_file_id, get_file_id, clear_file_id, ContextAwareFormatter.
These tests verify:
- file_id context management (set/get/clear)
- ContextAwareFormatter prepends [file_id] when set
- ContextAwareFormatter outputs message without prefix when file_id is not set
"""

from __future__ import annotations

import logging
import unittest


class TestSetFileId(unittest.TestCase):
    """set_file_id: file_id をコンテキストに設定する。"""

    def tearDown(self):
        """各テスト後にコンテキストをクリアする。"""
        from obsidian_etl.utils.log_context import clear_file_id

        clear_file_id()

    def test_set_file_id_basic(self):
        """set_file_id で設定した値が get_file_id で取得できること。

        FR-001: システムは contextvars を使用してログコンテキスト（file_id）を管理する
        """
        from obsidian_etl.utils.log_context import get_file_id, set_file_id

        set_file_id("abc123def456")
        self.assertEqual(get_file_id(), "abc123def456")

    def test_set_file_id_overwrite(self):
        """set_file_id を複数回呼ぶと最後の値が有効になること。

        State Transition: [設定済み] --set_file_id(new_id)--> [設定済み(上書き)]
        """
        from obsidian_etl.utils.log_context import get_file_id, set_file_id

        set_file_id("first_id")
        set_file_id("second_id")
        self.assertEqual(get_file_id(), "second_id")

    def test_set_file_id_with_sha256_prefix(self):
        """12文字の SHA256 ハッシュプレフィックスで正常動作すること。

        data-model.md: 12文字の SHA256 ハッシュプレフィックスが一般的
        """
        from obsidian_etl.utils.log_context import get_file_id, set_file_id

        sha_prefix = "a1b2c3d4e5f6"
        set_file_id(sha_prefix)
        self.assertEqual(get_file_id(), sha_prefix)

    def test_set_file_id_with_unicode(self):
        """Unicode 文字列を含む file_id でも正常動作すること。

        Edge case: Unicode/特殊文字
        """
        from obsidian_etl.utils.log_context import get_file_id, set_file_id

        set_file_id("日本語テスト_file_id")
        self.assertEqual(get_file_id(), "日本語テスト_file_id")


class TestGetFileId(unittest.TestCase):
    """get_file_id: コンテキストから file_id を取得する。"""

    def tearDown(self):
        """各テスト後にコンテキストをクリアする。"""
        from obsidian_etl.utils.log_context import clear_file_id

        clear_file_id()

    def test_get_file_id_default(self):
        """未設定時のデフォルト値は空文字列であること。

        data-model.md: _file_id_var: ContextVar[str] = ContextVar("file_id", default="")
        """
        from obsidian_etl.utils.log_context import get_file_id

        self.assertEqual(get_file_id(), "")

    def test_get_file_id_after_set(self):
        """set_file_id 後に正しい値が取得できること。"""
        from obsidian_etl.utils.log_context import get_file_id, set_file_id

        set_file_id("test_id")
        self.assertEqual(get_file_id(), "test_id")


class TestClearFileId(unittest.TestCase):
    """clear_file_id: file_id をクリアする。"""

    def tearDown(self):
        """各テスト後にコンテキストをクリアする。"""
        from obsidian_etl.utils.log_context import clear_file_id

        clear_file_id()

    def test_clear_file_id_resets_to_default(self):
        """clear_file_id 後に get_file_id がデフォルト値を返すこと。

        State Transition: [設定済み] --clear_file_id()--> [未設定]
        """
        from obsidian_etl.utils.log_context import clear_file_id, get_file_id, set_file_id

        set_file_id("some_id")
        clear_file_id()
        self.assertEqual(get_file_id(), "")

    def test_clear_file_id_when_already_empty(self):
        """未設定状態で clear_file_id を呼んでもエラーにならないこと。

        Edge case: 空入力/None
        """
        from obsidian_etl.utils.log_context import clear_file_id, get_file_id

        clear_file_id()
        self.assertEqual(get_file_id(), "")

    def test_set_clear_set_cycle(self):
        """set → clear → set のサイクルが正常に動作すること。"""
        from obsidian_etl.utils.log_context import clear_file_id, get_file_id, set_file_id

        set_file_id("first")
        self.assertEqual(get_file_id(), "first")

        clear_file_id()
        self.assertEqual(get_file_id(), "")

        set_file_id("second")
        self.assertEqual(get_file_id(), "second")


class TestContextAwareFormatterWithFileId(unittest.TestCase):
    """ContextAwareFormatter: file_id が設定されている場合のフォーマット。"""

    def tearDown(self):
        """各テスト後にコンテキストをクリアする。"""
        from obsidian_etl.utils.log_context import clear_file_id

        clear_file_id()

    def test_format_with_file_id_prepends_prefix(self):
        """file_id が設定されている場合、[file_id] がメッセージの前に付与されること。

        FR-003: ログフォーマッターは file_id が設定されている場合のみ
                [file_id] プレフィックスを出力しなければならない

        US1 Acceptance Scenario 1:
        Given: パーティション処理中に LLM が空のレスポンスを返した場合
        When: エラーがログに記録されるとき
        Then: ログメッセージに [file_id] プレフィックスが自動的に付与される
        """
        from obsidian_etl.utils.log_context import ContextAwareFormatter, set_file_id

        set_file_id("abc123def456")

        formatter = ContextAwareFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Empty response from LLM",
            args=None,
            exc_info=None,
        )

        formatted = formatter.format(record)
        self.assertIn("[abc123def456]", formatted)
        self.assertIn("Empty response from LLM", formatted)

    def test_format_with_file_id_prefix_position(self):
        """[file_id] プレフィックスがメッセージの先頭に付与されること。

        data-model.md: file_id 設定済み → [file_id] メッセージ
        """
        from obsidian_etl.utils.log_context import ContextAwareFormatter, set_file_id

        set_file_id("test_file")

        formatter = ContextAwareFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Processing started",
            args=None,
            exc_info=None,
        )

        formatted = formatter.format(record)
        # Message should start with [file_id]
        self.assertTrue(
            formatted.startswith("[test_file]"),
            f"Expected to start with '[test_file]', got: '{formatted}'",
        )

    def test_format_with_file_id_and_full_format(self):
        """完全なフォーマット文字列と組み合わせても [file_id] が含まれること。

        logging.yml の format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        """
        from obsidian_etl.utils.log_context import ContextAwareFormatter, set_file_id

        set_file_id("my_file_id")

        formatter = ContextAwareFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        record = logging.LogRecord(
            name="obsidian_etl.utils.ollama",
            level=logging.WARNING,
            pathname="ollama.py",
            lineno=136,
            msg="Empty response from LLM (context_len=1698 chars)",
            args=None,
            exc_info=None,
        )

        formatted = formatter.format(record)
        self.assertIn("[my_file_id]", formatted)
        self.assertIn("Empty response from LLM", formatted)

    def test_format_warning_level_with_file_id(self):
        """WARNING レベルのログに [file_id] が付与されること。

        US1 Acceptance Scenario 2:
        Given: パーティション処理中に任意の警告が発生した場合
        When: 警告がログに記録されるとき
        Then: ログメッセージに [file_id] プレフィックスが自動的に付与される
        """
        from obsidian_etl.utils.log_context import ContextAwareFormatter, set_file_id

        set_file_id("warn_file")

        formatter = ContextAwareFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Something went wrong",
            args=None,
            exc_info=None,
        )

        formatted = formatter.format(record)
        self.assertIn("[warn_file]", formatted)


class TestContextAwareFormatterWithoutFileId(unittest.TestCase):
    """ContextAwareFormatter: file_id が設定されていない場合のフォーマット。"""

    def tearDown(self):
        """各テスト後にコンテキストをクリアする。"""
        from obsidian_etl.utils.log_context import clear_file_id

        clear_file_id()

    def test_format_without_file_id_no_prefix(self):
        """file_id が未設定の場合、プレフィックスなしでメッセージが出力されること。

        FR-003: file_id が設定されていない場合はプレフィックスなし

        US1 Acceptance Scenario 3:
        Given: パーティション処理外でログが出力された場合
        When: ログが記録されるとき
        Then: [file_id] プレフィックスは付与されない（空やN/Aではない）
        """
        from obsidian_etl.utils.log_context import ContextAwareFormatter

        formatter = ContextAwareFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Normal log message",
            args=None,
            exc_info=None,
        )

        formatted = formatter.format(record)
        self.assertEqual(formatted, "Normal log message")

    def test_format_without_file_id_no_empty_brackets(self):
        """file_id 未設定時に空の [] や [None] が出力されないこと。

        Edge case: パーティション処理外でのログ出力
        """
        from obsidian_etl.utils.log_context import ContextAwareFormatter

        formatter = ContextAwareFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=None,
            exc_info=None,
        )

        formatted = formatter.format(record)
        self.assertNotIn("[]", formatted)
        self.assertNotIn("[None]", formatted)
        self.assertNotIn("[ ]", formatted)

    def test_format_after_clear_no_prefix(self):
        """clear_file_id 後はプレフィックスが付与されないこと。"""
        from obsidian_etl.utils.log_context import (
            ContextAwareFormatter,
            clear_file_id,
            set_file_id,
        )

        set_file_id("temp_id")
        clear_file_id()

        formatter = ContextAwareFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="After clear",
            args=None,
            exc_info=None,
        )

        formatted = formatter.format(record)
        self.assertEqual(formatted, "After clear")
        self.assertNotIn("[temp_id]", formatted)

    def test_format_without_file_id_preserves_full_format(self):
        """file_id 未設定時に完全なフォーマットが保持されること。"""
        from obsidian_etl.utils.log_context import ContextAwareFormatter

        formatter = ContextAwareFormatter(
            fmt="%(name)s - %(levelname)s - %(message)s",
        )
        record = logging.LogRecord(
            name="obsidian_etl",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Startup complete",
            args=None,
            exc_info=None,
        )

        formatted = formatter.format(record)
        self.assertEqual(formatted, "obsidian_etl - INFO - Startup complete")


class TestContextAwareFormatterIsLoggingFormatter(unittest.TestCase):
    """ContextAwareFormatter: logging.Formatter を継承していること。"""

    def test_inherits_from_logging_formatter(self):
        """ContextAwareFormatter は logging.Formatter のサブクラスであること。

        data-model.md: class ContextAwareFormatter(logging.Formatter)
        """
        from obsidian_etl.utils.log_context import ContextAwareFormatter

        self.assertTrue(issubclass(ContextAwareFormatter, logging.Formatter))

    def test_can_be_used_with_handler(self):
        """logging.Handler に設定できること。"""
        from obsidian_etl.utils.log_context import ContextAwareFormatter

        formatter = ContextAwareFormatter(fmt="%(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.assertIs(handler.formatter, formatter)


if __name__ == "__main__":
    unittest.main()
