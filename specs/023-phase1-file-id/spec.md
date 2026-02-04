# Feature Specification: 全工程での file_id 付与・維持

**Feature Branch**: `023-phase1-file-id`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "file_idをPhase1で付与。pipeline_stages.jsonlにもfile_idのfieldを追加。全ての工程でfile_idを維持。付与されていない場合は生成。"

## Overview

ファイルのライフサイクル全体を通じて file_id を付与・維持し、トレーサビリティを確保する。

**原則**: どの工程でも「file_id がなければ生成、あれば維持」

```
[Entry Point 1: LLM Import]
Claude Export → Phase 1 (parsed) → Phase 2 (@index/) → Organize (Vaults/)
                    ↑                   ↑                    ↑
                file_id生成         file_id継承          file_id維持

[Entry Point 2: 直接 Organize]
手動配置 → @index/ → Organize (Vaults/)
              ↑            ↑
          file_idなし   file_id生成
```

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Phase 1 完了時点でのファイル追跡 (Priority: P1)

ユーザー（開発者/運用者）として、Phase 1（パース）完了時点で生成された parsed ファイルを一意に識別したい。これにより、Phase 2 でエラーが発生した場合でも、元の parsed ファイルを file_id で特定できる。

**Why this priority**: Phase 2 エラー時のデバッグ・リトライにおいて、元ファイルの特定が最も重要な機能。

**Independent Test**: Phase 1 実行後、parsed ディレクトリのファイルの frontmatter に `file_id: [12文字16進数]` が含まれることを確認。

**Acceptance Scenarios**:

1. **Given** Claude エクスポートデータがある, **When** `make llm-import --phase1-only LIMIT=1` を実行, **Then** 生成された parsed ファイルの frontmatter に `file_id` が含まれる
2. **Given** Phase 1 で生成された parsed ファイルがある, **When** Phase 2 を実行, **Then** 出力ファイルは同じ `file_id` を継承する
3. **Given** 同じ入力ファイルを再度 Phase 1 で処理する, **When** ファイル内容が同一, **Then** 同じ `file_id` が生成される（決定論的）

---

### User Story 2 - pipeline_stages.jsonl での file_id 記録 (Priority: P2)

ユーザー（開発者/運用者）として、各パイプラインステージの実行ログに file_id を含めたい。これにより、ログからファイルへの逆引きが可能になり、処理履歴の追跡が容易になる。

**Why this priority**: US1 の file_id 付与があって初めて意味を持つ。ログの一貫性向上。

**Independent Test**: インポート実行後、`pipeline_stages.jsonl` の各エントリに `file_id` フィールドが存在することを確認。

**Acceptance Scenarios**:

1. **Given** Phase 1 を実行, **When** ステージログを記録, **Then** `pipeline_stages.jsonl` の Phase 1 エントリに `file_id` が含まれる
2. **Given** Phase 2 を実行, **When** ステージログを記録, **Then** `pipeline_stages.jsonl` の Phase 2 エントリに `file_id` が含まれる（Phase 1 と同一）
3. **Given** 既存の pipeline_stages.jsonl（file_id なし）がある, **When** 新規処理を実行, **Then** 新しいエントリのみ file_id を含み、既存エントリは影響を受けない（後方互換性）

---

### User Story 3 - Organize 時の file_id 付与・維持 (Priority: P3)

ユーザー（開発者/運用者）として、`@index/` から Vaults へファイルを移動する際に file_id が付与・維持されることを期待する。LLM import を経由せず直接 `@index/` に配置されたファイルでも、organize 時に file_id が自動付与される。

**Why this priority**: 直接配置されたファイルも含め、全ファイルのトレーサビリティを確保。

**Independent Test**: `/og:organize` 実行後、Vaults 内のすべてのファイルの frontmatter に `file_id` が存在することを確認。

**Acceptance Scenarios**:

