# Data Model: Import Session Log

## Entities

### 1. Session

セッション情報を表す。`session.json` に保存。

| Field | Type | Description |
|-------|------|-------------|
| session_id | string | セッション識別子（ISO 8601 形式のタイムスタンプ） |
| started_at | string | 開始時刻（ISO 8601） |
| updated_at | string | 最終更新時刻（ISO 8601） |
| total_files | int | 処理対象の総会話数 |
| provider | string | プロバイダー名（例: "claude"） |

### 2. StageRecord

各処理ステージの記録。`pipeline_stages.jsonl` に追記。

| Field | Type | Description |
|-------|------|-------------|
| timestamp | string | 記録時刻（ISO 8601） |
| filename | string | 処理対象のファイル名/会話タイトル |
| stage | string | ステージ名: "phase1" \| "phase2" |
| executed | bool | 実行されたか |
| timing_ms | int | 処理時間（ミリ秒） |
| skipped_reason | string \| null | スキップ理由（実行された場合は null） |

### 3. ProcessedFile

処理済みファイル情報。`processed.json` に保存（リスト形式）。

| Field | Type | Description |
|-------|------|-------------|
| file | string | ファイル名/会話ID |
| status | string | "success" |
| output | string | 出力先パス |
| timestamp | string | 処理完了時刻（ISO 8601） |

### 4. ErrorFile

エラーファイル情報。`errors.json` に保存（リスト形式）。

| Field | Type | Description |
|-------|------|-------------|
| file | string | ファイル名/会話ID |
| error | string | エラーメッセージ |
| stage | string | エラー発生ステージ |
| timestamp | string | エラー発生時刻（ISO 8601） |

### 5. PendingFile

未処理ファイル情報。`pending.json` に保存（リスト形式）。

| Field | Type | Description |
|-------|------|-------------|
| file | string | ファイル名/会話ID |
| reason | string | 未処理理由（例: "phase2_limit"） |

### 6. Results

最終結果サマリー。`results.json` に保存。

| Field | Type | Description |
|-------|------|-------------|
| total | int | 処理対象総数 |
| success | int | 成功数 |
| error | int | エラー数 |
| skipped | int | スキップ数 |
| pending | int | 未処理数（Phase 2 制限等） |
| phase1_only | int | Phase 1 のみ完了数 |
| phase2_completed | int | Phase 2 完了数 |
| elapsed_seconds | float | 総処理時間（秒） |
| avg_time_per_conversation | float | 会話あたり平均処理時間（秒） |

## File Structure

```
.staging/@plan/import_YYYYMMDD_HHMMSS/
├── session.json          # Session エンティティ
├── execution.log         # 人間可読ログ（テキスト）
├── pipeline_stages.jsonl # StageRecord のストリーム
├── processed.json        # ProcessedFile のリスト
├── errors.json           # ErrorFile のリスト
├── pending.json          # PendingFile のリスト
└── results.json          # Results エンティティ
```

## State Transitions

```
会話の状態遷移:

[未処理] → [Phase 1 処理中] → [Phase 1 完了] → [Phase 2 処理中] → [Phase 2 完了]
                ↓                    ↓                  ↓
            [エラー]           [Phase 2 スキップ]    [エラー]
```

各状態での記録先:
- Phase 1 完了 + Phase 2 スキップ → `pending.json`
- Phase 2 完了 → `processed.json`
- エラー → `errors.json`
