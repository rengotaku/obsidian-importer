#!/usr/bin/env python3
"""Test stripping language identifier from outer code fence."""

import re
import sys
from pathlib import Path

sys.path.insert(0, "src")

from obsidian_etl.utils.ollama import parse_markdown_response

EVIDENCE_DIR = Path("specs/056-fix-markdown-codeblock/evidence")


def strip_fence_language(text: str) -> str:
    """Strip language identifier from opening code fences.

    ```markdown  ->  ```
    ```python    ->  ```
    """
    # Only strip from the FIRST line if it's a fence
    lines = text.split("\n")
    if lines and lines[0].strip().startswith("```"):
        # Replace ```<lang> with ```
        lines[0] = re.sub(r"^(\s*)```[a-zA-Z0-9]*\s*$", r"\1```", lines[0])
    return "\n".join(lines)


def test_with_truncated_response():
    """Test with a response that has unclosed outer fence."""
    # Load a known problematic response (outer fence not closed)
    raw_file = EVIDENCE_DIR / "response_unlimited_20260217_182123_raw.txt"
    if not raw_file.exists():
        print(f"File not found: {raw_file}")
        return

    raw_response = raw_file.read_text()

    print("=== Original Response ===")
    print(f"Length: {len(raw_response)} chars")
    print(f"Starts with ```markdown: {raw_response.strip().startswith('```markdown')}")
    print(f"Ends with ```: {raw_response.strip().endswith('```')}")

    # Try parsing original
    print("\n=== Parsing Original ===")
    result, error = parse_markdown_response(raw_response)
    print(f"Error: {error}")
    print(f"Title: '{result.get('title', '')}'")
    print(f"Summary content length: {len(result.get('summary_content', ''))}")

    # Strip language identifier
    modified = strip_fence_language(raw_response)

    print("\n=== Modified Response ===")
    print(f"First line: '{modified.split(chr(10))[0]}'")
    print(f"Starts with ```: {modified.strip().startswith('```')}")
    print(f"Starts with ```markdown: {modified.strip().startswith('```markdown')}")

    # Try parsing modified
    print("\n=== Parsing Modified ===")
    result2, error2 = parse_markdown_response(modified)
    print(f"Error: {error2}")
    print(f"Title: '{result2.get('title', '')}'")
    print(f"Summary content length: {len(result2.get('summary_content', ''))}")

    # The real question: does stripping help when outer fence is NOT closed?
    print("\n=== Analysis ===")
    if not raw_response.strip().endswith("```"):
        print("Outer fence is NOT closed in original.")
        print("Stripping language identifier won't help - closing fence is missing entirely.")
    else:
        print("Outer fence IS closed. Testing if stripping helps...")


def test_fence_pattern():
    """Test the fence pattern matching with different inputs."""
    import re

    # Current pattern
    fence_pattern = re.compile(
        r"^\s*```(?:markdown)?\s*\n([\s\S]*?)\n\s*```\s*$",
        re.DOTALL,
    )

    test_cases = [
        ("```markdown\ncontent\n```", "markdown fence, closed"),
        ("```\ncontent\n```", "plain fence, closed"),
        ("```markdown\ncontent", "markdown fence, NOT closed"),
        ("```\ncontent", "plain fence, NOT closed"),
        ("```markdown\n# Title\n```python\ncode\n```\nmore\n```", "nested code block"),
    ]

    print("=== Fence Pattern Tests ===")
    for test_input, description in test_cases:
        match = fence_pattern.match(test_input)
        print(f"\n{description}:")
        print(f"  Input: {test_input[:50]}...")
        print(f"  Match: {match is not None}")
        if match:
            print(f"  Content: {match.group(1)[:30]}...")


if __name__ == "__main__":
    test_fence_pattern()
    print("\n" + "=" * 60 + "\n")
    test_with_truncated_response()
