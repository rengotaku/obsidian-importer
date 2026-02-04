"""Golden file comparator for E2E output validation.

This module compares Markdown files from pipeline output against golden reference files,
calculating similarity scores based on frontmatter structure and body text content.

Functions:
    split_frontmatter_and_body: Parse YAML frontmatter and body text
    calculate_frontmatter_similarity: Compare frontmatter dicts
    calculate_body_similarity: Compare body text via difflib
    calculate_total_score: Weighted average of frontmatter and body scores
    compare_directories: Compare all .md files in two directories
"""

from __future__ import annotations

import difflib
import os
from pathlib import Path
from typing import Any

import yaml


def split_frontmatter_and_body(content: str) -> tuple[dict[str, Any], str]:
    """Split Markdown content into YAML frontmatter and body text.

    Args:
        content: Full Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter_dict, body_text)
        If no frontmatter exists, returns ({}, full_content)
    """
    if not content.strip():
        return {}, ""

    lines = content.split("\n")
    if not lines[0].strip() == "---":
        return {}, content

    # Find end of frontmatter
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, content

    # Parse frontmatter YAML
    frontmatter_text = "\n".join(lines[1:end_idx])
    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        frontmatter = {}

    # Extract body (everything after second ---)
    body = "\n".join(lines[end_idx + 1 :])
    return frontmatter, body


def calculate_frontmatter_similarity(actual: dict[str, Any], golden: dict[str, Any]) -> float:
    """Calculate frontmatter similarity score.

    Scoring:
    - Key existence: penalize missing keys in actual
    - file_id: exact match required (critical field)
    - title, tags: difflib similarity

    Args:
        actual: Actual frontmatter dict
        golden: Golden reference frontmatter dict

    Returns:
        Similarity score [0.0, 1.0]
    """
    if not golden:
        return 1.0 if not actual else 0.0

    if not actual:
        return 0.0

    score_components = []

    # Key existence (30% weight)
    golden_keys = set(golden.keys())
    actual_keys = set(actual.keys())
    key_match_ratio = len(actual_keys & golden_keys) / len(golden_keys) if golden_keys else 1.0
    score_components.append(("key_existence", key_match_ratio, 0.3))

    # file_id exact match (40% weight)
    if "file_id" in golden:
        file_id_match = 1.0 if actual.get("file_id") == golden["file_id"] else 0.0
        score_components.append(("file_id", file_id_match, 0.4))

    # title similarity (20% weight)
    if "title" in golden and "title" in actual:
        title_sim = difflib.SequenceMatcher(
            None, str(actual["title"]), str(golden["title"])
        ).ratio()
        score_components.append(("title", title_sim, 0.2))

    # tags similarity (10% weight)
    if "tags" in golden and "tags" in actual:
        actual_tags = set(actual["tags"]) if isinstance(actual["tags"], list) else set()
        golden_tags = set(golden["tags"]) if isinstance(golden["tags"], list) else set()
        if golden_tags:
            tags_sim = len(actual_tags & golden_tags) / len(golden_tags)
        else:
            tags_sim = 1.0 if not actual_tags else 0.0
        score_components.append(("tags", tags_sim, 0.1))

    # Calculate weighted average
    total_score = sum(score * weight for _, score, weight in score_components)
    total_weight = sum(weight for _, _, weight in score_components)

    if total_weight > 0:
        return total_score / total_weight
    return 0.0


def calculate_body_similarity(actual: str, golden: str) -> float:
    """Calculate body text similarity using difflib.SequenceMatcher.

    Args:
        actual: Actual body text
        golden: Golden reference body text

    Returns:
        Similarity score [0.0, 1.0]
    """
    if not golden.strip() and not actual.strip():
        return 1.0

    matcher = difflib.SequenceMatcher(None, actual, golden)
    return matcher.ratio()


def calculate_total_score(frontmatter_score: float, body_score: float) -> float:
    """Calculate weighted total score.

    Args:
        frontmatter_score: Frontmatter similarity [0.0, 1.0]
        body_score: Body similarity [0.0, 1.0]

    Returns:
        Total score = frontmatter_score * 0.3 + body_score * 0.7
    """
    return frontmatter_score * 0.3 + body_score * 0.7


