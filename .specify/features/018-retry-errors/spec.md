# Feature Specification: エラーファイルのリトライ機能

**Feature Branch**: `018-retry-errors`
**Created**: 2026-01-17
**Status**: Draft
**Input**: User description: "--retry-errors"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - エラーファイルの自動リトライ (Priority: P1)

ユーザーは LLM インポート処理で発生したエラーファイルのみを再処理したい。前回の処理で errors.json に記録されたファイルを自動的に検出し、再度 Phase 2 処理を実行する。

**Why this priority**: 21件のエラーが発生しており、全体を再実行せずにエラー分のみを効率的に再処理することで、時間と API リソースを節約できる。

**Independent Test**: `make retry` を実行し、errors.json に記録されたファイルのみが処理されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 前回のインポートセッションで errors.json にエラーが記録されている, **When** `make retry` を実行, **Then** 新しいセッションが作成され、errors.json に記録されたファイルのみが Phase 2 処理の対象となる
2. **Given** errors.json が空である, **When** `make retry` を実行, **Then** 「リトライ対象のエラーがありません」と表示され処理が終了する
3. **Given** リトライ処理が成功した, **When** 処理完了後, **Then** 元のセッションの errors.json は変更されず、新しいセッションに処理結果が記録される

---

### User Story 2 - セッション指定によるリトライ (Priority: P2)

ユーザーは特定のセッションのエラーファイルをリトライしたい。複数のインポートセッションが存在する場合、対象セッションを明示的に指定できる。

**Why this priority**: 複数回インポートを実行した場合、どのセッションのエラーをリトライするか選択できる必要がある。

**Independent Test**: `make retry SESSION=<session_id>` でセッションを指定し、そのセッションのエラーのみが処理されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 複数のインポートセッションが存在する, **When** `make retry SESSION=import_20260116_203426` を実行, **Then** 指定セッションの errors.json からエラーファイルが読み込まれる
2. **Given** セッション指定なしで `make retry` を実行, **When** エラーを含むセッションが存在する, **Then** 対象セッション一覧（セッションID、エラー件数、最終更新日時）が表示され、処理は実行されない
3. **Given** 存在しないセッション ID を指定, **When** 実行, **Then** エラーメッセージ「セッション '{id}' が見つかりません」と表示される
4. **Given** エラーを含むセッションが1つのみ存在する, **When** セッション指定なしで `make retry` を実行, **Then** そのセッションが自動的に選択されリトライが実行される

---

### User Story 3 - プレビューモードでのリトライ確認 (Priority: P3)

ユーザーはリトライ前に対象ファイルを確認したい。実際の処理を行わずに、どのファイルがリトライ対象かを一覧表示する。

**Why this priority**: 再処理前に対象を確認することで、意図しないファイルの処理を防げる。

**Independent Test**: `make retry ACTION=preview` で対象ファイル一覧が表示され、実際の処理は行われないことを確認できる。

**Acceptance Scenarios**:

1. **Given** errors.json にエラーが記録されている, **When** `make retry ACTION=preview` を実行, **Then** リトライ対象ファイルの一覧（ファイル名、エラー種別、発生日時）が表示される
2. **Given** プレビューモードで実行, **When** 表示完了後, **Then** ファイルは変更されず、errors.json も更新されない

---

### Edge Cases

- errors.json が存在しない場合 → エラーメッセージを表示して終了
- errors.json が壊れている（不正な JSON）場合 → エラーメッセージを表示して終了
- 元の会話ファイル（Phase 1 出力）が削除されている場合 → そのファイルをスキップし、ログに記録
- リトライ中に新たなエラーが発生した場合 → 新しいセッションの errors.json に記録（元のセッションは変更しない）
- タイムアウトエラーの場合 → タイムアウト値を増加させるオプション（`--timeout`）を提供
- エラーを含むセッションが存在しない場合 → 「リトライ対象のセッションがありません」と表示して終了

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `--retry-errors` オプションを CLI 引数として受け付け、errors.json からエラーファイルを読み込む
- **FR-001a**: Makefile に `retry` ターゲットを定義し、以下のコマンドでリトライを実行可能にする
  - `make retry` - 最新セッションのエラーをリトライ
  - `make retry SESSION=import_20260116_203426` - 指定セッションのエラーをリトライ
  - `make retry ACTION=preview` - リトライ対象をプレビュー
  - `make retry TIMEOUT=180` - タイムアウト値を指定
- **FR-002**: システムは errors.json の `file` フィールド（会話 ID）を使用して、対応する Phase 1 出力ファイルを特定する
- **FR-003**: システムは Phase 2 処理のみを実行する（Phase 1 はスキップ）
- **FR-004**: システムはリトライ用の新しいセッションディレクトリを作成する（例: `import_20260117_120000`）
- **FR-005**: システムは元のセッションの errors.json を変更せず、履歴として保持する
- **FR-006**: システムは新しいセッションに処理結果（成功/失敗）を記録する
- **FR-007**: システムは `--session <session_id>` オプションで特定セッションを指定可能にする
- **FR-008**: システムはセッション未指定時、エラーを含むセッション一覧を表示する（1件のみの場合は自動選択）
- **FR-009**: システムは `--preview` と組み合わせてリトライ対象の一覧表示のみを行う
- **FR-010**: システムは `--timeout <seconds>` オプションでタイムアウト値をカスタマイズ可能にする（デフォルト: 120秒）
- **FR-011**: システムはリトライ処理の進捗を標準出力に表示する
- **FR-012**: システムは新しいセッションの session.json に元のセッション ID を `source_session` として記録する
- **FR-013**: システムは execution.log の先頭にリトライ情報を出力する（元セッションID、エラー件数、リトライ開始日時）

### Key Entities

- **Error Entry**: エラー情報を保持するエンティティ（file, error, stage, timestamp）
- **Session**: インポートセッション（session_id, started_at, updated_at, total_files, provider, source_session?）
- **Processed Entry**: 処理済みファイル情報（file, output, status, processed_at）

※ リトライセッションは通常の Session に `source_session` フィールドが追加される形式

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: リトライ対象のファイル特定が1秒以内に完了する
- **SC-002**: リトライ成功率が通常処理と同等以上である（同じ入力に対して）
- **SC-003**: 21件のエラーファイルのリトライ処理が、全体再実行の10%未満の時間で完了する
- **SC-004**: リトライセッションで成功したファイルは、新しい processed.json に記録される
- **SC-005**: ユーザーがプレビューモードで対象を確認後、安心してリトライを実行できる

## Assumptions

- errors.json のフォーマットは既存の構造（file, error, stage, timestamp）を維持する
- Phase 1 出力ファイル（中間 Markdown）はリトライ時点で存在していることが前提
- セッションディレクトリは `.staging/@plan/import_*` の命名規則に従う（リトライも同じ形式）
- 既存の `--phase2-only` オプションのロジックを活用できる
- セッション履歴は `source_session` フィールドでチェーン可能（元 → リトライ1 → リトライ2...）
