# Quickstart: ChatGPTExtractor Steps分離リファクタリング

**Date**: 2026-01-24

## 概要

ChatGPTExtractor の `discover_items()` を軽量化し、処理を 4 つの Step に分離。BaseStage フレームワークに 1:N 展開サポートを追加。また、session.json に各フェーズの item 統計を記録。

## 変更サマリー

| ファイル | 変更内容 |
|----------|----------|
| `src/etl/core/stage.py` | `BaseStep.process()` 戻り値型を拡張、`_process_item()` で 1:N 対応 |
| `src/etl/core/session.py` | `Session.phases` を `dict[str, PhaseStats]` に変更、フェーズ統計記録 |
| `src/etl/stages/extract/chatgpt_extractor.py` | 4 Step に分離、`discover_items()` 軽量化 |
| `src/etl/cli.py` | フェーズ完了時に PhaseStats を session.json に記録 |
| `src/etl/tests/test_expanding_step.py` | 1:N 展開のユニットテスト（新規） |

## 使用方法

### 実行（変更なし）

```bash
# ChatGPT インポート（既存と同じ）
make import INPUT=chatgpt_export.zip PROVIDER=openai

# Debug モードで steps.jsonl を確認
make import INPUT=chatgpt_export.zip PROVIDER=openai DEBUG=1

# 特定アイテムのトレース
make item-trace SESSION=20260124_123456 ITEM=abc123
```

### steps.jsonl 出力例

Debug モードで生成される `extract/output/debug/steps.jsonl`:

```jsonl
{"timestamp":"2026-01-24T12:00:00Z","item_id":"zip_abc123","step":"read_zip","timing_ms":150,"before_chars":0,"after_chars":245000}
{"timestamp":"2026-01-24T12:00:01Z","item_id":"conv_uuid_1","step":"parse_conversations","timing_ms":50,"before_chars":245000,"after_chars":5000,"parent_item_id":"zip_abc123","expansion_index":0,"total_expanded":42}
{"timestamp":"2026-01-24T12:00:01Z","item_id":"conv_uuid_2","step":"parse_conversations","timing_ms":2,"before_chars":245000,"after_chars":8000,"parent_item_id":"zip_abc123","expansion_index":1,"total_expanded":42}
...
{"timestamp":"2026-01-24T12:00:02Z","item_id":"conv_uuid_1","step":"convert_format","timing_ms":10,"before_chars":5000,"after_chars":4500}
{"timestamp":"2026-01-24T12:00:02Z","item_id":"conv_uuid_1","step":"validate_min_messages","timing_ms":1,"before_chars":4500,"after_chars":4500}
```

### item-trace 出力例

```
$ make item-trace SESSION=20260124_123456 ITEM=conv_uuid_1

Item Trace: conv_uuid_1
Session: 20260124_123456

Step                      Phase     Stage     Before    After     Ratio     Time(ms)
─────────────────────────────────────────────────────────────────────────────────────
read_zip                  import    extract   0         245000    -         150
parse_conversations       import    extract   245000    5000      0.02      50
convert_format            import    extract   5000      4500      0.90      10
validate_min_messages     import    extract   4500      4500      1.00      1
extract_knowledge         import    transform 4500      1200      0.27      3500
generate_metadata         import    transform 1200      1500      1.25      100
write_markdown            import    load      1500      1500      1.00      5
```

### session.json 出力例

フェーズ完了後の `session.json`:

```json
{
  "session_id": "20260124_120000",
  "created_at": "2026-01-24T12:00:00",
  "status": "completed",
  "phases": {
    "import": {
      "status": "completed",
      "success_count": 42,
      "error_count": 3,
      "completed_at": "2026-01-24T12:05:30"
    }
  },
  "debug_mode": true
}
```

例外発生（クラッシュ）時:

```json
{
  "phases": {
    "import": {
      "status": "crashed",
      "success_count": 0,
      "error_count": 0,
      "completed_at": "2026-01-24T12:03:15",
      "error": "Unexpected error: Connection refused to Ollama API"
    }
  }
}
```

