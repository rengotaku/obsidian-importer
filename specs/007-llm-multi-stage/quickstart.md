# Quickstart: LLM Multi-Stage Processing

## Overview

`ollama_normalizer.py` のLLM処理を4段階に分割し、エラー率を38%から10%以下に削減する。

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     normalize_file()                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                        │
│  │ Pre-processing  │ ─── 空/短文/英語/テンプレート判定       │
│  │   (ルールベース)  │                                        │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼ (skip if dust)                                  │
│  ┌─────────────────┐                                        │
│  │  Stage 1: Dust  │ ─── LLM: 価値判定                      │
│  │     (LLM)       │                                        │
│  └────────┬────────┘                                        │
│           │ (if not dust)                                   │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Stage 2: Genre  │ ─── LLM: ジャンル分類                  │
│  │     (LLM)       │                                        │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │Stage 3: Normalize│ ─── LLM: コンテンツ整形               │
│  │     (LLM)       │                                        │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │Stage 4: Metadata│ ─── LLM: タイトル・タグ生成            │
│  │     (LLM)       │                                        │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Post-processing │ ─── 検証・修正                         │
│  │   (ルールベース)  │                                        │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │NormalizationResult│ ─── 現行互換の出力                   │
│  └─────────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Pre-processing (ルールベース)

```python
def pre_process(filepath: Path, content: str) -> PreProcessingResult:
    """LLM呼び出し前のルールベース処理"""
    # 空ファイル、短文、英語判定、日付抽出、テンプレート検出
```

### 2. Stage Functions (LLM)

```python
def stage1_dust(content: str, filename: str) -> StageResult:
    """Stage 1: Dust判定"""

def stage2_genre(content: str, filename: str, is_english: bool) -> StageResult:
    """Stage 2: ジャンル分類"""

def stage3_normalize(content: str, filename: str, genre: str, is_english: bool) -> StageResult:
    """Stage 3: コンテンツ正規化"""

def stage4_metadata(normalized_content: str, filename: str, genre: str) -> StageResult:
    """Stage 4: タイトル・タグ生成"""
```

### 3. Post-processing (ルールベース)

```python
def post_process(stage_results: dict, pre_result: PreProcessingResult) -> NormalizationResult:
    """検証・修正・最終結果生成"""
    # validate_title(), validate_tags(), validate_markdown_format()
```

## File Structure

```
.claude/scripts/
├── ollama_normalizer.py      # Main (modified)
├── prompts/
│   ├── normalizer_v2.txt     # Current (deprecated)
│   ├── stage1_dust.txt       # NEW
│   ├── stage2_genre.txt      # NEW
│   ├── stage3_normalize.txt  # NEW
│   └── stage4_metadata.txt   # NEW
└── tests/
    └── test_multi_stage.py   # NEW
```

## Usage

```bash
# 現行と同じCLI（内部処理のみ変更）
python ollama_normalizer.py

# プレビューモード
python ollama_normalizer.py --preview

# 詳細ログ
python ollama_normalizer.py --verbose
```

## Testing Strategy

1. **Unit Tests**: 各Stage関数の個別テスト
2. **Integration Tests**: パイプライン全体のテスト
3. **Regression Tests**: 既存エラーファイルでの検証

```bash
# 既存エラーファイルでテスト
pytest tests/test_multi_stage.py -v
```

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Error Rate | 38% | <10% |
| Dust Processing Time | N/A | 50% faster |
| Classification Accuracy | - | >95% |
