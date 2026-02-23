---
name: ollama-production-readiness
description: "Ensure Ollama integration is production-ready with validation, preloading, timeout configuration, and error handling"
---

# Ollama Production Readiness

## Problem

Ollama integration often fails in production due to four common issues:

1. **Model Name Mismatches**: Config specifies `oss-gpt:20b`, actual model is `gpt-oss:20b`
2. **Improper Error Handling**: Switching to alternative models instead of fixing root cause
3. **Timeout Failures**: Default 30s timeout insufficient for large models (~55s load time)
4. **Cold Start Issues**: First API call fails because model isn't preloaded

**Real-World Impact:**
- Pipeline failures on first run
- Cryptic "Not Found" or timeout errors
- Time wasted debugging instead of running
- Inconsistent behavior between environments

## Solution

Implement a comprehensive Ollama readiness check covering all four areas:

### 1. Model Name Validation

Verify configured model exists before any API calls:

```python
import requests
from typing import List, Optional

def validate_ollama_model(
    model_name: str,
    ollama_base_url: str = "http://localhost:11434"
) -> None:
    """
    Validate that the specified Ollama model is available.

    Raises:
        ValueError: If model not found (with suggestions)
        ConnectionError: If Ollama unreachable
    """
    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        response.raise_for_status()

        available = [m["name"] for m in response.json().get("models", [])]

        if model_name not in available:
            # Find similar names
            suggestions = [m for m in available if model_name.split(':')[0] in m]

            raise ValueError(
                f"Model '{model_name}' not found in Ollama.\n"
                f"Available models: {', '.join(available)}\n"
                f"Similar names: {', '.join(suggestions) if suggestions else 'none'}\n"
                f"Run 'ollama list' to verify."
            )

    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to Ollama at {ollama_base_url}.\n"
            f"Ensure Ollama is running: 'ollama serve'"
        )
```

### 2. Model Preloading (Warmup)

Load model into memory before pipeline execution:

```python
def warmup_ollama_model(
    model_name: str,
    ollama_base_url: str = "http://localhost:11434",
    timeout: int = 120
) -> None:
    """
    Preload model into memory to avoid cold start delays.

    Args:
        model_name: Model to preload (e.g., "gpt-oss:20b")
        timeout: Max wait time for model loading (default: 120s)
    """
    import time

    print(f"Preloading model '{model_name}'...")
    start = time.time()

    try:
        response = requests.post(
            f"{ollama_base_url}/api/generate",
            json={"model": model_name, "prompt": "warmup", "stream": False},
            timeout=timeout
        )
        response.raise_for_status()

        elapsed = time.time() - start
        print(f"Model loaded in {elapsed:.1f}s")

    except requests.exceptions.Timeout:
        raise TimeoutError(
            f"Model '{model_name}' took >{timeout}s to load. "
            f"Consider increasing timeout or using a smaller model."
        )
```

### 3. Adaptive Timeout Configuration

Calculate timeout based on model size:

```python
def get_recommended_timeout(model_name: str) -> int:
    """
    Recommend timeout based on model size.

    Returns:
        Recommended timeout in seconds
    """
    # Extract size from model name (e.g., "gpt-oss:20b" -> 20)
    try:
        size_str = model_name.split(':')[-1].replace('b', '')
        size_gb = int(size_str)

        # Rule of thumb: ~3s per GB + 30s base
        return 30 + (size_gb * 3)

    except (ValueError, IndexError):
        # Default fallback for unknown sizes
        return 60

# Usage
timeout = get_recommended_timeout("gpt-oss:20b")  # Returns 90s
```

### 4. Comprehensive Startup Check

Combine all validations:

```python
def ensure_ollama_ready(
    model_name: str,
    ollama_base_url: str = "http://localhost:11434",
    preload: bool = True
) -> dict:
    """
    Comprehensive Ollama readiness check.

    Returns:
        Dict with status, timeout recommendation, and warnings

    Raises:
        Exception if Ollama is not ready
    """
    result = {
        "model": model_name,
        "validated": False,
        "preloaded": False,
        "recommended_timeout": 60,
        "warnings": []
    }

    # Step 1: Validate model exists
    validate_ollama_model(model_name, ollama_base_url)
    result["validated"] = True

    # Step 2: Calculate optimal timeout
    timeout = get_recommended_timeout(model_name)
    result["recommended_timeout"] = timeout

    # Step 3: Preload if requested
    if preload:
        warmup_ollama_model(model_name, ollama_base_url, timeout)
        result["preloaded"] = True
    else:
        result["warnings"].append(
            "Model not preloaded - first call may timeout"
        )

    return result

# Use at pipeline startup
status = ensure_ollama_ready(config["model"], preload=True)
print(f"Ollama ready: {status}")
```

## When to Use

Apply this pattern when:

- **Integrating Ollama**: Any project using Ollama for LLM inference
- **Pipeline Automation**: Kedro, Airflow, or batch processing systems
- **Production Deployments**: Ensuring reliability in automated environments
- **CI/CD Integration**: Validating Ollama setup in test pipelines
- **Multi-Environment**: Dev/staging/prod with different model availability

## Implementation Checklist

Before going to production:

- [ ] Model name validation at startup
- [ ] Model preloading (warmup) before first use
- [ ] Timeout adjusted for model size (30s base + 3s per GB)
- [ ] Error messages show available models
- [ ] `make warmup` or equivalent documented
- [ ] CI/CD includes Ollama health check

## Makefile Integration

```makefile
.PHONY: warmup
warmup:  ## Preload Ollama model
	@echo "Warming up Ollama model..."
	@curl -s http://localhost:11434/api/generate \
		-d '{"model": "$(MODEL)", "prompt": "warmup"}' > /dev/null
	@echo "Model ready"

.PHONY: check-ollama
check-ollama:  ## Verify Ollama setup
	@echo "Checking Ollama connection..."
	@curl -f http://localhost:11434/api/tags > /dev/null || \
		(echo "ERROR: Ollama not running" && exit 1)
	@echo "Verifying model $(MODEL)..."
	@ollama list | grep -q "$(MODEL)" || \
		(echo "ERROR: Model $(MODEL) not found" && ollama list && exit 1)
	@echo "Ollama ready ✓"

# Add to pipeline
run: check-ollama warmup
	kedro run
```

## Anti-Patterns to Avoid

❌ **Don't**: Switch to different model when configured model fails
✅ **Do**: Fix the root cause (config or missing model)

❌ **Don't**: Use default 30s timeout for all models
✅ **Do**: Calculate timeout based on model size

❌ **Don't**: Assume model is loaded on first call
✅ **Do**: Explicitly preload before pipeline starts

❌ **Don't**: Show cryptic "Not Found" errors
✅ **Do**: Display available models and suggestions

## Related Issues

- Configuration management across environments
- Service health checks in distributed systems
- Cold start optimization for serverless functions
- Timeout tuning for external API calls

## Benefits

- **Fail Fast**: Catch configuration errors before processing starts
- **Reliable Execution**: Preloading eliminates timeout failures
- **Clear Diagnostics**: Users see exactly what's wrong and how to fix
- **Production Grade**: Handles real-world model loading times
- **Time Savings**: 10 minutes debugging → 10 seconds validation
