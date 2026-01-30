"""
Format Validator - Markdown形式検証

Obsidian規約へのMarkdown形式準拠チェックを行う。
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def _extract_frontmatter(content: str) -> tuple[str | None, str]:
    """frontmatterと本文を分離

    Returns:
        (frontmatter, body) - frontmatterがない場合はNone
    """
    if not content.startswith("---"):
        return None, content

    # 2番目の---を探す
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return None, content

    frontmatter = content[3:end_idx].strip()
    body = content[end_idx + 3:].strip()

    return frontmatter, body


def validate_markdown_format(content: str) -> tuple[bool, list[str]]:
    """Markdown形式の検証

    Obsidian規約への準拠チェック:
    - 見出しが##から開始（#レベル1がない）
    - 連続空行がない（3行以上の連続空行）
    - 箇条書きが-で統一（*や+がない）
    - frontmatterが正しい形式

    Returns:
        (is_valid, issues) - 有効かどうかと問題点のリスト
    """
    issues = []

    # frontmatterと本文を分離
    fm, body = _extract_frontmatter(content)

    # 1. frontmatter検証
    if not fm:
        issues.append("frontmatterがありません")
    else:
        # 必須フィールドチェック
        if "title:" not in fm:
            issues.append("frontmatter: titleフィールドがありません")

    # 2. 見出しレベル検証（本文のみ）
    if body:
        # レベル1見出し（# で始まる行）を検出
        h1_pattern = re.compile(r"^#\s+", re.MULTILINE)
        if h1_pattern.search(body):
            issues.append("見出し: レベル1(#)が含まれています（##から開始すべき）")

    # 3. 連続空行検証
    if re.search(r"\n{3,}", content):
        issues.append("空行: 3行以上の連続空行があります")

    # 4. 箇条書き記号検証（本文のみ）
    if body:
        # * または + で始まる箇条書きを検出
        bullet_pattern = re.compile(r"^\s*[*+]\s+", re.MULTILINE)
        if bullet_pattern.search(body):
            issues.append("箇条書き: *または+が使用されています（-に統一すべき）")

    return len(issues) == 0, issues


def log_format_quality(
    filename: str,
    content: str,
    is_valid: bool,
    issues: list[str],
    session_dir: Path | None = None
) -> tuple[bool, list[str]]:
    """フォーマット品質をログに記録

    Args:
        filename: ファイル名
        content: コンテンツ
        is_valid: 有効かどうか
        issues: 問題点リスト
        session_dir: セッションディレクトリ（ログ保存先）

    Returns:
        (is_valid, issues)
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "filename": filename,
        "content_length": len(content),
        "is_valid": is_valid,
        "issues": issues
    }

    # セッションディレクトリにログを追記
    try:
        if session_dir and session_dir.exists():
            log_path = session_dir / "format_quality.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # ログ失敗は無視

    return is_valid, issues
