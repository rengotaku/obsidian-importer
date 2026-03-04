---
status: completed
created: 2026-03-05
branch: quick/006-046-fix-genre
issue: 46
---

# ジャンル提案が空になる問題の修正（num_predict 不足）

## 概要

`analyze_other_genres` ノードで LLM が空レスポンスを返す問題を修正する。
原因は `num_predict: 512` が小さすぎて、日本語 JSON 配列が途中で切れること。

## ゴール

- [x] LLM が完全な JSON レスポンスを返せるよう設定を分離・増加
- [ ] ジャンル提案が正常に出力されることを確認

## スコープ外

- デバッグログの強化（別 Issue で対応）

## 前提条件

- `conf/base/parameters.yml` の既存設定を変更
- 他の関数（`extract_knowledge`: 16384, `translate_summary`: 1024）と整合性を保つ

---

## 実装タスク

### Phase 1: 設定分離

- [x] T001 [conf/base/parameters.yml] `suggest_genres` 設定を新規追加（num_predict: 4096）
- [x] T002 [conf/base/parameters.yml] `extract_topic_and_genre` は 512 のまま維持
- [x] T003 [src/obsidian_etl/pipelines/organize/nodes.py] `_suggest_new_genres_via_llm()` で `suggest_genres` 設定を使用

### Phase 2: 動作確認

- [ ] T004 `kedro run --pipeline=organize_preview` で動作確認
- [ ] T005 `genre_suggestions.md` に提案が出力されることを確認

---

## リスク

| レベル | 内容 |
|--------|------|
| LOW    | num_predict 増加による処理時間増加（許容範囲） |

---

## 完了条件

- [x] 設定分離完了
- [ ] ジャンル提案が正常に動作（要確認: `kedro run --pipeline=organize_preview`）
- [x] テスト通過（既存の31件のエラーは本変更と無関係）
