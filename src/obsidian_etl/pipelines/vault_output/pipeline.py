"""Vault Output pipeline.

This pipeline provides organized file preview and copying to Obsidian Vaults.
"""

from __future__ import annotations

from kedro.pipeline import Pipeline, node

from .nodes import check_conflicts, log_preview_summary, resolve_vault_destination


def create_preview_pipeline(**kwargs) -> Pipeline:
    """Create preview pipeline for organized files.

    Shows destination paths and conflicts without copying files.

    Returns:
        Pipeline: Preview pipeline with destination resolution,
                 conflict detection, and summary logging.
    """
    return Pipeline(
        [
            node(
                func=resolve_vault_destination,
                inputs=["organized_files", "params:organize"],
                outputs="vault_destinations",
                name="resolve_vault_destination_node",
            ),
            node(
                func=check_conflicts,
                inputs="vault_destinations",
                outputs="vault_conflicts",
                name="check_conflicts_node",
            ),
            node(
                func=log_preview_summary,
                inputs=["vault_destinations", "vault_conflicts"],
                outputs="preview_summary",
                name="log_preview_summary_node",
            ),
        ]
    )
