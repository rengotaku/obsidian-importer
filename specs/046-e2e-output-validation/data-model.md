# Data Model: E2Eテスト出力検証

## Entities

### E-1: ゴールデンファイル (Golden File)

テストフィクスチャをパイプラインに通した結果の「正解」Markdown 出力。

**保存先**: `tests/fixtures/golden/*.md`

**構造**: `format_markdown` node が出力する Markdown と同一フォーマット

```yaml
---
title: <タイトル（日本語）>
created: <YYYY-MM-DD>
tags:
  - <タグ1>
  - <タグ2>
source_provider: claude
file_id: <12文字の16進数ハッシュ>
normalized: true
---

## 要約

<日本語の要約テキスト>

<summary_content（詳細な Markdown 本文）>
```

**ファイル数**: テストフィクスチャ (`claude_test.zip`) の会話数に依存（現在3件）

**ライフサイクル**:
- 生成: `make test-e2e-update-golden` で初回生成
- 更新: 同コマンドで上書き更新（LLMモデル変更・プロンプト変更時）
- 参照: `make test-e2e` で比較対象として読み込み

### E-2: 類似度スコア (Similarity Score)

2つの Markdown ファイル間の一致度。

**構成**:
- `frontmatter_score` (0.0〜1.0): YAML frontmatter の構造的類似度
  - 必須キーの存在チェック (`title`, `created`, `tags`, `file_id`, `normalized`)
  - `file_id`: 完全一致（決定的な値）
  - `title`, `tags`: `difflib.SequenceMatcher` による類似度
- `body_score` (0.0〜1.0): 本文テキストの `difflib.SequenceMatcher` による類似度
- `total_score` (0.0〜1.0): `frontmatter_score * 0.3 + body_score * 0.7`

**判定閾値**: `total_score >= 0.9` で成功

### E-3: 比較レポート (Comparison Report)

テスト失敗時に出力される診断情報。

**構成（ファイルごと）**:
- `filename`: ゴールデンファイル名
- `total_score`: 総合類似度スコア
- `frontmatter_score`: frontmatter 類似度
- `body_score`: body 類似度
- `missing_keys`: frontmatter で欠落しているキー一覧
- `diff_summary`: 主要な差分の要約

## Relationships

```
テストフィクスチャ (claude_test.zip)
    ↓ [パイプライン実行]
実行出力 (data/test/07_model_output/notes/*.md)
    ↔ [比較]
ゴールデンファイル (tests/fixtures/golden/*.md)
    → 類似度スコア
    → 比較レポート（失敗時のみ）
```
