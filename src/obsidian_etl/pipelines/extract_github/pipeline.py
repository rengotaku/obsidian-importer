"""GitHub Jekyll Extract pipeline definition."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node

from .nodes import clone_github_repo, convert_frontmatter, parse_jekyll


def create_pipeline(**kwargs) -> Pipeline:
    """Create GitHub Jekyll Extract pipeline.

    This pipeline transforms GitHub Jekyll blog posts into ParsedItem format.
    It handles git clone with sparse-checkout, Jekyll frontmatter parsing,
    and conversion to Obsidian format.

    Pipeline stages:
        1. clone_github_repo: Clone repo with sparse-checkout (URL → Markdown files)
        2. parse_jekyll: Parse Jekyll frontmatter and body
        3. convert_frontmatter: Convert Jekyll → Obsidian format

    Inputs:
        params:github_url: GitHub URL (format: https://github.com/{owner}/{repo}/tree/{branch}/{path})
        params:github_clone_dir: Target directory for git clone

    Outputs:
        parsed_items: PartitionedDataset with ParsedItem dicts

    Returns:
        Kedro Pipeline instance.
    """
    return Pipeline(
        [
            node(
                func=clone_github_repo,
                inputs=["params:github_url", "params:parameters"],
                outputs="raw_github_posts",
                name="clone_github_repo",
            ),
            node(
                func=parse_jekyll,
                inputs="raw_github_posts",
                outputs="parsed_github_items",
                name="parse_jekyll",
            ),
            node(
                func=convert_frontmatter,
                inputs="parsed_github_items",
                outputs="parsed_items",
                name="convert_frontmatter",
            ),
        ]
    )
