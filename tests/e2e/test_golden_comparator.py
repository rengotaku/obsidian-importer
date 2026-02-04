"""Tests for golden_comparator.py - E2E output validation via golden file comparison.

Phase 2 RED tests: split_frontmatter_and_body, calculate_frontmatter_similarity,
calculate_body_similarity, calculate_total_score, compare_directories.

These tests verify:
- Markdown frontmatter/body separation (YAML delimiters)
- Frontmatter similarity (key existence, file_id exact match, title/tags similarity)
- Body text similarity via difflib (exact, near-match, divergent)
- Total score calculation (frontmatter * 0.3 + body * 0.7)
- Directory comparison (file count match/mismatch, golden missing)
- Failure report (filename, score, missing_keys, diff_summary)
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from tests.e2e.golden_comparator import (
    calculate_body_similarity,
    calculate_frontmatter_similarity,
    calculate_total_score,
    compare_directories,
    split_frontmatter_and_body,
)

# ---------------------------------------------------------------------------
# Helper: sample Markdown content
# ---------------------------------------------------------------------------

SAMPLE_GOLDEN = """\
---
title: Python asyncio discussion
created: 2026-01-15
tags:
  - python
  - asyncio
source_provider: claude
file_id: a1b2c3d4e5f6
normalized: true
---

## Summary

asyncio is a library for writing concurrent code using async/await syntax.

This conversation covers the basics of Python asyncio including event loops,
coroutines, and tasks.
"""

SAMPLE_ACTUAL_IDENTICAL = SAMPLE_GOLDEN

SAMPLE_ACTUAL_MINOR_DIFF = """\
---
title: Python asyncio discussion
created: 2026-01-15
tags:
  - python
  - asyncio
source_provider: claude
file_id: a1b2c3d4e5f6
normalized: true
---

## Summary

asyncio is a library for writing concurrent code with the async/await pattern.

This conversation covers the fundamentals of Python asyncio including event loops,
coroutines, and tasks.
"""

SAMPLE_ACTUAL_MAJOR_DIFF = """\
---
title: Completely different topic
created: 2026-01-15
tags:
  - javascript
  - react
source_provider: claude
file_id: ffffffffffffffff
normalized: true
---

## Summary

React is a JavaScript library for building user interfaces.

This article explains component-based architecture and virtual DOM rendering.
"""

SAMPLE_MISSING_KEYS = """\
---
title: Python asyncio discussion
created: 2026-01-15
source_provider: claude
normalized: true
---

## Summary

