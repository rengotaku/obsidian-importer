"""
Single - 単一ファイル処理

ファイル名正規化、正規化実行、単一ファイル処理を行う。
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.models import (
    NormalizationResult,
    ProcessingResult,
)
from normalizer.config import (
    BASE_DIR,
)
from normalizer.validators.title import validate_title, log_title_quality
from normalizer.validators.format import validate_markdown_format, log_format_quality
from normalizer.validators.tags import normalize_tags, calculate_tag_consistency, log_tag_quality
from normalizer.detection.english import log_english_detection
from normalizer.io.files import get_destination_path, read_file_content, write_file_content
from normalizer.io.session import timestamp, log_message
from normalizer.pipeline.runner import run_pipeline_v2


# =============================================================================
# File ID Generation
# =============================================================================


def generate_file_id(content: str, filepath: Path) -> str:
    """ファイルコンテンツと初回パスからハッシュIDを生成

    Args:
        content: ファイルコンテンツ
        filepath: ファイルの相対パス（初回処理時のパス）

    Returns:
        12文字の16進数ハッシュID（SHA-256の先頭48ビット）
    """
    # コンテンツ + 相対パスを結合してハッシュ化
    # パスは POSIX 形式に正規化（クロスプラットフォーム対応）
    path_str = filepath.as_posix()
    combined = f"{content}\n---\n{path_str}"
    hash_digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return hash_digest[:12]


def extract_file_id_from_frontmatter(content: str) -> str | None:
    """Markdown ファイルの frontmatter から file_id を抽出する (T028)

    Args:
        content: Markdown ファイルの内容

    Returns:
        file_id (12文字の16進数) または None

    Example:
        >>> content = "---\\ntitle: Test\\nfile_id: a1b2c3d4e5f6\\n---\\n# Content"
        >>> extract_file_id_from_frontmatter(content)
        'a1b2c3d4e5f6'
    """
    # frontmatter を抽出 (--- で囲まれた部分)
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)

    # file_id を抽出 (12文字の16進数小文字のみ)
    file_id_match = re.search(r"^file_id:\s*([a-f0-9]{12})\s*$", frontmatter, re.MULTILINE)
    if file_id_match:
        return file_id_match.group(1)

    return None


def get_or_generate_file_id(content: str, filepath: Path) -> str:
    """既存の file_id を維持、なければ新規生成 (T029)

    「file_id がなければ生成、あれば維持」の原則に従う。

    Args:
        content: ファイルコンテンツ
        filepath: ファイルパス

    Returns:
        file_id (12文字の16進数)
    """
    # 既存の file_id を抽出
    existing_file_id = extract_file_id_from_frontmatter(content)
    if existing_file_id:
        return existing_file_id

    # 新規生成
    return generate_file_id(content, filepath)


# =============================================================================
# Filename Utilities
# =============================================================================


def clean_filename(filename: str) -> str:
    """ファイル名から日付プレフィックスを除去

    Args:
        filename: 元のファイル名（拡張子なし）

    Returns:
        クリーンなファイル名
    """
    # Jekyll形式の日付プレフィックスを除去: 2022-10-17-Title → Title
    cleaned = re.sub(r'^\d{4}[-_]\d{2}[-_]\d{2}[-_]', '', filename)
    return cleaned


def normalize_filename(title: str) -> str:
    """タイトルをファイル名として使用可能な形式に正規化

    Args:
        title: 元のタイトル

    Returns:
        正規化されたファイル名（拡張子なし）
    """
    if not title:
        return ""

    # 禁止文字を除去/置換
    # ファイルシステムで禁止される文字: / \\ : * ? " < > |
    normalized = re.sub(r'[/\\:*?"<>|]', '', title)

    # 複数の空白を1つに
    normalized = re.sub(r'\s+', ' ', normalized)

    # 前後の空白を除去
    normalized = normalized.strip()

    return normalized


# =============================================================================
# File Building
# =============================================================================


def extract_frontmatter(content: str) -> tuple[dict | None, str]:
    """コンテンツからfrontmatterを抽出

    Args:
        content: Markdownコンテンツ

    Returns:
        tuple: (frontmatter_dict, body_content)
    """
    if not content.startswith('---'):
        return None, content

    # frontmatterの終端を探す
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return None, content

    fm_end = end_match.end() + 3
    fm_content = content[4:fm_end - 4]
    body = content[fm_end:]

    # 簡易的なYAMLパース
    fm = {}
    for line in fm_content.split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            fm[key.strip()] = value.strip()

    return fm, body


def build_normalized_file(
    result: NormalizationResult,
    file_id: str | None = None
) -> str:
    """正規化結果からファイル内容を構築

    Args:
        result: 正規化結果
        file_id: ファイル追跡用ハッシュID

    Returns:
        Markdownファイル内容
    """
    fm = result["frontmatter"]

    # frontmatter構築
    lines = ["---"]
    lines.append(f'title: "{fm["title"]}"')

    if fm["tags"]:
        lines.append("tags:")
        for tag in fm["tags"]:
            lines.append(f"  - {tag}")

    if fm["created"]:
        lines.append(f"created: {fm['created']}")

    if fm.get("summary"):
        lines.append(f'summary: "{fm["summary"]}"')

    if fm.get("related"):
        lines.append("related:")
        for rel in fm["related"]:
            lines.append(f'  - "{rel}"')

    # ファイル追跡ID追加
    if file_id is not None:
        lines.append(f"file_id: {file_id}")

    lines.append("---")
    lines.append("")

    # 本文追加（既存frontmatterを除去して保護）
    body = result["normalized_content"]
    existing_fm, body_only = extract_frontmatter(body)
    if existing_fm:
        body = body_only.strip()

    lines.append(body)

    return "\n".join(lines)


# =============================================================================
# Markdown Normalization
# =============================================================================


def normalize_markdown(content: str) -> str:
    """Markdownコンテンツを正規化

    Args:
        content: 元のMarkdownコンテンツ

    Returns:
        正規化されたコンテンツ
    """
    # 複数の空行を1つに
    normalized = re.sub(r'\n{3,}', '\n\n', content)

    # 末尾の空白を除去
    lines = [line.rstrip() for line in normalized.split('\n')]
    normalized = '\n'.join(lines)

    # 末尾に改行を追加
    if not normalized.endswith('\n'):
        normalized += '\n'

    return normalized


# =============================================================================
# File Normalization
# =============================================================================


def normalize_file(filepath: Path) -> tuple[NormalizationResult | None, str | None]:
    """ファイルをOllamaで分類・正規化

    Args:
        filepath: 処理対象ファイルのパス

    Returns:
        tuple: (NormalizationResult, error_message)
    """
    # ファイル読み込み
    content, err = read_file_content(filepath)
    if err:
        return None, err

    # Multi-stage pipeline (A→B→C) を実行
    result = run_pipeline_v2(filepath, content)

    # 英語文書判定ログ記録
    log_english_detection(
        filepath.name,
        result["is_complete_english_doc"],
        0.0,  # スコアはpipeline内で計算済み
        {}
    )

    # タイトル品質検証・修正
    title = result["frontmatter"]["title"]
    is_valid, issues = validate_title(title)

    if not is_valid:
        # タイトルが無効な場合、正規化を試みる
        cleaned_title = normalize_filename(title)
        if cleaned_title:
            result["frontmatter"]["title"] = cleaned_title
        else:
            # 正規化でも空になる場合はファイル名をフォールバック
            result["frontmatter"]["title"] = clean_filename(filepath.stem)

    # タイトル品質ログ記録
    log_title_quality(filepath.name, result["frontmatter"]["title"])

    # タグ品質検証・修正
    tags = result["frontmatter"]["tags"]
    tags = normalize_tags(tags)
    result["frontmatter"]["tags"] = tags

    # タグ一貫性計算
    consistency_rate, matched, unmatched = calculate_tag_consistency(tags)

    # タグ品質ログ記録
    log_tag_quality(filepath.name, tags, consistency_rate, matched, unmatched)

    # Markdown正規化をpost-processingとして適用
    normalized_content = result["normalized_content"]
    if normalized_content:
        result["normalized_content"] = normalize_markdown(normalized_content)

    return result, None


# =============================================================================
# Single File Processing
# =============================================================================


def process_single_file(
    filepath: Path,
    preview: bool = False,
    quiet: bool = False,
    output_json: bool = False
) -> ProcessingResult:
    """単一ファイルを処理

    Args:
        filepath: 処理対象ファイル
        preview: プレビューモード（移動しない）
        quiet: 進捗表示抑制
        output_json: JSON出力

    Returns:
        ProcessingResult
    """
    import json

    # fixtures ディレクトリ内のファイルは自動的にpreviewモードを強制
    if "tests/fixtures/" in str(filepath):
        preview = True
        if not quiet:
            print("⚠️ fixturesディレクトリのため自動的にpreviewモードで実行")

    result: ProcessingResult = {
        "success": False,
        "file": str(filepath),
        "genre": None,
        "confidence": "low",
        "destination": None,
        "error": None,
        "timestamp": timestamp(),
        "original_chars": None,
        "normalized_chars": None,
        "char_diff": None,
        "improvements_made": None,
        "is_complete_english_doc": None,
        "file_id": None
    }

    # 元ファイルの文字数を取得 & file_id 取得/生成 (T030)
    try:
        original_content = filepath.read_text(encoding="utf-8")
        result["original_chars"] = len(original_content)
        # ファイル追跡用ハッシュID: 既存を維持、なければ生成
        result["file_id"] = get_or_generate_file_id(original_content, filepath)
    except Exception:
        pass

    # 正規化実行
    norm_result, err = normalize_file(filepath)
    if err:
        result["error"] = err
        if output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            log_message(f"❌ エラー\n  📄 ファイル: {result['file']}\n  💥 エラー: {result['error']}")
        return result

    result["genre"] = norm_result["genre"]
    confidence = norm_result["confidence"]
    result["confidence"] = confidence
    result["improvements_made"] = norm_result.get("improvements_made", [])
    result["is_complete_english_doc"] = norm_result.get("is_complete_english_doc", False)

    # 移動先決定
    title = norm_result["frontmatter"]["title"]
    normalized_title = normalize_filename(title)

    # フォールバック: タイトルが空の場合は元ファイル名から生成
    if not normalized_title:
        fallback_name = clean_filename(filepath.stem)
        normalized_title = fallback_name.replace('-', ' ')

    new_filename = normalized_title + ".md"
    dest_path = get_destination_path(norm_result["genre"], new_filename, norm_result.get("subfolder", ""))

    result["destination"] = str(dest_path.relative_to(BASE_DIR))

    if preview:
        # プレビューモード - 文字数も計算
        preview_content = build_normalized_file(
            norm_result,
            file_id=result["file_id"]
        )
        result["normalized_chars"] = len(preview_content)
        if result["original_chars"] is not None:
            result["char_diff"] = result["normalized_chars"] - result["original_chars"]

        result["success"] = True
        if output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif not quiet:
            _log_processing_result(result, norm_result)
            log_message("  👁️ プレビューモード（移動なし）")
        return result

    # ファイル書き込み
    normalized_content = build_normalized_file(
        norm_result,
        file_id=result["file_id"]
    )
    write_err = write_file_content(dest_path, normalized_content)
    if write_err:
        result["error"] = write_err
        if output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            log_message(f"❌ エラー\n  📄 ファイル: {result['file']}\n  💥 エラー: {result['error']}")
        return result

    # 文字数統計を記録
    result["normalized_chars"] = len(normalized_content)
    if result["original_chars"] is not None:
        result["char_diff"] = result["normalized_chars"] - result["original_chars"]

    # フォーマット検証
    format_valid, format_issues = validate_markdown_format(normalized_content)
    log_format_quality(new_filename, normalized_content, format_valid, format_issues)

    # 元ファイル削除
    try:
        filepath.unlink()
    except Exception as e:
        result["error"] = f"元ファイル削除エラー: {e}"
        if output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            log_message(f"❌ エラー\n  📄 ファイル: {result['file']}\n  💥 エラー: {result['error']}")
        return result

    result["success"] = True

    # 結果出力
    if output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not quiet:
        _log_processing_result(result, norm_result)

    return result


def _log_processing_result(
    result: ProcessingResult,
    norm_result: NormalizationResult,
) -> None:
    """処理結果をログに出力（内部ヘルパー）"""
    if norm_result["genre"] == "dust":
        log_message(f"""🗑️ Dust判定
  📄 ファイル: {result['file']}
  📂 移動先: {result['destination']}
  📝 理由: {norm_result['reason'] or '価値なしと判定'}""")
    else:
        lines = [
            "✅ ファイル整理完了",
            f"  📄 元ファイル: {result['file']}",
            f"  📂 移動先: {result['destination']}",
            f"  🏷️ ジャンル: {result['genre']} (confidence: {result['confidence']:.2f})"
        ]
        if result.get("is_complete_english_doc"):
            lines.append("  🌐 完全な英語文書（翻訳なし）")
        improvements = result.get("improvements_made", [])
        if improvements:
            lines.append(f"  ✨ 改善点 ({len(improvements)}件):")
            for imp in improvements[:3]:
                lines.append(f"    - {imp}")
            if len(improvements) > 3:
                lines.append(f"    ... 他 {len(improvements) - 3} 件")
        log_message("\n".join(lines))
