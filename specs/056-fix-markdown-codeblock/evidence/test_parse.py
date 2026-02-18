#!/usr/bin/env python3
"""Test how parse_markdown_response handles truncated response."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from obsidian_etl.utils.ollama import parse_markdown_response

# Load the truncated response
raw_response = Path(
    "specs/056-fix-markdown-codeblock/evidence/response_long_20260217_181400_raw.txt"
).read_text()

print("=== Raw Response Stats ===")
print(f"Length: {len(raw_response)} chars")
print(f"Starts with ```markdown: {raw_response.strip().startswith('```markdown')}")
print(f"Ends with ```: {raw_response.strip().endswith('```')}")

print("\n=== Parsing Response ===")
result, error = parse_markdown_response(raw_response)

print(f"Error: {error}")
print(f"Title: {result.get('title', 'N/A')}")
print(f"Summary length: {len(result.get('summary', ''))}")
print(f"Tags: {result.get('tags', [])}")
print(f"Summary content length: {len(result.get('summary_content', ''))}")

# Check summary_content for unclosed code blocks
summary_content = result.get("summary_content", "")
if summary_content:
    lines = summary_content.split("\n")
    opens = sum(1 for l in lines if l.strip().startswith("```") and l.strip() != "```")
    closes = sum(1 for l in lines if l.strip() == "```")
    print(f"\nSummary content code blocks: opens={opens}, closes={closes}, diff={opens - closes}")

    print("\n=== Last 5 lines of summary_content ===")
    for i, line in enumerate(lines[-5:], max(1, len(lines) - 4)):
        print(f"{i:4d}: {line[:80]}")
