"""
test_english.py - 英語文書検出モジュールのテスト

normalizer.detection.english モジュールの関数をテスト
"""
from __future__ import annotations

import unittest

from normalizer.tests import read_fixture


class TestCountEnglishChars(unittest.TestCase):
    """count_english_chars 関数のテスト"""

    def test_all_english(self):
        """全て英語の文字列"""
        from normalizer.detection.english import count_english_chars

        count = count_english_chars("Hello World")
        # スペースは含まない（英字のみ）
        self.assertEqual(count, 10)

    def test_mixed_with_japanese(self):
        """日本語混じりの文字列"""
        from normalizer.detection.english import count_english_chars

        count = count_english_chars("Hello 世界")
        self.assertEqual(count, 5)  # "Hello" の 5 文字

    def test_no_english(self):
        """英語を含まない文字列"""
        from normalizer.detection.english import count_english_chars

        count = count_english_chars("日本語のみ")
        self.assertEqual(count, 0)


class TestCountTotalLetters(unittest.TestCase):
    """count_total_letters 関数のテスト"""

    def test_english_only(self):
        """英語のみ"""
        from normalizer.detection.english import count_total_letters

        count = count_total_letters("Hello")
        self.assertEqual(count, 5)

    def test_japanese_only(self):
        """日本語のみ"""
        from normalizer.detection.english import count_total_letters

        count = count_total_letters("日本語")
        self.assertEqual(count, 3)

    def test_mixed(self):
        """混合"""
        from normalizer.detection.english import count_total_letters

        count = count_total_letters("Hello日本語World")
        self.assertEqual(count, 5 + 3 + 5)  # Hello + 日本語 + World

    def test_with_symbols_and_spaces(self):
        """記号とスペースは除外"""
        from normalizer.detection.english import count_total_letters

        count = count_total_letters("Hello, World! 123")
        # カンマ、感嘆符、スペース、数字は除外
        self.assertEqual(count, 10)  # HelloWorld


class TestIsCompleteEnglishDocument(unittest.TestCase):
    """is_complete_english_document 関数のテスト"""

    def test_english_document_fixture(self):
        """英語ドキュメントフィクスチャ"""
        from normalizer.detection.english import is_complete_english_document

        content = read_fixture("english_doc.md")
        is_english, score, details = is_complete_english_document(content)

        # 英語比率が高い
        self.assertGreater(details["english_ratio"], 0.8)

    def test_japanese_document_fixture(self):
        """日本語ドキュメントフィクスチャ"""
        from normalizer.detection.english import is_complete_english_document

        content = read_fixture("japanese_doc.md")
        is_english, score, details = is_complete_english_document(content)

        # 英語比率が低い
        self.assertFalse(is_english)
        self.assertLess(details["english_ratio"], 0.5)

    def test_mixed_content_fixture(self):
        """混合コンテンツフィクスチャ"""
        from normalizer.detection.english import is_complete_english_document

        content = read_fixture("mixed_content.md")
        is_english, score, details = is_complete_english_document(content)

        # 混合なので英語比率は中間
        self.assertGreater(details["english_ratio"], 0.3)
        self.assertLess(details["english_ratio"], 0.9)

    def test_empty_content(self):
        """空コンテンツ"""
        from normalizer.detection.english import is_complete_english_document

        is_english, score, details = is_complete_english_document("")

        self.assertFalse(is_english)
        self.assertEqual(score, 0.0)

    def test_short_english_text(self):
        """短い英語テキスト（500文字未満）"""
        from normalizer.detection.english import is_complete_english_document

        content = "# Short\n\nThis is short."
        is_english, score, details = is_complete_english_document(content)

        # 長さスコアが低い
        self.assertLess(details["length_score"], 0.3)

    def test_long_english_document(self):
        """長い英語ドキュメント"""
        from normalizer.detection.english import is_complete_english_document

        content = """# English Document

This is a long English document with multiple sections and headings.
It contains a lot of English text to ensure the document length score is maximized.

## Section One

Here is the first section with detailed content about programming concepts.
We discuss various topics including software architecture and design patterns.

## Section Two

The second section continues with more technical content about development.
This ensures we have enough heading structure for the heading score.

## Section Three

Finally, we conclude with additional content to reach the required length.
The total character count should exceed 500 characters for full length score.
"""
        is_english, score, details = is_complete_english_document(content)

        self.assertTrue(is_english)
        self.assertGreaterEqual(score, 0.7)

    def test_heading_detection(self):
        """見出し検出"""
        from normalizer.detection.english import is_complete_english_document

        content = """# Heading One

## Heading Two

### Heading Three
"""
        is_english, score, details = is_complete_english_document(content)

        self.assertEqual(details["heading_count"], 3)


class TestLogEnglishDetection(unittest.TestCase):
    """log_english_detection 関数のテスト"""

    def test_log_without_session(self):
        """セッションなしでのログ（エラーにならない）"""
        from normalizer.detection.english import log_english_detection

        # エラーなく実行されることを確認
        log_english_detection(
            filename="test.md",
            is_english=True,
            score=0.85,
            details={"length": 1000},
            session_dir=None
        )


if __name__ == "__main__":
    unittest.main()
