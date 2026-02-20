"""Pipeline registry for obsidian-etl.

Registers named pipelines for each import provider.
"""

from __future__ import annotations

from pathlib import Path

from kedro.pipeline import Pipeline
from omegaconf import OmegaConf

from obsidian_etl.pipelines.extract_claude import pipeline as extract_claude
from obsidian_etl.pipelines.extract_github import pipeline as extract_github
from obsidian_etl.pipelines.extract_openai import pipeline as extract_openai
from obsidian_etl.pipelines.organize import pipeline as organize
from obsidian_etl.pipelines.transform import pipeline as transform
from obsidian_etl.pipelines.vault_output import pipeline as vault_output

VALID_PROVIDERS = {"claude", "openai", "github"}


def register_pipelines() -> dict[str, Pipeline]:
    """Register project pipelines.

    Returns:
        Dict mapping pipeline names to Pipeline objects.

    Raises:
        ValueError: If import.provider in parameters.yml is not a valid provider.
    """
    # Load provider from parameters.yml
    params_path = Path(__file__).parent.parent.parent / "conf" / "base" / "parameters.yml"
    config = OmegaConf.load(params_path)
    provider = config["import"]["provider"]

    # Validate provider
    if provider not in VALID_PROVIDERS:
        raise ValueError(
            f"Invalid provider '{provider}'. Valid providers: {sorted(VALID_PROVIDERS)}"
        )

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

    # Build pipeline dictionary with dispatch
    pipelines = {
        "import_claude": import_claude_pipeline,
        "import_openai": import_openai_pipeline,
        "import_github": import_github_pipeline,
        "organize_preview": vault_output.create_preview_pipeline(),
    }

    # Set __default__ based on provider
    pipelines["__default__"] = pipelines[f"import_{provider}"]

    return pipelines
