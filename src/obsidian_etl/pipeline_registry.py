"""Pipeline registry for obsidian-etl.

Registers named pipelines for each import provider.
"""

from __future__ import annotations

from kedro.pipeline import Pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Register project pipelines.

    Returns:
        Dict mapping pipeline names to Pipeline objects.
    """
    return {
        "__default__": Pipeline([]),
    }
