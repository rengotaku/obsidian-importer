# Data Model: Normalizer Pipeline統合

**Feature**: 014-pipeline-consolidation
**Date**: 2026-01-15

## Entities

### StageAResult (新規)

Stage A（分類判定）の出力。Dust判定とジャンル分類を統合。

| Field | Type | Description |
|-------|------|-------------|
| genre | GenreType | "エンジニア", "ビジネス", "経済", "日常", "その他", "dust", "unknown" |
| subfolder | str | サブフォルダ名（空文字=ルート、"新規: xxx"=新規作成） |
| confidence | str | "high" or "low" |
| reason | str | 判定理由（dust/unknown含む全ケースで使用） |

**Validation Rules**:
- `genre`は定義済みの値のみ許可
- `genre="dust"` → @dust/ へルーティング
- `genre="unknown"` → @review/ へルーティング、`confidence="low"`

### StageBResult (既存Stage3Resultと同等)

Stage B（Markdown正規化）の出力。既存を維持。

| Field | Type | Description |
|-------|------|-------------|
| normalized_content | str | 整形済み本文 |
| improvements_made | list[str] | 改善リスト |

### StageCResult (新規)

Stage C（メタデータ生成）の出力。タイトル・タグ・サマリー・関連を統合。

| Field | Type | Description |
|-------|------|-------------|
| title | str | ファイル名に使用可能なタイトル |
| tags | list[str] | 3-5個のタグ |
| summary | str | **最大200文字**のサマリー（frontmatterプロパティ用） |
| related | list[str] | 内部リンク形式 `[["ファイル名"]]`、最大5件 |

**Validation Rules**:
- `title`はファイル名として有効な文字列
- `tags`は1-5個
- `summary`は空でなく、**200文字以内**
- `related`の各要素は`[["..."]]`形式

### Frontmatter (更新)

YAML Frontmatterの出力形式。

| Field | Type | Description |
|-------|------|-------------|
| title | str | タイトル |
| tags | list[str] | タグリスト |
| created | str | 作成日 YYYY-MM-DD |
| summary | str | サマリー（**新規追加**） |
| related | list[str] | 関連ノート（**新規追加**） |
| normalized | bool | 正規化済みフラグ（常にtrue） |

### NormalizationResult (更新)

パイプライン全体の出力。

| Field | Type | Description |
|-------|------|-------------|
| genre | GenreType | 分類結果 |
| subfolder | str | サブフォルダ |
| confidence | str | 確信度 |
| reason | str | 判定理由 |
| frontmatter | Frontmatter | 生成されたfrontmatter |
| normalized_content | str | 正規化済み本文 |
| improvements_made | list[str] | 改善リスト |

## State Transitions

```
                    ┌─────────────────┐
                    │   pre_process   │
                    │  (ルールベース) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    Stage A      │
                    │ (分類判定 LLM)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
         genre=dust    genre=unknown   genre=valid
              │              │              │
              ▼              ▼              ▼
          @dust/         @review/     ┌────▼────┐
          (終了)         (終了)       │ Stage B │
                                      │(正規化) │
                                      └────┬────┘
                                           │
                                      ┌────▼────┐
                                      │ Stage C │
                                      │(メタ生成)│
                                      └────┬────┘
                                           │
                                      ┌────▼────┐
                                      │post_proc│
                                      │(結果統合)│
                                      └────┬────┘
                                           │
                                           ▼
                                    Vault/subfolder/
```

## Relationships

```
StageAResult ─────┐
                  │
StageBResult ─────┼───► NormalizationResult ───► Frontmatter
                  │
StageCResult ─────┘
```
