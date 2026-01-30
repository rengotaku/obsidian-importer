"""
test_validators.py - バリデーターモジュールのテスト

normalizer.validators モジュールの関数をテスト
"""
from __future__ import annotations

import unittest

from normalizer.tests import read_fixture


class TestExtractFrontmatter(unittest.TestCase):
    """_extract_frontmatter 関数のテスト"""

    def test_extract_with_frontmatter(self):
        """frontmatter付きコンテンツから分離"""
        from normalizer.validators.format import _extract_frontmatter

        content = """---
title: Test
tags:
  - tag1
---

# Body
"""
        fm, body = _extract_frontmatter(content)

        self.assertIsNotNone(fm)
        self.assertIn("title: Test", fm)
        self.assertIn("# Body", body)

    def test_extract_without_frontmatter(self):
        """frontmatterなしの場合はNoneと元コンテンツ"""
        from normalizer.validators.format import _extract_frontmatter

        content = "# Just a heading\n\nSome content"
        fm, body = _extract_frontmatter(content)

        self.assertIsNone(fm)
        self.assertEqual(body, content)

    def test_extract_incomplete_frontmatter(self):
        """閉じタグのない不完全なfrontmatter"""
        from normalizer.validators.format import _extract_frontmatter

        content = "---\ntitle: Test\nno closing tag"
        fm, body = _extract_frontmatter(content)

        # 閉じタグがないので frontmatter として認識されない
        self.assertIsNone(fm)
        self.assertEqual(body, content)


class TestValidateMarkdownFormat(unittest.TestCase):
    """validate_markdown_format 関数のテスト"""

    def test_valid_markdown(self):
        """正しい形式のMarkdown"""
        from normalizer.validators.format import validate_markdown_format

        content = """---
title: Valid Document
normalized: true
---

## Section 1

- Item 1
- Item 2

## Section 2

Some content here.
"""
        is_valid, issues = validate_markdown_format(content)

        self.assertTrue(is_valid)
        self.assertEqual(issues, [])

    def test_missing_frontmatter(self):
        """frontmatterがない場合"""
        from normalizer.validators.format import validate_markdown_format

        content = "# No frontmatter\n\nJust content."
        is_valid, issues = validate_markdown_format(content)

        self.assertFalse(is_valid)
        self.assertIn("frontmatterがありません", issues)

    def test_missing_title(self):
        """titleフィールドがない場合"""
        from normalizer.validators.format import validate_markdown_format

        content = """---
normalized: true
---

## Content
"""
        is_valid, issues = validate_markdown_format(content)

        self.assertFalse(is_valid)
        self.assertTrue(any("title" in i for i in issues))

    def test_h1_in_body(self):
        """本文にH1見出しがある場合"""
        from normalizer.validators.format import validate_markdown_format

        content = """---
title: Test
normalized: true
---

# This is H1

## This is H2
"""
        is_valid, issues = validate_markdown_format(content)

        self.assertFalse(is_valid)
        self.assertTrue(any("レベル1" in i for i in issues))

    def test_consecutive_blank_lines(self):
        """3行以上の連続空行がある場合"""
        from normalizer.validators.format import validate_markdown_format

        content = """---
title: Test
normalized: true
---

## Content



Too many blank lines above.
"""
        is_valid, issues = validate_markdown_format(content)

        self.assertFalse(is_valid)
        self.assertTrue(any("空行" in i for i in issues))

    def test_wrong_bullet_markers(self):
        """*や+で始まる箇条書きがある場合"""
        from normalizer.validators.format import validate_markdown_format

        content = """---
title: Test
normalized: true
---

## List

* Item with asterisk
+ Item with plus
"""
        is_valid, issues = validate_markdown_format(content)

        self.assertFalse(is_valid)
        self.assertTrue(any("箇条書き" in i for i in issues))


class TestValidateTitle(unittest.TestCase):
    """validate_title 関数のテスト"""

    def test_valid_title(self):
        """有効なタイトル"""
        from normalizer.validators.title import validate_title

        is_valid, issues = validate_title("Valid Title")
        self.assertTrue(is_valid)
        self.assertEqual(issues, [])

    def test_title_with_forbidden_chars(self):
        """禁止文字を含むタイトル"""
        from normalizer.validators.title import validate_title

        is_valid, issues = validate_title("Title: With Colon")
        # 禁止文字を含むため無効
        self.assertFalse(is_valid)
        self.assertTrue(any("禁止文字" in i for i in issues))

    def test_empty_title(self):
        """空のタイトル"""
        from normalizer.validators.title import validate_title

        is_valid, issues = validate_title("")
        self.assertFalse(is_valid)
        self.assertTrue(any("空" in i for i in issues))

    def test_title_too_long(self):
        """長すぎるタイトル"""
        from normalizer.validators.title import validate_title

        long_title = "A" * 250
        is_valid, issues = validate_title(long_title)
        self.assertFalse(is_valid)
        self.assertTrue(any("長すぎ" in i for i in issues))


class TestNormalizeTags(unittest.TestCase):
    """normalize_tags 関数のテスト"""

    def test_normalize_tags(self):
        """タグの正規化"""
        from normalizer.validators.tags import normalize_tags

        tags = ["  tag1  ", "TAG2", "tag1"]  # 重複、空白、大文字
        normalized = normalize_tags(tags)

        # 重複除去、トリム
        self.assertIn("tag1", normalized)
        self.assertIn("tag2", [t.lower() for t in normalized])
        # 重複が除去されている
        self.assertEqual(len([t for t in normalized if t.lower() == "tag1"]), 1)

    def test_empty_tags(self):
        """空のタグリスト"""
        from normalizer.validators.tags import normalize_tags

        normalized = normalize_tags([])
        self.assertEqual(normalized, [])


if __name__ == "__main__":
    unittest.main()
