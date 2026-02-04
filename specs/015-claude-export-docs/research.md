# Research: Claude Export Knowledge Extraction

**Feature**: 015-claude-export-docs
**Date**: 2026-01-16
**Status**: Complete

## Research Questions

### R1: 知識抽出のプロンプト設計

**Question**: 長い会話ログから「概要」「主要な学び」「実践的なアクション」を効果的に抽出するためのプロンプト設計は？

**Decision**: 構造化出力を求める JSON 形式プロンプト（既存 normalizer パターンを踏襲）

**Rationale**:
- 既存 `normalizer/pipeline/stages.py` で実績のある JSON 出力パターンを採用
- `parse_json_response()` による堅牢な JSON パースを再利用
- フィールドを明確に定義することで、LLM の出力品質が安定

**Alternatives Considered**:
1. Markdown 直接出力 → パースが困難、フォーマット不安定
2. 複数回の LLM 呼び出し（概要→学び→アクション） → 遅延増加、コスト増

### R2: コンテキストウィンドウ制限への対処

**Question**: 長い会話（数万トークン）をどう処理するか？

**Decision**: 会話を適切な長さに分割せず、最初と最後の部分 + サマリー（あれば）を優先的に抽出

**Rationale**:
- 会話の最初（目的の明確化）と最後（結論・成果物）が最も重要
- Claude エクスポートには `summary` フィールドが含まれる場合があり、これを活用
- Ollama のコンテキストウィンドウ（16384 トークン）で処理可能な範囲に収める

**Alternatives Considered**:
1. 会話全体を複数チャンクに分割 → 統合処理が複雑
2. 先頭 N トークンのみ → 結論が欠落するリスク
3. 要約を先に生成 → 2段階処理で遅延増加

### R3: 短い会話のスキップ基準

**Question**: 「知識価値が低い」会話の判定基準は？

**Decision**: メッセージ数 ≤ 2 または総文字数 ≤ 500 文字をスキップ候補とし、最小限のメタデータのみ保存

**Rationale**:
- 1-2往復の会話は質問→回答の単発やりとりが多く、知識として再利用しにくい
- 500文字は日本語で約200単語、意味のある知識抽出には不十分
- スキップではなく「簡略化」として処理し、後から確認可能にする

**Alternatives Considered**:
1. 完全スキップ → ユーザーが見落とすリスク
2. すべて処理 → 低品質ドキュメントが大量生成

### R4: 出力ドキュメントの構造

**Question**: 生成されるナレッジドキュメントのフォーマットは？

**Decision**: Obsidian 互換 Markdown with frontmatter

```yaml
---
title: [会話から抽出したタイトル]
tags:
  - claude-knowledge
  - [抽出されたタグ1]
  - [抽出されたタグ2]
created: [会話の作成日]
source_conversation: [元の会話UUID]
normalized: false
---

## 概要

[会話の目的と主要な成果を1-2段落で]

## 主要な学び

- [学び1]
- [学び2]
- [学び3]

## 実践的なアクション

- [ ] [アクション1]
- [ ] [アクション2]

## コードスニペット（あれば）

\`\`\`[言語]
[重要なコード]
\`\`\`

## 関連リンク

- [[関連ノート1]]
- [[関連ノート2]]
```

**Rationale**:
- `normalized: false` により Phase 3 で追加処理が必要であることを明示
- `source_conversation` で元データへのトレーサビリティを確保
- チェックボックスリストでアクションの実行状態を追跡可能

### R5: 既存コードの再利用範囲

**Question**: `normalizer/io/ollama.py` をどの程度再利用するか？

**Decision**: `call_ollama()` と `parse_json_response()` を直接インポートして再利用

**Rationale**:
- 既にテスト済みの堅牢な実装
- API タイムアウト、リトライ、JSON パースが適切に処理される
- 標準ライブラリのみという制約を維持

**Alternatives Considered**:
1. 完全に独立した実装 → コード重複、バグ混入リスク
2. normalizer パッケージに統合 → 責務の分離が曖昧に

### R6: 中間ファイル削除のタイミング

**Question**: Phase 1 出力（会話ログ Markdown）をいつ削除するか？

**Decision**: Phase 2 処理が成功した会話のみ、個別に削除

**Rationale**:
- バッチ全体の完了を待つと、部分的な失敗時に手動介入が必要
- 処理成功時に即削除することで、ディスク容量を節約
- JSON 状態ファイルで処理済み会話を追跡し、再実行時に重複を回避

**Alternatives Considered**:
1. 全処理完了後に一括削除 → 部分失敗時の対応が複雑
2. 削除しない → ディスク容量消費、重複リスク

## Technical Decisions Summary

| Area | Decision | Key Rationale |
|------|----------|---------------|
| プロンプト | JSON 構造化出力 | 既存パターン踏襲、パース安定 |
| 長文対処 | 先頭+末尾+サマリー優先 | 重要情報の確実な抽出 |
| スキップ基準 | msg≤2 or char≤500 | 簡略化処理、後から確認可能 |
| 出力形式 | frontmatter付きMarkdown | Obsidian互換、Phase 3連携 |
| コード再利用 | ollama.py直接利用 | テスト済み、堅牢 |
| 中間ファイル | 個別削除 | 部分失敗時の柔軟性 |

## Dependencies

- **Ollama API**: `http://localhost:11434/api/chat`（既存設定を利用）
- **Model**: `gpt-oss:20b`（既存 config.py で定義済み）
- **Python**: 3.11+（標準ライブラリのみ）

## Next Steps

1. Phase 1 で `data-model.md` を作成（エンティティ定義）
2. Phase 1 で `contracts/` を作成（CLI インターフェース）
3. Phase 1 で `quickstart.md` を作成（開発者向けガイド）
