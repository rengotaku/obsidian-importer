"""
Prompts - プロンプト管理

プロンプトファイルの読み込みとLLMステージ呼び出しを行う。
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.config import (
    PROMPTS_DIR,
    PROMPT_TEMPLATE_PATH,
    EXAMPLES_DIR,
    STAGE_PROMPTS,
    NEW_STAGE_PROMPTS,
    API_DELAY,
)
from normalizer.io.ollama import call_ollama
from normalizer.state.manager import get_state


# =============================================================================
# Few-shot Examples
# =============================================================================


def load_few_shot_examples() -> list[dict]:
    """Few-shot例をJSONファイルから読み込み"""
    examples = []
    try:
        if EXAMPLES_DIR.exists():
            for json_file in sorted(EXAMPLES_DIR.glob("example_*.json")):
                with open(json_file, "r", encoding="utf-8") as f:
                    examples.append(json.load(f))
    except (json.JSONDecodeError, OSError):
        pass
    return examples


def format_few_shot_examples(examples: list[dict]) -> str:
    """Few-shot例をプロンプト用にフォーマット"""
    if not examples:
        return "(例なし)"

    lines = []
    for i, ex in enumerate(examples[:5], 1):  # 最大5例
        inp = ex.get("input", {})
        out = ex.get("output", {})

        lines.append(f"### 例{i}")
        lines.append(f"**入力ファイル名**: {inp.get('filename', '')}")
        lines.append(f"**入力内容**:")
        lines.append("```")
        content = inp.get("content", "")[:300]
        if len(inp.get("content", "")) > 300:
            content += "..."
        lines.append(content)
        lines.append("```")
        lines.append(f"**出力**:")
        lines.append("```json")
        # 主要フィールドのみ表示
        output_preview = {
            "genre": out.get("genre"),
            "confidence": out.get("confidence"),
            "is_dust": out.get("is_dust"),
            "frontmatter": out.get("frontmatter"),
        }
        lines.append(json.dumps(output_preview, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def build_dynamic_prompt() -> str:
    """Phase 3: US1 - タグ辞書とFew-shot例を含む動的プロンプトを構築"""
    from normalizer.validators.tags import load_tag_dictionary, format_tag_dictionary

    # テンプレート読み込み
    if PROMPT_TEMPLATE_PATH.exists():
        template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    else:
        return ""  # テンプレートがない場合は空

    # タグ辞書
    tag_dict = load_tag_dictionary()
    formatted_tags = format_tag_dictionary(tag_dict)

    # Few-shot例
    examples = load_few_shot_examples()
    formatted_examples = format_few_shot_examples(examples)

    # プレースホルダ置換
    prompt = template.replace("{{TAG_DICTIONARY}}", formatted_tags)
    prompt = prompt.replace("{{FEW_SHOT_EXAMPLES}}", formatted_examples)

    return prompt


def get_system_prompt(force_reload: bool = False) -> str:
    """システムプロンプトを取得（キャッシュ付き）"""
    state_mgr = get_state()

    if state_mgr.cached_prompt is None or force_reload:
        dynamic_prompt = build_dynamic_prompt()
        if dynamic_prompt:
            state_mgr.cached_prompt = dynamic_prompt
        else:
            # フォールバック
            from normalizer.config import NORMALIZER_SYSTEM_PROMPT
            state_mgr.cached_prompt = NORMALIZER_SYSTEM_PROMPT

    return state_mgr.cached_prompt


# =============================================================================
# Stage Prompt Loading
# =============================================================================


def load_prompt(stage_name: str) -> str:
    """
    指定されたstageのプロンプトをファイルから読み込む

    Args:
        stage_name: stage1_dust, stage2_genre, stage3_normalize, stage4_metadata,
                    stage_a_classify, stage_c_metadata のいずれか

    Returns:
        プロンプト文字列

    Raises:
        FileNotFoundError: プロンプトファイルが存在しない場合
        ValueError: 無効なstage_name
    """
    # 新しいステージプロンプトを優先
    all_prompts = {**STAGE_PROMPTS, **NEW_STAGE_PROMPTS}

    if stage_name not in all_prompts:
        raise ValueError(f"Unknown stage: {stage_name}. Valid stages: {list(all_prompts.keys())}")

    prompt_path = all_prompts[stage_name]
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


# =============================================================================
# LLM Stage Calling
# =============================================================================


def call_llm_for_stage(
    system_prompt: str,
    content: str,
    filename: str,
    extra_context: str = ""
) -> tuple[str, str | None]:
    """
    Multi-stage pipeline用のLLM呼び出し

    Args:
        system_prompt: ステージ固有のシステムプロンプト
        content: 処理対象コンテンツ
        filename: ファイル名（プロンプトに含める）
        extra_context: 追加コンテキスト（ジャンル、言語情報など）

    Returns:
        tuple: (response_content, error_message)
    """
    # ユーザーメッセージを構築
    user_message_parts = [f"ファイル名: {filename}"]
    if extra_context:
        user_message_parts.append(extra_context)
    user_message_parts.append(f"\n内容:\n{content}")

    user_message = "\n".join(user_message_parts)

    return call_ollama(system_prompt, user_message)


# =============================================================================
# Stage Debug Mode
# =============================================================================


def set_stage_debug_mode(enabled: bool) -> None:
    """Enable or disable stage debug output"""
    state_mgr = get_state()
    state_mgr.stage_debug_mode = enabled


def print_stage_debug(stage: str, result: dict, timing_ms: int = 0) -> None:
    """Print stage debug information"""
    state_mgr = get_state()
    if not state_mgr.stage_debug_mode:
        return

    print(f"\n{'='*60}")
    print(f"Stage: {stage} ({timing_ms}ms)")
    print(f"{'='*60}")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
