# Phase 2 RED Tests

## Summary

- Phase: Phase 2 - User Story 1 (まとめ品質の向上)
- FAIL tests: 10 (6 failures + 4 errors)
- Test files:
  - tests/pipelines/transform/test_nodes.py
  - tests/utils/test_compression_validator.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/pipelines/transform/test_nodes.py | test_prompt_includes_reason_instruction | Prompt contains "理由・背景" instruction for FR-001 |
| tests/pipelines/transform/test_nodes.py | test_prompt_includes_table_preservation | Prompt contains "表形式データの保持" instruction for FR-003 |
| tests/pipelines/transform/test_nodes.py | test_prompt_includes_code_preservation | Prompt contains explicit code block preservation instruction |
| tests/pipelines/transform/test_nodes.py | test_prompt_includes_analysis_structuring | Prompt contains "分析・考察の記述" instruction for FR-005 |
| tests/pipelines/transform/test_nodes.py | test_prompt_includes_specific_values_preservation | Prompt contains "数値・日付は省略せず" instruction for FR-004 |
| tests/utils/test_compression_validator.py | test_min_output_chars_small_conversation | min_output_chars(500) returns 300 |
| tests/utils/test_compression_validator.py | test_min_output_chars_large_conversation | min_output_chars(5000) returns 1000 |
| tests/utils/test_compression_validator.py | test_min_output_chars_boundary | min_output_chars(1500) returns 300 |
| tests/utils/test_compression_validator.py | test_min_output_chars_zero_original | min_output_chars(0) returns 0 |
| tests/utils/test_compression_validator.py | test_get_threshold_very_short_relaxed | get_threshold(999) returns 0.30 |

## Implementation Hints

### Prompt Changes (tests/pipelines/transform/test_nodes.py)

Add the following sections to `src/obsidian_etl/utils/prompts/knowledge_extraction.txt`:

```text
## 分析・考察の記述
- 理由・背景: 「なぜそうなるか」を必ず説明
- パターン・傾向: データから読み取れる傾向を明記
- 推奨・アドバイス: 結論だけでなく根拠も記述

## 表形式データの保持
- 必ず Markdown 表形式で保持
- 数値・日付は省略せず記載
- 表の前に簡潔な説明を追加

## コード主体の会話
- 重要なコードは省略せず完全に保持
- コードブロック保持を優先
```

### Compression Validator Changes (tests/utils/test_compression_validator.py)

1. Add `min_output_chars(original_size: int) -> int` function:
   ```python
   def min_output_chars(original_size: int) -> int:
       """Return minimum output character count.

       Returns max(original_size * 0.2, 300), or 0 if original is 0.
       """
       if original_size == 0:
           return 0
       return max(int(original_size * 0.2), 300)
   ```

2. Update `get_threshold()` for short conversations:
   ```python
   def get_threshold(original_size: int) -> float:
       if original_size >= 10000:
           return 0.10
       elif original_size >= 5000:
           return 0.15
       elif original_size >= 1000:
           return 0.20
       else:
           return 0.30  # Relaxed for very short conversations
   ```

## FAIL Output Sample

