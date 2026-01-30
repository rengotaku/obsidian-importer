"""
Title Validator - タイトル検証

タイトルの品質検証とログ記録を行う。
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# =============================================================================
# Title Validation
# =============================================================================


def validate_title(title: str) -> tuple[bool, list[str]]:
    """タイトルの品質を検証

    Returns:
        (is_valid, issues) - 有効かどうかと問題点のリスト
    """
    issues = []

    if not title or not title.strip():
        issues.append("タイトルが空です")
        return False, issues

    # ファイルシステム禁止文字チェック
    illegal_chars = '<>:"/\\|?*'
    found_illegal = [c for c in illegal_chars if c in title]
    if found_illegal:
        issues.append(f"禁止文字を含んでいます: {found_illegal}")

    # 長さチェック
    if len(title) > 200:
        issues.append(f"タイトルが長すぎます: {len(title)}文字 (上限200)")

    # 曖昧なタイトルチェック
    vague_titles = {"メモ", "ノート", "note", "memo", "test", "テスト", "untitled"}
    if title.lower().strip() in vague_titles:
        issues.append(f"曖昧なタイトル: {title}")

    # 日付プレフィックスのみチェック
    if re.match(r'^\d{4}[-_]\d{2}[-_]\d{2}$', title.strip()):
        issues.append("日付のみのタイトル")

    return len(issues) == 0, issues


def log_title_quality(
    original_filename: str,
    generated_title: str,
    result_path: Path | None = None,
    session_dir: Path | None = None
) -> tuple[bool, list[str]]:
    """タイトル品質をログに記録

    Args:
        original_filename: 元のファイル名
        generated_title: 生成されたタイトル
        result_path: 結果パス（未使用、互換性のため）
        session_dir: セッションディレクトリ（ログ保存先）

    Returns:
        (is_valid, issues)
    """
    is_valid, issues = validate_title(generated_title)

    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "original_filename": original_filename,
        "generated_title": generated_title,
        "is_valid": is_valid,
        "issues": issues
    }

    # セッションディレクトリにログを追記
    try:
        if session_dir and session_dir.exists():
            log_path = session_dir / "title_quality.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # ログ失敗は無視

    return is_valid, issues
