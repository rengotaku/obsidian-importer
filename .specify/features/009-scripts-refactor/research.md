# Research: Scripts コードリファクタリング

**Date**: 2026-01-14 | **Plan**: [plan.md](plan.md)

## Research Topics

1. 循環インポート回避パターン
2. グローバル状態のカプセル化
3. Python パッケージ構成ベストプラクティス
4. 既存コードの依存関係分析

---

## 1. 循環インポート回避パターン

### 問題

モジュール分割時、相互に依存するモジュール間で循環インポートが発生する可能性がある。

例: `pipeline/stages.py` が `types.py` を参照し、`types.py` が `pipeline/` の型を参照するケース。

### Decision: 型定義集約 + TYPE_CHECKING

**選択**: `types.py` に全型定義を集約し、実行時インポートと型チェック時インポートを分離

**Rationale**:
- Python 3.7+ の `TYPE_CHECKING` 定数で型ヒント用インポートを分離可能
- 実行時には型チェック用インポートは評価されない
- 標準ライブラリのみで実現可能

**パターン**:

```python
# types.py - 全型定義を集約
from typing import TypedDict, Literal

class StageResult(TypedDict):
    success: bool
    data: dict

class PipelineContext(TypedDict):
    file_path: str
    content: str
```

```python
# pipeline/stages.py - 型インポート
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from normalizer.types import StageResult, PipelineContext

def stage1_dust(ctx: PipelineContext) -> StageResult:
    ...
```

**Alternatives Considered**:
- Protocol による構造的サブタイピング → 過剰な複雑さ
- 文字列リテラル型ヒント → IDE サポートが弱い
- 動的インポート → 実行時オーバーヘッド

---

## 2. グローバル状態のカプセル化

### 問題

現在のコードには以下のグローバル変数が存在：

```python
_current_session_dir: Path | None = None  # L36
_cached_prompt: str | None = None          # L237
_stage_debug_mode: bool = False            # L764
_excluded_files: list[tuple[Path, str]] = []  # L1391
```

これらはモジュール分割時に参照が複雑になる。

### Decision: シングルトン State クラス

**選択**: `state/manager.py` に `StateManager` シングルトンクラスを作成

**Rationale**:
- グローバル状態を1箇所に集約し、アクセスを明示化
- テスト時にモック可能
- スレッドセーフ（必要に応じて）

**パターン**:

```python
# state/manager.py
from __future__ import annotations
from pathlib import Path
from typing import ClassVar

class StateManager:
    """グローバル状態を管理するシングルトン"""

    _instance: ClassVar[StateManager | None] = None

    def __new__(cls) -> StateManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        self.session_dir: Path | None = None
        self.cached_prompt: str | None = None
        self.stage_debug_mode: bool = False
        self.excluded_files: list[tuple[Path, str]] = []

    def reset(self) -> None:
        """テスト用: 状態をリセット"""
        self._initialize()

# 便利なアクセサ
def get_state() -> StateManager:
    return StateManager()
```

**使用例**:

```python
# pipeline/stages.py
from normalizer.state.manager import get_state

def stage1_dust(ctx):
    state = get_state()
    if state.stage_debug_mode:
        print_debug(...)
```

**Alternatives Considered**:
- モジュールレベル変数の維持 → 依存関係が不明確
- 依存性注入（DI）→ 過剰なリファクタリング
- コンテキストオブジェクト引き渡し → 全関数のシグネチャ変更が必要

---

## 3. Python パッケージ構成ベストプラクティス

### Decision: フラット + サブパッケージ構成

**選択**: `normalizer/` パッケージ内に機能別サブパッケージを配置

**Rationale**:
- 関連機能をディレクトリで視覚的にグループ化
- `__init__.py` で公開 API を制御
- 各サブパッケージは独立してテスト可能

**パターン**:

```
normalizer/
├── __init__.py          # 公開APIのエクスポート
├── config.py            # 定数（他に依存しない）
├── types.py             # 型定義（他に依存しない）
├── validators/
│   ├── __init__.py      # from .title import validate_title
│   └── ...
└── ...
```

**`__init__.py` の役割**:

```python
# normalizer/__init__.py
"""Obsidian Normalizer パッケージ"""

from normalizer.config import (
    OLLAMA_URL,
    MODEL,
    BASE_DIR,
    # ... 公開する定数
)

from normalizer.cli.commands import main

__all__ = [
    "main",
    "OLLAMA_URL",
    "MODEL",
    # ...
]
```

**Alternatives Considered**:
- 完全フラット構造 → ファイル数が多すぎる（18ファイル）
- 深いネスト → 相対インポートが複雑化
- namespace パッケージ → 標準ライブラリのみ制約に不適

---

## 4. 既存コードの依存関係分析

### 現在の関数グループと依存関係

分析対象: `ollama_normalizer.py` の 86 関数 + 11 クラス

#### グループ A: 設定・定数（依存なし）

| 関数/定数 | 行番号 | 移行先 |
|-----------|--------|--------|
| `OLLAMA_URL`, `MODEL`, `BASE_DIR`, etc. | L22-78 | `config.py` |
| `GENRES`, `VAULT_MAP` | L39-50 | `config.py` |
| `STAGE_PROMPTS`, `TEMPLATE_MARKERS` | L79-143 | `config.py` |

#### グループ B: 型定義（依存なし）

