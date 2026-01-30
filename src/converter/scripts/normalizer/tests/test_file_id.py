"""
Test File ID - ファイル追跡ハッシュIDのテスト

generate_file_id 関数とログ連携のテスト。
"""
import unittest
from pathlib import Path


class TestGenerateFileId(unittest.TestCase):
    """generate_file_id 関数のユニットテスト"""

    def test_generate_file_id_returns_12_char_hex(self):
        """12文字の16進数文字列を返す"""
        from normalizer.processing.single import generate_file_id

        content = "# Test Content\nThis is a test."
        filepath = Path("test.md")

        result = generate_file_id(content, filepath)

        self.assertEqual(len(result), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_generate_file_id_deterministic(self):
        """同じ入力に対して同じIDを生成する"""
        from normalizer.processing.single import generate_file_id

        content = "# Test Content"
        filepath = Path("test.md")

        result1 = generate_file_id(content, filepath)
        result2 = generate_file_id(content, filepath)

        self.assertEqual(result1, result2)

    def test_generate_file_id_different_content(self):
        """異なるコンテンツで異なるIDを生成する"""
        from normalizer.processing.single import generate_file_id

        filepath = Path("test.md")

        id1 = generate_file_id("Content A", filepath)
        id2 = generate_file_id("Content B", filepath)

        self.assertNotEqual(id1, id2)

    def test_generate_file_id_different_path(self):
        """異なるパスで異なるIDを生成する（同一コンテンツでも）"""
        from normalizer.processing.single import generate_file_id

        content = "Same content"

        id1 = generate_file_id(content, Path("file1.md"))
        id2 = generate_file_id(content, Path("file2.md"))

        self.assertNotEqual(id1, id2)

    def test_generate_file_id_path_normalization(self):
        """パスはPOSIX形式に正規化される"""
        from normalizer.processing.single import generate_file_id

        content = "Test"
        # POSIXパスとWindowsパスで同じ結果になる
        id1 = generate_file_id(content, Path("dir/subdir/test.md"))
        id2 = generate_file_id(content, Path("dir/subdir/test.md"))

        self.assertEqual(id1, id2)

    def test_generate_file_id_empty_content(self):
        """空コンテンツでもIDを生成できる"""
        from normalizer.processing.single import generate_file_id

        result = generate_file_id("", Path("empty.md"))

        self.assertEqual(len(result), 12)

    def test_generate_file_id_unicode_content(self):
        """Unicodeコンテンツ（日本語等）を処理できる"""
        from normalizer.processing.single import generate_file_id

        content = "# 日本語タイトル\nこれはテストです。"
        filepath = Path("日本語ファイル.md")

        result = generate_file_id(content, filepath)

        self.assertEqual(len(result), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))


