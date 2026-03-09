"""Generate golden LLM responses for integration test fixtures.

Reads test conversations, runs them through the actual LLM pipeline,
and saves the raw LLM responses as golden files for mock mode.

Usage:
    make test-golden-responses
    # or directly:
    .venv/bin/python scripts/generate_golden_responses.py

Requirements:
    - Ollama running locally
    - Model specified in conf/base/parameters.yml available
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_etl.utils.file_id import generate_file_id
from obsidian_etl.utils.knowledge_extractor import (
    _build_user_message,
    load_prompt,
    KNOWLEDGE_PROMPT_PATH,
    SUMMARY_PROMPT_PATH,
)
from obsidian_etl.utils.ollama import call_ollama

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Paths
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
CONVERSATIONS_JSON = FIXTURES_DIR / "claude_test_conversations.json"
GOLDEN_DIR = FIXTURES_DIR / "golden_responses"

# LLM parameters (match conf/base/parameters.yml)
DEFAULT_MODEL = "gemma3:12b"
DEFAULT_BASE_URL = "http://localhost:11434"

MIN_MESSAGES = 3


def _user_message_hash(user_message: str) -> str:
    """Compute SHA256 hash of user_message for index lookup."""
    return hashlib.sha256(user_message.encode("utf-8")).hexdigest()[:16]


def _format_conversation_content(messages: list[dict[str, Any]]) -> str:
    """Format messages into conversation text (same as extract_claude/nodes.py)."""
    lines = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        role_label = "Human" if role == "human" else "Assistant"
        lines.append(f"{role_label}: {content}")
    return "\n\n".join(lines)


def _build_genre_prompt() -> str:
    """Build genre prompt matching the organize pipeline config."""
    # Use the same genre definitions as parameters_organize.local.yml.example
    genre_definitions = {
        "ai": "AI/機械学習/LLM/生成AI/Claude/ChatGPT",
        "devops": "インフラ/CI/CD/クラウド/Docker/Kubernetes/AWS",
        "engineer": "プログラミング/アーキテクチャ/API/データベース/フレームワーク",
        "business": "ビジネス/マネジメント/リーダーシップ/マーケティング",
        "economy": "経済/投資/金融/市場",
        "health": "健康/医療/フィットネス/運動",
        "parenting": "子育て/育児/教育/幼児",
        "travel": "旅行/観光/ホテル",
        "lifestyle": "家電/DIY/住居/生活用品",
        "daily": "日常/趣味/雑記",
        "other": "上記に該当しないもの",
    }
    return "\n".join(f"- {k}: {v}" for k, v in genre_definitions.items())


def _build_topic_genre_prompts(body: str) -> tuple[str, str]:
    """Build system_prompt and user_message for extract_topic_and_genre."""
    genre_prompt = _build_genre_prompt()

    system_prompt = f"""あなたはコンテンツ分類の専門家です。会話内容から主題とジャンルを抽出してください。

**主題 (topic)**: カテゴリレベル（1-3単語）で答え、具体的な商品名・料理名・固有名詞ではなく、上位概念で答えてください。
例:
- バナナプリンの作り方 → 離乳食
- iPhone 15 Pro の設定 → スマートフォン
- Claude 3.5 Sonnet の使い方 → AI

**ジャンル (genre)**: 以下のいずれか1つを選んでください（必ず小文字で）:
{genre_prompt}

JSON形式で回答してください:
{{"topic": "主題", "genre": "ジャンル"}}

抽出できない場合:
{{"topic": "", "genre": "other"}}"""

    user_message = f"""会話内容:
{body[:1000]}

主題とジャンルをJSON形式で答えてください。"""

    return system_prompt, user_message


def generate_golden_responses(model: str = DEFAULT_MODEL) -> None:
    """Generate golden responses for all test fixture conversations."""
    # Load test conversations
    with open(CONVERSATIONS_JSON, encoding="utf-8") as f:
        conversations = json.load(f)

    logger.info(f"Loaded {len(conversations)} conversations from {CONVERSATIONS_JSON}")

    # Load prompts
    knowledge_prompt = load_prompt(KNOWLEDGE_PROMPT_PATH)
    _translation_prompt = load_prompt(SUMMARY_PROMPT_PATH)

    # Index: maps function_name:user_message_hash -> golden_file
    index: dict[str, str] = {}

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    for conv in conversations:
        # Validate structure
        if "uuid" not in conv or "chat_messages" not in conv:
            logger.warning(f"Skipping conversation: missing uuid or chat_messages")
            continue

        conv_uuid = conv["uuid"]
        conv_name = conv.get("name")
        created_at = conv.get("created_at")
        raw_messages = conv["chat_messages"]

        # Filter empty messages
        filtered = [msg for msg in raw_messages if msg.get("text", "").strip()]
        if len(filtered) < MIN_MESSAGES:
            logger.info(f"Skipping {conv_uuid}: too few messages ({len(filtered)})")
            continue

        # Normalize messages
        normalized = [{"role": msg["sender"], "content": msg["text"]} for msg in filtered]

        # Format content (same as pipeline)
        content = _format_conversation_content(normalized)

        # Generate file_id (same as pipeline)
        virtual_path = f"conversations/{conv_uuid}.md"
        file_id = generate_file_id(content, virtual_path)

        logger.info(f"Processing {conv_name or conv_uuid} (file_id={file_id})")

        # 1. extract_knowledge
        user_message = _build_user_message(content, conv_name, created_at, "claude")
        try:
            knowledge_response = call_ollama(
                knowledge_prompt,
                user_message,
                model=model,
                num_predict=16384,
                timeout=300,
                warmup_timeout=300,
                temperature=0.2,
            )
            golden_file = f"{file_id}_extract_knowledge.txt"
            (GOLDEN_DIR / golden_file).write_text(knowledge_response, encoding="utf-8")
            msg_hash = _user_message_hash(user_message)
            index[f"extract_knowledge:{msg_hash}"] = golden_file
            logger.info(f"  extract_knowledge -> {golden_file}")
        except Exception as e:
            logger.error(f"  extract_knowledge FAILED: {e}")
            continue

        # 2. extract_topic_and_genre (using the knowledge response as input body)
        # In the real pipeline, the body is the markdown output with frontmatter.
        # For golden response generation, we use the raw knowledge response as body.
        system_prompt_tg, user_message_tg = _build_topic_genre_prompts(knowledge_response)
        try:
            topic_genre_response = call_ollama(
                system_prompt_tg,
                user_message_tg,
                model=model,
                num_predict=512,
                timeout=120,
                warmup_timeout=300,
                temperature=0.2,
            )
            golden_file_tg = f"{file_id}_extract_topic_and_genre.txt"
            (GOLDEN_DIR / golden_file_tg).write_text(topic_genre_response, encoding="utf-8")
            msg_hash_tg = _user_message_hash(user_message_tg)
            index[f"extract_topic_and_genre:{msg_hash_tg}"] = golden_file_tg
            logger.info(f"  extract_topic_and_genre -> {golden_file_tg}")
        except Exception as e:
            logger.error(f"  extract_topic_and_genre FAILED: {e}")

    # Write index
    index_path = GOLDEN_DIR / "_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    logger.info(f"Index written to {index_path} ({len(index)} entries)")
    logger.info("Done.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate golden LLM responses")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    args = parser.parse_args()
    generate_golden_responses(model=args.model)
