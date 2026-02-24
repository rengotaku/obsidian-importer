---
status: complete
created: 2026-02-24
branch: quick/004-issue-ollama
issue: 33
---

# Issue#33 Ollama ウォームアップ処理の統一

## 概要

`call_ollama` 関数内で初回呼び出し時に自動ウォームアップを実行し、各モジュールでの個別対応を不要にする。

## ゴール

- [x] `utils/ollama.py` の `call_ollama` に自動ウォームアップを実装
- [ ] `organize/nodes.py` の `_warmup_model` 関数を削除（次フェーズで対応）
- [x] 全 LLM 呼び出しで一貫したウォームアップ動作を実現

## スコープ外

- LLM 呼び出しのリトライロジック（別 Issue で対応）
- Ollama 接続エラー時の詳細なエラーハンドリング

## 前提条件

- 既存の `call_ollama` API は変更しない（引数・戻り値）
- モジュールレベルの `set` でウォーム済みモデルを追跡

---

## 実装タスク

### Phase 1: 実装

- [x] T001 [src/obsidian_etl/utils/ollama.py] `_warmed_models: set[str]` 追加、`call_ollama` 内で初回ウォームアップ
- [x] T002 [src/obsidian_etl/utils/ollama.py] `_do_warmup(model, base_url)` ヘルパー関数追加

### Phase 2: テスト

- [x] T003 [tests/] ウォームアップ機能のユニットテスト追加（モック使用）

### Phase 3: 確認

- [x] T004 `make lint` で lint エラーがないことを確認
- [x] T005 `make test` でテスト通過を確認

---

## リスク

| レベル | 内容 |
|-------|------|
| LOW | モジュールグローバル変数によるテスト間の状態共有（テスト時にリセットが必要な場合あり） |

---

## 完了条件

- [x] 全タスク完了
- [x] `make lint` 通過
- [x] `make test` 通過
