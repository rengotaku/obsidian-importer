#!/usr/bin/env python3
"""
Markdown Normalizer - Obsidian規約に準拠したMarkdown後処理

FR-005: ルールベースの後処理でMarkdown本文を正規化
- 見出しレベルを適切に調整（##から開始）
- 空行圧縮（連続空行を1行に）
- 箇条書きを統一（-を使用）

Usage:
    python3 markdown_normalizer.py <file_path> [options]

Options:
    --output, -o    出力先（指定なしで標準出力）
    --in-place, -i  ファイルを直接更新
    --diff          変更箇所をdiff形式で表示
"""

from __future__ import annotations

import argparse
import re
import sys
from difflib import unified_diff
from pathlib import Path


# =============================================================================
# Normalization Rules (research.md)
# =============================================================================

def extract_frontmatter(content: str) -> tuple[str | None, str]:
    """frontmatterと本文を分離

    Returns:
        (frontmatter, body) - frontmatterがない場合はNone
    """
    if not content.startswith("---"):
        return None, content

    # 2番目の---を探す
    match = re.match(r"^(---\s*\n.*?\n---)\s*\n?", content, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        body = content[match.end():]
        return frontmatter, body

    return None, content


def normalize_heading_levels(content: str) -> str:
    """見出しレベルを調整（最上位を#から始める）

    - 最小レベルが2以上の場合、全体を上げて1から始める
    - 例: ## → #, ### → ##
    """
    lines = content.split("\n")

    # 最上位の見出しレベルを検出
    min_level = 7  # 見出しは最大6レベル
    for line in lines:
        match = re.match(r"^(#{1,6})\s+", line)
        if match:
            level = len(match.group(1))
            min_level = min(min_level, level)

    # 見出しがない、または既に1から始まっている場合はそのまま
    if min_level >= 7 or min_level == 1:
        return content

    # シフト量を計算（最小レベルを1にする）
    shift = min_level - 1

    result_lines = []
    for line in lines:
        match = re.match(r"^(#{1,6})(\s+.*)$", line)
        if match:
            hashes = match.group(1)
            rest = match.group(2)
            new_level = len(hashes) - shift
            if new_level >= 1:  # 最小1レベル
                result_lines.append("#" * new_level + rest)
            else:
                result_lines.append(line)
        else:
            result_lines.append(line)
    return "\n".join(result_lines)


def compress_blank_lines(content: str) -> str:
    """連続する空行を1行に圧縮"""
    # 3行以上の連続空行を2行に（1行の空白行）
    return re.sub(r"\n{3,}", "\n\n", content)


def unify_bullet_points(content: str) -> str:
    """箇条書き記号を統一（*、+を-に）"""
    lines = content.split("\n")
    result_lines = []

    for line in lines:
        # 行頭の*または+を-に置換（インデント保持）
        match = re.match(r"^(\s*)([*+])(\s+.*)$", line)
        if match:
            indent = match.group(1)
            rest = match.group(3)
            result_lines.append(f"{indent}-{rest}")
        else:
            result_lines.append(line)

    return "\n".join(result_lines)


def strip_trailing_whitespace(content: str) -> str:
    """各行の末尾空白を削除"""
    lines = content.split("\n")
    return "\n".join(line.rstrip() for line in lines)


def ensure_final_newline(content: str) -> str:
    """ファイル末尾に改行を確保"""
    if content and not content.endswith("\n"):
        return content + "\n"
    return content


def normalize_markdown(content: str) -> str:
    """Markdown正規化のメインパイプライン

    処理順序（research.md準拠）:
    1. frontmatter抽出・保護
    2. 見出しレベル調整（全体シフト）
    3. 箇条書き記号統一
    4. 空行圧縮
    5. 末尾空白削除
    6. frontmatter再結合
    """
    # 1. frontmatter分離
    frontmatter, body = extract_frontmatter(content)

    # 2. 見出しレベル調整
    body = normalize_heading_levels(body)

    # 3. 箇条書き統一
    body = unify_bullet_points(body)

    # 4. 空行圧縮
    body = compress_blank_lines(body)

    # 5. 末尾空白削除
    body = strip_trailing_whitespace(body)

    # 6. frontmatter再結合
    if frontmatter:
        result = frontmatter + "\n\n" + body.lstrip("\n")
    else:
        result = body.lstrip("\n")

    # ファイル末尾改行
    result = ensure_final_newline(result)

    return result


# =============================================================================
# English Document Detection (research.md)
# =============================================================================

def count_english_chars(text: str) -> int:
    """英語文字（アルファベット）の数をカウント"""
    return len(re.findall(r"[a-zA-Z]", text))


def count_japanese_chars(text: str) -> int:
    """日本語文字（ひらがな、カタカナ、漢字）の数をカウント"""
    return len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", text))


def count_headings(content: str) -> int:
    """見出しの数をカウント"""
    return len(re.findall(r"^#{1,6}\s+", content, re.MULTILINE))


def is_complete_english_document(content: str) -> tuple[bool, float]:
    """完全な英語文書かどうかを判定

    research.md の判定基準:
    - 文書長: 500文字以上 (重み0.3)
    - 英語比率: 80%以上 (重み0.4)
    - 見出し構造: 2個以上 (重み0.3)

    加重スコア 0.7以上 → 「完全な英語文書」として保持

    Returns:
        (is_complete, score) - 完全な英語文書かどうかとスコア
    """
    # frontmatterを除外して判定
    _, body = extract_frontmatter(content)

    # 空の場合
    if not body.strip():
        return False, 0.0

    # 文字数（空白除く）
    text_chars = len(re.sub(r"\s", "", body))

    # 1. 文書長スコア
    length_score = min(text_chars / 500, 1.0) * 0.3

    # 2. 英語比率スコア
    eng_count = count_english_chars(body)
    jpn_count = count_japanese_chars(body)
    total_lang_chars = eng_count + jpn_count

    if total_lang_chars > 0:
        english_ratio = eng_count / total_lang_chars
    else:
        english_ratio = 0.0

    # 80%以上で満点、それ未満は比例
    english_score = min(english_ratio / 0.8, 1.0) * 0.4

    # 3. 見出し構造スコア
    heading_count = count_headings(body)
    heading_score = min(heading_count / 2, 1.0) * 0.3

    # 合計スコア
    total_score = length_score + english_score + heading_score

    return total_score >= 0.7, total_score


def detect_primary_language(content: str) -> str:
    """主言語を検出

    Returns:
        "ja" | "en" | "mixed"
    """
    _, body = extract_frontmatter(content)

    eng_count = count_english_chars(body)
    jpn_count = count_japanese_chars(body)

    if eng_count == 0 and jpn_count == 0:
        return "mixed"

    total = eng_count + jpn_count
    eng_ratio = eng_count / total

    if eng_ratio >= 0.8:
        return "en"
    elif eng_ratio <= 0.2:
        return "ja"
    else:
        return "mixed"


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Obsidian規約に準拠したMarkdown正規化"
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        type=Path,
        help="処理対象のMarkdownファイル（省略時は標準入力）"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="出力先（指定なしで標準出力）"
    )
    parser.add_argument(
        "-i", "--in-place",
        action="store_true",
        help="ファイルを直接更新"
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="変更箇所をdiff形式で表示"
    )
    parser.add_argument(
        "--check-english",
        action="store_true",
        help="英語文書判定のみ実行"
    )

    args = parser.parse_args()

    # 入力読み込み
    if args.file_path:
        if not args.file_path.exists():
            print(f"エラー: ファイルが見つかりません: {args.file_path}", file=sys.stderr)
            sys.exit(1)
        original = args.file_path.read_text(encoding="utf-8")
    else:
        original = sys.stdin.read()

    # 英語文書判定モード
    if args.check_english:
        is_english, score = is_complete_english_document(original)
        lang = detect_primary_language(original)
        print(f"Primary Language: {lang}")
        print(f"Complete English Document: {is_english}")
        print(f"Score: {score:.2f}")
        sys.exit(0)

    # 正規化実行
    normalized = normalize_markdown(original)

    # diff表示
    if args.diff:
        diff = unified_diff(
            original.splitlines(keepends=True),
            normalized.splitlines(keepends=True),
            fromfile="before",
            tofile="after"
        )
        print("".join(diff))
        sys.exit(0)

    # 出力
    if args.in_place and args.file_path:
        args.file_path.write_text(normalized, encoding="utf-8")
        print(f"更新完了: {args.file_path}")
    elif args.output:
        args.output.write_text(normalized, encoding="utf-8")
        print(f"出力完了: {args.output}")
    else:
        print(normalized, end="")


if __name__ == "__main__":
    main()
