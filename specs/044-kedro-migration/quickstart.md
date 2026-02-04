# Quickstart: Kedro 移行

## Prerequisites

- Python 3.11+
- Ollama running locally (`http://localhost:11434`)
- `gemma3:12b` model pulled in Ollama

## Setup

```bash
# 1. Kedro プロジェクト生成
kedro new --name=obsidian-etl --tools=lint,test --example=n

# 2. 依存関係インストール
cd obsidian-etl
pip install kedro==1.1.1 kedro-datasets tenacity>=8.0 PyYAML>=6.0 requests>=2.28

# 3. 開発用依存関係
pip install kedro-viz  # DAG 可視化
```

## Usage

```bash
# Claude 会話インポート（デフォルト）
kedro run --pipeline=import_claude

# ChatGPT 会話インポート
kedro run --pipeline=import_openai

# GitHub Jekyll ブログインポート
kedro run --pipeline=import_github

# 入力パス指定（CLI パラメータ上書き）
kedro run --pipeline=import_claude --params='{"import.input_path": "/path/to/export"}'

# 処理件数制限
kedro run --pipeline=import_claude --params='{"import.limit": 10}'

# 特定ノードから実行（部分実行）
kedro run --pipeline=import_claude --from-nodes=extract_knowledge

# 特定ノードまで実行
kedro run --pipeline=import_claude --to-nodes=format_markdown

# DAG 可視化
kedro viz
```

## Resume (冪等再実行)

```bash
# 前回失敗した処理の再実行（同じコマンド）
kedro run --pipeline=import_claude

# PartitionedDataset の overwrite=false により:
# - 出力ファイルが存在するアイテム → スキップ
# - 出力ファイルが存在しないアイテム → 再処理
```

## Data Flow

```
data/01_raw/claude/*.json          ← 入力（Claude エクスポート）
    ↓ [extract_claude pipeline]
data/02_intermediate/parsed/*.json ← パース済みアイテム
    ↓ [transform pipeline]
data/03_primary/transformed/*.json ← LLM 処理済みアイテム
    ↓ [transform pipeline - format_markdown]
data/07_model_output/notes/*.md    ← 最終 Markdown
    ↓ [organize pipeline]
Vaults/エンジニア/*.md             ← Vault 配置
```

## Testing

```bash
# 全テスト実行
python -m unittest discover tests/

# 特定パイプラインのテスト
python -m unittest tests/pipelines/extract_claude/test_nodes.py

# ゴールデンデータテスト（ノード入出力比較）
python -m unittest tests/pipelines/transform/test_nodes.py
```

## Key Differences from Current Pipeline

| 項目 | 旧（src/etl/） | 新（src/obsidian_etl/） |
|------|---------------|----------------------|
| 実行 | `python -m src.etl import` | `kedro run --pipeline=import_claude` |
| Resume | `--session ID` | 再実行（冪等） |
| Retry | `make retry SESSION=...` | 再実行（冪等） |
| Status | `make status` | Kedro ログ + `kedro viz` |
| 設定 | コード内ハードコード | `conf/base/parameters.yml` |
| データ管理 | `.staging/@session/` | `data/` レイヤー（DataCatalog） |

## Node Reference

| Pipeline | Node | Input → Output |
|----------|------|----------------|
| extract_claude | parse_claude_json | raw_claude_conversations → parsed_items |
| extract_openai | parse_chatgpt_zip | raw_openai_conversations → parsed_items |
| extract_github | clone_and_parse | raw_github_posts → parsed_items |
| transform | extract_knowledge | parsed_items → knowledge_items |
| transform | generate_metadata | knowledge_items → metadata_items |
| transform | format_markdown | metadata_items → markdown_notes |
| organize | classify_and_place | markdown_notes → organized_items (+ Vault 配置) |
