# Feature Specification: Claude Export Knowledge Extraction

**Feature Branch**: `015-claude-export-docs`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "claude（web）のexportした内容を、まとめとした知識として残せる状態のドキュメントにしたい。"

## Processing Pipeline

Claude エクスポートデータは3段階のパイプラインで処理する：

1. **Phase 1: JSON → Markdown 変換**（既存 `parse_claude_export.py`）
   - Claude エクスポートの `conversations.json` を読み込み
   - 会話ログをそのまま Markdown ファイルに変換
   - 出力先: `@index/claude/parsed/conversations/`

2. **Phase 2: 会話 → 知識のまとめ**（**本機能で新規実装**）
   - Phase 1 出力の会話ログ Markdown を入力
   - **ローカル LLM（Ollama）を使用**（膨大なドキュメント数のため Claude Code では処理不可）
   - 長い会話から要点・学び・アクションを抽出し、まとめドキュメントを生成
   - 出力先: `@index/`

3. **Phase 3: Obsidian 形式に正規化**（既存 `ollama_normalizer.py`）
   - Phase 2 の出力を Obsidian 形式に整える（frontmatter、リンク形式など）
   - Vault への自動分類（エンジニア、ビジネス、経済、日常、その他）

## Implementation Architecture

- **Phase 2 スクリプト**: 完全に独立した新規スクリプトとして実装
- **エントリーポイント**: `.claude/commands/og/import-claude.md`（`/og:import-claude` コマンド）
  - 利用者は個別スクリプトを意識せず、コマンド経由で Phase 1〜3 を一括実行可能
  - 内部で各 Phase のスクリプトを順次呼び出し
- **出力単位**: 1会話 = 1ナレッジドキュメント
  - Claude に「まとめて」と依頼したときと同様の出力形式
  - 会話全体の要点、主要な学び、実践的なアクションを含む
- **中間ファイルの扱い**: Phase 1 出力（会話ログ Markdown）は Phase 2 処理完了後に削除
  - ナレッジドキュメントのみを残す（元の会話ログは保持しない）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Knowledge Extraction (Priority: P1)

ユーザーが Claude (web) からエクスポートしたデータを処理し、会話から得られた知識・学びを抽出して、後から参照可能なナレッジドキュメントとして保存したい。

**Why this priority**: 現状の `parse_claude_export.py` は会話ログをそのまま Markdown に変換するだけで、知識として再利用できない。会話から価値ある情報を抽出し、整理されたドキュメントとして残すことがユーザーの主目的。

**Independent Test**: エクスポートデータを処理し、生成されたドキュメントが「概要」「主要な学び」「実践的なアクション」を含む構造化された形式になっていることを確認できる。

**Acceptance Scenarios**:

1. **Given** Claude エクスポートデータ（conversations.json）がある、**When** 知識抽出処理を実行する、**Then** 各会話から抽出された知識が構造化されたドキュメントとして生成される
2. **Given** 複数の会話が同じトピックに関するものである、**When** 処理を実行する、**Then** 関連する会話がリンクまたはグループ化される
3. **Given** 会話に技術的な内容が含まれる、**When** 処理を実行する、**Then** コードスニペットや手順が保持され、適切にフォーマットされる

---

### User Story 2 - Automatic Genre Classification (Priority: P2)

生成されたナレッジドキュメントが、内容に基づいて自動的に適切な Vault（エンジニア、ビジネス、経済、日常、その他）に分類されるようにしたい。

**Why this priority**: 知識抽出後に手動で分類するのは手間がかかる。既存の ollama_normalizer.py と連携し、生成されたドキュメントを自動分類することで、ワークフローを効率化できる。

**Independent Test**: 生成されたナレッジドキュメントに対して既存の分類パイプラインを実行し、適切な Vault に移動されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 技術的な会話から生成されたドキュメント、**When** 分類処理を実行する、**Then** `エンジニア/` Vault に振り分けられる
2. **Given** ビジネス関連の会話から生成されたドキュメント、**When** 分類処理を実行する、**Then** `ビジネス/` Vault に振り分けられる

---

### User Story 3 - Summary Translation (Priority: P3)

Claude エクスポートに含まれる英語の "Summary/Conversation Overview" セクションを日本語に翻訳し、日本語話者にとって読みやすいドキュメントにしたい。

**Why this priority**: 現状、Claude のエクスポートには英語のサマリーが自動生成されており、日本語ユーザーにとって読みにくい。既存の Stage 3 正規化で対応可能だが、知識抽出と統合することでより自然なドキュメントになる。

