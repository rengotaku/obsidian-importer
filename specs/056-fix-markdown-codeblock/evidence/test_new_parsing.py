#!/usr/bin/env python3
"""Test the new parsing logic with language stripping."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from obsidian_etl.utils.ollama import _strip_fence_language, parse_markdown_response


def test_strip_fence_language():
    """Test _strip_fence_language function."""
    print("=== Test _strip_fence_language ===")

    test_cases = [
        ("```markdown\ncontent\n```", "```\ncontent\n```"),
        ("```python\ncode\n```", "```\ncode\n```"),
        ("```\ncontent\n```", "```\ncontent\n```"),
        ("no fence", "no fence"),
        (
            "```markdown\n# Title\n```python\ncode\n```\n```",
            "```\n# Title\n```python\ncode\n```\n```",
        ),
    ]

    for input_text, expected in test_cases:
        result = _strip_fence_language(input_text)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input first line: '{input_text.split(chr(10))[0]}'")
        print(f"   Result first line: '{result.split(chr(10))[0]}'")
        if result != expected:
            print(f"   Expected first line: '{expected.split(chr(10))[0]}'")
        print()


def test_parse_with_responses():
    """Test parsing with actual responses."""
    print("=== Test parse_markdown_response ===")

    evidence_dir = Path("specs/056-fix-markdown-codeblock/evidence")

    # Test with a properly closed response
    test_files = [
        ("response_plainfence_20260218_075028_raw.txt", "```markdown at start, properly closed"),
        ("response_unlimited_20260217_182123_raw.txt", "```markdown at start, NOT closed"),
    ]

    for filename, description in test_files:
        filepath = evidence_dir / filename
        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue

        raw = filepath.read_text()
        print(f"\n--- {description} ---")
        print(f"File: {filename}")
        print(f"First line: '{raw.split(chr(10))[0]}'")
        print(f"Last line: '{raw.split(chr(10))[-1]}'")

        result, error = parse_markdown_response(raw)
        print(f"Error: {error}")
        print(f"Title: '{result.get('title', '')}'")
        print(f"Summary length: {len(result.get('summary', ''))}")
        print(f"Summary content length: {len(result.get('summary_content', ''))}")
        print(f"Tags: {result.get('tags', [])}")


if __name__ == "__main__":
    test_strip_fence_language()
    test_parse_with_responses()
