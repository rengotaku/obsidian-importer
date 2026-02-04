# Quickstart: too_large 判定の LLM コンテキストベース化

## 概要

`too_large` 判定を `item.content`（生 JSON）から LLM に渡す実際のコンテキストサイズに変更する。

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/etl/stages/transform/knowledge_transformer.py` | `ExtractKnowledgeStep` に `_calculate_llm_context_size()` 追加、`process()` の判定ロジック修正 |
| `src/etl/tests/test_knowledge_transformer.py` | テストケース追加 |

## 実装手順

### Phase 1: Setup

1. ブランチ確認
   ```bash
   git checkout 038-too-large-llm-context
   ```

### Phase 2: 実装

1. `_calculate_llm_context_size()` メソッド追加
   ```python
   def _calculate_llm_context_size(self, data: dict) -> int:
       """LLM に渡す実際のコンテキストサイズを計算する。"""
       HEADER_SIZE = 200
       LABEL_OVERHEAD = 15
       messages = data.get("chat_messages", [])
       message_size = sum(len(msg.get("text", "")) for msg in messages)
       label_size = len(messages) * LABEL_OVERHEAD
       return HEADER_SIZE + message_size + label_size
   ```

2. `process()` の判定ロジック修正
   - JSON パースを先に実行
   - `_calculate_llm_context_size()` で判定
   - パース済みデータを後続処理で再利用

### Phase 3: テスト

1. ユニットテスト実行
   ```bash
   make test
   ```

2. 統合テスト（実データ）
   ```bash
   make import INPUT=... DEBUG=1
   ```

## 検証方法

1. 旧判定で too_large だったアイテムが処理されることを確認
2. 新判定で too_large のアイテムが正しくスキップされることを確認
3. 既存テストがすべてパスすることを確認

## ロールバック

`git revert` または `_calculate_llm_context_size()` を `len(item.content)` に戻す
