# Quickstart: @index フォルダ内再帰的Markdown処理

**Feature**: 006-index-markdown-process
**Date**: 2026-01-12

## 概要

このfeatureは `ollama_normalizer.py` を拡張し、`@index/` フォルダ内のサブフォルダに含まれるMarkdownファイルも処理対象とする機能です。

## 変更点

### 1. ファイル検出の再帰化

**Before**:
```python
for f in INDEX_DIR.glob("*.md"):
```

**After**:
```python
for f in INDEX_DIR.rglob("*.md"):
    if not should_exclude(f):
        files.append(f)
```

### 2. 除外ロジックの追加

```python
def should_exclude(path: Path) -> bool:
    """
    パスが除外対象かどうかを判定

    除外条件:
    - パスの任意のコンポーネントが . で始まる（隠しファイル/フォルダ）
    """
    for part in path.relative_to(INDEX_DIR).parts:
        if part.startswith("."):
            return True
    return False
```

### 3. 処理前確認の追加

- ファイル数が20件以上の場合、処理前に確認プロンプトを表示
- `--force` オプションで確認をスキップ可能

## 使用方法

### 基本的な使用

```bash
# @index/ 以下のすべてのMarkdownを処理
python ollama_normalizer.py

# 処理前にファイル一覧を確認（ドライラン）
python ollama_normalizer.py status
```

### オプション

| オプション | 説明 |
|------------|------|
| `--force` | 確認プロンプトをスキップ |
| `--cleanup-empty` | 処理後に空になったサブフォルダを削除 |

## テスト

```bash
cd .claude/scripts
pytest tests/test_recursive_scan.py -v
```

### テストケース

1. サブフォルダ内ファイルの検出
2. 隠しファイル/フォルダの除外
3. 深い階層のファイル検出
4. 空フォルダの処理

## 注意事項

- 既存の処理ロジック（ジャンル判定、正規化、移動）は変更なし
- `.obsidian/` フォルダは自動的に除外される
- シンボリックリンクは `rglob()` のデフォルト動作で追跡されない（安全）
