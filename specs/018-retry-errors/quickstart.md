# Quickstart: エラーファイルのリトライ機能

**Date**: 2026-01-17
**Feature**: 018-retry-errors

## 概要

LLM インポート処理で発生したエラーファイルのみを再処理する機能。

## 前提条件

- 前回のインポートセッション（`import_*`）が存在する
- セッションの `errors.json` にエラーが記録されている

## 基本的な使い方

### 1. リトライ対象の確認

```bash
make retry
```

エラーを含むセッション一覧が表示される:

```
リトライ対象のセッション一覧:

  SESSION                      ERRORS  UPDATED
  import_20260116_203426       21      2026-01-17 00:37

SESSION を指定して実行してください:
  make retry SESSION=import_20260116_203426
```

### 2. プレビュー（任意）

```bash
make retry ACTION=preview SESSION=import_20260116_203426
```

リトライ対象のエラー詳細を確認できる。

### 3. リトライ実行

```bash
make retry SESSION=import_20260116_203426
```

### 4. 結果確認

新しいセッションが作成される:

```
.staging/@plan/import_20260117_120000/
├── session.json       # source_session が記録される
├── errors.json        # リトライでも失敗したもの
├── processed.json     # リトライで成功したもの
└── execution.log      # リトライ情報がヘッダーに記録
```

## オプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `SESSION=xxx` | 対象セッションを指定 | `SESSION=import_20260116_203426` |
| `ACTION=preview` | プレビューモード | 処理は実行されない |
| `TIMEOUT=N` | タイムアウト秒数 | `TIMEOUT=180`（デフォルト: 120） |

## ワークフロー例

```bash
# 1. 通常のインポートを実行
make llm-import

# 2. エラーがあればリトライ対象を確認
make retry

# 3. プレビューで対象を確認
make retry ACTION=preview SESSION=import_20260116_203426

# 4. リトライ実行
make retry SESSION=import_20260116_203426

# 5. まだエラーがあればタイムアウトを延長して再実行
make retry SESSION=import_20260117_120000 TIMEOUT=180
```

## トラブルシューティング

### エラー: セッションが見つからない

```
ERROR: セッション 'import_xxx' が見つかりません
```

→ `.staging/@plan/` 配下のセッションディレクトリを確認

### エラー: リトライ対象がない

```
リトライ対象のエラーがありません
```

→ 指定セッションの `errors.json` が空

### タイムアウトエラーが多い

→ `TIMEOUT` を増加させて再実行

```bash
make retry SESSION=xxx TIMEOUT=300
```
