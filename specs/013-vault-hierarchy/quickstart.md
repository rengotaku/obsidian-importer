# Quickstart: Vault配下ファイル階層化

**Feature**: 013-vault-hierarchy

## 概要

Vault（エンジニア等）のルート直下に散在するファイルを、LLMでサブフォルダに自動分類する。

## 前提条件

- Python 3.11+
- Ollama起動中（`gpt-oss:20b` モデル利用可能）
- venv有効化済み

## クイックスタート

### 1. プレビュー（ドライラン）

```bash
# エンジニアVaultの分類提案を確認
make hierarchy-preview VAULT=エンジニア

# または直接実行
.venv/bin/python .claude/scripts/hierarchy_organizer.py エンジニア
```

出力例:
```
[階層化プレビュー] エンジニア Vault
対象ファイル: 927件

ファイル名                        提案先              確信度
─────────────────────────────────────────────────────────
Dockerの基本.md                   Docker/             0.92
AWSのIAM設定.md                   AWS学習/            0.88
テストの書き方.md                 テスト・QA/         0.85
...

新規フォルダ提案: 3件
- Docker (15ファイル)
- Kubernetes (8ファイル)
- Python (22ファイル)
```

### 2. 実行（ファイル移動）

```bash
# 確認後、実際に移動
make hierarchy-execute VAULT=エンジニア

# 新規フォルダも作成する場合
.venv/bin/python .claude/scripts/hierarchy_organizer.py -x --new-folders エンジニア
```

### 3. 結果確認

```bash
# 移動ログを確認
cat @index/hierarchy_logs/20260115_143052.json

# Vaultのフォルダ構造を確認
tree エンジニア/ -d
```

## 主要コマンド

| コマンド | 説明 |
|----------|------|
| `make hierarchy-preview` | 全Vaultプレビュー |
| `make hierarchy-preview VAULT=xxx` | 指定Vaultプレビュー |
| `make hierarchy-execute` | 全Vault実行 |
| `make hierarchy-execute VAULT=xxx` | 指定Vault実行 |

## オプション

| オプション | 説明 |
|------------|------|
| `-n, --dry-run` | プレビューのみ（デフォルト） |
| `-x, --execute` | 実際に移動 |
| `-l N, --limit N` | N件のみ処理 |
| `-c 0.7, --confidence 0.7` | 確信度閾値（デフォルト0.5） |
| `--new-folders` | 新規フォルダ作成許可 |
| `-o file.csv` | 結果をファイル出力 |

## トラブルシューティング

### Ollamaに接続できない

```bash
# Ollamaの状態確認
curl http://localhost:11434/api/tags

# 起動
ollama serve
```

### 分類精度が低い

```bash
# 確信度閾値を上げる
.venv/bin/python .claude/scripts/hierarchy_organizer.py -c 0.7 エンジニア
```

### ロールバック

```bash
# 移動ログから元に戻す
.venv/bin/python .claude/scripts/hierarchy_organizer.py --rollback @index/hierarchy_logs/20260115_143052.json
```

## 関連ドキュメント

- [spec.md](./spec.md) - 機能仕様
- [data-model.md](./data-model.md) - データモデル
- [contracts/cli-interface.md](./contracts/cli-interface.md) - CLIインターフェース
- [contracts/llm-prompt.md](./contracts/llm-prompt.md) - LLMプロンプト仕様
