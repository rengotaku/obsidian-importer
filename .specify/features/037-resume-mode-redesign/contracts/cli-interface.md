# CLI Interface Contract

## import コマンド

### 引数

```
python -m src.etl import [OPTIONS]
```

| 引数 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|----------|------|
| `--input` | Path/URL | 条件付き | - | 入力ファイル/ディレクトリ（Resume モード以外で必須） |
| `--provider` | string | No | "claude" | プロバイダー: "claude", "openai", "github" |
| `--session` | string | No | - | セッション ID（Resume モード） |
| `--limit` | int | No | None | 処理件数制限 |
| `--dry-run` | flag | No | False | プレビューモード |
| `--no-fetch-titles` | flag | No | False | URL タイトル取得無効化 |
| `--chunk` | flag | No | False | チャンク分割有効化 |

### 削除予定（deprecated）

| 引数 | 説明 |
|------|------|
| `--debug` | v2.0 で廃止。警告を出力し無視。 |
| `--no-debug` | v2.0 で廃止。警告を出力し無視。 |

### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 成功（全件処理完了） |
| 1 | 一般エラー |
| 2 | 入力ファイル/セッションが見つからない |
| 3 | Ollama 接続エラー |
| 4 | 部分成功（一部失敗） |
| 5 | 全件失敗 |

### 出力フォーマット

#### 標準出力

```
[Session] {session_id} {(reused|created)}
[Resume] Detected provider: {provider}  # Resume モード時のみ
[Phase] import started (provider: {provider})
[Phase] import completed ({success} success, {failed} failed[, {skipped} skipped])
```

#### 標準エラー出力

```
[Error] {error_message}
[Warning] {warning_message}
```

## status コマンド

### 引数

```
python -m src.etl status [OPTIONS]
```

| 引数 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|----------|------|
| `--session` | string | 条件付き | - | セッション ID |
| `--all` | flag | No | False | 全セッション表示 |
| `--json` | flag | No | False | JSON 形式で出力 |

### 出力フォーマット（テキスト）

```
Session: {session_id}
Status: {status}

Phase: import
  Success: {count}
  Failed: {count}
  Skipped: {count}
```

### 出力フォーマット（JSON）

```json
{
  "session_id": "20260126_100000",
  "status": "partial",
  "phases": {
    "import": {
      "status": "partial",
      "success_count": 50,
      "error_count": 5,
      "skipped_count": 0
    }
  }
}
```

## JSONL ログフォーマット

### pipeline_stages.jsonl

各行は以下の JSON オブジェクト:

```json
{
  "timestamp": "2026-01-26T10:00:00+00:00",
  "session_id": "20260126_100000",
  "filename": "conversation.json",
  "stage": "transform",
  "step": "extract_knowledge",
  "timing_ms": 5000,
  "status": "success",
  "item_id": "abc-123-def-456",
  "file_id": "sha256:...",
  "before_chars": 10000,
  "after_chars": 3000,
  "diff_ratio": 0.3,
  "is_chunked": false,
  "parent_item_id": null,
  "chunk_index": null,
  "error_message": null
}
```

| フィールド | 型 | 必須 | 説明 |
|----------|-----|------|------|
| `timestamp` | string | Yes | ISO8601 形式 |
| `session_id` | string | Yes | セッション ID |
| `filename` | string | Yes | ソースファイル名 |
| `stage` | string | Yes | "extract", "transform", "load" |
| `step` | string | Yes | ステップ名 |
| `timing_ms` | int | Yes | 処理時間（ミリ秒） |
| `status` | string | Yes | "success", "failed" |
| `item_id` | string | No | アイテム ID |
| `file_id` | string | No | ファイルハッシュ |
| `before_chars` | int | No | 変換前文字数 |
| `after_chars` | int | No | 変換後文字数 |
| `diff_ratio` | float | No | 変化率 |
| `is_chunked` | bool | No | チャンク分割フラグ |
| `parent_item_id` | string | No | 親アイテム ID |
| `chunk_index` | int | No | チャンクインデックス |
| `error_message` | string | No | エラーメッセージ |

**注意**: `status="skipped"` は Resume モードでは記録されない。
