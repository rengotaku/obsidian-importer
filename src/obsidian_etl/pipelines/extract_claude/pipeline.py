"""Claude Extract pipeline definition."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node

from .nodes import parse_claude_json


def create_pipeline(**kwargs) -> Pipeline:
    """Create Claude Extract pipeline.

    This pipeline transforms raw Claude conversations (JSON format) into
    ParsedItem format, the unified intermediate representation.

    Pipeline stages:
        1. parse_claude_json: Parse, validate, chunk, and generate file_id

    Inputs:
        raw_claude_conversations: PartitionedDataset with Claude JSON files

    Outputs:
        parsed_items: PartitionedDataset with ParsedItem dicts

    Returns:
        Kedro Pipeline instance.
    """
    return Pipeline(
        [
            node(
                func=parse_claude_json,
                inputs="raw_claude_conversations",
                outputs="parsed_items",
                name="parse_claude_json",
            ),
        ]
    )
