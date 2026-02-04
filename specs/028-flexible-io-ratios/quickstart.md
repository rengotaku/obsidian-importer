# Quickstart: 柔軟な入出力比率対応フレームワーク

**Date**: 2026-01-20
**Feature**: 028-flexible-io-ratios

## 概要

このドキュメントは、1:1 と 1:N 入出力比率に対応した ETL フレームワークの使い方を説明する。

## 基本的な使い方

### 1:1 処理（通常）

```bash
# 通常の import 実行
make import INPUT=~/.staging/@llm_exports/claude/

# debug モード（Step 毎のログ出力）
make import INPUT=... DEBUG=1
```

処理結果:
- 1 つの会話 JSON → 1 つの Markdown ファイル
- debug フォルダに Step 毎の JSONL ログ

### 1:N 処理（チャンク分割）

25000 文字を超える会話は自動的にチャンク分割される。

```bash
# 自動チャンク分割（設定不要）
make import INPUT=~/.staging/@llm_exports/claude/
```

処理結果:
- 1 つの大きな会話 JSON → 複数の Markdown ファイル
  - 例: `タイトル_001.md`, `タイトル_002.md`, `タイトル_003.md`
- 各チャンクは独立したファイルとして処理

## debug ログの確認

### Step 毎のログ

```bash
# debug モードで実行
make import INPUT=... DEBUG=1

# ログを確認
ls .staging/@session/YYYYMMDD_HHMMSS/import/transform/output/debug/
# step_001_extract_knowledge/
# step_002_generate_metadata/
# step_003_format_markdown/
# steps.jsonl
```

### pipeline_stages.jsonl

```bash
# 全アイテムの処理履歴を確認
cat .staging/@session/YYYYMMDD_HHMMSS/import/pipeline_stages.jsonl | jq '.'
```

チャンクアイテムの例:
```json
{
  "filename": "abc123_001.json",
  "is_chunked": true,
  "parent_item_id": "abc123",
  "chunk_index": 0
}
```

## 開発者向け: Stage の実装

### 1:1 処理の Stage（推奨パターン）

```python
class MyStage(BaseStage):
    """My custom stage."""

    @property
    def stage_type(self) -> StageType:
        return StageType.TRANSFORM

    @property
    def steps(self) -> list[BaseStep]:
        return [
            MyStep1(),
            MyStep2(),
        ]

    # run() はオーバーライドしない！（FR-006）
```

### Step の実装

```python
class MyStep(BaseStep):
    """My custom step."""

    @property
    def name(self) -> str:
        return "my_step"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        # 1:1 処理のみ
        item.transformed_content = transform(item.content)
        return item
```

### ❌ やってはいけないこと

```python
# BAD: run() をオーバーライドしない
class MyStage(BaseStage):
    def run(self, ctx, items):  # ← FR-006 違反
        # 独自のループ処理
        ...

# BAD: Step で複数アイテムを返さない
class MyStep(BaseStep):
    def process(self, item):
        return [item1, item2]  # ← BaseStep は 1:1 のみ
```

## チャンク分割の仕組み

1. **Phase.discover_items()** でチャンク判定
2. 25000 文字超 → `Chunker.split()` で分割
3. 各チャンクを個別の JSON ファイルとして `extract/input/` に配置
4. Extract/Transform/Load は全て 1:1 処理

```
conversations.json (50000 chars)
    ↓ discover_items() + Chunker
extract/input/
├── abc123_001.json (25000 chars)
└── abc123_002.json (25000 chars)
    ↓ Extract (1:1)
    ↓ Transform (1:1)
    ↓ Load (1:1)
load/output/
├── タイトル_001.md
└── タイトル_002.md
```

## トラブルシューティング

### debug ログが出力されない

```bash
# DEBUG=1 を指定しているか確認
make import INPUT=... DEBUG=1

# または直接実行
python -m src.etl import --input PATH --debug
```

### チャンク分割されない

```bash
# 閾値は 25000 文字
# 会話の総文字数を確認
python -c "
import json
with open('conversations.json') as f:
    data = json.load(f)
for conv in data:
    chars = sum(len(m.get('text', '')) for m in conv.get('chat_messages', []))
    print(f'{conv[\"uuid\"]}: {chars} chars')
"
```

### 元の会話を特定したい

```bash
# pipeline_stages.jsonl から parent_item_id を確認
jq 'select(.is_chunked == true) | {filename, parent_item_id, chunk_index}' \
  .staging/@session/*/import/pipeline_stages.jsonl
```
