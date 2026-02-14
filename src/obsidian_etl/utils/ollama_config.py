"""Ollama configuration management.

This module provides OllamaConfig dataclass and get_ollama_config function
for managing Ollama parameters with function-specific overrides.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OllamaConfig:
    """Ollama configuration for a specific function."""

    model: str = "gemma3:12b"
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    temperature: float = 0.2
    num_predict: int = -1  # -1 = unlimited


# Valid function names for per-function config
VALID_FUNCTION_NAMES = {
    "extract_knowledge",
    "translate_summary",
    "extract_topic",
}


def get_ollama_config(params: dict, function_name: str) -> OllamaConfig:
    """Get Ollama configuration for a specific function.

    Merge priority:
    1. HARDCODED_DEFAULTS (OllamaConfig defaults)
    2. ollama.defaults from parameters.yml
    3. ollama.functions.{function_name} from parameters.yml

    Args:
        params: Parameters dictionary from parameters.yml
        function_name: Name of the function ("extract_knowledge", etc.)

    Returns:
        OllamaConfig: Merged configuration for the function

    Examples:
        >>> params = {
        ...     "ollama": {
        ...         "defaults": {"model": "gemma3:12b", "timeout": 120},
        ...         "functions": {
        ...             "extract_knowledge": {"num_predict": 16384, "timeout": 300}
        ...         }
        ...     }
        ... }
        >>> config = get_ollama_config(params, "extract_knowledge")
        >>> config.num_predict
        16384
        >>> config.timeout
        300
    """
    # Get defaults from parameters.yml
    defaults = params.get("ollama", {}).get("defaults", {})

    # Get function-specific overrides from parameters.yml
    overrides = params.get("ollama", {}).get("functions", {}).get(function_name, {})

    # Merge: defaults first, then overrides
    # OllamaConfig dataclass defaults will be used for any missing fields
    merged = {**defaults, **overrides}

    return OllamaConfig(**merged)
