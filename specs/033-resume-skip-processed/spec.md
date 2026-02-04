# Feature Specification: Resume モードでの処理済みアイテムスキップ機能

**Feature Branch**: `033-resume-skip-processed`
**Created**: 2026-01-24
**Status**: Draft
**Input**: User description: "Resume モードで既存の処理済みアイテムをスキップする機能を追加"

## 背景と目的

### 現状の問題

現在の Resume モード（`--session` オプション）には以下の問題がある：

1. **Transform Stage で処理済みアイテムの検出がない**
   - 既に `knowledge_extracted: true` のアイテムでも、毎回 LLM（Ollama）を再呼び出し
   - 1アイテムあたり 30〜90 秒の処理時間が無駄に消費される
   - 1,000 件の Resume で数十時間の再処理が発生

2. **入力ファイルの上書きコピー**
   - Resume 時も毎回 ZIP/JSON ファイルを `extract/input` に上書きコピー
   - セッションの入力状態が毎回リセットされる

3. **スキップ状態の不明確さ**
   - ログに `status: "skipped"` と記録されるが、実際には処理が実行されている
   - 開発者が Resume の進行状況を正確に把握できない

### 目的

Resume モードを効率化し、以下を実現する：

1. **処理時間の大幅削減**: 処理済みアイテムをスキップすることで、Resume 実行時間を最小化
2. **リソースの節約**: 不要な LLM 呼び出しを回避し、計算コストを削減
3. **状態の明確化**: 何がスキップされ、何が新規処理されたかを明確にログ出力

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 中断されたインポートの高速再開 (Priority: P1)

ユーザーが大量の会話（1,000件以上）をインポート中にプロセスが中断された場合、Resume モードで続きから処理を再開でき、既に完了したアイテムは瞬時にスキップされる。

**Why this priority**: これが本機能の主目的。処理済みアイテムを再処理しないことで、Resume 時間を数十時間から数分に短縮する。

**Independent Test**: 500 件処理済みのセッションで Resume を実行し、処理済みアイテムのスキップ時間が 1 秒未満であることを確認。

**Acceptance Scenarios**:

1. **Given** 500 件中 300 件処理済みのセッション, **When** Resume モードで実行, **Then** 処理済み 300 件は LLM 呼び出しなしで即座にスキップされ、残り 200 件のみ処理される
2. **Given** 処理済みアイテム, **When** Resume でスキップされた場合, **Then** ログに `status: "skipped"`, `skipped_reason: "already_processed"`, `timing_ms: <10` と記録される

---

### User Story 2 - 入力ファイルの保持 (Priority: P1)

Resume モードで実行した際、前回のセッションの入力ファイルがそのまま保持され、不要な上書きコピーが発生しない。

**Why this priority**: 入力ファイルの上書きは Resume の基本的な前提を破壊する問題であり、修正が必須。

**Independent Test**: Resume 実行前後で `extract/input/` 内のファイルのタイムスタンプが変化しないことを確認。

**Acceptance Scenarios**:

1. **Given** 既存のセッション（extract/input に ZIP ファイルあり）, **When** Resume モードで `--session` を指定して実行, **Then** ZIP ファイルは上書きコピーされず、既存ファイルが使用される
2. **Given** 新規セッション（`--session` 未指定）, **When** インポートを実行, **Then** 入力ファイルは通常通り `extract/input/` にコピーされる

---

### User Story 3 - 処理状態の明確なログ出力 (Priority: P2)

開発者が Resume 実行時の進行状況を確認でき、何件がスキップされ、何件が新規処理されたかを把握できる。

**Why this priority**: デバッグと進行状況の可視化に寄与するが、コア機能には直接影響しない。

**Independent Test**: Resume 実行後のログとフェーズ完了メッセージを確認し、スキップ数と処理数が正確に報告されることを確認。

**Acceptance Scenarios**:

1. **Given** Resume モードでの実行完了, **When** コンソール出力を確認, **Then** `[Phase] import completed (100 success, 0 failed, 500 skipped)` のように、スキップ数が報告される
2. **Given** debug モードでの Resume 実行, **When** `steps.jsonl` を確認, **Then** スキップされたアイテムは `skipped_reason: "already_processed"` で記録される

---

### User Story 4 - セッション統計の正確な記録 (Priority: P2)

Resume 実行後の `session.json` に、スキップ数を含む正確な処理統計が記録される。

**Why this priority**: 運用監視と履歴管理に役立つが、機能の動作には直接影響しない。

**Independent Test**: Resume 完了後の `session.json` を確認し、`skipped_count` フィールドが追加されていることを確認。

**Acceptance Scenarios**:

1. **Given** Resume モードでの実行完了, **When** `session.json` を確認, **Then** `phases.import` に `success_count`, `error_count`, `skipped_count` が記録される
2. **Given** 全アイテムがスキップされた Resume, **When** `session.json` を確認, **Then** `status: "completed"`, `success_count: 0`, `skipped_count: N` と記録される