| クラス | 行番号 | 移行先 |
|--------|--------|--------|
| `PreProcessingResult` | L633 | `types.py` |
| `StageResult`, `Stage1-4Result` | L644-677 | `types.py` |
| `PipelineContext` | L679 | `types.py` |
| `Frontmatter`, `NormalizationResult` | L1334-1355 | `types.py` |
| `ProcessingResult`, `ScanResult` | L1356-1385 | `types.py` |

#### グループ C: 検証（config, types に依存）

| 関数 | 行番号 | 移行先 |
|------|--------|--------|
| `validate_title`, `log_title_quality` | L355-410 | `validators/title.py` |
| `get_all_known_tags`, `validate_tags`, `calculate_tag_consistency`, `normalize_tags`, `log_tag_quality` | L426-630 | `validators/tags.py` |
| `validate_markdown_format`, `log_format_quality` | L411-425 | `validators/format.py` |

#### グループ D: 判定（config に依存）

| 関数 | 行番号 | 移行先 |
|------|--------|--------|
| `count_english_chars`, `count_total_letters`, `is_complete_english_document`, `log_english_detection` | L283-354 | `detection/english.py` |

#### グループ E: パイプライン（types, config, io, state に依存）

| 関数 | 行番号 | 移行先 |
|------|--------|--------|
| `load_prompt`, `call_llm_for_stage`, `set_stage_debug_mode`, `print_stage_debug` | L758-900 | `pipeline/prompts.py` |
| `pre_process`, `stage1_dust`, `stage2_genre`, `stage3_normalize`, `stage4_metadata`, `post_process` | L901-1200 | `pipeline/stages.py` |
| `log_pipeline_stage`, `run_pipeline` | L1201-1330 | `pipeline/runner.py` |

#### グループ F: 入出力（config に依存）

| 関数 | 行番号 | 移行先 |
|------|--------|--------|
| `read_file_content`, `write_file_content`, `list_index_files`, `get_destination_path` | L1500-1600 | `io/files.py` |
| `get_session_dir`, `get_state_files`, `get_log_file`, `create_new_session`, `load_latest_session`, `log_message`, `start_new_log_session` | L1601-1750 | `io/session.py` |
| `call_ollama`, `extract_json_from_code_block`, `extract_first_json_object`, `format_parse_error`, `parse_json_response` | L1751-1900 | `io/ollama.py` |

#### グループ G: 状態管理（config, types に依存）

| 関数 | 行番号 | 移行先 |
|------|--------|--------|
| `load_state`, `save_state`, `delete_state`, `create_initial_state`, `update_state` | L2200-2400 | `state/manager.py` |
| グローバル変数 `_current_session_dir`, `_cached_prompt`, `_stage_debug_mode`, `_excluded_files` | 各所 | `state/manager.py` |

#### グループ H: ファイル処理（ほぼ全てに依存）

| 関数 | 行番号 | 移行先 |
|------|--------|--------|
| `extract_date_from_filename`, `clean_filename`, `normalize_filename`, `build_normalized_file`, `normalize_file`, `process_single_file` | L1901-2100 | `processing/single.py` |
| `process_all_files`, `should_exclude`, `get_excluded_files`, `clear_excluded_files`, `cleanup_empty_folders` | L2101-2200 | `processing/batch.py` |

#### グループ I: 出力（types に依存）

| 関数 | 行番号 | 移行先 |
|------|--------|--------|
| `format_success_result`, `format_dust_result`, `format_review_result`, `format_error_result`, `format_skip_result`, `output_json_result`, `print_summary` | L2401-2600 | `output/formatters.py` |
| `show_diff`, `process_file_with_diff` | L2601-2700 | `output/diff.py` |
| `progress_bar`, `timestamp` | L2701-2750 | `output/formatters.py` |

#### グループ J: CLI（ほぼ全てに依存）

| 関数 | 行番号 | 移行先 |
|------|--------|--------|
| `create_parser` | L2751-2900 | `cli/parser.py` |
| `cmd_status`, `cmd_metrics`, `main` | L2901-3233 | `cli/commands.py` |

### 依存関係グラフ（簡略化）

```
config.py ← types.py
    ↑           ↑
    │           │
validators/ ←───┤
detection/ ←────┤
    ↑           │
    │           │
io/files.py ────┤
io/session.py ──┤
io/ollama.py ───┤
    ↑           │
    │           │
state/manager.py ←─┐
    ↑              │
    │              │
pipeline/prompts.py
pipeline/stages.py
pipeline/runner.py
    ↑
    │
processing/single.py
processing/batch.py
    ↑
    │
output/formatters.py
output/diff.py
    ↑
    │
cli/parser.py
cli/commands.py
    ↑
    │
ollama_normalizer.py (エントリポイント)
```

---

## Summary

| トピック | Decision | Rationale |
|----------|----------|-----------|
| 循環インポート | TYPE_CHECKING + types.py 集約 | 標準ライブラリで実現可能、実行時オーバーヘッドなし |
| グローバル状態 | StateManager シングルトン | 1箇所に集約、テスト容易性向上 |
| パッケージ構成 | フラット + サブパッケージ | 視覚的グループ化、独立テスト可能 |
| 移行順序 | A→B→C→D→E→F→G→H→I→J | 依存関係の方向に従い段階的移行 |

**All NEEDS CLARIFICATION items resolved.**
