# Quickstart: ETL Import パリティ実装

**Generated**: 2026-01-19

## Prerequisites

1. Python 3.13+ インストール済み
2. Ollama ローカル稼働中（`ollama serve`）
3. 仮想環境アクティベート: `source src/converter/.venv/bin/activate`

## Quick Test

```bash
# テスト実行
make test

# 単体: import phase テスト
python -m unittest src.etl.tests.test_import_phase -v
```

## Usage

### 基本実行

```bash
# Claude エクスポートデータをインポート
make etl-import INPUT=~/.staging/@llm_exports/claude/

# プレビュー（実際の処理なし）
make etl-import INPUT=... DRY_RUN=1

# DEBUG モード（Step 毎出力）
make etl-import INPUT=... DEBUG=1

# 件数制限
make etl-import INPUT=... LIMIT=5
```

### 直接実行

```bash
python -m src.etl import --input ~/.staging/@llm_exports/claude/ --debug
```

## Output Structure

```
.staging/@session/20260119_143052/
├── session.json
└── import/
    ├── phase.json
    ├── pipeline_stages.jsonl      # 処理ログ
    ├── extract/
    │   ├── input/                 # DEBUG: 元入力
    │   └── step_*/                # DEBUG: Step 出力
    ├── transform/
    │   └── step_*/                # DEBUG: Step 出力
    ├── load/
    │   ├── output/                # 最終 Markdown
    │   └── errors/                # エラー詳細
    └── ...
```

## Key Files to Modify

| File | Purpose |
|------|---------|
| `src/etl/utils/` | [新規] converter からコピーしたユーティリティ |
| `src/etl/stages/transform/knowledge_transformer.py` | ExtractKnowledgeStep, GenerateMetadataStep |
| `src/etl/stages/load/session_loader.py` | WriteToSessionStep, UpdateIndexStep |
| `src/etl/core/stage.py` | BaseStage（JSONL 自動ログ追加） |

## Development Workflow

1. **スタブ実装確認**:
   ```bash
   grep -n "Stub" src/etl/stages/transform/knowledge_transformer.py
   ```

2. **utils モジュール import**:
   ```python
   # src/etl/stages/transform/knowledge_transformer.py
   from src.etl.utils.knowledge_extractor import KnowledgeExtractor, KnowledgeDocument
   from src.etl.utils.chunker import Chunker
   from src.etl.utils.file_id import generate_file_id
   ```

3. **テスト追加**:
   ```bash
   # 新規テストファイル
   touch src/etl/tests/test_knowledge_transformer.py
   ```

## Troubleshooting

### Ollama 接続エラー

```bash
# Ollama 稼働確認
curl http://localhost:11434/api/tags

# 再起動
ollama serve
```

### Import エラー

```bash
# PYTHONPATH 確認（プロジェクトルートが含まれていることを確認）
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### DEBUG 出力確認

```bash
# Step 出力を確認
ls -la .staging/@session/*/import/transform/step_*/
```
