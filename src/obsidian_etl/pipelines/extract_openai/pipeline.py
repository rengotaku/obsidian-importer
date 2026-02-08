"""OpenAI Extract pipeline definition."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node

from .nodes import parse_chatgpt_zip


def create_pipeline(**kwargs) -> Pipeline:
    """Create OpenAI (ChatGPT) Extract pipeline.

    This pipeline transforms raw ChatGPT export ZIP files into
    ParsedItem format, the unified intermediate representation.

    Pipeline stages:
        1. parse_chatgpt_zip: Parse ZIP, traverse mapping tree, convert to ParsedItem

    Inputs:
        raw_openai_conversations: PartitionedDataset with ChatGPT ZIP files

    Outputs:
        parsed_items: PartitionedDataset with ParsedItem dicts

    Returns:
        Kedro Pipeline instance.
    """
    return Pipeline(
        [
            node(
                func=parse_chatgpt_zip,
                inputs={
                    "partitioned_input": "raw_openai_conversations",
                    "params": "params:import",
                },
                outputs="parsed_items",
                name="parse_chatgpt_zip",
            ),
        ]
    )