asyncio is a library for writing concurrent code using async/await syntax.
"""


# ===========================================================================
# T008: test_split_frontmatter_and_body
# ===========================================================================


class TestSplitFrontmatterAndBody(unittest.TestCase):
    """frontmatter と body の分離テスト"""

    def test_normal_markdown(self):
        """正常な Markdown を frontmatter と body に分離できる"""
        frontmatter, body = split_frontmatter_and_body(SAMPLE_GOLDEN)
        self.assertIn("title", frontmatter)
        self.assertEqual(frontmatter["title"], "Python asyncio discussion")
        self.assertIn("tags", frontmatter)
        self.assertIsInstance(frontmatter["tags"], list)
        self.assertIn("python", frontmatter["tags"])
        self.assertIn("## Summary", body)

    def test_no_frontmatter(self):
        """frontmatter がない場合は空辞書と全体を body として返す"""
        content = "# Just a heading\n\nSome body text."
        frontmatter, body = split_frontmatter_and_body(content)
        self.assertEqual(frontmatter, {})
        self.assertIn("Just a heading", body)

    def test_empty_content(self):
        """空文字列の場合は空辞書と空文字列を返す"""
        frontmatter, body = split_frontmatter_and_body("")
        self.assertEqual(frontmatter, {})
        self.assertEqual(body, "")

    def test_frontmatter_keys_preserved(self):
        """frontmatter の全キーが保持される"""
        frontmatter, _ = split_frontmatter_and_body(SAMPLE_GOLDEN)
        expected_keys = {"title", "created", "tags", "source_provider", "file_id", "normalized"}
        self.assertEqual(set(frontmatter.keys()), expected_keys)

    def test_body_does_not_contain_frontmatter_delimiters(self):
        """body に frontmatter の --- デリミタが含まれない"""
        _, body = split_frontmatter_and_body(SAMPLE_GOLDEN)
        self.assertFalse(body.strip().startswith("---"))


# ===========================================================================
# T009: test_frontmatter_similarity
# ===========================================================================


class TestFrontmatterSimilarity(unittest.TestCase):
    """frontmatter 類似度計算テスト"""

    def test_identical_frontmatter(self):
        """同一の frontmatter はスコア 1.0"""
        golden_fm, _ = split_frontmatter_and_body(SAMPLE_GOLDEN)
        actual_fm, _ = split_frontmatter_and_body(SAMPLE_ACTUAL_IDENTICAL)
        score = calculate_frontmatter_similarity(actual_fm, golden_fm)
        self.assertAlmostEqual(score, 1.0)

    def test_file_id_mismatch_lowers_score(self):
        """file_id 不一致でスコアが下がる"""
        golden_fm, _ = split_frontmatter_and_body(SAMPLE_GOLDEN)
        actual_fm, _ = split_frontmatter_and_body(SAMPLE_ACTUAL_MAJOR_DIFF)
        score = calculate_frontmatter_similarity(actual_fm, golden_fm)
        self.assertLess(score, 1.0)

    def test_missing_keys_lower_score(self):
        """必須キーが欠落するとスコアが下がる"""
        golden_fm, _ = split_frontmatter_and_body(SAMPLE_GOLDEN)
        actual_fm, _ = split_frontmatter_and_body(SAMPLE_MISSING_KEYS)
        score = calculate_frontmatter_similarity(actual_fm, golden_fm)
        self.assertLess(score, 1.0)

    def test_score_between_zero_and_one(self):
        """スコアは 0.0 から 1.0 の範囲"""
        golden_fm, _ = split_frontmatter_and_body(SAMPLE_GOLDEN)
        actual_fm, _ = split_frontmatter_and_body(SAMPLE_ACTUAL_MAJOR_DIFF)
        score = calculate_frontmatter_similarity(actual_fm, golden_fm)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_similar_title_high_score(self):
        """title が類似していればスコアが高い"""
        golden_fm, _ = split_frontmatter_and_body(SAMPLE_GOLDEN)
        actual_fm, _ = split_frontmatter_and_body(SAMPLE_ACTUAL_MINOR_DIFF)
        score = calculate_frontmatter_similarity(actual_fm, golden_fm)
        self.assertGreater(score, 0.8)

    def test_empty_actual_frontmatter(self):
        """actual の frontmatter が空の場合はスコアが低い"""
        golden_fm, _ = split_frontmatter_and_body(SAMPLE_GOLDEN)
        score = calculate_frontmatter_similarity({}, golden_fm)
        self.assertLess(score, 0.5)


# ===========================================================================
# T010: test_body_similarity
# ===========================================================================


class TestBodySimilarity(unittest.TestCase):
    """body テキスト類似度計算テスト"""

    def test_identical_body(self):
        """同一テキストはスコア 1.0"""
        _, golden_body = split_frontmatter_and_body(SAMPLE_GOLDEN)
        _, actual_body = split_frontmatter_and_body(SAMPLE_ACTUAL_IDENTICAL)
        score = calculate_body_similarity(actual_body, golden_body)
        self.assertAlmostEqual(score, 1.0)

    def test_minor_diff_high_score(self):
        """微差は 0.9 以上"""
        _, golden_body = split_frontmatter_and_body(SAMPLE_GOLDEN)
        _, actual_body = split_frontmatter_and_body(SAMPLE_ACTUAL_MINOR_DIFF)
        score = calculate_body_similarity(actual_body, golden_body)
        self.assertGreaterEqual(score, 0.8)

    def test_major_diff_low_score(self):
        """大きく異なるテキストは 0.9 未満"""
        _, golden_body = split_frontmatter_and_body(SAMPLE_GOLDEN)
        _, actual_body = split_frontmatter_and_body(SAMPLE_ACTUAL_MAJOR_DIFF)
        score = calculate_body_similarity(actual_body, golden_body)
        self.assertLess(score, 0.9)

    def test_empty_body(self):
        """空テキスト同士は 1.0"""
        score = calculate_body_similarity("", "")
        self.assertAlmostEqual(score, 1.0)

    def test_one_empty_one_not(self):
        """一方が空、一方が非空は低スコア"""
        _, golden_body = split_frontmatter_and_body(SAMPLE_GOLDEN)
        score = calculate_body_similarity("", golden_body)
        self.assertLess(score, 0.5)

    def test_score_between_zero_and_one(self):
        """スコアは 0.0 から 1.0 の範囲"""
        _, golden_body = split_frontmatter_and_body(SAMPLE_GOLDEN)
        _, actual_body = split_frontmatter_and_body(SAMPLE_ACTUAL_MAJOR_DIFF)
        score = calculate_body_similarity(actual_body, golden_body)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_unicode_content(self):
        """Unicode テキスト(日本語)の類似度計算ができる"""
        body_a = "## 要約\n\nPythonの非同期処理について学びました。"
        body_b = "## 要約\n\nPythonの非同期処理について理解しました。"
        score = calculate_body_similarity(body_a, body_b)
        self.assertGreater(score, 0.8)


# ===========================================================================
# T011: test_total_score
# ===========================================================================


class TestTotalScore(unittest.TestCase):
    """総合スコア計算テスト (frontmatter * 0.3 + body * 0.7)"""

    def test_perfect_scores(self):
        """frontmatter=1.0, body=1.0 -> total=1.0"""
        score = calculate_total_score(1.0, 1.0)
        self.assertAlmostEqual(score, 1.0)

    def test_weighted_calculation(self):
        """加重平均の計算が正しい (0.3 * fm + 0.7 * body)"""
        score = calculate_total_score(0.5, 1.0)
        expected = 0.3 * 0.5 + 0.7 * 1.0  # 0.85
        self.assertAlmostEqual(score, expected)

    def test_zero_scores(self):
        """frontmatter=0.0, body=0.0 -> total=0.0"""
        score = calculate_total_score(0.0, 0.0)
        self.assertAlmostEqual(score, 0.0)

    def test_body_weighted_more(self):
        """body の重みが大きいことを確認"""
        score_high_body = calculate_total_score(0.5, 1.0)
        score_high_fm = calculate_total_score(1.0, 0.5)
        self.assertGreater(score_high_body, score_high_fm)

    def test_boundary_threshold(self):
        """閾値 0.9 付近の境界値テスト"""
        # frontmatter=0.8, body=0.95 -> 0.3*0.8 + 0.7*0.95 = 0.24 + 0.665 = 0.905
        score = calculate_total_score(0.8, 0.95)
        self.assertGreater(score, 0.9)

    def test_just_below_threshold(self):
        """閾値をぎりぎり下回るケース"""
        # frontmatter=0.5, body=0.9 -> 0.3*0.5 + 0.7*0.9 = 0.15 + 0.63 = 0.78
        score = calculate_total_score(0.5, 0.9)
        self.assertLess(score, 0.9)


# ===========================================================================
# T012: test_compare_directories
# ===========================================================================


class TestCompareDirectories(unittest.TestCase):
    """Directory comparison tests"""

    def setUp(self):
        """Create temporary directories for actual and golden files."""
        self.test_dir = tempfile.mkdtemp()
        self.actual_dir = os.path.join(self.test_dir, "actual")
        self.golden_dir = os.path.join(self.test_dir, "golden")
        os.makedirs(self.actual_dir)
        os.makedirs(self.golden_dir)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def _write_file(self, directory: str, filename: str, content: str) -> None:
        with open(os.path.join(directory, filename), "w", encoding="utf-8") as f:
            f.write(content)

    def test_identical_directories(self):
        """同一ファイルを持つディレクトリの比較は全て成功"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_GOLDEN)
        self._write_file(self.golden_dir, "file1.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["files"]), 1)
        self.assertAlmostEqual(result["files"][0]["total_score"], 1.0)

    def test_file_count_mismatch(self):
        """actual と golden でファイル数が異なる場合は失敗"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_GOLDEN)
        self._write_file(self.actual_dir, "file2.md", SAMPLE_GOLDEN)
        self._write_file(self.golden_dir, "file1.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        self.assertFalse(result["passed"])

    def test_golden_dir_not_exists(self):
        """golden ディレクトリが存在しない場合はエラー"""
        nonexistent = os.path.join(self.test_dir, "nonexistent")
        with self.assertRaises((FileNotFoundError, ValueError)):
            compare_directories(self.actual_dir, nonexistent, threshold=0.9)

    def test_golden_dir_empty(self):
        """golden ディレクトリが空の場合はエラー"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_GOLDEN)
        with self.assertRaises((FileNotFoundError, ValueError)):
            compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)

    def test_multiple_files_all_pass(self):
        """複数ファイルが全て閾値以上なら成功"""
        self._write_file(self.actual_dir, "a.md", SAMPLE_GOLDEN)
        self._write_file(self.actual_dir, "b.md", SAMPLE_GOLDEN)
        self._write_file(self.golden_dir, "a.md", SAMPLE_GOLDEN)
        self._write_file(self.golden_dir, "b.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["files"]), 2)

    def test_one_file_below_threshold(self):
        """1ファイルでも閾値を下回ればディレクトリ全体として失敗"""
        self._write_file(self.actual_dir, "good.md", SAMPLE_GOLDEN)
        self._write_file(self.actual_dir, "bad.md", SAMPLE_ACTUAL_MAJOR_DIFF)
        self._write_file(self.golden_dir, "good.md", SAMPLE_GOLDEN)
        self._write_file(self.golden_dir, "bad.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        self.assertFalse(result["passed"])

    def test_threshold_parameter(self):
        """閾値パラメータが正しく適用される"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_ACTUAL_MINOR_DIFF)
        self._write_file(self.golden_dir, "file1.md", SAMPLE_GOLDEN)
        # Low threshold should pass
        result_low = compare_directories(self.actual_dir, self.golden_dir, threshold=0.5)
        self.assertTrue(result_low["passed"])


# ===========================================================================
# T013: test_comparison_report
# ===========================================================================


class TestComparisonReport(unittest.TestCase):
    """Failure report tests: filename, score, missing_keys, diff_summary"""

    def setUp(self):
        """Create temporary directories for actual and golden files."""
        self.test_dir = tempfile.mkdtemp()
        self.actual_dir = os.path.join(self.test_dir, "actual")
        self.golden_dir = os.path.join(self.test_dir, "golden")
        os.makedirs(self.actual_dir)
        os.makedirs(self.golden_dir)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def _write_file(self, directory: str, filename: str, content: str) -> None:
        with open(os.path.join(directory, filename), "w", encoding="utf-8") as f:
            f.write(content)

    def test_report_contains_filename(self):
        """レポートにファイル名が含まれる"""
        self._write_file(self.actual_dir, "test_file.md", SAMPLE_ACTUAL_MAJOR_DIFF)
        self._write_file(self.golden_dir, "test_file.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        file_result = result["files"][0]
        self.assertEqual(file_result["filename"], "test_file.md")

    def test_report_contains_scores(self):
        """レポートに total_score, frontmatter_score, body_score が含まれる"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_ACTUAL_MINOR_DIFF)
        self._write_file(self.golden_dir, "file1.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        file_result = result["files"][0]
        self.assertIn("total_score", file_result)
        self.assertIn("frontmatter_score", file_result)
        self.assertIn("body_score", file_result)
        self.assertIsInstance(file_result["total_score"], float)
        self.assertIsInstance(file_result["frontmatter_score"], float)
        self.assertIsInstance(file_result["body_score"], float)

    def test_report_contains_missing_keys(self):
        """frontmatter キー欠落時に missing_keys が含まれる"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_MISSING_KEYS)
        self._write_file(self.golden_dir, "file1.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        file_result = result["files"][0]
        self.assertIn("missing_keys", file_result)
        missing = file_result["missing_keys"]
        self.assertIn("tags", missing)
        self.assertIn("file_id", missing)

    def test_report_contains_diff_summary(self):
        """レポートに diff_summary が含まれる"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_ACTUAL_MAJOR_DIFF)
        self._write_file(self.golden_dir, "file1.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        file_result = result["files"][0]
        self.assertIn("diff_summary", file_result)
        self.assertIsInstance(file_result["diff_summary"], str)
        self.assertGreater(len(file_result["diff_summary"]), 0)

    def test_passed_file_has_no_missing_keys(self):
        """成功ファイルの missing_keys は空リスト"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_GOLDEN)
        self._write_file(self.golden_dir, "file1.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        file_result = result["files"][0]
        self.assertEqual(file_result["missing_keys"], [])

    def test_report_overall_passed_flag(self):
        """レポートに全体の passed フラグが含まれる"""
        self._write_file(self.actual_dir, "file1.md", SAMPLE_GOLDEN)
        self._write_file(self.golden_dir, "file1.md", SAMPLE_GOLDEN)
        result = compare_directories(self.actual_dir, self.golden_dir, threshold=0.9)
        self.assertIn("passed", result)
        self.assertIsInstance(result["passed"], bool)


if __name__ == "__main__":
    unittest.main()
