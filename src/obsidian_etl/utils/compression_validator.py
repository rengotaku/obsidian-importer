"""圧縮率検証ユーティリティ

This module provides compression ratio validation for transform pipeline nodes.
Used by extract_knowledge and format_markdown to detect over-compressed content.

Usage:
    from obsidian_etl.utils.compression_validator import validate_compression

    result = validate_compression(
        original_content=conversation_text,
        output_content=markdown_output,
        body_content=body_only,
        node_name="extract_knowledge",
    )

    if not result.is_valid:
        logger.warning(
            f"{result.node_name}: body_ratio={result.body_ratio:.1%} < threshold={result.threshold:.1%}"
        )
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompressionResult:
    """圧縮率検証結果

    Attributes:
        original_size: 元コンテンツのサイズ (文字数)
        output_size: 出力コンテンツのサイズ (文字数、frontmatter 含む)
        body_size: 出力コンテンツの本文サイズ (文字数、frontmatter 除く)
        ratio: 出力/元のサイズ比 (output_size / original_size)
        body_ratio: 本文/元のサイズ比 (body_size / original_size)
        threshold: 適用されたしきい値
        is_valid: 圧縮率が基準を満たすか
        node_name: 処理ノード名
    """

    original_size: int
    output_size: int
    body_size: int
    ratio: float
    body_ratio: float
    threshold: float
    is_valid: bool
    node_name: str


def get_threshold(original_size: int) -> float:
    """元サイズに応じたしきい値を返す

    Args:
        original_size: 元コンテンツのサイズ (文字数)

    Returns:
        しきい値 (0.0-1.0 の float)
            - 10,000文字以上: 0.10 (10%)
            - 5,000-9,999文字: 0.15 (15%)
            - 5,000文字未満: 0.20 (20%)

    Examples:
        >>> get_threshold(10000)
        0.10
        >>> get_threshold(5000)
        0.15
        >>> get_threshold(4999)
        0.20
    """
    if original_size >= 10000:
        return 0.10  # 10%
    elif original_size >= 5000:
        return 0.15  # 15%
    else:
        return 0.20  # 20%


def validate_compression(
    original_content: str,
    output_content: str,
    body_content: str | None,
    node_name: str,
) -> CompressionResult:
    """圧縮率を検証

    Args:
        original_content: 元コンテンツ
        output_content: 出力コンテンツ (frontmatter 含む)
        body_content: 出力コンテンツの本文 (frontmatter 除く)。None の場合は output_content を使用
        node_name: 処理ノード名

    Returns:
        CompressionResult: 検証結果

    Examples:
        >>> result = validate_compression(
        ...     original_content="a" * 10000,
        ...     output_content="b" * 2000,
        ...     body_content="c" * 1500,
        ...     node_name="extract_knowledge",
        ... )
        >>> result.is_valid
        True
        >>> result.body_ratio
        0.15
    """
    original_size = len(original_content)
    output_size = len(output_content)
    body_size = len(body_content) if body_content else output_size

    # Edge case: 空の元コンテンツ（ゼロ除算回避）
    if original_size == 0:
        return CompressionResult(
            original_size=0,
            output_size=output_size,
            body_size=body_size,
            ratio=1.0,
            body_ratio=1.0,
            threshold=0.0,
            is_valid=True,
            node_name=node_name,
        )

    # 圧縮率計算
    ratio = output_size / original_size
    body_ratio = body_size / original_size
    threshold = get_threshold(original_size)
    is_valid = body_ratio >= threshold

    return CompressionResult(
        original_size=original_size,
        output_size=output_size,
        body_size=body_size,
        ratio=ratio,
        body_ratio=body_ratio,
        threshold=threshold,
        is_valid=is_valid,
        node_name=node_name,
    )
