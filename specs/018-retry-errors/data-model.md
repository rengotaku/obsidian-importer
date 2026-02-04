# Data Model: エラーファイルのリトライ機能

**Date**: 2026-01-17
**Feature**: 018-retry-errors

## Entities

### ErrorEntry

エラー情報を保持するエンティティ。既存の errors.json の構造を継承。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| file | string | 会話 ID（UUID） | 必須、UUID 形式 |
| error | string | エラーメッセージ | 必須 |
| stage | string | エラー発生ステージ | "phase1" または "phase2" |
| timestamp | string | ISO 8601 形式の日時 | 必須 |

**Example**:
```json
{
  "file": "fe26208b-dc85-48be-a01f-2e8fc98684b8",
  "error": "JSONパースエラー: Invalid \\escape (位置 1166)",
  "stage": "phase2",
  "timestamp": "2026-01-16T21:42:18"
}
```

---

### Session

インポートセッションのメタデータ。リトライセッションには `source_session` が追加される。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| session_id | string | セッション ID（ディレクトリ名） | 必須、`import_YYYYMMDD_HHMMSS` 形式 |
| started_at | string | 開始日時 | 必須、ISO 8601 |
| updated_at | string | 更新日時 | 必須、ISO 8601 |
| total_files | integer | 処理対象ファイル数 | 必須、>= 0 |
| provider | string | プロバイダー名 | 必須、"claude" など |
| source_session | string? | リトライ元セッション ID | オプショナル（リトライ時のみ） |

**通常セッション**:
```json
{
  "session_id": "import_20260116_203426",
  "started_at": "2026-01-16T20:34:26",
  "updated_at": "2026-01-17T00:37:01",
  "total_files": 422,
  "provider": "claude"
}
```

**リトライセッション**:
```json
{
  "session_id": "import_20260117_120000",
  "started_at": "2026-01-17T12:00:00",
  "updated_at": "2026-01-17T12:30:00",
  "total_files": 21,
  "provider": "claude",
  "source_session": "import_20260116_203426"
}
```

---

### ProcessedEntry

処理済みファイル情報。既存の processed.json の構造を継承。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| file | string | 会話 ID | 必須 |
| status | string | 処理ステータス | "success" または "error" |
| output | string | 出力ファイルパス | 成功時は必須 |
| timestamp | string | 処理完了日時 | 必須、ISO 8601 |

---

### SessionInfo（リトライ用）

セッション一覧表示用の情報を保持する内部エンティティ。

| Field | Type | Description |
|-------|------|-------------|
| session_id | string | セッション ID |
| error_count | integer | エラー件数 |
| updated_at | string | 最終更新日時 |
| source_session | string? | リトライ元（あれば） |

---

## State Transitions

### セッションのライフサイクル

```
[新規インポート]
    |
    v
import_YYYYMMDD_HHMMSS/
    ├── session.json (provider, total_files)
    ├── errors.json (エラーがあれば)
    └── processed.json
    |
    | (エラーあり & make retry)
    v
[リトライセッション]
    |
    v
import_YYYYMMDD_HHMMSS/
    ├── session.json (provider, total_files, source_session)
    ├── errors.json (リトライでも失敗したもの)
    └── processed.json (リトライで成功したもの)
```

### エラーエントリの状態遷移

```
[元セッション]
errors.json: [A, B, C]  (3件のエラー)
    |
    | make retry
    v
[リトライセッション]
processed.json: [A, B]  (2件成功)
errors.json: [C]        (1件失敗)

※ 元セッションの errors.json は変更されない
```

---

## Relationships

```
Session (source_session) -----> Session (session_id)
    |                              |
    |                              |
    v                              v
ErrorEntry[]                   ProcessedEntry[]
ErrorEntry[]
```

- 1つの Session は 0..* の ErrorEntry を持つ
- 1つの Session は 0..* の ProcessedEntry を持つ
- リトライ Session は 1 つの元 Session を参照する（source_session）