def compare_directories(actual_dir: str, golden_dir: str, threshold: float = 0.9) -> dict[str, Any]:
    """Compare all .md files in actual directory against golden directory.

    Args:
        actual_dir: Directory with actual output files
        golden_dir: Directory with golden reference files
        threshold: Minimum similarity threshold for pass

    Returns:
        Dict with keys:
            - passed: bool (all files >= threshold and count matches)
            - files: list of dicts with:
                - filename: str
                - total_score: float
                - frontmatter_score: float
                - body_score: float
                - missing_keys: list[str]
                - diff_summary: str

    Raises:
        FileNotFoundError: If golden_dir doesn't exist
        ValueError: If golden_dir is empty
    """
    golden_path = Path(golden_dir)
    actual_path = Path(actual_dir)

    if not golden_path.exists():
        raise FileNotFoundError(f"Golden directory not found: {golden_dir}")

    golden_files = sorted(golden_path.glob("*.md"))
    if not golden_files:
        raise ValueError(f"Golden directory is empty: {golden_dir}")

    actual_files = sorted(actual_path.glob("*.md"))

    # File count must match
    file_count_match = len(actual_files) == len(golden_files)

    results = []
    all_passed = file_count_match  # Start with file count check

    for golden_file in golden_files:
        filename = golden_file.name
        actual_file = actual_path / filename

        if not actual_file.exists():
            # Missing file in actual
            results.append(
                {
                    "filename": filename,
                    "total_score": 0.0,
                    "frontmatter_score": 0.0,
                    "body_score": 0.0,
                    "missing_keys": [],
                    "diff_summary": "File missing in actual output",
                }
            )
            all_passed = False
            continue

        # Read files
        with open(golden_file, encoding="utf-8") as f:
            golden_content = f.read()
        with open(actual_file, encoding="utf-8") as f:
            actual_content = f.read()

        # Split and compare
        golden_fm, golden_body = split_frontmatter_and_body(golden_content)
        actual_fm, actual_body = split_frontmatter_and_body(actual_content)

        fm_score = calculate_frontmatter_similarity(actual_fm, golden_fm)
        body_score = calculate_body_similarity(actual_body, golden_body)
        total_score = calculate_total_score(fm_score, body_score)

        # Missing keys
        golden_keys = set(golden_fm.keys())
        actual_keys = set(actual_fm.keys())
        missing_keys = sorted(golden_keys - actual_keys)

        # Diff summary (first 200 chars of diff)
        diff = difflib.unified_diff(
            golden_content.splitlines(keepends=True),
            actual_content.splitlines(keepends=True),
            lineterm="",
        )
        diff_text = "".join(diff)
        diff_summary = diff_text[:200] if diff_text else "No differences"

        results.append(
            {
                "filename": filename,
                "total_score": total_score,
                "frontmatter_score": fm_score,
                "body_score": body_score,
                "missing_keys": missing_keys,
                "diff_summary": diff_summary,
            }
        )

        if total_score < threshold:
            all_passed = False

    return {"passed": all_passed, "files": results}


if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description="Compare actual Markdown output against golden reference files"
    )
    parser.add_argument("--actual", required=True, help="Directory with actual output files")
    parser.add_argument("--golden", required=True, help="Directory with golden reference files")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.9,
        help="Minimum similarity threshold (default: 0.9)",
    )

    args = parser.parse_args()

    try:
        result = compare_directories(args.actual, args.golden, args.threshold)
        print(json.dumps(result, indent=2))

        if not result["passed"]:
            print("\n❌ Comparison failed:", file=sys.stderr)
            for file_result in result["files"]:
                if file_result["total_score"] < args.threshold:
                    print(
                        f"  {file_result['filename']}: {file_result['total_score']:.2%} "
                        f"(threshold: {args.threshold:.0%})",
                        file=sys.stderr,
                    )
                    if file_result["missing_keys"]:
                        print(
                            f"    Missing keys: {', '.join(file_result['missing_keys'])}",
                            file=sys.stderr,
                        )
            sys.exit(1)
        else:
            print("\n✅ All files passed similarity threshold", file=sys.stderr)
            sys.exit(0)

    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)
