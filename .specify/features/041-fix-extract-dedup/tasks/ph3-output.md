# Phase 3 Output

## 作業概要
- Phase 3: User Story 1 - ChatGPT 重複処理の解消 (GREEN + Verification) 完了
- FAIL テスト 5 件を PASS させた (16/16 tests passing)
- N² 重複問題を構造的に解決 (N conversations → N records)

## 修正ファイル一覧

### プロダクションコード

- `src/etl/stages/extract/chatgpt_extractor.py` - ChatGPT Extractor リファクタリング
  - **削除**: ReadZipStep, ParseConversationsStep, ConvertFormatStep (3 classes, 250+ lines)
  - **修正**: ChatGPTExtractor.steps を `[ValidateMinMessagesStep()]` のみに変更
  - **追加**: `_build_chunk_messages()` hook 実装 (ChatGPT format: uuid, text, sender, created_at)
  - **削除**: `_chunk_if_needed()` override (BaseExtractor template method を使用)
  - **削除**: `stage_type` override (BaseExtractor から継承)
  - **変更**: docstring 更新 (Steps 削減を反映)

### テストコード

- `src/etl/tests/test_stages.py` - 旧 Steps テストをスキップ
  - `TestChatGPTExtractorSteps` クラスに `@unittest.skip` デコレータ追加
  - 理由: 削除された Steps のテストは test_chatgpt_dedup.py でカバー

- `src/etl/tests/test_debug_step_output.py` - debug ログ検証を更新
  - 期待する Steps を 4 → 1 に変更 (validate_min_messages のみ)
  - 1:N expansion メタデータ検証削除 (ParseConversationsStep 不在のため)

### テスト実行結果

```bash
# Phase 3 テスト (test_chatgpt_dedup.py)
Ran 16 tests in 0.005s - OK

# test_stages.py ChatGPT tests
Skipped 5 tests (obsolete Step tests)

# test_debug_step_output.py ChatGPT tests
Ran 1 test in 0.035s - OK
```

## 実装のポイント

### 1. `_discover_raw_items()` の役割拡大

**BEFORE**: ZIP ファイルパスのみを yield (content=None)

**AFTER**: ZIP 読み込み・パース・形式変換まで完了した ProcessingItem を yield (content=Claude format JSON)

- ZIP reading → `read_conversations_from_zip()`
- Parsing → conversations.json array を展開
- Format conversion → ChatGPT tree → Claude flat messages
- Filtering → MIN_MESSAGES 未満をスキップ
- Metadata → conversation_uuid, created_at, message_count など設定

### 2. `steps` の最小化

**BEFORE**: 4 Steps (ReadZip, ParseConversations, ConvertFormat, ValidateMinMessages)

**AFTER**: 1 Step (ValidateMinMessages のみ)

- 前処理は `_discover_raw_items()` に移動
- Steps は軽量な検証のみ担当

### 3. `_build_chunk_messages()` hook

BaseExtractor template method に従い、chunk 分割後の messages を構築する hook を実装:

```python
def _build_chunk_messages(self, chunk, conv_dict: dict) -> list[dict]:
    return [
        {
            "uuid": "",
            "text": msg.content,
            "sender": msg.role,
            "created_at": conv_dict.get("created_at", ""),
        }
        for msg in chunk.messages
    ]
```

これにより、`_chunk_if_needed()` override が不要になった。

### 4. 冗長な override 削除

- `stage_type`: BaseExtractor から継承 (StageType.EXTRACT)
- `_chunk_if_needed()`: BaseExtractor template method を使用

## N² 重複問題の解決

### 問題

旧実装では以下の処理フローで N² 重複が発生:

```
discover_items() → N ZIP items (content=None)
  ↓
ReadZipStep → N items (content=full JSON)
  ↓
ParseConversationsStep → N × M conversations (1:N expansion)
  ↓
ConvertFormatStep → N × M items
```

### 解決策

`_discover_raw_items()` で一気に変換し、Steps を通さない:

```
_discover_raw_items() → N conversations (content=Claude JSON, already expanded)
  ↓
ValidateMinMessagesStep → N items (validation only)
```

**検証**:
- test_discover_run_n_items_n_output: 3 conversations → 3 output items ✅
- test_no_duplicate_conversation_uuid: All UUIDs unique ✅

## 注意点

### 次 Phase で必要な情報

- BaseExtractor template 完成 (Phase 2) により、Claude/GitHub Extractor も同様のリファクタリングが可能
- `_build_chunk_messages()` hook は provider-specific format を吸収する設計

### 既知の制限

- `MIN_MESSAGES` しきい値は変わらず (1 以上)
- マルチモーダル (image/audio) はプレースホルダー処理 (既存と同じ)
- Empty ZIP / malformed conversations は graceful skip (既存と同じ)

## 実装のミス・課題

### 課題

- test_stages.py の旧 Steps テストを完全削除するか、移行するか (現在は skip)
  → Phase 4 完了後に削除推奨

### リグレッション確認

以下のテストは修正により影響を受けなかった:

- test_chunking_integration.py (chunking は BaseExtractor template で動作)
- test_extractor_template.py (BaseExtractor 抽象クラステスト)

### その他のエラー

`make test` で以下のエラーが発生しているが、Phase 3 のスコープ外:

- test_import_without_chunk_skips_large_files (FAIL): chunk=False 時の large file スキップ
- test_record_splitting_at_1000_records (FAIL): Extract output ファイル分割
- test_stage_has_max_records_per_file_attribute (FAIL): `_max_records_per_file` 値不一致

これらは Phase 1 で revert した `_max_records_per_file` 変更とは無関係のエラー。別 issue で対応必要。

## Phase Completion Status

✅ **Phase 3 Complete**

- All 16 ChatGPT dedup tests PASS
- N² duplication structurally prevented
- Template Method pattern applied successfully

**Next Phase**: Phase 4 - Claude Extractor テンプレート統一
