# Data Model: ジャンル定義の動的設定

**Date**: 2026-02-22
**Branch**: `060-dynamic-genre-config`

## Entities

### GenreDefinition

ジャンルの定義情報。`genre_vault_mapping` の各エントリに対応。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key | string | Yes | ジャンル識別子（小文字英字、例: `ai`, `devops`） |
| vault | string | Yes | 出力先 Vault 名（例: `エンジニア`） |
| description | string | No | LLM への分類ヒント（例: `AI/機械学習/LLM`） |

**Validation Rules**:
- key: `^[a-z][a-z0-9_]*$` (小文字英字で始まり、英数字とアンダースコアのみ)
- vault: 空文字列不可
- description: 空の場合は key をそのまま使用

**State Transitions**: なし（設定ファイルで静的定義）

### GenreSuggestion

新ジャンルの提案情報。other 分析結果として生成。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| suggested_genre | string | Yes | 提案されるジャンル名 |
| suggested_description | string | Yes | 提案される description |
| sample_titles | list[string] | Yes | 該当コンテンツのタイトル例（最大5件） |
| content_count | int | Yes | 該当コンテンツ数 |

**Validation Rules**:
- suggested_genre: 既存ジャンルと重複しないこと
- content_count: >= 1

### OrganizeParameters

organize パイプラインのパラメータ。Kedro conf から読み込み。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| vault_base_path | string | Yes | Vault のベースパス |
| genre_vault_mapping | dict[str, GenreDefinition] | Yes | ジャンル定義のコレクション |
| conflict_handling | string | No | 競合処理モード（default: `skip`） |

## Configuration Schema

### 新形式（genre_vault_mapping）

```yaml
organize:
  vault_base_path: "/path/to/Obsidian/Vaults"

  genre_vault_mapping:
    ai:
      vault: "エンジニア"
      description: "AI/機械学習/LLM/生成AI/Claude/ChatGPT"
    devops:
      vault: "エンジニア"
      description: "インフラ/CI/CD/クラウド/Docker/Kubernetes/AWS"
    engineer:
      vault: "エンジニア"
      description: "プログラミング/アーキテクチャ/API/データベース"
    business:
      vault: "ビジネス"
      description: "ビジネス/マネジメント/リーダーシップ/マーケティング"
    economy:
      vault: "経済"
      description: "経済/投資/金融/市場"
    health:
      vault: "日常"
      description: "健康/医療/フィットネス/運動"
    parenting:
      vault: "日常"
      description: "子育て/育児/教育/幼児"
    travel:
      vault: "日常"
      description: "旅行/観光/ホテル"
    lifestyle:
      vault: "日常"
      description: "家電/DIY/住居/生活用品"
    daily:
      vault: "日常"
      description: "日常/趣味/雑記"
    other:
      vault: "その他"
      description: "上記に該当しないもの"

  conflict_handling: "skip"
```

## Output Schema

### genre_suggestions.md

```markdown
# ジャンル提案レポート

**生成日時**: YYYY-MM-DD HH:MM:SS
**other 分類数**: N件
**提案数**: M件

---

## 提案 1: {suggested_genre}

**Description**: {suggested_description}

**該当コンテンツ** ({content_count}件):
- {sample_titles[0]}
- {sample_titles[1]}
- ...

**設定への追加例**:
```yaml
{suggested_genre}:
  vault: "適切なVault名"
  description: "{suggested_description}"
```

---

## 提案なし

other 分類が5件未満のため、新ジャンルの提案はありません。
```

## Relationships

```
OrganizeParameters
    └── genre_vault_mapping: dict
            └── GenreDefinition (per genre key)

GenreSuggestion (output only, not stored)
    └── generated from other-classified content
```
