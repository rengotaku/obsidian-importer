# Phase 1: Setup Output

**Feature**: 051-ollama-params-config
**Date**: 2026-02-15
**Status**: Completed

## Summary

Phase 1 (Setup) completed successfully. Reviewed existing implementation and updated `parameters.yml` with the new `ollama` structure.

## Tasks Completed

| Task | Description | Status |
|------|-------------|--------|
| T001 | Read `src/obsidian_etl/utils/ollama.py` | ✅ |
| T002 | Read `src/obsidian_etl/utils/knowledge_extractor.py` | ✅ |
| T003 | Read `src/obsidian_etl/pipelines/organize/nodes.py` | ✅ |
| T004 | Read `conf/base/parameters.yml` | ✅ |
| T005 | Read `tests/pipelines/transform/test_nodes.py` | ✅ |
| T006 | Read `tests/pipelines/organize/test_nodes.py` | ✅ |
| T007 | Update `conf/base/parameters.yml` with new ollama structure | ✅ |
| T008 | Run `make test` to verify existing tests pass | ✅ |
| T009 | Generate phase output | ✅ |

## Code Analysis

### Current Implementation

| File | Functions | Parameter Access |
|------|-----------|------------------|
| `ollama.py` | `call_ollama()` | Direct args (model, base_url, timeout, etc.) |
| `knowledge_extractor.py` | `extract_knowledge()`, `translate_summary()` | `params.get("ollama", {})` |
| `organize/nodes.py` | `_extract_topic_via_llm()` | `params.get("ollama", {})` + `requests.post` |

### Current Parameter Structure

**Before (legacy)**:
```yaml
import:
  ollama:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    max_retries: 3

organize:
  ollama:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 60
```

### Updated Parameter Structure

**After (new)**:
```yaml
ollama:
  defaults:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    num_predict: -1

  functions:
    extract_knowledge:
      num_predict: 16384
      timeout: 300
    translate_summary:
      num_predict: 1024
    extract_topic:
      model: "llama3.2:3b"
      num_predict: 64
      timeout: 30
```

**Backward Compatibility**: Legacy `import.ollama` and `organize.ollama` sections retained (marked deprecated).

## Test Results

```
Ran 313 tests in 0.916s
OK
```

All existing tests pass after `parameters.yml` update.

## Key Findings

1. **`_extract_topic_via_llm`** uses `requests.post` directly instead of `call_ollama`
   - Uses `/api/generate` endpoint (not `/api/chat`)
   - No `temperature`, `num_predict` support
   - → Will be refactored in Phase 4 (US3)

2. **`extract_knowledge` / `translate_summary`** use consistent pattern:
   - `params.get("ollama", {}).get("key", default)`
   - → Will be updated to use `get_ollama_config()` in Phase 5

3. **New helper needed**: `get_ollama_config(params, function_name) -> dict`
   - Merge defaults + function-specific overrides
   - Validate parameter ranges
   - Handle legacy fallback

## Next Phase

Phase 2: User Story 1 - 関数別パラメーター設定 (TDD)
- Create `tests/utils/test_ollama_config.py` (RED)
- Implement `src/obsidian_etl/utils/ollama_config.py` (GREEN)