---

### Edge Cases

- **セッションが存在しない場合**: エラーメッセージを出力し、終了コード 2 で終了
- **処理済み判定と内容変更の競合**: 同じ `item_id` でもコンテンツが変更された場合は再処理する（コンテンツハッシュで判定）
- **部分的に処理済みのアイテム**: Transform は完了したが Load が未完了の場合、Load のみ再実行
- **debug モードの有無による差異**: debug モードの有無に関わらず、スキップ判定は同一のロジックで動作
- **空のセッション（処理済みアイテムなし）での Resume**: 全アイテムを新規処理として扱う

---

## Functional Requirements *(mandatory)*

### FR1: Transform Stage での処理済み検出

- Transform Stage の各ステップ（特に `extract_knowledge`）は、処理前に以下を確認する：
  - `item.metadata` に `knowledge_extracted: true` が設定されているか
  - `item.metadata` に有効な `knowledge_document` が存在するか
- 上記条件を満たす場合、LLM 呼び出しをスキップし、既存のメタデータをそのまま使用する
- スキップ時は `item.status = SKIPPED`, `item.metadata["skipped_reason"] = "already_processed"` を設定

### FR2: Load Stage での処理済み検出

- Load Stage は、出力先に同じ `item_id` のファイルが既に存在する場合、書き込みをスキップする
- ただし、コンテンツが変更されている場合（ハッシュ不一致）は上書きを実行
- スキップ時は `skipped_reason: "file_exists"` を記録

### FR3: Resume モードでの入力ファイル保持

- `--session` オプションが指定された場合、`cli.py` は入力ファイルのコピー処理をスキップする
- 既存の `extract/input/` 内のファイルをそのまま使用する
- 入力ファイルが存在しない場合のみ、新たにコピーを実行

### FR4: スキップ数のログ出力

- フェーズ完了時のコンソール出力に、スキップ数を含める
- 形式: `[Phase] import completed (N success, M failed, K skipped)`

### FR5: session.json への skipped_count 追加

- `session.json` の各フェーズ統計に `skipped_count` フィールドを追加
- 既存の `success_count`, `error_count` と同列で記録

### FR6: steps.jsonl への skipped_reason 記録

- スキップされたアイテムは `steps.jsonl` に以下の情報を記録：
  - `status: "skipped"`
  - `skipped_reason: "already_processed"` または `"file_exists"`
  - `timing_ms: <10`（瞬時スキップであることを示す）

---

## Success Criteria *(mandatory)*

### 定量的指標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| 処理済みアイテムのスキップ時間 | 1 アイテムあたり 10ms 未満 | `steps.jsonl` の `timing_ms` を確認 |
| Resume での全体処理時間削減率 | 処理済みアイテム数に比例して削減 | 500 件処理済み/1000 件全体 で 50% 以上の時間削減 |
| 入力ファイルの上書きなし | Resume 時は 0 回 | `extract/input/` のタイムスタンプ監視 |

### 定性的指標

| 指標 | 達成条件 |
|------|----------|
| ログの明確性 | スキップ理由が `steps.jsonl` とコンソールに記録される |
| 後方互換性 | 新規セッション（`--session` 未指定）での動作が変更前と同一 |
| 状態の一貫性 | `session.json` の統計とコンソール出力が一致 |

---

## Key Entities

### ProcessingItem.metadata の拡張

| フィールド | 型 | 説明 |
|----------|-----|------|
| `knowledge_extracted` | boolean | 知識抽出が完了したかどうか |
| `knowledge_document` | object | 抽出された知識ドキュメント |
| `skipped_reason` | string | スキップ理由（`already_processed`, `file_exists`） |

### session.json PhaseStats の拡張

| フィールド | 型 | 説明 |
|----------|-----|------|
| `skipped_count` | int | スキップされたアイテム数（新規追加） |

---

## Assumptions

- 処理済みの判定基準は `knowledge_extracted: true` の存在のみで十分（コンテンツハッシュの再計算は不要）
- Transform Stage のメタデータは、前回の実行結果がそのまま残っている（セッションフォルダ内のファイルが削除されていない）
- Load Stage の重複検出は既存の `item_id` ベースの仕組みを拡張する
- debug モードとの組み合わせは、スキップ時も `steps.jsonl` に記録する

---

## Dependencies

- 032-extract-step-refactor: session.json の PhaseStats 形式（本仕様で `skipped_count` を追加）
- 既存の `item_id` 生成ロジック（`generate_file_id()`）
- 既存の `SessionManager`, `PhaseManager` クラス

---

## Out of Scope

- Extract Stage でのスキップ（ZIP の再パースは毎回実行、ただし高速なため問題なし）
- 複数セッション間でのアイテム共有・重複検出
- 並列処理による Resume 高速化
- GUI/Web UI での進行状況表示
