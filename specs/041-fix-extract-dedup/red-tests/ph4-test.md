# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - User Story 2 - Claude Extractor テンプレート統一
- FAIL テスト数: 9
- テストファイル: src/etl/tests/test_extractor_template.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_extractor_template.py | test_build_chunk_messages_returns_list_of_dicts | `_build_chunk_messages()` が None でなく list を返す |
| test_extractor_template.py | test_build_chunk_messages_has_text_field | 各 dict に `text` フィールドがある |
| test_extractor_template.py | test_build_chunk_messages_has_sender_field | 各 dict に `sender` フィールドがある |
| test_extractor_template.py | test_build_chunk_messages_no_uuid_field | `uuid` フィールドがない (ChatGPT-specific) |
| test_extractor_template.py | test_build_chunk_messages_no_created_at_field | `created_at` フィールドがない (ChatGPT-specific) |
| test_extractor_template.py | test_build_chunk_messages_only_text_and_sender_keys | キーが `{text, sender}` のみ |
| test_extractor_template.py | test_chunk_if_needed_not_defined_on_claude_extractor | `_chunk_if_needed` が ClaudeExtractor に定義されていない |
| test_extractor_template.py | test_chunk_if_needed_is_inherited_from_base | `_chunk_if_needed` が BaseExtractor から継承されている |
| test_extractor_template.py | test_stage_type_not_defined_on_claude_extractor | `stage_type` が ClaudeExtractor に定義されていない |

## PASS テスト (既存 + 継承確認)

| テストファイル | テストメソッド | 理由 |
|---------------|---------------|------|
| test_extractor_template.py | test_stage_type_returns_extract_via_inheritance | ClaudeExtractor は EXTRACT を返す（冗長 override だが値は同じ） |

## 実装ヒント

### T035: `_build_chunk_messages()` 実装
- `src/etl/stages/extract/claude_extractor.py` に `_build_chunk_messages(self, chunk, conversation_dict: dict) -> list[dict]` を追加
- Claude format: `{"text": msg.content, "sender": msg.role}` のみ (uuid, created_at は不要)
- BaseExtractor の hook をオーバーライドする

### T036: `_chunk_if_needed()` override 削除
- `src/etl/stages/extract/claude_extractor.py` の `_chunk_if_needed()` メソッド (lines 364-428) を削除
- BaseExtractor の `_chunk_if_needed()` テンプレートメソッドが自動的に使われる
- `_build_chunk_messages()` hook が chunk content を構築する

### T037: `stage_type` override 削除
- `src/etl/stages/extract/claude_extractor.py` の `stage_type` プロパティ (lines 184-186) を削除
- BaseExtractor の `stage_type` が `StageType.EXTRACT` を返す

## FAIL 出力例

```
FAIL: test_build_chunk_messages_returns_list_of_dicts (src.etl.tests.test_extractor_template.TestClaudeBuildChunkMessages)
AssertionError: unexpectedly None : _build_chunk_messages() should not return None

FAIL: test_chunk_if_needed_not_defined_on_claude_extractor (src.etl.tests.test_extractor_template.TestClaudeNoChunkIfNeededOverride)
AssertionError: '_chunk_if_needed' unexpectedly found in mappingproxy({...})

FAIL: test_stage_type_not_defined_on_claude_extractor (src.etl.tests.test_extractor_template.TestClaudeNoStageTypeOverride)
AssertionError: 'stage_type' unexpectedly found in mappingproxy({...})
```

## FAIL の根本原因

| テストグループ | FAIL 原因 |
|---------------|----------|
| TestClaudeBuildChunkMessages (6 tests) | ClaudeExtractor に `_build_chunk_messages()` が未実装。BaseExtractor のデフォルト実装が None を返す |
| TestClaudeNoChunkIfNeededOverride (2 tests) | ClaudeExtractor が `_chunk_if_needed()` を override している (lines 364-428) |
| TestClaudeNoStageTypeOverride (1 test) | ClaudeExtractor が `stage_type` を override している (lines 184-186) |
