"""GitHub URL parsing and repository operations.

This module provides utilities for parsing GitHub URLs and cloning repositories.
"""

import hashlib
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# GitHub URL pattern for tree view
GITHUB_URL_PATTERN = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/tree/(?P<branch>[^/]+)/(?P<path>.+)"
)


@dataclass
class GitHubRepoInfo:
    """GitHub repository information parsed from URL."""

    owner: str
    repo: str
    branch: str
    path: str

    @property
    def clone_url(self) -> str:
        """Git clone URL."""
        return f"https://github.com/{self.owner}/{self.repo}.git"

    @property
    def full_path(self) -> str:
        """Full path within repository."""
        return f"{self.repo}/{self.path}"


def parse_github_url(url: str) -> GitHubRepoInfo | None:
    """Parse GitHub URL to extract repository information.

    Args:
        url: GitHub URL in format https://github.com/{owner}/{repo}/tree/{branch}/{path}

    Returns:
        GitHubRepoInfo if URL is valid, None otherwise

    Examples:
        >>> info = parse_github_url("https://github.com/user/repo/tree/master/_posts")
        >>> print(info.owner, info.repo, info.branch, info.path)
        user repo master _posts
    """
    match = GITHUB_URL_PATTERN.match(url)
    if not match:
        return None

    return GitHubRepoInfo(
        owner=match.group("owner"),
        repo=match.group("repo"),
        branch=match.group("branch"),
        path=match.group("path"),
    )


def clone_repo(repo_info: GitHubRepoInfo, target_dir: Path | None = None) -> Path:
    """Clone GitHub repository with sparse-checkout for target path.

    Args:
        repo_info: Repository information
        target_dir: Optional target directory (uses temp dir if None)

    Returns:
        Path to cloned repository directory

    Raises:
        subprocess.CalledProcessError: If git clone fails
    """
    if target_dir is None:
        target_dir = Path(tempfile.mkdtemp(prefix="github_clone_"))

    clone_dir = target_dir / repo_info.repo

    # Clone with sparse-checkout
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--sparse",
            "-b",
            repo_info.branch,
            repo_info.clone_url,
            str(clone_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    # Set sparse-checkout path
    subprocess.run(
        ["git", "-C", str(clone_dir), "sparse-checkout", "set", repo_info.path],
        check=True,
        capture_output=True,
        text=True,
    )

    return clone_dir / repo_info.path


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


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse Jekyll frontmatter from Markdown content.

    Args:
        content: Markdown file content

    Returns:
        Tuple of (frontmatter dict, body content)

    Examples:
        >>> fm, body = parse_frontmatter("---\\ntitle: Test\\n---\\nBody")
        >>> fm["title"]
        'Test'
    """
    import yaml

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


def extract_date_from_text(text: str) -> str | None:
    """Extract date from text using multiple patterns.

    Args:
        text: Text to search for dates

    Returns:
        Date string in YYYY-MM-DD format, or None if not found
    """
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            groups = match.groupdict()
            return f"{groups['year']}-{int(groups['month']):02d}-{int(groups['day']):02d}"
    return None


def extract_date(frontmatter: dict, filename: str, title: str, body: str) -> str:
    """Extract date from multiple sources with priority fallback.

    Priority:
    1. frontmatter.date
    2. Filename (Jekyll format: YYYY-MM-DD-*)
    3. Title (regex extraction)
    4. Body (first 1000 chars, regex extraction)
    5. Current date (fallback)

    Args:
        frontmatter: Parsed frontmatter dict
        filename: Markdown filename
        title: Document title
        body: Document body

    Returns:
        Date string in YYYY-MM-DD format
    """
    # 1. frontmatter.date (supports ISO 8601)
    if "date" in frontmatter:
        date_str = str(frontmatter["date"])[:10]
        return date_str

    # 2. Filename (Jekyll format)
    jekyll_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", filename)
    if jekyll_match:
        return f"{jekyll_match.group(1)}-{jekyll_match.group(2)}-{jekyll_match.group(3)}"

    # 3. Title extraction
    date = extract_date_from_text(title)
    if date:
        return date

    # 4. Body extraction (first 1000 chars)
    date = extract_date_from_text(body[:1000])
    if date:
        return date

    # 5. Fallback: current date
    return datetime.now().strftime("%Y-%m-%d")


def extract_tags(frontmatter: dict, body: str) -> list[str]:
    """Extract tags from multiple sources.

    Sources (priority order):
    1. frontmatter.tags
    2. frontmatter.categories
    3. frontmatter.keywords
    4. Body hashtags (#tag)

    Args:
        frontmatter: Parsed frontmatter dict
        body: Document body

    Returns:
        Deduplicated list of tags
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


def convert_frontmatter(frontmatter: dict, filename: str, body: str, raw_content: str) -> dict:
    """Convert Jekyll frontmatter to Obsidian format.

    Args:
        frontmatter: Parsed Jekyll frontmatter
        filename: Markdown filename
        body: Document body
        raw_content: Full file content (for file_id generation)

    Returns:
        Obsidian frontmatter dict

    Conversion rules:
    - title → title (required, fallback to filename)
    - date → created (YYYY-MM-DD)
    - tags/categories/keywords → tags (merged)
    - Add: normalized=true, file_id (SHA256)
    - Remove: layout, permalink, excerpt, slug, lastmod, headless, draft, private
    """
    obsidian_fm = {}

    # Title (required)
    if "title" in frontmatter:
        obsidian_fm["title"] = frontmatter["title"]
    else:
        # Fallback: filename without extension and date prefix
        title = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", filename)
        title = title.replace(".md", "")
        obsidian_fm["title"] = title

    # Date → created
    title = obsidian_fm["title"]
    created = extract_date(frontmatter, filename, title, body)
    obsidian_fm["created"] = created

    # Tags (merged from multiple sources)
    tags = extract_tags(frontmatter, body)
    if tags:
        obsidian_fm["tags"] = tags

    # Add normalized flag
    obsidian_fm["normalized"] = True

    # Generate file_id (SHA256 hash)
    file_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
    obsidian_fm["file_id"] = file_hash

    return obsidian_fm
