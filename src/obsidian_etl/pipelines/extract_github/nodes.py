"""Nodes for GitHub Jekyll Extract pipeline."""

from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

# GitHub URL pattern for tree view
GITHUB_URL_PATTERN = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/tree/(?P<branch>[^/]+)/(?P<path>.+)"
)

# Date extraction patterns
DATE_PATTERNS = [
    r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})",  # 2024-09-10
    r"(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})",  # 2024/09/10
    r"(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日",  # 2024年9月10日
]

# Hashtag extraction pattern
HASHTAG_PATTERN = re.compile(r"(?<!\S)#([a-zA-Z][a-zA-Z0-9_-]*)")

# Frontmatter pattern
FRONTMATTER_PATTERN = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)


def clone_github_repo(url: str, params: dict) -> dict[str, callable]:
    """Clone GitHub repository and return Markdown files as PartitionedDataset.

    Args:
        url: GitHub URL (format: https://github.com/{owner}/{repo}/tree/{branch}/{path}).
        params: Pipeline parameters (must contain "github_clone_dir" for target directory).

    Returns:
        Dict of filename -> callable returning Markdown content.
        Empty dict if URL is invalid or clone fails.
    """
    # Parse GitHub URL
    match = GITHUB_URL_PATTERN.match(url)
    if not match:
        return {}

    owner = match.group("owner")
    repo = match.group("repo")
    branch = match.group("branch")
    path = match.group("path")

    # Get target directory from params
    target_dir = Path(params.get("github_clone_dir", tempfile.mkdtemp(prefix="github_clone_")))
    clone_dir = target_dir / "repo"

    # Clone with sparse-checkout
    clone_url = f"https://github.com/{owner}/{repo}.git"
    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                "-b",
                branch,
                clone_url,
                str(clone_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Set sparse-checkout path
        subprocess.run(
            ["git", "-C", str(clone_dir), "sparse-checkout", "set", path],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return {}

    # Find Markdown files
    target_path = clone_dir / path
    if not target_path.exists():
        return {}

    md_files = list(target_path.glob("**/*.md"))

    # Return PartitionedDataset-style dict (filename -> callable)
    result = {}
    for md_file in md_files:
        # Use relative path from target_path as key
        rel_path = md_file.relative_to(target_path)
        key = str(rel_path)

        # Create loader callable
        def make_loader(file_path: Path) -> callable:
            def loader() -> str:
                return file_path.read_text(encoding="utf-8")

            return loader

        result[key] = make_loader(md_file)

    return result


def parse_jekyll(
    partitioned_input: dict[str, callable], existing_output: dict | None = None
) -> dict[str, dict]:
    """Parse Jekyll Markdown files to ParsedItem dicts.

    Args:
        partitioned_input: Dict of filename -> callable returning Markdown content.
        existing_output: Unused parameter for backward compatibility (idempotent pattern).

    Returns:
        Dict of item_id -> ParsedItem dict.
        Excludes files with draft: true or private: true.
    """
    result = {}

    for filename, loader in partitioned_input.items():
        # Skip non-Markdown files
        if not filename.endswith(".md"):
            continue

        # Load content
        content = loader()

        # Parse frontmatter
        frontmatter, body = _parse_frontmatter(content)

        # Skip draft or private posts
        if frontmatter.get("draft") is True:
            continue
        if frontmatter.get("private") is True:
            continue

        # Extract fields
        title = frontmatter.get("title", _title_from_filename(filename))
        created_at = _extract_date(frontmatter, filename, title, body)

        # Generate file_id (SHA256 hash, first 12 chars)
        file_id = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

        # Build ParsedItem (E-2 schema)
        parsed_item = {
            "item_id": file_id,
            "source_provider": "github",
            "source_path": filename,
            "conversation_name": title,
            "created_at": created_at,
            "messages": [],  # GitHub posts are not conversations
            "content": body.strip(),
            "file_id": file_id,
            "is_chunked": False,
            "chunk_index": None,
            "total_chunks": None,
            "parent_item_id": None,
        }

        result[file_id] = parsed_item

    return result


def convert_frontmatter(partitioned_input: dict[str, callable]) -> dict[str, dict]:
    """Convert Jekyll frontmatter to Obsidian format.

    Args:
        partitioned_input: Dict of filename -> callable returning Markdown content.

    Returns:
        Dict of item_id -> item dict with Obsidian frontmatter and markdown_content.
    """
    result = {}

    for filename, loader in partitioned_input.items():
        if not filename.endswith(".md"):
            continue

        content = loader()
        frontmatter, body = _parse_frontmatter(content)

        # Skip draft/private
        if frontmatter.get("draft") is True or frontmatter.get("private") is True:
            continue

        # Extract fields
        title = frontmatter.get("title", _title_from_filename(filename))
        created_at = _extract_date(frontmatter, filename, title, body)
        tags = _extract_tags(frontmatter, body)

        # Generate file_id
        file_id = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

        # Build Obsidian frontmatter
        obsidian_fm = {
            "title": title,
            "created": created_at,
            "tags": tags,
            "normalized": True,
            "file_id": file_id,
        }

        # Generate Markdown content with YAML frontmatter
        frontmatter_yaml = yaml.dump(
            obsidian_fm, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        markdown_content = f"---\n{frontmatter_yaml}---\n\n{body.strip()}"

        # Build output item
        item = {
            "item_id": file_id,
            "source_provider": "github",
            "source_path": filename,
            "conversation_name": title,
            "created_at": created_at,
            "messages": [],
            "content": body.strip(),
            "file_id": file_id,
            "is_chunked": False,
            "chunk_index": None,
            "total_chunks": None,
            "parent_item_id": None,
            "tags": tags,
            "markdown_content": markdown_content,
            "output_filename": f"{title}.md",
        }

        result[file_id] = item

    return result


# --- Helper functions ---


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse Jekyll frontmatter from Markdown content.

    Args:
        content: Markdown file content.

    Returns:
        Tuple of (frontmatter dict, body content).
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            return {}, content
    except yaml.YAMLError:
        return {}, content

    body = content[match.end() :]
    return frontmatter, body


def _title_from_filename(filename: str) -> str:
    """Extract title from filename.

    Args:
        filename: Markdown filename.

    Returns:
        Title derived from filename (strip date prefix and extension).
    """
    # Strip path components
    name = Path(filename).stem

    # Remove Jekyll date prefix (YYYY-MM-DD-)
    title = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)

    # Replace hyphens/underscores with spaces
    title = title.replace("-", " ").replace("_", " ")

    # Capitalize first letter of each word
    return title.title()


def _extract_date(frontmatter: dict, filename: str, title: str, body: str) -> str:
    """Extract date from multiple sources with priority fallback.

    Priority:
    1. frontmatter.date (supports ISO 8601)
    2. Filename (Jekyll format: YYYY-MM-DD-*)
    3. Title (regex extraction)
    4. Body (first 1000 chars, regex extraction)
    5. Current date (fallback)

    Args:
        frontmatter: Parsed frontmatter dict.
        filename: Markdown filename.
        title: Document title.
        body: Document body.

    Returns:
        Date string in YYYY-MM-DD format.
    """
    # 1. frontmatter.date (supports ISO 8601)
    if "date" in frontmatter:
        date_str = str(frontmatter["date"])[:10]
        return date_str

    # 2. Filename (Jekyll format)
    jekyll_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", Path(filename).name)
    if jekyll_match:
        return f"{jekyll_match.group(1)}-{jekyll_match.group(2)}-{jekyll_match.group(3)}"

    # 3. Title extraction
    date = _extract_date_from_text(title)
    if date:
        return date

    # 4. Body extraction (first 1000 chars)
    date = _extract_date_from_text(body[:1000])
    if date:
        return date

    # 5. Fallback: current date
    return datetime.now().strftime("%Y-%m-%d")


def _extract_date_from_text(text: str) -> str | None:
    """Extract date from text using multiple patterns.

    Args:
        text: Text to search for dates.

    Returns:
        Date string in YYYY-MM-DD format, or None if not found.
    """
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            groups = match.groupdict()
            return f"{groups['year']}-{int(groups['month']):02d}-{int(groups['day']):02d}"
    return None


def _extract_tags(frontmatter: dict, body: str) -> list[str]:
    """Extract tags from multiple sources.

    Sources (priority order):
    1. frontmatter.tags
    2. frontmatter.categories
    3. frontmatter.keywords
    4. Body hashtags (#tag)

    Args:
        frontmatter: Parsed frontmatter dict.
        body: Document body.

    Returns:
        Deduplicated list of tags.
    """
    tags = []

    # 1. frontmatter.tags
    if "tags" in frontmatter:
        fm_tags = frontmatter["tags"]
        if isinstance(fm_tags, list):
            tags.extend(fm_tags)
        elif isinstance(fm_tags, str):
            tags.append(fm_tags)

    # 2. frontmatter.categories
    if "categories" in frontmatter:
        cats = frontmatter["categories"]
        if isinstance(cats, list):
            tags.extend(cats)
        elif isinstance(cats, str):
            tags.append(cats)

    # 3. frontmatter.keywords
    if "keywords" in frontmatter:
        keywords = frontmatter["keywords"]
        if isinstance(keywords, list):
            tags.extend(keywords)
        elif isinstance(keywords, str):
            tags.append(keywords)

    # 4. Body hashtags
    hashtag_matches = HASHTAG_PATTERN.findall(body)
    tags.extend(hashtag_matches)

    # Deduplicate and filter empty strings
    return sorted(list(set(tag for tag in tags if tag)))
