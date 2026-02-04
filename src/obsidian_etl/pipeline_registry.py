"""Pipeline registry for obsidian-etl.

Registers named pipelines for each import provider.
"""

from __future__ import annotations

from kedro.pipeline import Pipeline

from obsidian_etl.pipelines.extract_claude import pipeline as extract_claude
from obsidian_etl.pipelines.extract_github import pipeline as extract_github
from obsidian_etl.pipelines.extract_openai import pipeline as extract_openai
from obsidian_etl.pipelines.organize import pipeline as organize
from obsidian_etl.pipelines.transform import pipeline as transform


def register_pipelines() -> dict[str, Pipeline]:
    """Register project pipelines.

    Returns:
        Dict mapping pipeline names to Pipeline objects.
    """
    # Create import_claude pipeline: extract_claude + transform + organize
    import_claude_pipeline = (
        extract_claude.create_pipeline() + transform.create_pipeline() + organize.create_pipeline()
    )

    # Create import_openai pipeline: extract_openai + transform + organize
    import_openai_pipeline = (
        extract_openai.create_pipeline() + transform.create_pipeline() + organize.create_pipeline()
    )

    # Create import_github pipeline: extract_github + transform + organize
    import_github_pipeline = (
        extract_github.create_pipeline() + transform.create_pipeline() + organize.create_pipeline()
    )

    return {
        "import_claude": import_claude_pipeline,
        "import_openai": import_openai_pipeline,
        "import_github": import_github_pipeline,
        "__default__": import_claude_pipeline,
    }