1. **Given** `@index/` に file_id 付きファイルがある, **When** `/og:organize` を実行, **Then** 移動先の Vaults ファイルに同じ `file_id` が維持される
2. **Given** `@index/` に file_id なしのファイルがある, **When** `/og:organize` を実行, **Then** organize 処理中に file_id が新規生成され、Vaults ファイルに付与される
3. **Given** organize 処理でファイル内容が正規化される, **When** frontmatter が更新される, **Then** 既存の `file_id` フィールドは変更されない

---

### Edge Cases

- Phase 1 で file_id 生成に失敗した場合 → file_id なしで続行（警告ログ出力）、後続工程で再生成を試みる
- チャンク分割時 → 各チャンクは異なる file_id を持つ（022-import-file-id の仕様を継承）
- organize でファイル名が変更される → file_id は維持（ファイル名とは独立）
- 手動で `@index/` に配置されたファイル → organize 時に file_id を新規生成
- 既に Vaults にあるファイルを再 organize → 既存の file_id を維持

## Requirements *(mandatory)*

### Functional Requirements

**共通原則**:
- **FR-000**: すべての工程において「file_id がなければ生成、あれば維持」の原則を適用する

**Phase 1（パース）**:
- **FR-001**: システムは Phase 1 完了時に、生成される parsed ファイルの frontmatter に `file_id` を含める
- **FR-002**: `file_id` は入力ファイルのパスと内容から決定論的に生成される（同一入力 → 同一 file_id）

**Phase 2（ナレッジ抽出）**:
- **FR-003**: Phase 2 実行時、システムは parsed ファイルから `file_id` を読み取り、出力ファイルに継承する
- **FR-004**: parsed ファイルに file_id がない場合、Phase 2 で新規生成して出力ファイルに付与する

**パイプラインログ**:
- **FR-005**: `pipeline_stages.jsonl` の各エントリに `file_id` フィールドを追加する
- **FR-006**: file_id 生成に失敗した場合、システムは警告ログを出力し、`file_id: null` として処理を続行する
- **FR-007**: 既存の `pipeline_stages.jsonl`（file_id フィールドなし）との後方互換性を維持する

**Organize（整理）**:
- **FR-008**: organize 処理時、`@index/` から Vaults へのファイル移動で frontmatter の `file_id` を維持する
- **FR-009**: file_id が存在しないファイルの場合、organize 処理中に file_id を新規生成して付与する
- **FR-010**: organize でファイル内容を正規化する際、既存の `file_id` フィールドは変更しない

### Key Entities

- **parsed ファイル**: Phase 1 で生成される中間 Markdown ファイル。frontmatter に `file_id` を含む
- **@index ファイル**: Phase 2 または手動配置されるファイル。frontmatter に `file_id` を含む（なければ organize で付与）
- **Vaults ファイル**: organize 後の最終ファイル。frontmatter に `file_id` を必ず含む
- **pipeline_stages.jsonl**: パイプラインステージの実行ログ。`file_id` フィールドを追加
- **file_id**: 12文字の16進数ハッシュ。ファイルパスと内容から SHA-256 で生成

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Phase 1 完了後、100% の parsed ファイルが frontmatter に `file_id` を含む
- **SC-002**: Phase 1 → Phase 2 間で file_id が一致する（継承率 100%）
- **SC-003**: pipeline_stages.jsonl の全エントリに `file_id` フィールドが存在する
- **SC-004**: 既存の state.json/pipeline_stages.jsonl がエラーなく読み込める（後方互換性）
- **SC-005**: 同一入力に対して同一 file_id が生成される（決定論性）
- **SC-006**: organize 後の Vaults ファイルで 100% が file_id を持つ（新規生成含む）
- **SC-007**: file_id により、Vaults ファイルから処理履歴を追跡可能

## Assumptions

- file_id 生成ロジックは 022-import-file-id で実装済みの `generate_file_id()` を再利用する
- parsed ファイル/Vaults ファイルの frontmatter 形式は既存の YAML 形式を踏襲する
- pipeline_stages.jsonl は追記専用であり、既存エントリの変更は行わない
- organize 処理（ollama_normalizer.py）の frontmatter 処理ロジックを拡張する
