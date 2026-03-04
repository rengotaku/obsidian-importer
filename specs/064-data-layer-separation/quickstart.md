# Quickstart: データレイヤー分離

**Feature**: 064-data-layer-separation
**Date**: 2026-03-03

## 概要

このガイドでは、`07_model_output/` の JSON/MD 混在を解消し、Kedro データレイヤー設計に準拠した構造へ移行する手順を説明します。

## 前提条件

- Python 3.11+
- venv 環境がアクティブ
- 既存データのバックアップ（推奨）

## 移行手順

### Step 1: 移行前確認（dry-run）

```bash
# 移行対象ファイルの確認
make migrate-data-layers-dry-run
```

出力例:
```
[DRY RUN] Migration Preview
----------------------------
classified/: 150 files → 05_model_input/classified/
cleaned/: 150 files → 05_model_input/cleaned/
normalized/: 150 files → 05_model_input/normalized/
----------------------------
Total: 450 files to migrate
```

### Step 2: 移行実行

```bash
# 実際の移行を実行
make migrate-data-layers
```

出力例:
```
Migration Complete
----------------------------
Migrated: 450 files
Skipped: 0 files (already exist)
Errors: 0
----------------------------
```

### Step 3: パイプライン実行テスト

```bash
# テスト実行
make test

# パイプライン実行（10件限定）
kedro run --params='{"import.limit": 10}'
```

### Step 4: 検証

```bash
# 07_model_output に JSON がないことを確認
find data/07_model_output -name "*.json" | wc -l
# 期待値: 0

# 05_model_input に JSON があることを確認
find data/05_model_input -name "*.json" | wc -l
# 期待値: 450 以上
```

## ロールバック手順

問題が発生した場合:

```bash
# バックアップから復元（バックアップがある場合）
cp -r data.backup/07_model_output data/

# または、05_model_input から 07_model_output に戻す
# （移行スクリプトの逆操作）
```

## よくある質問

### Q: 移行後もパイプラインは同じように動きますか？

A: はい。catalog.yml のパス変更のみで、パイプラインのロジックは変更されません。

### Q: 既存の Markdown ファイルはどうなりますか？

A: `07_model_output/` の Markdown ファイルはそのまま維持されます。移行対象は JSON ファイルのみです。

### Q: 05_model_input はなぜこの名前？

A: Kedro の公式レイヤー規約に従っています。「モデル（LLM）への入力データ」を意味します。

## 関連コマンド

```bash
# Makefile ターゲット一覧
make help

# パイプライン可視化
make kedro-viz

# テスト実行
make test

# lint チェック
make lint
```
