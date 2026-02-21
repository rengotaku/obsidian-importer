---
status: completed
created: 2026-02-22
branch: quick/002-028-llm-genre-classification
---

# 028: ジャンル分類をLLMベースに移行

## 概要

`classify_genre`（キーワードマッチング）と `extract_topic`（LLM）を `extract_topic_and_genre`（LLM 1回）に統合し、処理効率と分類精度を向上させる。

## ゴール

- [x] LLM 1回の呼び出しでトピックとジャンルを同時抽出
- [x] キーワードマッチング（`classify_genre`）を廃止
- [x] `genre_keywords` パラメータを削除
- [x] テスト通過・カバレッジ維持

## スコープ外

- organize パイプライン以外の変更
- ジャンル定義自体の変更（既存11カテゴリ維持）
- Vault出力ロジックの変更

## 前提条件

- 既存の `_extract_topic_via_llm` の呼び出しパターンを参考
- Ollama API の JSON モード使用
- フォールバック: JSON解析失敗時は `topic="", genre="other"`

---

## 実装タスク

### Phase 1: 新関数実装

- [x] T001 [src/obsidian_etl/pipelines/organize/nodes.py] `extract_topic_and_genre` 関数を実装
  - LLMプロンプトでトピック + ジャンルを JSON 形式で抽出
  - ジャンル定義をプロンプトに埋め込み
  - JSON解析 + エラーハンドリング

- [x] T002 [conf/base/parameters.yml] `ollama.functions.extract_topic_and_genre` 設定追加
  - num_predict: 128（JSON出力用に拡張）
  - timeout: 30

### Phase 2: パイプライン更新

- [x] T003 [src/obsidian_etl/pipelines/organize/pipeline.py] ノード定義を更新
  - `classify_genre` → `extract_topic_and_genre` に置換
  - `extract_topic` ノード削除（統合済み）

- [x] T004 [src/obsidian_etl/pipelines/organize/nodes.py] 旧関数を削除
  - `classify_genre` 関数削除
  - `extract_topic` 関数削除（`_extract_topic_via_llm` は残す）

### Phase 3: パラメータ整理

- [x] T005 [conf/base/parameters.yml] `genre_keywords` セクション削除
- [x] T006 [conf/base/parameters_organize.local.yml.example] `genre_keywords` 削除

### Phase 4: テスト

- [x] T007 [tests/pipelines/organize/test_nodes.py] テスト更新
  - `test_extract_topic_and_genre` 追加
  - 旧テスト削除 or 更新

- [x] T008 全テスト通過確認 (`make test`)

---

## リスク

| レベル | 内容 | 対策 |
|-------|------|------|
| MEDIUM | JSON解析エラー | try/except + フォールバック値 |
| MEDIUM | LLM出力の不安定性 | temperature=0.2、明確なプロンプト |
| LOW | 分類精度の変化 | ゴールデンファイルテストで検証 |

---

## 完了条件

- [x] 全タスク完了
- [x] `make test` 通過 (370 tests, 80% coverage)
- [x] `make lint` 通過
