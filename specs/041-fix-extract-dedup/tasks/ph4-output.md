# Phase 4 Output

## 作業概要
- User Story 2 - Claude Extractor テンプレート統一の実装完了
- FAIL テスト 9 件を PASS させた (test_extractor_template.py)
- ClaudeExtractor を BaseExtractor テンプレートメソッドパターンに統一

## 修正ファイル一覧
- `src/etl/stages/extract/claude_extractor.py` - テンプレート統一実装

### 詳細変更内容

#### 1. `_build_chunk_messages()` hook 実装 (T041)
```python
def _build_chunk_messages(self, chunk, conversation_dict: dict) -> list[dict]:
    """Build chat_messages for chunked conversation (Claude format).

    Implements BaseExtractor hook method.
    Claude conversations use simple {text, sender} format only.
    """
    return [{"text": msg.content, "sender": msg.role} for msg in chunk.messages]
```

**実装内容**:
- Claude 形式の chat_messages を構築する hook メソッドを実装
- `{text, sender}` のみのシンプルな形式（ChatGPT の `uuid`/`created_at` は不要）
- BaseExtractor の `_chunk_if_needed()` から呼び出される

#### 2. `_chunk_if_needed()` override 削除 (T042)
- **削除箇所**: lines 364-428 (65行削除)
- **効果**: BaseExtractor の `_chunk_if_needed()` テンプレートメソッドを使用
- **理由**: チャンクロジックは BaseExtractor で統一、Claude 固有の処理は `_build_chunk_messages()` hook に集約

**削除前** (冗長なコード):
```python
def _chunk_if_needed(self, item: ProcessingItem) -> list[ProcessingItem]:
    # Build conversation for chunking
    conversation = self._build_conversation_for_chunking(item)
    # ... 65 lines of redundant code ...
    chunk_conv["chat_messages"] = [
        {"text": msg.content, "sender": msg.role} for msg in chunk.messages
    ]
```

**削除後** (BaseExtractor テンプレート + hook):
- BaseExtractor が `_chunk_if_needed()` を提供
- ClaudeExtractor は `_build_chunk_messages()` hook のみ実装

#### 3. `stage_type` override 削除 (T043)
- **削除箇所**: lines 184-186 (3行削除)
- **効果**: BaseExtractor の `stage_type` プロパティを継承
- **理由**: 値が `StageType.EXTRACT` で BaseExtractor と同一のため冗長

**削除前**:
```python
@property
def stage_type(self) -> StageType:
    return StageType.EXTRACT  # ← BaseExtractor と同値
```

**削除後**:
- BaseExtractor の実装を継承（同じ値を返す）
- 未使用の `StageType` import も削除

## テスト結果

### Phase 4 テスト (test_extractor_template.py)

**TestClaudeBuildChunkMessages (6 tests)**: ✅ ALL PASS
- `test_build_chunk_messages_returns_list_of_dicts` - list 返却確認
- `test_build_chunk_messages_has_text_field` - `text` フィールド確認
- `test_build_chunk_messages_has_sender_field` - `sender` フィールド確認
- `test_build_chunk_messages_no_uuid_field` - `uuid` がないこと確認
- `test_build_chunk_messages_no_created_at_field` - `created_at` がないこと確認
- `test_build_chunk_messages_only_text_and_sender_keys` - キーが `{text, sender}` のみ

**TestClaudeNoChunkIfNeededOverride (2 tests)**: ✅ ALL PASS
- `test_chunk_if_needed_not_defined_on_claude_extractor` - override がないこと確認
- `test_chunk_if_needed_is_inherited_from_base` - BaseExtractor から継承確認

**TestClaudeNoStageTypeOverride (2 tests)**: ✅ ALL PASS
- `test_stage_type_not_defined_on_claude_extractor` - override がないこと確認
- `test_stage_type_returns_extract_via_inheritance` - 継承で EXTRACT を返すこと確認

**合計**: 10 tests PASS (9 FAIL → PASS + 1 既存 PASS)

