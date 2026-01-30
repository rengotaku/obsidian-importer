# Research: 柔軟な入出力比率対応フレームワーク

**Date**: 2026-01-20
**Feature**: 028-flexible-io-ratios

## Research Topics

### 1. 1:N 展開の実装アプローチ

**Decision**: Phase レベルでのチャンク分割（discover_items で展開）

**Rationale**:
- BaseStage の標準 `_process_item()` は 1 input → 1 output を前提としている
- 継承クラス（KnowledgeTransformer）が `run()` をオーバーライドしているのが現在の問題
- Phase の `discover_items` でチャンク分割を行えば、Extract/Transform/Load の全てが 1:1 処理のまま維持できる
- FR-006「継承クラスは run() をオーバーライドせずに実現」を満たす

**Alternatives considered**:

| Alternative | Rejected Because |
|-------------|------------------|
| BaseStage.run() で 1:N 対応 | run() の複雑化、既存 Stage への影響大 |
| Step が複数アイテムを返す | BaseStep インターフェース変更が必要、全 Step に影響 |
| Transform Stage でチャンクファイル書き出し | Stage 間の責務が曖昧になる |

### 2. チャンク分割の実行タイミング

**Decision**: Import Phase の `discover_items()` でチャンク分割を実行

**Rationale**:
- 既存の Chunker ユーティリティ（`src/etl/utils/chunker.py`）を活用
- Extract Stage の `input/` に既に分割されたファイルを配置
- Extract/Transform/Load は全て 1:1 処理として動作
- debug ログ出力は BaseStage の標準機能をそのまま使用可能

**Flow**:
```
conversations.json
    ↓ discover_items()
    ↓ Chunker.should_chunk() → True の場合
    ↓ Chunker.split()
    ↓
extract/input/
├── uuid_a.json (通常サイズ)
├── uuid_b_chunk_001.json (25000文字超)
├── uuid_b_chunk_002.json
└── uuid_c.json (通常サイズ)
```

### 3. debug ログ出力の統一

**Decision**: BaseStage._write_debug_step_output() を全 Stage で自動呼び出し

**Rationale**:
- FR-008「debug ログ出力は BaseStage.run() 内で自動実行」
- FR-009「継承クラスはログ出力をカスタマイズ不可」
- 現在の `_process_item()` 内で既に `_write_debug_step_output()` が呼ばれている
- KnowledgeTransformer の独自 `run()` を削除すれば、自動的にこの機能が使われる

**Current Implementation** (stage.py:358-367):
```python
# Write step-level debug output after successful step (DEBUG mode)
self._write_debug_step_output(
    ctx,
    current,
    step_index,
    step.name,
    timing_ms=timing_ms,
    before_chars=before_chars,
    after_chars=after_chars,
)
```

### 4. 親子関係のメタデータ記録

**Decision**: ProcessingItem.metadata に `parent_item_id` と `chunk_index` を追加

**Rationale**:
- FR-007「1:N 展開時、親子関係がメタデータに記録される」
- SC-005「任意の出力ファイルから元の入力ファイルを特定できる」
- discover_items でチャンク分割時に metadata を設定

**Schema**:
```python
# チャンク分割されたアイテムの metadata
{
    "is_chunked": True,
    "chunk_index": 0,  # 0-indexed
    "total_chunks": 3,
    "parent_item_id": "original_uuid",
    "chunk_filename": "original_uuid_001.json"
}

# 通常アイテムの metadata
{
    "is_chunked": False
}
```

### 5. KnowledgeTransformer のリファクタリング

**Decision**: 独自 `run()` を完全削除、チャンク展開ロジックを ExtractKnowledgeStep から削除

**Rationale**:
- 現在の KnowledgeTransformer.run() は 792 行あり、BaseStage.run() と重複したロジックが多い
- チャンク分割を Phase レベルに移動すれば、Transform Stage は 1:1 処理のみ
- ExtractKnowledgeStep の `process_with_expansion()` も不要になる

**Files to modify**:
1. `src/etl/stages/transform/knowledge_transformer.py` - run() 削除、Steps のみ定義
2. `src/etl/phases/import_phase.py` - discover_items にチャンク分割追加

### 6. 後方互換性の確保

**Decision**: 既存の metadata キーと JSONL スキーマを維持

**Rationale**:
- SC-006「既存テスト全パス」
- 新しい metadata キー（`is_chunked`, `chunk_index`, `parent_item_id`）は追加のみ
- 既存の `file_id`, `conversation_uuid` などは変更なし

## Summary

| Topic | Decision |
|-------|----------|
| 1:N 実装場所 | Phase.discover_items() |
| チャンク分割 | 既存 Chunker ユーティリティ使用 |
| debug ログ | BaseStage._write_debug_step_output() 自動呼び出し |
| 親子関係 | metadata に parent_item_id 追加 |
| KnowledgeTransformer | run() オーバーライド削除 |
| 後方互換性 | metadata キー追加のみ、既存キー維持 |
