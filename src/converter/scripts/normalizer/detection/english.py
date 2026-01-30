"""
English Detection - 英語文書判定

文書が完全な英語文書かどうかを判定する。
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
# Character Counting
# =============================================================================


def count_english_chars(content: str) -> int:
    """英語文字（ASCII英字）の数をカウント"""
    return sum(1 for c in content if c.isascii() and c.isalpha())


def count_total_letters(content: str) -> int:
    """全文字（英字・日本語等）の数をカウント（空白・記号除く）"""
    count = 0
    for c in content:
        # 英字
        if c.isalpha():
            count += 1
        # 日本語（ひらがな、カタカナ、漢字）
        elif '\u3040' <= c <= '\u309f':  # ひらがな
            count += 1
        elif '\u30a0' <= c <= '\u30ff':  # カタカナ
            count += 1
        elif '\u4e00' <= c <= '\u9fff':  # CJK統合漢字
            count += 1
    return count


# =============================================================================
# English Document Detection
# =============================================================================


def is_complete_english_document(content: str) -> tuple[bool, float, dict]:
    """完全な英語文書かどうかを判定

    research.md の仕様:
    - 文書長: 500文字以上 (重み 0.3)
    - 英語比率: 80%以上 (重み 0.4)
    - 見出し構造: 2個以上の見出し (重み 0.3)
    - 加重スコア 0.7以上で「完全な英語文書」

    Returns:
        (is_english_doc, total_score, details)
    """
    # 空コンテンツチェック
    if not content or not content.strip():
        return False, 0.0, {"length": 0, "english_ratio": 0.0, "heading_count": 0}

    # 1. 文書長スコア (0.3)
    length = len(content)
    length_score = min(length / 500, 1.0) * 0.3

    # 2. 英語比率スコア (0.4)
    total_letters = count_total_letters(content)
    if total_letters > 0:
        english_chars = count_english_chars(content)
        english_ratio = english_chars / total_letters
    else:
        english_ratio = 0.0
    english_score = min(english_ratio / 0.8, 1.0) * 0.4

    # 3. 見出し構造スコア (0.3)
    heading_pattern = re.compile(r'^#{1,6}\s+', re.MULTILINE)
    heading_count = len(heading_pattern.findall(content))
    heading_score = min(heading_count / 2, 1.0) * 0.3

    # 合計スコア
    total_score = length_score + english_score + heading_score

    details = {
        "length": length,
        "length_score": round(length_score, 3),
        "english_ratio": round(english_ratio, 3),
        "english_score": round(english_score, 3),
        "heading_count": heading_count,
        "heading_score": round(heading_score, 3),
        "total_score": round(total_score, 3)
    }

    return total_score >= 0.7, total_score, details


def log_english_detection(
    filename: str,
    is_english: bool,
    score: float,
    details: dict,
    session_dir: Path | None = None
) -> None:
    """英語文書判定結果をログに記録

    Args:
        filename: ファイル名
        is_english: 英語文書かどうか
        score: スコア
        details: 詳細情報
        session_dir: セッションディレクトリ（ログ保存先）
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "filename": filename,
        "is_complete_english_doc": is_english,
        "score": round(score, 3),
        **details
    }

    try:
        if session_dir and session_dir.exists():
            log_path = session_dir / "english_detection.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except OSError:
        pass
