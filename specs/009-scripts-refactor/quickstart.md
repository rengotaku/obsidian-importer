# Quickstart: normalizer パッケージ開発ガイド

**Date**: 2026-01-14 | **Plan**: [plan.md](plan.md)

## 概要

`ollama_normalizer.py` のモジュール分割開発を始めるためのクイックスタートガイド。

---

## 環境セットアップ

```bash
# 作業ディレクトリに移動
cd /path/to/project/.claude/scripts

# Python バージョン確認（3.11+ 必須）
python3 --version

# 構文チェック
make check
```

---

## パッケージ構造の作成

### Step 1: ディレクトリ作成

```bash
mkdir -p normalizer/{validators,detection,pipeline,io,state,processing,output,cli}
touch normalizer/__init__.py
touch normalizer/{config,models}.py
touch normalizer/validators/__init__.py
touch normalizer/detection/__init__.py
touch normalizer/pipeline/__init__.py
touch normalizer/io/__init__.py
touch normalizer/state/__init__.py
touch normalizer/processing/__init__.py
touch normalizer/output/__init__.py
touch normalizer/cli/__init__.py
```

### Step 2: 基盤モジュール作成

**推奨順序**（依存関係に従う）:

1. `config.py` - 定数、パス定義
2. `models.py` - TypedDict、型定義 (旧 types.py)
3. `validators/` - 検証関数
4. `detection/` - 判定関数
5. `io/` - 入出力関数
6. `state/` - 状態管理
7. `pipeline/` - LLMパイプライン
8. `processing/` - ファイル処理
9. `output/` - 出力フォーマット
10. `cli/` - CLIパーサー・コマンド

---

## 移行パターン

### 定数の移行

```python
# Before (ollama_normalizer.py)
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gpt-oss:20b"

# After (normalizer/config.py)
"""設定値と定数"""
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gpt-oss:20b"
BASE_DIR = Path("/path/to/project")
# ...
```

### TypedDict の移行

```python
# Before (ollama_normalizer.py L633)
class PreProcessingResult(TypedDict):
    filename: str
    original_content: str
    ...

# After (normalizer/models.py)
"""型定義"""
from typing import TypedDict, Literal

GenreType = Literal["エンジニア", "ビジネス", "経済", "日常", "その他", "dust"]

class PreProcessingResult(TypedDict):
    filename: str
    original_content: str
    ...
```

### 関数の移行

```python
# Before (ollama_normalizer.py L355)
def validate_title(title: str) -> tuple[bool, list[str]]:
    ...

# After (normalizer/validators/title.py)
"""タイトル検証"""
from __future__ import annotations


def validate_title(title: str) -> tuple[bool, list[str]]:
    """タイトルの妥当性を検証

    Args:
        title: 検証対象のタイトル

    Returns:
        (is_valid, error_messages)
    """
    ...
```

---

## テスト実行

### 構文チェック

```bash
# 全ファイルの構文チェック
python3 -m py_compile normalizer/*.py
python3 -m py_compile normalizer/**/*.py
```

### 既存テスト

```bash
# フィクスチャテスト（リファクタリング前後で同一結果を確認）
make test-fixtures
```

### 個別モジュールテスト

```python
# 対話的テスト例
python3
>>> from normalizer.config import OLLAMA_URL, MODEL
>>> print(OLLAMA_URL)
http://localhost:11434/api/chat
>>> from normalizer.types import GenreType
>>> genre: GenreType = "エンジニア"
```

---

## インポートパターン

### パッケージ内部

```python
# 同一パッケージ内
from normalizer.config import BASE_DIR
from normalizer.types import PipelineContext

# サブパッケージ間
from normalizer.validators.title import validate_title
from normalizer.io.files import read_file_content
```

### 型チェック用インポート

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from normalizer.types import StageResult
```

### エントリポイント

```python
# ollama_normalizer.py (リファクタリング後)
#!/usr/bin/env python3
"""Obsidian @index ファイル正規化ツール"""

from normalizer.cli.commands import main

if __name__ == "__main__":
    raise SystemExit(main())
```

---

## トラブルシューティング

### ImportError: No module named 'normalizer'

```bash
# PYTHONPATH に追加
export PYTHONPATH=/path/to/project/.claude/scripts:$PYTHONPATH

# または実行時指定
python3 -c "import sys; sys.path.insert(0, '.'); from normalizer import main"
```

### 循環インポートエラー

1. `types.py` に型定義が集約されているか確認
2. `TYPE_CHECKING` ブロック内でのみ型インポートしているか確認
3. 実行時に必要なインポートは関数内で遅延インポート

### 既存テストの失敗

1. CLI オプションが完全に移行されているか確認
2. `make test-fixtures` で出力を比較
3. JSON 出力形式が一致しているか確認

---

## 参照ドキュメント

- [spec.md](spec.md) - 機能仕様
- [plan.md](plan.md) - 実装計画
- [research.md](research.md) - 技術調査
- [data-model.md](data-model.md) - 型定義
- [contracts/cli.md](contracts/cli.md) - CLI仕様
