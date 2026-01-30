# Data Model: LLMインポート エラーデバッグ改善

## Entities

### ErrorDetail

エラー発生時の詳細情報を保持。

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | セッションID |
| conversation_id | str | 会話ID |
| conversation_title | str | 会話タイトル |
| timestamp | datetime | エラー発生時刻 |
| error_type | str | エラー種別（json_parse, no_json, timeout等） |
| error_message | str | エラーメッセージ |
| error_position | int | nullable | エラー位置（文字数） |
| error_context | str | nullable | エラー周辺のテキスト |
| original_content | str | 元の会話内容 |
| llm_prompt | str | LLMに送信したプロンプト |
| llm_output | str | nullable | LLMの生の出力 |
| stage | str | エラー発生段階（phase1, phase2） |

### Session

インポートセッションの情報。既存の SessionLogger を拡張。

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | セッションID（YYYYMMDD_HHMMSS形式） |
| session_type | str | セッション種別（import, organize, test） |
| provider | str | プロバイダー名（claude等） |
| start_time | datetime | 開始時刻 |
| end_time | datetime | nullable | 終了時刻 |
| total_files | int | 処理対象ファイル数 |
| processed_count | int | 処理完了数 |
| error_count | int | エラー数 |
| skipped_count | int | スキップ数 |

### CleanupPolicy

クリーンアップポリシー。CLI引数から構築。

| Field | Type | Description |
|-------|------|-------------|
| retention_days | int | 保持日数（デフォルト: 30） |
| preserve_errors | bool | エラー含むセッション保護（デフォルト: true） |
| target_types | list[str] | 対象種別（import, organize, test） |
| dry_run | bool | プレビューモード |

## Folder Structure

```
@plan/
├── import/
│   └── {session_id}/
│       ├── parsed/
│       │   └── conversations/
│       │       └── {title}.md          # Phase 1 output
│       ├── output/
│       │   └── {knowledge_file}.md     # Phase 2 output (pre-@index)
│       ├── errors/
│       │   └── {conversation_id}.md    # Error details
│       └── session.json                # Session metadata
├── organize/
│   └── {session_id}/
│       └── session.json
└── test/
    └── {session_id}/
        └── session.json
```

## File Formats

### session.json

```json
{
  "session_id": "20260117_150058",
  "session_type": "import",
  "provider": "claude",
  "start_time": "2026-01-17T15:00:58",
  "end_time": "2026-01-17T15:19:00",
  "total_files": 424,
  "processed": {
    "count": 401,
    "files": ["conv_id_1", "conv_id_2"]
  },
  "errors": {
    "count": 21,
    "files": ["conv_id_3", "conv_id_4"]
  },
  "skipped": {
    "count": 2,
    "files": ["conv_id_5"]
  }
}
```

### Error Detail File ({conversation_id}.md)

```markdown
# Error Detail: {conversation_title}

**Session**: {session_id}
**Conversation ID**: {conversation_id}
**Timestamp**: {timestamp}
**Error Type**: {error_type}
**Error Position**: {position}

## Error Message

{error_message}

## Original Content

\`\`\`text
{original_content}
\`\`\`

## LLM Prompt

\`\`\`text
{llm_prompt}
\`\`\`

## LLM Raw Output

\`\`\`text
{llm_raw_output}
\`\`\`

## Context

{context_around_error}
```

## State Transitions

### Session Lifecycle

```
CREATED → RUNNING → COMPLETED
                 ↘ FAILED (エラー終了)
```

### File Processing Flow

```
Source → Phase1 → Phase2 → @index
           ↓         ↓
        parsed/   output/
           ↓         ↓
        (保持)    (保持+コピー)
```

### Error Handling Flow

```
Phase2 Error → ErrorDetail作成 → errors/ に出力
            → StateManager に記録
            → 次のファイルへ継続
```
