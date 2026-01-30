# Data Model: Resume モードの再設計

## エンティティ一覧

### 1. ProcessingItem（既存・変更なし）

パイプラインを流れる処理単位。

```python
@dataclass
class ProcessingItem:
    item_id: str              # 一意識別子（UUID または ファイルパス）
    source_path: Path         # 元ファイルパス
    current_step: str         # 現在のステップ名
    status: ItemStatus        # PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED
    metadata: dict[str, Any]  # チャンク情報等
    content: str | None       # 抽出後のコンテンツ
    transformed_content: str | None  # 変換後のコンテンツ
    output_path: Path | None  # 出力先パス
    error: str | None         # エラーメッセージ
```

**チャンク関連 metadata キー**:
- `is_chunked: bool` - チャンク分割されたアイテムか
- `chunk_index: int` - チャンクインデックス（0-based）
- `total_chunks: int` - 総チャンク数
- `parent_item_id: str` - 分割元のアイテム ID
- `chunk_filename: str` - チャンクのファイル名

### 2. StageLogRecord（既存・変更なし）

`pipeline_stages.jsonl` の1レコード。

```python
@dataclass
class StageLogRecord:
    timestamp: str            # ISO8601 形式
    session_id: str           # セッション ID
    filename: str             # ソースファイル名
    stage: str                # "extract" / "transform" / "load"
    step: str                 # ステップ名
    timing_ms: int            # 処理時間（ミリ秒）
    status: str               # "success" / "failed" / "skipped"
    item_id: str | None       # アイテム ID
    file_id: str | None       # ファイルハッシュ
    skipped_reason: str | None  # スキップ理由
    before_chars: int | None  # 変換前文字数
    after_chars: int | None   # 変換後文字数
    diff_ratio: float | None  # 変化率
    is_chunked: bool | None   # チャンク分割フラグ
    parent_item_id: str | None  # 親アイテム ID
    chunk_index: int | None   # チャンクインデックス
    error_message: str | None # エラーメッセージ
```

### 3. CompletedItemsCache（新規）

処理完了アイテムのキャッシュ。Resume モードでスキップ判定に使用。

```python
@dataclass
class CompletedItemsCache:
    """処理完了アイテムのキャッシュ。

    pipeline_stages.jsonl から status="success" のアイテムを
    ステージ別に読み込み、スキップ判定に使用する。
    """

    items: set[str]
    """成功した item_id のセット。"""

    stage: StageType
    """対象ステージ。"""

    @classmethod
    def from_jsonl(cls, jsonl_path: Path, stage: StageType) -> "CompletedItemsCache":
        """pipeline_stages.jsonl から処理完了アイテムを読み込む。

        Args:
            jsonl_path: pipeline_stages.jsonl のパス
            stage: 対象ステージ（TRANSFORM または LOAD）

        Returns:
            CompletedItemsCache インスタンス
        """
        ...

    def is_completed(self, item_id: str) -> bool:
        """アイテムが処理完了済みか判定。"""
        return item_id in self.items

    def __len__(self) -> int:
        """完了アイテム数を返す。"""
        return len(self.items)
```

**フィールド定義**:

| フィールド | 型 | 説明 |
|----------|-----|------|
| `items` | `set[str]` | 成功した item_id のセット |
| `stage` | `StageType` | 対象ステージ（TRANSFORM / LOAD） |

**バリデーションルール**:
- `stage` は `TRANSFORM` または `LOAD` のみ（Extract は Stage 単位スキップ）
- JSONL 読み込みエラーは警告ログを出力し、空のキャッシュを返す

### 4. PhaseStatistics（既存・変更なし）

フェーズの統計情報。

```python
@dataclass
class PhaseStatistics:
    success_count: int     # 成功アイテム数
    error_count: int       # 失敗アイテム数
    skipped_count: int     # スキップアイテム数
    total_count: int       # 総アイテム数
```

**スキップ数の計算**:
- Resume モードでは `skipped_count = input_count - (success_count + error_count + newly_processed_count)`
- `pipeline_stages.jsonl` にはスキップアイテムは記録されない

### 5. StageContext（既存・修正）

ステージ実行コンテキスト。

```python
@dataclass
class StageContext:
    phase: Phase              # フェーズ情報
    stage: Stage              # ステージ情報
    debug_mode: bool          # [削除予定] DEBUG モード
    limit: int | None         # 処理件数制限
    chunk: bool               # チャンク分割有効
    # 追加
    completed_cache: CompletedItemsCache | None = None  # Resume 用キャッシュ
```

## リレーション

```
Session 1──* Phase 1──* Stage
                │
                └──* ProcessingItem
                        │
                        └── StageLogRecord (pipeline_stages.jsonl)
                                │
                                └── CompletedItemsCache (in-memory)
```

## 状態遷移

### ItemStatus

```
PENDING ──→ IN_PROGRESS ──→ COMPLETED
                │
                ├──→ FAILED
                │
                └──→ SKIPPED (Resume モード時のみ)
```

**注意**: Resume モードでスキップされたアイテムは `SKIPPED` ステータスにならない。
フレームワーク層でフィルタリングされ、Step には渡されないため、ステータス変更は発生しない。

### PhaseStatus

```
PENDING ──→ IN_PROGRESS ──→ COMPLETED (全件成功)
                │
                ├──→ PARTIAL (一部成功、一部失敗)
                │
                ├──→ FAILED (全件失敗)
                │
                └──→ CRASHED (予期しないエラー)
```

## データフロー

### 通常実行フロー

```
Input Files
    │
    ▼
Extract Stage
    │ ProcessingItem (item_id, content)
    ▼
Transform Stage
    │ ProcessingItem (transformed_content)
    ▼
Load Stage
    │ ProcessingItem (output_path)
    ▼
pipeline_stages.jsonl ← StageLogRecord (success/failed)
```

### Resume 実行フロー

```
pipeline_stages.jsonl
    │
    ▼
CompletedItemsCache.from_jsonl()
    │ set[item_id] (status="success" のみ)
    │
    ▼
Transform Stage
    │ if item_id in cache: skip
    │ else: process → StageLogRecord
    ▼
Load Stage
    │ if item_id in cache: skip
    │ else: process → StageLogRecord
    ▼
Console Output: "5 success, 2 failed, 3 skipped"
```

## JSONL フォーマット

### pipeline_stages.jsonl（変更なし）

```jsonl
{"timestamp":"2026-01-26T10:00:00+00:00","session_id":"20260126_100000","filename":"conv.json","stage":"transform","step":"extract_knowledge","timing_ms":5000,"status":"success","item_id":"abc-123","file_id":"sha256:...","before_chars":10000,"after_chars":3000,"diff_ratio":0.3}
{"timestamp":"2026-01-26T10:00:05+00:00","session_id":"20260126_100000","filename":"conv.json","stage":"load","step":"write_file","timing_ms":100,"status":"success","item_id":"abc-123","file_id":"sha256:..."}
```

**注意**: スキップされたアイテムは記録されない（FR-007）。

### error_details.jsonl（変更なし）

```jsonl
{"timestamp":"2026-01-26T10:00:00","session_id":"20260126_100000","item_id":"def-456","stage":"transform","step":"extract_knowledge","error_type":"JSONDecodeError","error_message":"...","backtrace":"...","metadata":{...}}
```