```
======================================================================
FAIL: test_prompt_includes_reason_instruction (tests.pipelines.transform.test_nodes.TestPromptQualityInstructions)
プロンプトに「理由・背景」の説明指示が含まれること。
----------------------------------------------------------------------
AssertionError: False is not true : Prompt should include reason/background instruction. Expected one of: ['理由・背景', '理由や背景', 'なぜそうなるか']. Prompt content length: 2181 chars

======================================================================
FAIL: test_prompt_includes_table_preservation (tests.pipelines.transform.test_nodes.TestPromptQualityInstructions)
プロンプトに表形式データの保持指示が含まれること。
----------------------------------------------------------------------
AssertionError: False is not true : Prompt should include table preservation instruction. Expected one of: ['表形式データの保持', '表形式を保持', 'Markdown 表形式で保持']. Prompt content length: 2181 chars

======================================================================
FAIL: test_prompt_includes_code_preservation (tests.pipelines.transform.test_nodes.TestPromptQualityInstructions)
プロンプトにコードブロック保持の強化指示が含まれること。
----------------------------------------------------------------------
AssertionError: False is not true : Prompt should include explicit code block preservation instruction. Expected one of: ['コードブロック保持', 'コードブロックを完全に保持', '重要なコードは省略せず', 'コード主体']. Prompt content length: 2181 chars

======================================================================
FAIL: test_prompt_includes_analysis_structuring (tests.pipelines.transform.test_nodes.TestPromptQualityInstructions)
プロンプトに分析・推奨の構造化指示が含まれること。
----------------------------------------------------------------------
AssertionError: False is not true : Prompt should include analysis/recommendation structuring instruction. Expected one of: ['分析・考察の記述', '分析・推奨', 'パターン・傾向', '推奨・アドバイス']. Prompt content length: 2181 chars

======================================================================
FAIL: test_prompt_includes_specific_values_preservation (tests.pipelines.transform.test_nodes.TestPromptQualityInstructions)
プロンプトに数値・日付・固有名詞の省略禁止指示が含まれること。
----------------------------------------------------------------------
AssertionError: False is not true : Prompt should include specific values preservation instruction. Expected one of: ['数値・日付は省略せず', '数値・日付・固有名詞', '具体的な数値']. Prompt content length: 2181 chars

======================================================================
ERROR: test_min_output_chars_small_conversation (tests.utils.test_compression_validator.TestMinCharactersValidation)
小さな会話では300文字が最低ライン。
----------------------------------------------------------------------
ImportError: cannot import name 'min_output_chars' from 'obsidian_etl.utils.compression_validator'

======================================================================
ERROR: test_min_output_chars_large_conversation (tests.utils.test_compression_validator.TestMinCharactersValidation)
大きな会話では20%が最低ライン。
----------------------------------------------------------------------
ImportError: cannot import name 'min_output_chars' from 'obsidian_etl.utils.compression_validator'

======================================================================
ERROR: test_min_output_chars_boundary (tests.utils.test_compression_validator.TestMinCharactersValidation)
境界値でのテスト。
----------------------------------------------------------------------
ImportError: cannot import name 'min_output_chars' from 'obsidian_etl.utils.compression_validator'

======================================================================
ERROR: test_min_output_chars_zero_original (tests.utils.test_compression_validator.TestMinCharactersValidation)
元の会話が空の場合、0を返す。
----------------------------------------------------------------------
ImportError: cannot import name 'min_output_chars' from 'obsidian_etl.utils.compression_validator'

======================================================================
FAIL: test_get_threshold_very_short_relaxed (tests.utils.test_compression_validator.TestShortConversationThreshold)
1,000文字未満の場合、しきい値が30% (0.30) に緩和されること。
----------------------------------------------------------------------
AssertionError: 0.2 != 0.3

----------------------------------------------------------------------
Ran 341 tests in 207.428s

FAILED (failures=6, errors=4)
```

## Test Class Locations

### TestPromptQualityInstructions

File: `/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py`
Lines: ~1707-1849

Tests:
- test_prompt_includes_reason_instruction (FR-001)
- test_prompt_includes_table_preservation (FR-003)
- test_prompt_includes_code_preservation (Edge Case)
- test_prompt_includes_analysis_structuring (FR-005)
- test_prompt_includes_specific_values_preservation (FR-004)

### TestMinCharactersValidation

File: `/data/projects/obsidian-importer/tests/utils/test_compression_validator.py`
Lines: ~240-307

Tests:
- test_min_output_chars_small_conversation
- test_min_output_chars_large_conversation
- test_min_output_chars_boundary
- test_min_output_chars_zero_original

### TestShortConversationThreshold

File: `/data/projects/obsidian-importer/tests/utils/test_compression_validator.py`
Lines: ~310-360

Tests:
- test_get_threshold_very_short_relaxed
- test_get_threshold_boundary_1000
- test_get_threshold_maintains_existing_behavior
