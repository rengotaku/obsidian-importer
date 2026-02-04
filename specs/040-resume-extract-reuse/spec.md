# Feature Specification: Resume モード Extract Output 再利用

**Feature Branch**: `040-resume-extract-reuse`
**Created**: 2026-01-28
**Status**: Draft
**Input**: Resume モードで Extract stage の output（data-dump-*.jsonl）を再利用することで、重複ログを防止する。BasePhaseOrchestrator（Template Method パターン）で FW が制御フローを管理し、各 Phase は具体的な Stage 実行のみを実装する。Extract output は固定ファイル名（data-dump-{番号4桁}.jsonl）で 1000 レコードごとに分割する。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resume モードでの Extract 重複ログ防止 (Priority: P1)

ETL パイプラインを Resume モードで再実行する際、Extract stage の output が既に存在する場合は、input フォルダから再処理せずに output の JSONL ファイルから ProcessingItem を復元する。これにより、pipeline_stages.jsonl への Extract ログの重複記録を防止する。

**Why this priority**: 現在 Resume モードで Extract が重複実行され、ログが肥大化・重複している。これはトレーサビリティとデータ品質に直接影響する最優先の問題。

**Independent Test**: 既存セッションに対して Resume モードで再実行し、pipeline_stages.jsonl に Extract ログが追加されないことを確認できる。

**Acceptance Scenarios**:

1. **Given** Extract stage の output フォルダに data-dump-*.jsonl が存在する状態で、**When** Resume モードで import コマンドを実行した場合、**Then** Extract stage は input フォルダを処理せず、output の JSONL から ProcessingItem を復元する
2. **Given** Resume モードで Extract output から復元した場合、**When** pipeline_stages.jsonl を確認すると、**Then** 新しい Extract ログは追記されていない
3. **Given** Extract stage の output フォルダが空の状態で、**When** Resume モードで import コマンドを実行した場合、**Then** 標準出力に「Extract output not found, processing from input/」と表示され、通常通り input フォルダから処理される

---

### User Story 2 - FW による Resume 制御フローの一元管理 (Priority: P2)

BasePhaseOrchestrator クラス（Template Method パターン）が Resume ロジックを一元管理し、ImportPhase と OrganizePhase は具体的な Stage 実行のみを実装する。これにより、新規 Phase 作成時の Resume ロジック実装漏れを防止する。

**Why this priority**: 継承クラスごとに Resume ロジックを実装すると、実装漏れや不整合が発生する。FW レベルで制御することで一貫性を保証する。

**Independent Test**: ImportPhase と OrganizePhase の両方で Resume モードが正しく動作し、新規 Phase クラス作成時にフックメソッドのみの実装で Resume が自動的に機能することを確認できる。

**Acceptance Scenarios**:

