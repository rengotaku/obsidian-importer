# CLI Interface Contract

**Feature**: 025-bonobo-tenacity-migration
**Date**: 2026-01-19

## Entry Point

```bash
python -m src.etl [COMMAND] [OPTIONS]
```

または Makefile 経由:

```bash
make etl-import    # import Phase 実行
make etl-organize  # organize Phase 実行
make etl-status    # セッション状態確認
```

---

## Commands

### `import` - Claude 会話インポート

```bash
python -m src.etl import --input PATH [OPTIONS]

Arguments:
  --input PATH       入力ディレクトリ（Claude エクスポート）【必須】

Options:
  --session ID       既存セッション ID を再利用
  --debug            詳細ログ出力を有効化
  --dry-run          処理をシミュレート（ファイル変更なし）
  --limit N          処理件数を制限

Exit Codes:
  0  成功
  1  引数エラー（--input 未指定含む）
  2  入力ディレクトリが存在しない
  3  Ollama 接続エラー
  4  部分エラー（一部成功）
  5  全件失敗
```

**例**:
```bash
# Claude エクスポートをインポート
python -m src.etl import --input ~/Downloads/claude-export

# デバッグモードで実行
python -m src.etl import --input ./data/export --debug

# 既存セッションを再開
python -m src.etl import --input ./data/export --session 20260119_143052

# ドライラン
python -m src.etl import --input ./data/export --dry-run --limit 5
```

---

### `organize` - ファイル整理

```bash
python -m src.etl organize --input PATH [OPTIONS]

Arguments:
  --input PATH       入力ディレクトリ（整理対象ファイル）【必須】

Options:
  --session ID       既存セッション ID を再利用
  --debug            詳細ログ出力を有効化
  --dry-run          処理をシミュレート（ファイル移動なし）
  --limit N          処理件数を制限

Exit Codes:
  0  成功
  1  引数エラー（--input 未指定含む）
  2  入力ディレクトリが存在しない
  3  Ollama 接続エラー
  4  部分エラー
  5  全件失敗
```

**例**:
```bash
# ディレクトリ内のファイルを整理
python -m src.etl organize --input ./data/to-organize

# 前回 import の出力を整理
python -m src.etl organize --input .staging/@session/20260119_143052/import/load/output

# ドライラン
python -m src.etl organize --input ./data/to-organize --dry-run
```

---

### `status` - セッション状態確認

```bash
python -m src.etl status [OPTIONS]

Options:
  --session ID       特定セッションの詳細を表示
  --all              全セッション一覧を表示
  --json             JSON 形式で出力

Exit Codes:
  0  成功
  1  セッションなし
```

**出力例**:
```
Session: 20260119_143052
Status: running
Debug: false

Phases:
  import:
    Status: completed
    Items: 10 success, 2 failed
    Duration: 45.2s

  organize:
    Status: running
    Current Stage: transform
    Items: 5 processing, 3 pending
```

---

### `retry` - エラーリトライ

```bash
python -m src.etl retry [OPTIONS]

Options:
  --session ID       対象セッション ID（必須）
  --phase TYPE       対象 Phase（import | organize）
  --debug            詳細ログ出力を有効化

Exit Codes:
  0  成功
  1  引数エラー
  2  対象セッションなし
  3  リトライ対象なし
  4  部分エラー
  5  全件失敗
```

---

### `clean` - 古いセッション削除

```bash
python -m src.etl clean [OPTIONS]

Options:
  --days N           N 日より古いセッションを削除（デフォルト: 7）
  --dry-run          削除対象を表示（削除なし）
  --force            確認なしで削除

Exit Codes:
  0  成功
  1  エラー
```

---

## Makefile Targets

```makefile
# ETL コマンド
etl-import:
	$(VENV_PYTHON) -m src.etl import $(ARGS)

etl-organize:
	$(VENV_PYTHON) -m src.etl organize $(ARGS)

etl-status:
	$(VENV_PYTHON) -m src.etl status $(ARGS)

etl-retry:
	$(VENV_PYTHON) -m src.etl retry $(ARGS)

etl-clean:
	$(VENV_PYTHON) -m src.etl clean $(ARGS)

# デバッグモード
etl-import-debug:
	$(VENV_PYTHON) -m src.etl import --debug

# エイリアス（後方互換）
llm-import: etl-import
organize: etl-organize
```

---

## Output Format

### 標準出力（human-readable）

```
[Session] 20260119_143052 created
[Phase] import started
[Stage] extract: 10 items found
  ✓ conversation_abc123
  ✓ conversation_def456
  ✗ conversation_ghi789 (parse error)
[Stage] transform: processing...
  ✓ conversation_abc123 → knowledge extracted
  ...
[Phase] import completed (8 success, 2 failed)
```

### JSON 出力（--json）

```json
{
  "session_id": "20260119_143052",
  "phase": "import",
  "status": "completed",
  "summary": {
    "total": 10,
    "success": 8,
    "failed": 2,
    "duration_seconds": 45.2
  },
  "errors": [
    {
      "item_id": "conversation_ghi789",
      "step": "extract",
      "error": "JSON parse error at line 42"
    }
  ]
}
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ETL_DEBUG` | デバッグモード | `false` |
| `ETL_SESSION_DIR` | セッションディレクトリ | `.staging/@session/` |
| `OLLAMA_HOST` | Ollama API ホスト | `http://localhost:11434` |
| `OLLAMA_TIMEOUT` | API タイムアウト（秒） | `120` |
