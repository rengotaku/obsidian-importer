# Data Model: Scripts コードリファクタリング

**Date**: 2026-01-14 | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

## Overview

`ollama_normalizer.py` から抽出する型定義を `normalizer/types.py` に集約。
全 TypedDict は既存コードから移行、新規型は追加しない（純粋リファクタリング）。

---

## Core Types (`normalizer/types.py`)

### ジャンル型

```python
from typing import Literal

GenreType = Literal["エンジニア", "ビジネス", "経済", "日常", "その他", "dust"]
```

### パイプライン関連

```python
from typing import TypedDict

class PreProcessingResult(TypedDict):
    """前処理結果"""
    filename: str
    original_content: str
    has_frontmatter: bool
    truncated: bool
    char_count: int

class StageResult(TypedDict):
    """ステージ共通結果"""
    success: bool
    stage: str
    message: str
    data: dict

class Stage1Result(TypedDict):
    """dust判定ステージ結果"""
    is_dust: bool
    confidence: float
    reason: str

class Stage2Result(TypedDict):
    """ジャンル分類ステージ結果"""
    genre: GenreType
    confidence: float
    reasoning: str

class Stage3Result(TypedDict):
    """正規化ステージ結果"""
    title: str
    tags: list[str]
    summary: str
    body: str

class Stage4Result(TypedDict):
    """メタデータ生成ステージ結果"""
    frontmatter: str
    final_content: str

class PipelineContext(TypedDict):
    """パイプライン実行コンテキスト"""
    file_path: str
    original_content: str
    preprocessed: PreProcessingResult
    stage1: Stage1Result | None
    stage2: Stage2Result | None
    stage3: Stage3Result | None
    stage4: Stage4Result | None
```

### ファイル処理関連

```python
class Frontmatter(TypedDict):
    """YAMLフロントマター"""
    title: str
    tags: list[str]
    created: str
    normalized: bool

class NormalizationResult(TypedDict):
    """正規化処理結果"""
    success: bool
    original_path: str
    destination_path: str | None
    genre: GenreType | None
    frontmatter: Frontmatter | None
    error: str | None

class ProcessingResult(TypedDict):
    """単一ファイル処理結果"""
    status: Literal["success", "dust", "review", "error", "skip"]
    file_path: str
    genre: GenreType | None
    destination: str | None
    message: str
    details: dict

class ScanResult(TypedDict):
    """バッチスキャン結果"""
    total_files: int
    processed: int
    success: int
    dust: int
    review: int
    error: int
    skip: int
    files: list[ProcessingResult]
```

---

## Entity Relationships

```
PipelineContext
├── PreProcessingResult (1:1)
├── Stage1Result (1:1, nullable)
├── Stage2Result (1:1, nullable)
├── Stage3Result (1:1, nullable)
└── Stage4Result (1:1, nullable)

ProcessingResult
├── GenreType (optional)
└── NormalizationResult (embedded in details)

ScanResult
└── ProcessingResult (1:N)
```

---

## State Types (`normalizer/state/manager.py`)

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ProcessingState:
    """処理状態（JSONシリアライズ対象）"""
    session_id: str
    started_at: str
    processed_files: list[str]
    pending_files: list[str]
    results: dict[str, ProcessingResult]

class StateManager:
    """グローバル状態管理（シングルトン）"""
    session_dir: Path | None
    cached_prompt: str | None
    stage_debug_mode: bool
    excluded_files: list[tuple[Path, str]]
```

---

## Validation Rules

### タイトル検証（`validators/title.py`）

| ルール | 条件 |
|--------|------|
| 最大長 | 100文字以下 |
| 禁止文字 | `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `\|` |
| 必須 | 空文字列禁止 |

### タグ検証（`validators/tags.py`）

| ルール | 条件 |
|--------|------|
| 最大数 | 10個以下 |
| フォーマット | 小文字英数字、ハイフン、スラッシュ |
| 禁止 | インラインハッシュタグ（#tag形式） |
| 辞書照合 | `data/tag_dictionary.json` で既知タグ優先 |

### フォーマット検証（`validators/format.py`）

| ルール | 条件 |
|--------|------|
| 見出し開始 | `##` から開始（`#` は frontmatter title 用） |
| 空行 | 連続2行以上禁止 |
| リスト記号 | `-` を使用（`*`, `+` は非推奨） |

---

## Migration Notes

- 全 TypedDict は既存定義をそのまま移行
- `GenreType` は現在 `str` alias だが、`Literal` に強化
- `ProcessingState` は既存 JSON 構造と互換性維持
- 型ヒントの厳密化は将来課題（本リファクタリングのスコープ外）
