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


# Hardcoded defaults - lowest priority in merge hierarchy
HARDCODED_DEFAULTS = {
    "model": "gemma3:12b",
    "base_url": "http://localhost:11434",
    "timeout": 120,
    "temperature": 0.2,
    "num_predict": -1,
}


# Valid function names for per-function config
VALID_FUNCTION_NAMES = {
    "extract_knowledge",
    "translate_summary",
    "extract_topic",
}


def _validate_config(config: dict) -> dict:
    """Validate and sanitize config values.

    Args:
        config: Configuration dictionary to validate

    Returns:
        dict: Validated configuration

    Raises:
        ValueError: If timeout or temperature is out of valid range
    """
    # Timeout validation (1-600 seconds)
    timeout = config.get("timeout", HARDCODED_DEFAULTS["timeout"])
    if timeout < 1 or timeout > 600:
        raise ValueError(f"timeout must be between 1 and 600, got {timeout}")

    # Temperature validation (0.0-2.0)
    temperature = config.get("temperature", HARDCODED_DEFAULTS["temperature"])
    if temperature < 0.0 or temperature > 2.0:
        raise ValueError(f"temperature must be between 0.0 and 2.0, got {temperature}")

    return config


def get_ollama_config(params: dict, function_name: str) -> OllamaConfig:
    """Get Ollama configuration for a specific function with hierarchical merging.

    This function retrieves and merges Ollama configuration parameters from multiple
    sources with well-defined precedence rules, enabling function-specific overrides
    while maintaining sensible defaults.

    Merge Priority (lowest to highest):
        1. HARDCODED_DEFAULTS: Fallback values defined in code
           - model: "gemma3:12b"
           - base_url: "http://localhost:11434"
           - timeout: 120
           - temperature: 0.2
           - num_predict: -1 (unlimited)

        2. ollama.defaults: Common defaults from parameters.yml
           - Applies to all functions unless overridden
           - Example: {"model": "gemma3:12b", "timeout": 120}

        3. ollama.functions.{function_name}: Function-specific overrides
           - Highest priority - overrides both defaults and hardcoded values
           - Example: {"num_predict": 16384, "timeout": 300}

    Valid Function Names:
        - "extract_knowledge": Long output, detailed markdown generation
        - "translate_summary": Medium output, summary translation
        - "extract_topic": Very short output (1-3 words)

    Args:
        params: Parameters dictionary from parameters.yml containing:
            - ollama.defaults (optional): Common default parameters
            - ollama.functions.{function_name} (optional): Function-specific overrides
        function_name: Name of the function requesting configuration.
            Must be one of VALID_FUNCTION_NAMES.

    Returns:
        OllamaConfig: Immutable configuration dataclass with merged parameters:
            - model (str): LLM model name
            - base_url (str): Ollama API endpoint URL
            - timeout (int): Request timeout in seconds (1-600)
            - temperature (float): Sampling temperature (0.0-2.0)
            - num_predict (int): Maximum output tokens (-1 = unlimited)

    Raises:
        ValueError: If timeout is not in range [1, 600] or
                   temperature is not in range [0.0, 2.0]

    Examples:
        Basic usage with defaults only:
        >>> params = {"ollama": {"defaults": {"model": "gemma3:12b"}}}
        >>> config = get_ollama_config(params, "extract_knowledge")
        >>> config.model
        'gemma3:12b'
        >>> config.timeout  # From HARDCODED_DEFAULTS
        120

        Function-specific override:
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
        >>> config.timeout  # Overridden by function config
        300

        Partial override (other values from defaults):
        >>> params = {
        ...     "ollama": {
        ...         "defaults": {"model": "gemma3:12b", "timeout": 120},
        ...         "functions": {"extract_topic": {"num_predict": 64}}
        ...     }
        ... }
        >>> config = get_ollama_config(params, "extract_topic")
        >>> config.num_predict
        64
        >>> config.model  # From defaults
        'gemma3:12b'
    """
    # Get defaults from parameters.yml
    defaults = params.get("ollama", {}).get("defaults", {})

    # Get function-specific overrides from parameters.yml
    overrides = params.get("ollama", {}).get("functions", {}).get(function_name, {})

    # Merge with priority: HARDCODED_DEFAULTS < defaults < overrides
    merged = {**HARDCODED_DEFAULTS, **defaults, **overrides}

    # Validate configuration
    validated = _validate_config(merged)

    return OllamaConfig(**validated)
