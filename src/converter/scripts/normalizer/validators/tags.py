"""
Tag Validator - タグ検証・正規化

タグの品質検証、一貫性計算、正規化を行う。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.config import TAG_DICTIONARY_PATH


# =============================================================================
# Tag Dictionary Loading
# =============================================================================


def load_tag_dictionary() -> dict:
    """タグ辞書をJSONから読み込み"""
    try:
        if TAG_DICTIONARY_PATH.exists():
            with open(TAG_DICTIONARY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def get_all_known_tags() -> set[str]:
    """タグ辞書から全既知タグを取得"""
    tag_dict = load_tag_dictionary()
    known_tags = set()

    for category in ["languages", "infrastructure", "tools", "concepts", "lifestyle"]:
        tags = tag_dict.get(category, [])
        known_tags.update(t.lower() for t in tags)

    return known_tags


# =============================================================================
# Tag Validation
# =============================================================================


def validate_tags(tags: list[str]) -> tuple[bool, list[str]]:
    """タグの品質を検証

    FR-003: 3〜5個の適切なタグ

    Returns:
        (is_valid, issues) - 有効かどうかと問題点のリスト
    """
    issues = []

    if not tags:
        issues.append("タグがありません")
        return False, issues

    # 個数チェック (3-5個)
    if len(tags) < 3:
        issues.append(f"タグが少なすぎます: {len(tags)}個 (推奨3-5個)")
    elif len(tags) > 5:
        issues.append(f"タグが多すぎます: {len(tags)}個 (推奨3-5個)")

    # 各タグの検証
    for tag in tags:
        if not tag or not tag.strip():
            issues.append("空のタグがあります")
        elif len(tag) > 50:
            issues.append(f"タグが長すぎます: {tag[:20]}... ({len(tag)}文字)")

    return len(issues) == 0, issues


def calculate_tag_consistency(tags: list[str]) -> tuple[float, list[str], list[str]]:
    """タグの一貫性を計算

    Returns:
        (consistency_rate, matched_tags, unmatched_tags)
    """
    if not tags:
        return 0.0, [], []

    known_tags = get_all_known_tags()
    matched = []
    unmatched = []

    for tag in tags:
        tag_lower = tag.lower().strip()
        if tag_lower in known_tags:
            matched.append(tag)
        else:
            # 部分一致もチェック
            partial_match = any(
                tag_lower in known or known in tag_lower
                for known in known_tags
            )
            if partial_match:
                matched.append(tag)
            else:
                unmatched.append(tag)

    total = len(tags)
    rate = len(matched) / total if total > 0 else 0.0

    return rate, matched, unmatched


def normalize_tags(tags: list[str]) -> list[str]:
    """タグを正規化（重複除去、空白トリム）"""
    seen = set()
    result = []

    for tag in tags:
        if not tag:
            continue
        normalized = tag.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(tag.strip())  # 元の大文字小文字を保持

    return result[:5]  # 最大5個


def log_tag_quality(
    original_filename: str,
    tags: list[str],
    consistency_rate: float,
    matched: list[str],
    unmatched: list[str],
    session_dir: Path | None = None
) -> tuple[bool, list[str], float]:
    """タグ品質をログに記録

    Args:
        original_filename: 元のファイル名
        tags: タグリスト
        consistency_rate: 一貫性率
        matched: マッチしたタグ
        unmatched: マッチしなかったタグ
        session_dir: セッションディレクトリ（ログ保存先）

    Returns:
        (is_valid, issues, consistency_rate)
    """
    is_valid, issues = validate_tags(tags)

    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "original_filename": original_filename,
        "tags": tags,
        "tag_count": len(tags),
        "is_valid": is_valid,
        "issues": issues,
        "consistency_rate": round(consistency_rate, 2),
        "matched_tags": matched,
        "unmatched_tags": unmatched
    }

    # セッションディレクトリにログを追記
    try:
        if session_dir and session_dir.exists():
            log_path = session_dir / "tag_quality.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # ログ失敗は無視

    return is_valid, issues, consistency_rate


def format_tag_dictionary(tag_dict: dict) -> str:
    """タグ辞書をプロンプト用にフォーマット"""
    if not tag_dict:
        return "(タグ辞書未生成)"

    lines = []
    categories = [
        ("languages", "言語・フレームワーク"),
        ("infrastructure", "インフラ"),
        ("tools", "ツール"),
        ("concepts", "概念"),
        ("lifestyle", "日常")
    ]

    for key, label in categories:
        tags = tag_dict.get(key, [])
        if tags:
            sample = ", ".join(tags[:10])
            if len(tags) > 10:
                sample += f" ... (他{len(tags)-10}件)"
            lines.append(f"- {label}: {sample}")

    return "\n".join(lines) if lines else "(タグ辞書未生成)"
