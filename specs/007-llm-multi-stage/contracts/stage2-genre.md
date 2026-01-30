# Stage 2: ジャンル分類 Contract

## Purpose

ファイルコンテンツを6つのジャンルに分類し、関連キーワードを抽出する。

## Input

### System Prompt

```text
あなたはコンテンツ分類AIです。
与えられたファイル内容を適切なジャンルに分類してください。

## ジャンル定義（6種類）

1. **エンジニア**: プログラミング、技術文書、システム設計、DevOps、AI/ML、インフラ
2. **ビジネス**: ビジネス書要約、マネジメント、キャリア、コミュニケーション、自己啓発
3. **経済**: 経済ニュース、投資、市場分析、金融、企業分析
4. **日常**: 日常生活、趣味、雑記、旅行、健康
5. **その他**: 上記に該当しないが価値のあるコンテンツ
6. **dust**: 価値なし（前段階で判定済みの場合のみ）

## 出力形式
必ず以下のJSON形式のみで回答してください。

```json
{
  "genre": "エンジニア",
  "confidence": 0.85,
  "related_keywords": ["Python", "CLI", "automation"]
}
```

- genre: 6種類のジャンルから1つ選択
- confidence: 判定の確信度（0.0-1.0）
- related_keywords: 関連ファイル検索用キーワード（3-5個）
```

### User Message

```text
ファイル名: {filename}
言語: {language_note}

内容:
{content}
```

`language_note`: 英語文書の場合 "この文書は英語文書です"、それ以外は空

## Output Schema

```json
{
  "type": "object",
  "required": ["genre", "confidence", "related_keywords"],
  "properties": {
    "genre": {
      "type": "string",
      "enum": ["エンジニア", "ビジネス", "経済", "日常", "その他", "dust"]
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "related_keywords": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 0,
      "maxItems": 5
    }
  }
}
```

## Validation Rules

1. `genre` は6つの値のいずれか
2. `confidence` は 0.0-1.0 の範囲
3. `related_keywords` は最大5個

## Default Values (リトライ失敗時)

```json
{
  "genre": "その他",
  "confidence": 0.5,
  "related_keywords": []
}
```

## Examples

### Input
```
ファイル名: python-cli.md
言語:

内容:
## Python CLI ツール作成

argparse を使ったコマンドラインツールの作成方法。

### 基本構成
- main.py でエントリポイントを定義
- setup.py でパッケージング
```

### Expected Output
```json
{
  "genre": "エンジニア",
  "confidence": 0.92,
  "related_keywords": ["Python", "CLI", "argparse", "コマンドライン"]
}
```
