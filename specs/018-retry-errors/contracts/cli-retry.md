# CLI Contract: --retry-errors

**Date**: 2026-01-17
**Feature**: 018-retry-errors

## 新規オプション

### --retry-errors

エラーファイルのリトライモードを有効にする。

```
--retry-errors
```

**動作**:
- `--session` 未指定時: エラーを含むセッション一覧を表示
- `--session` 指定時: 指定セッションのエラーをリトライ
- エラーセッションが1件のみ: 自動選択してリトライ

---

### --session SESSION_ID

リトライ対象のセッションを指定する。

```
--session <session_id>
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | セッション ID（例: `import_20260116_203426`） |

**Validation**:
- `.staging/@plan/{session_id}/` が存在すること
- `errors.json` が存在すること

**Error Cases**:
- セッションが見つからない: `ERROR: セッション '{session_id}' が見つかりません`
- errors.json がない: `ERROR: セッション '{session_id}' にエラーファイルがありません`

---

### --timeout SECONDS

Phase 2 処理のタイムアウト値を指定する。

```
--timeout <seconds>
```

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| seconds | integer | No | 120 | タイムアウト秒数 |

**Validation**:
- 正の整数であること
- 最大値: 600（10分）

---

## コマンド例

### セッション一覧表示

```bash
python -m scripts.llm_import.cli --provider claude --retry-errors
```

**Output**:
```
リトライ対象のセッション一覧:

  SESSION                      ERRORS  UPDATED
  import_20260116_203426       21      2026-01-17 00:37
  import_20260115_143210       5       2026-01-15 18:22

SESSION を指定して実行してください:
  python -m scripts.llm_import.cli --provider claude --retry-errors --session import_20260116_203426
```

---

### 指定セッションのリトライ

```bash
python -m scripts.llm_import.cli --provider claude --retry-errors --session import_20260116_203426
```

**Output**:
```
================================================================================
RETRY SESSION
================================================================================
Source Session: import_20260116_203426
Error Count: 21
Retry Started: 2026-01-17 12:00:00
================================================================================

[1/21] Processing fe26208b-dc85-48be-a01f-2e8fc98684b8...
  ✅ Success → @index/知識ノート.md
[2/21] Processing 74fda9a1-8db3-49c6-a107-5b143bd09492...
  ❌ Error: JSON形式の応答がありません
...

================================================================================
RETRY COMPLETE
================================================================================
Success: 18
Error: 3
Session: import_20260117_120000
================================================================================
```

---

### プレビューモード

```bash
python -m scripts.llm_import.cli --provider claude --retry-errors --session import_20260116_203426 --preview
```

**Output**:
```
リトライ対象のエラー一覧:

  FILE                                   ERROR                          TIMESTAMP
  fe26208b-dc85-48be-a01f-2e8fc98684b8   JSONパースエラー               2026-01-16 21:42
  74fda9a1-8db3-49c6-a107-5b143bd09492   JSON形式の応答がありません     2026-01-16 21:48
  ...

合計: 21 件

[プレビューモード] 実際の処理は行われません
```

---

## Exit Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | EXIT_SUCCESS | 正常終了（リトライ成功または一覧表示） |
| 1 | EXIT_ARGUMENT_ERROR | 引数エラー |
| 2 | EXIT_INPUT_NOT_FOUND | セッションまたはファイルが見つからない |
| 4 | EXIT_PARTIAL_ERROR | 一部のリトライが失敗 |
| 5 | EXIT_ALL_FAILED | すべてのリトライが失敗 |

---

## Makefile Integration

```makefile
# エラーリトライ
# SESSION=xxx, ACTION=preview, TIMEOUT=N
retry:
ifeq ($(ACTION),preview)
	@cd $(BASE_DIR)/development && $(PYTHON) -m scripts.llm_import.cli \
		--provider claude --retry-errors --preview \
		$(if $(SESSION),--session $(SESSION),)
else
	@cd $(BASE_DIR)/development && $(PYTHON) -m scripts.llm_import.cli \
		--provider claude --retry-errors \
		$(if $(SESSION),--session $(SESSION),) \
		$(if $(TIMEOUT),--timeout $(TIMEOUT),)
endif
```

### 使用例

```bash
# セッション一覧表示
make retry

# 指定セッションのリトライ
make retry SESSION=import_20260116_203426

# プレビュー
make retry ACTION=preview SESSION=import_20260116_203426

# タイムアウト指定
make retry SESSION=import_20260116_203426 TIMEOUT=180
```
