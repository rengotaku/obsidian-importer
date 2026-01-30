"""
error_writer モジュールのテスト
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from scripts.llm_import.common.error_writer import (
    ErrorDetail,
    write_error_file,
    _truncate_content,
    MAX_FILE_SIZE_BYTES,
)


class TestErrorDetail(unittest.TestCase):
    """ErrorDetail データクラスのテスト"""

    def test_error_detail_creation(self):
        """ErrorDetail が正しく作成されることを確認"""
        error = ErrorDetail(
            session_id="20260117_150000",
            conversation_id="conv_123",
            conversation_title="Test Conversation",
            timestamp=datetime(2026, 1, 17, 15, 0, 0),
            error_type="json_parse",
            error_message="Invalid JSON",
            original_content="original text",
            llm_prompt="prompt text",
            stage="phase2",
        )

        self.assertEqual(error.session_id, "20260117_150000")
        self.assertEqual(error.conversation_id, "conv_123")
        self.assertEqual(error.error_type, "json_parse")
        self.assertIsNone(error.error_position)
        self.assertIsNone(error.llm_output)


class TestWriteErrorFile(unittest.TestCase):
    """write_error_file 関数のテスト"""

    def test_write_error_file(self):
        """エラーファイルが正しく出力されることを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "errors"

            error = ErrorDetail(
                session_id="20260117_150000",
                conversation_id="conv_123",
                conversation_title="Test Conversation",
                timestamp=datetime(2026, 1, 17, 15, 0, 0),
                error_type="json_parse",
                error_message="Invalid JSON at position 42",
                original_content="Hello World",
                llm_prompt="Extract knowledge from...",
                llm_output='{"invalid": json}',
                stage="phase2",
                error_position=42,
            )

            output_path = write_error_file(error, output_dir)

            # ファイルが作成されたことを確認
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.name, "conv_123.md")

            # 内容を確認
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("# Error Detail: Test Conversation", content)
            self.assertIn("**Session**: 20260117_150000", content)
            self.assertIn("**Error Type**: json_parse", content)
            self.assertIn("Hello World", content)
            self.assertIn("Extract knowledge from...", content)
            self.assertIn('{"invalid": json}', content)

    def test_error_file_truncation(self):
        """10MB 超過時にトランケーションされることを確認"""
        # 大きなコンテンツを生成（約 4MB × 3 = 12MB で10MB超過）
        large_content = "x" * (4 * 1024 * 1024)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "errors"

            error = ErrorDetail(
                session_id="20260117_150000",
                conversation_id="conv_large",
                conversation_title="Large Content Test",
                timestamp=datetime(2026, 1, 17, 15, 0, 0),
                error_type="json_parse",
                error_message="Error",
                original_content=large_content,
                llm_prompt=large_content,
                llm_output=large_content,
                stage="phase2",
            )

            output_path = write_error_file(error, output_dir)

            # ファイルサイズが 10MB 以下であることを確認
            file_size = output_path.stat().st_size
            self.assertLessEqual(file_size, MAX_FILE_SIZE_BYTES)

            # トランケーションマーカーが含まれることを確認
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("... (truncated)", content)


class TestTruncateContent(unittest.TestCase):
    """_truncate_content 関数のテスト"""

    def test_no_truncation_needed(self):
        """制限以下の場合はそのまま返す"""
        content = "short content"
        result = _truncate_content(content, 100)
        self.assertEqual(result, content)

    def test_truncation_applied(self):
        """制限超過時は切り詰める"""
        content = "x" * 100
        result = _truncate_content(content, 50)
        self.assertTrue(result.startswith("x" * 50))
        self.assertIn("... (truncated)", result)


if __name__ == "__main__":
    unittest.main()
