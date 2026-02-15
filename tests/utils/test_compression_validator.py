"""Tests for compression_validator module.

Phase 3 RED tests: CompressionResult dataclass, get_threshold, validate_compression.
These tests verify:
- get_threshold returns correct threshold based on original size
- validate_compression returns CompressionResult with correct values
- Edge case handling (zero original size)
"""

from __future__ import annotations

import unittest


class TestGetThreshold(unittest.TestCase):
    """get_threshold: original_size -> threshold percentage."""

    def test_get_threshold_large(self):
        """10,000文字以上の場合、しきい値が10% (0.10) であること。

        FR-005: 10,000文字以上の会話は 10% の圧縮率しきい値を使用する
        """
        from obsidian_etl.utils.compression_validator import get_threshold

        # Boundary: exactly 10000
        self.assertEqual(get_threshold(10000), 0.10)

        # Above boundary
        self.assertEqual(get_threshold(15000), 0.10)
        self.assertEqual(get_threshold(100000), 0.10)

    def test_get_threshold_medium(self):
        """5,000〜9,999文字の場合、しきい値が15% (0.15) であること。

        FR-006: 5,000〜9,999文字の会話は 15% の圧縮率しきい値を使用する
        """
        from obsidian_etl.utils.compression_validator import get_threshold

        # Boundary: exactly 5000
        self.assertEqual(get_threshold(5000), 0.15)

        # Within range
        self.assertEqual(get_threshold(7500), 0.15)

        # Upper boundary: 9999
        self.assertEqual(get_threshold(9999), 0.15)

    def test_get_threshold_small(self):
        """5,000文字未満の場合、しきい値が20% (0.20) であること。

        FR-007: 5,000文字未満の会話は 20% の圧縮率しきい値を使用する
        """
        from obsidian_etl.utils.compression_validator import get_threshold

        # Upper boundary: 4999
        self.assertEqual(get_threshold(4999), 0.20)

        # Small values
        self.assertEqual(get_threshold(1000), 0.20)
        self.assertEqual(get_threshold(100), 0.20)
        self.assertEqual(get_threshold(1), 0.20)


class TestValidateCompression(unittest.TestCase):
    """validate_compression: content strings -> CompressionResult."""

    def test_validate_compression_valid(self):
        """圧縮率が基準を満たす場合、is_valid=True が返ること。

        Example: original=10000, body=1500 -> body_ratio=15% >= threshold=10%
        """
        from obsidian_etl.utils.compression_validator import (
            CompressionResult,
            validate_compression,
        )

        # 10000 chars original, 1500 body (15% ratio) >= 10% threshold
        original_content = "a" * 10000
        output_content = "b" * 2000  # includes frontmatter
        body_content = "c" * 1500  # 15% of original

        result = validate_compression(
            original_content=original_content,
            output_content=output_content,
            body_content=body_content,
            node_name="extract_knowledge",
        )

        self.assertIsInstance(result, CompressionResult)
        self.assertEqual(result.original_size, 10000)
        self.assertEqual(result.output_size, 2000)
        self.assertEqual(result.body_size, 1500)
        self.assertAlmostEqual(result.ratio, 0.20, places=2)  # 2000/10000
        self.assertAlmostEqual(result.body_ratio, 0.15, places=2)  # 1500/10000
        self.assertAlmostEqual(result.threshold, 0.10, places=2)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.node_name, "extract_knowledge")

    def test_validate_compression_invalid(self):
        """圧縮率が基準を満たさない場合、is_valid=False が返ること。

        Example: original=10000, body=500 -> body_ratio=5% < threshold=10%
        """
        from obsidian_etl.utils.compression_validator import (
            CompressionResult,
            validate_compression,
        )

        # 10000 chars original, 500 body (5% ratio) < 10% threshold
        original_content = "a" * 10000
        output_content = "b" * 800  # includes frontmatter
        body_content = "c" * 500  # Only 5% of original

        result = validate_compression(
            original_content=original_content,
            output_content=output_content,
            body_content=body_content,
            node_name="extract_knowledge",
        )

        self.assertIsInstance(result, CompressionResult)
        self.assertEqual(result.original_size, 10000)
        self.assertEqual(result.output_size, 800)
        self.assertEqual(result.body_size, 500)
        self.assertAlmostEqual(result.ratio, 0.08, places=2)  # 800/10000
        self.assertAlmostEqual(result.body_ratio, 0.05, places=2)  # 500/10000
        self.assertAlmostEqual(result.threshold, 0.10, places=2)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.node_name, "extract_knowledge")

    def test_validate_compression_zero_original(self):
        """original_size が 0 の場合、is_valid=True が返ること（ゼロ除算回避）。

        Edge case: empty original content should not cause error.
        """
        from obsidian_etl.utils.compression_validator import (
            CompressionResult,
            validate_compression,
        )

        # Empty original
        original_content = ""
        output_content = "some output"
        body_content = "some body"

        result = validate_compression(
            original_content=original_content,
            output_content=output_content,
            body_content=body_content,
            node_name="extract_knowledge",
        )

        self.assertIsInstance(result, CompressionResult)
        self.assertEqual(result.original_size, 0)
        self.assertEqual(result.output_size, 11)  # len("some output")
        self.assertEqual(result.body_size, 9)  # len("some body")
        self.assertAlmostEqual(result.ratio, 1.0, places=2)
        self.assertAlmostEqual(result.body_ratio, 1.0, places=2)
        self.assertAlmostEqual(result.threshold, 0.0, places=2)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.node_name, "extract_knowledge")