**Independent Test**: 英語サマリーを含むエクスポートデータを処理し、生成されたドキュメントのサマリーが日本語になっていることを確認できる。

**Acceptance Scenarios**:

1. **Given** 英語の "Conversation Overview" を含むエクスポートデータ、**When** 処理を実行する、**Then** サマリー部分が日本語に翻訳されている

---

### Edge Cases

- 会話内容が非常に短い（1-2往復）場合、意味のある知識を抽出できない可能性がある → 最小限のメタデータのみ保存するか、スキップする
- 会話が断片的または文脈が不明確な場合 → 元の会話へのリンクを保持し、ユーザーが参照できるようにする
- 複数言語が混在する会話 → 主要言語を検出し、一貫性のある出力を生成する
- 機密情報を含む可能性のある会話 → ユーザーが確認・編集できるプレビューモードを提供する

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、Claude エクスポートの conversations.json から会話データを読み込める MUST
- **FR-002**: システムは、各会話から「概要」「主要な学び」「実践的なアクション」を抽出してドキュメントを生成する MUST
- **FR-003**: システムは、会話に含まれるコードスニペットや手順を適切にフォーマットして保持する MUST
- **FR-004**: システムは、生成されたドキュメントに Obsidian 互換の frontmatter（title, tags, created, related）を付与する MUST
- **FR-005**: システムは、英語の "Summary/Conversation Overview" を日本語に翻訳する SHOULD
- **FR-006**: システムは、短すぎる会話（知識価値が低い）をスキップまたは簡略化して処理する SHOULD
- **FR-007**: システムは、生成されたドキュメントを既存の分類パイプライン（ollama_normalizer.py）と連携して Vault に振り分けできる SHOULD
- **FR-008**: システムは、処理前にプレビューモードでユーザーに確認を求めることができる MAY
- **FR-009**: システムは、元の会話ログファイルへの参照（リンク）を生成されたドキュメントに含める MUST

### Key Entities

- **ExportData**: Claude からエクスポートされた JSON データ（conversations.json, memories.json, projects.json）
- **Conversation**: 個別の会話。uuid, name, summary, chat_messages を含む
- **KnowledgeDocument**: 会話から抽出された知識を含む構造化ドキュメント。概要、学び、アクション、関連リンクを含む
- **VaultCategory**: 振り分け先の Vault カテゴリ（エンジニア、ビジネス、経済、日常、その他）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 生成されたナレッジドキュメントの 90% 以上が、「概要」セクションを含む構造化された形式になっている
- **SC-002**: ユーザーが生成されたドキュメントを見て、元の会話を読まなくても要点を理解できる（主観的だが、サンプルテストで検証）
- **SC-003**: 処理時間が 1 会話あたり 30 秒以内である（LLM 処理を含む）
- **SC-004**: 生成されたドキュメントの 80% 以上が、後続の分類パイプラインで適切な Vault に自動振り分けされる
- **SC-005**: 英語サマリーを含む会話の 95% 以上で、日本語翻訳が正常に完了する

## Scope & Boundaries

### In Scope

- Claude (web) エクスポートデータの解析と知識抽出
- 構造化されたナレッジドキュメントの生成
- 既存の分類パイプライン（ollama_normalizer.py）との連携
- 英語サマリーの日本語翻訳
- Obsidian 互換フォーマットでの出力

### Out of Scope

- Claude Code や他のプラットフォームからのエクスポート対応
- リアルタイムでの会話キャプチャ（エクスポート後の処理のみ）
- 複数ユーザーのエクスポートデータのマージ
- GUI/Web インターフェース（CLI ツールとして実装）

## Assumptions

- ユーザーは Claude (web) からデータをエクスポート済みである
- エクスポートデータは標準的な JSON 形式（conversations.json, memories.json, projects.json）である
- Ollama が利用可能であり、知識抽出と翻訳に使用できる
- 出力先は Obsidian Vault（@index/ フォルダ）である
- 既存の ollama_normalizer.py パイプラインが正常に動作している

## Clarifications

### Session 2026-01-16

- Q: Stage 1 出力をどう処理するか？ → A: Phase 1 出力の Markdown を入力として、ローカル LLM（Ollama）で知識抽出を行う
- Q: Phase 2 の実装方式は？ → A: 完全に独立した新規スクリプト。ただし `/og:import-claude` コマンドでラップし利用者は意識しない
- Q: Phase 2 の出力単位は？ → A: 1会話 = 1ナレッジドキュメント（Claude に「まとめて」と依頼したときと同様の形式）
- Q: Phase 1 出力（会話ログ）の保持は？ → A: Phase 2 処理完了後に削除。ナレッジドキュメントのみ残す
