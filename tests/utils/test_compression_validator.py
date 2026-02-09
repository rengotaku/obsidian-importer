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


if __name__ == "__main__":
    unittest.main()
