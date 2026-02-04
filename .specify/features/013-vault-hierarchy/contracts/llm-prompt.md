# LLM Prompt Contract: 階層分類

**Date**: 2026-01-15
**Feature**: 013-vault-hierarchy

## System Prompt Template

```
あなたはファイル分類AIです。ファイルの内容を読み、適切なジャンルとサブフォルダを判定してください。

## ジャンル（必須）
以下の5つから1つ選択:
- エンジニア: 技術、プログラミング、システム設計、インフラ、DevOps、AI/ML
- ビジネス: ビジネス書、マネジメント、キャリア、コミュニケーション
- 経済: 経済ニュース、投資、市場分析、金融
- 日常: 日常生活、趣味、雑記
- その他: 上記に該当しない

## サブフォルダ
{vault}の既存サブフォルダ:
{subfolder_list}

既存フォルダから最適なものを選ぶか、新規フォルダを提案してください。
新規フォルダの場合は「新規: フォルダ名」の形式で。

## 回答形式
JSON形式のみで回答:
{
  "genre": "ジャンル名",
  "subfolder": "サブフォルダ名",
  "confidence": 0.0-1.0,
  "reason": "理由（30字以内）"
}
```

## User Message Template

```
ファイル名: {filename}

タイトル: {title}
タグ: {tags}

内容:
{content_preview}
```

## Response Schema

```json
{
  "type": "object",
  "required": ["genre", "subfolder", "confidence", "reason"],
  "properties": {
    "genre": {
      "type": "string",
      "enum": ["エンジニア", "ビジネス", "経済", "日常", "その他"]
    },
    "subfolder": {
      "type": "string",
      "description": "既存フォルダ名 or '新規: xxx'"
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "reason": {
      "type": "string",
      "maxLength": 30
    }
  }
}
```

## Example: エンジニアVault

### Input

```
ファイル名: Dockerコンテナのネットワーク設定

タイトル: Dockerコンテナのネットワーク設定
タグ: [Docker, ネットワーク, コンテナ]

内容:
Dockerコンテナ間の通信を設定する方法について...
```

### Prompt with Subfolders

```
{vault}: エンジニア
{subfolder_list}:
- AWS Technical Essentials Part 1
- AWS Technical Essentials Part 2
- AWS学習
- DevOps・メトリクス
- キャリア
- セキュリティ
- テスト・QA
- データベース
- ネットワーク
- マネジメント
```

### Expected Response

```json
{
  "genre": "エンジニア",
  "subfolder": "新規: Docker",
  "confidence": 0.88,
  "reason": "Docker固有の技術メモ"
}
```

## Edge Case Handling

### 1. 確信度が低い場合

```json
{
  "genre": "エンジニア",
  "subfolder": "未分類",
  "confidence": 0.35,
  "reason": "内容が曖昧"
}
```

### 2. 複数カテゴリにまたがる場合

```json
{
  "genre": "エンジニア",
  "subfolder": "DevOps・メトリクス",
  "confidence": 0.65,
  "reason": "DevOps寄りの技術管理"
}
```

### 3. 新規フォルダ提案

```json
{
  "genre": "エンジニア",
  "subfolder": "新規: Kubernetes",
  "confidence": 0.90,
  "reason": "K8s専用フォルダが適切"
}
```

## Model Configuration

| Parameter | Value |
|-----------|-------|
| Model | gpt-oss:20b (Ollama) |
| Temperature | 0.3 |
| Max Tokens | 200 |
| Timeout | 120s |

## Error Handling

| Error | Response |
|-------|----------|
| JSON解析失敗 | `{"genre": "不明", "subfolder": "未分類", "confidence": 0, "reason": "JSON解析失敗"}` |
| タイムアウト | `{"genre": "エラー", "subfolder": "-", "confidence": 0, "reason": "タイムアウト"}` |
| 接続エラー | `{"genre": "エラー", "subfolder": "-", "confidence": 0, "reason": "接続エラー"}` |