### 回帰テスト (T045, T046)

**test_claude_extractor_refactoring.py (20 tests)**: ✅ ALL PASS
- 抽象メソッド実装テスト (4 tests)
- 動作維持確認テスト (3 tests)
- チャンク処理テスト (4 tests)
- エッジケーステスト (4 tests)
- ZIP サポートテスト (5 tests)

**test_chunking_integration.py (18 tests)**: ✅ ALL PASS
- 抽象メソッド実装確認 (4 tests)
- ChatGPT チャンク処理 (6 tests)
- チャンクメタデータフロー (4 tests)
- エッジケース処理 (4 tests)

**総計**: 48 tests PASS (Phase 4 + 回帰テスト)

### 実装前後の比較

| メトリクス | 実装前 | 実装後 | 変化 |
|---------|-------|-------|------|
| ClaudeExtractor LOC | 429 | 376 | -53 (-12.4%) |
| `_chunk_if_needed()` 実装 | 冗長 override (65行) | BaseExtractor 継承 | 削除 |
| `stage_type` 実装 | 冗長 override (3行) | BaseExtractor 継承 | 削除 |
| `_build_chunk_messages()` | なし | hook 実装 (15行) | 追加 |
| テンプレートパターン準拠 | 部分的 | 完全準拠 | 改善 |

## 注意点

### 次 Phase で必要な情報
- ClaudeExtractor は BaseExtractor テンプレートパターンに完全準拠
- ChatGPTExtractor も同様にテンプレート統一済み (Phase 3)
- GitHubExtractor も同じパターンを適用する必要がある (Phase 5)

### テンプレートメソッドパターンの責務分離

**BaseExtractor (テンプレート)**:
- `discover_items()` - 全体フロー制御
- `_chunk_if_needed()` - チャンク判定・分割ロジック
- `stage_type` - ステージ種別 (EXTRACT)

**ClaudeExtractor (子クラス)**:
- `_discover_raw_items()` - Claude JSON/ZIP からアイテム発見
- `_build_conversation_for_chunking()` - SimpleConversation 構築
- `_build_chunk_messages()` - **新規 hook**: Claude 形式 chat_messages 構築

### 実装のミス・課題
なし。テンプレートメソッドパターンが期待通りに動作している。

## 構造的重複防止の達成状況

### Phase 2-4 完了時点での状況

| Extractor | `_discover_raw_items()` | `_build_conversation_for_chunking()` | `_build_chunk_messages()` | `_chunk_if_needed()` override | `stage_type` override | Status |
|-----------|------------------------|-------------------------------------|---------------------------|------------------------------|----------------------|--------|
| BaseExtractor | abstract | abstract | hook (default: None) | ✅ 実装 | ✅ 実装 (EXTRACT) | - |
| ClaudeExtractor | ✅ 実装 | ✅ 実装 | ✅ 実装 | ❌ 削除 | ❌ 削除 | ✅ 統一 |
| ChatGPTExtractor | ✅ 実装 | ✅ 実装 | ✅ 実装 | ❌ 削除 | ❌ 削除 | ✅ 統一 |
| GitHubExtractor | ✅ 実装 | ✅ 実装 | ❌ 未実装 | ❌ なし | ✅ override あり | ⚠️ 要対応 |

**Phase 5 で対応すべきこと**:
- GitHubExtractor の `stage_type` override 削除
- GitHubExtractor の `discover_items()` override 削除（if any）
- 全 Extractor が統一テンプレートに従う状態

## 次 Phase への引き継ぎ

### Phase 5 (User Story 3 - GitHub Extractor テンプレート統一) への入力
- ClaudeExtractor と ChatGPTExtractor がテンプレートパターンに準拠
- GitHubExtractor も同じパターンを適用すれば、全 4 Extractor が統一設計に
- `_build_chunk_messages()` hook は GitHub では不要（チャンク処理しないため）
- `stage_type` override の削除が主な作業
