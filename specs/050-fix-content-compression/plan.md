# Implementation Plan: 出力コンテンツの圧縮率改善

**Branch**: `050-fix-content-compression` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Issue #12 - Transform: 出力コンテンツの過度な圧縮（情報欠落）

## Summary

Transform パイプラインで LLM が会話から知識を抽出する際、出力コンテンツが過度に圧縮され情報が欠落する問題を修正する。プロンプト改善、圧縮率検証の共通処理、基準未達ファイルのレビューフォルダ出力を実装。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, requests (Ollama API)
**Storage**: ファイルシステム (JSON, JSONL, Markdown)、Kedro PartitionedDataset
**Testing**: unittest (Python 標準ライブラリ)
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: Single project (Kedro pipeline)
**Performance Goals**: 既存パイプラインと同等の処理速度
**Constraints**: LLM モデル変更なし、チャンク分割ロジック変更なし
**Scale/Scope**: 287ファイルの再変換テスト

## Constitution Check

*Constitution ファイルなし - スキップ*

## Project Structure

### Documentation (this feature)

```text
specs/050-fix-content-compression/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── pipelines/
│   ├── transform/
│   │   ├── nodes.py          # 【修正】extract_knowledge, format_markdown
│   │   └── pipeline.py
│   └── organize/
│       ├── nodes.py          # 【修正】embed_frontmatter_fields (review_reason)
│       └── pipeline.py
├── utils/
│   ├── prompts/
│   │   └── knowledge_extraction.txt  # 【修正】プロンプト改善
│   └── compression_validator.py      # 【新規】圧縮率検証共通処理
└── datasets/                         # 【修正】review フォルダ追加

tests/
├── pipelines/
│   └── transform/
│       └── test_nodes.py     # 【修正】圧縮率検証テスト
└── utils/
    └── test_compression_validator.py  # 【新規】

data/
└── 07_model_output/
    ├── notes/                # 既存
    ├── organized/            # 既存
    └── review/               # 【新規】基準未達ファイル
```

**Structure Decision**: 既存の Kedro パイプライン構造を維持。新規に `compression_validator.py` を追加し、全 transform node で共通利用。

## Complexity Tracking

*Constitution Check なし - 違反なし*

---

## Phase 0: Research

### 研究課題

1. **プロンプト改善のベストプラクティス**
   - 情報量保持を指示する効果的なプロンプト設計
   - LLM に最小出力量を指示する方法

2. **圧縮率検証の実装パターン**
   - Kedro node での共通処理実装パターン
   - デコレータ vs 関数呼び出し

3. **PartitionedDataset の出力先分岐**
   - 条件に応じた出力先変更の可否
   - review フォルダへの出力方法

---

## Phase 1: Design

### 1.1 プロンプト改善設計

**現状の問題**:
- `knowledge_extraction.txt` に情報量の目安がない
- 「構造化されたまとめ」という曖昧な指示

**改善内容**:

```text
## 情報量の目安

元の会話サイズに応じた最小出力量:
- 10,000文字以上の会話 → 最低1,000文字の「内容」セクション
- 5,000-10,000文字の会話 → 最低750文字の「内容」セクション
- 5,000文字未満の会話 → 最低500文字の「内容」セクション

## 省略禁止

以下は**絶対に省略しないでください**:
- コードブロック（完全な形で含める）
- 手順・ステップ（すべてのステップを含める）
- 設定ファイルの内容
- コマンド例

「詳細は省略」「以下同様」などの省略表現は使用禁止です。
```

### 1.2 圧縮率検証共通処理設計

**ファイル**: `src/obsidian_etl/utils/compression_validator.py`

```python
"""圧縮率検証ユーティリティ"""

from dataclasses import dataclass
from typing import Literal

@dataclass
class CompressionResult:
    """圧縮率検証結果"""
    original_size: int
    output_size: int
    body_size: int
    ratio: float  # output_size / original_size
    body_ratio: float  # body_size / original_size
    threshold: float
    is_valid: bool
    node_name: str

def get_threshold(original_size: int) -> float:
    """元サイズに応じたしきい値を返す"""
    if original_size >= 10000:
        return 0.10  # 10%
    elif original_size >= 5000:
        return 0.15  # 15%
    else:
        return 0.20  # 20%

def validate_compression(
    original_content: str,
    output_content: str,
    body_content: str | None,
    node_name: str,
) -> CompressionResult:
    """圧縮率を検証"""
    original_size = len(original_content)
    output_size = len(output_content)
    body_size = len(body_content) if body_content else output_size

    if original_size == 0:
        return CompressionResult(
            original_size=0,
            output_size=output_size,
            body_size=body_size,
            ratio=1.0,
            body_ratio=1.0,
            threshold=0.0,
            is_valid=True,
            node_name=node_name,
        )

    ratio = output_size / original_size
    body_ratio = body_size / original_size
    threshold = get_threshold(original_size)
    is_valid = body_ratio >= threshold

    return CompressionResult(
        original_size=original_size,
        output_size=output_size,
        body_size=body_size,
        ratio=ratio,
        body_ratio=body_ratio,
        threshold=threshold,
        is_valid=is_valid,
        node_name=node_name,
    )
```

### 1.3 レビューファイル出力設計

**frontmatter に追加するフィールド**:

```yaml
review_reason: "extract_knowledge: body_ratio=3.8% < threshold=10.0%"
```

**出力先**: `data/07_model_output/review/`

### 1.4 Node 修正設計

**extract_knowledge** (transform/nodes.py):
- `compression_validator.validate_compression()` を呼び出し
- 基準未達の場合: 警告ログ + item に `review_reason` フラグを追加
- 処理は継続（ブロックしない）

**format_markdown** (transform/nodes.py):
- `review_reason` がある場合: `data/07_model_output/review/` に出力
- 通常の場合: `data/07_model_output/notes/` に出力

**embed_frontmatter_fields** (organize/nodes.py):
- `review_reason` フィールドを frontmatter に埋め込み

### 1.5 DataCatalog 修正

**conf/base/catalog.yml** に追加:

```yaml
review_notes:
  type: PartitionedDataset
  path: data/07_model_output/review
  dataset:
    type: text.TextDataset
  filename_suffix: ".md"
```

---

## Implementation Phases (for /speckit.tasks)

### Phase 1: Setup
- Feature ブランチ確認
- 既存テスト通過確認

### Phase 2: プロンプト改善
- `knowledge_extraction.txt` に情報量目安・省略禁止ルール追加
- プロンプト変更のみ（コード変更なし）

### Phase 3: 圧縮率検証共通処理
- `compression_validator.py` 新規作成
- ユニットテスト作成

### Phase 4: Node 修正 (extract_knowledge)
- 圧縮率検証呼び出し追加
- 警告ログ追加
- `review_reason` フラグ追加

### Phase 5: レビューフォルダ出力
- DataCatalog 修正
- `format_markdown` 修正（出力先分岐）
- `embed_frontmatter_fields` 修正（review_reason 埋め込み）

### Phase 6: E2E テスト
- 圧縮率改善の検証
- レビューフォルダ出力の検証

### Phase 7: Polish
- ドキュメント更新
- コードレビュー
