---
status: completed
created: 2026-02-21
branch: quick/001-027-sec-organize
issue: "#27"
---

# sec: organize パラメータを別ファイルに分離

## 概要

`conf/base/parameters.yml` に含まれる個人情報（ユーザー名入りパス）を `conf/local/` に分離し、セキュリティを確保する。

## ゴール

- [ ] `vault_base_path` と `genre_vault_mapping` が `conf/local/` に移動
- [ ] リポジトリに個人情報が含まれない
- [ ] 新規セットアップ時の手順が明確

## スコープ外

- organize パイプラインのロジック変更
- genre_keywords の移動（個人情報を含まないため）

## 前提条件

- `conf/local/` は既に `.gitignore` 対象（確認済み ✅）
- Kedro は `conf/local/` を自動マージ（ドキュメント要確認）

---

## 実装タスク

### Phase 1: 調査

- [x] T001 [conf/] Kedro の設定ファイルマージ仕様を確認

### Phase 2: 設定ファイル作成

- [x] T002 [conf/local/parameters_organize.yml.example] テンプレート作成
- [x] T003 [conf/base/parameters.yml] vault_base_path と genre_vault_mapping を削除

### Phase 3: ドキュメント更新

- [x] T004 [P] [CLAUDE.md] セットアップ手順追記
- [x] T005 [P] [Makefile] setup ターゲットに設定ファイルコピー追加

### Phase 4: 動作確認

- [x] T006 `make setup` が正常動作
- [x] T007 Kedro 設定マージ動作確認

---

## リスク

| レベル | 内容 |
|-------|------|
| LOW | Kedro の local 設定マージが期待通り動作しない可能性（調査で解消） |

---

## 完了条件

- [x] 全タスク完了
- [x] `git diff main` に個人情報が含まれない
- [x] `make setup` 成功、Kedro 設定マージ動作確認
