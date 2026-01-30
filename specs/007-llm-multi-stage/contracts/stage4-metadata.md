# Stage 4: タイトル・タグ生成 Contract

## Purpose

正規化済みコンテンツから適切なタイトルとタグを生成する。

## Input

### System Prompt

```text
あなたはメタデータ生成AIです。
与えられたファイル内容から適切なタイトルとタグを生成してください。

## タイトル生成ルール

タイトルは**ファイル名として使用される**ため、以下を厳守してください：

### 良いタイトル例
- 「MySQL Online DDL の仕組みと注意点」
- 「効果的な話し方の3つのポイント」
- 「AWS Lambda のコールドスタート対策」

### 悪いタイトル例
- 「2022-10-17-Online-DDL-of-mysql」（日付プレフィックス、ハイフン区切り）
- 「メモ」「ノート」（曖昧すぎる）
- 「ファイル名: test/sample」（禁止文字を含む）

### 禁止事項
- ファイルシステム禁止文字: < > : " / \ | ? *
- 200文字を超える長さ
- 先頭・末尾の空白

## タグ付けルール
- 3〜5個の適切なタグを付与
- 日本語タグも使用可
- 過剰なタグ付けは避ける

## 出力形式
必ず以下のJSON形式のみで回答してください。

```json
{
  "title": "適切なタイトル",
  "tags": ["タグ1", "タグ2", "タグ3"]
}
```
```

### User Message

```text
ファイル名: {filename}
ジャンル: {genre}

内容:
{normalized_content}
```

## Output Schema

```json
{
  "type": "object",
  "required": ["title", "tags"],
  "properties": {
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "pattern": "^[^<>:\"/\\|?*]+$",
      "description": "ファイル名に使用可能なタイトル"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1,
      "maxItems": 5,
      "description": "3-5個のタグ"
    }
  }
}
```

## Validation Rules

1. `title` に禁止文字 `< > : " / \ | ? *` を含まない
2. `title` は1-200文字
3. `title` の先頭・末尾に空白がない
4. `tags` は1-5個

## Default Values (リトライ失敗時)

ファイル名から生成:

```json
{
  "title": "{filepath.stem}",
  "tags": []
}
```

## Examples

### Input
```
ファイル名: 2022-10-17-online-ddl.md
ジャンル: エンジニア

内容:
## MySQL Online DDL

MySQLのオンラインDDLは、テーブルロックを最小限に抑えながらスキーマ変更を行う機能である。

### 対応操作
- インデックス追加
- カラム追加（末尾のみ）
- テーブル名変更

### 注意点
- 大規模テーブルでは時間がかかる
- レプリケーション遅延に注意
```

### Expected Output
```json
{
  "title": "MySQL Online DDL の仕組みと注意点",
  "tags": ["MySQL", "DDL", "データベース", "スキーマ変更"]
}
```
