# Quickstart: ジャンル定義の動的設定

**Date**: 2026-02-22
**Branch**: `060-dynamic-genre-config`

## 概要

この機能により、ジャンル定義をパラメータファイルで管理し、LLM プロンプトを動的に生成できます。また、other 分類が多い場合に新ジャンル候補を自動提案します。

## セットアップ

### 1. 設定ファイルの更新

`conf/local/parameters_organize.yml` を新形式に更新:

```yaml
organize:
  vault_base_path: "/path/to/your/Obsidian/Vaults"

  genre_vault_mapping:
    ai:
      vault: "エンジニア"
      description: "AI/機械学習/LLM/生成AI/Claude/ChatGPT"
    devops:
      vault: "エンジニア"
      description: "インフラ/CI/CD/クラウド/Docker/Kubernetes/AWS"
    # ... 他のジャンル
    other:
      vault: "その他"
      description: "上記に該当しないもの"

  conflict_handling: "skip"
```

### 2. パイプライン実行

```bash
make run
```

## 基本的な使い方

### ジャンルの追加

1. `conf/local/parameters_organize.yml` を編集
2. 新しいジャンルを追加:

```yaml
genre_vault_mapping:
  # 既存のジャンル...

  finance:
    vault: "経済"
    description: "投資/資産運用/金融商品/株式/債券"
```

3. `make run` を再実行

### ジャンル提案の確認

other 分類が5件以上ある場合、`make run` 完了後に提案レポートが生成されます:

```bash
cat data/07_model_output/genre_suggestions.md
```

提案を採用する場合:
1. レポートの `設定への追加例` をコピー
2. `conf/local/parameters_organize.yml` に追加
3. `make run` を再実行

## トラブルシューティング

### description がない場合

警告が出力されますが、ジャンル名のみで動作します:

```
WARNING: Genre 'finance' has no description, using genre name only
```

### vault が未定義の場合

エラーとなりパイプラインが停止します:

```
ERROR: Genre 'finance' has no vault defined
```

### genre_vault_mapping が空の場合

デフォルトで other のみにフォールバックします:

```
WARNING: genre_vault_mapping is empty, using 'other' only
```

## 設定例

### 技術系重視の設定

```yaml
genre_vault_mapping:
  ai:
    vault: "Tech/AI"
    description: "AI/機械学習/深層学習/LLM/生成AI"
  backend:
    vault: "Tech/Backend"
    description: "サーバーサイド/API/データベース/認証"
  frontend:
    vault: "Tech/Frontend"
    description: "React/Vue/CSS/UI/UX"
  devops:
    vault: "Tech/DevOps"
    description: "CI/CD/Docker/Kubernetes/AWS/GCP"
  other:
    vault: "Inbox"
    description: "未分類"
```

### シンプルな設定

```yaml
genre_vault_mapping:
  tech:
    vault: "Tech"
    description: "技術/プログラミング/AI/インフラ"
  life:
    vault: "Life"
    description: "日常/健康/旅行/趣味"
  other:
    vault: "Inbox"
    description: "未分類"
```
