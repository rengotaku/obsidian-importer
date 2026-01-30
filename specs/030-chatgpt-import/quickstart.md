# Quickstart: ChatGPT エクスポートインポート

**Created**: 2026-01-22

## 前提条件

- Python 3.13+ がインストール済み
- Ollama がローカルで起動中（`ollama serve`）
- ChatGPT エクスポート ZIP ファイルを取得済み

## セットアップ

```bash
# リポジトリルートに移動
cd /path/to/project

# 仮想環境の確認
source src/converter/.venv/bin/activate

# Ollama の起動確認
curl http://localhost:11434/api/tags
```

## ChatGPT エクスポートの取得

1. ChatGPT にログイン
2. Settings → Data controls → Export data
3. 「Export」をクリック
4. メールで届いた ZIP ファイルをダウンロード
5. `.staging/@llm_exports/chatgpt/` に配置

## 基本的な使い方

### インポート実行

```bash
# ChatGPT エクスポートをインポート
make import INPUT=.staging/@llm_exports/chatgpt/export.zip PROVIDER=openai

# または直接実行
python -m src.etl import \
  --input .staging/@llm_exports/chatgpt/export.zip \
  --provider openai
```

### オプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `--provider` | LLM プロバイダ | `openai`, `claude` |
| `--debug` | デバッグ出力有効 | `--debug` |
| `--dry-run` | 処理のプレビュー | `--dry-run` |
| `--limit` | 処理件数制限 | `--limit 10` |

### プレビューモード

```bash
# 処理内容を確認（ファイル出力なし）
make import INPUT=... PROVIDER=openai DRY_RUN=1
```

### デバッグモード

```bash
# 詳細ログを出力
make import INPUT=... PROVIDER=openai DEBUG=1
```

## 出力確認

### セッションフォルダ

```bash
# 最新セッションを確認
ls -la .staging/@session/

# 出力ファイルを確認
ls .staging/@session/YYYYMMDD_HHMMSS/import/load/output/conversations/
```

### ステータス確認

```bash
# セッション状態を表示
make status SESSION=YYYYMMDD_HHMMSS

# 全セッション一覧
make status ALL=1
```

## トラブルシューティング

### エラー: Ollama connection failed

```bash
# Ollama が起動しているか確認
pgrep ollama

# 起動
ollama serve
```

### エラー: ZIP ファイルが見つからない

```bash
# ファイルパスを確認
ls -la .staging/@llm_exports/chatgpt/

# 絶対パスで指定
make import INPUT=/full/path/to/export.zip PROVIDER=openai
```

### 失敗アイテムのリトライ

```bash
# 失敗したアイテムを再処理
make retry SESSION=YYYYMMDD_HHMMSS
```

## 次のステップ

1. **organize**: 生成されたファイルを Vault に振り分け

```bash
make organize INPUT=.staging/@session/YYYYMMDD_HHMMSS/import/load/output/conversations
```

2. **確認**: Obsidian で生成されたノートを確認
3. **クリーンアップ**: 古いセッションを削除

```bash
make session-clean DAYS=7
```