class TestValidateCompressionBodyNone(unittest.TestCase):
    """validate_compression: body_content=None -> use output_size as body_size."""

    def test_validate_compression_body_none_uses_output(self):
        """body_content が None の場合、output_size が body_size として使用されること。"""
        from obsidian_etl.utils.compression_validator import (
            CompressionResult,
            validate_compression,
        )

        # 5000 chars original, 1000 output, body=None (uses output_size)
        original_content = "a" * 5000
        output_content = "b" * 1000  # 20% of original

        result = validate_compression(
            original_content=original_content,
            output_content=output_content,
            body_content=None,
            node_name="format_markdown",
        )

        self.assertIsInstance(result, CompressionResult)
        self.assertEqual(result.original_size, 5000)
        self.assertEqual(result.output_size, 1000)
        self.assertEqual(result.body_size, 1000)  # Uses output_size
        self.assertAlmostEqual(result.ratio, 0.20, places=2)
        self.assertAlmostEqual(result.body_ratio, 0.20, places=2)
        self.assertAlmostEqual(result.threshold, 0.15, places=2)
        self.assertTrue(result.is_valid)  # 20% >= 15%
        self.assertEqual(result.node_name, "format_markdown")


class TestCompressionResultDataclass(unittest.TestCase):
    """CompressionResult: dataclass with correct fields."""

    def test_compression_result_has_all_fields(self):
        """CompressionResult が必要なフィールドをすべて持つこと。"""
        from obsidian_etl.utils.compression_validator import CompressionResult

        result = CompressionResult(
            original_size=10000,
            output_size=1500,
            body_size=1200,
            ratio=0.15,
            body_ratio=0.12,
            threshold=0.10,
            is_valid=True,
            node_name="test_node",
        )

        self.assertEqual(result.original_size, 10000)
        self.assertEqual(result.output_size, 1500)
        self.assertEqual(result.body_size, 1200)
        self.assertAlmostEqual(result.ratio, 0.15, places=2)
        self.assertAlmostEqual(result.body_ratio, 0.12, places=2)
        self.assertAlmostEqual(result.threshold, 0.10, places=2)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.node_name, "test_node")

    def test_compression_result_is_dataclass(self):
        """CompressionResult が dataclass であること。"""
        from dataclasses import is_dataclass

        from obsidian_etl.utils.compression_validator import CompressionResult

        self.assertTrue(is_dataclass(CompressionResult))


# ============================================================
# Phase 2 RED Tests: Dynamic Min Characters Validation (052-improve-summary-quality)
# ============================================================


