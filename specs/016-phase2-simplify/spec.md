# Feature Specification: Phase 2 簡素化 - 役割分離と構造化概要

**Feature Branch**: `016-phase2-simplify`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "Phase 2の簡素化: title/tags/relatedをPhase 3に委譲し、Summaryの日本語翻訳と構造化された概要生成に集中"

## 背景

LLM Import パイプラインの Phase 2（知識抽出）と Phase 3（正規化）で処理が重複している。

### 現状の問題

1. **重複処理**: Phase 2 で title, tags, related_keywords を抽出しているが、Phase 3 でも同様の処理を行う
2. **概要の品質**: 現在の `## まとめ` は構造がない壁のテキスト。元の会話にある表やリストを無視している
3. **関連セクション**: Phase 2 で `## 関連` を生成しているが、これは別のObsidianプロセスで追加すべき

### 解決方針

- Phase 2 の役割を「知識抽出 + サマリー翻訳/構造化」に限定
- title, tags, related は Phase 3 に委譲
- 概要を構造化（表、リスト、見出しを使用）

## User Scenarios & Testing

### User Story 1 - 構造化されたまとめの生成 (Priority: P1)

ユーザーが Claude との会話データをインポートすると、会話内容が構造化された形式（表、リスト、小見出し）で `## まとめ` セクションに出力される。元の会話が表形式の情報を含む場合、まとめにも表が使用される。

**Why this priority**: まとめの品質が最も重要。壁のテキストではなく、読みやすい構造化された情報が必要。

**Independent Test**: 表やリストを含む会話を処理し、出力の `## まとめ` が構造化されていることを確認する。

**Acceptance Scenarios**:

1. **Given** 表形式の情報を含む会話, **When** Phase 2 を実行, **Then** まとめに表が含まれる
2. **Given** 複数のトピックを含む会話, **When** Phase 2 を実行, **Then** まとめに小見出しまたはリストで整理される
3. **Given** 手順を説明する会話, **When** Phase 2 を実行, **Then** まとめに番号付きリストが含まれる

---

### User Story 2 - 英語サマリーの日本語翻訳 (Priority: P1)

Parse で生成された会話ファイルに `## Summary`（英語）がある場合、Phase 2 で日本語に翻訳され、frontmatter の `summary` プロパティと `## まとめ` セクションに反映される。

**Why this priority**: Claude の会話サマリーは英語で生成されるため、日本語翻訳は必須。

**Independent Test**: 英語 Summary を含む会話を処理し、日本語のまとめが生成されることを確認する。

**Acceptance Scenarios**:

1. **Given** `## Summary` が英語で存在する会話, **When** Phase 2 を実行, **Then** `## まとめ` が日本語で生成される
2. **Given** `## Summary` が英語で存在する会話, **When** Phase 2 を実行, **Then** frontmatter に `summary` プロパティが追加される
3. **Given** `## Summary` が存在しない会話, **When** Phase 2 を実行, **Then** LLM が会話内容からまとめを生成する

---

### User Story 3 - ファイル名の簡素化 (Priority: P2)

出力ファイル名は、会話タイトルから日付プレフィックスを除去したものを使用する。LLM によるタイトル生成は行わない。

**Why this priority**: ファイル名の一貫性と処理の簡素化。

**Independent Test**: 日付プレフィックス付きの会話を処理し、出力ファイル名に日付が含まれないことを確認する。

**Acceptance Scenarios**:

1. **Given** `2025-12-18_温泉BGMシステムのビジネス可能性.md`, **When** Phase 2 を実行, **Then** 出力ファイル名は `温泉BGMシステムのビジネス可能性.md`
2. **Given** `2025-12-23_設定ファイルのGithub公開運用方法.md`, **When** Phase 2 を実行, **Then** 出力ファイル名は `設定ファイルのGithub公開運用方法.md`

---

### User Story 4 - Phase 3 への委譲項目の削除 (Priority: P2)

Phase 2 は title, tags, related_keywords を抽出しない。これらは Phase 3 で処理される。

**Why this priority**: 重複処理の排除。

**Independent Test**: Phase 2 の出力に tags, `## 関連` セクションが含まれないことを確認する。

**Acceptance Scenarios**:

1. **Given** 任意の会話, **When** Phase 2 を実行, **Then** 出力の frontmatter に `tags` が含まれない
2. **Given** 任意の会話, **When** Phase 2 を実行, **Then** 出力に `## 関連` セクションが含まれない
3. **Given** 任意の会話, **When** Phase 2 を実行, **Then** LLM プロンプトに title, tags, related_keywords の抽出指示が含まれない

---

### Edge Cases

- Summary が空または非常に短い場合 → LLM で概要を生成
- 会話が技術的でない場合（日常会話など）→ リスト形式で要点をまとめる
- 会話タイトルに禁止文字（`<>:"/\|?*`）が含まれる場合 → 禁止文字を除去

## Requirements

### Functional Requirements

- **FR-001**: システムは Phase 2 で title を LLM で抽出しない。会話タイトルから日付プレフィックスを除去して使用する
- **FR-002**: システムは Phase 2 で tags を LLM で抽出しない（Phase 3 に委譲）
- **FR-003**: システムは Phase 2 で related_keywords を抽出しない、`## 関連` セクションを生成しない
- **FR-004**: システムは `## Summary`（英語）が存在する場合、日本語に翻訳して `## まとめ` と frontmatter.summary に設定する
- **FR-005**: システムは `## Summary` が存在しない場合、会話内容から構造化されたまとめを LLM で生成する
- **FR-006**: まとめは構造化された形式（表、リスト、小見出し）で出力する。壁のテキストは禁止
- **FR-007**: システムは key_learnings, code_snippets の抽出を継続する（action_items は削除）
- **FR-008**: 出力ファイル名は `YYYY-MM-DD_` プレフィックスを除去した会話タイトルを使用する

### Key Entities

- **会話ファイル（Phase 1 出力）**:
  - frontmatter: title, uuid, created, updated, tags
  - `## Summary`: Claude が生成した英語サマリー（オプション）
  - `## 会話`: ユーザーとアシスタントのやり取り

- **ナレッジファイル（Phase 2 出力）**:
  - frontmatter: title, created, source_provider, source_conversation, summary（日本語）, normalized: false
  - `## まとめ`: 会話内容を構造的に表現（表、リスト、小見出し）
  - `## 主要な学び`: 箇条書き
  - `## コードスニペット`: コードブロック（あれば）

## Success Criteria

### Measurable Outcomes

- **SC-001**: 概要セクションの80%以上が構造化要素（表、リスト、小見出し）を含む
- **SC-002**: 英語 Summary がある会話の100%で日本語翻訳された概要が生成される
- **SC-003**: 出力ファイルの100%で日付プレフィックスが除去されている
- **SC-004**: 出力ファイルの0%に `## 関連` セクションが含まれる
- **SC-005**: 出力 frontmatter の0%に `tags` が含まれる（Phase 3 で付与）

## Assumptions

- Phase 1 の出力形式（frontmatter + `## Summary` + `## 会話`）は変更しない
- Phase 3 は既存の正規化ロジックを維持し、Phase 2 出力を正しく処理できる
- Ollama API は日本語翻訳と構造化出力に対応している
