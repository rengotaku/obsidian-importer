# Phase 5 RED Tests

## Summary
- Phase: Phase 5 - Integration - extract_knowledge and translate_summary use get_ollama_config
- FAIL test count: 4
- Test files: tests/pipelines/transform/test_nodes.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_uses_config | `extract_knowledge` calls `get_ollama_config(params, "extract_knowledge")` |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_num_predict_applied | `extract_knowledge` passes `num_predict=16384` to `call_ollama` |
| tests/pipelines/transform/test_nodes.py | test_translate_summary_uses_config | `translate_summary` calls `get_ollama_config(params, "translate_summary")` |
| tests/pipelines/transform/test_nodes.py | test_translate_summary_num_predict_applied | `translate_summary` passes `num_predict=1024` to `call_ollama` |

## Implementation Hints

### extract_knowledge changes (src/obsidian_etl/utils/knowledge_extractor.py)

Current implementation:
```python
def extract_knowledge(..., params: dict) -> tuple[dict | None, str | None]:
    ...
    ollama_params = params.get("ollama", {})

    response, error = call_ollama(
        prompt,
        user_message,
        model=ollama_params.get("model", "gemma3:12b"),
        base_url=ollama_params.get("base_url", "http://localhost:11434"),
        num_predict=ollama_params.get("num_predict", -1),
        timeout=ollama_params.get("timeout", 120),
        temperature=ollama_params.get("temperature", 0.2),
    )
```

Required changes:
1. Import `get_ollama_config` from `obsidian_etl.utils.ollama_config`
2. Replace direct params access with:
```python
from obsidian_etl.utils.ollama_config import get_ollama_config

def extract_knowledge(..., params: dict) -> tuple[dict | None, str | None]:
    ...
    config = get_ollama_config(params, "extract_knowledge")

    response, error = call_ollama(
        prompt,
        user_message,
        model=config.model,
        base_url=config.base_url,
        num_predict=config.num_predict,
        timeout=config.timeout,
        temperature=config.temperature,
    )
```

### translate_summary changes (src/obsidian_etl/utils/knowledge_extractor.py)

Current implementation:
```python
def translate_summary(summary: str, params: dict) -> tuple[str | None, str | None]:
    ...
    ollama_params = params.get("ollama", {})

    response, error = call_ollama(
        prompt,
        f"...",
        model=ollama_params.get("model", "gemma3:12b"),
        base_url=ollama_params.get("base_url", "http://localhost:11434"),
        num_predict=ollama_params.get("num_predict", -1),
        timeout=ollama_params.get("timeout", 120),
        temperature=ollama_params.get("temperature", 0.2),
    )
```

Required changes:
```python
def translate_summary(summary: str, params: dict) -> tuple[str | None, str | None]:
    ...
    config = get_ollama_config(params, "translate_summary")

    response, error = call_ollama(
        prompt,
        f"...",
        model=config.model,
        base_url=config.base_url,
        num_predict=config.num_predict,
        timeout=config.timeout,
        temperature=config.temperature,
    )
```

## FAIL Output Example

```
======================================================================
ERROR: test_extract_knowledge_uses_config (tests.pipelines.transform.test_nodes.TestExtractKnowledgeUsesOllamaConfig.test_extract_knowledge_uses_config)
extract_knowledge が get_ollama_config を使用してパラメーターを取得すること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/mock.py", line 1423, in patched
    with self.decoration_helper(patched,
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^
                                args,
                                ^^^^^
                                keywargs) as (newargs, newkeywargs):
                                ^^^^^^^^^
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/contextlib.py", line 141, in __enter__
    return next(self.gen)
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/mock.py", line 1405, in decoration_helper
    arg = exit_stack.enter_context(patching)
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/contextlib.py", line 530, in enter_context
    result = _enter(cm)
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/mock.py", line 1497, in __enter__
    original, local = self.get_original()
                      ~~~~~~~~~~~~~~~~~^^
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/mock.py", line 1467, in get_original
    raise AttributeError(
        "%s does not have the attribute %r" % (target, name)
    )
AttributeError: <module 'obsidian_etl.utils.knowledge_extractor' from '/data/projects/obsidian-importer/src/obsidian_etl/utils/knowledge_extractor.py'> does not have the attribute 'get_ollama_config'

======================================================================
ERROR: test_extract_knowledge_num_predict_applied (tests.pipelines.transform.test_nodes.TestExtractKnowledgeUsesOllamaConfig.test_extract_knowledge_num_predict_applied)
extract_knowledge が num_predict=16384 を Ollama API に渡すこと。
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AttributeError: <module 'obsidian_etl.utils.knowledge_extractor' from '/data/projects/obsidian-importer/src/obsidian_etl/utils/knowledge_extractor.py'> does not have the attribute 'get_ollama_config'

======================================================================
ERROR: test_translate_summary_uses_config (tests.pipelines.transform.test_nodes.TestTranslateSummaryUsesOllamaConfig.test_translate_summary_uses_config)
translate_summary が get_ollama_config を使用してパラメーターを取得すること。
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AttributeError: <module 'obsidian_etl.utils.knowledge_extractor' from '/data/projects/obsidian-importer/src/obsidian_etl/utils/knowledge_extractor.py'> does not have the attribute 'get_ollama_config'

======================================================================
ERROR: test_translate_summary_num_predict_applied (tests.pipelines.transform.test_nodes.TestTranslateSummaryUsesOllamaConfig.test_translate_summary_num_predict_applied)
translate_summary が num_predict=1024 を Ollama API に渡すこと。
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AttributeError: <module 'obsidian_etl.utils.knowledge_extractor' from '/data/projects/obsidian-importer/src/obsidian_etl/utils/knowledge_extractor.py'> does not have the attribute 'get_ollama_config'

----------------------------------------------------------------------
Ran 341 tests in 6.764s

FAILED (errors=4)
```

## Test Details

### TestExtractKnowledgeUsesOllamaConfig

**test_extract_knowledge_uses_config**:
- Mocks `get_ollama_config` and `call_ollama`
- Calls `extract_knowledge` with params containing function-specific config
- Verifies `get_ollama_config(params, "extract_knowledge")` is called

**test_extract_knowledge_num_predict_applied**:
- Mocks `get_ollama_config` to return config with `num_predict=16384`
- Verifies `call_ollama` is called with `num_predict=16384` in kwargs

### TestTranslateSummaryUsesOllamaConfig

**test_translate_summary_uses_config**:
- Mocks `get_ollama_config` and `call_ollama`
- Calls `translate_summary` with params containing function-specific config
- Verifies `get_ollama_config(params, "translate_summary")` is called

**test_translate_summary_num_predict_applied**:
- Mocks `get_ollama_config` to return config with `num_predict=1024`
- Verifies `call_ollama` is called with `num_predict=1024` in kwargs

## Expected Values from contracts/parameters.yml

```yaml
ollama:
  functions:
    extract_knowledge:
      num_predict: 16384
      timeout: 300
    translate_summary:
      num_predict: 1024
```
