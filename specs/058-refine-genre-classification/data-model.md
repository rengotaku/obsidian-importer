# Data Model: ETL ジャンル分類の細分化

**Date**: 2026-02-19
**Feature**: 058-refine-genre-classification

## Entities

### Genre

分類カテゴリを表す列挙型。

| 値 | 説明 | 例 |
|----|------|-----|
| `ai` | AI/ML、生成AI、機械学習 | Claude Code, Stable Diffusion |
| `devops` | インフラ、クラウド、CI/CD、コンテナ | Docker, Kubernetes, AWS |
| `engineer` | プログラミング、アーキテクチャ、一般的な技術 | Python, API設計 |
| `economy` | 投資、金融、経済ニュース | 株式投資, 経済政策 |
| `business` | ビジネス、マネジメント、キャリア | リーダーシップ, マーケティング |
| `health` | 健康、医療、フィットネス | 運動, 病気 |
| `parenting` | 子育て、育児、教育 | 赤ちゃん, キッザニア |
| `travel` | 旅行、観光 | 宮崎旅行, ホテル |
| `lifestyle` | 家電、生活用品、住居、DIY | 空気清浄機, 電子レンジ |
| `daily` | 日記、雑記、感想、趣味 | 日常の出来事 |
| `other` | 上記に該当しないコンテンツ | 雑多なトピック |

### GenreKeywords

各ジャンルに関連付けられたキーワードのマッピング。

```yaml
# Structure in parameters.yml
organize:
  genre_keywords:
    {genre_name}:
      - {keyword_1}
      - {keyword_2}
      ...
```

**フィールド**:
- `genre_name`: Genre 列挙値（string）
- `keywords`: キーワードリスト（list[string]）

### GenrePriority

ジャンル判定時の優先順位。

```yaml
# Structure in parameters.yml
organize:
  genre_priority:
    - ai        # 最優先
    - devops
    - engineer
    - economy
    - business
    - health
    - parenting
    - travel
    - lifestyle
    - daily     # 最低優先
    # other は含めない（デフォルト）
```

**ルール**:
- リストの先頭ほど優先度が高い
- `other` は優先順位リストに含めない（フォールバック）
- 設定されていないジャンルは無視される

### ClassifiedItem

分類済みのアイテム。

```python
{
    "metadata": {
        "title": str,
        "tags": list[str],
        "created": str,
        # ... other frontmatter fields
    },
    "content": str,  # Original Markdown content
    "genre": str,    # Classified genre (one of Genre values)
}
```

### GenreDistribution

ジャンル分布の統計情報（ログ出力用）。

```python
{
    "total": int,          # 総件数
    "distribution": {
        "ai": {"count": int, "percentage": float},
        "devops": {"count": int, "percentage": float},
        # ... all genres
        "other": {"count": int, "percentage": float},
    }
}
```

## State Transitions

### Classification Flow

```
Input (Markdown file)
    ↓
Parse Frontmatter & Content
    ↓
Extract Tags
    ↓
Match Keywords (Tags → Content)
    ↓
Apply Priority Order
    ↓
Assign Genre (first match wins)
    ↓
Output (ClassifiedItem)
```

## Validation Rules

1. **Genre**: 必ず11種のいずれかの値を持つ
2. **Keywords**: 空リストは許可（その場合マッチしない）
3. **Priority**: 重複は許可しない
4. **Percentage**: 0.0 〜 100.0 の範囲

## Relationships

```
GenreKeywords ──1:N──▶ Keyword
      │
      └──────────────▶ Genre ◀──────────── ClassifiedItem
                         ▲
GenrePriority ──ordered──┘
```

## Configuration Schema

### parameters.yml 追加構造

```yaml
organize:
  # Existing
  genre_keywords:
    engineer: [...]
    business: [...]
    economy: [...]
    daily: [...]
    # New genres
    ai: [...]
    devops: [...]
    health: [...]
    parenting: [...]
    travel: [...]
    lifestyle: [...]

  # New
  genre_priority:
    - ai
    - devops
    - engineer
    - economy
    - business
    - health
    - parenting
    - travel
    - lifestyle
    - daily
```
