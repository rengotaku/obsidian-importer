# Data Model: 050-fix-content-compression

## Entities

### CompressionResult (新規)

圧縮率検証の結果を表すデータクラス。

| Field | Type | Description |
|-------|------|-------------|
| original_size | int | 元の会話コンテンツのサイズ（文字数） |
| output_size | int | 出力コンテンツの全体サイズ（文字数） |
| body_size | int | 本文部分のサイズ（frontmatter 除く） |
| ratio | float | output_size / original_size |
| body_ratio | float | body_size / original_size |
| threshold | float | 元サイズに応じたしきい値（0.10, 0.15, 0.20） |
| is_valid | bool | body_ratio >= threshold |
| node_name | str | 検証を実行した node 名 |

### ParsedItem (既存、変更なし)

| Field | Type | Description |
|-------|------|-------------|
| content | str | 元の会話コンテンツ |
| file_id | str | SHA256 ハッシュベースの ID |
| source_provider | str | "claude", "openai", "github" |
| created_at | str | ISO 8601 形式のタイムスタンプ |
| conversation_name | str | 会話名（オプション） |

### TransformedItem (既存、拡張)

| Field | Type | Description |
|-------|------|-------------|
| (既存フィールド) | ... | ... |
| review_reason | str \| None | **新規**: 基準未達の理由（例: "extract_knowledge: body_ratio=3.8% < threshold=10.0%"） |

### Markdown Frontmatter (既存、拡張)

| Field | Type | Description |
|-------|------|-------------|
| title | str | タイトル |
| created | str | 作成日（YYYY-MM-DD） |
| tags | list[str] | タグ一覧 |
| summary | str | 要約 |
| source_provider | str | プロバイダー |
| file_id | str | ファイル ID |
| normalized | bool | 正規化済みフラグ |
| genre | str | ジャンル |
| topic | str | トピック |
| review_reason | str \| None | **新規**: レビュー理由（基準未達の場合のみ） |

## Relationships

```
ParsedItem
    │
    ▼ [extract_knowledge]
TransformedItem (+ review_reason)
    │
    ├─ [review_reason なし] → data/07_model_output/notes/
    │
    └─ [review_reason あり] → data/07_model_output/review/
```

## Thresholds

| 元サイズ | しきい値 (Body%) |
|---------|-----------------|
| >= 10,000文字 | 10% |
| 5,000-9,999文字 | 15% |
| < 5,000文字 | 20% |

## State Transitions

### ファイルの状態遷移

```
[input]
    │
    ▼
[parsed] ─────────────────────────────────────────────►
    │                                                  │
    ▼                                                  │
[transformed]                                          │
    │                                                  │
    ├─ [is_valid=true] ──► [notes/] ──► [organized/]  │
    │                                                  │
    └─ [is_valid=false] ─► [review/] ◄─────────────────┘
                               │
                               ▼
                         [手動レビュー]
                               │
                               ▼
                         [organized/] (手動移動)
```
