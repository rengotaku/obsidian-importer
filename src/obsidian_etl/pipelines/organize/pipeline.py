"""Organize pipeline definition.

This pipeline handles genre classification and Vault placement:
- classify_genre: Keyword-based genre detection
- normalize_frontmatter: Clean frontmatter fields
- clean_content: Remove excess blank lines
- determine_vault_path: Map genre to vault directory
- move_to_vault: Write files to vault
"""

from __future__ import annotations

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    classify_genre,
    clean_content,
    determine_vault_path,
    move_to_vault,
    normalize_frontmatter,
)


def create_pipeline(**kwargs) -> Pipeline:
    """Create the organize pipeline.

    Args:
        **kwargs: Ignored

    Returns:
        Pipeline: Organize pipeline (classify → normalize → clean → determine → move)
    """
    return pipeline(
        [
            node(
                func=classify_genre,
                inputs=["markdown_notes", "params:organize"],
                outputs="classified_items",
                name="classify_genre",
            ),
            node(
                func=normalize_frontmatter,
                inputs=["classified_items", "params:organize"],
                outputs="normalized_items",
                name="normalize_frontmatter",
            ),
            node(
                func=clean_content,
                inputs="normalized_items",
                outputs="cleaned_items",
                name="clean_content",
            ),
            node(
                func=determine_vault_path,
                inputs=["cleaned_items", "params:organize"],
                outputs="vault_determined_items",
                name="determine_vault_path",
            ),
            node(
                func=move_to_vault,
                inputs=["vault_determined_items", "params:organize"],
                outputs="organized_items",
                name="move_to_vault",
            ),
        ]
    )