### debug 出力例 (Stage-level)

Debug モードで各 Stage の最終結果を JSONL 形式で出力:

**出力先**:
```
.staging/@session/20260124_120000/import/
├── extract/output/debug/
│   ├── test_extract.jsonl          # Extract Stage 最終結果
│   └── steps.jsonl                  # Step-level metrics
├── transform/output/debug/
│   ├── test_transform.jsonl        # Transform Stage 最終結果
│   └── steps.jsonl                  # Step-level metrics
└── load/output/debug/
    ├── test_load.jsonl              # Load Stage 最終結果
    └── steps.jsonl                  # Step-level metrics
```

**ファイル形式**: JSONL (1行1JSONオブジェクト、追記式)

**test_extract.jsonl の例**:
```jsonl
{"item_id":"conv_uuid_1","content":"[full content after all extract steps - ReadZip → Parse → Convert → Validate]"}
```

**test_transform.jsonl の例**:
```jsonl
{"item_id":"conv_uuid_1","content":"# Conversation Title\n\n## Summary\n...[full markdown after ExtractKnowledge → GenerateMetadata]"}
```

**test_load.jsonl の例**:
```jsonl
{"item_id":"conv_uuid_1","content":"---\ntitle: Conversation Title\nsummary: ...\n---\n\n# Conversation Title\n\n[final markdown with frontmatter]"}
```

**特徴**:
- 各 Stage の**最終ステップ後のみ**出力（中間ステップは出力しない）
- `content` はトランケートなし、フル出力
- 追記式のため、複数回実行した履歴が蓄積される
- `item_id` と `content` のみのシンプルな形式

**確認方法**:
```bash
# Extract Stage の最終結果を確認
cat .staging/@session/20260124_120000/import/extract/output/debug/test_extract.jsonl

# Transform Stage の最終結果を確認
cat .staging/@session/20260124_120000/import/transform/output/debug/test_transform.jsonl

# 複数アイテムの場合は jq で整形
cat debug/test_extract.jsonl | jq -r '.content' | head -100
```

## 開発者向け

### 新しい 1:N Step の作成

```python
from src.etl.core.stage import BaseStep
from src.etl.core.models import ProcessingItem

class MyExpandingStep(BaseStep):
    @property
    def name(self) -> str:
        return "my_expanding_step"

    def process(self, item: ProcessingItem) -> list[ProcessingItem]:
        # 1:N 展開: list を返す
        items_to_expand = parse_items(item.content)

        results = []
        for i, data in enumerate(items_to_expand):
            new_item = ProcessingItem(
                item_id=f"{item.item_id}_{i}",
                source_path=item.source_path,
                current_step=self.name,
                status=ItemStatus.PENDING,
                content=json.dumps(data),
                metadata={
                    **item.metadata,
                    "parent_item_id": item.item_id,
                    "expansion_index": i,
                    "total_expanded": len(items_to_expand),
                },
            )
            results.append(new_item)

        return results
```

### 1:1 Step は変更不要

既存の Step は単一の ProcessingItem を返し続けることで互換性維持:

```python
class MyRegularStep(BaseStep):
    def process(self, item: ProcessingItem) -> ProcessingItem:
        # 1:1 処理: 単一アイテムを返す（既存パターン）
        item.content = transform(item.content)
        return item
```

## テスト

```bash
# 全テスト実行
make test

# 1:N 展開テストのみ
python -m unittest src.etl.tests.test_expanding_step

# ChatGPT 統合テスト
python -m unittest src.etl.tests.test_chatgpt_transform_integration
```

## 互換性

- **入力**: 変更なし（ChatGPT エクスポート ZIP）
- **出力**: 変更なし（同一の Markdown ファイル生成）
- **API**: `ImportPhase.run()` インターフェース変更なし
- **既存 Step**: 変更不要（後方互換）
