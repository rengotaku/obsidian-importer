# Data Model: 出力ファイル品質改善

**Branch**: `049-output-quality-improve` | **Date**: 2026-02-08

## Overview

本 feature は既存の Kedro パイプラインを拡張するため、新規エンティティは最小限。主に既存エンティティの検証・変換ロジックを強化する。

## Entities

### 1. ValidationResult (新規)

検証結果を表現するデータクラス。

```python
from dataclasses import dataclass, field

@dataclass
class ValidationResult:
    """Result of content validation."""
    passed: bool
    skip_reason: str | None = None
    warnings: list[str] = field(default_factory=list)
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `passed` | `bool` | 検証通過フラグ |
| `skip_reason` | `str \| None` | スキップ理由（passed=False の場合） |
| `warnings` | `list[str]` | 警告メッセージリスト |

**Usage**:
- `extract_knowledge` ノードで `summary_content` の検証
- 今後の拡張で他の検証にも利用可能

### 2. ProcessedItem (既存 dict の検証強化)

既存の `ProcessedItem` dict に対する検証ルールを追加。

**既存構造**:
```python
ProcessedItem = {
    "file_id": str,
    "content": str,
    "source_provider": str,
    "created_at": str,
    "conversation_name": str | None,
    "generated_metadata": {
        "title": str,
        "summary": str,
        "summary_content": str,
        "tags": list[str]
    },
    "metadata": {
        "title": str,
        "created": str,
        "tags": list[str],
        "summary": str,
        "source_provider": str,
        "file_id": str,
        "normalized": bool
    }
}
```

**追加検証ルール**:

| Field | Validation | Action on Failure |
|-------|------------|-------------------|
| `generated_metadata.summary_content` | 非空チェック | アイテム除外 |
| `generated_metadata.title` | サニタイズ処理 | 問題文字除去 |
| `generated_metadata.summary` | 長さ警告 (>500) | 警告ログ |

## Validation Rules

### VR-001: Empty Content Validation

```python
def validate_content(summary_content: str | None) -> ValidationResult:
    """Validate summary_content is not empty."""
    if summary_content is None or not summary_content.strip():
        return ValidationResult(
            passed=False,
            skip_reason="empty_summary_content"
        )
    return ValidationResult(passed=True)
```

### VR-002: Summary Length Warning

```python
def validate_summary_length(summary: str) -> ValidationResult:
    """Check if summary exceeds recommended length."""
    warnings = []
    if len(summary) > 500:
        warnings.append(f"Summary length ({len(summary)}) exceeds 500 chars")
    return ValidationResult(passed=True, warnings=warnings)
```

### VR-003: Title Sanitization

```python
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE
)

def sanitize_title(title: str, file_id: str) -> str:
    """Sanitize title for use as filename."""
    # Remove emojis
    sanitized = EMOJI_PATTERN.sub("", title)

    # Remove unsafe chars including brackets and path chars
    unsafe_chars = r'[/\\:*?"<>|\[\]()~%]'
    sanitized = re.sub(unsafe_chars, "", sanitized)

    # Normalize whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    # Fallback to file_id
    if not sanitized:
        return file_id[:12]

    return sanitized[:250]
```

## State Transitions

```
ParsedItem (Extract)
    ↓
    ├─ [summary_content 空] → 除外 (ログ記録)
    │
    └─ [summary_content 非空]
        ↓
        ├─ [summary > 500] → 警告ログ出力
        │
        └─ ProcessedItem with generated_metadata
            ↓
            タイトルサニタイズ
            ↓
            Markdown 出力
```

## Integration Points

### Node: extract_knowledge

**Input**: `ParsedItem` (dict)
**Output**: `ProcessedItem` (dict with generated_metadata)

**Validation**:
1. LLM 抽出成功チェック (既存)
2. summary_content 非空チェック (新規 - FR-001)
3. summary 長さ警告 (新規 - FR-009)

### Node: format_markdown → _sanitize_filename

**Input**: `ProcessedItem.metadata.title`
**Output**: サニタイズ済みファイル名

**Transformation**:
1. 絵文字除去 (新規 - FR-003)
2. ブラケット除去 (新規 - FR-004)
3. パス記号除去 (新規 - FR-005)
4. 空タイトルフォールバック (既存強化 - FR-006)

## Metrics

各検証の結果はログに記録され、パイプライン終了時にサマリー表示:

```
extract_knowledge: total=100, skipped=5 (existing=2, file=3),
  processed=95, succeeded=90, failed=5, skipped_empty=3 ({node_time:.1f}s)
```

| Metric | Description |
|--------|-------------|
| `skipped_empty` | 空コンテンツでスキップされた件数 |
| `long_summary_warnings` | summary 長さ警告件数 |
