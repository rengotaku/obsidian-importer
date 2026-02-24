---
status: complete
created: 2026-02-24
completed: 2026-02-24
branch: quick/005-issue-ollama-default-model
issue: "#38"
---

# refactor: Ollama モデルのデフォルト値を統一

## 概要

ハードコードされた Ollama モデルのデフォルト値 (`gemma3:12b`) を削除し、設定必須化する。実際の本番環境では `gpt-oss:20b` が使用されており、コード内のデフォルト値は混乱を招くデッドコードになっている。

## ゴール

- [x] コード内の `gemma3:12b` デフォルト値を削除
- [x] `parameters.yml` での model 設定を必須化
- [x] テストでは明示的にモデル名を指定

## スコープ外

- ドキュメント（specs/）内の `gemma3:12b` 参照更新（歴史的資料として残す）
- RAG モジュール（`src/rag/`）の変更（別のコンテキストで使用）

## 前提条件

- 本番環境は `conf/base/parameters.yml` で `gpt-oss:20b` を設定済み
- テストでは `gemma3:12b` を明示的に指定する（モック使用のため実際のモデルは不要）

---

## 実装タスク

### Phase 1: コア実装

- [x] T001 [src/obsidian_etl/utils/ollama_config.py] OllamaConfig.model のデフォルト値を削除
- [x] T002 [src/obsidian_etl/utils/ollama_config.py] HARDCODED_DEFAULTS から "model" を削除
- [x] T003 [src/obsidian_etl/utils/ollama.py] call_ollama() の model 引数からデフォルト値を削除

### Phase 2: テスト更新

- [x] T004 [tests/utils/test_ollama_config.py] テストで model を明示的に指定
- [x] T005 [tests/utils/test_ollama_warmup.py] テストで model を明示的に指定（既に対応済み）
- [x] T006 [tests/pipelines/transform/test_nodes.py] テストで model を明示的に指定
- [x] T007 [tests/pipelines/organize/test_nodes.py] テストで model を明示的に指定（既に対応済み）
- [x] T008 [tests/test_integration.py] テストで model を明示的に指定

### Phase 3: 検証

- [x] T009 全テスト通過確認（make test）
- [x] T010 lint チェック通過確認（make lint）

---

## リスク

| レベル | 内容 |
|-------|------|
| HIGH | テスト修正箇所が多い（50+箇所）。慎重に一括置換を行う |
| MEDIUM | 設定なしでの実行がエラーになる。ドキュメントで明記が必要 |
| LOW | docstring 内のサンプルコードも更新が必要 |

---

## 完了条件

- [x] 全タスク完了
- [x] テスト通過（make test）
- [x] lint 通過（make lint）
