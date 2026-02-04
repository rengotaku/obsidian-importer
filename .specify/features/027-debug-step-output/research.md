# Research: Transform Stage Debug Step Output

**Feature Branch**: `027-debug-step-output`
**Date**: 2026-01-20

## 調査結果

### 1. 既存の debug 出力機能

**現在の実装** (`src/etl/core/stage.py` 566-629行目):

```python
def _write_debug_output(self, ctx, item, error=None):
    debug_folder = ctx.output_path / "debug"
    debug_file = debug_folder / f"{safe_name}_{self.stage_type.value}.json"
    # JSON 形式で出力（indent=2）
```

**現在の問題点**:
- ファイル名が `{filename}_{stage_type}.json` で **step 情報を含まない**
- 各 step の処理後に同じファイルに上書きされる（最終状態のみ保存）
- JSON 形式で出力（JSONL 形式ではない）

**Decision**: 既存の `_write_debug_output` を拡張して step 毎の出力に対応

### 2. Step 識別方法

**現在の Step 構造** (`src/etl/core/stage.py`):
- `BaseStage.steps` プロパティで step リストを取得
- 各 step は `name` プロパティを持つ
- `_process_item` メソッド内で `for step in self.steps` でループ処理

**KnowledgeTransformer の Steps** (`src/etl/stages/transform/knowledge_transformer.py`):
1. `ExtractKnowledgeStep` - name: `extract_knowledge`

> **Note**: 現時点では step は1つのみ。翻訳・フォーマット処理は step として分離されていない。
> plan.md の例（step_002, step_003）は将来の拡張を想定した例示。
> 実装は現在の step 構造に従い、将来 step が追加された場合に自動対応する設計とする。

**Decision**: 既存の `step.name` を使用して step を識別

### 3. 出力ディレクトリ構造

**要件** (FR-005, FR-006):
- 各 step の出力は明確に識別可能
- セッション構造内に配置

**検討した選択肢**:

| Option | ディレクトリ構造 | メリット | デメリット |
|--------|----------------|---------|-----------|
| A | `debug/{step_name}/{filename}.jsonl` | step でグループ化 | 同じファイルの比較が困難 |
| B | `debug/{filename}/{step_name}.jsonl` | ファイルでグループ化 | step 間の比較が困難 |
| C | `debug/step_NNN_{step_name}/{filename}.jsonl` | 順序明確、step でグループ化 | ディレクトリ名が長い |

**Decision**: **Option C** を採用
- step の実行順序が明確（NNN: 001, 002, 003...）
- step 毎に比較しやすい
- SC-004（30秒以内に特定）を満たす

### 4. 出力フォーマット

**要件** (FR-008):
- JSONL 形式（1行1JSON、改行なし）

**現在の出力** (JSON with indent=2):
```json
{
  "timestamp": "...",
  "item_id": "...",
  ...
}
```

**新しい出力** (JSONL compact):
```jsonl
{"timestamp":"...","item_id":"...","source_path":"...","current_step":"extract_knowledge","status":"completed","metadata":{...}}
```

**Decision**: `json.dumps(data, ensure_ascii=False)` で改行なしのコンパクト形式を出力

### 5. StageContext への debug_mode アクセス

**現在の実装**:
- `StageContext.debug_mode` プロパティが存在
- `_process_item` 内で `if ctx.debug_mode:` でチェック済み

**Decision**: 既存の `ctx.debug_mode` を活用

### 6. Step インデックスの取得

**問題**: 現在の `_process_item` では step のインデックス情報がない

**解決策**: `enumerate(self.steps)` を使用して step インデックスを取得

```python
for step_index, step in enumerate(self.steps, start=1):
    # step_index: 1, 2, 3, ...
```

**Decision**: `enumerate` でインデックスを取得し、`step_{index:03d}_{step.name}` 形式でディレクトリ名を生成

### 7. 出力内容

**要件** (SC-002): step 間で流れるデータの 100% を含む

**出力フィールド**:
```python
{
    "timestamp": "ISO 8601 形式",
    "item_id": "処理アイテムID",
    "source_path": "元ファイルパス",
    "current_step": "step 名",
    "status": "completed/failed/skipped",
    "metadata": { ... },  # 全 metadata（knowledge_document 含む）
    "content": "元コンテンツ（全文）",
    "transformed_content": "変換後コンテンツ（全文）",
    "error": "エラーメッセージ（あれば）"
}
```

**Decision**: content_preview ではなく **全文を含める**（SC-002 対応）

### 8. パフォーマンス影響

**要件** (FR-007, SC-003): debug モード OFF 時は影響なし

**現在の実装**:
```python
if ctx.debug_mode:
    self._write_debug_output(ctx, current)
```

**Decision**: 既存の条件分岐を維持。debug_mode が False の場合は何も出力しない。

## 実装方針

### 変更ファイル

1. **`src/etl/core/stage.py`**:
   - `_write_debug_output` メソッドを `_write_debug_step_output` にリネーム
   - step インデックスと step 名を引数に追加
   - 出力パスを `debug/step_NNN_{step_name}/` に変更
   - JSONL 形式（コンパクト）で出力
   - content/transformed_content の全文を含める

2. **`src/etl/core/stage.py` (`_process_item` メソッド)**:
   - `enumerate(self.steps)` で step インデックスを取得
   - `_write_debug_step_output` に step インデックスを渡す

3. **`src/etl/tests/test_debug_step_output.py`** (新規):
   - debug モード ON/OFF のテスト
   - step 毎の出力ファイル検証
   - JSONL 形式の検証

### 互換性

- 既存の `_write_debug_output` 呼び出しは `_write_debug_step_output` に変更
- 出力フォルダ構造が変更されるため、既存の debug 出力との互換性はない（破壊的変更）
- ただし、debug 出力は開発者専用なので影響は軽微

## 結論

既存の `_write_debug_output` メソッドを拡張して、step 毎の JSONL 出力に対応する。
主な変更点：
1. 出力パス: `debug/{filename}_{stage}.json` → `debug/step_NNN_{step_name}/{filename}.jsonl`
2. フォーマット: JSON (pretty) → JSONL (compact)
3. 内容: preview → 全文