class TestUpdateStateWithFileId(unittest.TestCase):
    """update_state 関数の file_id 連携テスト"""

    def test_update_state_includes_file_id_in_processed(self):
        """処理成功時、processed エントリに file_id が含まれる"""
        from normalizer.state.manager import update_state, create_initial_state

        state = create_initial_state([Path("test.md")])
        result = {
            "success": True,
            "file": "test.md",
            "genre": "エンジニア",
            "confidence": "high",
            "destination": "Vaults/エンジニア/test.md",
            "error": None,
            "timestamp": "2026-01-17T10:00:00",
            "original_chars": 100,
            "normalized_chars": 120,
            "char_diff": 20,
            "improvements_made": [],
            "is_complete_english_doc": False,
            "is_review": False,
            "review_reason": None,
            "file_id": "abc123def456"
        }

        updated = update_state(state, result)

        self.assertEqual(len(updated["processed"]), 1)
        self.assertEqual(updated["processed"][0]["file_id"], "abc123def456")

    def test_update_state_includes_file_id_in_errors(self):
        """処理失敗時、errors エントリに file_id が含まれる"""
        from normalizer.state.manager import update_state, create_initial_state

        state = create_initial_state([Path("broken.md")])
        result = {
            "success": False,
            "file": "broken.md",
            "genre": None,
            "confidence": "low",
            "destination": None,
            "error": "LLM parse error",
            "timestamp": "2026-01-17T10:00:00",
            "original_chars": None,
            "normalized_chars": None,
            "char_diff": None,
            "improvements_made": None,
            "is_complete_english_doc": None,
            "is_review": False,
            "review_reason": None,
            "file_id": "xyz789abc012"
        }

        updated = update_state(state, result)

        self.assertEqual(len(updated["errors"]), 1)
        self.assertEqual(updated["errors"][0]["file_id"], "xyz789abc012")

    def test_update_state_without_file_id_backward_compatible(self):
        """file_id がない場合でも後方互換性を維持"""
        from normalizer.state.manager import update_state, create_initial_state

        state = create_initial_state([Path("old.md")])
        # file_id が None の旧形式結果
        result = {
            "success": True,
            "file": "old.md",
            "genre": "ビジネス",
            "confidence": "high",
            "destination": "Vaults/ビジネス/old.md",
            "error": None,
            "timestamp": "2026-01-17T10:00:00",
            "original_chars": 50,
            "normalized_chars": 60,
            "char_diff": 10,
            "improvements_made": [],
            "is_complete_english_doc": False,
            "is_review": False,
            "review_reason": None,
            "file_id": None
        }

        updated = update_state(state, result)

        self.assertEqual(len(updated["processed"]), 1)
        # file_id が None の場合は含まれない
        self.assertNotIn("file_id", updated["processed"][0])


class TestBuildNormalizedFileWithFileId(unittest.TestCase):
    """build_normalized_file 関数の file_id frontmatter テスト"""

    def _create_result(self):
        """テスト用の NormalizationResult を作成"""
        return {
            "genre": "エンジニア",
            "subfolder": "",
            "confidence": "high",
            "reason": "技術文書",
            "frontmatter": {
                "title": "Test Title",
                "tags": ["test"],
                "created": "2026-01-17",
                "summary": "Test summary",
                "related": [],
                "normalized": True,
                "review_confidence": None,
                "review_reason": None
            },
            "normalized_content": "# Test Content",
            "improvements_made": [],
            "is_complete_english_doc": False
        }

    def test_file_id_in_frontmatter(self):
        """file_id が frontmatter に含まれる"""
        from normalizer.processing.single import build_normalized_file

        result = self._create_result()
        output = build_normalized_file(result, file_id="abc123def456")

        self.assertIn("file_id: abc123def456", output)

    def test_file_id_none_not_in_frontmatter(self):
        """file_id が None の場合は frontmatter に含まれない"""
        from normalizer.processing.single import build_normalized_file

        result = self._create_result()
        output = build_normalized_file(result, file_id=None)

        self.assertNotIn("file_id:", output)

    def test_file_id_position_in_frontmatter(self):
        """file_id は related の後に配置される"""
        from normalizer.processing.single import build_normalized_file

        result = self._create_result()
        result["frontmatter"]["related"] = ["[[Related Note]]"]
        output = build_normalized_file(
            result,
            file_id="abc123def456"
        )

        # file_id が related より後にあることを確認
        related_pos = output.find("related:")
        file_id_pos = output.find("file_id:")

        self.assertGreater(related_pos, 0)
        self.assertGreater(file_id_pos, related_pos)

    def test_file_id_with_all_fields(self):
        """全フィールドと file_id が正しく出力される"""
        from normalizer.processing.single import build_normalized_file

        result = self._create_result()
        result["frontmatter"]["related"] = ["[[Note1]]", "[[Note2]]"]
        output = build_normalized_file(result, file_id="123456789abc")

        # 必須フィールドの存在確認
        self.assertIn('title: "Test Title"', output)
        self.assertIn("tags:", output)
        self.assertIn("created: 2026-01-17", output)
        self.assertIn("file_id: 123456789abc", output)
        self.assertIn("# Test Content", output)


if __name__ == "__main__":
    unittest.main()
