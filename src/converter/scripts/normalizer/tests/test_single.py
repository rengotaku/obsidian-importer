"""
test_single.py - single.py モジュールのテスト

処理層（build_normalized_file, normalize_filename等）のテストカバレッジ追加
"""
from __future__ import annotations

import unittest


class TestCleanFilename(unittest.TestCase):
    """clean_filename 関数のテスト"""

    def test_removes_jekyll_date_prefix(self):
        """Jekyll形式の日付プレフィックスを除去"""
        from normalizer.processing.single import clean_filename

        result = clean_filename("2022-10-17-Online-DDL-of-mysql")
        self.assertEqual(result, "Online-DDL-of-mysql")

    def test_removes_underscore_date_prefix(self):
        """アンダースコア形式の日付プレフィックスを除去"""
        from normalizer.processing.single import clean_filename

        result = clean_filename("2022_10_17_Some_Title")
        self.assertEqual(result, "Some_Title")

    def test_keeps_filename_without_date(self):
        """日付プレフィックスがない場合はそのまま"""
        from normalizer.processing.single import clean_filename

        result = clean_filename("Some-Title-Without-Date")
        self.assertEqual(result, "Some-Title-Without-Date")

    def test_keeps_partial_date_pattern(self):
        """不完全な日付パターンは除去しない"""
        from normalizer.processing.single import clean_filename

        result = clean_filename("2022-10-Title")
        self.assertEqual(result, "2022-10-Title")


class TestNormalizeFilename(unittest.TestCase):
    """normalize_filename 関数のテスト"""

    def test_removes_forbidden_characters(self):
        """禁止文字を除去"""
        from normalizer.processing.single import normalize_filename

        result = normalize_filename("File/Name:With*Bad?Chars")
        self.assertEqual(result, "FileNameWithBadChars")

    def test_normalizes_whitespace(self):
        """複数スペースを1つに正規化"""
        from normalizer.processing.single import normalize_filename

        result = normalize_filename("Title   With   Spaces")
        self.assertEqual(result, "Title With Spaces")

    def test_strips_leading_trailing_spaces(self):
        """前後の空白を除去"""
        from normalizer.processing.single import normalize_filename

        result = normalize_filename("  Trimmed Title  ")
        self.assertEqual(result, "Trimmed Title")

    def test_empty_string(self):
        """空文字列の場合"""
        from normalizer.processing.single import normalize_filename

        result = normalize_filename("")
        self.assertEqual(result, "")

    def test_japanese_title(self):
        """日本語タイトルも正常に処理（半角禁止文字のみ除去）"""
        from normalizer.processing.single import normalize_filename

        # 全角コロン「：」は禁止文字ではないので残る
        result = normalize_filename("日本語タイトル：テスト")
        self.assertEqual(result, "日本語タイトル：テスト")

    def test_removes_half_width_colon(self):
        """半角コロンは除去"""
        from normalizer.processing.single import normalize_filename

        result = normalize_filename("Title:Subtitle")
        self.assertEqual(result, "TitleSubtitle")


