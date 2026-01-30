# Data Model: LLM Multi-Stage Processing

**Feature**: 007-llm-multi-stage
**Date**: 2026-01-13

## Entity Definitions

### PreProcessingResult

LLM呼び出し前のルールベース処理結果。

```python
class PreProcessingResult(TypedDict):
    is_empty: bool              # 空ファイル
    is_too_short: bool          # 50文字未満
    is_english_doc: bool        # 完全な英語文書
    english_score: float        # 英語判定スコア (0.0-1.0)
    extracted_date: str         # ファイル名から抽出した日付 (YYYY-MM-DD or "")
    has_template_markers: bool  # テンプレート残骸検出
    skip_reason: str | None     # スキップする場合の理由
```

**Validation Rules**:
- `is_empty` and `is_too_short` → 即座にdust扱い
- `is_english_doc` → Stage 3で翻訳をスキップ
- `has_template_markers` → 即座にdust扱い

---

### StageResult

各LLM処理段階の結果を表す汎用型。

```python
class StageResult(TypedDict):
    success: bool               # 処理成功
    data: dict                  # 段階固有の出力データ
    error: str | None           # エラーメッセージ
    retry_count: int            # リトライ回数
    raw_response: str | None    # LLMの生応答（デバッグ用）
```

---

### Stage1Result (Dust判定)

```python
class Stage1Result(TypedDict):
    is_dust: bool
    dust_reason: str | None
    confidence: float           # 0.0-1.0
```

**State Transitions**:
- `is_dust == True` → 処理終了、後続Stage不要
- `is_dust == False` → Stage 2へ進む

---

### Stage2Result (ジャンル分類)

```python
class Stage2Result(TypedDict):
    genre: Literal["エンジニア", "ビジネス", "経済", "日常", "その他", "dust"]
    confidence: float           # 0.0-1.0
    related_keywords: list[str] # 3-5個
```

**Validation Rules**:
- `genre` は6値のいずれか
- `confidence < 0.7` → @review送り候補
- `related_keywords` は最大5個

---

### Stage3Result (コンテンツ正規化)

```python
class Stage3Result(TypedDict):
    normalized_content: str     # 整形済み本文
    improvements_made: list[str] # 改善リスト
```

**Validation Rules**:
- `normalized_content` は空でない
- 既存frontmatterが含まれていないこと

---

### Stage4Result (タイトル・タグ生成)

```python
class Stage4Result(TypedDict):
    title: str                  # ファイル名に使用可能なタイトル
    tags: list[str]             # 3-5個のタグ
```

**Validation Rules**:
- `title` に禁止文字 `< > : " / \ | ? *` を含まない
- `title` は200文字以内
- `tags` は1-5個

---

### PipelineContext

処理パイプライン全体のコンテキスト。

```python
class PipelineContext(TypedDict):
    filepath: Path              # 処理対象ファイル
    original_content: str       # 元のファイル内容
    pre_result: PreProcessingResult
    stage1_result: StageResult | None
    stage2_result: StageResult | None
    stage3_result: StageResult | None
    stage4_result: StageResult | None
    final_result: NormalizationResult | None
    errors: list[str]           # 累積エラー
    processing_time_ms: int     # 処理時間
```

---

### NormalizationResult (既存・変更なし)

最終出力。現行と互換性維持。

```python
class NormalizationResult(TypedDict):
    genre: GenreType
    confidence: float
    is_dust: bool
    dust_reason: str | None
    related_keywords: list[str]
    frontmatter: Frontmatter
    normalized_content: str
    improvements_made: list[str]
    is_complete_english_doc: bool
```

---

## Entity Relationships

```
PreProcessingResult
       │
       ▼ (skip if dust)
Stage1Result ──────────────┐
       │                   │
       ▼ (if not dust)     │ (dust)
Stage2Result               │
       │                   │
       ▼                   │
Stage3Result               │
       │                   │
       ▼                   │
Stage4Result               │
       │                   │
       ▼                   ▼
  ┌────────────────────────────┐
  │    NormalizationResult     │
  │    (最終出力・互換維持)      │
  └────────────────────────────┘
```

---

## State Transitions

### ファイル処理状態

```
[Start]
   │
   ▼
[Pre-processing]
   │
   ├─ empty/too_short/template → [Dust] → [End]
   │
   ▼
[Stage 1: Dust判定]
   │
   ├─ is_dust=true → [Dust] → [End]
   │
   ▼
[Stage 2: ジャンル分類]
   │
   ├─ confidence < 0.7 → [Review候補]
   │
   ▼
[Stage 3: 正規化]
   │
   ▼
[Stage 4: タイトル/タグ]
   │
   ▼
[Post-processing]
   │
   ├─ validation pass → [Success] → [End]
   └─ validation fail → [Review] → [End]
```

### リトライ状態

```
[Stage N 実行]
   │
   ├─ success → [次Stage]
   │
   └─ failure
       │
       ├─ retry < 3 → [Stage N 再実行]
       │
       └─ retry >= 3 → [Default値適用] → [次Stage]
```

---

## Default Values (リトライ失敗時)

| Stage | Field | Default Value |
|-------|-------|---------------|
| Stage 1 | is_dust | `False` |
| Stage 1 | confidence | `0.5` |
| Stage 2 | genre | `"その他"` |
| Stage 2 | confidence | `0.5` |
| Stage 2 | related_keywords | `[]` |
| Stage 3 | normalized_content | 元のcontent |
| Stage 3 | improvements_made | `[]` |
| Stage 4 | title | ファイル名のstem |
| Stage 4 | tags | `[]` |