class TestMinCharactersValidation(unittest.TestCase):
    """min_output_chars: Validates minimum output character count.

    Tests for FR-002: システムは、まとめの最低文字数を動的に検証しなければならない
    （元の会話の20%以上 or 300文字以上のいずれか大きい方）

    This function should be added to compression_validator.py:
    - min_output_chars(original_size: int) -> int
    """

    def test_min_output_chars_small_conversation(self):
        """小さな会話では300文字が最低ライン。

        FR-002: min(original*0.2, 300) の大きい方を返す

        Example: original=500 -> 500*0.2=100 < 300 -> min=300
        """
        from obsidian_etl.utils.compression_validator import min_output_chars

        # 500 chars * 0.2 = 100, but 300 is larger
        self.assertEqual(min_output_chars(500), 300)

        # 1000 chars * 0.2 = 200, but 300 is larger
        self.assertEqual(min_output_chars(1000), 300)

        # 1500 chars * 0.2 = 300, equal to minimum
        self.assertEqual(min_output_chars(1500), 300)

    def test_min_output_chars_large_conversation(self):
        """大きな会話では20%が最低ライン。

        FR-002: min(original*0.2, 300) の大きい方を返す

        Example: original=2000 -> 2000*0.2=400 > 300 -> min=400
        """
        from obsidian_etl.utils.compression_validator import min_output_chars

        # 2000 chars * 0.2 = 400 > 300
        self.assertEqual(min_output_chars(2000), 400)

        # 5000 chars * 0.2 = 1000 > 300
        self.assertEqual(min_output_chars(5000), 1000)

        # 10000 chars * 0.2 = 2000 > 300
        self.assertEqual(min_output_chars(10000), 2000)

    def test_min_output_chars_boundary(self):
        """境界値でのテスト。

        1500 chars -> 1500*0.2 = 300 = minimum (boundary)
        """
        from obsidian_etl.utils.compression_validator import min_output_chars

        # Exactly at boundary: 1500 * 0.2 = 300
        self.assertEqual(min_output_chars(1500), 300)

        # Just below boundary: 1499 * 0.2 = 299.8 < 300
        self.assertEqual(min_output_chars(1499), 300)

        # Just above boundary: 1501 * 0.2 = 300.2 > 300
        self.assertEqual(min_output_chars(1501), 300)  # rounds to int

    def test_min_output_chars_zero_original(self):
        """元の会話が空の場合、0を返す。

        Edge case: 空の会話に対してはしきい値なし
        """
        from obsidian_etl.utils.compression_validator import min_output_chars

        self.assertEqual(min_output_chars(0), 0)


class TestShortConversationThreshold(unittest.TestCase):
    """get_threshold: Short conversation (<1000 chars) threshold relaxation.

    Tests for Edge Case: 元の会話が極端に短い場合（1,000 文字未満）、圧縮率のしきい値を緩和する

    Current behavior:
    - <5000 chars -> 20%

    Expected new behavior:
    - <1000 chars -> 30% (relaxed)
    - 1000-4999 chars -> 20% (current)
    """

    def test_get_threshold_very_short_relaxed(self):
        """1,000文字未満の場合、しきい値が30% (0.30) に緩和されること。

        Edge Case: 短い会話では圧縮率のしきい値を緩和する

        Expected: <1000 chars -> 0.30 (30%)
        """
        from obsidian_etl.utils.compression_validator import get_threshold

        # Very short conversations should have relaxed threshold
        self.assertEqual(get_threshold(999), 0.30)
        self.assertEqual(get_threshold(500), 0.30)
        self.assertEqual(get_threshold(100), 0.30)
        self.assertEqual(get_threshold(1), 0.30)

    def test_get_threshold_boundary_1000(self):
        """1,000文字ちょうどの場合、しきい値が20% (0.20) であること。

        Boundary: exactly 1000 chars -> 0.20 (not relaxed)
        """
        from obsidian_etl.utils.compression_validator import get_threshold

        # Exactly 1000 should use normal threshold
        self.assertEqual(get_threshold(1000), 0.20)

        # Above 1000 should also use normal threshold
        self.assertEqual(get_threshold(1001), 0.20)

    def test_get_threshold_maintains_existing_behavior(self):
        """既存のしきい値が維持されること（1000文字以上）。

        Verify existing thresholds are not changed:
        - 5000-9999 chars -> 15%
        - 10000+ chars -> 10%
        """
        from obsidian_etl.utils.compression_validator import get_threshold

        # Medium conversations: 15%
        self.assertEqual(get_threshold(5000), 0.15)
        self.assertEqual(get_threshold(7500), 0.15)

        # Large conversations: 10%
        self.assertEqual(get_threshold(10000), 0.10)
        self.assertEqual(get_threshold(20000), 0.10)


if __name__ == "__main__":
    unittest.main()
