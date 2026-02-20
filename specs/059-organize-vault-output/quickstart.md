# Quickstart: Organize パイプラインの Obsidian Vault 直接出力対応

**Date**: 2026-02-20
**Branch**: 059-organize-vault-output

## 前提条件

1. organized フォルダにファイルが存在すること

   ```bash
   ls data/07_model_output/organized/
   ```

2. Vault ベースパスが存在すること

   ```bash
   ls /home/takuya/Documents/Obsidian/Vaults/
   ```

3. 必要な Vault フォルダが作成済みであること

   ```bash
   # 必要に応じて作成
   mkdir -p /home/takuya/Documents/Obsidian/Vaults/{エンジニア,ビジネス,経済,日常,その他}
   ```

## 基本的な使い方

### Step 1: Preview（推奨）

実際にファイルをコピーする前に、出力先と競合を確認。

```bash
kedro run --pipeline=organize_preview
```

**出力例**:

```
Preview: Vault Output Summary
=============================
Total files: 50
Destination breakdown:
  エンジニア: 25 files
  ビジネス: 10 files
  日常: 12 files
  その他: 3 files

Conflicts detected: 3
  - /path/to/vault/エンジニア/python/file1.md (exists)
  - /path/to/vault/ビジネス/marketing/file2.md (exists)
  - /path/to/vault/日常/file3.md (exists)
```

### Step 2: Vault へコピー

確認後、実際にファイルをコピー。

```bash
kedro run --pipeline=organize_to_vault
```

**デフォルト動作**: 競合ファイルはスキップ

## 競合処理オプション

### Skip（デフォルト）

既存ファイルがある場合はスキップ。

```bash
kedro run --pipeline=organize_to_vault --params='{"organize.conflict_handling": "skip"}'
```

### Overwrite

既存ファイルを上書き。

```bash
kedro run --pipeline=organize_to_vault --params='{"organize.conflict_handling": "overwrite"}'
```

### Increment

別名で保存（file.md → file_1.md → file_2.md）。

```bash
kedro run --pipeline=organize_to_vault --params='{"organize.conflict_handling": "increment"}'
```

## 設定のカスタマイズ

### Vault ベースパスの変更

`conf/base/parameters.yml`:

```yaml
organize:
  vault_base_path: "/path/to/your/Obsidian/Vaults"
```

### Genre-Vault マッピングの変更

`conf/base/parameters.yml`:

```yaml
organize:
  genre_vault_mapping:
    ai: "エンジニア"
    devops: "エンジニア"
    engineer: "エンジニア"
    business: "ビジネス"
    economy: "経済"
    health: "日常"
    parenting: "日常"
    travel: "日常"
    lifestyle: "日常"
    daily: "日常"
    other: "その他"
```

## トラブルシューティング

### Vault ベースパスが存在しない

```
ERROR: Vault base path does not exist: /path/to/Vaults
```

**解決**: パスを確認し、存在するディレクトリを指定。

### 権限エラー

```
WARNING: Permission denied for /path/to/file.md, skipping
```

**解決**: 出力先ディレクトリの書き込み権限を確認。

### frontmatter に genre/topic がない

```
WARNING: No genre found in frontmatter for file.md, using 'other'
```

**解決**: organize パイプラインが正常に実行されたか確認。

## ワークフロー例

### 新規インポート → Vault 出力

```bash
# 1. Claude からインポート
kedro run --pipeline=import_claude

# 2. Preview で確認
kedro run --pipeline=organize_preview

# 3. Vault へコピー
kedro run --pipeline=organize_to_vault
```

### 既存ファイルの上書き更新

```bash
# 再インポート後、上書きモードでコピー
kedro run --pipeline=import_claude
kedro run --pipeline=organize_to_vault --params='{"organize.conflict_handling": "overwrite"}'
```
