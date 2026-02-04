# Data Model: ETL Pipeline Entities

**Feature**: 025-bonobo-tenacity-migration
**Date**: 2026-01-19

## Entity Hierarchy

```
Session (1)
├── Phase (1..n) [import, organize]
│   ├── Stage (3) [extract, transform, load]
│   │   ├── Step (1..n)
│   │   └── ProcessingItem (0..n)
│   └── PhaseStatus
└── SessionStatus
```

---

## Core Entities

### Session

処理全体を包含する最上位エンティティ。

```python
@dataclass
class Session:
    session_id: str          # Format: YYYYMMDD_HHMMSS
    created_at: datetime
    status: SessionStatus
    phases: list[Phase]
    debug_mode: bool = False

    # Paths
    base_path: Path          # .staging/@session/{session_id}/
```

**Validation Rules**:
- `session_id` は `YYYYMMDD_HHMMSS` 形式
- `base_path` は存在するディレクトリ

**State Transitions**:
```
pending → running → completed
                 → failed
                 → partial (一部成功)
```

### SessionStatus

```python
class SessionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
```

---

### Phase

Session 内の処理種別。

```python
@dataclass
class Phase:
    phase_type: PhaseType    # import | organize
    status: PhaseStatus
    stages: dict[StageType, Stage]  # extract, transform, load
    started_at: datetime | None
    completed_at: datetime | None
    error_count: int = 0
    success_count: int = 0

    # Paths
    base_path: Path          # .staging/@session/{session_id}/{phase_type}/
    status_file: Path        # phase.json
```

**PhaseType**:
```python
class PhaseType(Enum):
    IMPORT = "import"
    ORGANIZE = "organize"
```

**PhaseStatus**:
```python
class PhaseStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
```

---

### Stage

Phase を ETL パターンで分割したもの。

```python
@dataclass
class Stage:
    stage_type: StageType    # extract | transform | load
    status: StageStatus
    steps: list[Step]
    items: list[ProcessingItem]

    # Paths
    input_path: Path         # .../extract/input/, etc.
    output_path: Path        # .../extract/output/, etc.
```

**StageType**:
```python
class StageType(Enum):
    EXTRACT = "extract"
    TRANSFORM = "transform"
    LOAD = "load"
```

**StageStatus**:
```python
class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

### Step

Stage 内の具体的な処理単位。

```python
@dataclass
class Step:
    step_name: str           # e.g., "parse_json", "validate", "generate_metadata"
    status: StepStatus
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    error: str | None

    # Metrics
    items_processed: int = 0
    items_failed: int = 0
```

**StepStatus**:
```python
class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
```

---

### ProcessingItem

パイプラインを流れる処理対象。

```python
@dataclass
class ProcessingItem:
    item_id: str             # ファイルパス or UUID
    source_path: Path
    current_step: str
    status: ItemStatus
    metadata: dict[str, Any]

    # Processing state
    content: str | None = None
    transformed_content: str | None = None
    output_path: Path | None = None
    error: str | None = None
```

**ItemStatus**:
```python
class ItemStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
```

---

### StepResult

Step 処理結果。

```python
@dataclass
class StepResult:
    success: bool
    output: Any | None
    error: str | None
    duration_ms: int
    items_processed: int
    items_failed: int
```

---

## Retry Configuration

tenacity 用のリトライ設定。

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    min_wait_seconds: float = 2.0
    max_wait_seconds: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_exceptions: tuple[type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
    )
```

---

## JSON Schema

### session.json

```json
{
  "session_id": "20260119_143052",
  "created_at": "2026-01-19T14:30:52Z",
  "status": "running",
  "debug_mode": false,
  "phases": ["import"]
}
```

### phase.json

```json
{
  "phase_type": "import",
  "status": "running",
  "started_at": "2026-01-19T14:30:52Z",
  "completed_at": null,
  "error_count": 0,
  "success_count": 5,
  "current_stage": "transform",
  "items": [
    {
      "item_id": "conversation_abc123",
      "status": "completed",
      "current_step": "generate_metadata",
      "error": null
    },
    {
      "item_id": "conversation_def456",
      "status": "processing",
      "current_step": "extract_knowledge",
      "error": null
    }
  ]
}
```

---

## Relationships

```
Session 1 ─────< Phase (1..n)
Phase   1 ─────< Stage (exactly 3: extract, transform, load)
Stage   1 ─────< Step (1..n)
Stage   1 ─────< ProcessingItem (0..n)
Step    1 ─────< StepResult (1)
```

---

## Migration from Existing Models

| Existing | New | Notes |
|----------|-----|-------|
| `SessionInfo` (retry.py) | `Session` | 拡張して Phase 対応 |
| `NormalizationResult` | `ProcessingItem.metadata` + `StepResult` | 分割して再構成 |
| `StageResult` | `StepResult` | 名称変更、Step 単位に |
| `PipelineContext` | `Phase` + `Stage` | 階層化 |

---

## Framework Design: Abstract Base Classes

### Input/Output 階層構造

