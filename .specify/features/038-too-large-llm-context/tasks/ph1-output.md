# Phase 1 Output

## 作業概要

Phase 1 (Setup) では、ブランチ確認と既存コードの理解を行いました。

## 実施内容

### T001: ブランチ確認
- 現在のブランチが `038-too-large-llm-context` であることを確認
- 一部の feature-037 関連の WIP 変更があったため、それらを一時保存してリバート
- クリーンなベースラインを確立

### T002-T004: 既存コード理解

#### `knowledge_transformer.py` の現状判定ロジック (L193-203)

```python
if not chunk_enabled and not is_chunked and item.content:
    content_size = len(item.content)  # ← 生 JSON 全体
    if content_size > self._chunk_size:  # 25000 chars
        # Skip LLM processing, mark as too_large
        item.status = ItemStatus.SKIPPED
        item.metadata["skipped_reason"] = "too_large"
        item.metadata["too_large"] = True
        ...
        return item
```

**問題点**:
- `item.content` は生 JSON 全体（約 2.4 倍過大評価）
- 実際の LLM コンテキストはメッセージ `text` のみ

#### `knowledge_extractor.py` の `_build_user_message()` 構造 (L470-511)

LLM に渡す実際のコンテキスト構成:

```
ヘッダー (~200 chars):
- ファイル名
- プロバイダー
- 会話サマリー
- メッセージ数
- 会話作成日

メッセージ本文:
- 各メッセージ: [User]/[Assistant] (~15 chars) + msg.content
```

**計算式**:
```python
LLM_context_size = 200 (ヘッダー) + Σ(msg.text) + 15 * msg_count
```

### T005: テスト実行

- `knowledge_transformer` 関連のユニットテストは全 30 件パス（7 件スキップ）
- 一部の GitHub extractor と CLI 関連テストに既存の失敗あり（feature 038 とは無関係）

## 修正ファイル一覧

- `specs/038-too-large-llm-context/tasks.md` - Phase 1 タスク完了マーク
- `specs/038-too-large-llm-context/tasks/ph1-output.md` - This file

## 注意点

### 実装方針（research.md より）

1. **JSON パースタイミング**: 判定前に JSON をパースし、`chat_messages` から `text` を抽出して計算
2. **パース結果の再利用**: too_large でスキップしない場合、パース済みデータを後続処理で再利用
3. **計算関数**: `_calculate_llm_context_size(data: dict) -> int` を `ExtractKnowledgeStep` に追加

### 修正箇所

`knowledge_transformer.py` の `ExtractKnowledgeStep.process()` メソッド:
- L193-203: 判定ロジック変更
- JSON パースを L214 より前に移動
- 新規メソッド `_calculate_llm_context_size()` 追加

### テスト戦略

1. **ユニットテスト**: `test_too_large_context.py` 新規作成
   - `_calculate_llm_context_size()` 単体テスト
   - エッジケース（空メッセージ、null text）
2. **統合テスト**: 新旧判定結果の比較

## 次 Phase への引き継ぎ

Phase 2 (TDD) では:
1. テスト実装 (RED): `test_too_large_context.py` 作成
2. 実装 (GREEN): `_calculate_llm_context_size()` 追加 + 判定ロジック変更
3. 既存テスト互換性維持
