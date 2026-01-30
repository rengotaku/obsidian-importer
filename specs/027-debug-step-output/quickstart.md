# Quickstart: Transform Stage Debug Step Output

**Feature Branch**: `027-debug-step-output`
**Date**: 2026-01-20

## 概要

Transform stage で debug モードを有効にすると、各 step の処理後に中間出力が JSONL 形式で保存されます。

## 使用方法

### 1. Debug モードで ETL を実行

```bash
# Makefile 経由
make etl-import INPUT=~/.staging/@llm_exports/claude/ DEBUG=1

# 直接実行
python -m src.etl import --input PATH --debug
```

### 2. Debug 出力を確認

```bash
# セッションフォルダを確認
ls -la .staging/@session/YYYYMMDD_HHMMSS/import/transform/debug/

# Step 毎の出力を確認
ls -la .staging/@session/YYYYMMDD_HHMMSS/import/transform/debug/step_001_extract_knowledge/

# 特定ファイルの内容を確認（JSONL 形式）
cat .staging/@session/YYYYMMDD_HHMMSS/import/transform/debug/step_001_extract_knowledge/conversation_001.jsonl | jq .
```

### 3. Step 間の差分を比較

```bash
# Step 1 と Step 2 の出力を比較
diff \
  <(cat debug/step_001_extract_knowledge/conversation_001.jsonl | jq .) \
  <(cat debug/step_002_translate_summary/conversation_001.jsonl | jq .)
```

## 出力例

### ディレクトリ構造

```
.staging/@session/20260120_120000/import/transform/
├── debug/
│   ├── step_001_extract_knowledge/
│   │   ├── conversation_001.jsonl
│   │   └── conversation_002.jsonl
│   ├── step_002_translate_summary/
│   │   ├── conversation_001.jsonl
│   │   └── conversation_002.jsonl
│   └── step_003_format_markdown/
│       ├── conversation_001.jsonl
│       └── conversation_002.jsonl
└── output/
    └── ...
```

### JSONL ファイル内容

```jsonl
{"timestamp":"2026-01-20T12:00:00Z","item_id":"conversation_001","source_path":"/home/user/.staging/@llm_exports/claude/conversations/abc123.json","current_step":"extract_knowledge","step_index":1,"status":"completed","metadata":{"source_type":"conversation","conversation_id":"abc123","knowledge_extracted":true,"knowledge_document":{"title":"キッザニアでの仕事体験","summary":"キッザニアの仕事体験について"}},"content":"{\"id\":\"abc123\",...}","transformed_content":null,"error":null}
```

### jq で整形して確認

```bash
cat conversation_001.jsonl | jq .
```

```json
{
  "timestamp": "2026-01-20T12:00:00Z",
  "item_id": "conversation_001",
  "source_path": "/home/user/.staging/@llm_exports/claude/conversations/abc123.json",
  "current_step": "extract_knowledge",
  "step_index": 1,
  "status": "completed",
  "metadata": {
    "source_type": "conversation",
    "conversation_id": "abc123",
    "knowledge_extracted": true,
    "knowledge_document": {
      "title": "キッザニアでの仕事体験",
      "summary": "キッザニアの仕事体験について"
    }
  },
  "content": "{\"id\":\"abc123\",...}",
  "transformed_content": null,
  "error": null
}
```

## デバッグシナリオ

### シナリオ 1: LLM 抽出結果の確認

```bash
# Step 1 (extract_knowledge) の出力から knowledge_document を抽出
cat debug/step_001_extract_knowledge/conversation_001.jsonl | jq '.metadata.knowledge_document'
```

### シナリオ 2: 翻訳結果の確認

```bash
# Step 2 (translate_summary) 後の summary を確認
cat debug/step_002_translate_summary/conversation_001.jsonl | jq '.metadata.knowledge_document.summary'
```

### シナリオ 3: エラー発生箇所の特定

```bash
# 失敗した item を検索
grep '"status":"failed"' debug/step_*/conversation_001.jsonl

# エラーメッセージを確認
cat debug/step_001_extract_knowledge/conversation_001.jsonl | jq 'select(.status == "failed") | .error'
```

## 注意事項

- Debug 出力は **debug モード有効時のみ** 生成されます
- Debug 出力には **全コンテンツ** が含まれるため、ファイルサイズが大きくなる可能性があります
- 本番運用時は debug モードを **無効** にしてください（パフォーマンスへの影響を避けるため）
