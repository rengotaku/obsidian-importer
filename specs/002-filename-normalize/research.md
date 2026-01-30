# Research: Filename Normalize

**Date**: 2026-01-10
**Branch**: `002-filename-normalize`

## Problem Analysis

### Current Implementation

現在の `/og:organize` コマンドは `.claude/scripts/ollama_normalizer.py` で実装されている。

#### 問題のあるコードフロー

```
process_single_file() (L426-525)
  ↓
new_filename = clean_filename(filepath.name)  (L475)
  ↓
dest_path = get_destination_path(norm_result["genre"], new_filename)  (L476)
```

#### `clean_filename()` の現在の動作 (L312-317)

```python
def clean_filename(filename: str) -> str:
    """ファイル名からJekyll形式の日付プレフィックスを除去"""
    import re
    # パターン: 2022-10-17-Title.md → Title.md
    cleaned = re.sub(r'^\d{4}[-_]\d{2}[-_]\d{2}[-_]', '', filename)
    return cleaned if cleaned else filename
```

**問題点**:
1. 日付除去後のハイフン（`Pull-a-docker-image`）がスペースに変換されない
2. Ollamaが生成した `frontmatter.title` がファイル名に反映されない

### Ollama の出力

Ollama は `NORMALIZER_SYSTEM_PROMPT` に従って以下を返す：

```json
{
  "frontmatter": {
    "title": "適切なタイトル",  // ← これがファイル名になるべき
    ...
  },
  ...
}
```

しかし現在の実装では `frontmatter.title` はファイル内容の YAML frontmatter にのみ使用され、**ファイル名は元のファイル名から派生**している。

## Solution Design

### Decision: Ollamaが生成したタイトルをファイル名として使用

**Rationale**:
- Ollamaは内容を理解した上で適切なタイトルを生成する
- 人間が読みやすい形式（日本語や自然な英語）で生成される
- frontmatter.title とファイル名の整合性が自動的に確保される

**Alternatives Considered**:

| 代替案 | 却下理由 |
|--------|---------|
| 正規表現でハイフンをスペースに変換 | 技術用語（`AWS-CLI`, `Node.js`）の扱いが困難 |
| ルールベースの変換ロジック | 複雑化、保守困難、エッジケース多い |
| 元ファイル名をそのまま使用 | ユーザーの要望に反する |

### 実装方針

#### 変更点 1: `normalize_filename()` 関数の新規追加

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
    # ファイルシステム禁止文字を置換
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        title = title.replace(char, '_')

    # 長さ制限
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0]  # 単語境界で切る

    return title.strip()
```

#### 変更点 2: `process_single_file()` の修正

**Before** (L475-476):
```python
new_filename = clean_filename(filepath.name)
dest_path = get_destination_path(norm_result["genre"], new_filename)
```

**After**:
```python
# Ollamaが生成したタイトルをファイル名として使用
title = norm_result["frontmatter"]["title"]
new_filename = normalize_filename(title) + ".md"
dest_path = get_destination_path(norm_result["genre"], new_filename)
```

#### 変更点 3: Ollamaプロンプトの微調整

現在のプロンプト（`NORMALIZER_SYSTEM_PROMPT`）に以下を追加：

```
- frontmatter.title: **ファイル名として使用される**ため、以下に注意:
  - ハイフン区切りではなくスペース区切りの自然な形式
  - ファイルシステム禁止文字（<>:"/\|?*）を含めない
  - 200文字以内
```

## Edge Cases Handling

| ケース | 対応方針 |
|--------|---------|
| 日付のみのファイル名 | Ollamaが内容からタイトル生成（既存動作） |
| 空タイトル生成 | 元ファイル名から日付除去したものを使用（フォールバック） |
| 禁止文字を含むタイトル | `normalize_filename()` で置換 |
| 長すぎるタイトル | 200文字で切り詰め（単語境界考慮） |
| 重複ファイル名 | 既存の `get_destination_path()` で `_1`, `_2` 付与 |

## Files to Modify

| ファイル | 変更内容 |
|----------|---------|
| `.claude/scripts/ollama_normalizer.py` | `normalize_filename()` 追加、`process_single_file()` 修正、`NORMALIZER_SYSTEM_PROMPT` 更新 |

## Risk Assessment

| リスク | 軽減策 |
|--------|--------|
| 既存処理済みファイルとの不整合 | 新規ファイルのみ影響、既存は変更なし |
| Ollamaのタイトル生成品質 | フォールバックロジック実装 |
| プロンプト変更による予期せぬ動作 | テストケースで検証 |

## Testing Strategy

1. **単体テスト**: `normalize_filename()` の各パターン
2. **統合テスト**: 実際のファイルで `/og:organize` 実行
3. **回帰テスト**: 既存の正常ケースが壊れていないこと

## References

- 既存実装: `.claude/scripts/ollama_normalizer.py`
- 仕様書: `specs/002-filename-normalize/spec.md`
- Constitution: `.specify/memory/constitution.md` - Principle III (Normalization First)
