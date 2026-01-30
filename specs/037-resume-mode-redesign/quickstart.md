# Quickstart: Resume モードの再設計

## 概要

Resume モードにより、中断したインポート処理を効率的に再開できます。
処理済みアイテムは自動的にスキップされ、LLM 呼び出しの重複コストを回避します。

## 基本的な使い方

### 1. 通常のインポート実行

```bash
# Claude エクスポートをインポート
make import INPUT=~/.staging/@llm_exports/claude/

# ChatGPT エクスポートをインポート
make import INPUT=chatgpt_export.zip PROVIDER=openai
```

実行後、セッション ID が表示されます:
```
[Session] 20260126_100000 created
[Phase] import started (provider: claude)
[Phase] import completed (50 success, 5 failed)
```

### 2. 中断からの再開（Resume モード）

セッション ID のみを指定して再実行:

```bash
make import SESSION=20260126_100000
```

出力:
```
[Session] 20260126_100000 (reused)
[Resume] Detected provider: claude
[Phase] import completed (10 success, 0 failed, 45 skipped)
```

### 3. 失敗アイテムのリトライ

Resume モードでは、前回失敗したアイテムも自動的にリトライされます:

```bash
# 前回 5 件失敗した場合
make import SESSION=20260126_100000

# 出力: LLM タイムアウト等の一時的エラーなら成功する可能性あり
[Phase] import completed (3 success, 2 failed, 50 skipped)
```

## コマンドリファレンス

### import コマンド

```bash
python -m src.etl import --session SESSION_ID [--limit N]
```

| オプション | 説明 |
|-----------|------|
| `--session` | 既存セッション ID（Resume モード） |
| `--limit` | 処理件数制限（デフォルト: 無制限） |
| `--dry-run` | プレビューモード（処理しない） |
| `--no-fetch-titles` | URL タイトル取得を無効化 |
| `--chunk` | 大規模ファイルのチャンク分割を有効化 |

### status コマンド

```bash
python -m src.etl status --session SESSION_ID
```

セッションの処理状況を確認:
```
Session: 20260126_100000
Status: partial

Phase: import
  Success: 50
  Failed: 5
  Skipped: 0
```

## 動作原理

### ステージ別スキップ戦略

| ステージ | スキップ単位 | 理由 |
|---------|------------|------|
| Extract | Stage 単位 | 軽量処理（ファイル読み込み） |
| Transform | アイテム単位 | LLM 呼び出し（コスト大） |
| Load | アイテム単位 | 効率化のため |

### スキップ判定

1. `pipeline_stages.jsonl` から `status="success"` のアイテムを読み込み
2. 入力アイテムの `item_id` がキャッシュに存在するかチェック
3. 存在する場合はスキップ（ログには記録しない）
4. 存在しない場合は処理を実行

### 統計の算出

- **成功数**: `pipeline_stages.jsonl` の `status="success"` 件数
- **失敗数**: `pipeline_stages.jsonl` の `status="failed"` 件数
- **スキップ数**: 入力数 - (成功数 + 失敗数 + 今回処理数)

## トラブルシューティング

### Q: セッションが見つからない

```
[Error] Session not found: 20260126_100000
```

**原因**: 指定したセッション ID が存在しない

**対処**:
```bash
# 利用可能なセッション一覧を確認
make status ALL=1
```

### Q: 入力ファイルが見つからない

```
[Error] No input files in session: 20260126_100000
```

**原因**: セッションの `extract/input/` フォルダが空

**対処**: 新規セッションで再インポート
```bash
make import INPUT=path/to/export/
```

### Q: 全件スキップされる

```
[Phase] import completed (0 success, 0 failed, 100 skipped)
```

**原因**: 全アイテムが既に処理済み

**確認方法**:
```bash
# セッション状態を確認
make status SESSION=20260126_100000 JSON=1
```

### Q: ログファイルが破損している

警告が表示されるが、処理は継続されます:
```
[Warning] Failed to parse pipeline_stages.jsonl line 123
```

破損したレコードは無視され、読み込み可能なレコードのみ使用されます。

## パフォーマンス

- **ログ読み込み**: 1000件で <1秒
- **メモリ使用**: 10000アイテムで <1MB
- **LLM 呼び出し**: 処理済みアイテムに対して 0回（100%削減）

## 変更点サマリー

### v2.0（本リリース）

- Resume モードのステージ別スキップ戦略
- DEBUG モード廃止（ログ出力が通常動作に昇格）
- スキップアイテムはログに記録しない
- コンソール出力にスキップ数を表示
