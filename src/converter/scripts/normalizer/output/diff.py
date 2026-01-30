"""
Diff - 差分表示

処理前後の差分表示機能を提供。
"""
from __future__ import annotations

from difflib import unified_diff
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.processing.single import normalize_file, build_normalized_file


# =============================================================================
# Diff Display
# =============================================================================


def show_diff(original_content: str, normalized_content: str, filename: str) -> None:
    """処理前後の差分を表示

    Args:
        original_content: 元のファイル内容
        normalized_content: 正規化後の内容
        filename: ファイル名（表示用）
    """
    diff = unified_diff(
        original_content.splitlines(keepends=True),
        normalized_content.splitlines(keepends=True),
        fromfile=f"a/{filename} (元ファイル)",
        tofile=f"b/{filename} (正規化後)",
        lineterm=""
    )

    diff_lines = list(diff)
    if diff_lines:
        print("\n📊 差分表示:")
        print("=" * 60)
        for line in diff_lines:
            # 色分け表示（ANSI escape）
            if line.startswith("+") and not line.startswith("+++"):
                print(f"\033[32m{line}\033[0m", end="")  # 緑
            elif line.startswith("-") and not line.startswith("---"):
                print(f"\033[31m{line}\033[0m", end="")  # 赤
            elif line.startswith("@@"):
                print(f"\033[36m{line}\033[0m", end="")  # シアン
            else:
                print(line, end="")
            if not line.endswith("\n"):
                print()
        print("=" * 60)
    else:
        print("\n✅ 差分なし（変更されていません）")


def process_file_with_diff(filepath: Path) -> int:
    """diffモードでファイルを処理（移動は行わない）

    Args:
        filepath: 処理対象ファイル

    Returns:
        終了コード（0: 成功, 1: エラー）
    """
    print(f"📄 処理対象: {filepath}")
    print("⏳ Ollama API呼び出し中...")

    # 元ファイル読み込み
    try:
        original_content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")
        return 1

    # 正規化実行
    norm_result, err = normalize_file(filepath)
    if err:
        print(f"❌ 正規化エラー: {err}")
        return 1

    # 正規化後のコンテンツを生成
    normalized_content = build_normalized_file(norm_result)

    # 結果サマリー
    print(f"\n📋 正規化結果:")
    print(f"  ジャンル: {norm_result['genre']} (confidence: {norm_result['confidence']:.2f})")
    print(f"  タイトル: {norm_result['frontmatter']['title']}")
    print(f"  タグ: {', '.join(norm_result['frontmatter']['tags'])}")

    # 改善点表示
    improvements = norm_result.get("improvements_made", [])
    if improvements:
        print(f"\n✨ 改善点 ({len(improvements)}件):")
        for imp in improvements:
            print(f"  - {imp}")

    # 差分表示
    show_diff(original_content, normalized_content, filepath.name)

    return 0
