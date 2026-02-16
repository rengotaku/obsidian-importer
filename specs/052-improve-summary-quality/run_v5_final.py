#!/usr/bin/env python3
"""V5 最終検証スクリプト（表を後から追加する方式）"""

import sys

sys.path.insert(0, "/data/projects/obsidian-importer/specs/052-improve-summary-quality")

from pathlib import Path

import requests
from marker_preprocessor import get_marker_prompt_instruction, postprocess, preprocess

BASE_DIR = Path(__file__).parent / "verification-outputs"
PROMPT_FILE = Path(__file__).parent / "v3-prompt.txt"

SAMPLES = [
    "S1-389c1d35f44f",
    "S2-edb42c441a83",
    "S3-8b8869107b00",
    "S4-1b1679e5dd57",
]

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gpt-oss:20b"


def call_ollama(prompt: str, content: str) -> str:
    """Ollama API を呼び出して結果を返す"""
    full_prompt = f"{prompt}\n\n---\n\n以下の会話ログから知識を抽出してください:\n\n{content}"

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 16384,
        },
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    return response.json().get("response", "")


def main():
    base_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    marker_instruction = get_marker_prompt_instruction()
    prompt = base_prompt + "\n" + marker_instruction

    results = []

    for sample in SAMPLES:
        sample_dir = BASE_DIR / sample
        original_file = sample_dir / "original.md"
        output_file = sample_dir / "v5-output.md"

        if not original_file.exists():
            print(f"⚠️ {sample}: original.md not found")
            continue

        print(f"🔄 {sample}: Processing...")

        content = original_file.read_text(encoding="utf-8")

        # 前処理
        pre_result = preprocess(content)
        code_count = len(pre_result.code_markers)
        table_count = len(pre_result.extracted_tables)

        # LLM呼び出し
        llm_output = call_ollama(prompt, pre_result.processed_text)

        # 後処理
        post_result = postprocess(llm_output, pre_result)

        output_file.write_text(post_result.output, encoding="utf-8")

        # 統計
        original_len = len(content)
        output_len = len(post_result.output)
        ratio = (output_len / original_len * 100) if original_len > 0 else 0

        status = "🔍 REVIEW" if post_result.needs_review else "✅ OK"
        extras = []
        if code_count > 0:
            extras.append(f"code:{code_count}")
        if table_count > 0:
            extras.append(f"table:{table_count}")
        if post_result.fallback_used:
            extras.append("fallback")
        extra_str = f" ({', '.join(extras)})" if extras else ""

        print(f"{status} {sample}: {original_len} → {output_len} chars ({ratio:.1f}%){extra_str}")

        results.append(
            {
                "sample": sample,
                "original": original_len,
                "output": output_len,
                "ratio": ratio,
                "needs_review": post_result.needs_review,
                "code_count": code_count,
                "table_count": table_count,
                "markers_found": len(post_result.markers_found),
                "markers_missing": len(post_result.markers_missing),
            }
        )

    # サマリー
    print("\n" + "=" * 70)
    print("V5 最終検証結果")
    print("=" * 70)
    print(
        f"{'Sample':<20} {'元':<8} {'出力':<8} {'圧縮率':<8} {'Code':<6} {'Table':<6} {'状態':<10}"
    )
    print("-" * 70)
    for r in results:
        status = "REVIEW" if r["needs_review"] else "OK"
        print(
            f"{r['sample']:<20} {r['original']:<8} {r['output']:<8} "
            f"{r['ratio']:.1f}%{'':<4} {r['code_count']:<6} {r['table_count']:<6} {status:<10}"
        )

    print("-" * 70)
    review_count = sum(1 for r in results if r["needs_review"])
    print(f"REVIEW 行き: {review_count}/{len(results)}")


if __name__ == "__main__":
    main()
