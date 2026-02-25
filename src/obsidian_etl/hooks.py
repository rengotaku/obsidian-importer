"""Kedro hooks for obsidian-etl.

PreRunValidationHook: Validates prerequisites before pipeline runs.
ErrorHandlerHook: Catches node-level errors and logs details.
LoggingHook: Logs node execution timing.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from kedro.framework.hooks import hook_impl

from obsidian_etl.utils.ollama import OllamaWarmupError

logger = logging.getLogger(__name__)


class PreRunValidationHook:
    """Validates prerequisites before pipeline execution."""

    # Directories that need placeholder files for PartitionedDataset
    # (used as inputs for resume/incremental processing)
    PLACEHOLDER_DIRS = [
        "data/03_primary/transformed_knowledge",
        "data/07_model_output/classified",
    ]

    @hook_impl
    def before_pipeline_run(
        self,
        run_params: dict,
        pipeline: object,
        catalog: object,
    ) -> None:
        """Check prerequisites before running the pipeline."""
        pipeline_name = run_params.get("pipeline_name") or "import_claude"

        # Ensure placeholder files exist for PartitionedDataset inputs
        self._ensure_placeholder_files()

        # Check Ollama is running
        self._check_ollama()

        # Check input files exist
        self._check_input_files(pipeline_name, run_params)

    def _ensure_placeholder_files(self) -> None:
        """Create placeholder files in directories used by PartitionedDataset inputs."""
        import json

        project_root = Path.cwd()
        for dir_path in self.PLACEHOLDER_DIRS:
            full_path = project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            placeholder = full_path / ".placeholder.json"
            if not placeholder.exists():
                placeholder.write_text(json.dumps({"_placeholder": True}))

    def _check_ollama(self) -> None:
        """Verify Ollama server is accessible."""
        import urllib.error
        import urllib.request

        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5):
                pass
        except (urllib.error.URLError, TimeoutError):
            logger.error("")
            logger.error("❌ Error: Ollama is not running")
            logger.error("")
            logger.error("  Ollama は LLM 処理に必要です。起動してください:")
            logger.error("    ollama serve")
            logger.error("")
            sys.exit(1)

    def _check_input_files(self, pipeline_name: str, run_params: dict) -> None:
        """Verify input files exist for the specified pipeline."""
        # Get project root from catalog or use cwd
        project_root = Path.cwd()
        data_dir = project_root / "data" / "01_raw"

        if pipeline_name == "import_claude" or pipeline_name == "__default__":
            input_dir = data_dir / "claude"
            zip_files = list(input_dir.glob("*.zip"))
            if not zip_files:
                logger.error("")
                logger.error("❌ Error: No input files found")
                logger.error("")
                logger.error("  Claude エクスポート ZIP が見つかりません:")
                logger.error(f"    {input_dir}/*.zip")
                logger.error("")
                logger.error("  Claude からエクスポートした ZIP を配置してください:")
                logger.error(f"    cp ~/Downloads/data-*.zip {input_dir}/")
                logger.error("")
                sys.exit(1)

        elif pipeline_name == "import_openai":
            input_dir = data_dir / "openai"
            zip_files = list(input_dir.glob("*.zip"))
            if not zip_files:
                logger.error("")
                logger.error("❌ Error: No input files found")
                logger.error("")
                logger.error("  ChatGPT エクスポート ZIP が見つかりません:")
                logger.error(f"    {input_dir}/*.zip")
                logger.error("")
                logger.error("  ChatGPT Settings > Data controls > Export data")
                logger.error("  でエクスポートしてください")
                logger.error("")
                sys.exit(1)

        elif pipeline_name == "import_github":
            # GitHub URL is passed via params
            extra_params = run_params.get("extra_params", {})
            github_url = extra_params.get("github_url")
            if not github_url:
                logger.error("")
                logger.error("❌ Error: GITHUB_URL is required")
                logger.error("")
                logger.error("  GitHub Jekyll インポートには github_url パラメータが必要です:")
                logger.error(
                    '    kedro run --pipeline=import_github --params=\'{"github_url": "https://github.com/user/repo/tree/master/_posts"}\''
                )
                logger.error("")
                logger.error("  または Makefile 経由:")
                logger.error(
                    '    make run PIPELINE=import_github GITHUB_URL="https://github.com/user/repo/tree/master/_posts"'
                )
                logger.error("")
                sys.exit(1)


class ErrorHandlerHook:
    """Hook that handles node-level errors."""

    @hook_impl
    def on_node_error(
        self,
        error: Exception,
        node: object,
        catalog: object,
        inputs: dict,
        is_async: bool,
    ) -> None:
        """Log error details when a node fails."""
        # Check for OllamaWarmupError (direct or wrapped)
        warmup_error = None
        if isinstance(error, OllamaWarmupError):
            warmup_error = error
        elif error.__cause__ and isinstance(error.__cause__, OllamaWarmupError):
            warmup_error = error.__cause__

        if warmup_error:
            logger.error("")
            logger.error("❌ Error: Ollama model warmup failed")
            logger.error("")
            logger.error(f"  Model: {warmup_error.model}")
            logger.error(f"  Reason: {warmup_error.reason}")
            logger.error("")
            logger.error("  Ollama サーバーが起動していることを確認してください:")
            logger.error("    ollama serve")
            logger.error("")
            logger.error("  モデルがダウンロード済みであることを確認してください:")
            logger.error(f"    ollama pull {warmup_error.model}")
            logger.error("")
            sys.exit(3)

        # Handle other errors with default behavior
        logger.error(f"Node '{node}' failed: {error}")


class LoggingHook:
    """Hook that logs node execution timing."""

    def __init__(self) -> None:
        self._start_times: dict[str, float] = {}

    @hook_impl
    def before_node_run(self, node: object, catalog: object, inputs: dict) -> None:
        """Record start time before node execution."""
        import time

        self._start_times[str(node)] = time.time()

    @hook_impl
    def after_node_run(
        self,
        node: object,
        catalog: object,
        inputs: dict,
        outputs: dict,
        is_async: bool,
    ) -> None:
        """Log elapsed time after node execution."""
        import time

        node_name = str(node)
        start = self._start_times.pop(node_name, None)
        if start is not None:
            elapsed = time.time() - start
            logger.info(f"Node '{node_name}' completed in {elapsed:.2f}s")
