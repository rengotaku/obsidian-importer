"""Organize pipeline definition.

This pipeline handles genre classification and frontmatter embedding:
- classify_genre: Keyword-based genre detection
- extract_topic: LLM-based topic extraction
- normalize_frontmatter: Clean frontmatter fields
- clean_content: Remove excess blank lines
- embed_frontmatter_fields: Embed genre, topic, summary into frontmatter

Review notes (items with low compression ratios) are output directly by
format_markdown to review_notes without further processing.
"""

from __future__ import annotations

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    classify_genre,
    clean_content,
    embed_frontmatter_fields,
    extract_topic,
    normalize_frontmatter,
)


def create_pipeline(**kwargs) -> Pipeline:
    """Create the organize pipeline.

    Args:
        **kwargs: Ignored

    Returns:
        Pipeline: Organize pipeline (classify → extract_topic → normalize → clean → embed)
    """
    return pipeline(
        [
            node(
                func=classify_genre,
                inputs={
                    "partitioned_input": "markdown_notes",
                    "params": "params:organize",
                    "existing_output": "existing_classified_items",
                },
                outputs="classified_items",
                name="classify_genre",
            ),
            node(
                func=extract_topic,
                inputs=["classified_items", "params:organize"],
                outputs="topic_extracted_items",
                name="extract_topic",
            ),
            node(
                func=normalize_frontmatter,
                inputs=["topic_extracted_items", "params:organize"],
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
