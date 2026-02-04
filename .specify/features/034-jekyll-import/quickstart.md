# Quickstart: Jekyll ブログインポート

**Feature**: 034-jekyll-import
**Date**: 2026-01-25

## 概要

GitHub リポジトリの Jekyll ブログ（`_posts` 等）を Obsidian ナレッジベースにインポートする。

## 前提条件

- Python 3.11+
- git コマンド（PATH に存在）
- GitHub パブリックリポジトリ

## 基本的な使い方

### 1. GitHub からインポート

```bash
# 基本コマンド
make import INPUT=https://github.com/user/repo/tree/master/_posts PROVIDER=github

# 例: example-user のブログをインポート
make import INPUT=https://github.com/example-user/example-user.github.io/tree/master/_posts PROVIDER=github
```

### 2. オプション

```bash
# プレビュー（実際には処理しない）
make import INPUT=... PROVIDER=github DRY_RUN=1

# 件数制限
make import INPUT=... PROVIDER=github LIMIT=10

# Debug モード
make import INPUT=... PROVIDER=github DEBUG=1

# 組み合わせ
make import INPUT=... PROVIDER=github LIMIT=5 DEBUG=1 DRY_RUN=1
```

### 3. 直接実行

```bash
python -m src.etl import \
  --input https://github.com/user/repo/tree/master/_posts \
  --provider github \
  --debug \
  --limit 10
```

## 出力先

```
.staging/@session/YYYYMMDD_HHMMSS/import/
├── phase.json                    # 処理ステータス
├── extract/
│   ├── input/                    # clone した Markdown ファイル
│   └── output/                   # パース結果
├── transform/
│   └── output/                   # 変換後 Markdown
└── load/
    └── output/                   # 最終出力
        └── posts/                # Obsidian ノート

.staging/@index/github/           # インデックス（重複管理用）
```

## 変換例

### 入力

**ファイル名**: `2022-11-27-532.md`

```yaml
---
title: "propsの宣言のvalueの謎の？の意味"
draft: false
tags: ["react"]
private: false
slug: "60eb6716-a436-4885-9b37-d288c3ce2def"
date: "2020-01-20T15:12:41+09:00"
lastmod: "2020-01-20T15:12:41+09:00"
keywords: ["react","ベジプロ","プログ","プログラム"]
---

# 未解決
意味がわかりそうで分からない。
```

### 出力 (Obsidian)

**ファイル名**: `propsの宣言のvalueの謎の？の意味.md`

```yaml
---
title: propsの宣言のvalueの謎の？の意味
created: 2020-01-20
tags:
  - react
  - ベジプロ
  - プログ
  - プログラム
normalized: true
file_id: a1b2c3d4e5f6...
---

# 未解決
意味がわかりそうで分からない。
```

**抽出されたタグ**:
- frontmatter.tags: `react`
- frontmatter.keywords: `react`, `ベジプロ`, `プログ`, `プログラム`（重複排除後マージ）

**削除されたフィールド**:
- `draft`, `private`, `slug`, `lastmod`

## Resume モード

処理が中断された場合:

```bash
# セッション状態確認
make status SESSION=20260125_143052

# 続行
make import INPUT=... PROVIDER=github SESSION=20260125_143052

# 失敗したアイテムのリトライ
make retry SESSION=20260125_143052
```

## トラブルシューティング

| 問題 | 原因 | 解決策 |
|------|------|--------|
| `Invalid GitHub URL format` | URL 形式が不正 | `https://github.com/{owner}/{repo}/tree/{branch}/{path}` 形式を使用 |
| `git clone failed` | リポジトリが非公開または存在しない | URL を確認、パブリックリポジトリのみ対応 |
| `Empty directory` | 指定パスにファイルなし | パスを確認（`_posts` など） |
| `No Markdown files` | `.md` ファイルが見つからない | 対象ディレクトリを確認 |

## 終了コード

| Code | 意味 |
|------|------|
| 0 | 成功 |
| 1 | 一般エラー |
| 2 | 入力が見つからない |
| 3 | git clone エラー |
| 4 | 部分成功（一部失敗） |
| 5 | 全件失敗 |