class TestBuildNormalizedFile(unittest.TestCase):
    """build_normalized_file 関数のテスト"""

    def _make_result(
        self,
        title: str = "Test Title",
        tags: list[str] | None = None,
        created: str = "2024-01-01",
        summary: str = "",
        related: list[str] | None = None,
        content: str = "# Content\n\nBody text.",
    ) -> dict:
        """テスト用のNormalizationResultを生成"""
        return {
            "genre": "エンジニア",
            "subfolder": "",
            "confidence": "high",
            "reason": "技術文書",
            "frontmatter": {
                "title": title,
                "tags": tags or ["tag1"],
                "created": created,
                "summary": summary,
                "related": related or [],
                "normalized": True,
                "review_confidence": None,
                "review_reason": None,
            },
            "normalized_content": content,
            "improvements_made": [],
            "is_complete_english_doc": False,
        }

    def test_includes_summary_and_related(self):
        """T039: summary と related が frontmatter に含まれる"""
        from normalizer.processing.single import build_normalized_file

        result = self._make_result(
            summary="これはテストサマリーです。",
            related=["[[関連ノート1]]", "[[関連ノート2]]"],
        )
        output = build_normalized_file(result)

        self.assertIn('summary: "これはテストサマリーです。"', output)
        self.assertIn("related:", output)
        self.assertIn('  - "[[関連ノート1]]"', output)
        self.assertIn('  - "[[関連ノート2]]"', output)

    def test_includes_all_frontmatter_fields(self):
        """T040: 全てのfrontmatterフィールドが含まれる"""
        from normalizer.processing.single import build_normalized_file

        result = self._make_result(
            title="Complete Test",
            tags=["python", "test"],
            created="2024-06-15",
            summary="サマリーテキスト",
            related=["[[Link]]"],
        )
        output = build_normalized_file(result)

        # 必須フィールド
        self.assertIn('title: "Complete Test"', output)
        self.assertIn("tags:", output)
        self.assertIn("  - python", output)
        self.assertIn("  - test", output)
        self.assertIn("created: 2024-06-15", output)

        # オプションフィールド
        self.assertIn('summary: "サマリーテキスト"', output)
        self.assertIn("related:", output)

    def test_empty_optional_fields(self):
        """T042: summary/related が空の場合は出力しない"""
        from normalizer.processing.single import build_normalized_file

        result = self._make_result(summary="", related=[])
        output = build_normalized_file(result)

        self.assertNotIn("summary:", output)
        self.assertNotIn("related:", output)

    def test_frontmatter_structure(self):
        """frontmatterの構造が正しい（---で囲まれている）"""
        from normalizer.processing.single import build_normalized_file

        result = self._make_result()
        output = build_normalized_file(result)

        lines = output.split("\n")
        self.assertEqual(lines[0], "---")
        # 閉じ---を探す
        close_idx = None
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                close_idx = i
                break
        self.assertIsNotNone(close_idx, "Closing --- not found")

    def test_body_content_preserved(self):
        """本文内容が保持される"""
        from normalizer.processing.single import build_normalized_file

        result = self._make_result(content="# Heading\n\nParagraph content.")
        output = build_normalized_file(result)

        self.assertIn("# Heading", output)
        self.assertIn("Paragraph content.", output)

    def test_existing_frontmatter_in_content_removed(self):
        """本文中の既存frontmatterは除去される"""
        from normalizer.processing.single import build_normalized_file

        content_with_fm = """---
title: Old Title
---

# Real Content
"""
        result = self._make_result(content=content_with_fm)
        output = build_normalized_file(result)

        # 新しいfrontmatterのみ存在
        self.assertEqual(output.count("---"), 2)
        self.assertIn('title: "Test Title"', output)
        self.assertNotIn("Old Title", output)


class TestNormalizeMarkdown(unittest.TestCase):
    """normalize_markdown 関数のテスト"""

    def test_collapses_multiple_blank_lines(self):
        """3つ以上の空行を2つに圧縮"""
        from normalizer.processing.single import normalize_markdown

        content = "# Heading\n\n\n\n\nParagraph"
        result = normalize_markdown(content)

        self.assertEqual(result, "# Heading\n\nParagraph\n")

    def test_preserves_double_blank_lines(self):
        """2つの空行は維持"""
        from normalizer.processing.single import normalize_markdown

        content = "# Heading\n\nParagraph"
        result = normalize_markdown(content)

        self.assertEqual(result, "# Heading\n\nParagraph\n")

    def test_strips_trailing_whitespace(self):
        """各行の末尾空白を除去"""
        from normalizer.processing.single import normalize_markdown

        content = "Line with spaces   \nAnother line\t\t"
        result = normalize_markdown(content)

        self.assertEqual(result, "Line with spaces\nAnother line\n")

    def test_adds_trailing_newline(self):
        """末尾に改行を追加"""
        from normalizer.processing.single import normalize_markdown

        content = "Content without newline"
        result = normalize_markdown(content)

        self.assertTrue(result.endswith("\n"))

    def test_preserves_single_trailing_newline(self):
        """既存の末尾改行は重複しない"""
        from normalizer.processing.single import normalize_markdown

        content = "Content with newline\n"
        result = normalize_markdown(content)

        self.assertEqual(result.count("\n"), content.count("\n"))


class TestExtractFrontmatter(unittest.TestCase):
    """extract_frontmatter 関数のテスト"""

    def test_extract_valid_frontmatter(self):
        """正常なfrontmatterを抽出（辞書として返される）"""
        from normalizer.processing.single import extract_frontmatter

        content = """---
title: Test
tags:
  - tag1
---

# Body
"""
        fm, body = extract_frontmatter(content)

        self.assertIsNotNone(fm)
        self.assertIsInstance(fm, dict)
        self.assertEqual(fm.get("title"), "Test")
        self.assertIn("# Body", body)

    def test_no_frontmatter(self):
        """frontmatterがない場合"""
        from normalizer.processing.single import extract_frontmatter

        content = "# Just Content\n\nNo frontmatter here."
        fm, body = extract_frontmatter(content)

        self.assertIsNone(fm)
        self.assertEqual(body, content)

    def test_incomplete_frontmatter(self):
        """閉じ---がない不完全なfrontmatter"""
        from normalizer.processing.single import extract_frontmatter

        content = "---\ntitle: Test\nno closing"
        fm, body = extract_frontmatter(content)

        self.assertIsNone(fm)
        self.assertEqual(body, content)


