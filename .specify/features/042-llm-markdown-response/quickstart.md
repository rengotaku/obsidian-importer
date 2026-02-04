# Quickstart: LLM レスポンス形式をマークダウンに変更

**Date**: 2026-01-30
**Feature**: 042-llm-markdown-response

## 変更概要

LLM への知識抽出リクエストのレスポンス形式を JSON → マークダウンに変更する。

### Before（現行）

```
LLM プロンプト: "JSON形式で出力してください"
    ↓
LLM レスポンス: {"title": "...", "summary": "...", "summary_content": "..."}
    ↓
parse_json_response(): JSON → dict
    ↓
KnowledgeExtractor: dict → KnowledgeDocument
```

### After（変更後）

```
LLM プロンプト: "マークダウン形式で出力してください"
    ↓
LLM レスポンス: # タイトル\n## 要約\n...\n## 内容\n...
    ↓
parse_markdown_response(): Markdown → dict
    ↓
KnowledgeExtractor: dict → KnowledgeDocument（変更なし）
```

## 変更対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/etl/prompts/knowledge_extraction.txt` | JSON 出力指示 → マークダウン出力指示 |
| `src/etl/prompts/summary_translation.txt` | JSON 出力指示 → マークダウン出力指示 |
| `src/etl/utils/ollama.py` | `parse_markdown_response()` 関数追加 |
| `src/etl/utils/knowledge_extractor.py` | `parse_json_response` → `parse_markdown_response` 呼び出し変更 |
| `src/etl/tests/test_ollama.py` | マークダウンパースのユニットテスト追加 |
| `src/etl/tests/test_knowledge_extractor.py` | マークダウンレスポンスに対応したテスト更新 |

## 動作確認手順

```bash
# 1. テスト実行
make test

# 2. 実際のインポート（少数で確認）
make import INPUT=<path> PROVIDER=claude LIMIT=3 DEBUG=1

# 3. 出力ファイルの品質確認（目視）
ls .staging/@session/*/import/load/output/conversations/
```
