# Data Model: Transform Stage Debug Step Output

**Feature Branch**: `027-debug-step-output`
**Date**: 2026-01-20

## エンティティ

### 1. DebugStepOutput

step 処理後の中間状態を表すデータ構造。

| フィールド | 型 | 必須 | 説明 |
|-----------|----|----|------|
| timestamp | string (ISO 8601) | ✅ | 出力時刻 |
| item_id | string | ✅ | 処理アイテムID |
| source_path | string | ✅ | 元ファイルパス |
| current_step | string | ✅ | 現在の step 名 |
| step_index | integer | ✅ | step の順番（1始まり） |
| status | string | ✅ | 処理状態（completed/failed/skipped） |
| metadata | object | ✅ | 処理メタデータ（knowledge_document 含む） |
| content | string | ⬜ | 元コンテンツ（全文） |
| transformed_content | string | ⬜ | 変換後コンテンツ（全文） |
| error | string | ⬜ | エラーメッセージ |

**JSONL 出力例**:
```jsonl
{"timestamp":"2026-01-20T12:00:00Z","item_id":"conversation_001","source_path":"/path/to/input.json","current_step":"extract_knowledge","step_index":1,"status":"completed","metadata":{"knowledge_extracted":true,"knowledge_document":{"title":"タイトル","summary":"要約"}},"content":"{...}","transformed_content":null,"error":null}
```

### 2. ProcessingItem（既存）

ETL パイプラインで処理されるアイテム。DebugStepOutput の元データ。

| フィールド | 型 | 説明 |
|-----------|----|----|
| item_id | string | 一意識別子 |
| source_path | Path | 元ファイルパス |
| current_step | string | 現在の step 名 |
| status | ItemStatus | 処理状態 |
| metadata | dict | メタデータ |
| content | string | 元コンテンツ |
| transformed_content | string | 変換後コンテンツ |
| error | string | エラーメッセージ |

### 3. StageContext（既存）

Stage 実行時のコンテキスト。debug_mode フラグを含む。

| フィールド | 型 | 説明 |
|-----------|----|----|
| phase | Phase | 親 Phase |
| output_path | Path | 出力パス |
| debug_mode | bool | debug モードフラグ |

## ディレクトリ構造

### Debug 出力パス

```
{session}/import/transform/debug/
├── step_001_extract_knowledge/
│   ├── conversation_001.jsonl
│   ├── conversation_002.jsonl
│   └── ...
├── step_002_translate_summary/
│   ├── conversation_001.jsonl
│   └── ...
└── step_003_format_markdown/
    ├── conversation_001.jsonl
    └── ...
```

### ファイル命名規則

| 要素 | 形式 | 例 |
|------|-----|-----|
| Step ディレクトリ | `step_{NNN}_{step_name}` | `step_001_extract_knowledge` |
| 出力ファイル | `{item_id}.jsonl` | `conversation_001.jsonl` |

## 状態遷移

### ProcessingItem.status

```
PENDING → IN_PROGRESS → COMPLETED
                      → FAILED
                      → SKIPPED
```

### Debug 出力タイミング

```
for each item:
    for step_index, step in enumerate(steps):
        process(item)
        if debug_mode:
            write_debug_step_output(item, step_index, step.name)
```

## バリデーションルール

### DebugStepOutput

1. `timestamp` は有効な ISO 8601 形式
2. `item_id` は非空文字列
3. `status` は "completed", "failed", "skipped" のいずれか
4. `step_index` は 1 以上の整数
5. JSONL 形式（1行1JSON、改行なし）

### ディレクトリ名

1. `step_NNN` の NNN は 3桁ゼロ埋め（001, 002, ...）
2. `step_name` は英数字とアンダースコアのみ
3. ファイル名に使用できない文字（`/`, `\`, `:` 等）はアンダースコアに置換