```
┌─────────────────────────────────────────────────────────────────┐
│ Session                                                          │
│  Input:  SessionConfig (CLI args, settings)                     │
│  Output: SessionResult (summary, errors, metrics)               │
│  責務:   処理全体の管理、Phase 実行順序制御                      │
├─────────────────────────────────────────────────────────────────┤
│ Phase                                                            │
│  Input:  PhaseContext (session ref, input_path)                 │
│  Output: PhaseResult (items processed, errors, timing)          │
│  責務:   ETL Stage の順次実行、ステータス追跡                    │
├─────────────────────────────────────────────────────────────────┤
│ Stage                                                            │
│  Input:  StageContext, Iterable[ProcessingItem]                 │
│  Output: Iterable[ProcessingItem]                               │
│  責務:   Step の実行、item 変換、エラーハンドリング              │
├─────────────────────────────────────────────────────────────────┤
│ Step                                                             │
│  Input:  ProcessingItem                                         │
│  Output: ProcessingItem (transformed)                           │
│  責務:   単一 item の具体的変換ロジック                          │
└─────────────────────────────────────────────────────────────────┘
```

---

### Context Classes

各階層で必要な情報を保持するコンテキストオブジェクト。

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, TypeVar, Iterator, Any

T = TypeVar('T')
TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')


@dataclass
class SessionConfig:
    """Session 実行設定"""
    input_path: Path
    session_dir: Path = Path(".staging/@session")
    debug_mode: bool = False
    dry_run: bool = False
    limit: int | None = None
    retry_config: RetryConfig = field(default_factory=RetryConfig)


@dataclass
class SessionContext:
    """Session 実行中のコンテキスト"""
    session: Session
    config: SessionConfig

    @property
    def base_path(self) -> Path:
        return self.config.session_dir / self.session.session_id


@dataclass
class PhaseContext:
    """Phase 実行中のコンテキスト"""
    session_ctx: SessionContext
    phase: Phase

    @property
    def input_path(self) -> Path:
        return self.phase.stages[StageType.EXTRACT].input_path

    @property
    def output_path(self) -> Path:
        return self.phase.stages[StageType.LOAD].output_path


@dataclass
class StageContext:
    """Stage 実行中のコンテキスト"""
    phase_ctx: PhaseContext
    stage: Stage

    @property
    def input_path(self) -> Path:
        return self.stage.input_path

    @property
    def output_path(self) -> Path:
        return self.stage.output_path

    @property
    def debug_mode(self) -> bool:
        return self.phase_ctx.session_ctx.config.debug_mode
```

---

### Result Classes

各階層の処理結果を表すオブジェクト。

```python
@dataclass
class SessionResult:
    """Session 全体の処理結果"""
    session_id: str
    status: SessionStatus
    phases_completed: int
    phases_failed: int
    total_items: int
    success_items: int
    failed_items: int
    duration_seconds: float
    errors: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PhaseResult:
    """Phase の処理結果"""
    phase_type: PhaseType
    status: PhaseStatus
    items_processed: int
    items_failed: int
    duration_seconds: float
    stage_results: dict[StageType, 'StageResult'] = field(default_factory=dict)


@dataclass
class StageResult:
    """Stage の処理結果"""
    stage_type: StageType
    status: StageStatus
    items_in: int
    items_out: int
    items_failed: int
    duration_seconds: float
    step_results: list[StepResult] = field(default_factory=list)
```

---

### Abstract Base Classes

#### BaseStep - パイプラインの最小単位

```python
class BaseStep(ABC, Generic[TInput, TOutput]):
    """Step の抽象基底クラス

    単一の ProcessingItem を変換する最小単位。
    Step はステートレスであり、副作用を持たない純粋関数として実装する。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Step の識別名"""
        ...

    @abstractmethod
    def process(self, item: TInput) -> TOutput:
        """単一アイテムを処理

        Args:
            item: 処理対象アイテム

        Returns:
            処理後のアイテム

        Raises:
            StepError: 処理失敗時
        """
        ...

    def validate_input(self, item: TInput) -> bool:
        """入力バリデーション（オプション）"""
        return True

    def on_error(self, item: TInput, error: Exception) -> TOutput | None:
        """エラー時のフォールバック（オプション）

        Returns:
            None: アイテムをスキップ
            TOutput: フォールバック結果を返す
        """
        return None
