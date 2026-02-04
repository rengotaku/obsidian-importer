# Stage 1: Dust判定 Contract

## Purpose

ファイルコンテンツが「価値のないもの（dust）」かどうかを判定する。

## Input

### System Prompt

```text
あなたはファイル価値判定AIです。
与えられたファイル内容が「価値あり」か「価値なし（dust）」かを判定してください。

## dustの定義
- テスト投稿や意味のない文字列（「テスト」「あああ」「sample」等）
- 断片的すぎて文脈なしでは理解不能なメモ
- 明らかにゴミデータ

## 価値ありの定義
- 情報として意味がある内容
- 後で参照する価値がある
- 学習や記録として有用

## 出力形式
必ず以下のJSON形式のみで回答してください。

```json
{
  "is_dust": false,
  "dust_reason": null,
  "confidence": 0.95
}
```

- is_dust: dustならtrue、価値ありならfalse
- dust_reason: is_dust=trueの場合に理由を記載、falseならnull
- confidence: 判定の確信度（0.0-1.0）
```

### User Message

```text
ファイル名: {filename}

内容:
{content[:2000]}
```

## Output Schema

```json
{
  "type": "object",
  "required": ["is_dust", "dust_reason", "confidence"],
  "properties": {
    "is_dust": {
      "type": "boolean",
      "description": "dustならtrue"
    },
    "dust_reason": {
      "type": ["string", "null"],
      "description": "is_dust=trueの場合の理由"
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "判定の確信度"
    }
  }
}
```

## Validation Rules

1. `is_dust` は boolean 必須
2. `is_dust == true` の場合、`dust_reason` は空でない文字列
3. `confidence` は 0.0-1.0 の範囲

## Default Values (リトライ失敗時)

```json
{
  "is_dust": false,
  "dust_reason": null,
  "confidence": 0.5
}
```

## Examples

### Input
```
ファイル名: test.md

内容:
テスト投稿です
```

### Expected Output
```json
{
  "is_dust": true,
  "dust_reason": "テスト投稿",
  "confidence": 0.95
}
```
