"""Knowledge extraction logic for obsidian-etl.

Extracts structured knowledge from conversation data using LLM.
Function-based API with params dict input for Kedro integration.
Migrated from src/etl/utils/knowledge_extractor.py.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from obsidian_etl.utils.ollama import call_ollama, parse_markdown_response
from obsidian_etl.utils.ollama_config import get_ollama_config

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
KNOWLEDGE_PROMPT_PATH = PROMPTS_DIR / "knowledge_extraction.txt"
SUMMARY_PROMPT_PATH = PROMPTS_DIR / "summary_translation.txt"

# English summary detection patterns
ENGLISH_SUMMARY_PATTERNS = [
    r"^\*\*Conversation Overview\*\*",
    r"^Conversation Overview",
    r"^Summary:",
    r"^Overview:",
    r"^The user (asked|requested|wanted|discussed)",
]


def load_prompt(path: Path) -> str:
    """Load prompt template from file.

    Args:
        path: Path to prompt file.

    Returns:
        Prompt text.
    """
    with open(path, encoding="utf-8") as f:
        return f.read()


def is_english_summary(text: str | None) -> bool:
    """Detect if summary is in English.

    Args:
        text: Summary text.

    Returns:
        True if English summary detected.
    """
    if not text:
        return False

    for pattern in ENGLISH_SUMMARY_PATTERNS:
        if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
            return True

    # ASCII ratio check (>70% ASCII = English)
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    total_chars = len(text)
    if total_chars > 0 and ascii_chars / total_chars > 0.7:
        return True

    return False


def translate_summary(summary: str, params: dict) -> tuple[str | None, str | None]:
    """Translate English summary to Japanese.

    Args:
        summary: English summary text.
        params: Ollama params (model, base_url, timeout, temperature).

    Returns:
        Tuple of (translated_summary, error_message).
    """
    prompt = load_prompt(SUMMARY_PROMPT_PATH)
    config = get_ollama_config(params, "translate_summary")

    response, error = call_ollama(
        prompt,
        f"以下の英語サマリーを日本語に翻訳してください:\n\n{summary}",
        model=config.model,
        base_url=config.base_url,
        num_predict=config.num_predict,
        timeout=config.timeout,
        temperature=config.temperature,
    )

    if error:
        return None, error

    data, parse_error = parse_markdown_response(response)
    if parse_error:
        return None, parse_error

    return data.get("summary", ""), None


def extract_knowledge(
    content: str,
    conversation_name: str | None,
    created_at: str | None,
    source_provider: str,
    params: dict,
) -> tuple[dict | None, str | None]:
    """Extract knowledge from conversation content using LLM.

    Args:
        content: Formatted conversation text.
        conversation_name: Conversation name/title.
        created_at: Creation timestamp.
        source_provider: Provider name (claude, openai, github).
        params: Import params including ollama settings.

    Returns:
        Tuple of (knowledge_dict, error_message).
        knowledge_dict contains: title, summary, summary_content.
    """
    prompt = load_prompt(KNOWLEDGE_PROMPT_PATH)
    config = get_ollama_config(params, "extract_knowledge")

    # Build user message
    user_message = _build_user_message(content, conversation_name, created_at, source_provider)

    response, error = call_ollama(
        prompt,
        user_message,
        model=config.model,
        base_url=config.base_url,
        num_predict=config.num_predict,
        timeout=config.timeout,
        temperature=config.temperature,
    )

    if error:
        return None, error

    data, parse_error = parse_markdown_response(response)
    if parse_error:
        return None, parse_error

    return data, None


def _build_user_message(
    content: str,
    conversation_name: str | None,
    created_at: str | None,
    source_provider: str,
) -> str:
    """Build user message for knowledge extraction LLM call.

    Args:
        content: Conversation text.
        conversation_name: Conversation name.
        created_at: Creation timestamp.
        source_provider: Provider name.

    Returns:
        Formatted user message.
    """
    lines = [
        f"ファイル名: {conversation_name or 'Untitled'}",
        f"プロバイダー: {source_provider}",
        "会話サマリー: なし",
        f"会話作成日: {created_at or 'unknown'}",
        "",
        "--- 会話内容 ---",
        "",
        content,
    ]
    return "\n".join(lines)


def normalize_summary_headings(content: str) -> str:
    """Normalize headings in summary_content to ## level and below.

    Args:
        content: Markdown content.

    Returns:
        Content with headings shifted down one level.
    """
    lines = content.split("\n")
    result_lines = []

    for line in lines:
        match = re.match(r"^(#{1,6})(\s+.*)$", line)
        if match:
            hashes = match.group(1)
            rest = match.group(2)
            new_level = min(len(hashes) + 1, 6)
            result_lines.append("#" * new_level + rest)
        else:
            result_lines.append(line)

    return "\n".join(result_lines)
