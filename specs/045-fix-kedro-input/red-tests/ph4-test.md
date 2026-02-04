# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - dispatch 型パイプライン + 統合テスト (US1)
- FAIL テスト数: 10
- PASS テスト数 (新規): 3 (OpenAI 統合テスト -- 既存実装で動作)
- テストファイル: tests/test_pipeline_registry.py, tests/test_integration.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/test_pipeline_registry.py | TestDispatchPipeline.test_default_is_import_claude_when_provider_claude | provider=claude で __default__ が import_claude と同じノード群 |
| tests/test_pipeline_registry.py | TestDispatchPipeline.test_default_is_import_openai_when_provider_openai | provider=openai で __default__ が import_openai と同じノード群 |
| tests/test_pipeline_registry.py | TestDispatchPipeline.test_default_is_import_github_when_provider_github | provider=github で __default__ が import_github と同じノード群 |
| tests/test_pipeline_registry.py | TestDispatchPipeline.test_default_contains_parse_claude_zip_when_provider_claude | provider=claude で __default__ に parse_claude_zip ノード |
| tests/test_pipeline_registry.py | TestDispatchPipeline.test_default_contains_parse_chatgpt_zip_when_provider_openai | provider=openai で __default__ に parse_chatgpt_zip ノード |
| tests/test_pipeline_registry.py | TestDispatchPipeline.test_default_contains_clone_github_repo_when_provider_github | provider=github で __default__ に clone_github_repo ノード |
| tests/test_pipeline_registry.py | TestDispatchPipeline.test_individual_pipeline_names_still_work | dispatch 後も個別パイプライン名でアクセス可能 |
| tests/test_pipeline_registry.py | TestDispatchError.test_invalid_provider_raises_value_error | 無効 provider で ValueError + provider 名がメッセージに含まれる |
| tests/test_pipeline_registry.py | TestDispatchError.test_invalid_provider_error_message_lists_valid_providers | エラーメッセージに有効 provider 一覧が含まれる |
| tests/test_pipeline_registry.py | TestDispatchError.test_empty_provider_raises_value_error | 空文字列 provider で ValueError |

## PASS テスト一覧 (新規)

| テストファイル | テストメソッド | 備考 |
|---------------|---------------|------|
| tests/test_integration.py | TestE2EOpenAIImport.test_e2e_openai_import_produces_organized_items | OpenAI パイプラインは既に動作する |
| tests/test_integration.py | TestE2EOpenAIImport.test_e2e_openai_import_all_conversations_processed | 2会話 -> 2 organized_items |
| tests/test_integration.py | TestE2EOpenAIImport.test_e2e_openai_parsed_items_have_openai_provider | source_provider == "openai" |

## 実装ヒント

- `src/obsidian_etl/pipeline_registry.py` に OmegaConf を import し、`conf/base/parameters.yml` を読み込む
- `register_pipelines()` 内で `import.provider` を取得し、対応するパイプラインを `__default__` に設定
- 有効な provider は `{"claude", "openai", "github"}`
- 無効な provider の場合、`ValueError` を raise し、エラーメッセージに無効な provider 名と有効な provider 一覧を含める
- 個別パイプライン名 (`import_claude`, `import_openai`, `import_github`) は引き続き返す
- テストでは `obsidian_etl.pipeline_registry.OmegaConf.load` をモックする設計

実装パターン例:
```python
from omegaconf import OmegaConf
from pathlib import Path

VALID_PROVIDERS = {"claude", "openai", "github"}

def register_pipelines() -> dict[str, Pipeline]:
    # Read provider from parameters.yml
    params_path = Path(__file__).parent.parent.parent / "conf" / "base" / "parameters.yml"
    config = OmegaConf.load(params_path)
    provider = config["import"]["provider"]

    if provider not in VALID_PROVIDERS:
        raise ValueError(
            f"Invalid provider '{provider}'. "
            f"Valid providers: {sorted(VALID_PROVIDERS)}"
        )

    # Build pipelines...
    pipelines = {
        "import_claude": ...,
        "import_openai": ...,
        "import_github": ...,
    }
    pipelines["__default__"] = pipelines[f"import_{provider}"]
    return pipelines
```

## FAIL 出力例
```
ERROR: test_default_is_import_claude_when_provider_claude (tests.test_pipeline_registry.TestDispatchPipeline)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/test_pipeline_registry.py", line 135, in test_default_is_import_claude_when_provider_claude
    with self._mock_omegaconf_load("claude"):
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/mock.py", line 1481, in __enter__
    self.target = self.getter()
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/pkgutil.py", line 528, in resolve_name
    result = getattr(result, p)
AttributeError: module 'obsidian_etl.pipeline_registry' has no attribute 'OmegaConf'

ERROR: test_invalid_provider_raises_value_error (tests.test_pipeline_registry.TestDispatchError)
----------------------------------------------------------------------
AttributeError: module 'obsidian_etl.pipeline_registry' has no attribute 'OmegaConf'
```

## テスト数サマリー
- 全テスト数: 292 (279 baseline + 13 new)
- 新規 FAIL/ERROR: 10 (dispatch テスト)
- 新規 PASS: 3 (OpenAI 統合テスト)
- 既存テスト: 全て影響なし (既存 8 tests in TestPipelineRegistry: PASS)
- 既知 RAG failures: 3 failures + 22 errors (baseline と同じ)
