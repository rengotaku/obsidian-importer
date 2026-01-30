# Data Model: Robust JSON Parsing

**Feature**: 005-robust-json-parse
**Date**: 2026-01-12

## Entities

### ParseResult

JSON抽出・パースの結果を表現。

| Field | Type | Description |
|-------|------|-------------|
| success | bool | パース成功かどうか |
| data | dict | パースされたJSONオブジェクト（成功時） |
| error | ParseError \| None | エラー情報（失敗時） |
| extraction_method | str | 抽出方法（"code_block" or "bracket_balance"） |

### ParseError

パースエラーの詳細情報。

| Field | Type | Description |
|-------|------|-------------|
| type | str | エラー種別（"no_json", "incomplete", "invalid", "decode_error"） |
| message | str | 人間可読なエラーメッセージ |
| position | int \| None | エラー発生位置（文字数） |
| context | str \| None | エラー周辺のテキスト（前後50文字） |

### ExtractionState

括弧バランス追跡の内部状態。

| Field | Type | Description |
|-------|------|-------------|
| depth | int | 現在の括弧ネスト深度 |
| in_string | bool | 文字列リテラル内かどうか |
| escape_next | bool | 次の文字がエスケープされているか |
| start_pos | int | JSONオブジェクトの開始位置 |

## State Transitions

### ExtractionState Transitions

```
Initial State: depth=0, in_string=False, escape_next=False

On '{' (not in_string):
  depth += 1
  if depth == 1: start_pos = current_pos

On '}' (not in_string):
  depth -= 1
  if depth == 0: EXTRACTION_COMPLETE → return text[start_pos:current_pos+1]

On '"' (not in_string, not escape_next):
  in_string = True

On '"' (in_string, not escape_next):
  in_string = False

On '\\' (in_string):
  escape_next = True

On any char (escape_next):
  escape_next = False
```

## Validation Rules

1. **Empty Response**: 空文字列または空白のみ → エラー
2. **No JSON**: `{` が見つからない → "JSON形式の応答がありません"
3. **Incomplete JSON**: depth > 0 のまま終了 → "不完全なJSONオブジェクト"
4. **Invalid JSON**: json.loads() 失敗 → JSONDecodeError詳細を返す
