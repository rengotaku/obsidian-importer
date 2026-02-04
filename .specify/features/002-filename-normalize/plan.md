# Implementation Plan: Filename Normalize

**Branch**: `002-filename-normalize` | **Date**: 2026-01-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-filename-normalize/spec.md`

## Summary

`/og:organize` コマンドの出力ファイル名を改善する。現在は Jekyll 形式の日付プレフィックスが残り、ハイフン区切りのままになる問題を解決。Ollama が生成したタイトルをファイル名として使用し、人間が読みやすい形式で保存する。

## Technical Context

**Language/Version**: Python 3.11+（標準ライブラリのみ）
**Primary Dependencies**: なし（urllib, json, re, pathlib のみ）
**Storage**: ファイルシステム（Obsidian Vault）
**Testing**: 手動テスト（pytest なし）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single script modification
**Performance Goals**: 既存と同等（1ファイル/2秒程度）
**Constraints**: Ollama API（gpt-oss:20b）への依存
**Scale/Scope**: 単一ファイル修正（約50行追加/変更）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | Vault構造に変更なし |
| II. Obsidian Markdown Compliance | ✅ Pass | frontmatter形式維持、normalized: true 設定 |
| III. Normalization First | ✅ Pass | **直接支援** - Jekyll形式のファイル名をタイトルのみに変換 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル分類ロジックに変更なし |
| V. Automation with Oversight | ✅ Pass | 既存の確認フローを維持 |

**Post-Design Re-check**: ✅ Pass - 設計がすべての原則に準拠していることを確認

## Project Structure

### Documentation (this feature)

```text
specs/002-filename-normalize/
├── plan.md              # This file
├── research.md          # Phase 0 output ✅
├── data-model.md        # Phase 1 output ✅
├── quickstart.md        # Phase 1 output ✅
├── checklists/
│   └── requirements.md  # Spec quality checklist ✅
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
.claude/scripts/
└── ollama_normalizer.py    # 修正対象（既存ファイル）
```

**Structure Decision**: 既存の単一スクリプト（`ollama_normalizer.py`）への修正のみ。新規ファイル作成なし。

## Implementation Details

### 変更点 1: `normalize_filename()` 関数の追加

**Location**: L318 付近（`clean_filename()` の後）

```python
def normalize_filename(title: str, max_length: int = 200) -> str:
    """
    タイトルからファイル名として使用可能な文字列を生成

    Args:
        title: Ollamaが生成したタイトル
        max_length: ファイル名の最大文字数

    Returns:
        正規化されたファイル名（拡張子なし）
    """
    if not title or not title.strip():
        return ""

    # ファイルシステム禁止文字を置換
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        title = title.replace(char, '_')

    # 連続する空白を1つに
    title = ' '.join(title.split())

    # 長さ制限
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0]

    return title.strip()
```

### 変更点 2: `process_single_file()` の修正

**Location**: L475-476

**Before**:
```python
new_filename = clean_filename(filepath.name)
dest_path = get_destination_path(norm_result["genre"], new_filename)
```

**After**:
```python
# Ollamaが生成したタイトルをファイル名として使用
title = norm_result["frontmatter"]["title"]
normalized_title = normalize_filename(title)

# フォールバック: タイトルが空の場合は元ファイル名から生成
if not normalized_title:
    fallback_name = clean_filename(filepath.stem)  # 拡張子なし
    normalized_title = fallback_name.replace('-', ' ')

new_filename = normalized_title + ".md"
dest_path = get_destination_path(norm_result["genre"], new_filename)
```

### 変更点 3: `NORMALIZER_SYSTEM_PROMPT` の更新

**Location**: L51-101

**追加内容**（`## 正規化ルール` セクションの `frontmatter.title` 説明を更新）:

```
- frontmatter.title: **ファイル名として使用される**ため、以下に注意:
  - ハイフン区切りではなくスペース区切りの自然な形式で記述
  - 日本語タイトルまたは自然な英語タイトルを推奨
  - ファイルシステム禁止文字（<>:"/\|?*）を含めない
  - 200文字以内
```

## Risk Assessment

| リスク | 確率 | 影響 | 軽減策 |
|--------|------|------|--------|
| Ollamaが不適切なタイトル生成 | 中 | 低 | フォールバックロジック実装済み |
| 既存ファイルとの重複 | 低 | 低 | 既存の `get_destination_path()` で対応 |
| 長すぎるタイトル | 低 | 低 | 200文字制限で対応 |

## Complexity Tracking

> Constitution Check に違反なし。追記不要。

## Related Documents

- [Specification](./spec.md)
- [Research](./research.md)
- [Data Model](./data-model.md)
- [Quickstart](./quickstart.md)
