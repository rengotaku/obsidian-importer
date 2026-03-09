"""Mock responses for Ollama API calls.

Used when ollama.mock is true for integration testing without LLM server.
Loads golden response files when available, falls back to fixed responses.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Golden response directory
_GOLDEN_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "golden_responses"

# Cached index (loaded once on first use, mutable container avoids global statement)
_golden_cache: dict[str, dict[str, str] | None] = {"index": None}


def _load_golden_index() -> dict[str, str]:
    """Load golden response index from disk.

    Returns:
        Dict mapping function_name:user_message_hash -> golden_file name.
        Returns empty dict if index file not found.
    """
    cached = _golden_cache["index"]
    if cached is not None:
        return cached

    index_path = _GOLDEN_DIR / "_index.json"
    if not index_path.exists():
        logger.debug("Golden response index not found: %s", index_path)
        empty: dict[str, str] = {}
        _golden_cache["index"] = empty
        return empty

    with open(index_path, encoding="utf-8") as f:
        loaded: dict[str, str] = json.load(f)
        _golden_cache["index"] = loaded

    logger.info("[MOCK] Loaded golden response index: %d entries", len(loaded))
    return loaded


def _user_message_hash(user_message: str) -> str:
    """Compute SHA256 hash of user_message for index lookup."""
    return hashlib.sha256(user_message.encode("utf-8")).hexdigest()[:16]


def _detect_function(system_prompt: str) -> str:
    """Detect which function is calling based on system prompt content.

    Returns:
        Function name string for index lookup.
    """
    if "主題" in system_prompt and "ジャンル" in system_prompt and "JSON" in system_prompt:
        return "extract_topic_and_genre"
    if "主題を1つ抽出" in system_prompt or "トピック分類" in system_prompt:
        return "extract_topic"
    if "新しいジャンル" in system_prompt or "ジャンル提案" in system_prompt:
        return "suggest_genres"
    if "翻訳" in system_prompt:
        return "translate_summary"
    return "extract_knowledge"


def _lookup_golden_response(function_name: str, user_message: str) -> str | None:
    """Look up golden response file for the given function and user_message.

    Args:
        function_name: Detected function name.
        user_message: User message content.

    Returns:
        Golden response content or None if not found.
    """
    index = _load_golden_index()
    if not index:
        return None

    msg_hash = _user_message_hash(user_message)
    key = f"{function_name}:{msg_hash}"

    golden_file = index.get(key)
    if not golden_file:
        logger.debug("[MOCK] No golden response for %s", key)
        return None

    golden_path = _GOLDEN_DIR / golden_file
    if not golden_path.exists():
        logger.warning("[MOCK] Golden file not found: %s", golden_path)
        return None

    content = golden_path.read_text(encoding="utf-8")
    logger.info("[MOCK] Using golden response: %s", golden_file)
    return content


def mock_call_ollama(system_prompt: str, user_message: str) -> str:
    """Return mock response based on golden files or fallback.

    Detects which function is calling based on system prompt content,
    looks up golden response files, and falls back to fixed responses.

    Args:
        system_prompt: System prompt (used to detect caller function).
        user_message: User message (used for golden file lookup).

    Returns:
        Mock response string.
    """
    logger.info("[MOCK] call_ollama called in mock mode")

    function_name = _detect_function(system_prompt)

    # Try golden response first
    golden = _lookup_golden_response(function_name, user_message)
    if golden is not None:
        return golden

    # Fallback to fixed responses
    logger.debug("[MOCK] Falling back to fixed response for %s", function_name)
    return _fallback_response(function_name)


def _fallback_response(function_name: str) -> str:
    """Return fixed fallback response for the given function.

    Args:
        function_name: Detected function name.

    Returns:
        Fixed mock response string.
    """
    if function_name == "extract_topic_and_genre":
        return json.dumps({"topic": "テスト", "genre": "engineer"}, ensure_ascii=False)

    if function_name == "extract_topic":
        return "テスト"

    if function_name == "suggest_genres":
        return "[]"

    if function_name == "translate_summary":
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
