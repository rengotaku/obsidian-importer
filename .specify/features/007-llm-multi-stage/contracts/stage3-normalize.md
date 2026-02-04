# Stage 3: コンテンツ正規化 Contract

## Purpose

ファイルコンテンツを整形・改善し、読みやすいMarkdownに変換する。

## Input

### System Prompt

```text
あなたはMarkdown整形AIです。
与えられたファイル内容を読みやすく整形してください。

## 改善すべき点
1. **冗長な表現** → 簡潔に
   - 例: 「〜ということなのですが、実際には〜」→「〜である。実際には〜」
2. **不完全な文** → 文脈から補完
   - 例: 「設定ファイルを」→「設定ファイルを編集する」
3. **断片的な英語メモ** → 自然な日本語に（英語文書でない場合）
   - 例: 「cold start problem, use provisioned concurrency」→「コールドスタート問題にはProvisioned Concurrencyを使用する」

## 保持すべき点
- コードブロック（```）はそのまま保持
- 技術用語は適切に保持
- 完全な英語文書は翻訳しない

## 出力形式
必ず以下のJSON形式のみで回答してください。

```json
{
  "normalized_content": "## 見出し\n\n本文...",
  "improvements_made": ["冗長表現を簡潔化", "見出しレベル調整"]
}
```

- normalized_content: 整形済みの本文（frontmatterは含めない、##から開始）
- improvements_made: 行った改善のリスト
```

### User Message

```text
ファイル名: {filename}
ジャンル: {genre}
{language_note}

内容:
{content}
```

`language_note`: 英語文書の場合 "【注意】この文書は英語文書です。翻訳せず、構造のみ整理してください。"

## Output Schema

```json
{
  "type": "object",
  "required": ["normalized_content", "improvements_made"],
  "properties": {
    "normalized_content": {
      "type": "string",
      "minLength": 1,
      "description": "整形済み本文（frontmatter除く）"
    },
    "improvements_made": {
      "type": "array",
      "items": {"type": "string"},
      "description": "行った改善のリスト"
    }
  }
}
```

## Validation Rules

1. `normalized_content` は空でない
2. `normalized_content` にfrontmatter（`---`で囲まれた部分）を含まない
3. `improvements_made` は配列

## Default Values (リトライ失敗時)

元のコンテンツをそのまま使用:

```json
{
  "normalized_content": "{original_content}",
  "improvements_made": []
}
```

## Examples

### Input
```
ファイル名: aws-lambda.md
ジャンル: エンジニア

内容:
# Lambda

cold start problem, use provisioned concurrency

設定ファイルを

あと、メモリは512MBが良いということなのですが、実際には256MBでも動く
```

### Expected Output
```json
{
  "normalized_content": "## AWS Lambda\n\nコールドスタート問題にはProvisioned Concurrencyを使用する。\n\n設定ファイルを適切に設定する。\n\nメモリは512MBが推奨だが、256MBでも動作する。",
  "improvements_made": [
    "断片的な英語メモを日本語に変換",
    "不完全な文を補完",
    "冗長表現を簡潔化"
  ]
}
```