1. **Given** BasePhaseOrchestrator を継承した Phase クラスが存在する状態で、**When** Resume モードで run() を呼び出した場合、**Then** FW（BasePhaseOrchestrator.run()）が Extract output の存在を確認し、適切に復元または通常処理を選択する
2. **Given** 新規 Phase クラスを作成する際、**When** _run_extract_stage()、_run_transform_stage()、_run_load_stage() のフックメソッドのみを実装した場合、**Then** Resume ロジックは FW が自動的に処理する
3. **Given** Resume モードで実行中、**When** Extract output から復元した場合、**Then** 標準出力に「Resume mode: Loading from extract/output/*.jsonl」と表示される

---

### User Story 3 - Extract Output の固定ファイル名とレコード分割 (Priority: P3)

Extract stage の output ファイル名を固定パターン（data-dump-{番号4桁}.jsonl）にし、1000 レコードごとに新規ファイルに分割する。これにより、Resume 時のファイル特定が容易になり、ファイル肥大化を防止する。

**Why this priority**: ファイル名が可変だと Resume 時の特定が困難。また、大きなファイルは読み込み効率が悪く、Git 管理でも差分が大きくなる。

**Independent Test**: Extract stage を実行し、output フォルダに data-dump-0001.jsonl、data-dump-0002.jsonl... の形式でファイルが生成され、各ファイルが最大 1000 レコードであることを確認できる。

**Acceptance Scenarios**:

1. **Given** Extract stage を実行する際、**When** ProcessingItem を output に書き込む場合、**Then** ファイル名は data-dump-0001.jsonl から始まる固定パターンになる
2. **Given** 1000 レコードを書き込んだ状態で、**When** 次の ProcessingItem を書き込む場合、**Then** 新規ファイル data-dump-0002.jsonl が作成され、そこに書き込まれる
3. **Given** Extract output フォルダに data-dump-*.jsonl が複数存在する状態で、**When** Resume モードで復元する場合、**Then** すべての data-dump-*.jsonl ファイルから ProcessingItem が読み込まれる

---

### Edge Cases

- Extract output フォルダに data-dump-*.jsonl 以外の JSONL ファイル（steps.jsonl、error_details.jsonl）が存在する場合、Resume 復元対象から除外される
- JSONL ファイル内に破損したレコード（不正な JSON）が存在する場合、そのレコードはスキップされ、処理は継続される
- Extract output の途中でプロセスが中断された場合、次回 Resume 時は既存の data-dump-*.jsonl から復元され、input からの再処理は行われない
- Transform/Load の completed_cache は従来通り pipeline_stages.jsonl から構築される

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: FW は BasePhaseOrchestrator クラスを提供し、Template Method パターンで run() メソッドを実装する
- **FR-002**: BasePhaseOrchestrator.run() は Extract output（data-dump-*.jsonl）の存在を確認し、存在する場合は JSONL から ProcessingItem を復元する
- **FR-003**: BasePhaseOrchestrator.run() は Extract output が存在しない場合、標準出力にメッセージを表示し、input フォルダから通常処理を行う
- **FR-004**: 各 Phase クラス（ImportPhase、OrganizePhase）は BasePhaseOrchestrator を継承し、フックメソッド（_run_extract_stage、_run_transform_stage、_run_load_stage）のみを実装する
- **FR-005**: BaseStage._write_output_item() は固定ファイル名パターン（data-dump-{番号4桁}.jsonl）で output を書き込む
- **FR-006**: BaseStage は 1000 レコードごとに新規ファイルに分割して書き込む
- **FR-007**: Resume 時の JSONL 読み込みは data-dump-*.jsonl パターンのみを対象とし、steps.jsonl 等を除外する
- **FR-008**: Resume モードで Extract output から復元した場合、pipeline_stages.jsonl に新しい Extract ログは追記されない

### Key Entities

- **BasePhaseOrchestrator**: Phase 実行の共通基底クラス。Template Method パターンで run() を実装し、Resume ロジックを FW レベルで管理する
- **ProcessingItem**: ETL パイプラインで処理されるアイテム。JSONL でシリアライズ・デシリアライズされる
- **Extract Output**: data-dump-{番号4桁}.jsonl 形式の JSONL ファイル。1000 レコードごとに分割される
- **CompletedItemsCache**: Transform/Load stage で Resume 時に使用される処理済みアイテムのキャッシュ

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Resume モードで Extract stage を再実行した際、pipeline_stages.jsonl への Extract ログ追記が 0 件である
- **SC-002**: 新規 Phase クラス作成時、フックメソッド 3 つ（_run_extract_stage、_run_transform_stage、_run_load_stage）の実装のみで Resume 機能が動作する
- **SC-003**: Extract output ファイルは 1 ファイルあたり最大 1000 レコードに分割される
- **SC-004**: ImportPhase と OrganizePhase の両方で Resume 機能が一貫して動作する
- **SC-005**: 既存のテストが全てパスし、Resume 機能の新規テストが追加される
