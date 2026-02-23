---
status: completed
created: 2026-02-23
branch: quick/003-032-remove-legacy-converter
issue: "#32"
---

# 032-remove-legacy-converter

## 概要

`src/converter/` は旧実装であり、現在は `src/obsidian_etl/` (Kedro パイプライン) に移行済み。
未使用のレガシーコードを削除し、コードベースをクリーンアップする。

## ゴール

- [x] `src/converter/` ディレクトリを完全に削除
- [x] CLAUDE.md からレガシーコード関連の記載を削除
- [x] `make lint` が全て PASS

## スコープ外

- src/obsidian_etl/ の変更
- テストの追加（削除のみ）

## 前提条件

- converter は完全に未使用（Kedro パイプラインに移行済み）
- Makefile に converter 関連ターゲットなし（確認済み）
- converter のテストは tests/ 配下に存在しない（確認済み）

---

## 実装タスク

### Phase 1: 削除

- [x] T001 `src/converter/` ディレクトリを削除
- [x] T002 `CLAUDE.md` からレガシーコード関連記載を削除（3箇所）

### Phase 2: 確認

- [x] T003 `make lint` が全て PASS することを確認
- [x] T004 `make test` が全て PASS することを確認

---

## リスク

| レベル | 内容 |
|-------|------|
| LOW | 削除対象は完全に未使用。他コードからの参照なし |

---

## 完了条件

- [x] 全タスク完了
- [x] Lint PASS
- [x] テスト PASS
