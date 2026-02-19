# Quickstart: Frontmatter ファイル振り分けスクリプト

**Feature Branch**: `057-frontmatter-file-organizer`

## 前提条件

1. Python 3.11+ がインストール済み
2. venv がセットアップ済み（`make setup`）
3. ETL パイプラインで処理済みファイルが `data/07_model_output/organized/` に存在

## セットアップ

### 1. 設定ファイルの作成

```bash
# サンプルから設定ファイルをコピー
cp conf/base/genre_mapping.yml.sample conf/base/genre_mapping.yml

# 必要に応じて編集
vim conf/base/genre_mapping.yml
```

### 2. 出力先ディレクトリの確認

デフォルトの出力先: `~/Documents/Obsidian/Vaults`

```bash
# 出力先が存在することを確認（または作成）
mkdir -p ~/Documents/Obsidian/Vaults
```

## 使用方法

### プレビューモード（推奨: 最初に実行）

```bash
# 振り分け計画を確認（ファイルは移動しない）
make organize-preview
```

出力例:
```
═══════════════════════════════════════════════════════════
  Organize Preview (dry-run)
═══════════════════════════════════════════════════════════

Input:  data/07_model_output/organized
Output: ~/Documents/Obsidian/Vaults

Genre Distribution:
  エンジニア:  45 files
  ビジネス:    12 files
  経済:        23 files
  日常:         8 files
  その他:       5 files
  unclassified: 2 files

Folder Status:
  ✅ エンジニア/      (exists)
  ✅ ビジネス/        (exists)
  ⚠️ 経済/            (will be created)
  ✅ 日常/            (exists)
  ✅ その他/          (exists)
  ⚠️ unclassified/    (will be created)

Total: 95 files ready to organize
```

### 実行モード

```bash
# 実際にファイルを振り分け
make organize
```

出力例:
```
═══════════════════════════════════════════════════════════
  Organizing Files
═══════════════════════════════════════════════════════════

Processing 95 files...
  ✅ 90 files moved successfully
  ⚠️  3 files skipped (already exist)
  ❌  2 files failed (see errors below)

Errors:
  - invalid_frontmatter.md: YAML parse error
  - corrupted.md: Unable to read file

═══════════════════════════════════════════════════════════
  ✅ Organization complete
═══════════════════════════════════════════════════════════
```

### カスタムパスの指定

```bash
# 入力パスを変更
make organize-preview INPUT=/path/to/custom/input

# 出力パスを変更
make organize OUTPUT=/path/to/custom/output

# 両方を変更
make organize INPUT=/path/to/input OUTPUT=/path/to/output
```

## 設定ファイル形式

`conf/base/genre_mapping.yml`:

```yaml
# Genre English -> Japanese folder name mapping
genre_mapping:
  engineer: エンジニア
  business: ビジネス
  economy: 経済
  daily: 日常
  other: その他

# Default paths
default_input: data/07_model_output/organized
default_output: ~/Documents/Obsidian/Vaults

# Folder for files without genre/topic
unclassified_folder: unclassified
```

## トラブルシューティング

### 設定ファイルが見つからない

```
Error: Configuration file not found: conf/base/genre_mapping.yml

Setup instructions:
  cp conf/base/genre_mapping.yml.sample conf/base/genre_mapping.yml
```

→ セットアップ手順に従って設定ファイルを作成

### 入力ディレクトリが空

```
No files found in data/07_model_output/organized

Hint: Run the ETL pipeline first:
  make run
```

→ 先に Kedro パイプラインを実行

### 同名ファイルが存在

```
⚠️ Skipped: example.md (already exists at ~/Documents/Obsidian/Vaults/経済/スマートフォン/)
```

→ 既存ファイルは上書きされません。手動で確認してください。

## ワークフロー例

```bash
# 1. ETL パイプラインでファイルを処理
make run

# 2. 振り分け計画を確認
make organize-preview

# 3. 問題なければ実行
make organize
```
