# Quickstart: ローカルLLM品質向上

**Date**: 2026-01-11
**Feature**: 003-llm-quality-enhancement

---

## Prerequisites

- Python 3.11+
- Ollama (gpt-oss:20b モデル)
- pytest（テスト用、オプション）

---

## Setup

### 1. Ollama確認

```bash
# Ollamaサービス確認
curl http://localhost:11434/api/tags

# モデル確認
ollama list | grep gpt-oss
```

### 2. ディレクトリ構造確認

```bash
cd /path/to/project

# 必要なディレクトリ
ls -la @index/     # 未整理ファイル
ls -la @dust/      # dust判定ファイル
ls -la @plan/      # セッション管理
ls -la @review/    # 要確認ファイル（新規作成）

# @reviewフォルダがなければ作成
mkdir -p @review
```

---

## Development Workflow

### ステップ1: タグ辞書の生成

```bash
# 既存Vaultからタグを抽出
python3 .claude/scripts/tag_extractor.py

# 確認
cat .claude/scripts/data/tag_dictionary.json | jq '.languages[:5]'
```

### ステップ2: 単一ファイルでテスト

```bash
# プレビューモード（移動なし）
python3 .claude/scripts/ollama_normalizer.py @index/test.md --preview

# 実際に処理
python3 .claude/scripts/ollama_normalizer.py @index/test.md
```

### ステップ3: バッチ処理

```bash
# プレビュー
python3 .claude/scripts/ollama_normalizer.py --preview

# 新規セッション開始
python3 .claude/scripts/ollama_normalizer.py --all --new

# 中断時の再開
python3 .claude/scripts/ollama_normalizer.py --all --resume
```

---

## Key Files

| ファイル | 役割 |
|---------|------|
| `.claude/scripts/ollama_normalizer.py` | メイン処理スクリプト |
| `.claude/scripts/tag_extractor.py` | タグ辞書抽出（新規） |
| `.claude/scripts/markdown_normalizer.py` | Markdown後処理（新規） |
| `.claude/scripts/prompts/normalizer_v2.txt` | 改善版プロンプト（新規） |
| `.claude/scripts/data/tag_dictionary.json` | タグ辞書（自動生成） |

---

## Testing

### ユニットテスト

```bash
# 全テスト実行
pytest .claude/scripts/tests/ -v

# 特定テスト
pytest .claude/scripts/tests/test_tag_extractor.py -v
pytest .claude/scripts/tests/test_markdown_normalizer.py -v
```

### 品質評価

```bash
# サンプルファイルで処理
python3 .claude/scripts/ollama_normalizer.py @index/sample1.md --json > result1.json

# Claude Opusとの比較（手動）
# 1. 同一ファイルをClaude Opusで処理
# 2. 出力を並べて評価
```

---

## Troubleshooting

### Ollama接続エラー

```bash
# サービス確認
systemctl status ollama
# または
ollama serve
```

### JSONパースエラー

- LLM出力が不正なJSON形式
- プロンプトのJSON形式指定を確認
- `--json`オプションで生の出力を確認

### 処理が遅い

- `API_TIMEOUT`を延長（デフォルト120秒）
- `API_DELAY`を短縮（デフォルト0.3秒）
- ファイル内容の`MAX_CONTENT_CHARS`を削減

---

## Configuration

### 環境変数

```bash
export OLLAMA_URL="http://localhost:11434/api/chat"
export OLLAMA_MODEL="gpt-oss:20b"
export CONFIDENCE_THRESHOLD="0.7"
```

### スクリプト内定数

```python
# ollama_normalizer.py
MAX_CONTENT_CHARS = 4000  # LLMに送る最大文字数
CONFIDENCE_THRESHOLD = 0.7  # 自動処理の閾値
API_TIMEOUT = 120  # 秒
API_DELAY = 0.3  # 連続呼び出し間隔
```

---

## Next Steps

1. `/speckit.tasks` でタスク分解
2. 各タスクを実装
3. テストで品質確認
4. サンプルで評価
