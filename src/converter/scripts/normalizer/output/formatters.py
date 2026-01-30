"""
Formatters - 結果出力フォーマッター

処理結果の表示用フォーマット関数を提供。
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.models import ProcessingResult


# =============================================================================
# Result Formatters
# =============================================================================


def format_success_result(result: ProcessingResult) -> str:
    """成功結果をフォーマット"""
    lines = [
        "✅ ファイル整理完了",
        f"  📄 元ファイル: {result['file']}",
        f"  📂 移動先: {result['destination']}",
        f"  🏷️ ジャンル: {result['genre']} (confidence: {result['confidence']:.2f})"
    ]

    # 英語文書フラグ
    if result.get("is_complete_english_doc"):
        lines.append("  🌐 完全な英語文書（翻訳なし）")

    # 改善内容表示
    improvements = result.get("improvements_made", [])
    if improvements:
        lines.append(f"  ✨ 改善点 ({len(improvements)}件):")
        for imp in improvements[:3]:
            lines.append(f"    - {imp}")
        if len(improvements) > 3:
            lines.append(f"    ... 他 {len(improvements) - 3} 件")

    return "\n".join(lines)


def format_dust_result(result: ProcessingResult, reason: str) -> str:
    """dust判定結果をフォーマット"""
    return f"""🗑️ Dust判定
  📄 ファイル: {result['file']}
  📂 移動先: {result['destination']}
  📝 理由: {reason}"""


def format_error_result(result: ProcessingResult) -> str:
    """エラー結果をフォーマット"""
    return f"""❌ エラー
  📄 ファイル: {result['file']}
  💥 エラー: {result['error']}"""


def format_skip_result(filename: str, reason: str) -> str:
    """スキップ結果をフォーマット"""
    return f"""⏭️ スキップ
  📄 ファイル: {filename}
  📝 理由: {reason}"""


def output_json_result(result: ProcessingResult) -> None:
    """JSON形式で結果を出力"""
    print(json.dumps(result, ensure_ascii=False, indent=2))
