"""
llm_import.providers.claude.config - Claude 固有の設定

Claude エクスポートパーサー用の設定値を定義。
"""
from __future__ import annotations

from pathlib import Path


# =============================================================================
# Claude Export Configuration
# =============================================================================

# 入力ディレクトリ（デフォルト）
DEFAULT_INPUT_DIR = Path("@index/llm_exports/claude")

# 出力ディレクトリ（Phase 1 出力）
DEFAULT_OUTPUT_DIR = Path("@index/llm_exports/claude/parsed/conversations")

# スキップ基準
MIN_MESSAGE_COUNT = 1  # 最低メッセージ数
MIN_CONTENT_LENGTH = 50  # 最低文字数（全メッセージ合計）

# ファイル名設定
MAX_FILENAME_LENGTH = 80
DATE_FORMAT = "%Y-%m-%d"

# サマリー検出
SUMMARY_HEADER = "**Conversation Overview**"
