"""Mock responses for Ollama API calls.

Used when ollama.mock is true for integration testing without LLM server.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


def mock_call_ollama(system_prompt: str, user_message: str) -> str:
    """Return mock response based on the system prompt context.

    Detects which function is calling based on system prompt content
    and returns appropriate mock response.

    Args:
        system_prompt: System prompt (used to detect caller function).
        user_message: User message (ignored in mock mode).

    Returns:
        Mock response string.
    """
    logger.info("[MOCK] call_ollama called in mock mode")

    # Detect caller by system prompt content
    if "主題" in system_prompt and "ジャンル" in system_prompt and "JSON" in system_prompt:
        # _extract_topic_and_genre_via_llm
        return json.dumps({"topic": "テスト", "genre": "engineer"}, ensure_ascii=False)

    if "主題を1つ抽出" in system_prompt or "トピック分類" in system_prompt:
        # _extract_topic_via_llm
        return "テスト"

    if "新しいジャンル" in system_prompt or "ジャンル提案" in system_prompt:
        # _suggest_new_genres_via_llm
        return "[]"

    if "翻訳" in system_prompt:
        # translate_summary
        return (
            "# モック翻訳\n\n## 要約\nモック翻訳結果\n\n## タグ\nテスト\n\n## 内容\nモック翻訳内容"
        )

    # Default: extract_knowledge
    return _mock_knowledge_response()


def _mock_knowledge_response() -> str:
    """Return mock knowledge extraction response."""
    return """# モックナレッジタイトル

## 要約
これはモックモードで生成されたテスト用の要約です。

## タグ
テスト, モック, 統合テスト

## 内容
これはモックモードで生成されたテスト用のコンテンツです。

実際のLLM処理は行われていません。統合テストのパイプライン検証用データです。"""


def mock_check_ollama_connection() -> tuple[bool, str | None]:
    """Mock Ollama connection check.

    Returns:
        Always returns (True, None) in mock mode.
    """
    logger.info("[MOCK] check_ollama_connection called in mock mode")
    return True, None
