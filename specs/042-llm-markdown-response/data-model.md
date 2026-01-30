# Data Model: LLM レスポンス形式をマークダウンに変更

**Date**: 2026-01-30
**Feature**: 042-llm-markdown-response

## エンティティ

### マークダウンレスポンス（入力）

LLM から返されるマークダウン形式のテキスト。

```text
# タイトル（40文字以内）

## 要約

1-2文の要約テキスト（200文字以内）

## 内容

構造化されたまとめ（Markdown 形式、コード含む）
```

**セクション定義**:

| セクション | 見出し | 必須 | 説明 |
|-----------|--------|------|------|
| タイトル | `#` (H1) | オプション | 会話のタイトル。40文字以内 |
| 要約 | `## 要約` | 必須 | 会話の要点を1-2文で。200文字以内 |
| 内容 | `## 内容` | 必須 | 構造化されたまとめ。現行の `summary_content` に対応 |

### 構造化データ（出力 dict）

パース後のデータ。既存の `parse_json_response()` 出力と同一形式。

```python
{
    "title": str,            # タイトル（空文字可）
    "summary": str,          # 要約テキスト
    "summary_content": str,  # 構造化まとめ（Markdown）
}
```

**フィールドマッピング**:

| マークダウンセクション | dict キー | デフォルト値 |
|---------------------|-----------|------------|
| `#` 見出し | `title` | `""` (空文字) |
| `## 要約` 本文 | `summary` | `""` (空文字) |
| `## 内容` 本文 | `summary_content` | `""` (空文字) |

### 翻訳レスポンス（入力）

summary_translation.txt のレスポンス形式。

```text
## 要約

翻訳された日本語のサマリー（1-2文）
```

**パース結果**:

```python
{
    "summary": str  # 翻訳されたサマリー
}
```

## 関連する既存データ構造（変更なし）

### KnowledgeDocument

`src/etl/utils/knowledge_extractor.py` に定義。本機能では変更しない。

| フィールド | 型 | 説明 |
|----------|-----|------|
| title | str | タイトル |
| summary | str | 要約 |
| summary_content | str | 構造化まとめ |
| created | str | 作成日（YYYY-MM-DD） |
| source_provider | str | プロバイダー名 |
| source_conversation | str | 会話 UUID |
| code_snippets | list | コードスニペット（空リスト） |
| references | list | 参考リンク |
| item_id | str | ファイル追跡 ID |
| normalized | bool | 正規化済みフラグ |

### ExtractionResult

`src/etl/utils/knowledge_extractor.py` に定義。本機能では変更しない。

| フィールド | 型 | 説明 |
|----------|-----|------|
| success | bool | 抽出成功フラグ |
| document | KnowledgeDocument \| None | 抽出結果 |
| error | str \| None | エラーメッセージ |
| raw_response | str \| None | LLM 生レスポンス |
| user_prompt | str \| None | 送信プロンプト |

## パース処理フロー

```text
LLM レスポンス（マークダウン）
  ↓
前処理: コードブロックフェンス除去
  ↓
セクション分割: 見出しレベルで分割
  ↓
フィールド抽出: 各セクションからテキスト抽出
  ↓
dict 構築: {"title", "summary", "summary_content"}
  ↓
既存パイプラインに渡す（KnowledgeExtractor が使用）
```
