# Extract Stage Design Patterns

本ドキュメントは Extract Stage の Extractor 実装パターンを定義し、新しいデータソース（GitHub、Slack 等）を追加する際の参考として提供する。

## Table of Contents

- [設計原則](#設計原則)
- [推奨パターン: Steps First](#推奨パターン-steps-first)
- [実装テンプレート](#実装テンプレート)
- [既存 Extractor 比較](#既存-extractor-比較)
- [1:N 展開パターン](#1n-展開パターン)
- [ベストプラクティス](#ベストプラクティス)

## 設計原則

Extract Stage の Extractor は BaseStage を継承し、以下の責務を持つ:

1. **discover_items()**: 入力ファイル/データソースの発見
2. **steps プロパティ**: 処理を段階的に実行する Step クラスのリスト

### Extractor の役割

| 責務 | 説明 |
|------|------|
| **File Discovery** | 入力ファイル（JSON, ZIP 等）を見つける |
| **Item Initialization** | ProcessingItem を初期化し、メタデータを設定 |
| **Processing Delegation** | 実際の処理は Steps に委譲 |
| **Logging** | BaseStage フレームワークにより steps.jsonl が自動生成される |

## 推奨パターン: Steps First

新しい Extractor を追加する際は、**"Steps First"** パターンを推奨する。

### 特徴

- **discover_items()**: ファイル発見のみ（軽量、content=None）
- **steps**: すべての処理を Steps に分離（読み込み、パース、変換、検証）
- **利点**: steps.jsonl で全処理を可視化、パフォーマンス分析が容易

### 設計図

```
┌──────────────────────────────────────────────────────┐
│ Extractor                                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│ discover_items()                                     │
│   ├─ Find input files                               │
│   └─ Yield ProcessingItem(content=None)             │
│                                                      │
│ steps                                                │
│   ├─ Step 1: Read File      (1:1)                   │
│   ├─ Step 2: Parse Data     (1:N or 1:1)            │
│   ├─ Step 3: Convert Format (1:1)                   │
│   └─ Step 4: Validate       (1:1)                   │
│                                                      │
└──────────────────────────────────────────────────────┘

BaseStage framework automatically:
  - Executes each Step in order
  - Logs to steps.jsonl (timing_ms, diff_ratio, metadata)
  - Handles 1:N expansion (if Step returns list[ProcessingItem])
```

### 利点

| 項目 | 説明 |
|------|------|
| **可視化** | steps.jsonl で全処理ステップを追跡可能 |
| **デバッグ** | ステップ単位でエラー箇所を特定可能 |
| **パフォーマンス分析** | 各ステップの timing_ms、diff_ratio を測定 |
| **フレームワーク活用** | BaseStage/BaseStep の設計思想に沿う |
| **拡張性** | 新しいステップ追加が容易 |

### 欠点

| 項目 | 説明 |
|------|------|
| **複雑性** | Step クラスが増える（通常 3-5 個） |

## 実装テンプレート

新しい Extractor を追加する際の実装テンプレート。

### 1. Step クラスの定義

各 Step は BaseStep を継承し、process() メソッドで ProcessingItem を変換する。

```python
from src.etl.core.stage import BaseStep
from src.etl.core.models import ProcessingItem

class ReadFileStep(BaseStep):
    """Read input file and populate content.

    1:1 Step - Reads file and sets content.
    """

    @property
    def name(self) -> str:
        return "read_file"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Read file from item.source_path and set content.

        Args:
            item: Item with source_path, content=None.

        Returns:
            Item with content set to file contents.
        """
        with open(item.source_path, "r", encoding="utf-8") as f:
            data = f.read()

        item.content = data
        item.metadata["file_size"] = len(data)

        return item

    def validate_input(self, item: ProcessingItem) -> bool:
        """Validate input has source_path."""
        return item.source_path is not None


class ParseDataStep(BaseStep):
    """Parse file content and expand to individual items.

    1:N Step - Parses JSON array and creates one item per element.
    """

    @property
    def name(self) -> str:
        return "parse_data"

    def process(self, item: ProcessingItem) -> list[ProcessingItem]:
        """Parse JSON array and expand to individual items.

        Args:
            item: Item with content=JSON string.

        Returns:
            List of ProcessingItem, one per array element.
        """
        import json

        data = json.loads(item.content)

        if not isinstance(data, list):
            raise ValueError("Expected JSON array")

        expanded_items = []

        for element in data:
            element_id = element.get("id", "unknown")
            element_content = json.dumps(element, ensure_ascii=False)

            expanded_item = ProcessingItem(
                item_id=element_id,
                source_path=item.source_path,
                current_step=self.name,
                status=ItemStatus.PENDING,
                metadata={
                    "parent_item_id": item.item_id,  # Track parent
                },
                content=element_content,
            )

            expanded_items.append(expanded_item)

        return expanded_items


class ConvertFormatStep(BaseStep):
    """Convert data format.

    1:1 Step - Converts data from one format to another.
    """

    @property
    def name(self) -> str:
        return "convert_format"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Convert data format.

        Args:
            item: Item with content in original format.

        Returns:
            Item with content in target format.
        """
        import json

        data = json.loads(item.content)

        # Convert format (example: rename fields)
        converted_data = {
            "uuid": data.get("id"),
            "name": data.get("title"),
            "created_at": data.get("timestamp"),
            "messages": data.get("content", []),
        }

        item.content = json.dumps(converted_data, ensure_ascii=False)
        item.metadata["format"] = "target_format"

        return item


class ValidateStep(BaseStep):
    """Validate data and skip if invalid.

    1:1 Step - Checks validation rules and sets status=SKIPPED if invalid.
    """

    @property
    def name(self) -> str:
        return "validate"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Validate data.

        Args:
            item: Item with content.

        Returns:
            Item with status=PENDING or SKIPPED.
        """
        import json

        data = json.loads(item.content)

        # Validation rule (example: minimum message count)
        if len(data.get("messages", [])) < 3:
            item.status = ItemStatus.SKIPPED
            item.metadata["skip_reason"] = "insufficient_messages"
        else:
            # Set final item_id from content hash
            from src.etl.utils.file_id import generate_file_id
            from pathlib import Path

            virtual_path = Path(f"items/{data['uuid']}.md")
            item.item_id = generate_file_id(item.content, virtual_path)

        return item
```

### 2. Extractor クラスの定義

```python
from pathlib import Path
from typing import Iterator

from src.etl.core.stage import BaseStage
from src.etl.core.types import StageType
from src.etl.core.models import ProcessingItem
from src.etl.core.status import ItemStatus


class NewExtractor(BaseStage):
    """Extract stage for new data source.

    Discovers input files and delegates processing to Steps:
    1. ReadFileStep: Read file and populate content
    2. ParseDataStep: Parse and expand to N items (1:N)
    3. ConvertFormatStep: Convert to target format
    4. ValidateStep: Validate and skip if invalid

    Design Pattern: discover_items() only finds files (content=None),
    actual processing is delegated to Steps. This enables steps.jsonl logging.
    """

    @property
    def stage_type(self) -> StageType:
        return StageType.EXTRACT

    @property
    def steps(self) -> list[BaseStep]:
        """Return ordered list of extraction steps."""
        return [
            ReadFileStep(),
            ParseDataStep(),
            ConvertFormatStep(),
            ValidateStep(),
        ]

    def discover_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Discover input files.

        Lightweight discovery: only finds files and yields ProcessingItem
        with content=None. Actual processing is delegated to Steps.

        Design Pattern: discover_items() is responsible ONLY for finding input files.
        This matches the recommended "Steps First" pattern and enables steps.jsonl logging.

        Args:
            input_path: Path to input file or directory.

        Yields:
            ProcessingItem with content=None for each file found.
        """
        # Find files
        if input_path.is_dir():
            files = list(input_path.glob("*.json"))
        else:
            files = [input_path] if input_path.exists() else []

        for file_path in files:
            # Yield ProcessingItem with content=None
            # Steps will populate content through processing pipeline
            item = ProcessingItem(
                item_id=f"file_{file_path.stem}",
                source_path=file_path,
                current_step="discover",
                status=ItemStatus.PENDING,
                metadata={
                    "source_provider": "new_source",
                    "source_type": "data",
                },
                content=None,  # ← Steps が処理
            )

            yield item
```

### 3. 使用例

```python
from src.etl.phases.import_phase import ImportPhase
from pathlib import Path

# Initialize phase with extractor
phase = ImportPhase(
    session_id="20260124_120000",
    extractor=NewExtractor(),
    transformer=KnowledgeTransformer(),
    loader=SessionLoader(),
)

# Run phase (BaseStage framework handles Steps automatically)
phase.run(input_path=Path("/path/to/input"))
```

## 既存 Extractor 比較

### ChatGPTExtractor (推奨パターン)

**パターン**: Steps First

**discover_items()**:
- ✅ ファイル発見のみ（ZIP ファイルを見つける）
- ✅ content=None で yield
- ✅ 処理は Steps に完全委譲

**steps**:
1. ReadZipStep (1:1): ZIP 読み込み、conversations.json 抽出
2. ParseConversationsStep (1:N): JSON パース、会話ごとに展開
3. ConvertFormatStep (1:1): ChatGPT → Claude フォーマット変換
4. ValidateMinMessagesStep (1:1): MIN_MESSAGES 閾値検証

**steps.jsonl 出力**: ✅ 4ステップの詳細ログ

**利点**:
- パフォーマンス分析が容易（各ステップの timing_ms、diff_ratio を追跡）
- BaseStage フレームワークを完全活用
- デバッグ時にステップ単位でエラー箇所を特定可能

### ClaudeExtractor (レガシーパターン)

**パターン**: Discovery First

**discover_items()**:
- ⚠️ ファイル発見 + JSON 読み込み + パース + 展開を実行
- ⚠️ content=conv_content で yield（処理済みデータを設定）
- ⚠️ Steps は補助的検証のみ

**steps**:
1. ParseJsonStep (1:1): content 既存時はパススルー
2. ValidateStructureStep (1:1): 構造検証

**steps.jsonl 出力**: ⚠️ 2ステップのみ（主要処理は discover_items() で完結）

**利点**:
- シンプル（Step クラスが少ない）
- 1:N 展開ロジックが discover_items() に集約され理解しやすい

**欠点**:
- steps.jsonl で主要処理（JSON 読み込み、パース、展開）が追跡できない
- パフォーマンスボトルネックの特定が困難

### 設計比較表

| 項目 | ChatGPTExtractor (推奨) | ClaudeExtractor (レガシー) |
|------|------------------------|--------------------------|
| **discover_items() の責務** | ファイル発見のみ | ファイル発見 + 読み込み + パース + 展開 |
| **content 設定** | None (Steps が処理) | conv_content (discover_items() で設定) |
| **1:N 展開の場所** | ParseConversationsStep | discover_items() 内 |
| **Steps の役割** | 主要処理（読み込み・変換・検証） | 補助的検証（パススルー中心） |
| **steps.jsonl 詳細度** | 高（4ステップログ） | 低（2ステップ、主要処理は未記録） |
| **パフォーマンス分析** | 容易（各ステップの timing_ms、diff_ratio） | 困難（主要処理は discover_items() で完結） |
| **デバッグ容易性** | 高（ステップ単位でエラー特定） | 低（discover_items() がブラックボックス） |

### 移行方針

- **新規 Extractor**: ChatGPT パターン（Steps First）を採用
- **ClaudeExtractor**: 現状維持（既存動作の安定性を優先）

## 1:N 展開パターン

BaseStage フレームワークは 1:N 展開を自動処理する。Step が list[ProcessingItem] を返すと、フレームワークが自動的に展開する。

### 1:N 展開の仕組み

```python
class ExpandingStep(BaseStep):
    """Example 1:N step - expands one item to multiple items."""

    @property
    def name(self) -> str:
        return "expand"

    def process(self, item: ProcessingItem) -> list[ProcessingItem]:
        """Expand one item to multiple items.

        Args:
            item: Single input item.

        Returns:
            List of ProcessingItem (N items).
        """
        # Parse data
        data = json.loads(item.content)

        # Create multiple items
        expanded_items = []

        for element in data["elements"]:
            expanded_item = ProcessingItem(
                item_id=element["id"],
                source_path=item.source_path,
                current_step=self.name,
                status=ItemStatus.PENDING,
                content=json.dumps(element),
                metadata={
                    "parent_item_id": item.item_id,  # Track parent
                },
            )

            expanded_items.append(expanded_item)

        return expanded_items
```

### BaseStage の自動処理

BaseStage.run() が以下を自動実行:

1. **list 検出**: step.process() が list[ProcessingItem] を返すことを検出
2. **展開**: 各アイテムに次のステップを適用
3. **メタデータ**: parent_item_id、expansion_index、total_expanded を自動設定
4. **ログ**: steps.jsonl に展開メタデータを記録

### steps.jsonl 出力例

```jsonl
{"step_index": 1, "current_step": "read_file", "before_chars": null, "after_chars": 5000, "diff_ratio": null}
{"step_index": 2, "current_step": "expand", "before_chars": 5000, "after_chars": 1000, "diff_ratio": 0.2, "metadata": {"parent_item_id": "file_abc", "expansion_index": 0, "total_expanded": 5}}
{"step_index": 2, "current_step": "expand", "before_chars": 5000, "after_chars": 1000, "diff_ratio": 0.2, "metadata": {"parent_item_id": "file_abc", "expansion_index": 1, "total_expanded": 5}}
{"step_index": 2, "current_step": "expand", "before_chars": 5000, "after_chars": 1000, "diff_ratio": 0.2, "metadata": {"parent_item_id": "file_abc", "expansion_index": 2, "total_expanded": 5}}
```

### 制約

- **空リスト禁止**: Step が空リストを返すと RuntimeError
- **1:N のみ**: N:M 展開は未対応（将来の拡張ポイント）

## ベストプラクティス

### DO: Steps First パターンを採用

```python
class GoodExtractor(BaseStage):
    def discover_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        # Find files only
        for file_path in input_path.glob("*.json"):
            yield ProcessingItem(
                item_id=f"file_{file_path.stem}",
                source_path=file_path,
                content=None,  # ✅ Steps が処理
            )

    @property
    def steps(self) -> list[BaseStep]:
        return [
            ReadFileStep(),
            ParseDataStep(),
            ConvertStep(),
        ]
```

### DON'T: discover_items() で処理を完結させる

```python
class BadExtractor(BaseStage):
    def discover_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        # ❌ ファイル読み込み + パースを discover_items() で実行
        for file_path in input_path.glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)

            for element in data:
                yield ProcessingItem(
                    item_id=element["id"],
                    content=json.dumps(element),  # ❌ 処理済みデータを設定
                )

    @property
    def steps(self) -> list[BaseStep]:
        return []  # ❌ Steps が空
```

**問題点**:
- steps.jsonl が生成されない
- パフォーマンス分析ができない
- BaseStage フレームワークを活かせていない

### DO: 1:N 展開は Step で実行

```python
class ParseDataStep(BaseStep):
    def process(self, item: ProcessingItem) -> list[ProcessingItem]:
        # ✅ Step で 1:N 展開
        data = json.loads(item.content)
        return [
            ProcessingItem(item_id=e["id"], content=json.dumps(e))
            for e in data["elements"]
        ]
```

### DO: エラーハンドリングを適切に実装

```python
class ReadFileStep(BaseStep):
    def process(self, item: ProcessingItem) -> ProcessingItem:
        try:
            with open(item.source_path, "r", encoding="utf-8") as f:
                data = f.read()
            item.content = data
        except Exception as e:
            # ✅ エラー情報を item に設定
            item.error = f"Failed to read file: {e}"
            item.status = ItemStatus.FAILED
            raise  # BaseStage がエラー処理を継続

        return item
```

### DO: メタデータを適切に設定

```python
class ConvertStep(BaseStep):
    def process(self, item: ProcessingItem) -> ProcessingItem:
        # ✅ メタデータで処理結果を記録
        item.metadata["message_count"] = len(data["messages"])
        item.metadata["format"] = "target_format"
        item.metadata["converted_at"] = datetime.now().isoformat()

        return item
```

### DO: validate_input() で入力検証

```python
class ReadFileStep(BaseStep):
    def validate_input(self, item: ProcessingItem) -> bool:
        # ✅ 入力検証を実装
        return item.source_path is not None and item.source_path.exists()
```

## 参考実装

- **ChatGPTExtractor**: `src/etl/stages/extract/chatgpt_extractor.py`
  - Steps First パターンの完全実装
  - 4つの Step クラス（ReadZip, Parse, Convert, Validate）
  - 1:N 展開（ParseConversationsStep）
  - エッジケース処理（空 JSON、破損 ZIP、マルチモーダル）

- **ClaudeExtractor**: `src/etl/stages/extract/claude_extractor.py`
  - Discovery First パターン（レガシー）
  - discover_items() で 1:N 展開
  - チャンク処理（大規模会話の分割）

## まとめ

新しい Extractor を追加する際は:

1. **Steps First パターンを採用**
2. **discover_items() は軽量に**（ファイル発見のみ、content=None）
3. **処理は Steps に分離**（Read, Parse, Convert, Validate）
4. **1:N 展開は Step で実行**（list[ProcessingItem] を返す）
5. **エラーハンドリングを適切に実装**
6. **メタデータで処理結果を記録**

このパターンに従うことで:
- ✅ steps.jsonl で全処理を可視化
- ✅ パフォーマンス分析が容易
- ✅ デバッグが効率的
- ✅ BaseStage フレームワークを完全活用

**Happy Extracting!**
