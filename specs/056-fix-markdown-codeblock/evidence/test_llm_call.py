#!/usr/bin/env python3
"""Test LLM response format and save evidence."""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from obsidian_etl.utils.ollama import call_ollama
from obsidian_etl.utils.knowledge_extractor import load_prompt, KNOWLEDGE_PROMPT_PATH

EVIDENCE_DIR = Path(__file__).parent


def save_evidence(name, content):
    """Save evidence file."""
    filepath = EVIDENCE_DIR / name
    filepath.write_text(content, encoding="utf-8")
    print(f"Saved: {filepath}")
    return filepath


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Load the actual prompt
    system_prompt = load_prompt(KNOWLEDGE_PROMPT_PATH)

    # Test case: Simple short content
    test_user_message = """ファイル名: テスト会話
プロバイダー: claude
会話サマリー: なし
会話作成日: 2024-01-01

--- 会話内容 ---