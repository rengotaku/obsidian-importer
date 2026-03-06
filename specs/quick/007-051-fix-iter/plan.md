---
status: completed
created: 2026-03-05
branch: quick/007-051-fix-iter
---

# 051-fix-iter-with-file-id-tests

## 概要

`064-data-layer-separation` で `iter_with_file_id` が `str` のみをサポートするように変更されたが、`extract_knowledge` は `dict` 入力を期待しているため、31件のテストが失敗している。

## 根本原因

| エラー種別 | 件数 | 原因 |
|-----------|------|------|
| `iter_with_file_id only supports str input` | 17 | `iter_with_file_id` が `dict` を拒否 |
| `parameters not found in DataCatalog` | 14 | organize パイプラインが `parameters` を要求するが、テストで追加されていない |

## ゴール

- [x] 全31件のテストが PASS
- [x] 実際のパイプライン（`kedro run`）が動作

## スコープ外

- パイプラインのリファクタリング
- 新機能追加

## 前提条件

- `iter_with_file_id` は transform と organize 両方で使用される
- transform: `dict` 入力（JSON PartitionedDataset）
- organize: `str` 入力（Markdown PartitionedDataset）
- 両方をサポートする必要がある

---

## 実装タスク

### Phase 1: iter_with_file_id の修正

- [x] T001 [src/obsidian_etl/utils/log_context.py] `iter_with_file_id` を `dict` 入力もサポートするように修正
  - TypeError を削除
  - dict の場合は `item.get("metadata", {}).get("file_id")` または `item.get("file_id")` から file_id を抽出
  - str の場合は frontmatter から抽出（現行動作）
  - [tests/utils/test_log_context.py] dict 入力を期待する3つのテストを修正

### Phase 2: テストの parameters 修正

- [x] T002 [tests/test_integration.py] organize パイプラインを使用するテストに `parameters` を追加
  - `MemoryDataset({"import": {...}, "organize": {...}})` 形式で追加
  - 関連テストクラス: `TestResumeAfterFailure`, `TestPartialRunFromTo`, `TestE2EOpenAIImport`, `TestE2EClaudeImport`
  - [src/obsidian_etl/pipelines/organize/nodes.py] `get_ollama_config` 呼び出しを修正 (organize_params を渡す)

### Phase 3: 確認

- [x] T003 `make test` で全テスト PASS を確認 (Issue #51 の31件エラーは解消)
- [x] T004 `make lint` で品質チェック

---

## リスク

| レベル | 内容 |
|-------|------|
| LOW | `iter_with_file_id` の変更は元の動作に戻すだけ |
| LOW | テストの `parameters` 追加は既存動作に影響しない |

---

## 完了条件

- [x] 全タスク完了
- [x] Issue #51 の31件エラー解消 (iter_with_file_id 17件 + parameters 14件)
- [x] lint 通過

## 備考

- 残り3件のエラー (TestExtractKnowledgeFileIdContext) は `set_file_id` 関数が存在しないため発生
- これらは `064-data-layer-separation` で `set_file_id` が削除されたことによる別の問題
- Issue #51 の範囲外