```

#### BaseStage - Step のコンテナ

```python
class BaseStage(ABC):
    """Stage の抽象基底クラス

    複数の Step を順次実行し、ProcessingItem のストリームを変換する。
    """

    @property
    @abstractmethod
    def stage_type(self) -> StageType:
        """Stage の種別（extract/transform/load）"""
        ...

    @property
    @abstractmethod
    def steps(self) -> list[BaseStep]:
        """この Stage で実行する Step のリスト"""
        ...

    def run(
        self,
        ctx: StageContext,
        items: Iterator[ProcessingItem]
    ) -> Iterator[ProcessingItem]:
        """Stage を実行

        Args:
            ctx: Stage コンテキスト
            items: 入力アイテムのイテレータ

        Yields:
            処理済みアイテム
        """
        for item in items:
            try:
                result = self._process_item(ctx, item)
                if result is not None:
                    yield result
            except Exception as e:
                self._handle_error(ctx, item, e)

    def _process_item(
        self,
        ctx: StageContext,
        item: ProcessingItem
    ) -> ProcessingItem | None:
        """単一アイテムを全 Step で処理"""
        current = item
        for step in self.steps:
            current.current_step = step.name
            if not step.validate_input(current):
                current.status = ItemStatus.SKIPPED
                return current
            try:
                current = step.process(current)
            except Exception as e:
                fallback = step.on_error(current, e)
                if fallback is None:
                    current.status = ItemStatus.FAILED
                    current.error = str(e)
                    return current
                current = fallback
        current.status = ItemStatus.COMPLETED
        return current

    def _handle_error(
        self,
        ctx: StageContext,
        item: ProcessingItem,
        error: Exception
    ) -> None:
        """エラーハンドリング"""
        item.status = ItemStatus.FAILED
        item.error = str(error)
        if ctx.debug_mode:
            self._write_debug_log(ctx, item, error)
```

#### BasePhase - Stage のオーケストレーター

```python
class BasePhase(ABC):
    """Phase の抽象基底クラス

    ETL パターンに従い、Extract → Transform → Load の順で Stage を実行する。
    """

    @property
    @abstractmethod
    def phase_type(self) -> PhaseType:
        """Phase の種別（import/organize）"""
        ...

    @abstractmethod
    def create_extract_stage(self) -> BaseStage:
        """Extract Stage を生成"""
        ...

    @abstractmethod
    def create_transform_stage(self) -> BaseStage:
        """Transform Stage を生成"""
        ...

    @abstractmethod
    def create_load_stage(self) -> BaseStage:
        """Load Stage を生成"""
        ...

    def run(self, ctx: PhaseContext) -> PhaseResult:
        """Phase を実行"""
        stages = {
            StageType.EXTRACT: self.create_extract_stage(),
            StageType.TRANSFORM: self.create_transform_stage(),
            StageType.LOAD: self.create_load_stage(),
        }

        # ETL パイプライン実行
        items = self._run_extract(ctx, stages[StageType.EXTRACT])
        items = self._run_transform(ctx, stages[StageType.TRANSFORM], items)
        result = self._run_load(ctx, stages[StageType.LOAD], items)

        return self._build_result(ctx, result)

    def _run_extract(
        self,
        ctx: PhaseContext,
        stage: BaseStage
    ) -> Iterator[ProcessingItem]:
        """Extract Stage 実行"""
        stage_ctx = StageContext(ctx, ctx.phase.stages[StageType.EXTRACT])
        input_items = self._discover_items(ctx.input_path)
        return stage.run(stage_ctx, input_items)

    @abstractmethod
    def _discover_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """入力パスからアイテムを発見"""
        ...
