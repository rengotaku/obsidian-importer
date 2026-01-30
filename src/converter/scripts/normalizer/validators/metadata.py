"""
Metadata Validators - サマリーと関連ノートの検証

Stage C (メタデータ生成) の出力検証を行う。
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# =============================================================================
# Summary Validation
# =============================================================================

MAX_SUMMARY_LENGTH = 200

# 禁止パターン（会話経緯の説明）
FORBIDDEN_SUMMARY_PATTERNS = [
    r"The user asked",
    r"Claude provided",
    r"Claude said",
    r"Claude explained",
    r"ユーザーが質問した",
    r"Claudeが回答した",
    r"Claudeが説明した",
    r"会話では",
    r"このセッションでは",
]


def validate_summary(summary: str) -> tuple[bool, list[str]]:
    """
    サマリーの検証

    Args:
        summary: 検証対象のサマリー文字列

    Returns:
        tuple: (is_valid, issues)
            - is_valid: 検証結果
            - issues: 問題点のリスト
    """
    issues = []

    # 空チェック
    if not summary or not summary.strip():
        issues.append("サマリーが空です")
        return False, issues

    # 長さチェック
    if len(summary) > MAX_SUMMARY_LENGTH:
        issues.append(f"サマリーが{MAX_SUMMARY_LENGTH}文字を超えています（{len(summary)}文字）")

    # 禁止パターンチェック
    for pattern in FORBIDDEN_SUMMARY_PATTERNS:
        if re.search(pattern, summary, re.IGNORECASE):
            issues.append(f"禁止パターンが含まれています: {pattern}")

    is_valid = len(issues) == 0
    return is_valid, issues


def truncate_summary(summary: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
    """
    サマリーを指定文字数で切り詰め

    Args:
        summary: 元のサマリー
        max_length: 最大文字数

    Returns:
        切り詰められたサマリー
    """
    if len(summary) <= max_length:
        return summary
    return summary[:max_length]


# =============================================================================
# Related Notes Validation
# =============================================================================

# 内部リンク形式の正規表現
INTERNAL_LINK_PATTERN = re.compile(r'^\[\[.+\]\]$')


def validate_related(related: list[str]) -> tuple[bool, list[str]]:
    """
    関連ノートリストの検証

    Args:
        related: 検証対象の関連ノートリスト

    Returns:
        tuple: (is_valid, issues)
            - is_valid: 検証結果
            - issues: 問題点のリスト
    """
    issues = []

    # リスト型チェック
    if not isinstance(related, list):
        issues.append("関連ノートがリスト形式ではありません")
        return False, issues

    # 最大件数チェック
    if len(related) > 5:
        issues.append(f"関連ノートが5件を超えています（{len(related)}件）")

    # 各要素の形式チェック
    for i, item in enumerate(related):
        if not isinstance(item, str):
            issues.append(f"関連ノート[{i}]が文字列ではありません")
            continue
        if not INTERNAL_LINK_PATTERN.match(item):
            issues.append(f"関連ノート[{i}]が内部リンク形式ではありません: {item}")

    is_valid = len(issues) == 0
    return is_valid, issues


def normalize_related(related: list) -> list[str]:
    """
    関連ノートリストを正規化

    様々な形式を [[xxx]] 形式に統一
    ネストされたリストや余分な括弧にも対応
    .md 拡張子は自動的に削除

    Args:
        related: 元の関連ノートリスト

    Returns:
        正規化された関連ノートリスト
    """
    if not isinstance(related, list):
        return []

    def extract_name(item) -> str | None:
        """要素から名前を抽出（ネストされたリストにも対応）"""
        # リストの場合: 再帰的に最初の要素を取得
        while isinstance(item, list):
            if not item:
                return None
            item = item[0]

        if not isinstance(item, str) or not item:
            return None

        # 全ての [ ] を除去して名前を抽出
        name = item.replace("[", "").replace("]", "")

        # .md 拡張子を除去
        if name.endswith(".md"):
            name = name[:-3]

        return name.strip() if name.strip() else None

    normalized = []
    for item in related[:5]:  # 最大5件
        name = extract_name(item)
        if name:
            normalized.append(f"[[{name}]]")

    return normalized


# =============================================================================
# Created Date Validation
# =============================================================================

# YYYY-MM-DD 形式の正規表現
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_created(created) -> str:
    """
    作成日を正規化

    YYYY-MM-DD 形式のみ許可、それ以外は空文字を返す

    Args:
        created: 作成日（任意の型）

    Returns:
        正規化された作成日（YYYY-MM-DD形式）または空文字
    """
    if not isinstance(created, str) or not created:
        return ""

    if DATE_PATTERN.match(created):
        return created

    return ""
