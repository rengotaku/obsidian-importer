"""Organize pipeline definition.

This pipeline handles genre classification and frontmatter embedding:
- classify_genre: Keyword-based genre detection (runs on both normal and review notes)
- extract_topic: LLM-based topic extraction
- normalize_frontmatter: Clean frontmatter fields
- clean_content: Remove excess blank lines
- embed_frontmatter_fields: Embed genre, topic, summary, review_reason into frontmatter

This pipeline processes both normal notes (markdown_notes) and review notes (review_notes).
Review notes are flagged items with low compression ratios that require manual review.
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
                 Runs separately for normal and review notes.
    """
    # Normal notes path
    normal_path = [
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

    # Review notes path (same processing, different datasets)
    review_path = [
        node(
            func=classify_genre,
            inputs={
                "partitioned_input": "review_notes",
                "params": "params:organize",
            },
            outputs="classified_review_items",
            name="classify_genre_review",
        ),
        node(
            func=extract_topic,
            inputs=["classified_review_items", "params:organize"],
            outputs="topic_extracted_review_items",
            name="extract_topic_review",
        ),
        node(
            func=normalize_frontmatter,
            inputs=["topic_extracted_review_items", "params:organize"],
            outputs="normalized_review_items",
            name="normalize_frontmatter_review",
        ),
        node(
            func=clean_content,
            inputs="normalized_review_items",
            outputs="cleaned_review_items",
            name="clean_content_review",
        ),
        node(
            func=embed_frontmatter_fields,
            inputs=["cleaned_review_items", "params:organize"],
            outputs="organized_review_notes",
            name="embed_frontmatter_fields_review",
        ),
    ]

    return pipeline(normal_path + review_path)