```

#### SessionRunner - Phase のオーケストレーター

```python
class SessionRunner:
    """Session の実行管理

    Session を開始し、登録された Phase を順次実行する。
    """

    def __init__(self, config: SessionConfig):
        self.config = config
        self._phases: list[BasePhase] = []

    def add_phase(self, phase: BasePhase) -> 'SessionRunner':
        """Phase を追加（ビルダーパターン）"""
        self._phases.append(phase)
        return self

    def run(self) -> SessionResult:
        """Session を実行"""
        session = self._create_session()
        ctx = SessionContext(session, self.config)

        results = []
        for phase in self._phases:
            phase_ctx = self._create_phase_context(ctx, phase)
            result = phase.run(phase_ctx)
            results.append(result)
            self._update_status(ctx, result)

        return self._build_result(ctx, results)

    def _create_session(self) -> Session:
        """新規 Session を生成"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        return Session(
            session_id=session_id,
            created_at=datetime.now(),
            status=SessionStatus.PENDING,
            phases=[],
            debug_mode=self.config.debug_mode,
            base_path=self.config.session_dir / session_id,
        )
```

---

### Declarative Pipeline Definition API

パイプラインを宣言的に定義するためのビルダー API。

```python
# 使用例: Import Phase の定義
class ImportPhase(BasePhase):
    phase_type = PhaseType.IMPORT

    def create_extract_stage(self) -> BaseStage:
        return ExtractStage(steps=[
            ParseJsonStep(),
            ValidateStructureStep(),
        ])

    def create_transform_stage(self) -> BaseStage:
        return TransformStage(steps=[
            ExtractKnowledgeStep(),
            GenerateMetadataStep(),
            FormatMarkdownStep(),
        ])

    def create_load_stage(self) -> BaseStage:
        return LoadStage(steps=[
            WriteFileStep(),
            UpdateIndexStep(),
        ])


# 使用例: Session 実行
def main():
    config = SessionConfig(
        input_path=Path("./data/claude-export"),
        debug_mode=True,
    )

    result = (
        SessionRunner(config)
        .add_phase(ImportPhase())
        .add_phase(OrganizePhase())  # オプション
        .run()
    )

    print(f"Session {result.session_id}: {result.status}")
    print(f"  Processed: {result.success_items}/{result.total_items}")
```

---

### Step 実装例

```python
class ParseJsonStep(BaseStep[ProcessingItem, ProcessingItem]):
    """Claude エクスポート JSON をパース"""

    name = "parse_json"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        with open(item.source_path) as f:
            data = json.load(f)
        item.content = data
        item.metadata["parsed_at"] = datetime.now().isoformat()
        return item

    def validate_input(self, item: ProcessingItem) -> bool:
        return item.source_path.suffix == ".json"


class ExtractKnowledgeStep(BaseStep[ProcessingItem, ProcessingItem]):
    """Ollama で知識を抽出（tenacity リトライ付き）"""

    name = "extract_knowledge"

    def __init__(self, retry_config: RetryConfig | None = None):
        self.retry_config = retry_config or RetryConfig()

    @with_retry()  # tenacity デコレータ
    def process(self, item: ProcessingItem) -> ProcessingItem:
        prompt = self._build_prompt(item.content)
        response = self._call_ollama(prompt)
        item.transformed_content = response
        return item

    def on_error(self, item: ProcessingItem, error: Exception) -> ProcessingItem:
        """リトライ上限到達時のフォールバック"""
        item.metadata["extraction_failed"] = True
        item.metadata["error"] = str(error)
        return item  # スキップせず、メタデータ付きで継続
```

---

### Type Safety: Generic Constraints

```python
from typing import Protocol

class Extractable(Protocol):
    """Extract 可能なアイテム"""
    source_path: Path
    content: Any | None


class Transformable(Protocol):
    """Transform 可能なアイテム"""
    content: Any
    transformed_content: Any | None


class Loadable(Protocol):
    """Load 可能なアイテム"""
    transformed_content: Any
    output_path: Path | None


# Stage は適切な Protocol を要求
class ExtractStage(BaseStage):
    stage_type = StageType.EXTRACT

    def run(
        self,
        ctx: StageContext,
        items: Iterator[Extractable]
    ) -> Iterator[Transformable]:
        ...
```

---

### Status Emission (JSON ログ出力)

FW が自動的にステータスを JSON 形式で出力する。実装側はステータス出力を意識する必要がない。

#### StatusEmitter - ステータス出力の責務

```python
import json
import sys
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import TextIO, Any


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


@dataclass
class MarkdownDocument:
    """Markdown ドキュメント（Property + Content 分離）

    Obsidian 形式:
    ```
    ---
    title: タイトル        ← Property (YAML frontmatter)
    tags: [tag1, tag2]
    ---
    # 見出し              ← Content (本文)
    本文テキスト...
    ```
    """
    properties: dict[str, Any]   # YAML frontmatter
    content: str                  # 本文（frontmatter 以降）
    raw: str                      # 元の生テキスト

    @classmethod
    def parse(cls, text: str, delimiter: str = "---") -> 'MarkdownDocument':
        """デリミタで Property と Content を分離"""
        properties = {}
        content = text
        raw = text

        lines = text.split('\n')
        if lines and lines[0].strip() == delimiter:
            # frontmatter 開始を検出
            end_idx = None
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == delimiter:
                    end_idx = i
                    break

            if end_idx:
                frontmatter_lines = lines[1:end_idx]
                content_lines = lines[end_idx + 1:]

                # YAML パース
                frontmatter_text = '\n'.join(frontmatter_lines)
                try:
                    import yaml
                    properties = yaml.safe_load(frontmatter_text) or {}
                except Exception:
                    properties = {"_raw": frontmatter_text}

                content = '\n'.join(content_lines).lstrip('\n')

        return cls(properties=properties, content=content, raw=raw)

    def to_text(self, delimiter: str = "---") -> str:
        """Property + Content を結合してテキストに戻す"""
        if not self.properties:
            return self.content

        import yaml
        frontmatter = yaml.dump(self.properties, allow_unicode=True, default_flow_style=False)
        return f"{delimiter}\n{frontmatter}{delimiter}\n\n{self.content}"


@dataclass
class ContentMetrics:
    """コンテンツ情報量（必須）

    Content（本文）のサイズ変化を追跡。
    Property（frontmatter）は別途 context で追跡。

    delta は変化率（浮動小数点）:
      - 0.0: 変化なし
      - -0.5: 50% 圧縮（元の半分になった）
      - 1.0: 2倍に増加
      - -1.0: 完全削除（size_out = 0）

    異常検出の例:
      - delta <= -0.5: 50%以上圧縮 → レビュー必要
      - delta >= 2.0: 3倍以上増加 → 要確認
    """
    size_in: int              # 入力 Content サイズ
    size_out: int             # 出力 Content サイズ
    delta: float              # 変化率（(size_out - size_in) / size_in）
    unit: str = "bytes"       # "bytes" | "chars" | "lines"

    @classmethod
    def from_content(cls, before: Any, after: Any, unit: str = "bytes") -> 'ContentMetrics':
        """コンテンツから自動計算"""
        before_content = cls._extract_content(before)
        after_content = cls._extract_content(after)
        size_in = cls._measure(before_content, unit)
        size_out = cls._measure(after_content, unit)
        # 変化率を計算（size_in が 0 の場合は特別処理）
        if size_in == 0:
            delta = float('inf') if size_out > 0 else 0.0
        else:
            delta = (size_out - size_in) / size_in
        return cls(size_in=size_in, size_out=size_out, delta=delta, unit=unit)

    @staticmethod
    def _extract_content(obj: Any) -> str | Any:
        """MarkdownDocument の場合は content を抽出"""
        if isinstance(obj, MarkdownDocument):
            return obj.content
        return obj

    @staticmethod
    def _measure(content: Any, unit: str) -> int:
        if content is None:
            return 0
        if unit == "bytes":
            if isinstance(content, (str, bytes)):
                return len(content.encode('utf-8') if isinstance(content, str) else content)
            return len(json.dumps(content, ensure_ascii=False).encode('utf-8'))
        elif unit == "chars":
            return len(str(content))
        elif unit == "lines":
            return len(str(content).split('\n'))
        return 0


@dataclass
class PropertyChange:
    """Property（frontmatter）の変化（オプション）"""
    added: dict[str, Any]      # 追加されたプロパティ
    removed: list[str]         # 削除されたキー
    modified: dict[str, tuple[Any, Any]]  # 変更（before, after）

    @classmethod
    def from_properties(
        cls,
        before: dict[str, Any],
        after: dict[str, Any]
    ) -> 'PropertyChange':
        """2つの Property dict から差分を計算"""
        added = {k: v for k, v in after.items() if k not in before}
        removed = [k for k in before if k not in after]
        modified = {
            k: (before[k], after[k])
            for k in before
            if k in after and before[k] != after[k]
        }
        return cls(added=added, removed=removed, modified=modified)

    def is_empty(self) -> bool:
        return not self.added and not self.removed and not self.modified

    def to_dict(self) -> dict[str, Any]:
        """ログ出力用の辞書形式"""
        result = {}
        if self.added:
            result["added"] = self.added
        if self.removed:
            result["removed"] = self.removed
        if self.modified:
            result["modified"] = {k: {"from": v[0], "to": v[1]} for k, v in self.modified.items()}
        return result


@dataclass
class StatusEvent:
    """ステータスイベント（JSON ログの1行）"""
    timestamp: str
    level: LogLevel
    event_type: str           # session.start, phase.start, step.complete, etc.
    session_id: str
    phase: str | None = None
    stage: str | None = None
    step: str | None = None
    item_id: str | None = None
    status: str | None = None
    message: str | None = None
    duration_ms: int | None = None
    content: ContentMetrics | None = None       # Content 情報量（必須）
    properties: PropertyChange | None = None    # Property 変化（オプション）
    context: dict[str, Any] | None = None       # Step 固有情報（オプション）
    metadata: dict[str, Any] = field(default_factory=dict)


class StatusEmitter:
    """ステータス出力管理（JSON Lines 形式）

    FW 内部で自動的にステータスを出力する。
    実装者はこのクラスを直接使用しない。
    """

    def __init__(
        self,
        session_id: str,
        output: TextIO = sys.stdout,
        debug_mode: bool = False,
    ):
        self.session_id = session_id
        self.output = output
        self.debug_mode = debug_mode
        self._phase: str | None = None
        self._stage: str | None = None

    def emit(self, event: StatusEvent) -> None:
        """イベントを JSON Lines 形式で出力"""
        if event.level == LogLevel.DEBUG and not self.debug_mode:
            return

        data = {
            "ts": event.timestamp,
            "level": event.level.value,
            "event": event.event_type,
            "session": event.session_id,
        }

        # Optional fields（None は出力しない）
        if event.phase:
            data["phase"] = event.phase
        if event.stage:
            data["stage"] = event.stage
        if event.step:
            data["step"] = event.step
        if event.item_id:
            data["item"] = event.item_id
        if event.status:
            data["status"] = event.status
        if event.message:
            data["msg"] = event.message
        if event.duration_ms is not None:
            data["duration_ms"] = event.duration_ms

        # Content 情報量（必須）
        if event.content:
            data["content"] = {
                "in": event.content.size_in,
                "out": event.content.size_out,
                "delta": event.content.delta,
                "unit": event.content.unit,
            }

        # Property 変化（オプション: frontmatter の差分）
        if event.properties and not event.properties.is_empty():
            data["props"] = event.properties.to_dict()

        # Step 固有コンテキスト（オプション）
        if event.context:
            data["ctx"] = event.context

        if event.metadata:
            data["meta"] = event.metadata

        self.output.write(json.dumps(data, ensure_ascii=False) + "\n")
        self.output.flush()

    # ---- Convenience methods ----

    def session_start(self, config: SessionConfig) -> None:
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.INFO,
            event_type="session.start",
            session_id=self.session_id,
            metadata={"input_path": str(config.input_path), "debug": config.debug_mode},
        ))

    def session_end(self, result: SessionResult) -> None:
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.INFO,
            event_type="session.end",
            session_id=self.session_id,
            status=result.status.value,
            duration_ms=int(result.duration_seconds * 1000),
            metadata={
                "total": result.total_items,
                "success": result.success_items,
                "failed": result.failed_items,
            },
        ))

    def phase_start(self, phase_type: PhaseType) -> None:
        self._phase = phase_type.value
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.INFO,
            event_type="phase.start",
            session_id=self.session_id,
            phase=self._phase,
        ))

    def phase_end(self, result: PhaseResult) -> None:
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.INFO,
            event_type="phase.end",
            session_id=self.session_id,
            phase=self._phase,
            status=result.status.value,
            duration_ms=int(result.duration_seconds * 1000),
            metadata={
                "processed": result.items_processed,
                "failed": result.items_failed,
            },
        ))
        self._phase = None

    def stage_start(self, stage_type: StageType) -> None:
        self._stage = stage_type.value
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.INFO,
            event_type="stage.start",
            session_id=self.session_id,
            phase=self._phase,
            stage=self._stage,
        ))

    def stage_end(self, result: StageResult) -> None:
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.INFO,
            event_type="stage.end",
            session_id=self.session_id,
            phase=self._phase,
            stage=self._stage,
            status=result.status.value,
            duration_ms=int(result.duration_seconds * 1000),
            metadata={
                "in": result.items_in,
                "out": result.items_out,
                "failed": result.items_failed,
            },
        ))
        self._stage = None

    def step_start(self, step_name: str, item_id: str) -> None:
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.DEBUG,  # DEBUG: debug_mode のみ出力
            event_type="step.start",
            session_id=self.session_id,
            phase=self._phase,
            stage=self._stage,
            step=step_name,
            item_id=item_id,
        ))

    def step_complete(
        self,
        step_name: str,
        item_id: str,
        duration_ms: int,
        content: ContentMetrics,
        properties: PropertyChange | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.DEBUG,
            event_type="step.complete",
            session_id=self.session_id,
            phase=self._phase,
            stage=self._stage,
            step=step_name,
            item_id=item_id,
            status="completed",
            duration_ms=duration_ms,
            content=content,
            properties=properties,
            context=context,
        ))

    def step_error(self, step_name: str, item_id: str, error: str) -> None:
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.ERROR,
            event_type="step.error",
            session_id=self.session_id,
            phase=self._phase,
            stage=self._stage,
            step=step_name,
            item_id=item_id,
            status="failed",
            message=error,
        ))

    def item_complete(
        self,
        item_id: str,
        status: ItemStatus,
        content: ContentMetrics | None = None,
        properties: PropertyChange | None = None,
    ) -> None:
        self.emit(StatusEvent(
            timestamp=self._now(),
            level=LogLevel.INFO,
            event_type="item.complete",
            session_id=self.session_id,
            phase=self._phase,
            stage=self._stage,
            item_id=item_id,
            status=status.value,
            content=content,
            properties=properties,
        ))

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="milliseconds")
```

#### JSON ログ出力例

```jsonl
{"ts":"2026-01-19T14:30:52.123","level":"info","event":"session.start","session":"20260119_143052","meta":{"input_path":"./data/export","debug":true}}
{"ts":"2026-01-19T14:30:52.125","level":"info","event":"phase.start","session":"20260119_143052","phase":"import"}
{"ts":"2026-01-19T14:30:52.126","level":"info","event":"stage.start","session":"20260119_143052","phase":"import","stage":"extract"}
{"ts":"2026-01-19T14:30:52.130","level":"debug","event":"step.start","session":"20260119_143052","phase":"import","stage":"extract","step":"parse_markdown","item":"Automated_image_001.md"}
{"ts":"2026-01-19T14:30:52.145","level":"debug","event":"step.complete","session":"20260119_143052","phase":"import","stage":"extract","step":"parse_markdown","item":"Automated_image_001.md","status":"completed","duration_ms":15,"content":{"in":4523,"out":4200,"delta":-0.071,"unit":"bytes"}}
{"ts":"2026-01-19T14:30:52.200","level":"debug","event":"step.complete","session":"20260119_143052","phase":"import","stage":"transform","step":"normalize","item":"Automated_image_001.md","status":"completed","duration_ms":50,"content":{"in":4200,"out":3800,"delta":-0.095,"unit":"bytes"},"props":{"added":{"normalized":true,"file_id":"abc123"},"modified":{"title":{"from":"Automated image...","to":"画像オーバーレイ技術"}}}}
{"ts":"2026-01-19T14:30:52.300","level":"debug","event":"step.complete","session":"20260119_143052","phase":"import","stage":"transform","step":"classify","item":"Automated_image_001.md","status":"completed","duration_ms":1250,"content":{"in":3800,"out":3800,"delta":0.0,"unit":"bytes"},"props":{"added":{"genre":"エンジニア","tags":["画像処理","Python"]}},"ctx":{"model":"llama3","confidence":0.92}}
{"ts":"2026-01-19T14:30:52.350","level":"info","event":"item.complete","session":"20260119_143052","phase":"import","stage":"load","item":"Automated_image_001.md","status":"completed","content":{"in":4523,"out":3800,"delta":-0.160,"unit":"bytes"},"props":{"added":{"normalized":true,"file_id":"abc123","genre":"エンジニア"}}}
{"ts":"2026-01-19T14:30:53.200","level":"error","event":"step.error","session":"20260119_143052","phase":"import","stage":"transform","step":"classify","item":"another_file.md","status":"failed","msg":"Connection timeout","content":{"in":8900,"out":0,"delta":-1.0,"unit":"bytes"}}
{"ts":"2026-01-19T14:31:05.500","level":"info","event":"stage.end","session":"20260119_143052","phase":"import","stage":"transform","status":"completed","duration_ms":13374,"content":{"in":45230,"out":38000,"delta":-0.160,"unit":"bytes"},"meta":{"in":10,"out":9,"failed":1}}
{"ts":"2026-01-19T14:32:00.000","level":"info","event":"phase.end","session":"20260119_143052","phase":"import","status":"partial","duration_ms":67875,"content":{"in":45230,"out":38000,"delta":-0.160,"unit":"bytes"},"meta":{"processed":10,"failed":1}}
{"ts":"2026-01-19T14:32:00.100","level":"info","event":"session.end","session":"20260119_143052","status":"partial","duration_ms":67977,"content":{"in":45230,"out":38000,"delta":-0.160,"unit":"bytes"},"meta":{"total":10,"success":9,"failed":1}}
```

#### ログフィールド説明

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `content` | ✅ | Content（本文）の情報量変化 |
| `content.in` | ✅ | 入力 Content サイズ |
| `content.out` | ✅ | 出力 Content サイズ |
| `content.delta` | ✅ | 変化率（float: -0.5 = 50%圧縮, -1.0 = 完全削除） |
| `content.unit` | ✅ | 単位（bytes/chars/lines） |
| `props` | ❌ | Property（frontmatter）の変化 |
| `props.added` | ❌ | 追加されたプロパティ |
| `props.removed` | ❌ | 削除されたキー |
| `props.modified` | ❌ | 変更されたプロパティ（from/to） |
| `ctx` | ❌ | Step 固有コンテキスト（LLM 情報等） |

#### 用語定義

| 用語 | 説明 | 例 |
|------|------|-----|
| **Property** | YAML frontmatter | `title`, `tags`, `normalized` |
| **Content** | frontmatter 以降の本文 | `# 見出し` 以降のテキスト |
| **Delimiter** | frontmatter 区切り文字 | `---`（デフォルト） |

#### コンテキストプロパティ例

Step 固有の情報をオプションで記録：

```python
# Ollama 呼び出し時
context = {
    "model": "llama3",
    "tokens_used": 450,
    "prompt_tokens": 320,
    "completion_tokens": 130,
}

# ファイル処理時
context = {
    "source_type": "claude_export",
    "conversation_id": "abc123",
    "message_count": 42,
}

# 分類時
context = {
    "genre": "エンジニア",
    "confidence": 0.92,
    "tags": ["Python", "設計"],
}
```

#### Step でコンテキストを提供する方法

Step 実装者は `last_context` 属性を設定することで、ログにコンテキスト情報を追加できる：

```python
class ExtractKnowledgeStep(BaseStep[ProcessingItem, ProcessingItem]):
    """Ollama で知識を抽出（コンテキスト情報付き）"""

    name = "extract_knowledge"
    last_context: dict[str, Any] | None = None  # FW が参照

    def process(self, item: ProcessingItem) -> ProcessingItem:
        response = self._call_ollama(item.content)

        # コンテキスト情報を設定（FW が自動的にログに記録）
        self.last_context = {
            "model": "llama3",
            "tokens_used": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        }

        item.transformed_content = response.content
        return item


class ClassifyStep(BaseStep[ProcessingItem, ProcessingItem]):
    """ジャンル分類"""

    name = "classify"
    last_context: dict[str, Any] | None = None

    def process(self, item: ProcessingItem) -> ProcessingItem:
        result = self._classify(item.content)

        self.last_context = {
            "genre": result.genre,
            "confidence": result.confidence,
            "tags": result.tags,
        }

        item.metadata["genre"] = result.genre
        item.metadata["tags"] = result.tags
        return item
```

**Note**: `last_context` はオプション。設定しなければログに `ctx` フィールドは出力されない。

---

#### FW への組み込み（Base Classes 更新）

StatusEmitter を Context に組み込み、自動的にステータスを出力する。

```python
@dataclass
class SessionContext:
    """Session 実行中のコンテキスト"""
    session: Session
    config: SessionConfig
    emitter: StatusEmitter = field(init=False)

    def __post_init__(self):
        self.emitter = StatusEmitter(
            session_id=self.session.session_id,
            debug_mode=self.config.debug_mode,
        )


class BaseStage(ABC):
    """Stage の抽象基底クラス（ステータス出力組み込み）"""

    def run(
        self,
        ctx: StageContext,
        items: Iterator[ProcessingItem]
    ) -> Iterator[ProcessingItem]:
        emitter = ctx.phase_ctx.session_ctx.emitter
        emitter.stage_start(self.stage_type)

        start_time = time.time()
        items_in = items_out = items_failed = 0

        for item in items:
            items_in += 1
            try:
                result = self._process_item_with_tracking(ctx, item, emitter)
                if result is not None:
                    items_out += 1
                    yield result
                else:
                    items_failed += 1
            except Exception as e:
                items_failed += 1
                emitter.step_error("unknown", item.item_id, str(e))

        duration = time.time() - start_time
        emitter.stage_end(StageResult(
            stage_type=self.stage_type,
            status=StageStatus.COMPLETED if items_failed == 0 else StageStatus.PARTIAL,
            items_in=items_in,
            items_out=items_out,
            items_failed=items_failed,
            duration_seconds=duration,
        ))

    def _process_item_with_tracking(
        self,
        ctx: StageContext,
        item: ProcessingItem,
        emitter: StatusEmitter,
    ) -> ProcessingItem | None:
        """Step 実行 + ステータス追跡（Content/Property 自動計測）"""
        current = item
        initial_doc = self._get_document(current)
        initial_props = initial_doc.properties.copy() if initial_doc else {}

        for step in self.steps:
            step_start = time.time()
            before_doc = self._get_document(current)
            before_props = before_doc.properties.copy() if before_doc else {}
            emitter.step_start(step.name, item.item_id)

            try:
                current = step.process(current)
                after_doc = self._get_document(current)
                duration_ms = int((time.time() - step_start) * 1000)

                # Content 情報量を自動計測
                content_metrics = ContentMetrics.from_content(
                    before_doc, after_doc, unit="bytes"
                )

                # Property 変化を自動検出
                after_props = after_doc.properties if after_doc else {}
                prop_change = PropertyChange.from_properties(before_props, after_props)

                # Step 固有コンテキスト（オプション）
                step_context = getattr(step, 'last_context', None)

                emitter.step_complete(
                    step.name, item.item_id, duration_ms,
                    content=content_metrics,
                    properties=prop_change if not prop_change.is_empty() else None,
                    context=step_context,
                )
            except Exception as e:
                emitter.step_error(step.name, item.item_id, str(e))
                fallback = step.on_error(current, e)
                if fallback is None:
                    current.status = ItemStatus.FAILED
                    emitter.item_complete(item.item_id, ItemStatus.FAILED)
                    return None
                current = fallback

        # アイテム全体の Content/Property 変化
        final_doc = self._get_document(current)
        total_metrics = ContentMetrics.from_content(initial_doc, final_doc, unit="bytes")
        final_props = final_doc.properties if final_doc else {}
        total_prop_change = PropertyChange.from_properties(initial_props, final_props)

        current.status = ItemStatus.COMPLETED
        emitter.item_complete(
            item.item_id, ItemStatus.COMPLETED,
            content=total_metrics,
            properties=total_prop_change if not total_prop_change.is_empty() else None,
        )
        return current

    def _get_document(self, item: ProcessingItem) -> MarkdownDocument | None:
        """アイテムから MarkdownDocument を取得"""
        content = item.transformed_content or item.content
        if isinstance(content, MarkdownDocument):
            return content
        if isinstance(content, str):
            return MarkdownDocument.parse(content, delimiter="---")
        return None
```

---

#### ファイル出力（debug モード）

debug モード時は、JSON ログをファイルにも出力する。

```python
class StatusEmitter:
    def __init__(
        self,
        session_id: str,
        output: TextIO = sys.stdout,
        debug_mode: bool = False,
        log_dir: Path | None = None,
    ):
        self.session_id = session_id
        self.output = output
        self.debug_mode = debug_mode
        self._file_output: TextIO | None = None

        if debug_mode and log_dir:
            log_path = log_dir / f"{session_id}.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_output = open(log_path, "a", encoding="utf-8")

    def emit(self, event: StatusEvent) -> None:
        # ... 既存の出力処理 ...

        # ファイルにも出力
        if self._file_output:
            self._file_output.write(json.dumps(data, ensure_ascii=False) + "\n")
            self._file_output.flush()

    def close(self) -> None:
        if self._file_output:
            self._file_output.close()
```

---

#### Log Level ルール

| Level | 出力条件 | イベント例 |
|-------|----------|-----------|
| `debug` | debug_mode のみ | step.start, step.complete |
| `info` | 常に出力 | session.*, phase.*, stage.*, item.complete |
| `warn` | 常に出力 | retry 発生時 |
| `error` | 常に出力 | step.error, phase.error |

---

### Error Handling Strategy

```python
class StepError(Exception):
    """Step 処理エラー"""
    def __init__(self, step_name: str, item_id: str, message: str):
        self.step_name = step_name
        self.item_id = item_id
        super().__init__(f"[{step_name}] {item_id}: {message}")


class RetryableError(StepError):
    """リトライ可能なエラー"""
    pass


class FatalError(StepError):
    """リトライ不可能な致命的エラー"""
    pass


# Step 内での使用
class ExtractKnowledgeStep(BaseStep):
    def process(self, item: ProcessingItem) -> ProcessingItem:
        try:
            response = self._call_ollama(item.content)
        except ConnectionError as e:
            raise RetryableError(self.name, item.item_id, str(e))
        except ValueError as e:
            raise FatalError(self.name, item.item_id, str(e))
        return item
```
