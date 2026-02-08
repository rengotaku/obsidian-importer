# Quickstart: Kedro 入力フロー修正

## 前提条件

- Python 3.11+
- Kedro 1.1.1
- Ollama サーバーがローカルで稼働中

## セットアップ

```bash
# リポジトリに移動
cd /data/projects/obsidian-importer

# 依存インストール（既存環境がある場合は不要）
pip install -e ".[dev]"
```

## 使い方

### Claude 会話インポート

```bash
# 1. Claude エクスポート ZIP を配置
cp ~/Downloads/data-2026-*.zip data/01_raw/claude/

# 2. パイプライン実行（デフォルト: claude）
kedro run

# または明示的に指定
kedro run --pipeline=import_claude
```

### ChatGPT 会話インポート

```bash
# 1. ChatGPT エクスポート ZIP を配置
cp ~/Downloads/chatgpt-export-*.zip data/01_raw/openai/

# 2. パイプライン実行
kedro run --pipeline=import_openai
```

### GitHub Jekyll ブログインポート

```bash
# URL を指定して実行
kedro run --pipeline=import_github \
  --params='{"github_url": "https://github.com/rengotaku/rengotaku.github.io/tree/master/test_posts"}'
```

### 冪等 Resume（再実行）

```bash
# 前回失敗した処理の再実行（同じコマンド）
kedro run

# 出力ファイルが存在するアイテムは自動スキップ
# LLM 呼び出しなど高コスト処理の不要な再実行を回避
```

## テスト

```bash
# 全テスト実行
make test

# カバレッジ
make coverage
```

## ディレクトリ構造

```
data/01_raw/
├── claude/          ← Claude エクスポート ZIP を配置
│   └── *.zip
├── openai/          ← ChatGPT エクスポート ZIP を配置
│   └── *.zip
└── github/          ← (使用しない: git clone で自動取得)
```

## トラブルシューティング

- **"No partitions found"**: `data/01_raw/{provider}/` に ZIP ファイルがあるか確認
- **"conversations.json not found"**: ZIP 内に `conversations.json` が直下にあるか確認
- **Ollama 接続エラー**: `ollama serve` が起動しているか確認
