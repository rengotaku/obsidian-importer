"""Transform pipeline definition.

This pipeline processes ParsedItems from the Extract pipeline:
1. extract_knowledge: LLM-based knowledge extraction (title, summary, tags)
2. generate_metadata: Metadata generation (file_id, created, normalized)
3. format_markdown: Markdown formatting with YAML frontmatter (split by review_reason)

Pipeline Inputs:
- parsed_items: PartitionedDataset of ParsedItem dicts (from Extract)

Pipeline Outputs:
- markdown_notes: PartitionedDataset of Markdown files (normal, no review_reason)
- review_notes: PartitionedDataset of Markdown files (with review_reason for manual review)
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import extract_knowledge, format_markdown, generate_metadata


def create_pipeline(**kwargs) -> Pipeline:
    """Create the Transform pipeline.

    Args:
        **kwargs: Additional pipeline parameters.

    Returns:
        Transform pipeline.
    """
    return pipeline(
        [
            node(
                func=extract_knowledge,
                inputs={
                    "partitioned_input": "parsed_items",
                    "params": "params:import",
                    "existing_output": "existing_transformed_items_with_knowledge",
                },
                outputs="transformed_items_with_knowledge",
                name="extract_knowledge",
            ),
            node(
                func=generate_metadata,
                inputs=["transformed_items_with_knowledge", "params:import"],
                outputs="transformed_items_with_metadata",
                name="generate_metadata",
            ),
            node(
                func=format_markdown,
                inputs="transformed_items_with_metadata",
                outputs=["markdown_notes", "review_notes"],
                name="format_markdown",
            ),
        ]
    )
