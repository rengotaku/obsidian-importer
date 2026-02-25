"""Organize pipeline definition.

This pipeline handles LLM-based classification and frontmatter embedding:
- extract_topic_and_genre: LLM-based topic and genre extraction
- normalize_frontmatter: Clean frontmatter fields
- clean_content: Remove excess blank lines
- embed_frontmatter_fields: Embed genre, topic, summary into frontmatter

Review notes (items with low compression ratios) are output directly by
format_markdown to review_notes without further processing.
"""

from __future__ import annotations

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    analyze_other_genres,
    clean_content,
    embed_frontmatter_fields,
    extract_topic_and_genre,
    normalize_frontmatter,
)


def create_pipeline(**kwargs) -> Pipeline:
    """Create the organize pipeline.

    Args:
        **kwargs: Ignored

    Returns:
        Pipeline: Organize pipeline (extract_topic_and_genre → analyze_other_genres → normalize → clean → embed)
    """
    return pipeline(
        [
            node(
                func=extract_topic_and_genre,
                inputs=["markdown_notes", "parameters"],
                outputs="classified_items",
                name="extract_topic_and_genre",
            ),
            node(
                func=analyze_other_genres,
                inputs=["classified_items", "parameters"],
                outputs="genre_suggestions_report",
                name="analyze_other_genres",
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
                func=embed_frontmatter_fields,
                inputs=["cleaned_items", "params:organize"],
                outputs="organized_notes",
                name="embed_frontmatter_fields",
            ),
        ]
    )
