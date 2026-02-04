# Feature Specification: LLMインポートでのfile_id付与

**Feature Branch**: `022-import-file-id`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "importからfile_idを付与するようにしてほしい"

## Overview

LLMインポート処理（llm_import）で生成されるナレッジファイルに、ファイル追跡用のfile_idを付与する。これにより、インポート時点からファイルを一意に識別でき、後続の正規化処理（normalizer）との連携やファイル移動後の追跡が可能になる。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - インポート時のfile_id自動付与 (Priority: P1)

ユーザーがClaudeエクスポートデータをインポートすると、生成されるナレッジファイルのfrontmatterにfile_idが自動的に付与される。これにより、ファイルが@indexからVaultに移動しても追跡可能になる。

**Why this priority**: file_idの付与はこの機能の核心であり、これがなければ追跡機能は成立しない。

**Independent Test**: `make llm-import LIMIT=1`を実行し、生成されたファイルのfrontmatterにfile_idが含まれていることを確認する。

**Acceptance Scenarios**:

1. **Given** Claudeエクスポートデータが存在する, **When** `make llm-import`を実行する, **Then** 生成されたMarkdownファイルのfrontmatterに`file_id: [12文字の16進数]`が含まれる
2. **Given** 同じ会話を再度インポートする, **When** ファイルが既に処理済みの場合, **Then** 同じfile_idが生成される（決定論的）
3. **Given** インポート処理が完了する, **When** session.jsonを確認する, **Then** 処理したファイルのfile_idが記録されている

---

### User Story 2 - state.jsonでのfile_id記録 (Priority: P2)

インポート処理の状態管理（state.json）にfile_idを記録し、リトライ処理やエラー追跡でファイルを特定できるようにする。

**Why this priority**: 状態管理との連携により、リトライ時やエラー調査時にファイルを追跡できる。US1の付加価値。

**Independent Test**: インポート後にstate.jsonを確認し、processedエントリにfile_idが含まれていることを確認する。

**Acceptance Scenarios**:

1. **Given** インポートが正常完了する, **When** state.jsonを確認する, **Then** processedエントリにfile_idが含まれる
2. **Given** インポートでエラーが発生する, **When** state.jsonを確認する, **Then** errorsエントリにfile_idが含まれる（エラー発生前にfile_idが生成されていた場合）

---

### Edge Cases

- 空のコンテンツの場合: file_idは生成される（空文字列もハッシュ可能）
- 非常に長いタイトルの場合: file_idは正常に生成される（コンテンツベースのため影響なし）
- チャンク分割された会話の場合: 各チャンクに異なるfile_idが付与される
- 日本語タイトル・コンテンツの場合: UTF-8エンコーディングでハッシュ化され、正常に動作する

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、Phase 2出力（ナレッジファイル）のfrontmatterにfile_idを含めなければならない
- **FR-002**: file_idは12文字の16進数ハッシュでなければならない（既存のnormalizerと同じ形式）
- **FR-003**: file_idは会話コンテンツと初回出力パスから決定論的に生成されなければならない
- **FR-004**: システムは、state.jsonのprocessedエントリにfile_idを記録しなければならない
- **FR-005**: システムは、KnowledgeDocumentのto_markdown()メソッドでfile_idをfrontmatterに出力しなければならない
- **FR-006**: チャンク分割処理の場合、各チャンクに固有のfile_idを付与しなければならない

### Key Entities

- **KnowledgeDocument**: ナレッジファイルを表すデータクラス。file_idフィールドを追加する
- **StateManager**: 処理状態を管理。processedエントリにfile_idを含める
- **file_id**: 12文字の16進数ハッシュ。コンテンツ+パスから生成される一意識別子

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100%のインポートされたファイルにfile_idがfrontmatterに含まれる
- **SC-002**: 同一入力に対するfile_idは100%再現可能（決定論的）
- **SC-003**: file_idは12文字の16進数形式に100%準拠する
- **SC-004**: state.jsonの全processedエントリにfile_idが含まれる

## Assumptions

- 既存のnormalizerで使用されている`generate_file_id`関数のロジックを再利用または移植する
- file_idの生成はコンテンツ + 出力パスをベースとする（normalizer と同じアルゴリズム）
- 後方互換性: file_idがないファイルも引き続き処理可能
