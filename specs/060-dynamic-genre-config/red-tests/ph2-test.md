# Phase 2 RED Tests

## Summary
- Phase: Phase 2 - User Story 1+2 (ジャンル定義の動的設定)
- FAIL test count: 14
- Test file: `tests/pipelines/organize/test_nodes.py`
- Test class: `TestDynamicGenreConfig`

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|------------|-------------------|
| test_nodes.py | test_build_genre_prompt_contains_all_genres | _build_genre_prompt が全ジャンルをプロンプト文字列に含める |
| test_nodes.py | test_build_genre_prompt_contains_descriptions | _build_genre_prompt が各ジャンルの description を含める |
| test_nodes.py | test_build_genre_prompt_format | '- key: description' 形式で出力する |
| test_nodes.py | test_build_genre_prompt_empty_definitions | 空の genre_definitions で空文字列を返す |
| test_nodes.py | test_parse_genre_config_returns_tuple | (genre_definitions, valid_genres) のタプルを返す |
| test_nodes.py | test_parse_genre_config_extracts_descriptions | description を正しく抽出する |
| test_nodes.py | test_parse_genre_config_missing_description_uses_genre_name | description なしの場合ジャンル名を使用 |
| test_nodes.py | test_parse_genre_config_valid_genres_set | valid_genres を set として返す |
| test_nodes.py | test_valid_genres_includes_custom_genre | カスタムジャンルが valid_genres に含まれる |
| test_nodes.py | test_valid_genres_always_includes_other | other が常に valid_genres に含まれる |
| test_nodes.py | test_valid_genres_matches_config_keys | valid_genres が設定キーと一致する (ハードコード値は含まない) |
| test_nodes.py | test_genre_fallback_with_custom_config | カスタム設定で不正ジャンルが other にフォールバック |
| test_nodes.py | test_genre_fallback_valid_genre_not_changed | 有効なジャンルはそのまま保持 |
| test_nodes.py | test_genre_fallback_integration_with_extract | extract_topic_and_genre が設定ベースでフォールバック |

## Implementation Hints

### New Functions to Implement

1. `_parse_genre_config(genre_vault_mapping: dict) -> tuple[dict, set]`
   - Input: genre_vault_mapping (new format with vault + description)
   - Output: (genre_definitions: dict[str, str], valid_genres: set[str])
   - genre_definitions maps genre_key -> description
   - If description is missing, use genre_key as description
   - valid_genres always includes "other"

2. `_build_genre_prompt(genre_definitions: dict) -> str`
   - Input: genre_definitions dict (key -> description)
   - Output: Formatted string for LLM prompt
   - Format: `- key: description` per line
   - Empty dict returns empty string

3. Update `_extract_topic_and_genre_via_llm()`:
   - Call `_parse_genre_config()` to get genre_definitions and valid_genres
   - Call `_build_genre_prompt()` to generate prompt section
   - Replace hardcoded genre list in system_prompt
   - Replace hardcoded valid_genres set

### Files to Modify
- `src/obsidian_etl/pipelines/organize/nodes.py`

## FAIL Output Example

```
FAIL: test_build_genre_prompt_contains_all_genres (tests.pipelines.organize.test_nodes.TestDynamicGenreConfig.test_build_genre_prompt_contains_all_genres)
_build_genre_prompt が全ジャンルをプロンプト文字列に含めること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/pipelines/organize/test_nodes.py", line 1135, in setUp
    self.fail("_parse_genre_config is not yet implemented (RED)")
AssertionError: _parse_genre_config is not yet implemented (RED)
```

## Existing Tests Status

- All 370 existing tests: PASS
- 14 new tests: FAIL (RED)
- Total: 384 tests, 14 failures
