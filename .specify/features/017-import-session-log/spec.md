# Feature Specification: Import Session Log

**Feature Branch**: `017-import-session-log`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "llm_import に既存の normalizer/io/session.py と同様のセッション管理機能を追加し、@plan ディレクトリに進捗ログを出力する"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 処理進捗の可視化 (Priority: P1)

ユーザーが `llm_import` で大量の会話データを処理する際、`.staging/@plan/import_YYYYMMDD_HHMMSS/` ディレクトリに進捗ログが出力され、リアルタイムで処理状況を確認できる。

**Why this priority**: 長時間処理（数百件の会話処理）では進捗確認が必須。現状では出力ファイル数を手動カウントするしかなく、処理状況が不透明。

**Independent Test**: 10件以上の会話を処理し、セッションディレクトリ内のログファイルで進捗を確認できる。

**Acceptance Scenarios**:

1. **Given** llm_import を実行開始した状態, **When** 処理が開始される, **Then** `.staging/@plan/import_YYYYMMDD_HHMMSS/` ディレクトリが作成され、`session.json` と `execution.log` が生成される
2. **Given** 処理が進行中の状態, **When** コンソールを確認する, **Then** プログレスバーと各会話の Phase 1/Phase 2 結果がリアルタイムで表示される
3. **Given** 処理が進行中の状態, **When** `execution.log` を確認する, **Then** コンソールと同じ内容がタイムスタンプ付きで記録されている
4. **Given** 処理が完了した状態, **When** サマリーを確認する, **Then** 成功/エラー/スキップ数、Phase別内訳、平均処理時間、出力先パス、セッションディレクトリパスが表示される

---

### User Story 2 - ステージ別処理詳細の記録 (Priority: P2)

各会話の Phase 1（JSON→Markdown）と Phase 2（LLM知識抽出）の処理時間と結果が `pipeline_stages.jsonl` に記録され、パフォーマンス分析が可能になる。

**Why this priority**: LLM処理のボトルネック特定や処理時間の見積もりに必要。normalizer と同じ形式で記録することで、既存の分析ツールを流用可能。

**Independent Test**: 5件の会話を処理し、`pipeline_stages.jsonl` に各ステージの処理時間が記録されていることを確認できる。

**Acceptance Scenarios**:

1. **Given** 会話処理が完了した状態, **When** `pipeline_stages.jsonl` を確認する, **Then** 各会話の phase1, phase2 の処理時間（timing_ms）が JSONL 形式で記録されている
2. **Given** Phase 2 でエラーが発生した場合, **When** `pipeline_stages.jsonl` を確認する, **Then** エラーが発生したステージと理由が記録されている

---

### User Story 3 - 状態ファイルの分離管理 (Priority: P3)

処理済み、保留中、エラーの会話が `processed.json`, `pending.json`, `errors.json` に分離して記録され、再実行時の継続処理やエラー調査が容易になる。

**Why this priority**: 現状の `.extraction_state.json` は単一ファイルで管理しているが、normalizer と同様に分離することで運用性が向上する。

**Independent Test**: 一部エラーを含む処理を実行し、各状態ファイルに適切に分類されていることを確認できる。

**Acceptance Scenarios**:

1. **Given** 処理が完了した状態, **When** `processed.json` を確認する, **Then** 成功した会話のリストが記録されている
2. **Given** エラーが発生した会話がある状態, **When** `errors.json` を確認する, **Then** エラー会話とエラー詳細が記録されている
3. **Given** Phase 2 制限で未処理の会話がある状態, **When** `pending.json` を確認する, **Then** 未処理会話のリストが記録されている

---

### Edge Cases

- セッションディレクトリの作成に失敗した場合（権限不足等）は、ログ出力をスキップして処理を継続する
- 既存セッションがある状態で新規処理を開始した場合、新しいセッションを作成する
- 処理中にプロセスが強制終了された場合、最後に書き込まれた状態までは保持される

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a session directory at `.staging/@plan/import_YYYYMMDD_HHMMSS/` when processing starts
- **FR-002**: System MUST write `session.json` with session metadata (session_id, started_at, updated_at, total_files)
- **FR-003**: System MUST write human-readable progress to `execution.log` with timestamps
- **FR-004**: System MUST record each processing stage to `pipeline_stages.jsonl` in JSONL format
- **FR-005**: System MUST maintain separate state files: `processed.json`, `pending.json`, `errors.json`
- **FR-006**: System MUST write `results.json` with final processing summary upon completion
- **FR-007**: System MUST follow the same file format as `normalizer/io/session.py` for compatibility
- **FR-008**: System MUST update `execution.log` in real-time (flush after each write)
- **FR-009**: System MUST continue processing even if session logging fails (graceful degradation)
- **FR-010**: System MUST display progress bar during processing (e.g., `[████████░░░░░░░░] 25/100 (25.0%)`)
- **FR-011**: System MUST show per-conversation result with phase status (e.g., `[1/100] タイトル... Phase1 ✅ Phase2 ✅ (15.2s)`)
- **FR-012**: System MUST display rich summary on completion including:
  - Total processed / success / error / skipped counts
  - Phase 1 only vs Phase 2 completed breakdown
  - Average processing time per conversation
  - Output directory path
  - Session directory path for detailed logs
- **FR-013**: System MUST write identical content to both console and `execution.log` (dual output)

### Key Entities

- **Session**: 処理セッションを表す。session_id、開始時刻、更新時刻、対象ファイル数を持つ
- **StageRecord**: 各処理ステージの記録。タイムスタンプ、ファイル名、ステージ名（phase1/phase2）、処理時間、スキップ理由を持つ
- **ProcessingState**: 会話の処理状態。processed（成功）、pending（未処理）、error（エラー）に分類

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 処理開始から1秒以内にセッションディレクトリと初期ファイルが作成される
- **SC-002**: `execution.log` を見れば、任意の時点での処理進捗（N/M件完了）が分かる
- **SC-003**: `pipeline_stages.jsonl` の各レコードに timing_ms が記録され、処理時間の分析が可能
- **SC-004**: normalizer の既存分析スクリプト・ツールが llm_import のセッションログでも動作する（フォーマット互換性）
- **SC-005**: セッション機能追加後も、既存の `--status` コマンドが正常に動作する
- **SC-006**: コンソール出力を見るだけで、処理全体の状況と結果が一目で分かる（ログファイルを開く必要がない）
- **SC-007**: `execution.log` の内容がコンソール出力と完全に一致する（後から処理結果を確認可能）

## Assumptions

- `.staging/@plan/` ディレクトリは既に存在する（または作成可能）
- `normalizer/io/session.py` のコードを共通モジュールとして再利用可能
- 既存の `.extraction_state.json` との後方互換性は不要（新形式に移行）
