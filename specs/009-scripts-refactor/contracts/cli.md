# CLI Contract: ollama_normalizer.py

**Date**: 2026-01-14 | **Plan**: [../plan.md](../plan.md)

## Overview

リファクタリング後も完全互換を維持するCLIインターフェース仕様。
既存の全オプションとサブコマンドを同一の動作で提供する。

---

## Entry Point

```bash
python3 ollama_normalizer.py [OPTIONS] [FILE]
```

または

```bash
python3 -m normalizer [OPTIONS] [FILE]
```

---

## Global Options

| オプション | 短縮 | 型 | デフォルト | 説明 |
|-----------|------|-----|----------|------|
| `--help` | `-h` | flag | - | ヘルプ表示 |
| `--version` | `-V` | flag | - | バージョン表示 |
| `--verbose` | `-v` | flag | false | 詳細ログ出力 |
| `--json` | `-j` | flag | false | JSON形式で出力 |
| `--dry-run` | - | flag | false | 実際のファイル操作を行わない |

---

## Subcommands / Modes

### 単一ファイル処理（デフォルト）

```bash
python3 ollama_normalizer.py <FILE> [OPTIONS]
```

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|----------|------|
| `--preview` | flag | false | プレビューモード（移動なし） |
| `--diff` | flag | false | 変更内容をdiff形式で表示 |
| `--force` | flag | false | 確認なしで処理 |

**出力例（標準）**:
```
✅ tech_document.md → エンジニア/tech_document.md
   Tags: [python, programming]
   Confidence: 0.95
```

**出力例（JSON）**:
```json
{
  "status": "success",
  "file_path": "tech_document.md",
  "genre": "エンジニア",
  "destination": "エンジニア/tech_document.md",
  "confidence": 0.95
}
```

### バッチ処理

```bash
python3 ollama_normalizer.py --all [OPTIONS]
```

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|----------|------|
| `--all` | flag | - | @index内の全ファイルを処理 |
| `--preview` | flag | false | プレビューモード |
| `--reset` | flag | false | 状態をリセットして再処理 |
| `--limit` | int | 0 | 処理ファイル数上限（0=無制限） |

### 状態確認

```bash
python3 ollama_normalizer.py --status
```

| オプション | 型 | 説明 |
|-----------|-----|------|
| `--status` | flag | 現在の処理状態を表示 |
| `--metrics` | flag | 処理統計を表示 |

**出力例**:
```
📊 Processing Status
───────────────────
Session: 2026-01-14_1430
Processed: 15/42 files
Success: 12
Dust: 2
Review: 1
```

---

## Exit Codes

| コード | 意味 |
|--------|------|
| 0 | 成功 |
| 1 | 一般エラー |
| 2 | 引数エラー |
| 3 | ファイル不在 |
| 4 | Ollama接続エラー |
| 5 | 処理中断（Ctrl+C） |

---

## Environment Variables

| 変数 | デフォルト | 説明 |
|------|----------|------|
| `OLLAMA_URL` | `http://localhost:11434/api/chat` | Ollama APIエンドポイント |
| `OLLAMA_MODEL` | `gpt-oss:20b` | 使用モデル |
| `NORMALIZER_DEBUG` | `0` | デバッグモード（1で有効） |

---

## Internal Module API

### `normalizer.cli.commands.main()`

エントリポイント関数。`sys.argv` を解析して適切なコマンドを実行。

```python
def main() -> int:
    """CLI エントリポイント

    Returns:
        exit code (0: success, non-zero: error)
    """
```

### `normalizer.cli.parser.create_parser()`

argparse パーサーを構築。

```python
def create_parser() -> argparse.ArgumentParser:
    """CLI引数パーサーを作成

    Returns:
        設定済みの ArgumentParser
    """
```

---

## Backward Compatibility

以下の既存Makefileターゲットが動作することを保証：

| ターゲット | コマンド | 動作 |
|-----------|---------|------|
| `make status` | `python3 ollama_normalizer.py --status` | 状態表示 |
| `make preview` | `python3 ollama_normalizer.py --preview` | プレビュー |
| `make all` | `python3 ollama_normalizer.py --all` | 全処理 |
| `make reset` | `python3 ollama_normalizer.py --all --reset` | リセット+処理 |
| `make single FILE=...` | `python3 ollama_normalizer.py <FILE>` | 単一処理 |
| `make test-fixtures` | 各フィクスチャで `--preview --diff` | テスト |
