"""Claude Extract pipeline definition."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node

from .nodes import parse_claude_zip


def create_pipeline(**kwargs) -> Pipeline:
    """Create Claude Extract pipeline.

    This pipeline transforms raw Claude conversations (ZIP format) into
    ParsedItem format, the unified intermediate representation.

    Pipeline stages:
        1. parse_claude_zip: Extract ZIP, parse, validate, chunk, and generate file_id

    Inputs:
        raw_claude_conversations: PartitionedDataset with Claude ZIP files

    Outputs:
        parsed_items: PartitionedDataset with ParsedItem dicts

    Returns:
        Kedro Pipeline instance.
    """
    return Pipeline(
        [
            node(
                func=parse_claude_zip,
                inputs="raw_claude_conversations",
                outputs="parsed_items",
                name="parse_claude_zip",
            ),
        ]
    )
