---
status: completed
created: 2026-03-07
branch: quick/009-058-lint-ruff-format
---

# 009-058-lint-ruff-format

## 概要

lint.yml に ruff format チェックを追加し、Makefile に format-check / format ターゲットを追加する。既存コードのフォーマット修正も含む（20ファイル）。

## ゴール

- [x] `make format-check` でフォーマットチェックが通る
- [x] lint.yml で ruff format が CI 実行される
- [x] `make test` が引き続き通る

## スコープ外

- mypy の導入（Issue #59）
- テストワークフロー追加（Issue #57）

## 前提条件

- ruff は既に pyproject.toml に設定済み
- Makefile に ruff / pylint ターゲットが存在
- 20ファイルにフォーマット差分あり

---

## 実装タスク

### Phase 1: Makefile 更新

- [x] T001 [Makefile] `format-check` ターゲット追加（ruff format --check src/ tests/）
- [x] T002 [Makefile] `format` ターゲット追加（ruff format src/ tests/）

### Phase 2: 既存コードのフォーマット

- [x] T003 `make format` で20ファイルをフォーマット
- [x] T004 `make test` でフォーマット後もテストが通ることを確認

### Phase 3: CI 更新

- [x] T005 [.github/workflows/lint.yml] ruff format チェックステップを追加

---

## リスク

| レベル | 内容 |
|-------|------|
| LOW | ruff format はコードの意味を変えない（空白・改行のみ） |
| LOW | テスト結果に影響なし |

---

## 完了条件

- [x] 全タスク完了（5タスク）
- [x] `make format-check` が通る
- [x] `make test` が通る
- [x] lint.yml に ruff format ステップが追加されている
