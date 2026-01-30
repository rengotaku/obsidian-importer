"""
エラー詳細ファイル出力モジュール

LLMインポート処理でエラー発生時に、デバッグに必要な情報を
Markdownファイルとして出力する。

出力先: @session/import/{session_id}/errors/{conversation_id}.md
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ErrorDetail:
    """
    エラー発生時の詳細情報

    Attributes:
        session_id: セッションID
        conversation_id: 会話ID
        conversation_title: 会話タイトル
        timestamp: エラー発生時刻
        error_type: エラー種別（json_parse, no_json, timeout等）
        error_message: エラーメッセージ
        error_position: エラー位置（文字数）
        error_context: エラー周辺のテキスト
        original_content: 元の会話内容
        llm_prompt: LLMに送信したプロンプト
        llm_output: LLMの生の出力
        stage: エラー発生段階（phase1, phase2）
    """

    session_id: str
    conversation_id: str
    conversation_title: str
    timestamp: datetime
    error_type: str
    error_message: str
    original_content: str
    llm_prompt: str
    stage: str
    error_position: int | None = None
    error_context: str | None = None
    llm_output: str | None = None


# 最大ファイルサイズ（10MB）
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _truncate_content(content: str, max_chars: int) -> str:
    """コンテンツを指定文字数で切り詰める"""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n... (truncated)"


def write_error_file(error: ErrorDetail, output_dir: Path) -> Path:
    """
    エラー詳細をMarkdownファイルとして出力

    Args:
        error: エラー詳細情報
        output_dir: 出力ディレクトリ（errors/）

    Returns:
        出力ファイルパス
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名: conversation_id.md
    filename = f"{error.conversation_id}.md"
    output_path = output_dir / filename

    # Markdown生成
    content = _format_error_markdown(error)

    # サイズチェック・トランケーション
    content_bytes = content.encode("utf-8")
    if len(content_bytes) > MAX_FILE_SIZE_BYTES:
        # 各セクションを均等に削減
        max_section_chars = MAX_FILE_SIZE_BYTES // 4  # 各セクション約2.5MB
        error_truncated = ErrorDetail(
            session_id=error.session_id,
            conversation_id=error.conversation_id,
            conversation_title=error.conversation_title,
            timestamp=error.timestamp,
            error_type=error.error_type,
            error_message=error.error_message,
            error_position=error.error_position,
            error_context=error.error_context,
            original_content=_truncate_content(
                error.original_content, max_section_chars
            ),
            llm_prompt=_truncate_content(error.llm_prompt, max_section_chars),
            llm_output=_truncate_content(error.llm_output or "", max_section_chars),
            stage=error.stage,
        )
        content = _format_error_markdown(error_truncated)

    output_path.write_text(content, encoding="utf-8")
    return output_path


def _format_error_markdown(error: ErrorDetail) -> str:
    """エラー詳細をMarkdown形式にフォーマット"""
    position_str = str(error.error_position) if error.error_position else "N/A"
    timestamp_str = error.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# Error Detail: {error.conversation_title}",
        "",
        f"**Session**: {error.session_id}",
        f"**Conversation ID**: {error.conversation_id}",
        f"**Timestamp**: {timestamp_str}",
        f"**Error Type**: {error.error_type}",
        f"**Error Position**: {position_str}",
        f"**Stage**: {error.stage}",
        "",
        "## Error Message",
        "",
        error.error_message,
        "",
        "## Original Content",
        "",
        "```text",
        error.original_content,
        "```",
        "",
        "## LLM Prompt",
        "",
        "```text",
        error.llm_prompt,
        "```",
        "",
        "## LLM Raw Output",
        "",
        "```text",
        error.llm_output or "(no output)",
        "```",
        "",
    ]

    if error.error_context:
        lines.extend(
            [
                "## Context",
                "",
                error.error_context,
                "",
            ]
        )

    return "\n".join(lines)
