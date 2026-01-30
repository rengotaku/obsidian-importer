# Feature Specification: Summary 日本語化

**Feature Branch**: `008-japanese-summary`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Summaryは日本語に直すようにする"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Claude エクスポート文書の Summary 日本語化 (Priority: P1)

ユーザーが @index/ フォルダ内の Claude エクスポートから生成されたファイルを正規化する際、英語で書かれた「Summary」や「Conversation Overview」セクションが自動的に日本語に翻訳される。

**Why this priority**: Claude エクスポートファイルは会話内容自体は日本語だが、自動生成されたサマリー部分が英語になっている。これにより文書全体の一貫性が損なわれ、可読性が低下している。

**Independent Test**: 英語サマリーを含むファイルを正規化処理にかけ、サマリー部分が日本語に翻訳されていることを確認する。

**Acceptance Scenarios**:

1. **Given** 英語の「Summary」セクションを含むファイル, **When** 正規化処理を実行, **Then** Summary セクションが日本語に翻訳される
2. **Given** 英語の「Conversation Overview」セクションを含むファイル, **When** 正規化処理を実行, **Then** Conversation Overview が日本語の概要に置き換わる
3. **Given** 会話内容が日本語のファイル, **When** 正規化処理を実行, **Then** サマリーも日本語で統一される

---

### User Story 2 - 既存の日本語サマリーの保持 (Priority: P2)

既に日本語でサマリーが書かれているファイルは、そのまま保持される。

**Why this priority**: 既に正規化済みのファイルを再処理しても意図しない変更が発生しないことを保証する。

**Independent Test**: 日本語サマリーを含むファイルを正規化処理にかけ、内容が変更されていないことを確認する。

**Acceptance Scenarios**:

1. **Given** 日本語の Summary を含むファイル, **When** 正規化処理を実行, **Then** サマリー内容は変更されない

---

### Edge Cases

- 英語と日本語が混在するサマリーの場合、日本語に統一する
- サマリーセクションが存在しないファイルは、サマリー翻訳処理をスキップする
- 翻訳処理がエラーを返した場合、元の英語サマリーを保持し、エラーをログに記録する
- 完全英語文書であっても、サマリーは日本語に翻訳する（例外なし）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、ファイル内の「Summary」「Conversation Overview」セクションを検出できる MUST
- **FR-002**: システムは、検出されたサマリーセクションが英語かどうかを判定できる MUST
- **FR-003**: システムは、英語サマリーを**いかなる場合も**日本語に翻訳する MUST（Stage 3 の一部として処理）
- **FR-004**: システムは、翻訳後のサマリーが元の意味を正確に伝える MUST
- **FR-005**: システムは、翻訳エラー時に元のサマリーを保持し、処理を継続する MUST

### Implementation Note

- 本機能は既存の `stage3_normalize` に統合する
- `stage3_normalize.txt` プロンプトに Summary 翻訳指示を追加

### Key Entities

- **Summary Section**: ファイル内の要約部分。「## Summary」や「**Conversation Overview**」で始まるセクション

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Claude エクスポート由来のファイルの 95% 以上で、サマリーが日本語化される
- **SC-002**: 翻訳されたサマリーは、元の英語サマリーの主要な情報をすべて含む
- **SC-003**: 正規化処理の所要時間が、サマリー翻訳追加により 20% 以上増加しない
- **SC-004**: 翻訳エラー発生時も、ファイル処理全体は正常に完了する

## Assumptions

- Ollama LLM は日英翻訳に対応したモデルが利用可能
- Claude エクスポートファイルのサマリー形式は一貫している（「Summary」「Conversation Overview」）
