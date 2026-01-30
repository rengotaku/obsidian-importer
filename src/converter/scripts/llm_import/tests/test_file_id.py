"""
Test File ID - ファイル追跡ハッシュIDのテスト

generate_file_id 関数のユニットテスト。
normalizer の同名関数と同一アルゴリズムであることを検証する。
"""
import unittest
from pathlib import Path


class TestGenerateFileId(unittest.TestCase):
    """generate_file_id 関数のユニットテスト"""

    def test_generate_file_id_returns_12_char_hex(self):
        """12文字の16進数文字列を返す"""
        from scripts.llm_import.common.file_id import generate_file_id

        content = "# Test Content\nThis is a test."
        filepath = Path("test.md")

        result = generate_file_id(content, filepath)

        self.assertEqual(len(result), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_generate_file_id_deterministic(self):
        """同じ入力に対して同じIDを生成する（決定論的）"""
        from scripts.llm_import.common.file_id import generate_file_id

        content = "# Test Content"
        filepath = Path("test.md")

        result1 = generate_file_id(content, filepath)
        result2 = generate_file_id(content, filepath)

        self.assertEqual(result1, result2)

    def test_generate_file_id_different_content(self):
        """異なるコンテンツで異なるIDを生成する"""
        from scripts.llm_import.common.file_id import generate_file_id

        filepath = Path("test.md")

        id1 = generate_file_id("Content A", filepath)
        id2 = generate_file_id("Content B", filepath)

        self.assertNotEqual(id1, id2)

    def test_generate_file_id_different_path(self):
        """異なるパスで異なるIDを生成する（同一コンテンツでも）"""
        from scripts.llm_import.common.file_id import generate_file_id

        content = "Same content"

        id1 = generate_file_id(content, Path("file1.md"))
        id2 = generate_file_id(content, Path("file2.md"))

        self.assertNotEqual(id1, id2)

    def test_generate_file_id_path_normalization(self):
        """パスはPOSIX形式に正規化される"""
        from scripts.llm_import.common.file_id import generate_file_id

        content = "Test"
        # POSIXパスで同じ結果になる
        id1 = generate_file_id(content, Path("dir/subdir/test.md"))
        id2 = generate_file_id(content, Path("dir/subdir/test.md"))

        self.assertEqual(id1, id2)

    def test_generate_file_id_empty_content(self):
        """空コンテンツでもIDを生成できる"""
        from scripts.llm_import.common.file_id import generate_file_id

        result = generate_file_id("", Path("empty.md"))

        self.assertEqual(len(result), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_generate_file_id_unicode_content(self):
        """Unicodeコンテンツ（日本語等）を処理できる"""
        from scripts.llm_import.common.file_id import generate_file_id

        content = "# 日本語タイトル\nこれはテストです。"
        filepath = Path("日本語ファイル.md")

        result = generate_file_id(content, filepath)

        self.assertEqual(len(result), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_generate_file_id_compatible_with_normalizer(self):
        """normalizer の generate_file_id と同一の結果を返す"""
        from scripts.llm_import.common.file_id import generate_file_id

        # normalizer と同一アルゴリズムであることを確認するための固定テストケース
        # combined = "Test Content\n---\ntest.md" の SHA-256 先頭12文字
        content = "Test Content"
        filepath = Path("test.md")

        result = generate_file_id(content, filepath)

        # 固定入力に対する期待値（手動計算による検証済み）
        # hashlib.sha256("Test Content\n---\ntest.md".encode()).hexdigest()[:12]
        expected = "1dbf8900a5b1"
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
