#!/usr/bin/env python3
"""Check the original problematic file parsing."""

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

# Load the original problematic file
json_path = Path("data/03_primary/transformed_knowledge/31e99f19afcd_chunk6.json")
data = json.loads(json_path.read_text())

gm = data.get("generated_metadata", {})
summary_content = gm.get("summary_content", "")

print("=== Original Issue File Analysis ===")
print(f"File: {json_path.name}")
print(f"Title: {gm.get('title', 'N/A')}")
print(f"Summary length: {len(gm.get('summary', ''))}")
print(f"Summary content length: {len(summary_content)}")

if summary_content:
    lines = summary_content.split("\n")
    opens = []
    closes = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if stripped == "```":
                closes.append((i, stripped))
            else:
                opens.append((i, stripped))

    print(f"\nCode block opens ({len(opens)}):")
    for line_num, content in opens:
        print(f"  Line {line_num}: {content}")

    print(f"\nCode block closes ({len(closes)}):")
    for line_num, content in closes:
        print(f"  Line {line_num}: {content}")

    print(f"\nDiff: {len(opens) - len(closes)} unclosed")

    print("\n=== Last 10 lines ===")
    for i, line in enumerate(lines[-10:], max(1, len(lines) - 9)):
        print(f"{i:4d}: {line[:80]}")