class TestExtractFileIdFromFrontmatter(unittest.TestCase):
    """extract_file_id_from_frontmatter 関数のテスト (T028)"""

    def test_extracts_file_id_from_valid_frontmatter(self):
        """有効な frontmatter から file_id を抽出"""
        from normalizer.processing.single import extract_file_id_from_frontmatter

        content = "---\ntitle: Test\nfile_id: a1b2c3d4e5f6\n---\n# Content"
        result = extract_file_id_from_frontmatter(content)

        self.assertEqual(result, "a1b2c3d4e5f6")

    def test_extracts_file_id_at_different_position(self):
        """file_id が別の位置にあっても抽出可能"""
        from normalizer.processing.single import extract_file_id_from_frontmatter

        content = "---\nfile_id: 1234567890ab\ntitle: Test\ntags:\n  - tag1\n---\n# Body"
        result = extract_file_id_from_frontmatter(content)

        self.assertEqual(result, "1234567890ab")

    def test_returns_none_for_missing_file_id(self):
        """file_id がない場合は None を返す"""
        from normalizer.processing.single import extract_file_id_from_frontmatter

        content = "---\ntitle: Test\n---\n# Content"
        result = extract_file_id_from_frontmatter(content)

        self.assertIsNone(result)

    def test_returns_none_for_no_frontmatter(self):
        """frontmatter がない場合は None を返す"""
        from normalizer.processing.single import extract_file_id_from_frontmatter

        content = "# Just Content\n\nNo frontmatter here."
        result = extract_file_id_from_frontmatter(content)

        self.assertIsNone(result)

    def test_returns_none_for_invalid_file_id_format(self):
        """無効な file_id 形式の場合は None を返す"""
        from normalizer.processing.single import extract_file_id_from_frontmatter

        # 12文字未満
        content1 = "---\nfile_id: abc123\n---\n# Content"
        self.assertIsNone(extract_file_id_from_frontmatter(content1))

        # 12文字を超える
        content2 = "---\nfile_id: a1b2c3d4e5f67890\n---\n# Content"
        self.assertIsNone(extract_file_id_from_frontmatter(content2))

        # 大文字を含む
        content3 = "---\nfile_id: A1B2C3D4E5F6\n---\n# Content"
        self.assertIsNone(extract_file_id_from_frontmatter(content3))

    def test_does_not_match_file_id_outside_frontmatter(self):
        """frontmatter 外の file_id にはマッチしない"""
        from normalizer.processing.single import extract_file_id_from_frontmatter

        content = "---\ntitle: Test\n---\n# Content\nfile_id: a1b2c3d4e5f6"
        result = extract_file_id_from_frontmatter(content)

        self.assertIsNone(result)


class TestGetOrGenerateFileId(unittest.TestCase):
    """get_or_generate_file_id 関数のテスト (T029)"""

    def test_preserves_existing_file_id(self):
        """T031: 既存の file_id を維持する"""
        from pathlib import Path
        from normalizer.processing.single import get_or_generate_file_id

        # 12文字の16進数小文字 (有効な file_id 形式)
        content = "---\ntitle: Test\nfile_id: a1b2c3d4e5f6\n---\n# Content"
        filepath = Path("test/file.md")

        result = get_or_generate_file_id(content, filepath)

        self.assertEqual(result, "a1b2c3d4e5f6")

    def test_generates_file_id_when_missing(self):
        """T032: file_id がない場合は新規生成"""
        from pathlib import Path
        from normalizer.processing.single import get_or_generate_file_id, generate_file_id

        content = "---\ntitle: Test\n---\n# Content"
        filepath = Path("test/file.md")

        result = get_or_generate_file_id(content, filepath)

        # 新規生成されるべき file_id と一致
        expected = generate_file_id(content, filepath)
        self.assertEqual(result, expected)

    def test_generates_file_id_for_no_frontmatter(self):
        """frontmatter がない場合も新規生成"""
        from pathlib import Path
        from normalizer.processing.single import get_or_generate_file_id, generate_file_id

        content = "# Just Content\n\nNo frontmatter here."
        filepath = Path("test/file.md")

        result = get_or_generate_file_id(content, filepath)

        # 新規生成されるべき file_id と一致
        expected = generate_file_id(content, filepath)
        self.assertEqual(result, expected)

    def test_file_id_format(self):
        """生成される file_id のフォーマット検証"""
        from pathlib import Path
        from normalizer.processing.single import get_or_generate_file_id
        import re

        content = "# Test Content"
        filepath = Path("test/file.md")

        result = get_or_generate_file_id(content, filepath)

        # 12文字の16進数小文字
        self.assertIsNotNone(re.match(r"^[a-f0-9]{12}$", result))


if __name__ == "__main__":
    unittest.main()
